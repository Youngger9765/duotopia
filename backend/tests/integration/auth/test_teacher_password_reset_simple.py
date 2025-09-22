"""簡化的密碼重設測試 - 專注於核心功能"""

from unittest.mock import patch
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
from models import Teacher
from auth import get_password_hash
from services.email_service import email_service
import secrets
from base64 import urlsafe_b64encode


def test_password_reset_api_flow():
    """測試密碼重設 API 的基本流程"""
    client = TestClient(app)

    # Mock 郵件發送，專注於 API 行為
    with patch.object(email_service, "send_password_reset_email") as mock_send:
        mock_send.return_value = True

        # Test 1: 請求密碼重設
        response = client.post(
            "/api/auth/teacher/forgot-password",
            json={"email": "demo@duotopia.com"},  # 使用已知存在的帳號
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "如果該電子郵件存在" in data["message"]

        # 確認 mock 被呼叫
        assert mock_send.called
        print("✅ Test 1: 密碼重設請求成功")

    # Test 2: 不存在的 email（安全性測試）
    response = client.post(
        "/api/auth/teacher/forgot-password", json={"email": "nonexistent@example.com"}
    )

    # 應該返回相同的訊息，不洩漏帳號是否存在
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "如果該電子郵件存在" in data["message"]
    print("✅ Test 2: 安全性測試通過（不洩漏帳號資訊）")


def test_password_reset_token_validation():
    """測試 token 驗證邏輯"""
    client = TestClient(app)
    session = SessionLocal()

    try:
        # 創建測試教師
        teacher = (
            session.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
        )
        if teacher:
            # 設置測試 token
            test_token = urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
            teacher.password_reset_token = test_token
            teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=2)
            session.commit()

            # Test 3: 驗證有效 token
            response = client.get(
                f"/api/auth/teacher/verify-reset-token?token={test_token}"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["email"] == "demo@duotopia.com"
            print("✅ Test 3: Token 驗證成功")

            # Test 4: 使用 token 重設密碼
            new_password = "new_test_password_123"
            response = client.post(
                "/api/auth/teacher/reset-password",
                json={"token": test_token, "new_password": new_password},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            print("✅ Test 4: 密碼重設成功")

            # Test 5: 驗證新密碼可以登入
            response = client.post(
                "/api/auth/teacher/login",
                json={"email": "demo@duotopia.com", "password": new_password},
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            print("✅ Test 5: 新密碼登入成功")

            # 還原密碼
            teacher.password_hash = get_password_hash("demo123")
            teacher.password_reset_token = None
            teacher.password_reset_expires_at = None
            session.commit()
            print("✅ Test 6: 密碼已還原")

    finally:
        session.close()


def test_password_reset_security():
    """測試安全性相關功能"""
    client = TestClient(app)

    # Test 7: 無效 token
    response = client.get(
        "/api/auth/teacher/verify-reset-token?token=invalid_token_xyz"
    )
    assert response.status_code == 400
    print("✅ Test 7: 無效 token 被拒絕")

    # Test 8: 密碼太短
    response = client.post(
        "/api/auth/teacher/reset-password",
        json={"token": "some_token", "new_password": "123"},  # 太短
    )
    assert response.status_code == 400
    data = response.json()
    assert "至少需要6個字元" in data["detail"]
    print("✅ Test 8: 弱密碼被拒絕")


def test_rate_limiting():
    """測試頻率限制"""
    client = TestClient(app)
    session = SessionLocal()

    try:
        # 找到測試教師
        teacher = (
            session.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
        )
        if teacher:
            # 設置最近發送時間
            teacher.password_reset_sent_at = datetime.utcnow()
            session.commit()

            # Test 9: 嘗試立即再次發送（應該被限制）
            response = client.post(
                "/api/auth/teacher/forgot-password", json={"email": "demo@duotopia.com"}
            )

            # 應該返回 429 Too Many Requests
            assert response.status_code == 429
            data = response.json()
            assert "請稍後再試" in data["detail"]
            print("✅ Test 9: 頻率限制正常運作")

            # 清理
            teacher.password_reset_sent_at = None
            session.commit()

    finally:
        session.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("開始測試密碼重設功能")
    print("=" * 60 + "\n")

    try:
        test_password_reset_api_flow()
        print()
        test_password_reset_token_validation()
        print()
        test_password_reset_security()
        print()
        test_rate_limiting()

        print("\n" + "=" * 60)
        print("✅ 所有測試通過！")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        raise
