"""
Payment Security Utilities
確保不會存儲敏感支付資訊
"""

import re
from typing import Dict, Any


def sanitize_payment_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理支付 metadata，移除敏感資訊

    Args:
        metadata: 原始 metadata

    Returns:
        清理後的 metadata
    """
    if not metadata:
        return {}

    # 複製 dict 避免修改原始資料
    safe_metadata = metadata.copy()

    # 敏感欄位黑名單
    sensitive_fields = [
        "card_number",
        "cvv",
        "cvc",
        "security_code",
        "expiry",
        "expiration",
        "full_card",
        "pin",
    ]

    # 移除敏感欄位
    for field in list(safe_metadata.keys()):
        # 檢查欄位名稱
        if any(sensitive in field.lower() for sensitive in sensitive_fields):
            del safe_metadata[field]
            continue

        # 檢查是否包含信用卡號碼模式
        if isinstance(safe_metadata[field], str):
            # 移除看起來像信用卡號的資料（13-19 位數字）
            if re.match(
                r"^\d{13,19}$", safe_metadata[field].replace(" ", "").replace("-", "")
            ):
                safe_metadata[field] = mask_card_number(safe_metadata[field])

            # 移除 CVV 格式（3-4 位數字）
            if re.match(r"^\d{3,4}$", safe_metadata[field]):
                safe_metadata[field] = "***"

    return safe_metadata


def mask_card_number(card_number: str) -> str:
    """
    遮罩信用卡號碼，只顯示最後 4 碼

    Args:
        card_number: 信用卡號碼

    Returns:
        遮罩後的號碼
    """
    # 移除空格和破折號
    clean_number = card_number.replace(" ", "").replace("-", "")

    if len(clean_number) >= 4:
        return "*" * (len(clean_number) - 4) + clean_number[-4:]
    return "*" * len(clean_number)


def validate_prime_token(prime_token: str) -> bool:
    """
    驗證 TapPay Prime Token 格式

    Args:
        prime_token: TapPay prime token

    Returns:
        是否為有效格式
    """
    # Prime token 通常很長（超過 100 字元）
    # 且包含英數字和特殊字符
    if not prime_token or len(prime_token) < 50:
        return False

    # 不應該是純數字（避免誤存信用卡號）
    if prime_token.isdigit():
        return False

    return True


def get_safe_transaction_display(
    transaction_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    取得安全的交易顯示資料（給前端用）

    Args:
        transaction_metadata: 交易 metadata

    Returns:
        安全的顯示資料
    """
    safe_data = {}

    # 只顯示安全的欄位
    safe_fields = [
        "transaction_id",
        "payment_method",
        "card_last_four",
        "bank_name",
        "created_at",
        "status",
    ]

    for field in safe_fields:
        if field in transaction_metadata:
            safe_data[field] = transaction_metadata[field]

    return safe_data
