"""測試教師密碼重設功能的完整流程"""

import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from main import app
from database import get_db, SessionLocal
from models import Teacher
from auth import get_password_hash, verify_password
from services.email_service import email_service
import secrets


@pytest.fixture
def db_session():
    """創建測試資料庫會話"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_teacher(db_session: Session):
    """創建測試用的教師帳號"""
    # 先清理可能存在的相同 email
    existing = (
        db_session.query(Teacher)
        .filter(Teacher.email == "test.teacher@example.com")
        .first()
    )
    if existing:
        db_session.delete(existing)
        db_session.commit()

    teacher = Teacher(
        email="test.teacher@example.com",
        password_hash=get_password_hash("old_password123"),
        name="Test Teacher",
        email_verified=True,
        is_active=True,
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def client(db_session: Session):
    """創建測試客戶端"""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestPasswordResetFlow:
    """測試密碼重設完整流程"""

    def test_forgot_password_success(self, client, test_teacher, db_session):
        """測試成功發送密碼重設郵件"""
        with patch.object(email_service, "send_password_reset_email") as mock_send:
            mock_send.return_value = True

            response = client.post(
                "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "如果該電子郵件存在" in data["message"]

            # 確認 mock 被呼叫
            mock_send.assert_called_once()

            # 確認資料庫有更新 token
            db_session.refresh(test_teacher)
            assert test_teacher.password_reset_token is not None
            assert test_teacher.password_reset_sent_at is not None
            assert test_teacher.password_reset_expires_at is not None

    def test_forgot_password_nonexistent_email(self, client, db_session):
        """測試不存在的 email（應該返回相同訊息，防止枚舉攻擊）"""
        response = client.post(
            "/api/auth/teacher/forgot-password",
            json={"email": "nonexistent@example.com"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "如果該電子郵件存在" in data["message"]

    def test_forgot_password_rate_limit(self, client, test_teacher, db_session):
        """測試頻率限制（5分鐘內不能重複發送）"""
        # 第一次發送
        with patch.object(email_service, "send_password_reset_email") as mock_send:
            mock_send.return_value = True

            response1 = client.post(
                "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
            )
            assert response1.status_code == 200

        # 立即再次發送（應該被拒絕）
        response2 = client.post(
            "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
        )
        assert response2.status_code == 429
        data = response2.json()
        assert "請稍後再試" in data["detail"]

    def test_verify_reset_token_valid(self, client, test_teacher, db_session):
        """測試驗證有效的重設 token"""
        # 設置有效的 token
        token = secrets.urlsafe_base64_encode(secrets.token_bytes(32))
        test_teacher.password_reset_token = token
        test_teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=2)
        db_session.commit()

        response = client.get(f"/api/auth/teacher/verify-reset-token?token={token}")

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["email"] == test_teacher.email
        assert data["name"] == test_teacher.name

    def test_verify_reset_token_expired(self, client, test_teacher, db_session):
        """測試驗證過期的 token"""
        # 設置過期的 token
        token = secrets.urlsafe_base64_encode(secrets.token_bytes(32))
        test_teacher.password_reset_token = token
        test_teacher.password_reset_expires_at = datetime.utcnow() - timedelta(
            hours=1
        )  # 已過期
        db_session.commit()

        response = client.get(f"/api/auth/teacher/verify-reset-token?token={token}")

        assert response.status_code == 400
        data = response.json()
        assert "過期" in data["detail"]

    def test_verify_reset_token_invalid(self, client):
        """測試驗證無效的 token"""
        response = client.get(
            "/api/auth/teacher/verify-reset-token?token=invalid_token_12345"
        )

        assert response.status_code == 400
        data = response.json()
        assert "無效" in data["detail"]

    def test_reset_password_success(self, client, test_teacher, db_session):
        """測試成功重設密碼"""
        # 設置有效的 token
        token = secrets.urlsafe_base64_encode(secrets.token_bytes(32))
        test_teacher.password_reset_token = token
        test_teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=2)
        db_session.commit()

        # 重設密碼
        new_password = "new_secure_password123"
        response = client.post(
            "/api/auth/teacher/reset-password",
            json={"token": token, "new_password": new_password},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "成功" in data["message"]

        # 確認密碼已更新
        db_session.refresh(test_teacher)
        assert verify_password(new_password, test_teacher.password_hash)

        # 確認 token 已清除
        assert test_teacher.password_reset_token is None
        assert test_teacher.password_reset_expires_at is None

    def test_reset_password_weak_password(self, client, test_teacher, db_session):
        """測試密碼太弱（少於6個字元）"""
        # 設置有效的 token
        token = secrets.urlsafe_base64_encode(secrets.token_bytes(32))
        test_teacher.password_reset_token = token
        test_teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=2)
        db_session.commit()

        # 使用太短的密碼
        response = client.post(
            "/api/auth/teacher/reset-password",
            json={"token": token, "new_password": "123"},  # 太短
        )

        assert response.status_code == 400
        data = response.json()
        assert "至少需要6個字元" in data["detail"]

    def test_reset_password_expired_token(self, client, test_teacher, db_session):
        """測試使用過期的 token 重設密碼"""
        # 設置過期的 token
        token = secrets.urlsafe_base64_encode(secrets.token_bytes(32))
        test_teacher.password_reset_token = token
        test_teacher.password_reset_expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        response = client.post(
            "/api/auth/teacher/reset-password",
            json={"token": token, "new_password": "new_password123"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "過期" in data["detail"]

    def test_reset_password_invalid_token(self, client):
        """測試使用無效的 token 重設密碼"""
        response = client.post(
            "/api/auth/teacher/reset-password",
            json={"token": "invalid_token_xyz", "new_password": "new_password123"},
        )

        assert response.status_code == 400
        data = response.json()
        assert "無效" in data["detail"]

    def test_complete_password_reset_flow(self, client, test_teacher, db_session):
        """測試完整的密碼重設流程"""
        # Step 1: 請求密碼重設
        with patch.object(email_service, "send_password_reset_email") as mock_send:
            mock_send.return_value = True

            response = client.post(
                "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
            )
            assert response.status_code == 200

        # Step 2: 從資料庫取得 token（模擬從郵件取得）
        db_session.refresh(test_teacher)
        reset_token = test_teacher.password_reset_token
        assert reset_token is not None

        # Step 3: 驗證 token
        response = client.get(
            f"/api/auth/teacher/verify-reset-token?token={reset_token}"
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

        # Step 4: 使用 token 重設密碼
        new_password = "brand_new_password456"
        response = client.post(
            "/api/auth/teacher/reset-password",
            json={"token": reset_token, "new_password": new_password},
        )
        assert response.status_code == 200

        # Step 5: 使用新密碼登入
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": test_teacher.email, "password": new_password},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

        # Step 6: 確認舊密碼無法登入
        response = client.post(
            "/api/auth/teacher/login",
            json={"email": test_teacher.email, "password": "old_password123"},
        )
        assert response.status_code == 401


class TestPasswordResetEmailMocking:
    """測試郵件發送的 Mock 功能"""

    @patch.object(email_service, "send_password_reset_email")
    def test_mock_email_sending(self, mock_send, client, test_teacher):
        """測試 mock 郵件發送功能"""
        # 設置 mock 返回值
        mock_send.return_value = True

        response = client.post(
            "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
        )

        assert response.status_code == 200

        # 驗證 mock 被呼叫
        assert mock_send.called

    @patch.object(email_service, "send_password_reset_email")
    def test_mock_password_reset_email_failure(self, mock_send, client, test_teacher):
        """測試郵件發送失敗的情況"""
        # 模擬郵件發送失敗
        mock_send.return_value = False

        response = client.post(
            "/api/auth/teacher/forgot-password", json={"email": test_teacher.email}
        )

        # 即使發送失敗，也應該返回 200（安全考量）
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True  # 不洩漏失敗資訊
