-- Supabase Security Configuration
-- 執行這個 SQL 來加強資料庫安全性

-- =====================================================
-- 1. 建立應用程式專用角色（最小權限原則）
-- =====================================================

-- 建立只讀角色
CREATE ROLE duotopia_readonly;
GRANT USAGE ON SCHEMA public TO duotopia_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO duotopia_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO duotopia_readonly;

-- 建立應用程式角色（讀寫但不能改 schema）
CREATE ROLE duotopia_app;
GRANT USAGE ON SCHEMA public TO duotopia_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO duotopia_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO duotopia_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO duotopia_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO duotopia_app;

-- =====================================================
-- 2. Row Level Security (RLS) 政策
-- =====================================================

-- 啟用所有表格的 RLS
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE classrooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE programs ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_results ENABLE ROW LEVEL SECURITY;

-- Teachers 表格政策
CREATE POLICY "Teachers can only see their own data" ON teachers
    FOR ALL USING (auth.uid()::text = id::text);

CREATE POLICY "Teachers can update their own data" ON teachers
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Students 表格政策
CREATE POLICY "Teachers can see their students" ON students
    FOR SELECT USING (
        classroom_id IN (
            SELECT id FROM classrooms
            WHERE teacher_id = auth.uid()::text
        )
    );

CREATE POLICY "Students can see their own data" ON students
    FOR SELECT USING (auth.uid()::text = id::text);

-- Classrooms 表格政策
CREATE POLICY "Teachers can manage their classrooms" ON classrooms
    FOR ALL USING (teacher_id = auth.uid()::text);

CREATE POLICY "Students can view their classroom" ON students
    FOR SELECT USING (
        id IN (
            SELECT classroom_id FROM students
            WHERE id = auth.uid()::text
        )
    );

-- Programs 表格政策
CREATE POLICY "Teachers can manage their programs" ON programs
    FOR ALL USING (teacher_id = auth.uid()::text);

CREATE POLICY "Public programs are viewable by all" ON programs
    FOR SELECT USING (is_public = true);

-- Assignments 表格政策
CREATE POLICY "Teachers can see all assignments for their students" ON student_assignments
    FOR SELECT USING (
        student_id IN (
            SELECT id FROM students
            WHERE classroom_id IN (
                SELECT id FROM classrooms
                WHERE teacher_id = auth.uid()::text
            )
        )
    );

CREATE POLICY "Students can see their own assignments" ON student_assignments
    FOR SELECT USING (student_id = auth.uid()::text);

-- =====================================================
-- 3. 審計記錄表
-- =====================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_id VARCHAR(100),
    changed_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 建立審計觸發器函數
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs(table_name, operation, user_id, changed_data)
    VALUES (
        TG_TABLE_NAME,
        TG_OP,
        COALESCE(current_setting('app.current_user_id', true), 'system'),
        to_jsonb(NEW)
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 為重要表格加入審計觸發器
CREATE TRIGGER audit_teachers AFTER INSERT OR UPDATE OR DELETE ON teachers
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_students AFTER INSERT OR UPDATE OR DELETE ON students
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_programs AFTER INSERT OR UPDATE OR DELETE ON programs
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- =====================================================
-- 4. 資料加密函數
-- =====================================================

-- 加密敏感資料的函數
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT)
RETURNS TEXT AS $$
BEGIN
    -- 使用 Supabase 的加密擴展
    RETURN encode(encrypt(data::bytea, current_setting('app.encryption_key')::bytea, 'aes'), 'base64');
END;
$$ LANGUAGE plpgsql;

-- 解密敏感資料的函數
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN convert_from(decrypt(decode(encrypted_data, 'base64'), current_setting('app.encryption_key')::bytea, 'aes'), 'UTF8');
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 5. 連線限制
-- =====================================================

-- 限制每個使用者的連線數
ALTER ROLE duotopia_app CONNECTION LIMIT 20;
ALTER ROLE duotopia_readonly CONNECTION LIMIT 5;

-- =====================================================
-- 6. 密碼政策（需要在 Supabase Dashboard 設定）
-- =====================================================
-- 建議設定：
-- - 密碼最小長度：12 字元
-- - 必須包含大小寫字母、數字和特殊字元
-- - 密碼過期時間：90 天
-- - 密碼歷史記錄：不可重複最近 5 個密碼

-- =====================================================
-- 7. 定期清理過期資料
-- =====================================================

-- 清理 30 天前的審計記錄
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '30 days';
END;
$$ LANGUAGE plpgsql;

-- 建立定期執行的工作（需要 pg_cron 擴展）
-- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT cleanup_old_audit_logs();');

-- =====================================================
-- 8. 監控查詢
-- =====================================================

-- 查看目前活動連線
CREATE VIEW active_connections AS
SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    query_start,
    state_change,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start DESC;

-- 查看慢查詢
CREATE VIEW slow_queries AS
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 1000  -- 超過 1 秒的查詢
ORDER BY mean_exec_time DESC
LIMIT 20;

-- =====================================================
-- 9. 備份驗證
-- =====================================================

-- 建立備份驗證表
CREATE TABLE IF NOT EXISTS backup_validation (
    id SERIAL PRIMARY KEY,
    backup_date DATE NOT NULL,
    record_count INTEGER NOT NULL,
    checksum VARCHAR(64),
    validated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- 執行完成訊息
-- =====================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Security configuration completed!';
    RAISE NOTICE '⚠️  Remember to:';
    RAISE NOTICE '  1. Create database users with these roles';
    RAISE NOTICE '  2. Update connection strings to use new users';
    RAISE NOTICE '  3. Test RLS policies thoroughly';
    RAISE NOTICE '  4. Set up regular backups';
    RAISE NOTICE '  5. Monitor audit logs regularly';
END $$;
