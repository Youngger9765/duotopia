# 🚨 立即修復：Supabase RLS 手動執行步驟

## ⚡ 快速步驟（5分鐘）

### **Staging 環境**

1. **打開 Supabase Dashboard**
   ```
   https://supabase.com/dashboard/project/gpmcajqrqmzgzzndbtbg
   ```

2. **進入 SQL Editor**
   - 左側選單：**SQL Editor**
   - 點擊：**New Query**

3. **複製貼上完整 SQL**
   ```bash
   # 在本機複製檔案內容
   cat backend/migrations/enable_rls_all_tables.sql | pbcopy
   ```

   或直接打開檔案：`backend/migrations/enable_rls_all_tables.sql`

4. **執行 SQL**
   - 貼上到 SQL Editor
   - 點擊：**Run** 或按 `Cmd+Enter`
   - 等待執行完成（約 10 秒）

5. **驗證成功**
   - 在 SQL Editor 執行：
   ```sql
   SELECT tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY tablename;
   ```
   - 所有表的 `rowsecurity` 應該都是 `t` (true)

6. **檢查 Security Advisor**
   - 左側選單：**Database** → **Security Advisor**
   - 應該顯示：✅ **0 warnings**

---

### **Production 環境**（Staging 測試通過後）

重複上述步驟，但使用 Production 專案：

```
https://supabase.com/dashboard/project/szjeagbrubcibunofzud
```

---

## 🔍 驗證 SQL（每個表確認）

執行以下 SQL 確認 RLS 已啟用：

```sql
-- 檢查所有表的 RLS 狀態
SELECT
  schemaname,
  tablename,
  rowsecurity as rls_enabled,
  (SELECT COUNT(*)
   FROM pg_policies
   WHERE tablename = pg_tables.tablename) as policy_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

**預期結果**：
```
tablename                        | rls_enabled | policy_count
---------------------------------|-------------|-------------
assignments                      | t           | 5
assignment_contents              | t           | 4
classrooms                       | t           | 4
classroom_students               | t           | 4
contents                         | t           | 4
content_items                    | t           | 4
invoice_status_history           | t           | 2
lessons                          | t           | 4
programs                         | t           | 4
students                         | t           | 3
student_assignments              | t           | 3
student_content_progress         | t           | 4
student_item_progress            | t           | 4
teachers                         | t           | 2
teacher_subscription_transactions| t           | 2
```

所有 `rls_enabled` 都應該是 `t` (true)！

---

## ⚠️ 如果執行失敗

### **錯誤 1: "policy already exists"**

**原因**：Policy 已存在（可能部分已執行）

**解決**：
```sql
-- 先刪除所有 policies
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tablename, policyname
        FROM pg_policies
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', r.policyname, r.tablename);
    END LOOP;
END $$;

-- 然後重新執行完整 SQL
```

### **錯誤 2: "table does not exist"**

**原因**：表名不符（可能是大小寫）

**解決**：
```sql
-- 檢查實際的表名
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- 手動修改 SQL 中的表名
```

### **錯誤 3: "column auth.uid does not exist"**

**原因**：需要啟用 Supabase Auth

**解決**：已經啟用（你有 SUPABASE_ANON_KEY），忽略此錯誤繼續執行

---

## 📋 Checklist

### **Staging**
- [ ] 打開 Supabase Dashboard（Staging）
- [ ] SQL Editor 執行完整 SQL
- [ ] 驗證所有表 `rowsecurity = t`
- [ ] Security Advisor 顯示 0 warnings
- [ ] 測試教師登入功能
- [ ] 測試學生登入功能
- [ ] 測試派作業功能

### **Production**
- [ ] Staging 測試通過
- [ ] 打開 Supabase Dashboard（Production）
- [ ] SQL Editor 執行完整 SQL
- [ ] 驗證所有表 `rowsecurity = t`
- [ ] Security Advisor 顯示 0 warnings
- [ ] 快速功能測試

---

## 🎯 完成後

執行此命令確認：

```bash
# 檢查 Staging Security Advisor
open "https://supabase.com/dashboard/project/gpmcajqrqmzgzzndbtbg/database/security-advisor"

# 檢查 Production Security Advisor
open "https://supabase.com/dashboard/project/szjeagbrubcibunofzud/database/security-advisor"
```

應該都顯示：✅ **All security checks passed**

---

**預估時間**：
- Staging: 5 分鐘
- Production: 3 分鐘
- **總計**: 8 分鐘

**立即執行！** 🚀
