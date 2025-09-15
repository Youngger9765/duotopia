"""
EmailService 完整單元測試，目標覆蓋率 80% 以上
"""
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from services.email_service import EmailService, email_service  # noqa: E402


class TestEmailServiceInit:
    """測試 EmailService 初始化"""

    def test_init_with_default_values(self):
        """測試使用預設值初始化"""
        service = EmailService()
        assert service.smtp_host == "smtp.gmail.com"
        assert service.smtp_port == 587
        assert service.from_email == "noreply@duotopia.com"
        assert service.from_name == "Duotopia"
        assert service.frontend_url == "http://localhost:5173"

    def test_init_with_environment_variables(self):
        """測試使用環境變數初始化"""
        with patch.dict(
            os.environ,
            {
                "SMTP_HOST": "custom.smtp.com",
                "SMTP_PORT": "465",
                "SMTP_USER": "user@test.com",
                "SMTP_PASSWORD": "secret",
                "FROM_EMAIL": "custom@test.com",
                "FROM_NAME": "CustomName",
                "FRONTEND_URL": "https://custom.com",
            },
        ):
            service = EmailService()
            assert service.smtp_host == "custom.smtp.com"
            assert service.smtp_port == 465
            assert service.smtp_user == "user@test.com"
            assert service.smtp_password == "secret"
            assert service.from_email == "custom@test.com"
            assert service.from_name == "CustomName"
            assert service.frontend_url == "https://custom.com"


class TestGenerateVerificationToken:
    """測試 token 生成"""

    def test_generate_verification_token_unique(self):
        """測試生成唯一 token"""
        service = EmailService()
        tokens = [service.generate_verification_token() for _ in range(10)]

        # 所有 token 應該都是唯一的
        assert len(set(tokens)) == 10

        # 每個 token 應該有適當長度
        for token in tokens:
            assert len(token) > 20
            assert isinstance(token, str)

    @patch("secrets.token_urlsafe")
    def test_generate_verification_token_calls_secrets(self, mock_token):
        """測試確實呼叫 secrets.token_urlsafe"""
        mock_token.return_value = "test_token_123"
        service = EmailService()

        token = service.generate_verification_token()

        assert token == "test_token_123"
        mock_token.assert_called_once_with(32)


class TestSendVerificationEmail:
    """測試發送驗證 email"""

    def test_send_verification_email_development_mode(self):
        """測試開發模式（無 SMTP 設定）"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"

        with patch("builtins.print") as mock_print:
            result = service.send_verification_email(mock_db, mock_student)

        assert result is True
        mock_db.commit.assert_called_once()
        assert mock_student.email_verification_token is not None
        assert mock_student.email_verification_sent_at is not None

        # 檢查開發模式輸出
        mock_print.assert_called()

    def test_send_verification_email_update_email(self):
        """測試更新 email 地址"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "old@test.com"

        result = service.send_verification_email(
            mock_db, mock_student, email="new@test.com"
        )

        assert result is True
        assert mock_student.email == "new@test.com"
        mock_db.commit.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_verification_email_with_smtp(self, mock_smtp_class):
        """測試使用 SMTP 發送"""
        service = EmailService()
        service.smtp_user = "user@test.com"
        service.smtp_password = "password"

        mock_smtp = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_smtp

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"

        result = service.send_verification_email(mock_db, mock_student)

        assert result is True
        mock_db.commit.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("user@test.com", "password")
        mock_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_verification_email_smtp_failure(self, mock_smtp_class):
        """測試 SMTP 發送失敗"""
        service = EmailService()
        service.smtp_user = "user@test.com"
        service.smtp_password = "password"

        # 模擬 SMTP 錯誤
        mock_smtp_class.side_effect = Exception("SMTP connection failed")

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"

        result = service.send_verification_email(mock_db, mock_student)

        assert result is False

    def test_send_verification_email_database_error(self):
        """測試資料庫錯誤"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_db.commit.side_effect = Exception("Database error")

        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"

        result = service.send_verification_email(mock_db, mock_student)

        assert result is False


class TestVerifyEmailToken:
    """測試驗證 email token"""

    def test_verify_email_token_success(self):
        """測試成功驗證 token"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email = "student@test.com"
        mock_student.email_verification_sent_at = datetime.utcnow()
        mock_student.email_verification_token = "valid_token"

        mock_db.query().filter().first.return_value = mock_student

        result = service.verify_email_token(mock_db, "valid_token")

        assert result == mock_student
        assert mock_student.email_verified is True
        assert mock_student.email_verified_at is not None
        assert mock_student.email_verification_token is None
        mock_db.commit.assert_called_once()

    def test_verify_email_token_not_found(self):
        """測試 token 不存在"""
        service = EmailService()

        mock_db = Mock()
        mock_db.query().filter().first.return_value = None

        result = service.verify_email_token(mock_db, "invalid_token")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_verify_email_token_expired(self):
        """測試 token 過期"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        # 設定為 25 小時前發送
        mock_student.email_verification_sent_at = datetime.utcnow() - timedelta(
            hours=25
        )
        mock_student.email_verification_token = "expired_token"

        mock_db.query().filter().first.return_value = mock_student

        result = service.verify_email_token(mock_db, "expired_token")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_verify_email_token_with_timezone(self):
        """測試處理時區問題"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()

        # 模擬有時區資訊的時間
        mock_sent_at = Mock()
        mock_sent_at.tzinfo = Mock()  # 有時區資訊
        mock_sent_at.replace.return_value = datetime.utcnow() - timedelta(hours=1)

        mock_student.email_verification_sent_at = mock_sent_at
        mock_student.email_verification_token = "valid_token"

        mock_db.query().filter().first.return_value = mock_student

        result = service.verify_email_token(mock_db, "valid_token")

        assert result == mock_student
        mock_sent_at.replace.assert_called_once_with(tzinfo=None)

    def test_verify_email_token_database_error(self):
        """測試資料庫錯誤"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email_verification_sent_at = datetime.utcnow()

        mock_db.query().filter().first.return_value = mock_student
        mock_db.commit.side_effect = Exception("Database error")

        result = service.verify_email_token(mock_db, "valid_token")

        assert result is None
        mock_db.rollback.assert_called_once()


class TestResendVerificationEmail:
    """測試重新發送驗證 email"""

    def test_resend_verification_email_success(self):
        """測試成功重新發送"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"
        mock_student.email_verified = False
        mock_student.email_verification_sent_at = datetime.utcnow() - timedelta(hours=1)

        with patch("builtins.print"):
            result = service.resend_verification_email(mock_db, mock_student)

        assert result is True
        mock_db.commit.assert_called_once()

    def test_resend_verification_email_already_verified(self):
        """測試已驗證的 email 不能重送"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email_verified = True

        result = service.resend_verification_email(mock_db, mock_student)

        assert result is False
        mock_db.commit.assert_not_called()

    def test_resend_verification_email_no_email(self):
        """測試沒有 email 地址"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email_verified = False
        mock_student.email = None

        result = service.resend_verification_email(mock_db, mock_student)

        assert result is False
        mock_db.commit.assert_not_called()

    def test_resend_verification_email_rate_limit(self):
        """測試發送頻率限制"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email = "student@test.com"
        mock_student.email_verified = False
        # 3 分鐘前發送過
        mock_student.email_verification_sent_at = datetime.utcnow() - timedelta(
            minutes=3
        )

        result = service.resend_verification_email(mock_db, mock_student)

        assert result is False
        mock_db.commit.assert_not_called()

    def test_resend_verification_email_after_rate_limit(self):
        """測試超過頻率限制時間後可以重送"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"
        mock_student.email_verified = False
        # 6 分鐘前發送過
        mock_student.email_verification_sent_at = datetime.utcnow() - timedelta(
            minutes=6
        )

        with patch("builtins.print"):
            result = service.resend_verification_email(mock_db, mock_student)

        assert result is True
        mock_db.commit.assert_called_once()


class TestEmailServiceIntegration:
    """整合測試"""

    def test_complete_email_verification_flow(self):
        """測試完整的 email 驗證流程"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"
        mock_student.email_verified = False
        mock_student.email_verification_sent_at = None
        mock_student.email_verification_token = None

        # 步驟 1: 發送驗證 email
        with patch("builtins.print"):
            send_result = service.send_verification_email(mock_db, mock_student)

        assert send_result is True
        assert mock_student.email_verification_token is not None

        # 儲存 token
        token = mock_student.email_verification_token

        # 步驟 2: 驗證 token
        mock_db.query().filter().first.return_value = mock_student
        verify_result = service.verify_email_token(mock_db, token)

        assert verify_result == mock_student
        assert mock_student.email_verified is True
        assert mock_student.email_verification_token is None

    def test_email_service_singleton(self):
        """測試全域 email_service 實例"""
        from services.email_service import email_service as global_service

        assert isinstance(global_service, EmailService)
        assert hasattr(global_service, "send_verification_email")
        assert hasattr(global_service, "verify_email_token")
        assert hasattr(global_service, "resend_verification_email")


class TestEmailServiceEdgeCases:
    """邊界情況測試"""

    def test_send_email_with_special_characters_in_name(self):
        """測試特殊字元名稱"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test <Student> & Co."
        mock_student.email = "student@test.com"

        with patch("builtins.print"):
            result = service.send_verification_email(mock_db, mock_student)

        assert result is True

    def test_verify_token_with_none_sent_at(self):
        """測試沒有發送時間的 token"""
        service = EmailService()

        mock_db = Mock()
        mock_student = Mock()
        mock_student.email_verification_sent_at = None
        mock_student.email_verification_token = "valid_token"

        mock_db.query().filter().first.return_value = mock_student

        result = service.verify_email_token(mock_db, "valid_token")

        assert result == mock_student
        assert mock_student.email_verified is True

    @patch("services.email_service.logger")
    def test_logging_on_errors(self, mock_logger):
        """測試錯誤日誌記錄"""
        service = EmailService()
        service.smtp_user = "user@test.com"
        service.smtp_password = "password"

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = Exception("Test error")

            mock_db = Mock()
            mock_student = Mock()
            mock_student.name = "Test"
            mock_student.email = "test@test.com"

            result = service.send_verification_email(mock_db, mock_student)

        assert result is False
        mock_logger.error.assert_called()

    def test_html_email_content_generation(self):
        """測試 HTML email 內容生成"""
        service = EmailService()
        service.smtp_user = ""
        service.smtp_password = ""
        service.frontend_url = "https://test.com"

        mock_db = Mock()
        mock_student = Mock()
        mock_student.name = "Test Student"
        mock_student.email = "student@test.com"

        with patch("builtins.print") as mock_print:
            result = service.send_verification_email(mock_db, mock_student)

        assert result is True

        # 檢查生成的 token 和 URL
        token = mock_student.email_verification_token
        assert token is not None

        # 檢查輸出包含正確的驗證連結
        print_calls = str(mock_print.call_args_list)
        assert "https://test.com/verify-email?token=" in print_calls
