# 機構模組一頁式介紹網站 - 實現指南

## 📋 概述

這是一個為 Duotopia 機構版打造的專業落地頁（Landing Page），展示系統的核心優勢和報價方案。

**功能特性：**
- ✅ 核心優勢展示（AI 自動批改、全機構管理、數據驅動決策）
- ✅ 實時報價計算機（支援一年/兩年約）
- ✅ 機構資料收集表單（用於 CRM 集成）
- ✅ LINE 客服 QR Code 展示
- ✅ 響應式設計（Mobile/Tablet/Desktop）
- ✅ 專業 UI/UX 設計

---

## 🚀 快速開始

### 1. 路由配置

在 `frontend/src/App.tsx` 或你的路由文件中新增：

```typescript
import { lazy } from 'react';

const OrgLandingPage = lazy(() => 
  import('@/pages/public/org-landing').then(m => ({ default: m.default }))
);

// 在 Router 中
<Route path="/org-landing" element={<OrgLandingPage />} />
```

### 2. 訪問頁面

```
http://localhost:5173/org-landing
```

### 3. 部署到生產環境

```bash
npm run build
# 然後部署 dist 文件夾到你的服務器
```

**公開 URL 建議：**
```
https://duotopia.tw/org-landing
或
https://org.duotopia.tw
或
https://business.duotopia.tw
```

---

## 🎯 頁面結構

### 章節分佈

```
1. Navigation Bar (置頂導航)
   ├─ Logo
   └─ LINE 客服按鈕

2. Hero Section (英雄區)
   ├─ 主標題：「AI 助教，不再是奢侈品」
   ├─ 副標題：競爭優勢簡介
   ├─ CTA 按鈕：查看報價 / 聯絡業務
   └─ 問題 vs 解決方案對比

3. 核心優勢展示
   ├─ ⚡ AI 自動批改
   ├─ 👥 全機構管理
   └─ 📊 數據驅動決策

4. ROI 計算區段
   ├─ 4 大關鍵指標
   └─ 成本對比表

5. 報價計算機 (交互式)
   ├─ 學生數、練習次數、句數滑桿
   ├─ 合約類型選擇（一年/兩年約）
   ├─ 實時報價摘要
   └─ 下載報價單 / 詢問細節按鈕

6. 適用對象
   ├─ 🏫 中小型補習班
   ├─ 🏢 連鎖補習班集團
   └─ 🎓 私立學校

7. CTA Section
   ├─ 行動號召
   └─ 填寫表單 / 掃描 QR Code

8. Footer (頁腳)
   ├─ 公司信息
   ├─ 快速鏈接
   └─ 聯絡方式
```

---

## 💻 交互功能詳解

### 1. 報價計算機

**參數說明：**
- **學生總數**：50-500 (滑桿調整)
- **每週練習次數**：1-7 次
- **每次練習句數**：5-30 句
- **教師數**：1-100 位
- **合約類型**：一年約 / 兩年約

**計算公式：**
```
年度點數 = 學生數 × 週練習次數 × 句數 × 52週
點數費用 = 年度點數 × 0.0015 TWD
教師授權費 = (教師數 - 贈送數) × 月費 × 12 × 合約年數

一年約贈送教師：3 位
兩年約贈送教師：5 位

節省額 = (一年約 × 2) - 兩年約
```

**實時更新：**
- 每次調整滑桿後立即計算顯示
- 顯示預估點數、費用、節省額

### 2. 表單提交

**收集欄位：**
- 機構名稱 *
- 聯絡人姓名 *
- 電子郵件 *
- 手機號碼 *
- 所在城市
- 英文老師數

**表單提交後：**
1. 驗證必填欄位
2. 顯示成功提示
3. 清空表單
4. 關閉 Modal

**TODO：實際實現時需要連接到：**
- CRM 系統 (e.g., HubSpot, Salesforce)
- Email 服務 (自動寄送報價單)
- 業務通知系統 (Slack, Teams)

### 3. LINE 客服 QR Code

**設計要點：**
- 展示 QR Code 圖片
- 提供 LINE ID
- 營業時間資訊
- 平均回覆時間

**TODO：實際實現時需要：**
1. 上傳真實 QR Code 圖片到 `public/images/line-qrcode.png`
2. 更新 LINE ID 和營業時間

---

## 🎨 設計特點

### 顏色方案
- **主色**：藍色 (`#3b82f6`) - 專業、信任
- **輔色**：紫色 (`#a855f7`) - 創新、科技感
- **強調色**：綠色 (`#22c55e`) - 正面、成長

### 排版
- **標題**：Bold, 4xl-6xl
- **副標題**：SemiBold, 2xl-3xl
- **本文**：Regular, lg
- **說明文字**：Regular, sm

### 響應式設計
```
Mobile (< 768px)：
  - 單欄佈局
  - 較小字體
  - 移除複雜效果

Tablet (768px - 1024px)：
  - 兩欄佈局
  - 中等字體
  - 部分效果啟用

Desktop (> 1024px)：
  - 多欄佈局
  - 全尺寸字體
  - 全部效果啟用
```

---

## 📊 核心內容亮點

### 市場定位

**我們不是 Duolingo**
- ❌ 沒有老師介入
- ❌ 無法追蹤班級進度
- ❌ 不符合台灣補習班需求

**我們的定位：「AI + 真人老師」的 B2B2C 模式**
- ✅ 目標：補習班、學校（B2B）
- ✅ 使用者：老師、學生（B2C）
- ✅ 定位：老師的 AI 助教平台

### 競爭優勢

| 維度 | Duolingo | ELSA | **Duotopia** |
|------|----------|------|--------------|
| 目標市場 | B2C 個人 | B2C 個人 | **B2B 機構** |
| 使用場景 | 自學 | 自學 | **課堂教學** |
| 老師角色 | 無 | 無 | **核心** |
| 班級管理 | ❌ | ❌ | **✅** |
| 作業指派 | ❌ | ❌ | **✅** |
| 進度追蹤 | 個人 | 個人 | **班級+機構** |

### ROI 計算

**時間節省**
- 批改時間：24 小時 → 5 分鐘（95% 節省）
- 老師日常：40% 時間被解放

**成本對比**
- 自研系統：200-500 萬 + 3-6 個月
- 買教材授權：100-300 萬 + 持續費用
- **Duotopia**：按使用量計費 + 立即使用

---

## 🔧 技術棧

### 前端框架
- **React 18** - UI 框架
- **TypeScript** - 類型安全
- **Tailwind CSS** - 樣式系統
- **Lucide React** - 圖標

### 依賴組件
- Toast 通知系統 (需要自行實現或使用 library)

### 路由
- React Router v6

---

## 📱 表單集成指南

### 後端 API 設計

**建議端點：**
```
POST /api/org-inquiries
```

**請求體：**
```json
{
  "schoolName": "ABC 補習班",
  "contactName": "王小明",
  "email": "wang@abc.edu.tw",
  "phone": "0912345678",
  "city": "Taipei",
  "teacherCount": 10,
  "estimatedPrice": 67311,
  "contractType": "2years"
}
```

**響應：**
```json
{
  "id": "inq_12345",
  "status": "pending",
  "quotePdfUrl": "https://...",
  "message": "感謝您的垂詢！業務人員將在 24 小時內聯絡您。"
}
```

### Email 模板

**自動回覆郵件主題：**
```
Duotopia 機構報價單 - ABC 補習班
```

**內容：**
```
尊敬的王小明，

感謝您對 Duotopia 的興趣！

以下是您的機構報價詳情：
- 機構名稱：ABC 補習班
- 預估年度點數：234,000
- 合約類型：兩年約
- 預估報價：NT$ 67,311

詳細報價單已附件提供，請查收。

我們的業務團隊將在 24 小時內聯絡您，為您解答任何問題。

如有緊急需求，請聯絡我們的 LINE 客服：
LINE ID: @duotopia_org

最佳問候，
Duotopia 團隊
```

---

## 🎯 後續優化方向

### Phase 2 - 分析與優化

- [ ] 集成 Google Analytics / Mixpanel
  - 追蹤用戶流量、轉化率
  - 了解用戶行為

- [ ] A/B 測試
  - 測試不同的 CTA 按鈕文案
  - 測試報價計算機的預設值

- [ ] SEO 優化
  - Meta tags（標題、描述）
  - 結構化數據 (Schema.org)
  - Open Graph（社群分享）

### Phase 3 - 功能擴展

- [ ] 多語言支援 (English, 简体中文)
- [ ] 線上聊天支援 (Intercom, Drift)
- [ ] 動畫效果 (Framer Motion)
- [ ] 深色模式 (Dark Mode)

---

## 🚨 注意事項

### 安全性
- ✅ 表單驗證（客戶端 + 伺服器端）
- ✅ 不存儲敏感資訊在前端
- ✅ HTTPS only
- ✅ CSRF protection

### 性能
- ✅ 圖片最佳化（WebP format）
- ✅ 代碼分割（Lazy loading）
- ✅ 緩存策略
- ✅ 最小化 JavaScript Bundle

### 可訪問性
- ✅ WCAG 2.1 AA 標準
- ✅ 鍵盤導航支援
- ✅ Screen reader 友善
- ✅ 充足的色彩對比

---

## 📞 聯絡方式

**有任何問題或建議？**

- 📧 Email: org@duotopia.tw
- 📱 Phone: 0912-345-678
- 💬 LINE: @duotopia_org
- 🌐 Website: https://duotopia.tw

---

**最後更新：2026-01-27**
**Branch: feat/org-intro-pricing-page**
