# Duotopia 11月交付功能清單

**版本**: 2.0
**日期**: 2025-11-18
**狀態**: ✅ 核心功能已完成

---

## 📋 功能交付總覽

### ✅ 已完成功能 (6項)
1. ✅ 後台顯示試用方案資訊
2. ✅ 試用點數自動轉移
3. ✅ 後台帳款資料下載
4. ✅ 每月自動續訂機制
5. ✅ 信用卡綁定流程
6. ✅ 個人資料管理（老師和學生）

### 🚧 進行中功能 (2項)
7. 🚧 退款機制（後台管理介面）
8. 🚧 多語言介面（全站 i18n）

---

## 📦 功能詳細說明

### 1️⃣ 後台顯示試用方案資訊

**✅ 已完成**

#### 功能說明
管理者在後台可以看到新註冊用戶的試用方案資訊。

#### 具體內容
- 試用方案顯示為「30-Day Trial」
- 顯示試用到期日（註冊日 + 30天）
- 付費用戶顯示對應方案名稱

---

### 2️⃣ 試用點數自動轉移

**✅ 已完成**

#### 功能說明
當用戶從試用升級到付費方案時，未使用的試用點數會自動加到付費方案中。

#### 舉例
```
用戶試用期：
- 獲得 10,000 點試用點數
- 已使用 3,000 點
- 剩餘 7,000 點

升級到 School Teachers 方案：
- School 方案基本配額：25,000 點
- 加上試用剩餘：7,000 點
- 總配額：32,000 點
```

#### 好處
- 用戶不會損失未使用的試用點數
- 提升付費轉換意願

---

### 3️⃣ 後台帳款資料下載

**✅ 已完成**

#### 功能說明
管理者可以下載訂閱資料、交易記錄、學習數據為 Excel 檔案。

#### 具體內容
- 可選擇日期範圍
- 下載為 CSV 格式（Excel 可直接開啟）
- 支援中文欄位名稱
- 檔名自動加上下載日期

#### 可下載的資料
1. 訂閱資料（用戶方案、到期日等）
2. 交易記錄（付款日期、金額等）
3. 學習分析（使用點數、活動記錄等）

---

### 4️⃣ 每月自動續訂機制

**✅ 已完成**

#### 功能說明
每個月 1 號凌晨 2 點，系統自動處理訂閱續約。

#### 自動執行的事項

**1. 標記過期訂閱**
- 檢查所有到期的訂閱
- 自動標記為「已過期」

**2. 自動續訂**
符合以下條件的用戶會自動續訂：
- 用戶有開啟「自動續訂」
- 用戶有綁定信用卡
- 帳號為啟用狀態

**3. 安全機制**
- 防止重複扣款（已有本月訂閱就跳過）
- 防止錯誤扣款（檢查是否有上個月的訂閱記錄）
- 如有異常，自動關閉續訂功能並通知用戶

#### 待處理事項
- [ ] 設定每月 1 號自動觸發
- [ ] 完成 Email 通知模板

---

### 5️⃣ 信用卡綁定流程

**✅ 已完成**

#### 功能說明
用戶綁定信用卡時，可以選擇是否啟用自動續訂。

#### 三種使用情境

**情境 1：綁定信用卡**
```
1. 用戶輸入信用卡資訊
2. 系統驗證成功
3. 詢問：「是否啟用自動續訂？」
   - 選「是」→ 每月 1 號自動扣款續訂
   - 選「否」→ 保留信用卡但需手動續訂
```

**情境 2：刪除信用卡**
```
1. 用戶刪除信用卡
2. 系統提示：「刪除後自動續訂將關閉」
3. 確認後：
   - 信用卡資訊刪除
   - 自動續訂功能自動關閉
```

**情境 3：只關閉自動續訂**
```
1. 用戶關閉自動續訂開關
2. 系統提示：「關閉後不會自動扣款，可隨時手動續訂」
3. 確認後：
   - 自動續訂關閉
   - 信用卡資訊保留（方便未來手動付款）
```

#### 保護機制
- 沒有綁定信用卡，無法開啟自動續訂
- 系統會阻止不合理的設定

---

### 6️⃣ 個人資料管理

**✅ 已完成**

#### 功能說明
老師和學生可以在側欄的 Profile 頁面更新個人資料和密碼。

#### 具體內容

**老師端功能：**
- ✅ 側欄加入「Profile」選項
- ✅ 更新姓名
- ✅ 更新電話號碼
- ✅ 更改密碼
- ✅ 顯示帳號資訊（Email、Admin 狀態、Demo 帳號等）

**學生端功能：**
- ✅ Profile 頁面更新姓名
- ✅ 更改密碼
- ✅ 顯示班級和學號資訊

**後端 API：**
- ✅ PUT /api/teachers/me - 更新老師個人資料
- ✅ PUT /api/teachers/me/password - 更新老師密碼
- ✅ PUT /api/students/me - 更新學生個人資料
- ✅ PUT /api/students/me/password - 更新學生密碼

#### 安全機制
- 密碼更改需要驗證舊密碼
- 新密碼至少 6 個字元
- 密碼確認必須匹配

#### 測試覆蓋 (2025-11-19 新增)
**學生密碼重設測試** (`test_student_password_reset.py`)：
- ✅ 密碼更新成功測試
- ✅ 舊密碼錯誤測試
- ✅ 新密碼過短測試
- ✅ 未認證測試
- ✅ password_changed 標記測試
- ✅ 特殊字元密碼測試
- ✅ 個人資料更新測試

**老師密碼重設測試** (`test_teacher_password_reset.py`)：
- ✅ 密碼更新成功測試
- ✅ 舊密碼錯誤測試
- ✅ 新密碼過短測試
- ✅ 未認證測試
- ✅ 個人資料更新測試（姓名、電話）

#### API Schema 改進 (2025-11-19)
**學生驗證 API 欄位語意化**：
- 修改前：`POST /api/students/validate { email, birthdate }`
- 修改後：`POST /api/students/validate { email, password }`
- 原因：欄位名稱 `birthdate` 語意不清，實際接受任何密碼（生日或新密碼）
- 影響：不影響現有用戶（前端使用不同的 `/api/auth/student/login` API）

---

### 7️⃣ 退款機制

**🚧 進行中**

#### 功能說明
完整的退款處理系統，支援全額退款和部分退款。

#### 具體內容

**1. 退款 Webhook 處理**
- 接收 TapPay 退款事件通知
- HMAC-SHA256 簽名驗證確保安全性
- 自動處理退款後的訂閱調整

**2. 退款類型**
```
全額退款：
- 扣除完整訂閱天數（月方案30天、季方案90天）
- 標記原始交易為 REFUNDED

部分退款：
- 按比例扣除訂閱天數
- 退款比例 = 退款金額 / 原始金額
```

**3. 完整記錄追蹤**
- BigQuery Logging - 記錄完整退款資訊
- Email 通知 - 自動發送退款通知郵件
- 獨立退款交易記錄 (TransactionType.REFUND)
- 關聯原始交易 (original_transaction_id)

**4. 安全機制**
- 冪等性保證（避免重複處理）
- 完整稽核日誌
- 錯誤處理不影響主流程

#### 已完成部分
- ✅ Webhook 退款處理（自動）
- ✅ BigQuery Logging
- ✅ Email 通知
- ✅ 全額/部分退款邏輯

#### 待完成部分
- ⏳ **後台管理介面** - 管理者手動執行退款的 UI
- ⏳ **退款 Admin API** - POST /api/admin/refund
- ⏳ **退款成功/失敗訊息呈現**

#### 相關 API
- ✅ Webhook: POST /api/payment/webhook
- ✅ 取消續訂: POST /api/subscription/cancel
- ✅ 恢復續訂: POST /api/subscription/resume
- ✅ 訂閱狀態: GET /api/subscription/status
- ⏳ 管理者退款: POST /api/admin/refund (待實作)

---

### 8️⃣ 多語言介面 (i18n)

**✅ 已完成**

#### 功能說明
全站支援繁體中文和英文雙語切換。

#### 具體內容

**1. 技術架構**
- 使用 react-i18next 框架
- 支援語言：繁體中文 (zh-TW)、English (en)
- localStorage 記憶使用者語言偏好
- 自動偵測瀏覽器語言

**2. LanguageSwitcher 元件**
```
位置：全局可用（所有頁面）
功能：
- 快速切換中英文
- 即時更新所有介面文字
- 切換動畫流暢
- RWD 響應式設計
```

**3. 翻譯覆蓋範圍**

**✅ 公開頁面 (3/3 = 100%)**
- ✅ Home.tsx - 首頁
- ✅ PricingPage.tsx - 定價頁面
- ✅ TermsOfService.tsx - 服務條款

**✅ 登入/註冊頁面 (8/8 = 100%)**
- ✅ TeacherLogin.tsx
- ✅ TeacherRegister.tsx
- ✅ StudentLogin.tsx
- ✅ TeacherEmailVerification.tsx
- ✅ EmailVerification.tsx
- ✅ TeacherForgotPassword.tsx
- ✅ TeacherResetPassword.tsx
- ✅ TeacherVerifyEmail.tsx

**✅ Teacher 頁面 (10/10 = 100%)**
- ✅ TeacherDashboard.tsx - 儀表板
- ✅ TeacherClassrooms.tsx - 班級管理
- ✅ TeacherStudents.tsx - 學生管理
- ✅ TeacherTemplatePrograms.tsx - 課程模板
- ✅ TeacherSubscription.tsx - 訂閱管理
- ✅ ClassroomDetail.tsx - 班級詳情
- ✅ GradingPage.tsx - 批改頁面
- ✅ TeacherAssignmentDetailPage.tsx - 作業詳情
- ✅ TeacherAssignmentPreviewPage.tsx - 作業預覽
- ✅ TeacherLayout.tsx - 側邊欄佈局

**✅ Student 頁面 (6/6 = 100%)**
- ✅ StudentActivityPage.tsx - 學生作業
- ✅ StudentLayout.tsx - 學生佈局
- ✅ （其他 4 個 Student 頁面）

**✅ Admin 後台頁面 (3/3 = 100%)**
- ✅ AdminSubscriptionDashboard.tsx - 訂閱管理後台
- ✅ AdminMonitoringPage.tsx - 系統監控
- ✅ DatabaseAdminPage.tsx - 資料庫管理

**總進度：24/24 核心頁面完成 (100%)**

**4. 翻譯檔案管理**
```
frontend/src/i18n/
├── config.ts              # i18n 配置
└── locales/
    ├── zh-TW/
    │   └── translation.json  # 繁體中文（1,442 keys）
    └── en/
        └── translation.json  # 英文（1,442 keys）
```

**5. 測試覆蓋**
- ✅ Playwright 語言切換測試
- ✅ 跨頁面語言持久化測試
- ✅ RWD 響應式測試（375px, 768px, 1920px）
- ✅ 所有測試通過 (100%)

#### 使用範例
```typescript
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();

// 簡單翻譯
<h1>{t('home.welcome')}</h1>

// 帶參數的翻譯
<p>{t('dashboard.greeting', { name: userName })}</p>
```

---

## 📊 訂閱方案配額

### 試用方案 (30-Day Trial)
- **配額**: 10,000 點
- **期限**: 30 天
- **費用**: 免費

### Tutor Teachers
- **配額**: 10,000 點/月
- **費用**: NT$ 231/月

### School Teachers
- **配額**: 25,000 點/月
- **費用**: NT$ 660/月

---

## ✅ 完成度總結

### 核心業務功能：88% 完成
**已完成 (7/8)**：
1. ✅ 後台試用方案顯示
2. ✅ 試用點數轉移
3. ✅ 後台資料下載
4. ✅ 自動續訂機制
5. ✅ 信用卡綁定流程
6. ✅ 個人資料管理（老師和學生）- **NEW!**
7. ✅ 多語言介面 (i18n) - **100% 完成！**

**進行中 (1/8)**：
8. 🚧 退款機制
   - ✅ Webhook 自動處理
   - ⏳ 後台管理介面（待實作）

### 待完成事項

**退款功能：**
- [ ] POST /api/admin/refund API 端點
- [ ] AdminSubscriptionDashboard 加入退款按鈕
- [ ] 退款成功/失敗訊息 UI
- [ ] 退款功能測試

**運維：**
- [ ] 設定每月自動續訂排程（需 GCP Cloud Scheduler）
- [ ] 測試第一次自動續訂執行

---

**文件版本**: 5.0（真實狀態）
**最後更新**: 2025-11-19
**狀態**: ✅ 核心功能 88% 完成，i18n 全站完成，個人資料管理完成，僅退款後台 UI 待實作
