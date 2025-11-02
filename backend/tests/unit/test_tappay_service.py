"""
TapPayService Unit Tests
測試 TapPay 服務配置和環境變數讀取
"""
import pytest
import os
from unittest.mock import patch
from services.tappay_service import TapPayService


class TestTapPayServiceConfiguration:
    """測試 TapPayService 配置"""

    def test_service_initialization_with_env_vars(self):
        """測試使用環境變數初始化服務"""
        with patch.dict(
            os.environ,
            {
                "TAPPAY_PARTNER_KEY": "test_partner_key",
                "TAPPAY_MERCHANT_ID": "test_merchant_id",
                "TAPPAY_ENV": "sandbox",
            },
        ):
            service = TapPayService()

            assert service.partner_key == "test_partner_key"
            assert service.merchant_id == "test_merchant_id"
            assert service.environment == "sandbox"
            assert (
                service.api_url
                == "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
            )

    def test_service_initialization_requires_env_vars(self):
        """測試服務初始化必須有環境變數"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TAPPAY_PARTNER_KEY environment variable is required"):
                TapPayService()

    def test_service_does_not_use_app_id_app_key(self):
        """測試服務不再使用 APP_ID 和 APP_KEY（Frontend 專用）"""
        service = TapPayService()

        # 確保 service 物件沒有 app_id 和 app_key 屬性
        assert not hasattr(service, "app_id")
        assert not hasattr(service, "app_key")

    def test_production_environment(self):
        """測試 production 環境配置"""
        with patch.dict(os.environ, {"TAPPAY_ENV": "production"}):
            service = TapPayService()

            assert service.environment == "production"
            assert (
                service.api_url == "https://prod.tappaysdk.com/tpc/payment/pay-by-prime"
            )

    def test_sandbox_environment(self):
        """測試 sandbox 環境配置"""
        with patch.dict(os.environ, {"TAPPAY_ENV": "sandbox"}):
            service = TapPayService()

            assert service.environment == "sandbox"
            assert (
                service.api_url
                == "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
            )


class TestTapPayServiceErrorParsing:
    """測試 TapPay 錯誤訊息解析"""

    def test_parse_known_error_codes(self):
        """測試解析已知錯誤碼"""
        assert TapPayService.parse_error_code(1, "Card error") == "信用卡號錯誤"
        assert TapPayService.parse_error_code(2, "Transaction failed") == "交易失敗"
        assert TapPayService.parse_error_code(3, "Expired") == "信用卡已過期"
        assert TapPayService.parse_error_code(4, "Insufficient") == "餘額不足"
        assert TapPayService.parse_error_code(5, "CVV error") == "CVV 錯誤"

    def test_parse_unknown_error_code(self):
        """測試解析未知錯誤碼"""
        result = TapPayService.parse_error_code(999, "Unknown error")
        assert "付款失敗" in result
        assert "Unknown error" in result


class TestTapPayServicePaymentProcessing:
    """測試 TapPay 付款處理"""

    @patch("services.tappay_service.requests.post")
    def test_process_payment_success(self, mock_post):
        """測試成功的付款處理"""
        # Mock TapPay API 成功回應
        mock_post.return_value.json.return_value = {
            "status": 0,
            "msg": "Success",
            "rec_trade_id": "TEST_TRADE_123",
            "bank_transaction_id": "BANK_123",
        }
        mock_post.return_value.raise_for_status.return_value = None

        service = TapPayService()
        result = service.process_payment(
            prime="test_prime_token",
            amount=230,
            details={"item_name": "Test Subscription"},
            cardholder={"name": "Test User", "email": "test@example.com"},
            order_number="TEST_ORDER_001",
        )

        assert result["status"] == 0
        assert result["msg"] == "Success"
        assert result["rec_trade_id"] == "TEST_TRADE_123"

        # 驗證調用參數
        call_args = mock_post.call_args
        assert (
            call_args[0][0] == "https://sandbox.tappaysdk.com/tpc/payment/pay-by-prime"
        )

        payload = call_args[1]["json"]
        assert payload["prime"] == "test_prime_token"
        assert payload["amount"] == 230
        assert payload["order_number"] == "TEST_ORDER_001"

    @patch("services.tappay_service.requests.post")
    def test_process_payment_failure(self, mock_post):
        """測試失敗的付款處理"""
        # Mock TapPay API 失敗回應
        mock_post.return_value.json.return_value = {
            "status": 4,
            "msg": "Insufficient funds",
        }
        mock_post.return_value.raise_for_status.return_value = None

        service = TapPayService()
        result = service.process_payment(
            prime="test_prime_token",
            amount=230,
            details={"item_name": "Test"},
            cardholder={"name": "Test", "email": "test@example.com"},
        )

        assert result["status"] == 4
        assert "餘額不足" == TapPayService.parse_error_code(result["status"], result["msg"])

    @patch("services.tappay_service.requests.post")
    def test_process_payment_api_exception(self, mock_post):
        """測試 API 調用異常處理"""
        # Mock requests exception
        mock_post.side_effect = Exception("Network error")

        service = TapPayService()
        result = service.process_payment(
            prime="test_prime_token",
            amount=230,
            details={"item_name": "Test"},
            cardholder={"name": "Test", "email": "test@example.com"},
        )

        assert result["status"] == -1
        assert "error" in result
        assert result["error"] == "INTERNAL_ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
