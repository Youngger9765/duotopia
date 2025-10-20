"""
測試 BigQuery Logger 功能
"""

import os
from unittest.mock import patch, MagicMock
from utils.bigquery_logger import (
    log_payment_attempt,
    log_payment_success,
    log_payment_failure,
)


def test_bigquery_logger_disabled_when_credentials_missing():
    """測試當沒有 BigQuery credentials 時，logger 應該安靜失敗"""
    # 確保沒有設定 credentials
    with patch.dict(os.environ, {}, clear=True):
        # 這些呼叫不應該拋出錯誤
        log_payment_attempt(
            transaction_id="test_123",
            user_id=1,
            user_email="test@example.com",
            amount=100,
            plan_name="test_plan",
            prime_token="test_prime_token",
            request_data={"amount": 100, "plan": "test_plan"},
        )

        log_payment_success(
            transaction_id="test_123",
            user_id=1,
            user_email="test@example.com",
            amount=100,
            plan_name="test_plan",
            tappay_response={"status": 0, "msg": "Success"},
            tappay_rec_trade_id="tappay_123",
            execution_time_ms=100,
        )

        log_payment_failure(
            transaction_id="test_123",
            user_id=1,
            user_email="test@example.com",
            amount=100,
            plan_name="test_plan",
            error_stage="authentication",
            error_code="401",
            error_message="Unauthorized",
            execution_time_ms=50,
        )

    print("✅ BigQuery logger 在沒有 credentials 時正確運作（不拋錯）")


def test_bigquery_logger_with_mock_client():
    """測試 BigQuery logger 使用 mock client"""
    with patch("utils.bigquery_logger.bigquery") as mock_bigquery:
        # 設定 mock
        mock_client = MagicMock()
        mock_bigquery.Client.return_value = mock_client

        # 設定假的 credentials
        with patch.dict(
            os.environ,
            {
                "GOOGLE_APPLICATION_CREDENTIALS": "/fake/path/credentials.json",
                "GCP_PROJECT_ID": "test-project",
            },
        ):
            # 重新 import 以觸發初始化
            import importlib
            from utils import bigquery_logger

            importlib.reload(bigquery_logger)

            # 測試 log 函數
            bigquery_logger.log_payment_attempt(
                transaction_id="test_456",
                user_id=2,
                user_email="test2@example.com",
                amount=200,
                plan_name="premium_plan",
                prime_token="test_prime",
                request_data={"amount": 200},
            )

    print("✅ BigQuery logger mock 測試通過")


def test_error_stage_classification():
    """測試錯誤階段分類是否正確"""
    test_cases = [
        {
            "stage": "authentication",
            "code": "401",
            "message": "Invalid token",
            "expected": "authentication",
        },
        {
            "stage": "prime_token",
            "code": "400",
            "message": "Invalid prime token",
            "expected": "prime_token",
        },
        {
            "stage": "tappay_api",
            "code": "500",
            "message": "TapPay API error",
            "expected": "tappay_api",
        },
        {
            "stage": "database",
            "code": "500",
            "message": "Database error",
            "expected": "database",
        },
    ]

    for case in test_cases:
        # 測試 log_payment_failure 接受正確的 error_stage 參數
        try:
            log_payment_failure(
                transaction_id=f"test_{case['stage']}",
                user_id=1,
                user_email="test@example.com",
                amount=100,
                plan_name="test_plan",
                error_stage=case["stage"],
                error_code=case["code"],
                error_message=case["message"],
                execution_time_ms=50,
            )
            print(f"✅ Error stage '{case['stage']}' 測試通過")
        except Exception as e:
            print(f"❌ Error stage '{case['stage']}' 測試失敗: {e}")
            raise


def test_sensitive_data_sanitization():
    """測試敏感資料遮蔽"""
    from utils.bigquery_logger import transaction_logger

    # 測試 1: Prime token 遮蔽
    request_body = {
        "prime": "test_prime_token_1234567890_very_long_token",
        "amount": 230,
        "plan_name": "test",
        "cardholder": {
            "name": "Test User",
            "email": "test@example.com",
            "card_number": "4242424242424242",
            "ccv": "123",
            "expiry_date": "12/25",
        },
    }

    sanitized_body = transaction_logger._sanitize_body(request_body)
    assert sanitized_body["prime"].endswith("..."), "Prime token should be truncated"
    assert len(sanitized_body["prime"]) == 23, "Prime token should be 20 chars + '...'"
    assert (
        sanitized_body["cardholder"]["card_number"] == "[REDACTED]"
    ), "Card number should be redacted"
    assert sanitized_body["cardholder"]["ccv"] == "[REDACTED]", "CCV should be redacted"
    assert (
        sanitized_body["cardholder"]["expiry_date"] == "[REDACTED]"
    ), "Expiry date should be redacted"
    print("✅ Request body 敏感資料遮蔽測試通過")

    # 測試 2: TapPay response 遮蔽
    tappay_response = {
        "status": 0,
        "msg": "Success",
        "rec_trade_id": "D20241020000001",
        "card_secret": "secret_key_12345",
        "card_token": "token_abcdef",
        "bank_transaction_id": "bank_123456",
        "card_info": {"bin_code": "424242", "last_four": "4242", "issuer": "VISA"},
    }

    sanitized_response = transaction_logger._sanitize_tappay_response(tappay_response)
    assert (
        sanitized_response["card_secret"] == "[REDACTED]"
    ), "Card secret should be redacted"
    assert (
        sanitized_response["card_token"] == "[REDACTED]"
    ), "Card token should be redacted"
    assert (
        sanitized_response["bank_transaction_id"] == "[REDACTED]"
    ), "Bank transaction ID should be redacted"
    assert (
        sanitized_response["card_info"]["bin_code"] == "[REDACTED]"
    ), "BIN code should be redacted"
    assert (
        sanitized_response["card_info"]["last_four"] == "4242"
    ), "Last four digits should be kept"
    assert sanitized_response["card_info"]["issuer"] == "VISA", "Issuer should be kept"
    print("✅ TapPay response 敏感資料遮蔽測試通過")

    # 測試 3: Response body 遮蔽
    response_body = {
        "success": True,
        "transaction_id": "test_123",
        "access_token": "secret_token_abc123",
        "refresh_token": "refresh_xyz789",
        "api_key": "key_123456",
    }

    sanitized = transaction_logger._sanitize_response_body(response_body)
    assert sanitized["access_token"] == "[REDACTED]", "Access token should be redacted"
    assert (
        sanitized["refresh_token"] == "[REDACTED]"
    ), "Refresh token should be redacted"
    assert sanitized["api_key"] == "[REDACTED]", "API key should be redacted"
    assert sanitized["success"] is True, "Non-sensitive fields should be kept"
    print("✅ Response body 敏感資料遮蔽測試通過")

    # 測試 4: Authorization header 遮蔽
    headers = {
        "Authorization": "Bearer secret_token_12345",
        "Content-Type": "application/json",
        "Cookie": "session_id=abc123",
        "X-API-Key": "api_key_secret",
    }

    sanitized_headers = transaction_logger._sanitize_headers(headers)
    assert (
        sanitized_headers["Authorization"] == "[REDACTED]"
    ), "Authorization should be redacted"
    assert sanitized_headers["Cookie"] == "[REDACTED]", "Cookie should be redacted"
    assert (
        sanitized_headers["X-API-Key"] == "[REDACTED]"
    ), "API key header should be redacted"
    assert (
        sanitized_headers["Content-Type"] == "application/json"
    ), "Non-sensitive headers should be kept"
    print("✅ Headers 敏感資料遮蔽測試通過")

    # 測試 5: Frontend error 遮蔽
    frontend_error = {
        "error_type": "PaymentError",
        "message": "Payment failed",
        "user_token": "secret_user_token_12345",
        "api_key": "api_key_abcdef",
        "details": {
            "amount": 230,
            "prime": "test_prime_token_very_long_string_12345678901234567890",
            "card_number": "4242424242424242",
            "authorization": "Bearer secret_token",
        },
        "stack": "Error at line 42...",
        "long_token": "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    }

    sanitized_frontend = transaction_logger._sanitize_frontend_error(frontend_error)
    assert (
        sanitized_frontend["user_token"] == "[REDACTED]"
    ), "User token should be redacted"
    assert sanitized_frontend["api_key"] == "[REDACTED]", "API key should be redacted"
    assert (
        sanitized_frontend["details"]["prime"] == "[REDACTED]"
    ), "Prime in details should be redacted"
    assert (
        sanitized_frontend["details"]["card_number"] == "[REDACTED]"
    ), "Card number in details should be redacted"
    assert (
        sanitized_frontend["details"]["authorization"] == "[REDACTED]"
    ), "Authorization in details should be redacted"
    assert (
        sanitized_frontend["error_type"] == "PaymentError"
    ), "Non-sensitive fields should be kept"
    assert (
        sanitized_frontend["details"]["amount"] == 230
    ), "Non-sensitive fields should be kept"
    assert (
        sanitized_frontend["long_token"] == "[REDACTED]"
    ), "Token field should be redacted"
    print("✅ Frontend error 敏感資料遮蔽測試通過")


def test_security_edge_cases():
    """測試安全邊界案例（H-1, H-2, H-3, H-4）"""
    from utils.bigquery_logger import transaction_logger

    # H-1: 測試深度限制
    deeply_nested = {"level": 1}
    current = deeply_nested
    for i in range(2, 105):
        current["nested"] = {"level": i}
        current = current["nested"]

    sanitized = transaction_logger._sanitize_frontend_error(deeply_nested)
    # 應該在深度 100 處停止
    current_check = sanitized
    for i in range(100):
        if "nested" in current_check:
            current_check = current_check["nested"]
        else:
            break
    # 最後一層應該是 MAX_DEPTH_EXCEEDED
    assert "[REDACTED: MAX_DEPTH_EXCEEDED]" in str(
        current_check
    ), "Should stop at max depth"
    print("✅ H-1: 深度限制測試通過")

    # H-2: 測試特殊字元 key
    special_keys = {
        "api.key": "secret1",  # 點號
        "api-key": "secret2",  # 破折號
        "api:key": "secret3",  # 冒號
        "apiKey": "secret4",  # camelCase
        "api_key": "secret5",  # 底線（原本就支援）
        "normalKey": "safe_value",  # 非敏感
    }

    sanitized_keys = transaction_logger._sanitize_frontend_error(special_keys)
    assert sanitized_keys["api.key"] == "[REDACTED]", "api.key should be redacted"
    assert sanitized_keys["api-key"] == "[REDACTED]", "api-key should be redacted"
    assert sanitized_keys["api:key"] == "[REDACTED]", "api:key should be redacted"
    assert sanitized_keys["apiKey"] == "[REDACTED]", "apiKey should be redacted"
    assert sanitized_keys["api_key"] == "[REDACTED]", "api_key should be redacted"
    assert (
        sanitized_keys["normalKey"] == "safe_value"
    ), "normalKey should not be redacted"
    print("✅ H-2: 特殊字元 key 匹配測試通過")

    # H-3: 測試循環引用
    circular = {"name": "test", "data": {"value": 123}}
    circular["self"] = circular  # 循環引用

    sanitized_circular = transaction_logger._sanitize_frontend_error(circular)
    # 不應該拋出 RecursionError
    assert (
        sanitized_circular["self"] == "[REDACTED: CIRCULAR_REFERENCE]"
    ), "Circular reference should be detected"
    assert sanitized_circular["name"] == "test", "Other fields should be preserved"
    print("✅ H-3: 循環引用保護測試通過")

    # H-4: 測試強化的 token 偵測
    token_tests = {
        "short_30": "a" * 30,  # 剛好 30 字元（邊界值）
        "short_31": "a" * 31,  # 31 字元，應該被遮蔽
        "with_one_space": "a" * 31 + " ",  # 有一個空格，應該被遮蔽
        "with_two_spaces": "hello world test sentence",  # 多個空格的正常文字
        # jwt_token 會因為 key 名稱被遮蔽
        "some_jwt": (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ),
        "normal_text": "This is a normal sentence with spaces",
    }

    sanitized_tokens = transaction_logger._sanitize_frontend_error(token_tests)
    assert (
        sanitized_tokens["short_30"] == "a" * 30
    ), "30 chars should not be redacted (boundary)"
    assert (
        "...[REDACTED]" in sanitized_tokens["short_31"]
    ), "31 chars should be redacted"
    assert (
        "...[REDACTED]" in sanitized_tokens["with_one_space"]
    ), "31 chars + 1 space should be redacted"
    assert (
        sanitized_tokens["with_two_spaces"] == "hello world test sentence"
    ), "String with multiple spaces should not be redacted"
    # some_jwt 因為 key 名稱有 jwt 所以整個被遮蔽（正確行為）
    assert (
        sanitized_tokens["some_jwt"] == "[REDACTED]"
    ), "JWT key should be redacted by key name"
    assert (
        sanitized_tokens["normal_text"] == "This is a normal sentence with spaces"
    ), "Normal text should not be redacted"
    print("✅ H-4: 強化 token 偵測測試通過")


if __name__ == "__main__":
    test_bigquery_logger_disabled_when_credentials_missing()
    test_bigquery_logger_with_mock_client()
    test_error_stage_classification()
    test_sensitive_data_sanitization()
    test_security_edge_cases()
    print("\n✅ 所有 BigQuery Logger 測試通過！")
