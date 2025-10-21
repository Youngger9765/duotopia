# TapPay 電子發票整合文件

> **最後更新**: 2025-10-21
> **文件版本**: 1.0
> **TapPay API 版本**: V1.4 (2025/02)

## 📋 目錄

1. [整合概述](#整合概述)
2. [TapPay 官方澄清事項](#tappay-官方澄清事項)
3. [完整流程圖](#完整流程圖)
4. [資料庫設計](#資料庫設計)
5. [API 整合規格](#api-整合規格)
6. [退款與發票處理邏輯](#退款與發票處理邏輯)
7. [定期定額訂閱](#定期定額訂閱)
8. [錯誤處理與 Notify](#錯誤處理與-notify)
9. [測試環境說明](#測試環境說明)
10. [上線檢查清單](#上線檢查清單)

---

## 整合概述

### 系統架構

```
Duotopia 平台
    ↓ (付款成功)
TapPay 金流 API
    ↓ (自動觸發)
TapPay 電子發票 API
    ↓ (自動處理)
雲端發票加值中心 (Cloud Mobile)
    ↓ (自動寄送)
用戶 Email 信箱
```

### 關鍵概念

- **TapPay 負責**: 金流處理、發票開立 API、發票資料儲存
- **雲端發票負責**: 發票上傳財政部、Email 自動寄送
- **我們負責**:
  - 呼叫 TapPay 發票 API
  - 儲存 `rec_invoice_id` 和 `invoice_number`
  - 處理退款時的發票作廢/折讓邏輯
  - 處理 Notify Webhook（發票異常時）

---

## TapPay 官方澄清事項

### 🟢 Q1: Sandbox 測試字軌

**問題**: Sandbox 環境是否已有預設測試字軌？還是需要先去雲端發票後台設定字軌才能測試？

**TapPay 回答**:
> 測試字軌有預設的，不需要自行增加，如果開立字軌不足，可以通知我們，會協助增加。

**結論**: ✅ Sandbox 可直接測試，不需事先設定字軌

---

### 🟡 Q2: Notify 測試

**問題**: Sandbox 環境如何測試 Notify 功能？有模擬錯誤情境的工具嗎？

**TapPay 回答**:
> 您說的是發票的Notify嗎？只有異常情況才會有Notify，目前沒有相關的測試。

**結論**: ⚠️ Notify 無法在 Sandbox 主動測試，只能等實際異常發生

**建議**:
- 實作 Notify Webhook 時做好 error handling
- 用 ngrok 或類似工具在本地測試 webhook 接收
- Production 上線後透過 logging 監控 Notify 事件

---

### 🔴 Q3: 付款與發票時序

**問題**: TapPay 金流付款成功後，建議立即開立發票？還是等入帳確認後再開？如果付款後發生退刷，建議如何處理發票？

**TapPay 回答**:
> 一般是付款完成就要開立發票，付款後有部分退款或者全額退款，
> 要看發票是當期還是跨期，
> **當期**：可作廢重開
> **跨期**：開立折讓

**結論**: ✅ 付款成功 → 立即開立發票

**退款處理邏輯**:
```python
# 退款時的發票處理邏輯
if 發票開立月份 == 當前月份:
    # 當期發票 → 作廢重開
    if 全額退款:
        作廢發票(rec_invoice_id)
    else:
        作廢發票(rec_invoice_id)
        重新開立發票(新金額)
else:
    # 跨期發票 → 開立折讓（不能作廢）
    開立折讓(rec_invoice_id, 退款金額)
```

---

### 🔵 Q4: 定期定額訂閱

**問題**: 定期定額的設定會是我們平台方自己定時扣款跟開發票，對嗎？還是這部分會有 TapPay 相關 API 可以設定？

**TapPay 回答**:
> 要由貴司一樣透過API觸發，因為定期定額，也是由貴司API 觸發。

**結論**: ✅ 我們需要自己實作定期扣款排程

**實作方式**:
```python
# 使用 Google Cloud Scheduler 或類似工具
# 每月固定時間觸發

@scheduler.task(cron="0 0 1 * *")  # 每月 1 號 00:00
async def monthly_subscription_charge():
    """處理月訂閱自動扣款"""

    # 1. 查詢需要續訂的用戶
    subscriptions = db.query(TeacherSubscription).filter(
        TeacherSubscription.subscription_end_date <= today + timedelta(days=7),
        TeacherSubscription.auto_renew == True
    ).all()

    for sub in subscriptions:
        # 2. 呼叫 TapPay Pay by Token API（定期扣款）
        payment_result = charge_by_token(
            card_key=sub.card_key,
            card_token=sub.card_token,
            amount=sub.plan_amount
        )

        # 3. 扣款成功 → 自動開立發票
        if payment_result.success:
            invoice_result = issue_invoice(
                rec_trade_id=payment_result.rec_trade_id,
                buyer_email=sub.teacher.email,
                amount=sub.plan_amount
            )

            # 4. 更新訂閱期限
            sub.subscription_end_date += timedelta(days=30)
```

---

## 完整流程圖

### 正常付款 + 開立發票流程

```
用戶選擇訂閱方案
    ↓
前端呼叫 TapPay.Pay() 取得 prime
    ↓
後端呼叫 TapPay Pay API
    ↓
TapPay 返回 rec_trade_id (付款成功)
    ↓
[關鍵] 立即呼叫 TapPay Issue Invoice API
    ↓
TapPay 返回 rec_invoice_id + invoice_number
    ↓
雲端發票自動寄送 Email 給用戶
    ↓
更新訂閱期限 + 儲存發票資訊
```

### 退款流程（當期 vs 跨期）

```
用戶申請退款
    ↓
檢查發票開立日期
    ↓
    ├─ 當期（同一個月）
    │   ↓
    │   呼叫 TapPay Void Invoice API（作廢）
    │   ↓
    │   如果是部分退款 → 重新開立新金額發票
    │
    └─ 跨期（不同月）
        ↓
        呼叫 TapPay Allowance API（折讓）
        ↓
        不需重新開立發票
```

---

## 資料庫設計

### 🔍 是否需要記錄發票狀態變更歷史？

根據 TapPay API 文件分析，**發票確實會有狀態變更**：

1. **Notify API 機制**（Section 3.1）
   - 當加值中心上傳財政部後發生異常，TapPay 會主動發送 Notify
   - 可能情境：開立成功 → 上傳財政部失敗 → 狀態變更
   - **重要**：需要記錄這些異常通知！

2. **發票可能的狀態變化**
   ```
   PENDING (待開立)
     ↓
   ISSUED (已開立) ← 開立成功
     ↓
   ├─ VOIDED (已作廢) ← 當期作廢
   ├─ ALLOWANCED (已折讓) ← 跨期退款
   ├─ REISSUED (已註銷重開) ← 修正資訊
   └─ ERROR (異常) ← Notify 通知異常
   ```

### 方案：在現有 table 新增欄位 + 新增狀態歷史 table

#### 主表 (teacher_subscription_transactions)

```sql
-- Migration: Add E-Invoice fields to teacher_subscription_transactions
ALTER TABLE teacher_subscription_transactions ADD COLUMN
    -- 發票核心資訊
    rec_invoice_id VARCHAR(30),           -- TapPay 發票 ID（查詢/作廢/折讓用）
    invoice_number VARCHAR(10),            -- 發票號碼（顯示給用戶）
    invoice_status VARCHAR(20) DEFAULT 'PENDING',  -- 當前狀態
    invoice_issued_at TIMESTAMP,           -- 發票開立時間（判斷當期/跨期用）

    -- 買受人資訊（台灣法規需求）
    buyer_tax_id VARCHAR(8),               -- 統一編號（B2B 需要）
    buyer_name VARCHAR(100),               -- 買受人名稱（B2B 需要）
    buyer_email VARCHAR(255) NOT NULL,     -- 發票寄送 Email（必填）

    -- 載具資訊（B2C）
    carrier_type VARCHAR(10),              -- 載具類型（如: 3J0002=手機條碼）
    carrier_id VARCHAR(64),                -- 載具號碼

    -- 完整發票回應（備查/Debug 用）
    invoice_response JSONB;
```

#### 狀態歷史 table (invoice_status_history)

```sql
-- 發票狀態變更歷史（稽核與追蹤用）
CREATE TABLE invoice_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transaction_id UUID NOT NULL REFERENCES teacher_subscription_transactions(id) ON DELETE CASCADE,

    -- 狀態變更
    from_status VARCHAR(20),               -- 原始狀態
    to_status VARCHAR(20) NOT NULL,        -- 新狀態

    -- 變更原因
    action_type VARCHAR(20) NOT NULL,      -- ISSUE/VOID/ALLOWANCE/REISSUE/NOTIFY
    reason TEXT,                           -- 變更原因（退款/錯誤/異常等）

    -- Notify 相關（Section 3.1）
    is_notify BOOLEAN DEFAULT FALSE,       -- 是否為 Notify 觸發
    notify_error_code VARCHAR(20),         -- Notify 錯誤代碼
    notify_error_msg TEXT,                 -- Notify 錯誤訊息

    -- 完整資料
    request_payload JSONB,                 -- 請求資料
    response_payload JSONB,                -- 回應資料

    -- 時間戳記
    created_at TIMESTAMP DEFAULT NOW(),

    -- 索引
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_created_at (created_at DESC)
);
```

### 為什麼需要 invoice_status_history table？

1. ✅ **符合法規稽核需求** - 台灣電子發票需保留 7 年完整記錄
2. ✅ **追蹤 Notify 異常** - 記錄 TapPay 主動通知的發票狀態變更
3. ✅ **支援退款流程** - 清楚記錄作廢/折讓的完整歷程
4. ✅ **客服查詢** - 當用戶反應發票問題時，可查詢完整歷史
5. ✅ **偵測異常** - 監控是否有大量發票開立失敗

### 為什麼不把所有資料都放在 invoices table？

1. ✅ **一對一關係** - 每筆交易只對應一張發票（當前狀態）
2. ✅ **簡化查詢** - 不需要 JOIN 就能查到發票狀態
3. ✅ **減少維護成本** - 主表只記錄當前狀態，歷史另外存
4. ✅ **符合現有設計** - `payment_response` 也是 JSONB 存在同一 table

---

## API 整合規格

### 1. 開立發票 (Issue Invoice)

**時機**: 付款成功後立即呼叫

```python
import httpx
from datetime import datetime

async def issue_invoice(
    rec_trade_id: str,       # TapPay 付款交易 ID
    buyer_email: str,        # 買受人 Email（必填）
    amount: int,             # 金額（含稅）
    buyer_tax_id: str = None,  # 統一編號（B2B 必填）
    buyer_name: str = None,    # 買受人名稱（B2B 必填）
    carrier_type: str = None,  # 載具類型（B2C）
    carrier_id: str = None     # 載具號碼（B2C）
):
    """開立電子發票"""

    url = "https://prod.tappaysdk.com/tpc/einvoice/issue"  # Production
    # url = "https://sandbox.tappaysdk.com/tpc/einvoice/issue"  # Sandbox

    # 計算稅額（內含稅 5%）
    tax_amount = round(amount * 5 / 105)
    sales_amount = amount - tax_amount

    payload = {
        "partner_key": TAPPAY_PARTNER_KEY,
        "rec_trade_id": rec_trade_id,

        # 買受人資訊
        "buyer_email": buyer_email,
        "buyer_tax_id": buyer_tax_id or "",       # B2B 必填
        "buyer_name": buyer_name or "",           # B2B 必填

        # 載具資訊（B2C）
        "carrier_type": carrier_type or "",
        "carrier_id": carrier_id or "",

        # 金額資訊
        "sales_amount": sales_amount,             # 未稅金額
        "tax_amount": tax_amount,                 # 稅額
        "total_amount": amount,                   # 總金額

        # 發票明細
        "items": [
            {
                "item_name": "Duotopia 訂閱方案",
                "item_count": 1,
                "item_price": amount,
                "item_tax_type": "TAXED"          # 應稅
            }
        ],

        # 自動寄送發票
        "issue_notify_email": "AUTO",

        # 2025/6 後必填（提前加入）
        "free_tax_sales_amount": 0,
        "zero_tax_sales_amount": 0,
        "invoice_type": "B2C" if not buyer_tax_id else "B2B"
    }

    headers = {
        "x-api-key": TAPPAY_PARTNER_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()

        if result.get("status") == 0:
            # 成功
            return {
                "success": True,
                "rec_invoice_id": result["rec_invoice_id"],  # 重要！儲存此 ID
                "invoice_number": result["invoice_number"],
                "invoice_date": result["invoice_date"]
            }
        else:
            # 失敗
            raise Exception(f"開立發票失敗: {result.get('msg')}")
```

---

### 2. 作廢發票 (Void Invoice)

**時機**: 當期全額退款 或 當期部分退款（作廢後重開）

```python
async def void_invoice(rec_invoice_id: str, reason: str = "訂單取消"):
    """作廢發票（只能作廢當期發票）"""

    url = "https://prod.tappaysdk.com/tpc/einvoice/void"

    payload = {
        "partner_key": TAPPAY_PARTNER_KEY,
        "rec_invoice_id": rec_invoice_id,
        "void_reason": reason
    }

    headers = {
        "x-api-key": TAPPAY_PARTNER_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()

        if result.get("status") != 0:
            raise Exception(f"作廢發票失敗: {result.get('msg')}")

        return {"success": True, "msg": result.get("msg")}
```

---

### 3. 開立折讓 (Allowance)

**時機**: 跨期退款（不能作廢，只能折讓）

```python
async def issue_allowance(
    rec_invoice_id: str,
    allowance_amount: int,  # 折讓金額
    reason: str = "部分退款"
):
    """開立折讓（跨期退款使用）"""

    url = "https://prod.tappaysdk.com/tpc/einvoice/allowance"

    # 計算折讓稅額
    allowance_tax = round(allowance_amount * 5 / 105)
    allowance_sales = allowance_amount - allowance_tax

    payload = {
        "partner_key": TAPPAY_PARTNER_KEY,
        "rec_invoice_id": rec_invoice_id,

        # 折讓金額
        "allowance_sales_amount": allowance_sales,   # 未稅金額
        "allowance_tax_amount": allowance_tax,       # 稅額
        "allowance_total_amount": allowance_amount,  # 總金額

        # 折讓原因
        "allowance_reason": reason,

        # 折讓明細
        "items": [
            {
                "item_name": "訂閱方案部分退款",
                "item_count": 1,
                "item_price": allowance_amount,
                "item_tax_type": "TAXED"
            }
        ]
    }

    headers = {
        "x-api-key": TAPPAY_PARTNER_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()

        if result.get("status") != 0:
            raise Exception(f"開立折讓失敗: {result.get('msg')}")

        return {
            "success": True,
            "rec_allowance_id": result["rec_allowance_id"],
            "allowance_number": result["allowance_number"]
        }
```

---

### 4. 查詢發票 (Query Invoice)

**時機**: 用戶查詢發票詳情、客服查詢

```python
async def query_invoice(rec_invoice_id: str):
    """查詢發票詳細資訊"""

    url = "https://prod.tappaysdk.com/tpc/einvoice/query"

    payload = {
        "partner_key": TAPPAY_PARTNER_KEY,
        "rec_invoice_id": rec_invoice_id
    }

    headers = {
        "x-api-key": TAPPAY_PARTNER_KEY,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        result = response.json()

        if result.get("status") != 0:
            raise Exception(f"查詢發票失敗: {result.get('msg')}")

        return result  # 完整發票資訊
```

---

## 退款與發票處理邏輯

### 完整退款處理流程

```python
from datetime import datetime

async def process_refund(
    transaction_id: str,
    refund_amount: int,
    reason: str = "用戶申請退款"
):
    """處理退款 + 發票作廢/折讓"""

    # 1. 查詢交易記錄
    transaction = db.query(TeacherSubscriptionTransaction).filter_by(
        id=transaction_id
    ).first()

    if not transaction or not transaction.rec_invoice_id:
        raise Exception("找不到交易或發票記錄")

    # 2. 呼叫 TapPay Refund API
    refund_result = await refund_payment(
        rec_trade_id=transaction.external_transaction_id,
        refund_amount=refund_amount
    )

    if not refund_result["success"]:
        raise Exception("退款失敗")

    # 3. 判斷發票處理方式
    invoice_date = transaction.invoice_issued_at
    current_month = datetime.now().strftime("%Y-%m")
    invoice_month = invoice_date.strftime("%Y-%m")

    is_same_period = (current_month == invoice_month)
    is_full_refund = (refund_amount == transaction.amount)

    if is_same_period:
        # 當期發票 → 作廢
        await void_invoice(
            rec_invoice_id=transaction.rec_invoice_id,
            reason=reason
        )

        transaction.invoice_status = "VOIDED"

        # 部分退款需要重新開立新金額發票
        if not is_full_refund:
            new_amount = transaction.amount - refund_amount
            new_invoice = await issue_invoice(
                rec_trade_id=transaction.external_transaction_id,
                buyer_email=transaction.buyer_email,
                amount=new_amount,
                buyer_tax_id=transaction.buyer_tax_id,
                buyer_name=transaction.buyer_name
            )

            transaction.rec_invoice_id = new_invoice["rec_invoice_id"]
            transaction.invoice_number = new_invoice["invoice_number"]
            transaction.invoice_status = "ISSUED"

    else:
        # 跨期發票 → 開立折讓
        allowance_result = await issue_allowance(
            rec_invoice_id=transaction.rec_invoice_id,
            allowance_amount=refund_amount,
            reason=reason
        )

        transaction.invoice_status = "ALLOWANCED"

        # 儲存折讓資訊到 invoice_response
        if not transaction.invoice_response:
            transaction.invoice_response = {}
        transaction.invoice_response["allowances"] = [
            allowance_result
        ]

    # 4. 更新交易記錄
    transaction.refunded_amount = refund_amount
    transaction.refund_status = "completed"
    db.commit()

    # 5. 寄送退款通知 Email
    await send_refund_notification(
        teacher_email=transaction.teacher.email,
        refund_amount=refund_amount,
        invoice_handling="作廢" if is_same_period else "開立折讓"
    )

    return {
        "success": True,
        "refund_amount": refund_amount,
        "invoice_action": "void" if is_same_period else "allowance"
    }
```

---

## 定期定額訂閱

### Cloud Scheduler 設定

```yaml
# cloud_scheduler.yaml
name: monthly-subscription-charge
schedule: "0 0 1 * *"  # 每月 1 號 00:00 執行
time_zone: Asia/Taipei
http_target:
  uri: https://duotopia-backend.run.app/api/cron/charge-subscriptions
  http_method: POST
  headers:
    X-Cron-Secret: ${CRON_SECRET}
```

### 定期扣款實作

```python
from fastapi import APIRouter, Header, HTTPException
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/api/cron/charge-subscriptions")
async def charge_monthly_subscriptions(
    x_cron_secret: str = Header(...)
):
    """每月自動扣款 + 開立發票"""

    # 驗證 Cron Secret
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")

    # 查詢需要續訂的用戶（訂閱即將到期 7 天內 + 啟用自動續訂）
    subscriptions = db.query(Teacher).filter(
        Teacher.subscription_end_date <= datetime.now() + timedelta(days=7),
        Teacher.subscription_end_date > datetime.now(),
        Teacher.auto_renew == True,
        Teacher.card_key.isnot(None)  # 有儲存付款方式
    ).all()

    results = {
        "total": len(subscriptions),
        "success": 0,
        "failed": 0,
        "errors": []
    }

    for teacher in subscriptions:
        try:
            # 1. 使用儲存的卡片資訊扣款（Pay by Token）
            payment_result = await charge_by_token(
                card_key=teacher.card_key,
                card_token=teacher.card_token,
                amount=teacher.subscription_plan_amount,
                order_number=f"DUOTOPIA_AUTO_{teacher.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )

            if not payment_result["success"]:
                raise Exception(f"扣款失敗: {payment_result.get('msg')}")

            # 2. 建立交易記錄
            transaction = TeacherSubscriptionTransaction(
                teacher_id=teacher.id,
                amount=teacher.subscription_plan_amount,
                transaction_type="SUBSCRIPTION_RENEWAL",
                status="SUCCESS",
                external_transaction_id=payment_result["rec_trade_id"],
                payment_response=payment_result
            )
            db.add(transaction)
            db.flush()

            # 3. 開立發票
            invoice_result = await issue_invoice(
                rec_trade_id=payment_result["rec_trade_id"],
                buyer_email=teacher.email,
                amount=teacher.subscription_plan_amount,
                buyer_tax_id=teacher.tax_id,
                buyer_name=teacher.company_name
            )

            # 4. 更新交易發票資訊
            transaction.rec_invoice_id = invoice_result["rec_invoice_id"]
            transaction.invoice_number = invoice_result["invoice_number"]
            transaction.invoice_status = "ISSUED"
            transaction.invoice_issued_at = datetime.now()
            transaction.buyer_email = teacher.email

            # 5. 延長訂閱期限
            if teacher.subscription_plan == "MONTHLY":
                teacher.subscription_end_date += timedelta(days=30)
            elif teacher.subscription_plan == "QUARTERLY":
                teacher.subscription_end_date += timedelta(days=90)
            elif teacher.subscription_plan == "YEARLY":
                teacher.subscription_end_date += timedelta(days=365)

            db.commit()

            # 6. 寄送續訂成功通知
            await send_renewal_success_email(
                teacher_email=teacher.email,
                amount=teacher.subscription_plan_amount,
                new_end_date=teacher.subscription_end_date,
                invoice_number=invoice_result["invoice_number"]
            )

            results["success"] += 1

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({
                "teacher_id": teacher.id,
                "error": str(e)
            })

            # 寄送續訂失敗通知
            await send_renewal_failed_email(
                teacher_email=teacher.email,
                reason=str(e)
            )

            db.rollback()

    # 記錄到 BigQuery
    await log_to_bigquery({
        "event_type": "monthly_subscription_charge",
        "timestamp": datetime.now().isoformat(),
        "results": results
    })

    return results
```

---

## 錯誤處理與 Notify

### Notify Webhook 處理

**TapPay 說明**: 只有異常情況才會觸發 Notify，會重試 3 次，每次間隔 10 分鐘，30 分鐘內完成

```python
@router.post("/api/einvoice/notify")
async def handle_invoice_notify(request: Request):
    """處理 TapPay 發票異常通知"""

    payload = await request.json()

    # 記錄所有 Notify（重要！因為無法在 Sandbox 測試）
    logger.error(f"收到 TapPay 發票 Notify: {payload}")

    # 解析 Notify 內容
    rec_invoice_id = payload.get("rec_invoice_id")
    error_msg = payload.get("msg")
    error_code = payload.get("status")

    # 查詢對應的交易
    transaction = db.query(TeacherSubscriptionTransaction).filter_by(
        rec_invoice_id=rec_invoice_id
    ).first()

    if not transaction:
        logger.error(f"找不到對應交易: rec_invoice_id={rec_invoice_id}")
        return {"status": "error", "msg": "Transaction not found"}

    # 更新發票狀態為錯誤
    transaction.invoice_status = "ERROR"
    if not transaction.invoice_response:
        transaction.invoice_response = {}
    transaction.invoice_response["notify_error"] = {
        "error_code": error_code,
        "error_msg": error_msg,
        "received_at": datetime.now().isoformat()
    }
    db.commit()

    # 記錄到 BigQuery
    await log_to_bigquery({
        "event_type": "invoice_notify_error",
        "rec_invoice_id": rec_invoice_id,
        "error_code": error_code,
        "error_msg": error_msg,
        "transaction_id": str(transaction.id)
    })

    # 發送告警給開發團隊
    await send_alert_to_slack(
        channel="#alerts",
        message=f"🚨 發票開立異常\n"
                f"rec_invoice_id: {rec_invoice_id}\n"
                f"錯誤: {error_msg}\n"
                f"交易 ID: {transaction.id}"
    )

    # 必須返回 200 讓 TapPay 知道我們收到了
    return {"status": "ok"}
```

---

## 測試環境說明

### Sandbox 環境

**Base URL**: `https://sandbox.tappaysdk.com`

**測試流程**:
1. ✅ 測試字軌已預設，可直接測試開立發票
2. ✅ 可測試作廢發票
3. ✅ 可測試開立折讓
4. ⚠️ Notify 無法主動測試（只能等異常發生）

**測試建議**:
```bash
# 使用 ngrok 測試本地 webhook
ngrok http 8080

# 在 TapPay 後台設定 Notify URL
https://xxxx.ngrok.io/api/einvoice/notify
```

### Production 環境

**Base URL**: `https://prod.tappaysdk.com`

**上線前檢查**:
- [ ] 已取得 Production `partner_key`（2025/10/21 後）
- [ ] 已在雲端發票後台完成設定
- [ ] Notify URL 已設定為正式網域
- [ ] 已測試完整流程（付款 → 開立發票 → 退款 → 作廢/折讓）

---

## 上線檢查清單

### 開發階段
- [ ] 實作 Issue Invoice API
- [ ] 實作 Void Invoice API
- [ ] 實作 Allowance API
- [ ] 實作 Query Invoice API
- [ ] 實作 Notify Webhook
- [ ] 資料庫 Migration 完成
- [ ] 單元測試覆蓋率 > 80%
- [ ] E2E 測試（付款 + 發票流程）

### 測試階段
- [ ] Sandbox 完整測試（開立/作廢/折讓/查詢）
- [ ] 測試當期退款（作廢重開）
- [ ] 測試跨期退款（折讓）
- [ ] 測試定期扣款排程
- [ ] 壓力測試（100 筆發票開立）

### 上線階段
- [ ] Production Partner Key 已取得
- [ ] 環境變數設定完成
- [ ] Notify URL 已設定
- [ ] BigQuery Logging 已啟用
- [ ] Slack 告警已設定
- [ ] 監控 Dashboard 已建立

### 合規階段
- [ ] 台灣電子發票法規檢查
- [ ] 統一編號驗證邏輯
- [ ] 個資保護措施
- [ ] 資料保留政策（至少 7 年）

---

## 參考資源

- **TapPay E-Invoice API 文件**: `docs/payment/電子發票Open_API規格_商戶_V1.4.pdf`
- **TapPay 後台操作手冊**: `docs/payment/TapPay後台 - E-invoice系統操作.pdf`
- **財政部電子發票整合服務平台**: https://www.einvoice.nat.gov.tw/
- **雲端發票**: https://www.cloud-mobile.com.tw/

---

**文件維護**: 本文件會隨 TapPay API 更新而更新，請定期檢查版本號。
