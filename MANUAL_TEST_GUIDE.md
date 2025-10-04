# 🧪 金流系統手動測試指南

## 📋 測試前準備

### 1. 環境變數設定

#### Backend (.env)
```bash
cd backend

# 創建 .env 檔案
cat > .env << 'EOF'
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/duotopia

# TapPay 設定 (Sandbox)
TAPPAY_PARTNER_KEY=your_partner_key_here
TAPPAY_MERCHANT_ID=your_merchant_id_here

# 啟用 Mock 付款模式 (測試用)
USE_MOCK_PAYMENT=true
VITE_ENVIRONMENT=development

# JWT
JWT_SECRET=your-secret-key-here
EOF
```

#### Frontend (.env)
```bash
cd frontend

# 創建 .env 檔案
cat > .env << 'EOF'
# API URL
VITE_API_URL=http://localhost:8000

# TapPay 設定
VITE_TAPPAY_APP_ID=164155
VITE_TAPPAY_APP_KEY=app_your_key_here
VITE_TAPPAY_SERVER_TYPE=sandbox

# 環境
VITE_ENVIRONMENT=development
EOF
```

### 2. 啟動服務

#### Terminal 1: 啟動後端
```bash
cd backend
python3 -m uvicorn main:app --reload --port 8000
```

**✅ 確認後端啟動成功：**
- 看到 "Application startup complete"
- 訪問 http://localhost:8000 看到 {"message": "Duotopia API is running"}

#### Terminal 2: 啟動前端
```bash
cd frontend
npm run dev
```

**✅ 確認前端啟動成功：**
- 看到 "Local: http://localhost:5173"
- 打開瀏覽器訪問 http://localhost:5173

---

## 🎯 測試流程 1: 新用戶訂閱流程

### 步驟 1: 訪問定價頁面
1. 打開瀏覽器到 http://localhost:5173/pricing
2. **驗證點**：
   - [ ] 看到兩個方案卡片 (Tutor $230 / School $330)
   - [ ] 價格顯示正確
   - [ ] 「開始訂閱」按鈕可見

**📸 截圖**: `01_pricing_page.png`

---

### 步驟 2: 選擇方案
1. 點擊「Tutor Teachers」的「開始訂閱」按鈕
2. **驗證點**：
   - [ ] 彈出登入 Modal
   - [ ] Modal 標題顯示「教師登入」
   - [ ] 有 Email 和 Password 輸入框
   - [ ] 有「登入」和「註冊」按鈕

**📸 截圖**: `02_login_modal.png`

---

### 步驟 3: 註冊新帳號
1. 點擊「還沒有帳號？註冊」連結
2. 填寫註冊資料：
   ```
   姓名: 測試老師
   Email: test@duotopia.com
   密碼: Test1234!
   ```
3. 點擊「註冊」按鈕

**驗證點**：
- [ ] 註冊成功後自動登入
- [ ] Modal 關閉
- [ ] 進入付款頁面

**📸 截圖**: `03_register_success.png`

---

### 步驟 4: 檢查付款頁面
1. **驗證頁面元素**：
   - [ ] 顯示進度條 (4步驟，目前在「填寫付款資訊」)
   - [ ] 顯示方案名稱「Tutor Teachers」
   - [ ] 顯示金額「NT$ 230」
   - [ ] TapPay 安全標章顯示
   - [ ] 三個信用卡欄位：卡號、有效期限、CVV
   - [ ] 測試模式提示框
   - [ ] 「快速填入」按鈕
   - [ ] 「支付」按鈕（灰色，因為欄位未填）

**📸 截圖**: `04_payment_page.png`

---

### 步驟 5: 填寫信用卡資訊 (方法A - 手動)

1. **填寫卡號**：
   ```
   卡號: 4242 4242 4242 4242
   ```
   - **驗證**：自動加入空格分隔
   - **驗證**：欄位框線變藍色 (focus)

2. **填寫有效期限**：
   ```
   有效期限: 12/28
   ```
   - **驗證**：自動加入 "/" 分隔符

3. **填寫 CVV**：
   ```
   CVV: 123
   ```

**驗證點**：
- [ ] 所有欄位填寫完成後，「支付」按鈕變成可點擊（藍色）
- [ ] 沒有錯誤訊息顯示

**📸 截圖**: `05_card_filled.png`

---

### 步驟 5 (方法B - 快速填入) ⚡

1. 點擊「快速填入」按鈕
   - **或** 按 `Ctrl+T` (Windows) / `Cmd+T` (Mac)

**驗證點**：
- [ ] 三個欄位自動填入
- [ ] 顯示 Toast 提示「已自動填入測試卡號」
- [ ] 「支付」按鈕變成可點擊

**📸 截圖**: `05b_quick_fill.png`

---

### 步驟 6: 提交付款

1. 點擊「支付 NT$ 230」按鈕

**驗證點**：
- [ ] 按鈕顯示 Loading 圖示和「處理中...」
- [ ] 按鈕變成灰色不可點擊
- [ ] 等待 2-3 秒（Mock 模擬延遲）

**📸 截圖**: `06_processing.png`

---

### 步驟 7: 付款成功

**驗證點**：
- [ ] 顯示成功 Toast「付款成功！（測試模式）」
- [ ] 進度條跳到「完成訂閱」
- [ ] 自動跳轉或顯示成功訊息

**📸 截圖**: `07_payment_success.png`

---

### 步驟 8: 驗證後端記錄

#### 8.1 檢查資料庫
```bash
# 連接資料庫
psql -U your_user -d duotopia

# 查詢教師訂閱狀態
SELECT id, email, subscription_type, subscription_end_date
FROM teachers
WHERE email = 'test@duotopia.com';
```

**驗證點**：
- [ ] subscription_type = 'Tutor Teachers'
- [ ] subscription_end_date 是未來 30 天

#### 8.2 檢查交易記錄
```sql
SELECT
  id,
  teacher_email,
  amount,
  status,
  external_transaction_id,
  created_at
FROM teacher_subscription_transactions
WHERE teacher_email = 'test@duotopia.com'
ORDER BY created_at DESC
LIMIT 1;
```

**驗證點**：
- [ ] status = 'SUCCESS'
- [ ] amount = 230
- [ ] external_transaction_id 以 'MOCK_' 開頭

**📸 截圖**: `08_database_check.png`

---

## 🎯 測試流程 2: 現有用戶訂閱延期

### 步驟 1: 登入現有帳號
1. 訪問 http://localhost:5173/pricing
2. 選擇方案點「開始訂閱」
3. 使用已註冊帳號登入：
   ```
   Email: test@duotopia.com
   密碼: Test1234!
   ```

**驗證點**：
- [ ] 登入成功
- [ ] 進入付款頁面

---

### 步驟 2: 完成第二次付款
1. 使用快速填入或手動填寫卡號
2. 點擊「支付」

**驗證點**：
- [ ] 付款成功
- [ ] Toast 提示成功訊息

---

### 步驟 3: 驗證訂閱延期
```sql
SELECT
  email,
  subscription_end_date,
  (subscription_end_date - NOW()) as days_remaining
FROM teachers
WHERE email = 'test@duotopia.com';
```

**驗證點**：
- [ ] subscription_end_date 延長了 30 天
- [ ] days_remaining 約為 60 天

---

## 🎯 測試流程 3: 錯誤處理測試

### 測試 3.1: 卡號格式錯誤

1. 進入付款頁面
2. 輸入錯誤卡號：`1234 5678 9012 3456`
3. 點擊其他欄位

**驗證點**：
- [ ] 卡號欄位下方顯示紅色錯誤訊息「卡號格式不正確」
- [ ] 「支付」按鈕保持灰色不可點擊
- [ ] 欄位框線變紅色

**📸 截圖**: `error_01_invalid_card.png`

---

### 測試 3.2: 有效期限錯誤

1. 輸入過期日期：`01/20` (2020年)
2. 點擊其他欄位

**驗證點**：
- [ ] 顯示錯誤訊息「有效期限格式不正確」
- [ ] 「支付」按鈕不可點擊

**📸 截圖**: `error_02_expired_date.png`

---

### 測試 3.3: 未登入嘗試付款

1. 清除 localStorage（開發者工具 > Application > Local Storage > Clear）
2. 直接訪問付款頁面（如果有直接 URL）

**驗證點**：
- [ ] 自動跳轉到登入頁面
- [ ] 或顯示「請先登入」提示

---

### 測試 3.4: 金額篡改防護（後端測試）

使用 curl 測試：
```bash
# 嘗試用錯誤金額付款
curl -X POST http://localhost:8000/api/payment/process \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "prime": "test_prime",
    "amount": 1,
    "plan_name": "Tutor Teachers"
  }'
```

**驗證點**：
- [ ] 返回 400 錯誤
- [ ] 錯誤訊息：「Amount mismatch. Expected 230, got 1」

---

## 🎯 測試流程 4: 付款歷史查詢

### 步驟 1: 登入教師後台
1. 訪問教師儀表板
2. 找到「訂閱管理」或「付款記錄」

### 步驟 2: 查看交易歷史
1. 點擊「付款歷史」

**驗證點**：
- [ ] 顯示所有交易記錄
- [ ] 每筆記錄顯示：日期、金額、狀態
- [ ] 最新記錄在最上面
- [ ] 限制顯示 10 筆

**📸 截圖**: `payment_history.png`

---

## 🎯 測試流程 5: 不同方案測試

### 測試 School Teachers 方案

1. 登出當前帳號
2. 註冊新帳號：
   ```
   Email: school_teacher@duotopia.com
   密碼: Test1234!
   ```
3. 選擇「School Teachers」方案 ($330)
4. 完成付款流程

**驗證點**：
- [ ] 金額顯示「NT$ 330」
- [ ] 付款成功
- [ ] 資料庫記錄：
  ```sql
  SELECT subscription_type, amount
  FROM teacher_subscription_transactions
  WHERE teacher_email = 'school_teacher@duotopia.com';
  ```
  - subscription_type = 'School Teachers'
  - amount = 330

---

## 🔍 測試檢查清單

### 前端功能
- [ ] 定價頁面正常顯示
- [ ] 登入 Modal 正常彈出
- [ ] 註冊功能正常
- [ ] 付款頁面進度條顯示正確
- [ ] TapPay SDK 正常初始化
- [ ] 信用卡欄位自動格式化
- [ ] 即時驗證錯誤提示
- [ ] 快速填入功能正常
- [ ] Loading 狀態顯示
- [ ] 成功 Toast 提示
- [ ] 失敗錯誤訊息

### 後端功能
- [ ] POST /api/payment/process 正常
- [ ] Mock 付款模式運作
- [ ] 金額驗證功能
- [ ] 訂閱日期計算正確
- [ ] 訂閱延期功能
- [ ] 交易記錄創建
- [ ] JWT 認證正常
- [ ] 錯誤處理完整

### 資料庫
- [ ] teachers.subscription_end_date 更新
- [ ] teachers.subscription_type 正確
- [ ] teacher_subscription_transactions 記錄創建
- [ ] 所有必要欄位填寫
- [ ] idempotency_key 防重複

### 安全性
- [ ] 不儲存完整卡號
- [ ] 金額驗證防篡改
- [ ] JWT token 認證
- [ ] IP/UA 記錄稽核

---

## 📊 測試報告範本

### 測試執行紀錄

| 測試項目 | 狀態 | 備註 | 截圖 |
|---------|------|------|------|
| 新用戶註冊訂閱 | ✅ / ❌ | | |
| 現有用戶延期 | ✅ / ❌ | | |
| 卡號格式驗證 | ✅ / ❌ | | |
| 金額防篡改 | ✅ / ❌ | | |
| 付款歷史查詢 | ✅ / ❌ | | |
| School 方案測試 | ✅ / ❌ | | |

### 發現的問題

1. **問題描述**:
   - 重現步驟:
   - 預期結果:
   - 實際結果:
   - 嚴重程度: 🔴高 / 🟡中 / 🟢低

---

## 🚀 進階測試（選做）

### 效能測試
```bash
# 使用 Apache Bench 測試 API
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/payment/history
```

### 並發測試
- 同時多個用戶訂閱
- 同一用戶快速點擊付款按鈕（測試 idempotency）

### 瀏覽器相容性
- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

---

## 📞 測試問題回報

如發現問題，請記錄：
1. 📸 截圖
2. 🖥️ Console 錯誤訊息（F12 > Console）
3. 🌐 Network 請求記錄（F12 > Network）
4. 📋 重現步驟

**測試完成！** 🎉
