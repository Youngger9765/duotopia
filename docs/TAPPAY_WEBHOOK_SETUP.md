# TapPay Webhook 設定指南

## 📋 概述

當客服人員在 TapPay Portal 後台手動退款時，我們的平台需要透過 Webhook 機制自動同步退款狀態。

## 🔧 Webhook 設定步驟

### 1. 登入 TapPay Portal

- **測試環境**: https://portal.tappaysdk.com/
- **正式環境**: https://portal.tappaysdk.com/

### 2. 設定 Webhook URL

導航至：**設定 > Webhook 通知**

設定以下 URL：

#### Staging 環境
```
https://duotopia-backend-staging-123456789.asia-east1.run.app/api/payment/webhook
```

#### Production 環境
```
https://duotopia-backend-prod-123456789.asia-east1.run.app/api/payment/webhook
```

### 3. 選擇通知事件

勾選以下事件類型：
- ✅ **付款成功** (Payment Success)
- ✅ **付款失敗** (Payment Failed)
- ✅ **退款** (Refund)
- ✅ **3D驗證** (3D Secure)

### 4. 測試 Webhook

在 TapPay Portal 使用「測試 Webhook」功能：

**測試資料範例**：
```json
{
  "rec_trade_id": "D20251020SKxuJI",
  "status": 0,
  "msg": "Success",
  "event": "refund",
  "is_refund": true,
  "refund_amount": 230,
  "original_amount": 230
}
```

**預期回應**：
```json
{
  "status": "success",
  "message": "Webhook processed"
}
```

## 🔐 安全機制

### Webhook 簽名驗證

每個 Webhook 請求都包含 `X-TapPay-Signature` header，我們的系統會驗證：

```python
# 使用 HMAC-SHA256 驗證
expected_signature = hmac.new(
    key=PARTNER_KEY.encode('utf-8'),
    msg=request_body,
    digestmod=hashlib.sha256
).hexdigest()

# Constant-time 比較防止 timing attack
is_valid = hmac.compare_digest(expected_signature, signature)
```

### 重試機制

TapPay 會在以下時間重試：
- 第1次：1分鐘後
- 第2次：2分鐘後
- 第3次：4分鐘後
- 第4次：8分鐘後
- 第5次：16分鐘後

如果5次都失敗，會發送通知郵件給技術聯絡人。

## 📊 退款處理流程

### 1. 客服在 TapPay Portal 執行退款

- 找到交易記錄
- 點擊「退款」按鈕
- 輸入退款金額（全額或部分）
- 確認退款

### 2. TapPay 發送 Webhook 通知

```json
{
  "rec_trade_id": "D20251020SKxuJI",
  "event": "refund",
  "status": 0,
  "msg": "Refund processed",
  "refund_amount": 230,
  "original_amount": 230,
  "is_refund": true
}
```

### 3. 我們的平台自動處理

#### 全額退款
- 更新交易狀態為 `REFUNDED`
- 扣除對應訂閱天數（月方案30天、季方案90天）

#### 部分退款
- 更新交易狀態為 `REFUNDED`
- 按比例扣除訂閱天數
- 例如：退款 115元（原230元）→ 扣除 15天

### 4. 用戶訂閱自動調整

```sql
-- 訂閱到期日自動調整
UPDATE teachers
SET subscription_end_date = subscription_end_date - INTERVAL '30 days'
WHERE id = ?
```

## 🧪 測試退款流程

### 使用測試帳號

```bash
# 1. 用 demo@duotopia.com 登入並付款
curl -X POST https://staging.duotopia.com/api/payment/process \
  -H "Authorization: Bearer <token>" \
  -d '{"prime": "...", "amount": 230, "plan_name": "月方案"}'

# 2. 記下 rec_trade_id

# 3. 在 TapPay Portal 手動退款

# 4. 檢查訂閱狀態
curl https://staging.duotopia.com/api/auth/me \
  -H "Authorization: Bearer <token>"
```

## 📝 監控與日誌

### Cloud Run 日誌查詢

```bash
gcloud logging read "resource.labels.service_name=duotopia-backend-staging AND textPayload=~'Webhook received'" --limit 50 --format json
```

### 查看退款處理記錄

```bash
gcloud logging read "resource.labels.service_name=duotopia-backend-staging AND textPayload=~'Processing refund'" --limit 50
```

### 警告監控

如果 Webhook 驗證失敗：
```bash
gcloud logging read "resource.labels.service_name=duotopia-backend-staging AND textPayload=~'Invalid webhook signature'" --limit 10
```

## ⚠️ 注意事項

### 1. Webhook URL 必須是 HTTPS
- ✅ `https://duotopia.com/api/payment/webhook`
- ❌ `http://duotopia.com/api/payment/webhook`

### 2. 回應必須是 200 OK
- Webhook handler 必須在 30 秒內回應
- 回應 HTTP 200 才算成功

### 3. 測試環境分離
- Sandbox 環境和 Production 環境使用不同的 Webhook URL
- 確保測試不會影響正式用戶

### 4. 退款時間
- 銀行退款需要 7-14 個工作天
- Webhook 通知是立即的（TapPay 處理完成）
- 訂閱調整立即生效

## 🆘 故障排除

### Webhook 未收到通知

1. **檢查 TapPay Portal 設定**
   - Webhook URL 是否正確
   - 事件類型是否勾選

2. **檢查 Cloud Run 日誌**
   ```bash
   gcloud logging read "resource.labels.service_name=duotopia-backend-staging" --limit 100
   ```

3. **測試 Webhook 端點**
   ```bash
   curl -X POST https://staging.duotopia.com/api/payment/webhook \
     -H "X-TapPay-Signature: test" \
     -d '{"rec_trade_id": "test", "status": 0}'
   ```

### Webhook 簽名驗證失敗

1. 確認 `TAPPAY_PARTNER_KEY` 環境變數正確
2. 檢查 request body 是否被修改（需要原始 bytes）
3. 查看日誌中的 expected vs actual signature

### 退款未同步到訂閱

1. 檢查交易記錄是否更新為 `REFUNDED`
2. 查看日誌確認訂閱天數計算
3. 確認 `subscription_end_date` 是否調整

## 📞 聯絡支援

- **TapPay 技術支援**: support@tappaysdk.com
- **文件**: https://docs.tappaysdk.com/
- **內部 Slack**: #duotopia-payment
