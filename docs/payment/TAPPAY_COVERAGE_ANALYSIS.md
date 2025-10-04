# TapPay 責任分工分析

## 🎯 TapPay 幫我們 Cover 的部分

### ✅ **1. 信用卡資料安全（最重要）**
```
TapPay 處理：
├─ 信用卡號加密傳輸
├─ CVV 驗證（不存儲）
├─ 3D Secure 驗證
├─ PCI DSS Level 1 合規
└─ Tokenization（卡號轉 token）
```

### ✅ **2. 支付處理**
```
TapPay 處理：
├─ 與銀行溝通授權
├─ 交易狀態管理（授權/請款/退款）
├─ 風險控管（盜刷偵測）
├─ 多銀行串接
└─ 交易加密
```

### ✅ **3. TapPay 會回傳的資料**
```json
{
  "status": 0,                    // 交易狀態碼
  "msg": "Success",               // 訊息
  "rec_trade_id": "D20241004xxxx", // TapPay 交易編號（重要！要存）
  "bank_transaction_id": "TP2024xxxx", // 銀行端交易編號
  "bank_result_code": "00",       // 銀行回應碼
  "bank_result_msg": "Success",   // 銀行回應訊息
  "auth_code": "123456",          // 授權碼（重要！要存）
  "card_info": {
    "bin_code": "424242",        // 卡號前6碼
    "last_four": "4242",         // 卡號後4碼（可存）
    "card_type": 1,              // 卡片類型
    "funding": 0,                // 信用卡/簽帳卡
    "issuer": "台灣銀行"         // 發卡銀行
  },
  "transaction_time_millis": 1628000000, // 交易時間
  "card_key": "xxx",             // 定期扣款用（選擇性存儲）
  "card_token": "xxx"            // 定期扣款用（選擇性存儲）
}
```

## ⚠️ **TapPay 可選服務（需額外申請）**

### 1. **台灣發票系統** 🧾
```
TapPay 提供電子發票整合服務：
├─ 整合多家電子發票服務商
├─ 統一 API 介面
├─ 自動開立發票
├─ 發票查詢與管理
└─ 發票作廢/折讓

我們仍需處理：
├─ 統一編號收集與驗證
├─ 選擇是否啟用 TapPay 發票服務
├─ 營業稅申報
└─ 發票資料備份
```

**注意**：TapPay 電子發票為加值服務，需要：
1. 額外申請開通
2. 可能有額外費用
3. 需要提供營業人資料

### 2. **訂閱管理** 📅
```
我們要處理：
├─ 訂閱週期計算
├─ 到期提醒
├─ 自動續訂邏輯
├─ 方案升降級
└─ 使用量限制
```

### 3. **交易記錄與稽核** 📊
```
我們要處理：
├─ 完整交易歷史
├─ 用戶付款記錄
├─ 退款追蹤
├─ 財務報表
├─ 稽核日誌
└─ 異常監控
```

### 4. **用戶體驗** 🎨
```
我們要處理：
├─ 付款成功/失敗頁面
├─ Email 通知
├─ 付款收據
├─ 訂閱狀態顯示
└─ 客服系統
```

## 📝 **必須存儲的 TapPay 資料**

### 🔴 **必存（查詢與對帳用）**
```sql
-- 這些一定要存在我們資料庫
rec_trade_id         -- TapPay 交易編號（最重要！）
auth_code           -- 授權碼（退款需要）
bank_transaction_id -- 銀行交易編號
transaction_time    -- 交易時間
amount              -- 金額
status              -- 狀態
```

### 🟡 **選存（提升體驗）**
```sql
-- 這些可以存，但非必要
card_last_four      -- 卡號後4碼（顯示用）
card_type          -- 卡片類型
issuer             -- 發卡銀行
bank_result_code   -- 銀行回應碼
bank_result_msg    -- 銀行回應訊息
```

### 🟢 **定期扣款才需要**
```sql
-- 只有做定期扣款才需要存
card_key           -- 卡片金鑰
card_token         -- 卡片 token
```

## 🔍 **查詢 TapPay 交易的方式**

### 1. **使用 rec_trade_id 查詢**
```python
# 可以用 rec_trade_id 查詢交易狀態
def query_tappay_transaction(rec_trade_id: str):
    """
    使用 TapPay API 查詢交易
    GET https://sandbox.tappaysdk.com/tpc/transaction/query
    """
    response = requests.post(
        "https://sandbox.tappaysdk.com/tpc/transaction/query",
        headers={
            "x-api-key": TAPPAY_PARTNER_KEY,
            "Content-Type": "application/json"
        },
        json={
            "partner_key": TAPPAY_PARTNER_KEY,
            "rec_trade_id": rec_trade_id
        }
    )
    return response.json()
```

### 2. **TapPay Portal 查詢**
- 登入 TapPay 後台
- 可查詢所有交易記錄
- 可下載對帳單

## 💡 **架構建議**

### Phase 1: MVP（現在）
```python
# 最小必要存儲
transaction_data = {
    "external_transaction_id": rec_trade_id,  # TapPay ID
    "gateway_response": {                     # 完整回應
        "auth_code": auth_code,
        "bank_transaction_id": bank_id,
        "card_last_four": last_four
    },
    "amount": amount,
    "status": "SUCCESS"
}
```

### Phase 2: 完整版
```python
# 加入更多資訊
transaction_data = {
    # ... 上面的資料
    "payment_provider": "tappay",
    "payment_method": "credit_card",
    "ip_address": request.client_ip,
    "user_agent": request.user_agent,
    "idempotency_key": unique_key,
    # 發票相關
    "invoice_data": {
        "buyer_tax_id": tax_id,
        "invoice_number": None,  # 開立後補上
        "invoice_status": "PENDING"
    }
}
```

## 🎯 **結論**

### TapPay 負責：
✅ 信用卡安全（PCI DSS）
✅ 銀行授權與請款
✅ 基本交易處理
⚠️ 電子發票（需額外申請）

### 我們必須負責：
❌ 訂閱邏輯
❌ 交易記錄
❌ 用戶通知
❌ 統編驗證
⚠️ 決定是否使用 TapPay 發票服務

### 存儲策略：
1. **必存 rec_trade_id** - 這是查詢的 key
2. **完整 response 存 JSON** - gateway_response 欄位
3. **發票資料另外處理** - 跟 TapPay 無關

**重點：**
1. **TapPay 核心是金流處理，發票是加值服務**
2. **電子發票需要額外申請與費用**
3. **可以選擇：**
   - 使用 TapPay 發票服務（整合方便）
   - 直接串接綠界/藍新等發票商（可能較便宜）
   - 初期手動開發票（省成本）