"""
TapPay 電子發票 API 連線測試腳本

執行方式: python backend/test_einvoice_api.py
"""

import requests
import os
import sys
from dotenv import load_dotenv

# 載入環境變數
load_dotenv("backend/.env.local")

partner_key = os.getenv("TAPPAY_PARTNER_KEY")
merchant_id = os.getenv("TAPPAY_MERCHANT_ID")

print("=" * 70)
print("🧪 TapPay 電子發票 API 連線測試")
print("=" * 70)
print("\n🔑 環境設定:")
print(f'  Partner Key: {partner_key[:30] if partner_key else "未設定"}...')
print(f"  Merchant ID: {merchant_id}")
print("  環境: Sandbox")

if not partner_key:
    print("\n❌ 錯誤: TAPPAY_PARTNER_KEY 未設定")
    sys.exit(1)

# ====== 測試 1: 基礎金流 API ======
print("\n" + "-" * 70)
print("📡 測試 1: 基礎金流 API (Transaction Query)")
print("-" * 70)

payment_url = "https://sandbox.tappaysdk.com/tpc/transaction/query"
payment_payload = {
    "partner_key": partner_key,
    "filters": {"order_number": "TEST_ORDER"},
}

try:
    response = requests.post(
        payment_url,
        json=payment_payload,
        headers={"x-api-key": partner_key, "Content-Type": "application/json"},
        timeout=10,
    )
    result = response.json()

    print(f"HTTP Status: {response.status_code}")
    print(f'TapPay Status: {result.get("status")}')
    print(f'Message: {result.get("msg")}')

    if response.status_code == 200:
        print("✅ 金流 API 連線正常")
    else:
        print("❌ 金流 API 連線失敗")

except Exception as e:
    print(f"❌ 連線失敗: {e}")

# ====== 測試 2: 電子發票 Issue API ======
print("\n" + "-" * 70)
print("📡 測試 2: 電子發票 Issue API")
print("-" * 70)

invoice_url = "https://sandbox.tappaysdk.com/tpc/einvoice/issue"
invoice_payload = {
    "partner_key": partner_key,
    "rec_trade_id": "TEST_TRADE_DUOTOPIA_001",
    # 買受人
    "buyer_email": "test@duotopia.com",
    "buyer_name": "",
    "buyer_tax_id": "",
    # 載具
    "carrier_type": "",
    "carrier_id": "",
    # 金額（1000元含稅）
    "sales_amount": 952,
    "tax_amount": 48,
    "total_amount": 1000,
    # 商品
    "items": [
        {
            "item_name": "Duotopia 訂閱服務測試",
            "item_count": 1,
            "item_price": 1000,
            "item_tax_type": "TAXED",
        }
    ],
    # 設定
    "issue_notify_email": "AUTO",
    "free_tax_sales_amount": 0,
    "zero_tax_sales_amount": 0,
    "invoice_type": "B2C",
}

try:
    response = requests.post(
        invoice_url,
        json=invoice_payload,
        headers={"x-api-key": partner_key, "Content-Type": "application/json"},
        timeout=10,
    )

    print(f"HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f'TapPay Status: {result.get("status")}')
        print(f'Message: {result.get("msg")}')

        if result.get("status") == 0:
            print("\n✅ 成功！電子發票 API 已啟用並可正常使用")
            print(f'   rec_invoice_id: {result.get("rec_invoice_id")}')
            print(f'   invoice_number: {result.get("invoice_number")}')
            print(f'   invoice_date: {result.get("invoice_date")}')
        else:
            print("\n⚠️  TapPay 回傳錯誤")
            print(f"   完整回應: {result}")
    elif response.status_code == 403:
        print(f"Response: {response.text}")
        print("\n❌ 電子發票服務未啟用 (HTTP 403)")
        print("\n建議動作:")
        print("  1. 確認 TapPay 後台是否已開通電子發票服務")
        print("  2. 檢查 Merchant ID 是否正確")
        print("  3. 聯繫 TapPay 客服確認啟用狀態")
        print("     - Email: support@cherri.tech")
        print(f"     - Merchant ID: {merchant_id}")
    else:
        print(f"Response: {response.text[:500]}")
        print(f"\n⚠️  未預期的 HTTP 狀態碼: {response.status_code}")

except Exception as e:
    print(f"❌ 連線失敗: {e}")
    import traceback

    traceback.print_exc()

# ====== 測試 3: 電子發票 Query API ======
print("\n" + "-" * 70)
print("📡 測試 3: 電子發票 Query API")
print("-" * 70)

query_url = "https://sandbox.tappaysdk.com/tpc/einvoice/query"
query_params = {"partner_key": partner_key, "rec_invoice_id": "TEST_INVOICE_ID"}

try:
    response = requests.get(
        query_url, params=query_params, headers={"x-api-key": partner_key}, timeout=10
    )

    print(f"HTTP Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f'TapPay Status: {result.get("status")}')
        print(f'Message: {result.get("msg")}')
        print("✅ Query API 可以連線")
    elif response.status_code == 403:
        print(f"Response: {response.text}")
        print("❌ Query API 也是 403 - 確認電子發票服務未啟用")
    else:
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"❌ 連線失敗: {e}")

# ====== 總結 ======
print("\n" + "=" * 70)
print("📋 測試總結")
print("=" * 70)
print("\n如果看到 HTTP 403 錯誤，請執行以下步驟：")
print("  1. 登入 TapPay Portal: https://portal.tappaysdk.com/")
print("  2. 檢查「電子發票」功能是否已啟用")
print("  3. 確認 Sandbox 環境的設定")
print("  4. 若未啟用，請聯繫 TapPay 客服申請開通")
print("=" * 70)
