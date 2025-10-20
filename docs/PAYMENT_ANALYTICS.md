# 金流資料收集系統

## 概述

完整的金流交易資料收集機制，將所有成功與失敗的交易資訊送到 Google BigQuery 進行分析。

## 架構

```
前端錯誤 → Backend API → BigQuery
後端處理 → Direct BigQuery Insert
```

## BigQuery Schema

### Dataset
- **Project**: `duotopia-472708`
- **Dataset**: `duotopia_analytics`
- **Table**: `transaction_logs`

### 資料表結構

```sql
- transaction_id STRING       -- 交易 ID
- timestamp TIMESTAMP         -- 時間戳記
- environment STRING          -- production, staging, local
- user_id INT64              -- 用戶 ID
- user_email STRING          -- 用戶 Email
- user_type STRING           -- teacher, student
- amount INT64               -- 金額
- plan_name STRING           -- 方案名稱
- status STRING              -- success, failed, pending
- error_stage STRING         -- 錯誤階段
- error_code STRING          -- 錯誤代碼
- error_message STRING       -- 錯誤訊息
- tappay_response JSON       -- TapPay 回應
- execution_time_ms INT64    -- 執行時間
- 等等...
```

## Views

### 1. 失敗交易分析 (`failed_transactions`)
```sql
SELECT * FROM `duotopia-472708.duotopia_analytics.failed_transactions`
WHERE date = CURRENT_DATE()
ORDER BY failure_count DESC;
```

查詢結果：
- 每日失敗次數統計
- 按錯誤階段分類
- 最近 5 筆失敗案例

### 2. 成功交易統計 (`successful_transactions`)
```sql
SELECT * FROM `duotopia-472708.duotopia_analytics.successful_transactions`
WHERE date = CURRENT_DATE();
```

查詢結果：
- 每日交易數量
- 總營收
- 獨立用戶數

### 3. 用戶交易歷史 (`user_transaction_history`)
```sql
SELECT * FROM `duotopia-472708.duotopia_analytics.user_transaction_history`
WHERE user_email = 'user@example.com';
```

查詢結果：
- 用戶所有交易嘗試
- 成功/失敗次數
- 最近 10 筆交易詳情

## 錯誤階段 (error_stage)

1. **authentication** - 認證失敗 (401)
2. **prime_token** - TapPay Prime Token 取得失敗
3. **tappay_api** - TapPay API 處理失敗
4. **database** - 資料庫錯誤
5. **validation** - 輸入驗證失敗
6. **unknown** - 未知錯誤

## 使用方式

### 後端自動記錄

所有付款 API 請求都會自動記錄到 BigQuery：

```python
# 成功交易
log_payment_success(
    transaction_id="TXN123",
    user_id=1,
    user_email="user@example.com",
    amount=230,
    plan_name="Tutor Teachers",
    tappay_response=response,
    tappay_rec_trade_id="REC123",
    execution_time_ms=1500,
)

# 失敗交易
log_payment_failure(
    transaction_id="TXN123",
    user_id=1,
    user_email="user@example.com",
    amount=230,
    plan_name="Tutor Teachers",
    error_stage="tappay_api",
    error_code="10021",
    error_message="Invalid arguments",
    execution_time_ms=500,
)
```

### 前端錯誤收集

```typescript
import { analyticsService } from "@/services/analyticsService";

// TapPay SDK 錯誤
analyticsService.logTapPayInitError("TapPay SDK not loaded");

// Prime Token 錯誤
analyticsService.logTapPayPrimeError(status, message);

// API 錯誤
analyticsService.logPaymentApiError(amount, planName, error);

// 認證錯誤
analyticsService.logAuthenticationError(amount, planName);
```

## 查詢範例

### 1. 查看今日失敗交易
```sql
SELECT
  error_stage,
  error_code,
  COUNT(*) as count,
  ARRAY_AGG(error_message LIMIT 5) as messages
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE DATE(timestamp) = CURRENT_DATE()
  AND status = 'failed'
GROUP BY error_stage, error_code
ORDER BY count DESC;
```

### 2. 查看特定用戶的交易
```sql
SELECT
  timestamp,
  status,
  amount,
  plan_name,
  error_stage,
  error_message
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE user_email = 'user@example.com'
ORDER BY timestamp DESC
LIMIT 10;
```

### 3. 成功率分析
```sql
SELECT
  DATE(timestamp) as date,
  COUNT(*) as total_attempts,
  COUNTIF(status = 'success') as successful,
  COUNTIF(status = 'failed') as failed,
  ROUND(COUNTIF(status = 'success') / COUNT(*) * 100, 2) as success_rate
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY date
ORDER BY date DESC;
```

### 4. 錯誤階段分佈
```sql
SELECT
  error_stage,
  COUNT(*) as count,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER() * 100, 2) as percentage
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE status = 'failed'
  AND DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY error_stage
ORDER BY count DESC;
```

## 效能考量

- **Partitioning**: 按日期分區，查詢時自動過濾
- **Clustering**: 按 environment, status, user_id 分群，加速查詢
- **非同步記錄**: 不影響付款 API 回應時間
- **錯誤處理**: BigQuery 記錄失敗不影響付款流程

## 監控

建議建立 Data Studio Dashboard 監控：

1. **即時成功率** - 最近 1 小時的成功率
2. **錯誤趨勢** - 各錯誤階段的趨勢圖
3. **用戶行為** - 重複失敗的用戶
4. **效能指標** - 平均執行時間

## 資料保留

- **Hot storage**: 最近 30 天
- **Cold storage**: 30 天以上自動轉移
- **保留期限**: 2 年

## 隱私與安全

- ✅ 敏感資料已遮蔽 (Prime token 只保留前 20 字元)
- ✅ Authorization headers 已移除
- ✅ 完整信用卡號永不記錄
- ✅ 符合 GDPR 與個資法要求
