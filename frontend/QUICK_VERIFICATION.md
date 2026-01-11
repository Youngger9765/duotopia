# 快速驗證指南

## Issue #112: Organization Portal Separation

### 驗證時間：2 分鐘

---

## 測試步驟

### 1. org_owner 登入測試 ⚠️ CRITICAL

```bash
1. 開啟瀏覽器：http://localhost:5173/teacher/login
2. 登入帳號：owner@duotopia.com / owner123
3. 預期結果：
   ✅ 自動重定向到 /organization/dashboard
   ✅ 顯示「組織管理後台」標題
   ✅ Sidebar 有「組織架構」、「學校管理」、「教師管理」
   ✅ 可以看到組織架構樹
```

**如果失敗**：
- 檢查瀏覽器 Console 是否有錯誤
- 檢查 Network tab，確認 login API 回應包含 role
- 檢查是否重定向到錯誤的頁面

---

### 2. 純教師登入測試 ⚠️ CRITICAL

```bash
1. 登出當前帳號
2. 登入帳號：orgteacher@duotopia.com / orgteacher123
3. 預期結果：
   ✅ 自動重定向到 /teacher/dashboard
   ✅ 顯示教師後台（不是組織後台）
   ✅ Sidebar 沒有組織管理相關項目
   ✅ 嘗試訪問 /organization/dashboard 會被阻擋
```

**如果失敗**：
- 確認登入 API 回應中 role 為 "teacher"
- 確認沒有重定向到組織後台

---

### 3. 組織管理功能測試（選做）

```bash
以 org_owner 登入後：
1. 點擊「學校管理」
   ✅ 進入 /organization/schools
   ✅ 顯示學校列表
2. 點擊「教師管理」
   ✅ 進入 /organization/teachers
   ✅ 顯示教師列表
3. 點擊「切換到教師後台」
   ✅ 導航到 /teacher/dashboard
```

---

## 驗證 API 回應（開發者工具）

### 登入 API 應該返回：

```json
{
  "access_token": "...",
  "user": {
    "id": 6,
    "email": "owner@duotopia.com",
    "name": "張機構",
    "role": "org_owner",  // ✅ 必須有
    "organization_id": "22f0f71f-...",  // ✅ 必須有
    "school_id": null
  }
}
```

### 檢查方式：
1. 開啟 Chrome DevTools (F12)
2. 切換到 Network tab
3. 登入
4. 找到 `/api/auth/teacher/login` 請求
5. 查看 Response，確認有 role, organization_id, school_id

---

## 成功標準

- ✅ org_owner → 重定向到組織後台
- ✅ teacher → 重定向到教師後台
- ✅ 組織後台功能正常（學校管理、教師管理）
- ✅ 權限控制正常（純教師無法訪問組織後台）
- ✅ 無 Console 錯誤
- ✅ 無 API 錯誤

---

## 如果全部通過

**Issue #112 完成！** 🎉

可以：
1. 截圖關鍵頁面
2. 更新 Issue #112 狀態
3. 準備合併到 staging
4. 通知 QA 團隊進行完整測試

---

## 如果有問題

**立即回報**：
- 什麼步驟失敗了
- 瀏覽器 Console 錯誤訊息
- Network tab 的 API 回應
- 截圖

我會立即協助 debug。
