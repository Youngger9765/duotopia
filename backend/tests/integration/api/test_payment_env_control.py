"""
測試金流環境控制功能
"""
import os
import sys


# 設定環境變數來模擬不同環境
def test_enable_payment_false():
    """測試 ENABLE_PAYMENT=false 的情況"""
    print("=" * 60)
    print("測試 1: ENABLE_PAYMENT=false (免費優惠期)")
    print("=" * 60)

    # 設定環境變數
    os.environ["ENABLE_PAYMENT"] = "false"
    os.environ["ENVIRONMENT"] = "production"

    # 重新載入 payment router 來使用新的環境變數
    import importlib
    import routers.payment as payment_module

    importlib.reload(payment_module)

    print(f"✅ ENABLE_PAYMENT = {payment_module.ENABLE_PAYMENT}")
    print(f"✅ ENVIRONMENT = {payment_module.ENVIRONMENT}")

    expected_behavior = """
    預期行為:
    - Payment API 應該返回 success=False
    - message 應該包含 "免費優惠期間"
    - 不應該觸發實際付款流程
    """
    print(expected_behavior)
    print()


def test_enable_payment_true():
    """測試 ENABLE_PAYMENT=true 的情況"""
    print("=" * 60)
    print("測試 2: ENABLE_PAYMENT=true (正常付款)")
    print("=" * 60)

    # 設定環境變數
    os.environ["ENABLE_PAYMENT"] = "true"
    os.environ["ENVIRONMENT"] = "staging"

    # 重新載入 payment router
    import importlib
    import routers.payment as payment_module

    importlib.reload(payment_module)

    print(f"✅ ENABLE_PAYMENT = {payment_module.ENABLE_PAYMENT}")
    print(f"✅ ENVIRONMENT = {payment_module.ENVIRONMENT}")

    expected_behavior = """
    預期行為:
    - Payment API 應該正常處理付款請求
    - 呼叫 TapPay API
    - 記錄交易
    """
    print(expected_behavior)
    print()


if __name__ == "__main__":
    test_enable_payment_false()
    test_enable_payment_true()

    print("=" * 60)
    print("✅ 環境配置測試完成")
    print("=" * 60)
