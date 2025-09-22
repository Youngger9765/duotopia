"""
完整的教師批改功能整合測試
包含：單題評語、通過狀態、按需創建記錄
"""

from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from models import (
    Teacher,
    Student,
    StudentItemProgress,
    ContentItem,
    StudentAssignment,
    Assignment,
    Content,
    Classroom,
    ClassroomStudent,
)


class TestTeacherGradingComplete:
    """測試完整的教師批改功能"""

    def test_save_and_retrieve_item_feedback(
        self, test_client: TestClient, db_session: Session
    ):
        """測試1：儲存和讀取單題評語"""
        # Arrange: 準備測試資料
        teacher = Teacher(
            email="teacher@test.com", name="Test Teacher", password_hash="hashed"
        )
        student = Student(email="student@test.com", name="Test Student")
        classroom = Classroom(name="Test Class", teacher_id=1)

        db_session.add_all([teacher, student, classroom])
        db_session.commit()

        # 建立班級學生關係
        classroom_student = ClassroomStudent(classroom_id=1, student_id=1)
        db_session.add(classroom_student)

        # 建立作業和內容
        assignment = Assignment(
            title="Test Assignment",
            classroom_id=1,
            teacher_id=1,
            due_date=datetime.now(timezone.utc),
        )
        content = Content(title="Test Content", type="lesson", created_by_teacher_id=1)
        db_session.add_all([assignment, content])
        db_session.commit()

        # 建立內容項目
        content_items = [
            ContentItem(
                content_id=1, order_index=0, text="Question 1", translation="題目1"
            ),
            ContentItem(
                content_id=1, order_index=1, text="Question 2", translation="題目2"
            ),
        ]
        db_session.add_all(content_items)
        db_session.commit()

        # 建立學生作業
        student_assignment = StudentAssignment(
            student_id=1, assignment_id=1, status="SUBMITTED"
        )
        db_session.add(student_assignment)
        db_session.commit()

        # 建立學生答題記錄（有錄音）
        item_progress = StudentItemProgress(
            student_assignment_id=1,
            content_item_id=1,
            recording_url="https://example.com/recording1.mp3",
            status="SUBMITTED",
        )
        db_session.add(item_progress)
        db_session.commit()

        # Act: 教師批改（給評語和通過狀態）
        # 這裡需要模擬 JWT token
        headers = {"Authorization": "Bearer test_token"}
        response = test_client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 85,
                "feedback": "整體表現良好",
                "item_results": [
                    {
                        "item_index": 0,
                        "feedback": "題目1：發音清晰",
                        "passed": True,
                        "score": 90,
                    },
                    {
                        "item_index": 1,
                        "feedback": "題目2：需要加強語調",
                        "passed": False,
                        "score": 75,
                    },
                ],
            },
        )

        # Assert: 驗證批改成功
        assert response.status_code == 200

        # 驗證資料庫中的單題評語
        item1 = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.content_item_id == 1)
            .first()
        )
        assert item1.teacher_feedback == "題目1：發音清晰"
        assert item1.teacher_passed is True
        assert item1.teacher_review_score == 90

        # 驗證按需創建的記錄（題目2原本沒有記錄）
        item2 = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.content_item_id == 2)
            .first()
        )
        assert item2 is not None  # 應該被創建了
        assert item2.teacher_feedback == "題目2：需要加強語調"
        assert item2.teacher_passed is False
        assert item2.teacher_review_score == 75
        assert item2.status == "NOT_SUBMITTED"  # 學生沒有提交錄音

    def test_on_demand_creation_of_progress_record(
        self, test_client: TestClient, db_session: Session
    ):
        """測試2：按需創建 StudentItemProgress 記錄"""
        # Arrange: 準備沒有 StudentItemProgress 的情況
        teacher = Teacher(
            email="teacher2@test.com", name="Teacher 2", password_hash="hashed"
        )
        student = Student(email="student2@test.com", name="Student 2")
        db_session.add_all([teacher, student])
        db_session.commit()

        # 建立作業但不建立 StudentItemProgress
        student_assignment = StudentAssignment(
            student_id=2, assignment_id=1, status="NOT_STARTED"
        )
        db_session.add(student_assignment)
        db_session.commit()

        # 確認沒有 StudentItemProgress 記錄
        progress_count = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == 2)
            .count()
        )
        assert progress_count == 0

        # Act: 教師給評語（應該觸發按需創建）
        headers = {"Authorization": "Bearer test_token"}
        response = test_client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 2,
                "score": 0,
                "feedback": "學生未提交",
                "item_results": [
                    {
                        "item_index": 0,
                        "feedback": "未提交但給予指導",
                        "passed": False,
                        "score": 0,
                    }
                ],
            },
        )

        # Assert: 驗證記錄被創建
        assert response.status_code == 200

        # 檢查記錄是否被創建
        new_progress = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == 2)
            .first()
        )
        assert new_progress is not None
        assert new_progress.teacher_feedback == "未提交但給予指導"
        assert new_progress.teacher_passed is False
        assert new_progress.status == "NOT_SUBMITTED"
        assert new_progress.recording_url is None

    def test_retrieve_mixed_feedback_status(
        self, test_client: TestClient, db_session: Session
    ):
        """測試3：讀取混合狀態（部分有評語、部分沒有）"""
        # Arrange: 建立混合狀態的資料
        student_assignment = StudentAssignment(
            student_id=1, assignment_id=1, status="SUBMITTED"
        )
        db_session.add(student_assignment)
        db_session.commit()

        # 只有部分題目有教師評語
        progress_with_feedback = StudentItemProgress(
            student_assignment_id=3,
            content_item_id=1,
            recording_url="https://example.com/rec.mp3",
            teacher_feedback="有評語",
            teacher_passed=True,
            status="SUBMITTED",
        )
        progress_without_feedback = StudentItemProgress(
            student_assignment_id=3,
            content_item_id=2,
            recording_url="https://example.com/rec2.mp3",
            teacher_feedback=None,
            teacher_passed=None,
            status="SUBMITTED",
        )
        db_session.add_all([progress_with_feedback, progress_without_feedback])
        db_session.commit()

        # Act: 讀取學生提交
        headers = {"Authorization": "Bearer test_token"}
        response = test_client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )

        # Assert: 驗證回傳資料
        assert response.status_code == 200
        data = response.json()

        submissions = data.get("submissions", [])
        assert len(submissions) >= 2

        # 第一題有評語
        assert submissions[0]["feedback"] == "有評語"
        assert submissions[0]["passed"] is True

        # 第二題沒有評語
        assert (
            submissions[1].get("feedback") == ""
            or submissions[1].get("feedback") is None
        )
        assert submissions[1].get("passed") is None

    def test_update_existing_feedback(
        self, test_client: TestClient, db_session: Session
    ):
        """測試4：更新已存在的評語"""
        # Arrange: 建立已有評語的記錄
        progress = StudentItemProgress(
            student_assignment_id=1,
            content_item_id=1,
            teacher_feedback="原始評語",
            teacher_passed=True,
            teacher_review_score=85,
            status="SUBMITTED",
        )
        db_session.add(progress)
        db_session.commit()

        # Act: 更新評語
        headers = {"Authorization": "Bearer test_token"}
        response = test_client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 90,
                "feedback": "更新總評",
                "item_results": [
                    {
                        "item_index": 0,
                        "feedback": "更新後的評語",
                        "passed": False,  # 改變通過狀態
                        "score": 70,
                    }
                ],
            },
        )

        # Assert: 驗證更新成功
        assert response.status_code == 200

        # 檢查資料庫
        updated = (
            db_session.query(StudentItemProgress)
            .filter(StudentItemProgress.id == progress.id)
            .first()
        )
        assert updated.teacher_feedback == "更新後的評語"
        assert updated.teacher_passed is False
        assert updated.teacher_review_score == 70
