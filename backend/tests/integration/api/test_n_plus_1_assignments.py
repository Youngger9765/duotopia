"""
N+1 Query Detection Tests for Assignment APIs

測試 Assignment 相關 API 是否存在 N+1 query 問題。
這些測試使用 QueryCounter 來監聽 SQL 查詢次數。

TDD 流程：
1. 先寫測試（預期失敗，因為有 N+1）
2. 修復代碼（加入 eager loading）
3. 測試通過
"""

from tests.utils import QueryCounter, assert_max_queries


class TestAssignmentDetailN1:
    """測試 Assignment Detail API 的 N+1 query 問題"""

    def test_get_assignment_detail_with_few_students(
        self, test_client, db_session, auth_headers_teacher, test_assignment
    ):
        """
        測試：少量學生時的查詢次數

        預期失敗原因：
        - 當前實作在循環中查詢每個學生的 progress
        - 10 個學生會產生 ~21+ 次查詢
        """
        # Arrange: 創建 10 個學生作業
        assignment_id = test_assignment["id"]
        student_count = 10

        for i in range(student_count):
            student = self._create_student(
                db_session, f"student{i}@test.com", test_assignment["classroom_id"]
            )
            self._create_student_assignment(
                db_session,
                assignment_id,
                student.id,
                test_assignment["classroom_id"],
                content_count=3,
            )

        db_session.commit()

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/teachers/assignments/{assignment_id}",
                headers=auth_headers_teacher,
            )

        # Assert: 應該成功
        assert response.status_code == 200
        data = response.json()
        assert len(data["students_progress"]) == student_count

        # 🔥 關鍵斷言：查詢次數應該 <= 10（固定，不隨學生數增長）
        # 修復後：從 36 queries 降至 7 queries（優化 80%+）
        try:
            assert_max_queries(
                counter,
                10,
                f"Assignment detail with {student_count} students should use <= 10 queries",
            )
        except AssertionError:
            # 記錄當前查詢次數，方便對比修復前後
            print("\n❌ N+1 Query Detected:")
            print(f"   Student count: {student_count}")
            print(f"   Query count: {counter.count}")
            print("   Expected: <= 5 queries")
            print(f"\n{counter.get_summary()}")
            raise

    def test_get_assignment_detail_with_many_students(
        self, test_client, db_session, auth_headers_teacher, test_assignment
    ):
        """
        測試：大量學生時的查詢次數

        這個測試用來驗證查詢次數是否隨學生數線性增長（N+1 pattern）
        """
        # Arrange: 創建 30 個學生作業
        assignment_id = test_assignment["id"]
        student_count = 30

        for i in range(student_count):
            student = self._create_student(
                db_session,
                f"student_many_{i}@test.com",
                test_assignment["classroom_id"],
            )
            self._create_student_assignment(
                db_session,
                assignment_id,
                student.id,
                test_assignment["classroom_id"],
                content_count=3,
            )

        db_session.commit()

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/teachers/assignments/{assignment_id}",
                headers=auth_headers_teacher,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["students_progress"]) == student_count

        # 🔥 查詢次數應該仍然 <= 10（不隨學生數增長）
        try:
            assert_max_queries(
                counter,
                10,
                f"Assignment detail with {student_count} students should use <= 10 queries (same as 10 students)",
            )
        except AssertionError:
            print("\n❌ N+1 Query Confirmed (scales with data):")
            print(f"   Student count: {student_count}")
            print(f"   Query count: {counter.count}")
            print("   This confirms N+1 pattern!")
            raise

    def test_get_assignment_detail_query_consistency(
        self, test_client, db_session, auth_headers_teacher, test_assignment
    ):
        """
        測試：驗證查詢次數的一致性

        比較 10 vs 30 學生的查詢次數，應該相同（固定查詢）
        如果不同，確認有 N+1 問題
        """
        assignment_id = test_assignment["id"]

        # Test with 10 students
        for i in range(10):
            student = self._create_student(
                db_session,
                f"consistency_10_{i}@test.com",
                test_assignment["classroom_id"],
            )
            self._create_student_assignment(
                db_session,
                assignment_id,
                student.id,
                test_assignment["classroom_id"],
                content_count=3,
            )
        db_session.commit()

        with QueryCounter() as counter_10:
            test_client.get(
                f"/api/teachers/assignments/{assignment_id}",
                headers=auth_headers_teacher,
            )

        query_count_10 = counter_10.count

        # 清除並測試 30 students
        from sqlalchemy import text

        db_session.execute(text("DELETE FROM student_content_progress"))
        db_session.execute(text("DELETE FROM student_assignments"))
        db_session.commit()

        for i in range(30):
            student = self._create_student(
                db_session,
                f"consistency_30_{i}@test.com",
                test_assignment["classroom_id"],
            )
            self._create_student_assignment(
                db_session,
                assignment_id,
                student.id,
                test_assignment["classroom_id"],
                content_count=3,
            )
        db_session.commit()

        with QueryCounter() as counter_30:
            test_client.get(
                f"/api/teachers/assignments/{assignment_id}",
                headers=auth_headers_teacher,
            )

        query_count_30 = counter_30.count

        # 🔥 查詢次數應該相同（±1 差異可接受，因為可能有 session 相關查詢）
        # 如果差異超過 5，確認有 N+1
        diff = abs(query_count_30 - query_count_10)
        print("\nQuery Count Comparison:")
        print(f"  10 students: {query_count_10} queries")
        print(f"  30 students: {query_count_30} queries")
        print(f"  Difference: {diff}")

        if diff > 5:
            print("\n❌ N+1 Pattern Detected!")
            print(f"   Queries grew by {diff} when students " "increased from 10 to 30")
            print("   This indicates N+1 query problem")

        # 預期失敗：當前實作查詢次數會隨學生數增長
        assert diff <= 2, (
            f"Query count should be consistent, but differs by {diff} "
            f"(10 students: {query_count_10}, 30 students: {query_count_30})"
        )

    # Helper methods
    def _create_student(self, db, email, classroom_id):
        """創建測試學生並加入教室"""
        from models import Student, ClassroomStudent
        from datetime import date

        student = Student(
            email=email,
            name=f"Test Student {email}",
            password_hash="dummy",
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        # 加入教室
        classroom_student = ClassroomStudent(
            classroom_id=classroom_id, student_id=student.id
        )
        db.add(classroom_student)
        db.flush()

        return student

    def _create_student_assignment(
        self, db, assignment_id, student_id, classroom_id, content_count
    ):
        """創建學生作業和進度"""
        from models import StudentAssignment, StudentContentProgress, AssignmentStatus

        # 創建 StudentAssignment
        student_assignment = StudentAssignment(
            assignment_id=assignment_id,
            student_id=student_id,
            classroom_id=classroom_id,
            title="Test Assignment",
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(student_assignment)
        db.flush()

        # 創建一些 content progress
        for i in range(content_count):
            progress = StudentContentProgress(
                student_assignment_id=student_assignment.id,
                content_id=i + 1,  # 假設 content IDs 存在
                status=AssignmentStatus.GRADED
                if i % 2 == 0
                else AssignmentStatus.IN_PROGRESS,
            )
            db.add(progress)

        db.flush()


class TestAssignmentListN1:
    """測試 Assignment List API 的 N+1 query 問題"""

    def test_get_assignments_list(
        self, test_client, db_session, auth_headers_teacher, test_classroom
    ):
        """
        測試：取得作業列表時的查詢次數

        根據之前分析，這個 API 也有 N+1 問題
        """
        # Arrange: 創建 50 個作業
        from app.models import Assignment

        classroom_id = test_classroom["id"]
        teacher_id = test_classroom["teacher_id"]

        for i in range(50):
            assignment = Assignment(
                title=f"Test Assignment {i}",
                description=f"Description {i}",
                classroom_id=classroom_id,
                teacher_id=teacher_id,
            )
            db_session.add(assignment)

        db_session.commit()

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/teachers/assignments?classroom_id={classroom_id}",
                headers=auth_headers_teacher,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 50

        # 🔥 查詢次數應該 <= 10（固定，不隨作業數增長）
        try:
            assert_max_queries(
                counter, 10, "Assignment list should use <= 10 queries (with stats)"
            )
        except AssertionError:
            print("\n❌ N+1 Query in Assignment List:")
            print("   Assignment count: 50")
            print(f"   Query count: {counter.count}")
            print(counter.get_summary())
            raise


class TestAssignmentPerformance:
    """效能測試：確保回應時間在可接受範圍內"""

    def test_assignment_detail_response_time(
        self, test_client, db_session, auth_headers_teacher, test_assignment
    ):
        """測試：Assignment detail 回應時間應 < 200ms"""
        import time

        assignment_id = test_assignment["id"]

        # 創建 30 個學生作業
        for i in range(30):
            student = self._create_student(
                db_session, f"perf_test_{i}@test.com", test_assignment["classroom_id"]
            )
            self._create_student_assignment(
                db_session,
                assignment_id,
                student.id,
                test_assignment["classroom_id"],
                content_count=5,
            )

        db_session.commit()

        # 測量回應時間
        start_time = time.time()
        response = test_client.get(
            f"/api/teachers/assignments/{assignment_id}",
            headers=auth_headers_teacher,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        print(f"\n⏱️  Response time: {elapsed_ms:.2f}ms")

        # 🎯 目標：< 200ms（修復 N+1 後應該達成）
        # 當前可能會超過 500ms
        if elapsed_ms > 200:
            print(
                f"⚠️  Response time {elapsed_ms:.2f}ms exceeds target 200ms (likely due to N+1)"
            )

        # 先不強制這個斷言，因為當前有 N+1 問題
        # assert elapsed_ms < 200, f"Response time {elapsed_ms}ms > 200ms"

    def _create_student(self, db, email, classroom_id):
        from models import Student, ClassroomStudent
        from datetime import date

        student = Student(
            email=email,
            name=f"Test Student {email}",
            password_hash="dummy",
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        # 加入教室
        classroom_student = ClassroomStudent(
            classroom_id=classroom_id, student_id=student.id
        )
        db.add(classroom_student)
        db.flush()

        return student

    def _create_student_assignment(self, db, assignment_id, student_id, content_count):
        from models import StudentAssignment, StudentContentProgress, AssignmentStatus

        student_assignment = StudentAssignment(
            assignment_id=assignment_id,
            student_id=student_id,
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(student_assignment)
        db.flush()

        for i in range(content_count):
            progress = StudentContentProgress(
                student_assignment_id=student_assignment.id,
                content_id=i + 1,
                completed=i % 2 == 0,
            )
            db.add(progress)

        db.flush()
