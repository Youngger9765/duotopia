"""
測試批改狀態流程 API
測試教師批改作業的完整狀態轉換流程
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date  # noqa: F401

from main import app
from models import (
    Teacher,
    Student,
    Classroom,
    Assignment,
    StudentAssignment,
    AssignmentStatus,
)
from auth import create_access_token

client = TestClient(app)


@pytest.fixture
def teacher_token(db: Session):
    """創建測試教師並返回 JWT token"""
    teacher = Teacher(
        email="test_teacher@example.com",
        name="Test Teacher",
        password_hash="hashed_password",
    )
    db.add(teacher)
    db.commit()

    token = create_access_token(data={"sub": teacher.email, "user_type": "teacher"})
    return token


@pytest.fixture
def test_assignment_setup(db: Session):
    """設置測試用的作業環境"""
    # 創建教師
    teacher = Teacher(
        email="test_teacher@example.com",
        name="Test Teacher",
        password_hash="hashed_password",
    )
    db.add(teacher)

    # 創建班級
    classroom = Classroom(name="Test Class", teacher_id=1)
    db.add(classroom)

    # 創建學生
    student = Student(
        email="test_student@example.com",
        name="Test Student",
        password_hash="hashed_password",
        birthdate=date(2010, 1, 1),
    )
    db.add(student)

    # 創建主作業
    assignment = Assignment(
        title="Test Assignment",
        classroom_id=1,
        teacher_id=1,
        due_date=datetime.now(timezone.utc),
    )
    db.add(assignment)

    # 創建學生作業
    student_assignment = StudentAssignment(
        assignment_id=1,
        student_id=1,
        classroom_id=1,
        title="Test Assignment",
        status=AssignmentStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(student_assignment)

    db.commit()

    return {
        "teacher": teacher,
        "student": student,
        "classroom": classroom,
        "assignment": assignment,
        "student_assignment": student_assignment,
    }


class TestGradingStatusFlow:
    """測試批改狀態流程"""

    def test_save_grade_without_status_change(
        self, test_assignment_setup, teacher_token
    ):
        """測試儲存評分但不改變狀態（update_status=false）"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 儲存評分但不改變狀態
        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 85,
                "feedback": "Good work!",
                "update_status": False,  # 不更新狀態
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 85
        assert data["feedback"] == "Good work!"

        # 確認狀態仍然是 SUBMITTED
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.status_code == 200
        submission = response.json()
        assert submission["status"] == "SUBMITTED"

    def test_complete_grading_with_status_change(
        self, test_assignment_setup, teacher_token
    ):
        """測試完成批改並更新狀態（update_status=true）"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 完成批改並更新狀態
        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 90,
                "feedback": "Excellent!",
                "update_status": True,  # 更新狀態為 GRADED
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 90
        assert data["graded_at"] is not None

        # 確認狀態已更新為 GRADED
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.status_code == 200
        submission = response.json()
        assert submission["status"] == "GRADED"

    def test_set_in_progress_from_graded(self, test_assignment_setup, teacher_token):
        """測試從已批改狀態設回批改中"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 先將狀態設為 GRADED
        client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 85,
                "feedback": "Good",
                "update_status": True,
            },
        )

        # 設回批改中狀態
        response = client.post(
            "/api/teachers/assignments/1/set-in-progress",
            headers=headers,
            json={"student_id": 1},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUBMITTED"
        assert data["message"] == "Assignment set to in progress"

    def test_return_for_revision(self, test_assignment_setup, teacher_token):
        """測試要求學生訂正"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 要求訂正
        response = client.post(
            "/api/teachers/assignments/1/return-for-revision",
            headers=headers,
            json={"student_id": 1, "message": "Please revise your work"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "RETURNED"
        assert data["returned_at"] is not None

    def test_status_flow_complete_cycle(self, test_assignment_setup, teacher_token):
        """測試完整的狀態流程循環"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 1. 初始狀態應該是 SUBMITTED
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.json()["status"] == "SUBMITTED"

        # 2. 完成批改 -> GRADED
        client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 80,
                "feedback": "Good",
                "update_status": True,
            },
        )
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.json()["status"] == "GRADED"

        # 3. 要求訂正 -> RETURNED
        client.post(
            "/api/teachers/assignments/1/return-for-revision",
            headers=headers,
            json={"student_id": 1},
        )
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.json()["status"] == "RETURNED"

        # 4. 設回批改中 -> SUBMITTED
        client.post(
            "/api/teachers/assignments/1/set-in-progress",
            headers=headers,
            json={"student_id": 1},
        )
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.json()["status"] == "SUBMITTED"

    def test_save_item_results_with_feedback(
        self, test_assignment_setup, teacher_token
    ):
        """測試儲存個別題目評分和評語"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 儲存包含個別題目評分的資料
        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 85,
                "feedback": "總評：表現良好",
                "item_results": [
                    {"item_index": 0, "feedback": "發音清晰", "passed": True, "score": 90},
                    {
                        "item_index": 1,
                        "feedback": "需要加強語調",
                        "passed": False,
                        "score": 70,
                    },
                ],
                "update_status": False,
            },
        )

        assert response.status_code == 200

        # 確認個別題目評分已儲存
        response = client.get(
            "/api/teachers/assignments/1/submissions/1", headers=headers
        )
        assert response.status_code == 200
        # 這裡需要根據實際 API 回應格式調整驗證邏輯

    def test_unauthorized_teacher_cannot_grade(self, test_assignment_setup):
        """測試未授權教師無法批改作業"""
        # 創建另一個教師的 token
        other_teacher_token = create_access_token(
            data={"sub": "other_teacher@example.com", "user_type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {other_teacher_token}"}

        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={"student_id": 1, "score": 80, "feedback": "Test"},
        )

        assert response.status_code == 403
