# Supabase RLS 修復指南

## 🚨 問題

Supabase Security Advisor 顯示 16 個錯誤，因為資料表沒有啟用 Row Level Security (RLS)。

## ⚠️ 風險

**沒有 RLS = 資料完全公開！**
- 任何人只要知道 Supabase URL 就能讀取/修改資料
- 學生可以看到其他學生的資料
- 教師可以看到其他教師的資料
- **極高安全風險！**

---

## ✅ 解決方案

已建立完整的 RLS 修復腳本：`backend/migrations/enable_rls_all_tables.sql`

### 執行步驟

#### 1. **Staging 環境測試**

```bash
# 1. 登入 Supabase CLI
supabase login

# 2. 連接到 Staging 專案
supabase link --project-ref gpmcajqrqmzgzzndbtbg

# 3. 執行 SQL 腳本
supabase db execute -f backend/migrations/enable_rls_all_tables.sql

# 4. 驗證 RLS 已啟用
supabase db execute "
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN (
  'teachers', 'students', 'classrooms',
  'classroom_students', 'programs', 'lessons'
);
"
```

#### 2. **測試 Staging**

```bash
# 啟動本地開發環境連接 Staging
cd /Users/young/project/duotopia
export $(cat .env.staging | xargs)
cd backend && uvicorn main:app --reload --port 8000
cd ../frontend && npm run dev
```

**測試項目**：
- [ ] 教師登入 → 能看到自己的班級
- [ ] 教師登入 → 不能看到其他教師的班級
- [ ] 學生登入 → 能看到自己的作業
- [ ] 學生登入 → 不能看到其他學生的作業
- [ ] 教師新增學生 → 成功
- [ ] 教師派作業 → 成功

#### 3. **Production 環境部署**

```bash
# 確認 Staging 測試通過後

# 1. 連接到 Production 專案
supabase link --project-ref szjeagbrubcibunofzud

# 2. 執行 SQL 腳本
supabase db execute -f backend/migrations/enable_rls_all_tables.sql

# 3. 驗證
supabase db execute "
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public';
"
```

---

## 📋 RLS Policies 說明

### **核心概念**

每個資料表都有以下 policies：

1. **SELECT** - 誰可以讀取資料
2. **INSERT** - 誰可以新增資料
3. **UPDATE** - 誰可以修改資料
4. **DELETE** - 誰可以刪除資料

### **權限設計**

#### **教師權限**
- ✅ 可以管理自己的班級
- ✅ 可以管理自己班級的學生
- ✅ 可以管理自己的課程計畫
- ✅ 可以派作業給自己班級的學生
- ❌ **不能**看到其他教師的資料

#### **學生權限**
- ✅ 可以查看自己的作業
- ✅ 可以提交自己的作業
- ✅ 可以查看自己的進度
- ❌ **不能**看到其他學生的資料
- ❌ **不能**修改作業內容

#### **公開資料**
- ✅ Programs（課程計畫） - 所有人可讀
- ✅ Lessons（課程單元） - 所有人可讀
- ✅ Contents（課程內容） - 所有人可讀
- ✅ Content Items（課程題目） - 所有人可讀

---

## 🔍 驗證 RLS 是否生效

### 方法一：Supabase Dashboard

1. 進入 Supabase Dashboard
2. **Database** → **Tables**
3. 檢查每個表的 **RLS** 欄位應顯示 ✅
4. 點擊表名 → **Policies** → 確認有對應的 policies

### 方法二：SQL 查詢

```sql
-- 檢查 RLS 狀態
SELECT
  tablename,
  rowsecurity,
  (SELECT COUNT(*)
   FROM pg_policies
   WHERE tablename = pg_tables.tablename) as policy_count
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;
```

### 方法三：Security Advisor

1. Supabase Dashboard → **Database** → **Security Advisor**
2. 應該顯示 ✅ **0 errors**

---

## ⚠️ 注意事項

### 1. **Backend API 仍需要驗證**

RLS 是**資料庫層**的防護，但 Backend API 仍需要：
```python
# 檢查用戶身份
current_user = get_current_user(token)

# 檢查權限
if classroom.teacher_id != current_user.id:
    raise HTTPException(status_code=403, detail="無權限")
```

### 2. **auth.uid() 的設定**

確保 Backend 使用 Supabase Auth 或設定 JWT：
```python
# backend/main.py
# Supabase JWT 會自動設定 auth.uid()
headers = {
    "Authorization": f"Bearer {supabase_jwt_token}"
}
```

### 3. **如果使用 Service Role Key**

Service Role Key **繞過 RLS**！
- ⚠️ 只在 Backend server-to-server 使用
- ❌ 絕對不要暴露給前端

---

## 🐛 常見問題

### Q: 執行 SQL 後前端報錯「permission denied」

**A**: RLS 啟用後，原本的查詢可能被阻擋。需要：
1. 確認 Backend 有正確傳遞 JWT token
2. 確認 token 包含正確的 user_id
3. 檢查 RLS policy 是否正確

### Q: 可以暫時關閉 RLS 嗎？

**A**: **絕對不行！** 這會讓資料完全公開。如果測試需要：
```sql
-- 暫時用 Service Role Key 連線（只在開發環境）
-- 但 Production 絕對不能關閉 RLS
```

### Q: 如何測試 RLS policy？

**A**: 使用 Supabase Dashboard 的 SQL Editor：
```sql
-- 模擬某個用戶的權限
SET LOCAL role authenticated;
SET LOCAL request.jwt.claims.sub = 'user_id_here';

-- 測試查詢
SELECT * FROM classrooms;  -- 應該只看到該用戶的班級
```

---

## 📊 修復前後對比

| 項目 | 修復前 | 修復後 |
|------|--------|--------|
| Security Advisor | ❌ 16 errors | ✅ 0 errors |
| 資料安全性 | ❌ 完全公開 | ✅ 權限控制 |
| 跨用戶存取 | ❌ 可以 | ✅ 不可以 |
| Production Ready | ❌ 否 | ✅ 是 |

---

## ✅ Checklist

執行前：
- [ ] 備份 Staging 資料庫
- [ ] 通知團隊即將進行資料庫維護

Staging 執行：
- [ ] 執行 RLS SQL 腳本
- [ ] 驗證 RLS 已啟用（SQL 查詢）
- [ ] 測試教師登入功能
- [ ] 測試學生登入功能
- [ ] 測試新增學生
- [ ] 測試派作業
- [ ] 檢查 Security Advisor（0 errors）

Production 執行：
- [ ] Staging 測試通過
- [ ] 執行 RLS SQL 腳本
- [ ] 驗證 RLS 已啟用
- [ ] 快速冒煙測試（登入 + 基本功能）
- [ ] 檢查 Security Advisor（0 errors）
- [ ] 監控 1 小時，確認無異常

---

**建立日期**: 2025-10-29
**優先級**: 🔴 **Critical** - 立即修復
**預估時間**: 30 分鐘（Staging） + 15 分鐘（Production）
