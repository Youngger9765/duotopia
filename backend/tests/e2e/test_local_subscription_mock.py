"""
Playwright 測試：本地測試訂閱模擬功能
測試三個 demo 帳號的模擬充值功能（不經過 TapPay）
"""
import time
from playwright.sync_api import sync_playwright, Page

# Local API URL
LOCAL_API = "http://localhost:8080"

# 測試三個帳號
TEST_ACCOUNTS = [
    {"email": "demo@duotopia.com", "name": "Demo 老師"},
    {"email": "trial@duotopia.com", "name": "試用老師"},
    {"email": "expired@duotopia.com", "name": "過期老師"},
]


def test_get_status(page: Page, email: str):
    """測試查詢訂閱狀態"""
    print(f"\n📊 查詢 {email} 的訂閱狀態...")

    response = page.request.get(f"{LOCAL_API}/api/test/subscription/{email}/status")

    if response.status == 200:
        data = response.json()
        print(f"   ✅ 狀態: {data['status']}")
        print(f"   📅 剩餘天數: {data['days_remaining']} 天")
        print(f"   📆 到期日: {data.get('end_date', 'N/A')}")
        return data
    else:
        print(f"   ❌ 查詢失敗: {response.status}")
        print(f"   錯誤: {response.text()}")
        return None


def test_set_subscribed(page: Page, email: str):
    """測試設定為已訂閱（30天）"""
    print(f"\n✅ 設定 {email} 為已訂閱（30天）...")

    response = page.request.post(
        f"{LOCAL_API}/api/test/subscription/{email}/update",
        data={"action": "set_subscribed"},
    )

    if response.status == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   📊 新狀態: {data['status']['status']}")
        print(f"   📅 剩餘天數: {data['status']['days_remaining']} 天")
        return True
    else:
        print(f"   ❌ 操作失敗: {response.status}")
        return False


def test_set_expired(page: Page, email: str):
    """測試設定為未訂閱"""
    print(f"\n❌ 設定 {email} 為未訂閱...")

    response = page.request.post(
        f"{LOCAL_API}/api/test/subscription/{email}/update",
        data={"action": "set_expired"},
    )

    if response.status == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   📊 新狀態: {data['status']['status']}")
        print(f"   📅 剩餘天數: {data['status']['days_remaining']} 天")
        return True
    else:
        print(f"   ❌ 操作失敗: {response.status}")
        return False


def test_add_months(page: Page, email: str, months: int):
    """測試增加月數"""
    print(f"\n➕ 為 {email} 增加 {months} 個月...")

    response = page.request.post(
        f"{LOCAL_API}/api/test/subscription/{email}/update",
        data={"action": "add_months", "months": months},
    )

    if response.status == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   📊 新狀態: {data['status']['status']}")
        print(f"   📅 剩餘天數: {data['status']['days_remaining']} 天")
        return True
    else:
        print(f"   ❌ 操作失敗: {response.status}")
        return False


def test_reset_to_new(page: Page, email: str):
    """測試重置為新帳號（30天試用）"""
    print(f"\n🔄 重置 {email} 為新帳號（30天試用）...")

    response = page.request.post(
        f"{LOCAL_API}/api/test/subscription/{email}/update",
        data={"action": "reset_to_new"},
    )

    if response.status == 200:
        data = response.json()
        print(f"   ✅ {data['message']}")
        print(f"   📊 新狀態: {data['status']['status']}")
        print(f"   📅 剩餘天數: {data['status']['days_remaining']} 天")
        return True
    else:
        print(f"   ❌ 操作失敗: {response.status}")
        return False


def run_tests():
    """執行所有測試"""
    print("\n" + "=" * 70)
    print("🧪 Playwright 測試 - 本地訂閱模擬功能")
    print("=" * 70)
    print(f"API Endpoint: {LOCAL_API}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        results = []

        try:
            # 測試每個帳號
            for account in TEST_ACCOUNTS:
                email = account["email"]
                name = account["name"]

                print(f"\n{'=' * 70}")
                print(f"🧑‍🏫 測試帳號: {name} ({email})")
                print("=" * 70)

                # 1. 查詢初始狀態
                initial_status = test_get_status(page, email)
                results.append(("查詢狀態", initial_status is not None))

                # 2. 設定為已訂閱
                success = test_set_subscribed(page, email)
                results.append(("設定已訂閱", success))
                time.sleep(0.5)

                # 3. 增加 3 個月
                success = test_add_months(page, email, 3)
                results.append(("增加月數", success))
                time.sleep(0.5)

                # 4. 設定為未訂閱
                success = test_set_expired(page, email)
                results.append(("設定未訂閱", success))
                time.sleep(0.5)

                # 5. 重置為新帳號
                success = test_reset_to_new(page, email)
                results.append(("重置新帳號", success))
                time.sleep(0.5)

                # 6. 查詢最終狀態
                final_status = test_get_status(page, email)
                results.append(("查詢最終狀態", final_status is not None))

                print("\n" + "-" * 70)

        except Exception as e:
            print(f"\n❌ 測試錯誤: {e}")
            import traceback

            traceback.print_exc()

        finally:
            browser.close()

        # 測試結果總結
        print("\n" + "=" * 70)
        print("📊 測試結果總結")
        print("=" * 70)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} - {test_name}")

        print("=" * 70)
        print(f"總計: {passed}/{total} 通過")

        if passed == total:
            print("🎉 所有測試通過！")
        else:
            print(f"⚠️  {total - passed} 個測試失敗")

        print("=" * 70)


if __name__ == "__main__":
    run_tests()
