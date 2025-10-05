# 🧪 瀏覽器實際測試步驟 - 認證系統重構驗證

**測試日期**: 2025-10-05
**測試目的**: 驗證 teacherAuthStore 重構後登入功能正常

---

## 📋 測試前準備

### 1. 啟動開發伺服器
```bash
cd /Users/young/project/duotopia/frontend
npm run dev
```

### 2. 清除舊的 localStorage (重要！)
在瀏覽器開發者工具 Console 執行：
```javascript
localStorage.clear()
```

---

## ✅ 測試案例 1：教師登入功能

### 步驟：
1. **打開登入頁面**
   ```
   http://localhost:5173/teacher/login
   ```

2. **使用測試帳號登入**
   - Email: `demo@duotopia.com`
   - Password: `demo123`
   - 或點擊「Demo 教師」快速登入按鈕

3. **檢查 Console 輸出**
   應該看到：
   ```
   🔑 [DEBUG] teacherLogin 方法被調用
   🔑 [DEBUG] 登入成功，返回 response
   🔑 [DEBUG] localStorage 檢查: { teacher_auth_storage: ..., keys: [...] }
   ```

4. **檢查 localStorage (F12 → Application → Local Storage)**

   ✅ **應該存在的 keys**:
   - `teacher-auth-storage` - 格式：`{"state":{"token":"...","user":{...},"isAuthenticated":true},"version":0}`
   - `selectedPlan` (如果從 PricingPage 登入)

   ❌ **不應該存在的舊 keys**:
   - `token`
   - `access_token`
   - `user`
   - `userInfo`
   - `role`
   - `username`
   - `userType`
   - `auth-storage`

5. **驗收標準**
   - [ ] 登入成功後跳轉到 `/teacher/dashboard`
   - [ ] localStorage 只有 `teacher-auth-storage`
   - [ ] `teacher-auth-storage` 包含正確的 token 和 user 資料
   - [ ] Console 沒有錯誤

---

## ✅ 測試案例 2：PricingPage 登入流程

### 步驟：
1. **清除 localStorage**
   ```javascript
   localStorage.clear()
   ```

2. **打開 PricingPage**
   ```
   http://localhost:5173/pricing
   ```

3. **點擊任一訂閱方案**
   - 應該彈出登入 Modal

4. **在 Modal 中登入**
   - Email: `demo@duotopia.com`
   - Password: `demo123`

5. **檢查結果**
   - [ ] 登入成功
   - [ ] localStorage 有 `teacher-auth-storage`
   - [ ] localStorage 有 `selectedPlan`
   - [ ] 沒有舊的 token keys

---

## ✅ 測試案例 3：Logout 功能

### 步驟：
1. **確保已登入**
   (執行測試案例 1)

2. **檢查登入狀態**
   在 Console 執行：
   ```javascript
   JSON.parse(localStorage.getItem('teacher-auth-storage'))
   ```
   應該顯示 `isAuthenticated: true`

3. **執行 Logout**
   - 方法 1: 在頁面上點擊登出按鈕
   - 方法 2: 在 Console 執行：
     ```javascript
     useTeacherAuthStore.getState().logout()
     ```

4. **檢查結果**
   ```javascript
   JSON.parse(localStorage.getItem('teacher-auth-storage'))
   ```
   應該顯示：
   ```json
   {
     "state": {
       "token": null,
       "user": null,
       "isAuthenticated": false
     },
     "version": 0
   }
   ```

5. **驗收標準**
   - [ ] token 被清除
   - [ ] user 被清除
   - [ ] isAuthenticated = false
   - [ ] 重新整理頁面後仍然是登出狀態

---

## ✅ 測試案例 4：跨角色隔離測試

### 步驟：
1. **Teacher 登入**
   ```
   http://localhost:5173/teacher/login
   Email: demo@duotopia.com
   Password: demo123
   ```

2. **檢查 localStorage**
   應該有：`teacher-auth-storage`

3. **Student 登入 (開新分頁)**
   ```
   http://localhost:5173/student/login
   學號: [任意學生學號]
   密碼: [對應密碼]
   ```

4. **檢查 localStorage**
   應該同時有：
   - `teacher-auth-storage`
   - `student-auth-storage`

5. **Teacher Logout**
   ```javascript
   useTeacherAuthStore.getState().logout()
   ```

6. **檢查結果**
   - [ ] Teacher token 被清除
   - [ ] Student token 不受影響
   - [ ] 兩個 store 獨立運作

---

## 🐛 常見問題排查

### 問題 1: 登入後 localStorage 仍有舊 keys
**原因**: 可能沒有清除舊資料
**解決**:
```javascript
localStorage.clear()
location.reload()
```

### 問題 2: 登入失敗
**檢查**:
1. 後端是否正在運行？
2. API URL 是否正確？ (檢查 `.env` 中的 `VITE_API_URL`)
3. Console 是否有錯誤訊息？

### 問題 3: localStorage 格式錯誤
**正確格式**:
```json
{
  "state": {
    "token": "eyJ...",
    "user": {
      "id": 1,
      "name": "Demo Teacher",
      "email": "demo@duotopia.com",
      "is_demo": true
    },
    "isAuthenticated": true
  },
  "version": 0
}
```

---

## 📸 測試完成確認清單

執行所有測試後，請確認：

- [ ] 測試案例 1: 教師登入 ✅
- [ ] 測試案例 2: PricingPage 登入 ✅
- [ ] 測試案例 3: Logout 功能 ✅
- [ ] 測試案例 4: 跨角色隔離 ✅
- [ ] 沒有 Console 錯誤
- [ ] 沒有舊的 localStorage keys
- [ ] 截圖存證（如果需要）

---

## 🎯 預期結果總結

### ✅ 成功標準
1. 只有 `teacher-auth-storage` 和 `student-auth-storage` 兩個 auth keys
2. 所有舊的 token keys 都不存在
3. 登入/登出功能正常
4. Token 正確儲存在對應的 store
5. 跨角色登入互不干擾

### ❌ 失敗標準（需要修復）
1. localStorage 仍有舊 keys (`token`, `access_token`, 等)
2. 登入後無法取得 token
3. Logout 後 token 沒有被清除
4. Console 有錯誤訊息
5. 頁面功能異常

---

**測試完成後請回報結果！** 🚀
