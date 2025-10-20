-- Migration: 新增訂閱自動續訂欄位
-- Date: 2025-10-20
-- Description: 支援用戶取消自動續訂功能

-- 新增欄位
ALTER TABLE teachers
ADD COLUMN IF NOT EXISTS subscription_auto_renew BOOLEAN DEFAULT TRUE;

ALTER TABLE teachers
ADD COLUMN IF NOT EXISTS subscription_cancelled_at TIMESTAMP WITH TIME ZONE;

-- 為現有資料設定預設值
UPDATE teachers
SET subscription_auto_renew = TRUE
WHERE subscription_auto_renew IS NULL;

-- 建立索引（可選，方便查詢已取消訂閱的用戶）
CREATE INDEX IF NOT EXISTS idx_teachers_auto_renew
ON teachers(subscription_auto_renew)
WHERE subscription_end_date IS NOT NULL;

-- 驗證
SELECT
    COUNT(*) as total_teachers,
    COUNT(subscription_end_date) as subscribed_teachers,
    SUM(CASE WHEN subscription_auto_renew = TRUE THEN 1 ELSE 0 END) as auto_renew_enabled,
    SUM(CASE WHEN subscription_auto_renew = FALSE THEN 1 ELSE 0 END) as auto_renew_disabled
FROM teachers;
