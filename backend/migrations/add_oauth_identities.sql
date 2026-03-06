-- Migration: 新增 OAuth 身份連結表 + teachers.has_password 欄位
-- Date: 2026-03-06
-- Issue: #241 SSO 單一登入系統 帳號統整
-- Description: 建立 oauth_identities 表支援多 OAuth provider 連結，
--              並新增 has_password 欄位標記帳號是否有設定密碼

-- ============================================================
-- 1. 新增 oauth_identities 表
-- ============================================================
CREATE TABLE IF NOT EXISTS oauth_identities (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,

    -- OAuth provider 資訊
    provider VARCHAR(50) NOT NULL,              -- 'google', 'line', '1campus', 'ischool'
    provider_user_id VARCHAR(255) NOT NULL,     -- provider 回傳的唯一 user ID

    -- provider 給的 profile 資訊
    provider_email VARCHAR(255),                -- 可能為 null（LINE 不一定給）
    display_name VARCHAR(255),
    avatar_url TEXT,

    -- OAuth tokens（加密存放）
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,

    -- 完整 profile 備查
    raw_profile JSONB DEFAULT '{}',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 約束：同 provider 同 user ID 不可重複（防止同一個外部帳號綁到多個教師）
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_oauth_provider_user') THEN
        ALTER TABLE oauth_identities
            ADD CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id);
    END IF;
END $$;

-- 約束：一個教師每個 provider 只能綁一個帳號
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_oauth_teacher_provider') THEN
        ALTER TABLE oauth_identities
            ADD CONSTRAINT uq_oauth_teacher_provider UNIQUE (teacher_id, provider);
    END IF;
END $$;

-- 索引
CREATE INDEX IF NOT EXISTS ix_oauth_identity_teacher
    ON oauth_identities(teacher_id);

CREATE INDEX IF NOT EXISTS ix_oauth_identity_lookup
    ON oauth_identities(provider, provider_user_id);

-- ============================================================
-- 2. teachers 新增 has_password 欄位
-- ============================================================
ALTER TABLE teachers
ADD COLUMN IF NOT EXISTS has_password BOOLEAN DEFAULT TRUE;

-- 現有帳號全部預設 true（都是 email/password 註冊的）
UPDATE teachers
SET has_password = TRUE
WHERE has_password IS NULL;

-- ============================================================
-- 驗證
-- ============================================================
SELECT
    (SELECT COUNT(*) FROM information_schema.tables
     WHERE table_name = 'oauth_identities') as oauth_table_exists,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'teachers' AND column_name = 'has_password') as has_password_exists;
