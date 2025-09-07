"""
測試 Email 綁定和解除綁定的完整端到端流程
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock
import secrets
import hashlib
from main import app
from database import get_db, engine, Base
from models import Student, Teacher, Classroom
from sqlalchemy.orm import Session
import time

# 創建測試客戶端
client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """創建測試資料庫會話"""
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    yield db
    db.rollback()
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def setup_test_student(test_db: Session):
    """設置測試學生和環境"""
    # 創建老師
    teacher = Teacher(
        name="測試老師",
        email="teacher@test.com",
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",  # "password123" hashed
    )
    test_db.add(teacher)
    test_db.flush()

    # 創建班級
    classroom = Classroom(name="五年一班", teacher_id=teacher.id)
    test_db.add(classroom)
    test_db.flush()

    # 創建學生
    student = Student(
        name="小明",
        birthdate=datetime(2012, 3, 15).date(),
        classroom_id=classroom.id,
        teacher_id=teacher.id,
        password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",
    )
    test_db.add(student)
    test_db.commit()

    return student


class TestEmailBindingFlow:
    """測試 Email 綁定流程"""

    def test_complete_email_binding_flow(self, test_db: Session, setup_test_student):
        """測試完整的 Email 綁定流程：登入 -> 設定 Email -> 驗證 -> 確認"""
        student = setup_test_student

        # Step 1: 學生登入
        login_response = client.post(
            "/api/students/login",
            json={"student_id": student.id, "password": "20120315"},  # 生日作為密碼
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Step 2: 檢查初始狀態（無 Email）
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] is None
        assert profile_data["email_verified"] is False

        # Step 3: 設定 Email
        test_email = "xiaoming@test.com"
        with patch(
            "services.email_service.EmailService.send_verification_email"
        ) as mock_send:
            mock_send.return_value = True

            update_response = client.post(
                "/api/students/update-email",
                headers=headers,
                json={"email": test_email},
            )
            assert update_response.status_code == 200
            assert update_response.json()["verification_sent"] is True

            # 確認郵件被發送
            mock_send.assert_called_once()

        # Step 4: 檢查 Email 已更新但未驗證
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == test_email
        assert profile_data["email_verified"] is False

        # Step 5: 從資料庫取得驗證 token
        test_db.refresh(student)
        stored_token = student.email_verification_token
        assert stored_token is not None

        # 反推原始 token（測試用）
        # 實際上我們需要從發送的郵件中取得 token
        # 這裡我們手動創建一個 token 並更新資料庫
        verification_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(verification_token.encode()).hexdigest()
        student.email_verification_token = hashed_token
        test_db.commit()

        # Step 6: 驗證 Email
        verify_response = client.get(f"/api/students/verify-email/{verification_token}")
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["student_name"] == "小明"
        assert verify_data["email"] == test_email

        # Step 7: 確認 Email 已驗證
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == test_email
        assert profile_data["email_verified"] is True
        assert profile_data["email_verified_at"] is not None

    def test_unbind_email_flow(self, test_db: Session, setup_test_student):
        """測試解除 Email 綁定流程"""
        student = setup_test_student

        # 設置已驗證的 Email
        student.email = "xiaoming@test.com"
        student.email_verified = True
        student.email_verified_at = datetime.utcnow()
        test_db.commit()

        # 學生登入
        login_response = client.post(
            "/api/students/login",
            json={"student_id": student.id, "password": "20120315"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 確認目前有 Email
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "xiaoming@test.com"
        assert profile_response.json()["email_verified"] is True

        # 解除綁定
        unbind_response = client.post("/api/students/unbind-email", headers=headers)
        assert unbind_response.status_code == 200
        assert unbind_response.json()["message"] == "Email 綁定已解除"

        # 確認 Email 已被移除
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] is None
        assert profile_data["email_verified"] is False
        assert profile_data["email_verified_at"] is None

    def test_change_email_flow(self, test_db: Session, setup_test_student):
        """測試更換 Email 流程"""
        student = setup_test_student

        # 設置初始已驗證的 Email
        old_email = "old@test.com"
        student.email = old_email
        student.email_verified = True
        student.email_verified_at = datetime.utcnow()
        test_db.commit()

        # 學生登入
        login_response = client.post(
            "/api/students/login",
            json={"student_id": student.id, "password": "20120315"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 更換到新 Email
        new_email = "new@test.com"
        with patch(
            "services.email_service.EmailService.send_verification_email"
        ) as mock_send:
            mock_send.return_value = True

            update_response = client.post(
                "/api/students/update-email", headers=headers, json={"email": new_email}
            )
            assert update_response.status_code == 200

        # 確認 Email 已更新但需要重新驗證
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == new_email
        assert profile_data["email_verified"] is False  # 需要重新驗證

        # 驗證新 Email
        test_db.refresh(student)
        verification_token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(verification_token.encode()).hexdigest()
        student.email_verification_token = hashed_token
        test_db.commit()

        verify_response = client.get(f"/api/students/verify-email/{verification_token}")
        assert verify_response.status_code == 200

        # 確認新 Email 已驗證
        profile_response = client.get("/api/students/me", headers=headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["email"] == new_email
        assert profile_data["email_verified"] is True

    def test_cannot_use_duplicate_email(self, test_db: Session, setup_test_student):
        """測試不能使用已被其他學生使用的 Email"""
        student1 = setup_test_student

        # 創建第二個學生
        student2 = Student(
            name="小華",
            birthdate=datetime(2012, 5, 20).date(),
            classroom_id=student1.classroom_id,
            teacher_id=student1.teacher_id,
            password_hash="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiGRsiEz1DpS",
            email="used@test.com",
            email_verified=True,
        )
        test_db.add(student2)
        test_db.commit()

        # 第一個學生登入
        login_response = client.post(
            "/api/students/login",
            json={"student_id": student1.id, "password": "20120315"},
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 嘗試使用已被佔用的 Email
        with patch(
            "services.email_service.EmailService.send_verification_email"
        ) as mock_send:
            update_response = client.post(
                "/api/students/update-email",
                headers=headers,
                json={"email": "used@test.com"},
            )
            assert update_response.status_code == 400
            assert "Email 已被其他帳號使用" in update_response.json()["detail"]

            # 確認郵件沒有被發送
            mock_send.assert_not_called()

    def test_verify_token_only_once(self, test_db: Session, setup_test_student):
        """測試驗證 token 只能使用一次"""
        student = setup_test_student

        # 設置待驗證的 Email
        token = secrets.token_urlsafe(32)
        hashed_token = hashlib.sha256(token.encode()).hexdigest()

        student.email = "test@test.com"
        student.email_verification_token = hashed_token
        student.email_verification_sent_at = datetime.utcnow()
        student.email_verified = False
        test_db.commit()

        # 第一次驗證成功
        first_response = client.get(f"/api/students/verify-email/{token}")
        assert first_response.status_code == 200

        # 第二次驗證失敗（模擬 React StrictMode 重複呼叫）
        time.sleep(0.1)  # 確保不是同時發生
        second_response = client.get(f"/api/students/verify-email/{token}")
        assert second_response.status_code == 400
        assert "Invalid or expired token" in second_response.json()["detail"]

        # 確認 Email 仍然是已驗證狀態
        test_db.refresh(student)
        assert student.email_verified is True
        assert student.email_verification_token is None  # token 已被清除


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
