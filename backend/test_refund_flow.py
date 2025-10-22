"""
測試退款流程 (Refund Flow Test)

功能：
1. 模擬 TapPay webhook 發送退款通知
2. 測試全額退款和部分退款
3. 驗證訂閱天數扣除邏輯
4. 檢查 BigQuery 記錄和 Email 通知
"""
import requests
import json
from datetime import datetime

# API 端點設定
# LOCAL_API = "http://localhost:8080"
STAGING_API = "https://duotopia-staging-backend-316409492201.asia-east1.run.app"

# 選擇測試環境
API_URL = STAGING_API  # 改成 LOCAL_API 可測試本地


def test_full_refund_webhook():
    """
    測試全額退款 Webhook

    模擬 TapPay 發送全額退款通知
    """
    print("=" * 70)
    print("1️⃣ 測試全額退款 Webhook")
    print("=" * 70)

    # 模擬 TapPay 退款 webhook payload
    webhook_payload = {
        "rec_trade_id": "REFUND_TEST_001",  # 需要先有一筆交易記錄
        "event": "refund",
        "status": 0,  # 成功
        "msg": "退款成功",
        "is_refund": True,
        "refund_amount": 230,  # 全額退款 (月方案)
        "original_amount": 230,
        "bank_transaction_id": "BANK_REFUND_001",
        "order_number": "DUOTOPIA_TEST_001",
        "amount": 230,
        "currency": "TWD",
        "bank_result_code": "00",
        "bank_result_msg": "Success",
        "card_info": {
            "bin_code": "424242",
            "last_four": "4242",
            "issuer": "測試銀行",
            "type": 1,
            "funding": 0,
        },
        "refund_time": datetime.now().isoformat(),
    }

    print(f"📤 發送 Webhook 到: {API_URL}/api/payment/tappay-webhook")
    print("📋 Payload:")
    print(json.dumps(webhook_payload, indent=2, ensure_ascii=False))

    response = requests.post(
        f"{API_URL}/api/payment/tappay-webhook",
        json=webhook_payload,
    )

    print("\n📥 回應:")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json()


def test_partial_refund_webhook():
    """
    測試部分退款 Webhook

    模擬 TapPay 發送部分退款通知 (退一半)
    """
    print("\n" + "=" * 70)
    print("2️⃣ 測試部分退款 Webhook (50%)")
    print("=" * 70)

    webhook_payload = {
        "rec_trade_id": "REFUND_TEST_002",
        "event": "refund",
        "status": 0,
        "msg": "部分退款成功",
        "is_refund": True,
        "refund_amount": 115,  # 退一半 (230 / 2)
        "original_amount": 230,
        "bank_transaction_id": "BANK_REFUND_002",
        "order_number": "DUOTOPIA_TEST_002",
        "amount": 230,
        "currency": "TWD",
        "bank_result_code": "00",
        "bank_result_msg": "Success",
        "card_info": {
            "bin_code": "424242",
            "last_four": "4242",
            "issuer": "測試銀行",
            "type": 1,
            "funding": 0,
        },
        "refund_time": datetime.now().isoformat(),
    }

    print(f"📤 發送 Webhook 到: {API_URL}/api/payment/tappay-webhook")
    print("📋 Payload:")
    print(json.dumps(webhook_payload, indent=2, ensure_ascii=False))

    response = requests.post(
        f"{API_URL}/api/payment/tappay-webhook",
        json=webhook_payload,
    )

    print("\n📥 回應:")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

    return response.json()


def check_results(full_refund_result, partial_refund_result):
    """
    檢查測試結果
    """
    print("\n" + "=" * 70)
    print("3️⃣ 測試結果檢查")
    print("=" * 70)

    print("\n📊 全額退款結果:")
    if full_refund_result.get("status") == "success":
        print("  ✅ Webhook 處理成功")
        print(f"  📝 訊息: {full_refund_result.get('message')}")
    else:
        print(f"  ❌ 處理失敗: {full_refund_result.get('message')}")

    print("\n📊 部分退款結果:")
    if partial_refund_result.get("status") == "success":
        print("  ✅ Webhook 處理成功")
        print(f"  📝 訊息: {partial_refund_result.get('message')}")
    else:
        print(f"  ❌ 處理失敗: {partial_refund_result.get('message')}")

    print("\n" + "=" * 70)
    print("📋 資料庫檢查清單")
    print("=" * 70)
    print(
        """
請到資料庫確認：

1. TeacherSubscriptionTransaction 表格:
   - 原始交易的 status 是否更新為 'REFUNDED'
   - refunded_amount 是否正確記錄
   - refund_status 是否為 'completed'
   - 是否建立了新的 REFUND 類型交易記錄

2. Teacher 表格:
   - subscription_end_date 是否正確扣除天數
   - 全額退款: 扣除 30 天 (月方案) 或 90 天 (季方案)
   - 部分退款: 按比例扣除 (50% 退款 = 扣除 15 天)

3. BigQuery duotopia_analytics.transaction_logs:
   - 是否記錄了 REFUND 類型的交易
   - transaction_type = 'refund'
   - refund_amount 和 original_amount 是否正確
   - 敏感資料是否遮蔽

4. Email 通知:
   - 老師是否收到退款通知信
   - Email 內容是否包含退款金額和調整後的訂閱期限
"""
    )


def main():
    """
    執行完整退款測試流程
    """
    print("\n🧪 開始測試退款流程 (Refund Flow)")
    print(f"📍 API Endpoint: {API_URL}\n")

    print("⚠️  注意事項:")
    print("  1. 測試前請確保資料庫有對應的交易記錄 (rec_trade_id)")
    print("  2. 可以修改 webhook_payload 中的 rec_trade_id 為真實交易 ID")
    print("  3. 建議先在本地環境測試，再測 staging\n")

    input("按 Enter 繼續測試...")

    # 測試全額退款
    full_refund_result = test_full_refund_webhook()

    # 測試部分退款
    partial_refund_result = test_partial_refund_webhook()

    # 檢查結果
    check_results(full_refund_result, partial_refund_result)

    print("\n✅ 測試完成")


if __name__ == "__main__":
    main()
