"""
測試教師郵件驗證完整流程
包含註冊、發送驗證信、點擊驗證連結、自動登入等完整流程
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Teacher
from services.email_service import EmailService
import hashlib
import time


class TestTeacherEmailVerification:
    """教師郵件驗證流程測試"""

    @pytest.fixture(autouse=True)
    def setup(self, db_session: Session):
        """每個測試前的設置"""
        self.client = TestClient(app)
        db_session = db_session
        self.email_service = EmailService()

        # 清理測試資料
        db_session.query(Teacher).filter(Teacher.email.like("%test%")).delete()
        db_session.commit()

    def test_teacher_registration_sends_verification_email(self, db_session: Session):
        """測試：教師註冊後應該發送驗證郵件"""

        # 準備測試資料
        test_data = {
            "email": "test_teacher@example.com",
            "password": "Test123456!",  # 符合密碼政策：8+ 字元 + 大小寫 + 數字 + 特殊字元
            "name": "測試老師",
            "phone": "0912345678",
        }

        # Mock email 發送
        with patch.object(
            EmailService, "send_teacher_verification_email", return_value=True
        ) as mock_send:
            # 發送註冊請求
            response = self.client.post("/api/auth/teacher/register", json=test_data)

            # 驗證回應
            assert response.status_code == 200
            data = response.json()
            assert data["verification_required"] is True
            assert "message" in data
            # 訊息可能是英文或中文
            assert "email" in data["message"].lower() or "Email" in data["message"]

            # 驗證 email 被呼叫
            mock_send.assert_called_once()

            # 驗證教師被創建但未驗證
            teacher = (
                db_session.query(Teacher).filter_by(email=test_data["email"]).first()
            )
            assert teacher is not None
            assert teacher.is_email_verified is False
            assert teacher.email_verification_token is not None

    def test_verification_link_format(self, db_session: Session):
        """測試：驗證連結格式正確"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="verify_test@example.com",
            name="驗證測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 測試驗證連結格式
        expected_url = f"{self.email_service.frontend_url}/teacher/verify-email?token={verification_token}"

        # Mock email 發送並檢查 URL
        with patch.object(EmailService, "_send_email") as mock_send:
            self.email_service.send_teacher_verification_email(teacher)

            # 檢查發送的內容包含正確的 URL
            call_args = mock_send.call_args
            email_body = call_args[0][2]  # HTML 內容
            assert expected_url in email_body

    def test_verify_email_with_valid_token(self, db_session: Session):
        """測試：使用有效 token 驗證郵件"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="valid_token_test@example.com",
            name="Token測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )

        # 驗證回應
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == teacher.email

        # 驗證教師已被標記為已驗證
        db_session.refresh(teacher)
        assert teacher.is_email_verified is True
        assert teacher.email_verification_token is None

        # 驗證教師有試用權限
        db_session.refresh(teacher)
        assert teacher.trial_end_date is not None
        assert teacher.trial_end_date > datetime.now()

    def test_verify_email_with_invalid_token(self):
        """測試：使用無效 token 驗證郵件應該失敗"""

        invalid_token = "invalid_token_12345"

        # 發送驗證請求
        response = self.client.get(f"/api/auth/verify-teacher?token={invalid_token}")

        # 驗證回應
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "無效" in data["detail"] or "invalid" in data["detail"].lower()

    def test_verify_email_with_expired_token(self, db_session: Session):
        """測試：使用過期 token 驗證郵件應該失敗"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="expired_token_test@example.com",
            name="過期測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成過期的 token (簡化版)
        expired_token = "expired_token_12345"

        teacher.email_verification_token = expired_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(f"/api/auth/verify-teacher?token={expired_token}")

        # 驗證回應
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "過期" in data["detail"] or "expired" in data["detail"].lower()

    def test_already_verified_teacher(self, db_session: Session):
        """測試：已驗證的教師不應該重複驗證"""

        # 創建已驗證的教師
        teacher = Teacher(
            email="already_verified@example.com",
            name="已驗證",
            password_hash="hashed_password",
            is_email_verified=True,
            email_verification_token=None,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成 token (簡化版)
        token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()

        # 發送驗證請求
        response = self.client.get(f"/api/auth/verify-teacher?token={token}")

        # 應該返回錯誤或提示已驗證
        assert response.status_code == 400
        data = response.json()
        assert (
            "已驗證" in data.get("detail", "")
            or "already verified" in data.get("detail", "").lower()
        )

    def test_auto_login_after_verification(self, db_session: Session):
        """測試：驗證成功後自動登入"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="auto_login_test@example.com",
            name="自動登入測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )

        # 驗證回應包含登入資訊
        assert response.status_code == 200
        data = response.json()

        # 檢查是否返回有效的登入 token
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

        # 檢查用戶資訊
        assert "user" in data
        assert data["user"]["id"] == teacher.id
        assert data["user"]["email"] == teacher.email
        assert data["user"]["name"] == teacher.name

        # 使用返回的 token 訪問受保護的端點
        headers = {"Authorization": f"Bearer {data['access_token']}"}
        protected_response = self.client.get("/api/teacher/profile", headers=headers)
        assert protected_response.status_code == 200

    def test_trial_period_created_on_verification(self, db_session: Session):
        """測試：驗證成功後創建 30 天試用期"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="trial_test@example.com",
            name="試用測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )

        # 驗證回應
        assert response.status_code == 200

        # 檢查試用期是否被設定
        db_session.refresh(teacher)
        assert teacher.trial_end_date is not None

        # 檢查試用期為 30 天
        days_diff = (teacher.trial_end_date - datetime.now()).days
        assert 29 <= days_diff <= 30  # 允許少許時間差

        # 檢查試用期結束日期
        assert teacher.trial_end_date > datetime.now()

    def test_frontend_url_configuration(self):
        """測試：前端 URL 配置正確"""

        # 檢查 email service 的前端 URL 設定
        assert self.email_service.frontend_url is not None

        # 本地環境應該是 localhost:5173
        if "localhost" in self.email_service.frontend_url:
            assert "5173" in self.email_service.frontend_url

        # 生產環境應該是 https
        if "duotopia" in self.email_service.frontend_url:
            assert self.email_service.frontend_url.startswith("https://")

    def test_verification_url_correct_format(self, db_session: Session):
        """測試：驗證連結必須是 /teacher/verify-email 而不是錯誤的 /verify-teacher"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="url_format_test@example.com",
            name="URL格式測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # Mock email 發送並檢查 URL
        with patch.object(EmailService, "_send_email") as mock_send:
            self.email_service.send_teacher_verification_email(teacher)

            # 檢查發送的內容
            call_args = mock_send.call_args
            email_body = call_args[0][2]  # HTML 內容

            # 確保使用正確的路徑 /teacher/verify-email
            assert "/teacher/verify-email?token=" in email_body

            # 確保沒有使用錯誤的路徑
            assert "/verify-teacher?token=" not in email_body
            assert "/verify-teacher" not in email_body

    def test_duplicate_verification_attempts(self, db_session: Session):
        """測試：防止重複驗證（模擬 React Strict Mode 問題）"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="duplicate_test@example.com",
            name="重複測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 第一次驗證應該成功
        response1 = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert "access_token" in data1

        # 第二次驗證應該失敗（token 已被使用）
        response2 = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )
        assert response2.status_code == 400
        data2 = response2.json()
        assert "detail" in data2
        assert "無效" in data2["detail"] or "invalid" in data2["detail"].lower()

    def test_token_one_time_use(self, db_session: Session):
        """測試：Token 只能使用一次"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="one_time_token@example.com",
            name="一次性Token測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 使用 token 驗證
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )
        assert response.status_code == 200

        # 檢查 token 已被清除
        db_session.refresh(teacher)
        assert teacher.email_verification_token is None
        assert teacher.is_email_verified is True

        # 再次使用相同 token 應該失敗
        response2 = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )
        assert response2.status_code == 400

    def test_verification_response_structure(self, db_session: Session):
        """測試：驗證回應結構正確（不是 response.data.access_token）"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="response_structure@example.com",
            name="結構測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )

        # 驗證回應結構
        assert response.status_code == 200
        data = response.json()

        # 確保 access_token 在頂層，不是在 data 物件內
        assert "access_token" in data
        assert "user" in data
        assert "message" in data

        # 確保沒有額外的 data 包裝
        assert "data" not in data

        # 驗證 user 物件結構
        user = data["user"]
        assert "id" in user
        assert "email" in user
        assert "name" in user
        assert user["email"] == teacher.email

    def test_no_auto_redirect_after_verification(self, db_session: Session):
        """測試：驗證後不應該自動跳轉（避免 Invalid token 錯誤）"""

        # 創建未驗證的教師
        teacher = Teacher(
            email="no_auto_redirect@example.com",
            name="無自動跳轉測試",
            password_hash="hashed_password",
            is_email_verified=False,
        )
        db_session.add(teacher)
        db_session.commit()

        # 生成驗證 token (簡化版)
        verification_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()
        teacher.email_verification_token = verification_token
        db_session.commit()

        # 發送驗證請求
        response = self.client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )

        # 驗證成功回應
        assert response.status_code == 200
        data = response.json()

        # 確保回應包含訊息告知用戶手動前往 dashboard
        assert "message" in data
        assert "成功" in data["message"] or "success" in data["message"].lower()

        # 確保回應不包含任何重定向指令
        assert "redirect" not in response.headers
        assert response.headers.get("Location") is None

    def test_verification_with_missing_token(self):
        """測試：沒有提供 token 參數的處理"""

        # 發送沒有 token 的驗證請求
        response = self.client.get("/api/auth/verify-teacher")

        # 應該返回錯誤
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    def test_verification_idempotency(self, db_session: Session):
        """測試：驗證的冪等性 - 已驗證的教師重複驗證不應該改變狀態"""

        # 創建已驗證的教師（模擬之前已經驗證過）
        teacher = Teacher(
            email="idempotent_test@example.com",
            name="冪等測試",
            password_hash="hashed_password",
            is_email_verified=True,  # 已經驗證
            email_verification_token=None,  # Token 已清除
        )
        db_session.add(teacher)
        db_session.commit()

        # 設定試用期（模擬已經有試用期）
        teacher.trial_end_date = datetime.now() + timedelta(days=30)
        db_session.commit()

        # 生成新 token 嘗試重複驗證
        new_token = hashlib.md5(
            f"{teacher.id}-{teacher.email}-{time.time()}".encode()
        ).hexdigest()

        # 發送驗證請求
        response = self.client.get(f"/api/auth/verify-teacher?token={new_token}")

        # 應該返回錯誤或提示已驗證
        assert response.status_code == 400
        data = response.json()
        assert (
            "已驗證" in data.get("detail", "")
            or "already verified" in data.get("detail", "").lower()
        )

        # 確保試用期沒有被改變
        db_session.refresh(teacher)
        # 試用期應該保持不變（不會重新設定）
        days_remaining = (teacher.trial_end_date - datetime.now()).days
        assert 29 <= days_remaining <= 30


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
