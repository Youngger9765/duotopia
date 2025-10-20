-- BigQuery Schema: 金流交易紀錄
-- Dataset: duotopia_analytics
-- Table: transaction_logs

CREATE TABLE IF NOT EXISTS `duotopia-472708.duotopia_analytics.transaction_logs` (
  -- 基本資訊
  transaction_id STRING,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  environment STRING,  -- production, staging, local

  -- 用戶資訊
  user_id INT64,
  user_email STRING,
  user_type STRING,  -- teacher, student

  -- 交易資訊
  amount INT64,
  plan_name STRING,
  payment_method STRING,  -- credit_card, etc

  -- 狀態
  status STRING,  -- success, failed, pending
  error_stage STRING,  -- authentication, prime_token, tappay_api, database, unknown
  error_code STRING,
  error_message STRING,

  -- TapPay 相關
  tappay_prime_token STRING,
  tappay_response JSON,
  tappay_rec_trade_id STRING,

  -- 技術細節
  api_endpoint STRING,
  request_headers JSON,
  request_body JSON,
  response_status INT64,
  response_body JSON,

  -- 前端資訊
  frontend_error JSON,
  user_agent STRING,
  client_ip STRING,

  -- 診斷資訊
  execution_time_ms INT64,
  stack_trace STRING,
  additional_context JSON
)
PARTITION BY DATE(timestamp)
CLUSTER BY environment, status, user_id
OPTIONS(
  description="金流交易完整紀錄 - 包含成功與失敗的交易",
  require_partition_filter=false
);

-- 建立 View: 失敗交易分析
CREATE OR REPLACE VIEW `duotopia-472708.duotopia_analytics.failed_transactions` AS
SELECT
  DATE(timestamp) as date,
  environment,
  error_stage,
  error_code,
  COUNT(*) as failure_count,
  ARRAY_AGG(STRUCT(user_email, error_message, timestamp) ORDER BY timestamp DESC LIMIT 5) as recent_failures
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE status = 'failed'
GROUP BY date, environment, error_stage, error_code
ORDER BY date DESC, failure_count DESC;

-- 建立 View: 成功交易統計
CREATE OR REPLACE VIEW `duotopia-472708.duotopia_analytics.successful_transactions` AS
SELECT
  DATE(timestamp) as date,
  environment,
  plan_name,
  COUNT(*) as transaction_count,
  SUM(amount) as total_revenue,
  COUNT(DISTINCT user_id) as unique_users
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
WHERE status = 'success'
GROUP BY date, environment, plan_name
ORDER BY date DESC;

-- 建立 View: 用戶交易歷史
CREATE OR REPLACE VIEW `duotopia-472708.duotopia_analytics.user_transaction_history` AS
SELECT
  user_email,
  user_id,
  COUNT(*) as total_attempts,
  COUNTIF(status = 'success') as successful_transactions,
  COUNTIF(status = 'failed') as failed_transactions,
  SUM(IF(status = 'success', amount, 0)) as total_spent,
  MAX(timestamp) as last_transaction_time,
  ARRAY_AGG(
    STRUCT(
      timestamp,
      status,
      amount,
      plan_name,
      error_stage,
      error_message
    )
    ORDER BY timestamp DESC
    LIMIT 10
  ) as recent_transactions
FROM `duotopia-472708.duotopia_analytics.transaction_logs`
GROUP BY user_email, user_id
ORDER BY last_transaction_time DESC;
