#!/usr/bin/env python
"""
測試 TapPay Sandbox 完整功能
"""
import sys

sys.path.insert(0, "backend")


def test_config():
    """測試 Backend Config"""
    print("=== 測試 1: Backend Config ===")
    from core.config import settings

    assert (
        settings.TAPPAY_ENV == "sandbox"
    ), f"Expected sandbox, got {settings.TAPPAY_ENV}"
    assert settings.tappay_app_id == "164155", f"APP_ID 錯誤: {settings.tappay_app_id}"
    assert settings.tappay_partner_key, "PARTNER_KEY 是空的！"
    assert (
        settings.tappay_merchant_id == "tppf_duotopia_GP_POS_3"
    ), f"MERCHANT_ID 錯誤: {settings.tappay_merchant_id}"

    print(f"✅ TAPPAY_ENV: {settings.TAPPAY_ENV}")
    print(f"✅ APP_ID: {settings.tappay_app_id}")
    print(f"✅ PARTNER_KEY: {settings.tappay_partner_key[:20]}...")
    print(f"✅ MERCHANT_ID: {settings.tappay_merchant_id}")
    print()


def test_service():
    """測試 TapPayService"""
    print("=== 測試 2: TapPayService ===")
    from services.tappay_service import TapPayService

    service = TapPayService()

    assert service.environment == "sandbox", f"Environment 錯誤: {service.environment}"
    assert "sandbox.tappaysdk.com" in service.api_url, f"API URL 錯誤: {service.api_url}"
    assert (
        service.merchant_id == "tppf_duotopia_GP_POS_3"
    ), f"Merchant ID 錯誤: {service.merchant_id}"

    print(f"✅ Environment: {service.environment}")
    print(f"✅ API URL: {service.api_url}")
    print(f"✅ Merchant ID: {service.merchant_id}")
    print()


def test_frontend_env():
    """測試 Frontend 環境變數"""
    print("=== 測試 3: Frontend 環境變數 ===")
    import os

    env_file = "frontend/.env"
    if not os.path.exists(env_file):
        raise FileNotFoundError(f"{env_file} 不存在！")

    with open(env_file, "r") as f:
        content = f.read()

    assert "VITE_TAPPAY_SERVER_TYPE=sandbox" in content, "SERVER_TYPE 不是 sandbox"
    assert "VITE_TAPPAY_SANDBOX_APP_ID=164155" in content, "SANDBOX_APP_ID 錯誤"
    assert "VITE_TAPPAY_SANDBOX_APP_KEY=app_" in content, "SANDBOX_APP_KEY 缺失"

    print("✅ Frontend .env 存在")
    print("✅ VITE_TAPPAY_SERVER_TYPE=sandbox")
    print("✅ VITE_TAPPAY_SANDBOX_APP_ID=164155")
    print("✅ VITE_TAPPAY_SANDBOX_APP_KEY 已設定")
    print()


def test_frontend_build():
    """測試 Frontend 建置"""
    print("=== 測試 4: Frontend 建置檔案 ===")
    import glob  # noqa: F401

    js_files = glob.glob("frontend/dist/assets/*.js")
    if not js_files:
        raise FileNotFoundError("找不到建置檔案！請先執行 npm run build")

    from core.config import settings

    found_app_id = False
    found_app_key = False

    # 從環境變數取得實際的 APP_KEY（不要硬編碼）
    expected_app_key = settings.tappay_app_key

    for js_file in js_files:
        with open(js_file, "r") as f:
            content = f.read()
            if settings.tappay_app_id in content:
                found_app_id = True
            if expected_app_key and expected_app_key in content:
                found_app_key = True

    assert found_app_id, "APP_ID 未注入建置檔案"
    assert found_app_key, "APP_KEY 未注入建置檔案"

    print(f"✅ 找到 {len(js_files)} 個 JS 檔案")
    print(f"✅ APP_ID ({settings.tappay_app_id}) 已注入")
    print("✅ APP_KEY 已注入")
    print()


def main():
    print("╔══════════════════════════════════════════════╗")
    print("║   TapPay Sandbox 完整功能測試                ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    try:
        test_config()
        test_service()
        test_frontend_env()
        test_frontend_build()

        print("╔══════════════════════════════════════════════╗")
        print("║   🎉 所有測試通過！Sandbox 功能正常！        ║")
        print("╚══════════════════════════════════════════════╝")
        return 0

    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
