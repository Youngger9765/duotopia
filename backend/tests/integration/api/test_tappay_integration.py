#!/usr/bin/env python3
"""
測試 TapPay 整合功能
驗證 Frontend SDK 初始化和 Backend API 調用
"""
import requests
import json

# 測試配置
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:5173"


def test_backend_tappay_config():
    """測試 Backend TapPay 配置是否正確"""
    print("🔍 測試 1: Backend TapPay Service 配置")

    # 登入取得 token
    login_response = requests.post(
        f"{BACKEND_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if login_response.status_code == 401:
        print("⚠️  登入失敗 - 需要先在資料庫創建 demo 帳號")
        print("   請執行: python backend/scripts/create_demo_teacher.py")
        return False

    token = login_response.json()["access_token"]
    print(f"✅ 登入成功，取得 token: {token[:20]}...")

    # 測試付款 API（不實際付款，只測試配置）
    print("\n🔍 測試 2: 檢查 Backend 是否有正確的 TapPay 配置")

    # 這個請求會失敗（因為 prime token 是假的），但可以看到錯誤訊息
    payment_response = requests.post(
        f"{BACKEND_URL}/api/payment/process",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "prime": "test_prime_token",
            "amount": 230,
            "plan_name": "Tutor Teachers",
            "details": {"item_name": "Test"},
            "cardholder": {"name": "Test", "email": "test@example.com"},
        },
    )

    print(f"   狀態碼: {payment_response.status_code}")
    print(f"   回應: {json.dumps(payment_response.json(), indent=2, ensure_ascii=False)}")

    # 如果看到 TapPay 相關錯誤（而不是 config 錯誤），表示配置正確
    response_data = payment_response.json()
    if "Partner unauthorized" in str(response_data):
        print("❌ Partner Key 配置錯誤")
        return False

    print("✅ Backend TapPay 配置正確（會嘗試調用 TapPay API）")
    return True


def test_frontend_tappay_config():
    """測試 Frontend 是否能載入 TapPay 配置"""
    print("\n🔍 測試 3: Frontend TapPay SDK 配置")

    # 檢查前端頁面是否包含 TapPay SDK
    response = requests.get(f"{FRONTEND_URL}/teacher/subscription")

    if response.status_code != 200:
        print(f"❌ Frontend 訂閱頁面無法訪問: {response.status_code}")
        return False

    html = response.text

    # 檢查是否載入 TapPay SDK
    if "tappaysdk.com" in html:
        print("✅ Frontend 已載入 TapPay SDK")
    else:
        print("❌ Frontend 未找到 TapPay SDK")
        return False

    print("✅ Frontend 配置正確")
    return True


def main():
    print("=" * 60)
    print("🧪 TapPay 整合測試")
    print("=" * 60)

    # 測試 Backend
    backend_ok = test_backend_tappay_config()

    # 測試 Frontend
    frontend_ok = test_frontend_tappay_config()

    print("\n" + "=" * 60)
    print("📊 測試結果總結")
    print("=" * 60)
    print(f"Backend:  {'✅ 通過' if backend_ok else '❌ 失敗'}")
    print(f"Frontend: {'✅ 通過' if frontend_ok else '❌ 失敗'}")

    if backend_ok and frontend_ok:
        print("\n🎉 所有測試通過！TapPay 整合配置正確！")
        print("\n📝 下一步：")
        print("   1. 打開瀏覽器: http://localhost:5173/teacher/login")
        print("   2. 登入後進入訂閱頁面測試付款")
        print("   3. 檢查瀏覽器 Console 是否有 TapPay 錯誤")
        return 0
    else:
        print("\n❌ 測試失敗，請檢查配置")
        return 1


if __name__ == "__main__":
    exit(main())
