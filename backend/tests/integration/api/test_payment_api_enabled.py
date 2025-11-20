"""
測試 Payment API 在 ENABLE_PAYMENT=true 時的行為
"""
import os

# 設定測試環境變數（必須在 import main 之前）
os.environ["ENABLE_PAYMENT"] = "true"
os.environ["ENVIRONMENT"] = "staging"

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402
from models import Teacher  # noqa: E402
from auth import get_password_hash  # noqa: E402
from database import get_session_local  # noqa: E402

client = TestClient(app)


def setup_test_teacher():
    """創建測試教師帳號"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # 清理舊的測試帳號
        db.query(Teacher).filter(
            Teacher.email == "payment_enabled_test@duotopia.com"
        ).delete()
        db.commit()

        # 創建新的測試教師
        teacher = Teacher(
            email="payment_enabled_test@duotopia.com",
            name="Payment Enabled Test Teacher",
            password_hash=get_password_hash("Test123456!"),
            is_active=True,
            email_verified=True,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
        return teacher
    finally:
        db.close()


def login_teacher():
    """登入並獲取 token"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": "payment_enabled_test@duotopia.com", "password": "Test123456!"},
    )

    if response.status_code != 200:
        print(f"❌ 登入失敗: {response.status_code}")
        print(response.json())
        return None

    data = response.json()
    return data.get("access_token")


def test_payment_enabled():
    """測試付款功能啟用"""
    print("=" * 70)
    print("🧪 測試: Payment API (ENABLE_PAYMENT=true)")
    print("=" * 70)
    print()

    # 1. 設置測試教師
    print("1️⃣ 創建測試教師帳號...")
    teacher = setup_test_teacher()
    print(f"   ✅ 教師創建成功: {teacher.email}")
    print()

    # 2. 登入
    print("2️⃣ 登入教師帳號...")
    token = login_teacher()
    if not token:
        print("   ❌ 無法取得 token，測試中止")
        return
    print(f"   ✅ 登入成功，token: {token[:20]}...")
    print()

    # 3. 測試付款 API
    print("3️⃣ 測試付款 API (ENABLE_PAYMENT=true)...")
    payment_data = {
        "prime": "test_prime_token_12345_invalid",  # 故意用無效 prime 測試
        "amount": 230,
        "plan_name": "Tutor Teachers",
        "details": {"item_name": "Duotopia Tutor Teachers"},
        "cardholder": {
            "name": "Test User",
            "email": "payment_enabled_test@duotopia.com",
        },
    }

    response = client.post(
        "/api/payment/process",
        json=payment_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"   HTTP Status: {response.status_code}")
    print()

    # 4. 驗證回應
    if response.status_code == 200:
        data = response.json()
        print("   📦 API 回應:")
        print(f"      - success: {data.get('success')}")
        print(f"      - message: {data.get('message')}")
        print()

        # 當 ENABLE_PAYMENT=true 時，應該會嘗試呼叫 TapPay
        # 因為我們用的是無效的 prime token，應該會失敗（這是預期的）
        if data.get("success") is False:
            # 檢查是否為免費優惠期訊息
            if "免費優惠期間" in data.get("message", ""):
                print("   ❌ 測試失敗！")
                print("   ❌ ENABLE_PAYMENT=true 但仍然返回免費優惠期訊息")
            else:
                print("   ✅ 測試通過！")
                print("   ✅ Payment API 嘗試處理付款（如預期失敗，因為使用無效 prime）")
                print(f"   ℹ️  失敗原因: {data.get('message')}")
        else:
            print("   ⚠️  付款成功（不太可能，因為使用測試 prime）")
            print("   ⚠️  請檢查 TapPay 配置")
    else:
        print(f"   ❌ API 返回錯誤: {response.status_code}")
        print(f"   {response.json()}")

    print()
    print("=" * 70)
    print("✅ 測試完成")
    print("=" * 70)


if __name__ == "__main__":
    test_payment_enabled()
