# Duotopia 機構版一頁式介紹網站

## 🎯 專案概述

這個專案為 Duotopia 機構版（B2B SaaS）打造一個專業的落地頁，用於吸引和轉化補習班、學校等教育機構客戶。

**核心目標：**
- ✅ 展示 Duotopia 相對於傳統方案的核心優勢
- ✅ 提供實時報價計算工具
- ✅ 收集機構決策者的聯絡資訊
- ✅ 提供客服支持入口 (LINE QR Code)

---

## 📁 檔案結構

```
frontend/src/pages/public/org-landing/
├── OrgLandingPage.tsx              # 主頁面元件（完整實現）
├── index.tsx                        # 路由出口
├── IMPLEMENTATION_GUIDE.md          # 前端實現指南

backend/routers/
└── org_inquiries_api_guide.md      # 後端 API 實現指南

docs/
└── org-intro-pricing-page/         # 設計文檔（可選）
    ├── market-analysis.md
    ├── competitive-advantage.md
    └── pricing-strategy.md
```

---

## ✨ 主要功能

### 1️⃣ 優勢展示

**問題 vs 解決方案對比**
- 展示訪間現況的 6 大痛點
- 對應 Duotopia 的 6 大解決方案

**核心優勢卡片**
- ⚡ AI 自動批改 - 節省 40-60% 時間
- 👥 全機構管理 - 支援多分校、多層級權限
- 📊 數據驅動決策 - 實時 Dashboard

**ROI 計算**
- 4 大關鍵指標視覺化
- 成本對比（自研 vs 教材 vs Duotopia）

### 2️⃣ 報價計算機

**可調參數：**
- 🎓 學生總數（50-500）
- 📝 每週練習次數（1-7）
- ✏️ 每次練習句數（5-30）
- 👨‍🏫 教師授權數（1-100）
- 📅 合約類型（一年 / 兩年）

**實時計算：**
- 年度點數估算
- 點數費用
- 教師授權費用
- 兩年約節省額
- 直觀的報價摘要

### 3️⃣ 機構資料收集

**表單欄位：**
- 機構名稱 *
- 聯絡人姓名 *
- 電郵 *
- 手機號碼 *
- 所在城市
- 教師數量

**後續處理：**
- 自動發送確認郵件
- 同步到 CRM (HubSpot)
- 通知銷售團隊 (Slack)

### 4️⃣ LINE 客服

**提供：**
- QR Code 掃描入口
- LINE ID 顯示
- 營業時間
- 平均回覆時間

---

## 🚀 快速開始

### 前端集成

**1. 路由配置 (React Router v6)**

```typescript
import { lazy } from 'react';

const OrgLandingPage = lazy(() => 
  import('@/pages/public/org-landing').then(m => ({ default: m.default }))
);

// 在 Router 配置中
<Route path="/org-landing" element={<OrgLandingPage />} />
```

**2. 訪問頁面**

```
開發：http://localhost:5173/org-landing
生產：https://duotopia.tw/org-landing
```

### 後端集成

**1. 建立數據庫表**

```bash
alembic upgrade head  # 執行遷移
```

**2. 新增路由**

```python
from backend.routers import org_inquiries
app.include_router(org_inquiries.router)
```

**3. 配置環境變數**

```bash
SMTP_SERVER=smtp.gmail.com
HUBSPOT_API_KEY=your_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

---

## 📊 技術棧

### 前端
- React 18
- TypeScript 5.3
- Tailwind CSS 3
- Lucide React (圖標)
- React Router v6

### 後端
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- PostgreSQL
- Pydantic v2

### 外部服務
- 📧 SMTP (Email)
- 🌐 HubSpot (CRM)
- 💬 Slack (通知)

---

## 📈 預期數據流

```
訪問者
  ↓
查看優勢和報價
  ↓
使用報價計算機
  ↓
填寫表單或掃描 LINE QR Code
  ↓
✅ 表單提交
  ├─ → 寄送確認郵件
  ├─ → 同步 CRM (HubSpot)
  ├─ → 通知銷售 (Slack)
  └─ → 業務跟進
```

---

## 🎨 設計原則

### 色彩方案
- 🔵 主色：藍色 (`#3b82f6`) - 專業、信任
- 🟣 輔色：紫色 (`#a855f7`) - 創新、科技
- 🟢 強調：綠色 (`#22c55e`) - 成長、正面

### 排版
- **標題**：Bold, 4xl-6xl
- **副標題**：SemiBold, 2xl-3xl
- **本文**：Regular, lg
- **說明**：Regular, sm

### 響應式
- 📱 Mobile < 768px
- 📱 Tablet 768-1024px
- 💻 Desktop > 1024px

---

## 📋 內容亮點

### 市場定位

**我們的優勢 vs 競爭對手**

| 方面 | Duolingo | ELSA/TalkMe | **Duotopia** |
|------|----------|------------|------------|
| **目標市場** | B2C 個人 | B2C 個人 | **B2B 機構** |
| **使用場景** | 自學 | 自學 | **課堂教學** |
| **老師角色** | 無 | 無 | **核心** |
| **班級管理** | ❌ | ❌ | **✅** |
| **作業系統** | ❌ | ❌ | **✅** |
| **進度追蹤** | 個人 | 個人 | **班級+機構** |

### ROI 計算

**時間節省**
- 批改時間從 24 小時 → 5 分鐘
- 老師日常時間節省 40%

**成本對比**
- 自研系統：200-500 萬 + 3-6 個月
- 教材授權：100-300 萬 + 持續費用
- **Duotopia**：按使用量計費 + 立即可用

---

## 🔄 集成檢查清單

### 前端
- [ ] 複製 `OrgLandingPage.tsx` 到 `frontend/src/pages/public/org-landing/`
- [ ] 更新路由配置
- [ ] 確保 Lucide React 已安裝
- [ ] 確保 Toast 組件可用
- [ ] 在 `public/images/` 中放置 LINE QR Code 圖片

### 後端
- [ ] 建立 `org_inquiries` 資料庫表
- [ ] 實現 `/api/org-inquiries` 路由
- [ ] 配置 SMTP (Email)
- [ ] 配置 HubSpot API 集成
- [ ] 配置 Slack Webhook
- [ ] 設定環境變數

### 部署
- [ ] 測試表單提交
- [ ] 測試 Email 發送
- [ ] 測試 CRM 同步
- [ ] 測試 Slack 通知
- [ ] 驗證響應式設計
- [ ] 驗證 SEO (Meta tags)

---

## 📞 後續支援

### Phase 2 - 分析與優化
- [ ] Google Analytics 集成
- [ ] A/B 測試
- [ ] 轉化率優化 (CRO)
- [ ] SEO 優化

### Phase 3 - 功能擴展
- [ ] 多語言支援 (EN, 簡中)
- [ ] 線上客服聊天 (Intercom)
- [ ] 動畫效果 (Framer Motion)
- [ ] 深色模式

---

## 🐛 常見問題

**Q: 報價計算機的數值是否準確？**
A: 報價計算是基於 spec 文檔中定義的公式，但實際價格由業務確認。

**Q: 如何修改報價計算公式？**
A: 在 `OrgLandingPage.tsx` 的 `calculateQuote()` 函數中修改。

**Q: 表單資料存儲在哪裡？**
A: 存儲在 `org_inquiries` 資料表，同時同步到 HubSpot CRM。

**Q: 如何自訂 LINE QR Code？**
A: 替換 `public/images/line-qrcode.png` 並更新組件中的圖片路徑。

---

## 🔒 安全性與合規

- ✅ 表單客戶端和伺服器端驗證
- ✅ HTTPS only
- ✅ CSRF 保護
- ✅ 敏感資訊不存儲在前端
- ✅ WCAG 2.1 AA 可訪問性標準
- ✅ GDPR 友善 (隱私政策鏈接)

---

## 📝 文檔

詳細實現指南：
- 📖 [前端實現指南](./frontend/src/pages/public/org-landing/IMPLEMENTATION_GUIDE.md)
- 📖 [後端 API 指南](./backend/routers/org_inquiries_api_guide.md)

---

## 👥 團隊聯絡

- 📧 org@duotopia.tw
- 📱 0912-345-678
- 💬 LINE: @duotopia_org

---

**建立日期：2026-01-27**
**Branch：feat/org-intro-pricing-page**
**狀態：✅ 完成 (前端) / ⏳ 等待後端集成**
