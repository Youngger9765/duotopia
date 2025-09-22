"""
Test teacher review functionality
老師批改功能的整合測試
"""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from models import Teacher, Student, StudentItemProgress, ContentItem, StudentAssignment


@pytest.fixture
def teacher_token(test_db: Session) -> str:
    """Create a test teacher and return auth token"""
    teacher = Teacher(
        email="teacher@test.com", name="Test Teacher", password_hash="hashed_password"
    )
    test_db.add(teacher)
    test_db.commit()

    # 模擬登入取得 token
    # 實際實作時需要使用正確的 JWT 生成
    return "test_teacher_token"


@pytest.fixture
def student_item_progress(test_db: Session) -> StudentItemProgress:
    """Create test data for grading"""
    # 建立測試學生
    student = Student(email="student@test.com", name="Test Student")
    test_db.add(student)

    # 建立測試作業
    assignment = StudentAssignment(
        student_id=1, assignment_id=1, title="Test Assignment", status="SUBMITTED"
    )
    test_db.add(assignment)

    # 建立測試題目
    content_item = ContentItem(
        content_id=1, order_index=0, text="What is your name?", translation="你叫什麼名字？"
    )
    test_db.add(content_item)

    # 建立學生答題進度
    progress = StudentItemProgress(
        student_assignment_id=1,
        content_item_id=1,
        answer_text="My name is John",
        recording_url="https://example.com/recording.mp3",
        status="SUBMITTED",
        # AI 評分
        accuracy_score=85.5,
        fluency_score=82.0,
        pronunciation_score=88.0,
        ai_feedback='{"overall": "Good job!"}',
        # 初始狀態未批改
        review_status="PENDING",
    )
    test_db.add(progress)
    test_db.commit()

    return progress


class TestTeacherReview:
    """測試老師批改功能"""

    def test_submit_teacher_review(
        self, client: TestClient, teacher_token: str, student_item_progress
    ):
        """測試提交老師批改"""
        response = client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "teacher_review_score": 90.5,
                "teacher_feedback": "題目 1 教師評語：發音清晰，語調自然！",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證回傳資料
        assert data["student_item_progress_id"] == student_item_progress.id
        assert data["teacher_review_score"] == 90.5
        assert data["teacher_feedback"] == "題目 1 教師評語：發音清晰，語調自然！"
        assert data["review_status"] == "REVIEWED"
        assert data["teacher_id"] is not None
        assert data["teacher_reviewed_at"] is not None

    def test_update_teacher_review(
        self, client: TestClient, teacher_token: str, student_item_progress
    ):
        """測試更新老師批改"""
        # 先提交初始批改
        client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_review_score": 85.0, "teacher_feedback": "初始評語"},
        )

        # 更新批改
        response = client.patch(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_feedback": "更新後的評語：表現進步了！"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["teacher_feedback"] == "更新後的評語：表現進步了！"
        assert data["teacher_review_score"] == 85.0  # 分數保持不變

    def test_get_assignment_items_for_review(
        self, client: TestClient, teacher_token: str, test_db: Session
    ):
        """測試取得待批改項目列表"""
        # 建立多個測試項目
        for i in range(3):
            progress = StudentItemProgress(
                student_assignment_id=1,
                content_item_id=i + 1,
                answer_text=f"Answer {i+1}",
                status="SUBMITTED",
                review_status="PENDING" if i < 2 else "REVIEWED",
                teacher_review_score=90.0 if i >= 2 else None,
            )
            test_db.add(progress)
        test_db.commit()

        # 查詢待批改項目
        response = client.get(
            "/api/teacher-review/assignment/1/items?review_status=PENDING",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 只有 2 個待批改

        for item in data:
            assert item["review_status"] == "PENDING"
            assert item["student_name"] is not None
            assert item["item_text"] is not None

    def test_batch_review_items(
        self, client: TestClient, teacher_token: str, test_db: Session
    ):
        """測試批次批改功能"""
        # 建立多個測試項目
        item_ids = []
        for i in range(3):
            progress = StudentItemProgress(
                student_assignment_id=1,
                content_item_id=i + 1,
                answer_text=f"Answer {i+1}",
                status="SUBMITTED",
                review_status="PENDING",
            )
            test_db.add(progress)
            test_db.flush()
            item_ids.append(progress.id)
        test_db.commit()

        # 批次批改
        response = client.post(
            "/api/teacher-review/batch",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "item_reviews": [
                    {
                        "student_item_progress_id": item_ids[0],
                        "teacher_review_score": 85,
                        "teacher_feedback": "題目1批改",
                    },
                    {
                        "student_item_progress_id": item_ids[1],
                        "teacher_review_score": 90,
                        "teacher_feedback": "題目2批改",
                    },
                    {
                        "student_item_progress_id": item_ids[2],
                        "teacher_review_score": 95,
                        "teacher_feedback": "題目3批改",
                    },
                ]
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failed_count"] == 0

    def test_delete_teacher_review(
        self, client: TestClient, teacher_token: str, student_item_progress
    ):
        """測試刪除老師批改（重置為 AI 評分）"""
        # 先提交批改
        client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_review_score": 88.0, "teacher_feedback": "要刪除的評語"},
        )

        # 刪除批改
        response = client.delete(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Teacher review removed successfully"

        # 驗證批改已被重置
        # 實際應該查詢資料庫確認

    def test_review_score_validation(
        self, client: TestClient, teacher_token: str, student_item_progress
    ):
        """測試評分驗證（0-100）"""
        # 測試無效分數
        response = client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_review_score": 150, "teacher_feedback": "測試"},  # 超出範圍
        )

        assert response.status_code == 422  # Validation error

        # 測試負分數
        response = client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_review_score": -10, "teacher_feedback": "測試"},  # 負數
        )

        assert response.status_code == 422

    def test_teacher_feedback_persistence(
        self,
        client: TestClient,
        teacher_token: str,
        student_item_progress,
        test_db: Session,
    ):
        """測試教師評語的持久性儲存"""
        feedback_text = "題目 1 教師評語：這是一段很長的評語，包含詳細的指導和建議..."

        # 提交評語
        response = client.post(
            f"/api/teacher-review/item/{student_item_progress.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"teacher_review_score": 92.5, "teacher_feedback": feedback_text},
        )

        assert response.status_code == 200

        # 從資料庫重新讀取驗證
        test_db.refresh(student_item_progress)
        assert student_item_progress.teacher_feedback == feedback_text
        assert student_item_progress.teacher_review_score == 92.5
        assert student_item_progress.review_status == "REVIEWED"
        assert student_item_progress.teacher_reviewed_at is not None
