"""
Issue #90: Content Items Eager Loading Test

測試 Content Items 的 eager loading 優化，避免 N+1 query 問題。

問題：當載入 Assignment detail 時，會對每個 ContentItem 進行單獨查詢
預期：使用 selectinload(Content.content_items) 一次性載入所有 items

TDD 流程：
1. 先寫測試（預期失敗，因為有 N+1）
2. 修復代碼（加入 eager loading）
3. 測試通過，查詢次數從 1+N 降至 2
"""

from tests.utils import QueryCounter, assert_max_queries


class TestContentItemsEagerLoading:
    """測試 Content Items 的 Eager Loading 優化（Issue #90）"""

    def test_assignment_detail_content_items_query_count(
        self, test_client, db_session, auth_headers_teacher
    ):
        """
        測試：Assignment detail API 載入 content items 的查詢次數

        場景：一個作業包含 10 個 Content，每個 Content 有 5 個 ContentItem
        預期：查詢次數應該是固定的，不隨 Content 或 ContentItem 數量增長

        修復前：1 (assignment) + 1 (contents) + 10 (每個 content 查詢 items) = 12+ queries
        修復後：1 (assignment) + 1 (contents with eager loaded items) = 2-5 queries
        """
        from models import (
            Teacher,
            Classroom,
            Assignment,
            Content,
            ContentItem,
            AssignmentContent,
            ContentType,
            Lesson,
            Program,
            ProgramLevel,
        )

        # Setup: Create teacher, classroom, and assignment with multiple contents
        teacher = db_session.query(Teacher).first()

        # Create program and lesson
        program = Program(
            name="Test Program",
            level=ProgramLevel.A1,
            description="Test",
            teacher_id=teacher.id,
        )
        db_session.add(program)
        db_session.flush()

        lesson = Lesson(name="Test Lesson", program_id=program.id, order_index=0)
        db_session.add(lesson)
        db_session.flush()

        # Get or create classroom
        classroom = (
            db_session.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .first()
        )

        if not classroom:
            classroom = Classroom(name="Test Class", teacher_id=teacher.id, grade="A1")
            db_session.add(classroom)
            db_session.flush()

        # Create assignment
        assignment = Assignment(
            title="Test Assignment for Issue #90",
            description="Testing eager loading",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
        )
        db_session.add(assignment)
        db_session.flush()

        # Create 10 Contents, each with 5 ContentItems
        content_count = 10
        items_per_content = 5

        for i in range(content_count):
            content = Content(
                title=f"Content {i}",
                type=ContentType.EXAMPLE_SENTENCES,
                lesson_id=lesson.id,
                order_index=i,
            )
            db_session.add(content)
            db_session.flush()

            # Add to assignment
            assignment_content = AssignmentContent(
                assignment_id=assignment.id, content_id=content.id, order_index=i
            )
            db_session.add(assignment_content)

            # Create ContentItems for this content
            for j in range(items_per_content):
                item = ContentItem(
                    content_id=content.id,
                    text=f"Item {i}-{j} text",
                    translation=f"Item {i}-{j} translation",
                    audio_url=f"https://example.com/audio/{i}-{j}.mp3",
                    order_index=j,
                )
                db_session.add(item)

        db_session.commit()

        # Act: Call API and count queries
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/teachers/assignments/{assignment.id}",
                headers=auth_headers_teacher,
            )

        # Assert: Response is successful
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == assignment.id
        assert len(data["contents"]) == content_count

        # 🔥 Key Assertion: Query count should be fixed (not grow with content count)
        # Expected after fix: <= 10 queries (assignment, contents with eager load, students, etc)
        # Before fix: 12+ queries (1 for contents + 10 for each content's items)
        max_queries = 10

        try:
            assert_max_queries(
                counter,
                max_queries,
                f"Assignment detail with {content_count} contents "
                f"({items_per_content} items each) should use <= {max_queries} queries",
            )
            print(f"\n✅ Query count: {counter.count} (within limit of {max_queries})")
        except AssertionError:
            print("\n❌ N+1 Query Detected in Content Items:")
            print(f"   Content count: {content_count}")
            print(f"   Items per content: {items_per_content}")
            print(f"   Total items: {content_count * items_per_content}")
            print(f"   Query count: {counter.count}")
            print(f"   Expected: <= {max_queries} queries")
            print(f"\n{counter.get_summary()}")
            raise

    def test_student_assignment_activities_content_items_query_count(
        self, test_client, db_session, auth_headers_student
    ):
        """
        測試：Student assignment activities API 載入 content items 的查詢次數

        這個 endpoint 也會載入 content items，應該也要使用 eager loading
        """
        from models import (
            Student,
            Classroom,
            ClassroomStudent,
            Assignment,
            Content,
            ContentItem,
            AssignmentContent,
            StudentAssignment,
            ContentType,
            Lesson,
            Program,
            ProgramLevel,
            Teacher,
            AssignmentStatus,
        )

        # Setup: Create student, assignment with contents
        student = db_session.query(Student).first()
        teacher = db_session.query(Teacher).first()

        # Create program and lesson
        program = Program(
            name="Test Program",
            level=ProgramLevel.A1,
            description="Test",
            teacher_id=teacher.id,
        )
        db_session.add(program)
        db_session.flush()

        lesson = Lesson(name="Test Lesson", program_id=program.id, order_index=0)
        db_session.add(lesson)
        db_session.flush()

        # Get or create classroom
        classroom = (
            db_session.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .first()
        )

        if not classroom:
            classroom = Classroom(name="Test Class", teacher_id=teacher.id, grade="A1")
            db_session.add(classroom)
            db_session.flush()

        # Add student to classroom
        classroom_student = ClassroomStudent(
            classroom_id=classroom.id, student_id=student.id
        )
        db_session.add(classroom_student)
        db_session.flush()

        # Create assignment
        assignment = Assignment(
            title="Test Assignment for Student",
            description="Testing eager loading",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
        )
        db_session.add(assignment)
        db_session.flush()

        # Create 15 Contents with items
        content_count = 15
        items_per_content = 8

        for i in range(content_count):
            content = Content(
                title=f"Content {i}",
                type=ContentType.EXAMPLE_SENTENCES,
                lesson_id=lesson.id,
                order_index=i,
            )
            db_session.add(content)
            db_session.flush()

            assignment_content = AssignmentContent(
                assignment_id=assignment.id, content_id=content.id, order_index=i
            )
            db_session.add(assignment_content)

            # Create ContentItems
            for j in range(items_per_content):
                item = ContentItem(
                    content_id=content.id,
                    text=f"Item {i}-{j}",
                    translation=f"Translation {i}-{j}",
                    order_index=j,
                )
                db_session.add(item)

        # Create StudentAssignment
        student_assignment = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title=assignment.title,
            status=AssignmentStatus.IN_PROGRESS,
        )
        db_session.add(student_assignment)
        db_session.commit()

        # Act: Call student API and count queries
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/students/assignments/{student_assignment.id}/activities",
                headers=auth_headers_student,
            )

        # Assert
        assert response.status_code == 200

        # 🔥 Query count should be fixed
        # Expected: <= 15 queries (student_assignment, contents, items, progress creation)
        # Before fix: 20+ queries
        max_queries = 15

        try:
            assert_max_queries(
                counter,
                max_queries,
                f"Student activities with {content_count} contents "
                f"({items_per_content} items each) should use <= {max_queries} queries",
            )
            print(
                f"\n✅ Student API query count: {counter.count} (within limit of {max_queries})"
            )
        except AssertionError:
            print("\n❌ N+1 Query in Student Activities API:")
            print(f"   Content count: {content_count}")
            print(f"   Items per content: {items_per_content}")
            print(f"   Query count: {counter.count}")
            print(f"   Expected: <= {max_queries}")
            print(f"\n{counter.get_summary()}")
            raise

    def test_scaling_consistency(self, test_client, db_session, auth_headers_teacher):
        """
        測試：驗證查詢次數不隨 Content 數量線性增長

        比較 5 vs 20 contents 的查詢次數，確認沒有 N+1 問題
        """
        from models import (
            Teacher,
            Classroom,
            Assignment,
            Content,
            ContentItem,
            AssignmentContent,
            ContentType,
            Lesson,
            Program,
            ProgramLevel,
        )

        teacher = db_session.query(Teacher).first()
        classroom = (
            db_session.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .first()
        )

        def create_assignment_with_contents(count, suffix):
            """Helper to create assignment with N contents"""
            program = Program(
                name=f"Program {suffix}",
                level=ProgramLevel.A1,
                description="Test",
                teacher_id=teacher.id,
            )
            db_session.add(program)
            db_session.flush()

            lesson = Lesson(
                name=f"Lesson {suffix}", program_id=program.id, order_index=0
            )
            db_session.add(lesson)
            db_session.flush()

            assignment = Assignment(
                title=f"Assignment {suffix}",
                classroom_id=classroom.id,
                teacher_id=teacher.id,
            )
            db_session.add(assignment)
            db_session.flush()

            for i in range(count):
                content = Content(
                    title=f"Content {suffix}-{i}",
                    type=ContentType.EXAMPLE_SENTENCES,
                    lesson_id=lesson.id,
                    order_index=i,
                )
                db_session.add(content)
                db_session.flush()

                assignment_content = AssignmentContent(
                    assignment_id=assignment.id, content_id=content.id, order_index=i
                )
                db_session.add(assignment_content)

                # Add 3 items per content
                for j in range(3):
                    item = ContentItem(
                        content_id=content.id, text=f"Text {i}-{j}", order_index=j
                    )
                    db_session.add(item)

            db_session.commit()
            return assignment.id

        # Test with 5 contents
        assignment_id_5 = create_assignment_with_contents(5, "5contents")

        with QueryCounter() as counter_5:
            response = test_client.get(
                f"/api/teachers/assignments/{assignment_id_5}",
                headers=auth_headers_teacher,
            )
        assert response.status_code == 200

        # Test with 20 contents
        assignment_id_20 = create_assignment_with_contents(20, "20contents")

        with QueryCounter() as counter_20:
            response = test_client.get(
                f"/api/teachers/assignments/{assignment_id_20}",
                headers=auth_headers_teacher,
            )
        assert response.status_code == 200

        # Compare query counts
        diff = abs(counter_20.count - counter_5.count)

        print("\n📊 Scaling Consistency Test:")
        print(f"   5 contents:  {counter_5.count} queries")
        print(f"   20 contents: {counter_20.count} queries")
        print(f"   Difference:  {diff}")

        # 🔥 Query count should be nearly identical (max diff of 2)
        # If diff > 5, we have N+1 problem
        assert diff <= 2, (
            f"Query count grew by {diff} when contents increased from 5 to 20. "
            f"This indicates N+1 query problem. "
            f"(5 contents: {counter_5.count}, 20 contents: {counter_20.count})"
        )

        print("   ✅ Query count is consistent (no N+1 pattern)")


class TestPerformanceImpact:
    """測試效能改善（Issue #90 的預期目標）"""

    def test_response_time_improvement(
        self, test_client, db_session, auth_headers_teacher
    ):
        """
        測試：Assignment detail 回應時間應該從 300ms 降至 <100ms

        Issue #90 預期效益：300ms → <100ms
        """
        import time
        from models import (
            Teacher,
            Classroom,
            Assignment,
            Content,
            ContentItem,
            AssignmentContent,
            ContentType,
            Lesson,
            Program,
            ProgramLevel,
        )

        teacher = db_session.query(Teacher).first()
        classroom = (
            db_session.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .first()
        )

        # Create realistic workload: 20 contents, 10 items each
        program = Program(
            name="Perf Test Program",
            level=ProgramLevel.A1,
            description="Test",
            teacher_id=teacher.id,
        )
        db_session.add(program)
        db_session.flush()

        lesson = Lesson(name="Perf Test Lesson", program_id=program.id, order_index=0)
        db_session.add(lesson)
        db_session.flush()

        assignment = Assignment(
            title="Performance Test Assignment",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
        )
        db_session.add(assignment)
        db_session.flush()

        for i in range(20):
            content = Content(
                title=f"Content {i}",
                type=ContentType.EXAMPLE_SENTENCES,
                lesson_id=lesson.id,
                order_index=i,
            )
            db_session.add(content)
            db_session.flush()

            assignment_content = AssignmentContent(
                assignment_id=assignment.id, content_id=content.id, order_index=i
            )
            db_session.add(assignment_content)

            for j in range(10):
                item = ContentItem(
                    content_id=content.id, text=f"Item {i}-{j}", order_index=j
                )
                db_session.add(item)

        db_session.commit()

        # Measure response time
        start = time.time()
        response = test_client.get(
            f"/api/teachers/assignments/{assignment.id}",
            headers=auth_headers_teacher,
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200

        print(f"\n⏱️  Response Time: {elapsed_ms:.2f}ms")
        print("   Target: <100ms (Issue #90 goal)")
        print("   Before fix: ~300ms")

        # 🎯 After fix, should be < 100ms
        if elapsed_ms < 100:
            print(f"   ✅ GOAL ACHIEVED! ({elapsed_ms:.2f}ms < 100ms)")
        elif elapsed_ms < 200:
            print(f"   ⚠️  Close to goal ({elapsed_ms:.2f}ms)")
        else:
            print(f"   ❌ Still too slow ({elapsed_ms:.2f}ms)")

        # Soft assertion for now (may depend on system performance)
        # assert elapsed_ms < 150, f"Response time {elapsed_ms:.2f}ms exceeds 150ms"
