"""
Playwright E2E 測試：Staging Backend Payment Flow
使用 Demo 帳號測試完整流程
"""

import time
import uuid
from playwright.sync_api import sync_playwright, Page

# Staging URLs
STAGING_BACKEND_URL = "https://duotopia-staging-backend-316409492201.asia-east1.run.app"
STAGING_FRONTEND_URL = (
    "https://duotopia-staging-frontend-316409492201.asia-east1.run.app"
)

# Test 帳號
DEMO_EMAIL = "payment_test@duotopia.com"
DEMO_PASSWORD = "Test123456!"


def login_demo_teacher(page: Page) -> str:
    """登入 Demo 教師並返回 token"""
    print("\n1️⃣  登入 Demo 教師...")

    # 直接用 API 登入（不依賴前端頁面）
    response = page.request.post(
        f"{STAGING_BACKEND_URL}/api/auth/teacher/login",
        data={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )

    if response.status == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"   ✅ API 登入成功，token: {token[:20]}...")
        return token
    else:
        print(f"   ❌ API 登入失敗: {response.status}")
        print(f"   Response: {response.json()}")
        return None


def test_invalid_prime_token(page: Page, token: str) -> dict:
    """測試無效 Prime Token"""
    print("\n2️⃣  測試無效 Prime Token...")

    transaction_id = f"playwright_test_{uuid.uuid4().hex[:8]}"
    print(f"   Transaction ID: {transaction_id}")

    # 直接呼叫 payment API
    response = page.request.post(
        f"{STAGING_BACKEND_URL}/api/payment/process",
        headers={"Authorization": f"Bearer {token}"},
        data={
            "prime": f"playwright_invalid_prime_{transaction_id}",
            "amount": 230,
            "plan_name": "Tutor Teachers",
            "details": {"item_name": "Playwright E2E Test"},
            "cardholder": {"name": "Demo Teacher", "email": DEMO_EMAIL},
        },
    )

    print("\n3️⃣  API 回應:")
    print(f"   Status: {response.status}")

    if response.status == 200:
        data = response.json()
        print(f"   Success: {data.get('success')}")
        print(f"   Message: {data.get('message', '')[:150]}")

        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "response": data,
        }
    else:
        print(f"   Error: {response.text()}")
        return {
            "transaction_id": transaction_id,
            "status": "failed",
            "error": response.text(),
        }


def test_401_unauthenticated(page: Page) -> dict:
    """測試 401 未認證錯誤"""
    print("\n2️⃣  測試 401 未認證錯誤...")

    transaction_id = f"playwright_401_{uuid.uuid4().hex[:8]}"

    # 不帶 Authorization header
    response = page.request.post(
        f"{STAGING_BACKEND_URL}/api/payment/process",
        data={
            "prime": "test_prime",
            "amount": 230,
            "plan_name": "Test",
            "details": {"item_name": "Test"},
            "cardholder": {"name": "Test", "email": "test@example.com"},
        },
    )

    print("\n3️⃣  API 回應:")
    print(f"   Status: {response.status}")
    print(f"   Response: {response.json()}")

    if response.status == 401:
        print("   ✅ 401 測試通過")
        return {"transaction_id": transaction_id, "status": "pass", "expected": True}
    else:
        print("   ❌ 401 測試失敗")
        return {"transaction_id": transaction_id, "status": "fail", "expected": False}


def run_playwright_tests():
    """執行所有 Playwright 測試"""
    print("\n" + "=" * 70)
    print("🎭 Playwright E2E Tests - Staging Backend")
    print("=" * 70)
    print(f"Backend: {STAGING_BACKEND_URL}")
    print(f"Frontend: {STAGING_FRONTEND_URL}")
    print(f"Account: {DEMO_EMAIL}")
    print("=" * 70)

    with sync_playwright() as p:
        # 使用 headless mode
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        results = []

        try:
            # 測試 1: 401 未認證
            print("\n【測試 1】401 未認證錯誤")
            print("-" * 70)
            result_401 = test_401_unauthenticated(page)
            results.append(("401 Authentication", result_401))

            # 測試 2: 登入 + 無效 Prime Token
            print("\n【測試 2】登入 + 無效 Prime Token")
            print("-" * 70)
            token = login_demo_teacher(page)

            if token:
                result_prime = test_invalid_prime_token(page, token)
                results.append(("Invalid Prime Token", result_prime))

                print("\n4️⃣  等待 BigQuery 記錄（10秒）...")
                time.sleep(10)

                print("\n✅ Playwright 測試完成！")
                print("\n📊 請查詢 BigQuery 驗證記錄:")
                print("-" * 70)
                print(
                    f"""
bq query --use_legacy_sql=false '
SELECT
  transaction_id,
  timestamp,
  environment,
  status,
  error_stage,
  error_code,
  user_email,
  amount
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE transaction_id = "{result_prime['transaction_id']}"
  OR user_email = "{DEMO_EMAIL}"
ORDER BY timestamp DESC
LIMIT 5;
'
                """
                )
            else:
                print("   ❌ 無法登入，跳過 Prime Token 測試")
                results.append(
                    (
                        "Invalid Prime Token",
                        {"status": "skipped", "reason": "Login failed"},
                    )
                )

        except Exception as e:
            print(f"\n❌ 測試錯誤: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()

        # 輸出測試結果
        print("\n" + "=" * 70)
        print("📊 測試結果總結")
        print("=" * 70)
        for test_name, result in results:
            status = result.get("status", "unknown")
            if status == "pass" or status == "completed":
                print(f"✅ {test_name}: {status}")
            elif status == "skipped":
                print(f"⚠️  {test_name}: {status} ({result.get('reason', '')})")
            else:
                print(f"❌ {test_name}: {status}")
        print("=" * 70)


if __name__ == "__main__":
    run_playwright_tests()
