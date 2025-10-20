"""
測試 Staging Payment Flow + BigQuery 資料收集
"""
import requests
import json

# Staging API 端點
STAGING_API = "https://duotopia-staging-backend-316409492201.asia-east1.run.app"


def test_login():
    """測試登入"""
    print("=" * 70)
    print("1️⃣ 測試登入")
    print("=" * 70)

    response = requests.post(
        f"{STAGING_API}/api/auth/teacher/login",
        json={"email": "payment_test@duotopia.com", "password": "Test123456!"},
    )

    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("✅ 登入成功")
        print(f"Token: {data.get('access_token', '')[:30]}...")
        return data.get("access_token")
    else:
        print(f"❌ 登入失敗: {response.text}")
        return None


def test_payment(token):
    """測試付款流程"""
    print("\n" + "=" * 70)
    print("2️⃣ 測試付款流程")
    print("=" * 70)

    payment_data = {
        "prime": "test_prime_invalid_for_bigquery_logging",
        "amount": 230,
        "plan_name": "Tutor Teachers",
        "details": {"item_name": "Duotopia Tutor Teachers - Staging Test"},
        "cardholder": {
            "name": "BigQuery Test User",
            "email": "payment_test@duotopia.com",
        },
    }

    response = requests.post(
        f"{STAGING_API}/api/payment/process",
        json=payment_data,
        headers={"Authorization": f"Bearer {token}"},
    )

    print(f"Status: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json()


def main():
    """執行完整測試流程"""
    print("\n🧪 開始測試 Staging Payment Flow")
    print(f"📍 API Endpoint: {STAGING_API}\n")

    # Step 1: 登入
    token = test_login()
    if not token:
        print("\n❌ 無法繼續測試，登入失敗")
        return

    # Step 2: 測試付款
    result = test_payment(token)

    # Step 3: 結果分析
    print("\n" + "=" * 70)
    print("3️⃣ 測試結果分析")
    print("=" * 70)

    if result.get("success"):
        print("⚠️ 付款成功（不應該，因為使用測試 prime）")
    else:
        print("✅ 付款失敗（預期行為，使用無效 prime）")
        print(f"錯誤訊息: {result.get('message')}")

    print("\n📊 BigQuery 日誌記錄檢查：")
    print("請到 BigQuery 確認以下資料是否被記錄：")
    print("  - Table: duotopia_analytics.transaction_logs")
    print("  - 尋找最新的 transaction_id")
    print("  - 檢查 敏感資料是否正確遮蔽（prime, card_number, etc.）")
    print("  - 檢查 error_stage 欄位是否正確記錄")


if __name__ == "__main__":
    main()
