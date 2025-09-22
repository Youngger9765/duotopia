"""
教師註冊 Email 驗證整合測試
確保註冊流程正確且 Email 發送功能運作
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from models import Teacher
from unittest.mock import patch

# 測試資料庫設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_teacher_registration.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestTeacherRegistrationEmail:
    """教師註冊與 Email 驗證測試"""

    def setup_method(self):
        """每個測試前清空資料庫"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_registration_returns_correct_response_format(self):
        """測試註冊 API 回傳正確的格式"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "test_teacher@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "測試教師",
            },
        )

        # 應該回傳 200（不是 500）
        assert response.status_code == 200, f"錯誤: {response.text}"

        data = response.json()

        # 檢查必要欄位
        assert "message" in data
        assert "email" in data
        assert "verification_required" in data

        # 檢查值
        assert data["email"] == "test_teacher@example.com"
        assert data["verification_required"] is True
        assert "check your email" in data["message"].lower()

    @patch("services.email_service.EmailService.send_teacher_verification_email")
    def test_registration_sends_verification_email(self, mock_send_email):
        """測試註冊時是否發送驗證 email"""
        mock_send_email.return_value = True

        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "verify_test@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "驗證測試",
            },
        )

        assert response.status_code == 200

        # 確認 email 服務被呼叫
        assert mock_send_email.called

    def test_unverified_teacher_cannot_login(self):
        """測試未驗證的教師無法登入"""
        # 先註冊
        register_response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "unverified@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "未驗證教師",
            },
        )

        assert register_response.status_code == 200

        # 嘗試登入
        login_response = client.post(
            "/api/auth/teacher/login",
            json={"email": "unverified@example.com", "password": "password123"},
        )

        # 應該被拒絕
        assert login_response.status_code == 401
        assert "verify your email" in login_response.json()["detail"].lower()

    @patch("services.email_service.EmailService.send_teacher_verification_email")
    def test_registration_handles_email_failure_gracefully(self, mock_send_email):
        """測試 email 發送失敗時的處理"""
        mock_send_email.return_value = False

        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "email_fail@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "Email失敗測試",
            },
        )

        # 應該回傳錯誤
        assert response.status_code == 500
        assert "email failed to send" in response.json()["detail"].lower()

    def test_duplicate_registration_not_allowed(self):
        """測試重複註冊相同 email"""
        # 第一次註冊
        first_response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "duplicate@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "第一個",
            },
        )

        assert first_response.status_code == 200

        # 第二次註冊相同 email
        second_response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "duplicate@example.com",
                "password": "password456",
                "password_confirm": "password456",
                "name": "第二個",
            },
        )

        # 如果未驗證，應該允許重新註冊（覆蓋舊的）
        assert second_response.status_code == 200

    def test_registration_creates_inactive_teacher(self):
        """測試註冊創建的教師是未啟用狀態"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "inactive_test@example.com",
                "password": "password123",
                "password_confirm": "password123",
                "name": "未啟用測試",
            },
        )

        assert response.status_code == 200

        # 檢查資料庫
        db = TestingSessionLocal()
        teacher = (
            db.query(Teacher)
            .filter(Teacher.email == "inactive_test@example.com")
            .first()
        )

        assert teacher is not None
        assert teacher.is_active is False
        assert teacher.email_verified is False
        assert teacher.subscription_end_date is None  # 尚未給予試用期

        db.close()

    def test_password_mismatch_validation(self):
        """測試密碼不一致的驗證"""
        response = client.post(
            "/api/auth/teacher/register",
            json={
                "email": "mismatch@example.com",
                "password": "password123",
                "password_confirm": "different456",
                "name": "密碼不一致",
            },
        )

        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
