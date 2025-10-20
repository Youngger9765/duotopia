# Payment Flow Test Cases

本文件列出所有需要測試的金流場景，確保每個 case 都能正確記錄到 BigQuery。

## 測試目標
- ✅ 每個 success case 都記錄到 BigQuery
- ✅ 每個 error case 都記錄錯誤階段、錯誤代碼、錯誤訊息
- ✅ 能從 BigQuery 查詢並分析每筆交易

---

## Success Cases

### S1. 完整付款流程成功
**描述**: 用戶從登入到完成付款的完整流程

**步驟**:
1. 教師登入
2. 進入訂閱頁面
3. 選擇方案
4. 填寫信用卡資訊（使用 TapPay 測試卡號）
5. 送出付款
6. 收到成功回應

**預期 BigQuery 記錄**:
```json
{
  "status": "success",
  "user_id": <teacher_id>,
  "user_email": "<teacher_email>",
  "amount": 230,
  "plan_name": "Tutor Teachers",
  "error_stage": null,
  "error_code": null,
  "tappay_rec_trade_id": "<rec_trade_id>",
  "execution_time_ms": <time>
}
```

---

## Error Cases

### E1. 未登入就嘗試付款（401 - Authentication Error）
**描述**: 用戶未登入就直接呼叫 payment API

**步驟**:
1. 不進行登入
2. 直接呼叫 `/api/payment/process`

**預期 BigQuery 記錄**:
```json
{
  "status": "failed",
  "error_stage": "authentication",
  "error_code": "401",
  "error_message": "Not authenticated",
  "user_id": null,
  "user_email": null
}
```

---

### E2. 無效的 Prime Token（400 - Prime Token Error）
**描述**: 前端成功取得 token，但 prime token 無效

**步驟**:
1. 教師登入
2. 呼叫 payment API，但提供無效的 prime token

**預期 BigQuery 記錄**:
```json
{
  "status": "failed",
  "error_stage": "prime_token",
  "error_code": "400",
  "error_message": "Invalid prime token",
  "user_id": <teacher_id>,
  "user_email": "<teacher_email>",
  "amount": 230,
  "plan_name": "Tutor Teachers"
}
```

---

### E3. TapPay API 錯誤（500 - TapPay API Error）
**描述**: Prime token 有效，但 TapPay API 返回錯誤

**步驟**:
1. 教師登入
2. 使用測試卡號產生 prime token
3. TapPay 返回錯誤（如餘額不足、卡片被拒等）

**預期 BigQuery 記錄**:
```json
{
  "status": "failed",
  "error_stage": "tappay_api",
  "error_code": "500",
  "error_message": "TapPay payment failed: <tappay_error_msg>",
  "user_id": <teacher_id>,
  "user_email": "<teacher_email>",
  "amount": 230,
  "tappay_response": {"status": 1, "msg": "..."}
}
```

---

### E4. 資料庫錯誤（500 - Database Error）
**描述**: TapPay 成功扣款，但儲存到資料庫時失敗

**步驟**:
1. Mock 資料庫連線失敗
2. 執行付款流程

**預期 BigQuery 記錄**:
```json
{
  "status": "failed",
  "error_stage": "database",
  "error_code": "500",
  "error_message": "Failed to save subscription to database",
  "tappay_rec_trade_id": "<rec_trade_id>"
}
```

---

### E5. 前端：TapPay SDK 初始化失敗
**描述**: TapPay SDK 載入失敗或初始化錯誤

**步驟**:
1. 進入付款頁面
2. TapPay SDK 初始化失敗

**預期 BigQuery 記錄** (透過 `/api/payment/log-frontend-error`):
```json
{
  "status": "failed",
  "error_stage": "frontend_sdk_init",
  "error_code": "SDK_INIT_FAILED",
  "error_message": "TapPay SDK initialization failed",
  "frontend_error": {...}
}
```

---

### E6. 前端：Prime Token 生成失敗
**描述**: 用戶填寫信用卡資料，但無法產生 prime token

**步驟**:
1. 教師登入
2. 填寫錯誤的信用卡資訊
3. 點擊付款按鈕
4. TapPay 無法產生 prime token

**預期 BigQuery 記錄** (透過 `/api/payment/log-frontend-error`):
```json
{
  "status": "failed",
  "error_stage": "frontend_prime_generation",
  "error_code": "PRIME_FAILED",
  "error_message": "Failed to get prime token from TapPay",
  "user_id": <teacher_id>,
  "user_email": "<teacher_email>"
}
```

---

### E7. 前端：API 請求失敗（網路錯誤）
**描述**: Prime token 成功產生，但 API 請求失敗

**步驟**:
1. 教師登入
2. 填寫信用卡資訊並產生 prime token
3. 呼叫 `/api/payment/process` 時網路中斷

**預期 BigQuery 記錄** (透過 `/api/payment/log-frontend-error`):
```json
{
  "status": "failed",
  "error_stage": "frontend_api_request",
  "error_code": "NETWORK_ERROR",
  "error_message": "Failed to call payment API",
  "user_id": <teacher_id>,
  "user_email": "<teacher_email>"
}
```

---

## Test Matrix Summary

| Case ID | Stage | Error Code | Should Log to BigQuery |
|---------|-------|------------|------------------------|
| S1 | - | - | ✅ Success record |
| E1 | authentication | 401 | ✅ Backend log |
| E2 | prime_token | 400 | ✅ Backend log |
| E3 | tappay_api | 500 | ✅ Backend log |
| E4 | database | 500 | ✅ Backend log |
| E5 | frontend_sdk_init | SDK_INIT_FAILED | ✅ Frontend log |
| E6 | frontend_prime_generation | PRIME_FAILED | ✅ Frontend log |
| E7 | frontend_api_request | NETWORK_ERROR | ✅ Frontend log |

---

## BigQuery 驗證查詢

### 查詢所有測試記錄
```sql
SELECT
  transaction_id,
  timestamp,
  status,
  error_stage,
  error_code,
  error_message,
  user_email,
  amount,
  plan_name
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE DATE(timestamp) = CURRENT_DATE()
  AND environment = 'staging'
ORDER BY timestamp DESC
LIMIT 20;
```

### 按錯誤階段分組統計
```sql
SELECT
  error_stage,
  error_code,
  COUNT(*) as count,
  ARRAY_AGG(DISTINCT error_message LIMIT 3) as sample_messages
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE status = 'failed'
  AND DATE(timestamp) = CURRENT_DATE()
GROUP BY error_stage, error_code
ORDER BY count DESC;
```

### 驗證成功交易
```sql
SELECT
  transaction_id,
  user_email,
  amount,
  plan_name,
  tappay_rec_trade_id,
  execution_time_ms
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE status = 'success'
  AND DATE(timestamp) = CURRENT_DATE()
ORDER BY timestamp DESC;
```

---

## 測試執行計畫

1. **E2E Playwright 測試** - 執行所有 success/error cases
2. **驗證 BigQuery** - 每個測試後查詢 BigQuery 確認資料
3. **資料完整性** - 確保所有欄位都正確記錄
4. **效能測試** - 確認 logging 不影響交易速度

---

**建立日期**: 2025-10-20
**測試環境**: staging
**BigQuery Dataset**: `duotopia_analytics.transaction_logs`
