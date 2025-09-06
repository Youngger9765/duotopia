"""
測試批改回饋分離功能
測試詳實記錄和總評分離的功能
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date  # noqa: F401
import json  # noqa: F401

from main import app
from models import (
    Teacher,
    Student,
    Classroom,
    Assignment,
    StudentAssignment,
    AssignmentStatus,
    StudentContentProgress,
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
def test_grading_setup(db: Session):
    """設置測試用的批改環境"""
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

    # 創建5個題目的進度記錄
    for i in range(5):
        progress = StudentContentProgress(
            student_assignment_id=1,
            content_id=i + 1,
            status=AssignmentStatus.SUBMITTED,
            order_index=i,
            response_data={
                "audio_url": f"/api/files/audio/student_{i + 1}.mp3",
                "transcript": f"Student answer for question {i + 1}",
            },
        )
        db.add(progress)

    db.commit()

    return {
        "teacher": teacher,
        "student": student,
        "classroom": classroom,
        "assignment": assignment,
        "student_assignment": student_assignment,
    }


class TestFeedbackSeparation:
    """測試回饋分離功能"""

    def test_save_detailed_record_and_overall_comment(
        self, test_grading_setup, teacher_token, db: Session
    ):
        """測試儲存詳實記錄和總評"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 準備各題評語
        item_results = [
            {"item_index": 0, "feedback": "發音清晰", "passed": True, "score": 90},
            {"item_index": 1, "feedback": "語調需要加強", "passed": False, "score": 70},
            {"item_index": 2, "feedback": "表現良好", "passed": True, "score": 85},
            {"item_index": 3, "feedback": "需要多練習", "passed": False, "score": 60},
            {"item_index": 4, "feedback": "進步很多", "passed": True, "score": 88},
        ]

        # 總評（獨立的）
        overall_comment = "整體表現不錯，繼續加油！"

        # 組合完整回饋（詳實記錄 + 總評）
        detailed_record = "\n".join(
            [
                f"題目 {i+1} {'✅' if result['passed'] else '❌'}: {result['feedback']}"
                for i, result in enumerate(item_results)
            ]
        )
        combined_feedback = f"{detailed_record}\n\n總評: {overall_comment}"

        # 儲存評分
        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 80,
                "feedback": combined_feedback,
                "item_results": item_results,
                "update_status": False,
            },
        )

        assert response.status_code == 200

        # 驗證儲存的資料
        student_assignment = (
            db.query(StudentAssignment).filter_by(assignment_id=1, student_id=1).first()
        )

        assert student_assignment is not None
        assert student_assignment.feedback == combined_feedback
        assert "題目 1 ✅: 發音清晰" in student_assignment.feedback
        assert "題目 2 ❌: 語調需要加強" in student_assignment.feedback
        assert "總評: 整體表現不錯，繼續加油！" in student_assignment.feedback

    def test_detailed_record_without_overall_comment(
        self, test_grading_setup, teacher_token, db: Session
    ):
        """測試只有詳實記錄，沒有總評的情況"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        item_results = [
            {"item_index": 0, "feedback": "Good job", "passed": True},
            {"item_index": 1, "feedback": "Needs improvement", "passed": False},
        ]

        # 只有詳實記錄，沒有總評
        detailed_record = "\n".join(
            [
                f"題目 {i+1} {'✅' if result['passed'] else '❌'}: {result['feedback']}"
                for i, result in enumerate(item_results)
            ]
        )

        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 75,
                "feedback": detailed_record,  # 沒有總評部分
                "item_results": item_results,
                "update_status": False,
            },
        )

        assert response.status_code == 200

        # 驗證沒有總評部分
        student_assignment = (
            db.query(StudentAssignment).filter_by(assignment_id=1, student_id=1).first()
        )

        assert "總評:" not in student_assignment.feedback

    def test_overall_comment_only(self, test_grading_setup, teacher_token, db: Session):
        """測試只有總評，沒有各題評語的情況"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 只有總評
        overall_comment = "總體表現優秀，繼續保持！"

        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 95,
                "feedback": f"總評: {overall_comment}",
                "item_results": [],  # 沒有各題評語
                "update_status": False,
            },
        )

        assert response.status_code == 200

        # 驗證只有總評
        student_assignment = (
            db.query(StudentAssignment).filter_by(assignment_id=1, student_id=1).first()
        )

        assert student_assignment.feedback == f"總評: {overall_comment}"
        assert "題目" not in student_assignment.feedback

    def test_item_feedback_persistence(
        self, test_grading_setup, teacher_token, db: Session
    ):
        """測試各題評語的持久性"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 第一次儲存：只有部分題目有評語
        item_results_1 = [
            {"item_index": 0, "feedback": "第一題評語", "passed": True},
            {"item_index": 2, "feedback": "第三題評語", "passed": False},
        ]

        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 70,
                "feedback": "第一次儲存",
                "item_results": item_results_1,
                "update_status": False,
            },
        )
        assert response.status_code == 200

        # 驗證各題評語已儲存
        progress_1 = (
            db.query(StudentContentProgress)
            .filter_by(student_assignment_id=1, content_id=1)
            .first()
        )
        assert progress_1.feedback == "第一題評語"
        assert progress_1.checked.is_(True)

        progress_3 = (
            db.query(StudentContentProgress)
            .filter_by(student_assignment_id=1, content_id=3)
            .first()
        )
        assert progress_3.feedback == "第三題評語"
        assert progress_3.checked.is_(False)

        # 第二次儲存：更新部分評語
        item_results_2 = [
            {"item_index": 0, "feedback": "第一題更新評語", "passed": False},  # 改變通過狀態
            {"item_index": 1, "feedback": "第二題新評語", "passed": True},
        ]

        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 75,
                "feedback": "第二次儲存",
                "item_results": item_results_2,
                "update_status": False,
            },
        )
        assert response.status_code == 200

        # 驗證評語已更新
        db.refresh(progress_1)
        assert progress_1.feedback == "第一題更新評語"
        assert progress_1.checked.is_(False)

        progress_2 = (
            db.query(StudentContentProgress)
            .filter_by(student_assignment_id=1, content_id=2)
            .first()
        )
        assert progress_2.feedback == "第二題新評語"
        assert progress_2.checked.is_(True)

        # 第三題應該保持不變
        db.refresh(progress_3)
        assert progress_3.feedback == "第三題評語"
        assert progress_3.checked.is_(False)
