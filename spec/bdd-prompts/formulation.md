# Formulation：從規格文本產出規格模型

## 目標

從原始規格文本中萃取並結構化為規格模型，包含：

1. **業務實體參考模型 (Business Entity Reference Model)**：以 DBML 格式描述業務概念的實體關係，作為工程師的參考建議
2. **功能模型 (Functional Model)**：以 Gherkin Language 描述功能規格（最終驗收標準）

---

## 重要定位說明

### 資料模型的角色定位

**DBML 資料模型 = 業務層面的參考建議，非技術實作規範**

- ✅ **Owner 的職責**：用 DBML 表達「業務上有哪些實體、它們之間的關係、業務規則」
- ✅ **工程師的權限**：可自由調整技術細節（資料型別、索引策略、表結構、正規化程度等）
- ⚠️ **明確界線**：Owner 不做資料庫設計決策，只表達業務需求

**實際分工範例**：

| 業務需求（Owner 描述）     | 技術實作（工程師決定）         |
| -------------------------- | ------------------------------ |
| 「學生需要有姓名和生日」   | 決定用 VARCHAR(100) 還是 TEXT  |
| 「學生可以屬於多個機構」   | 決定用中介表還是 JSONB 陣列    |
| 「訂閱有開始和結束日期」   | 決定用 DATETIME 還是 TIMESTAMP |
| 「Email 應該唯一識別學生」 | 決定索引策略、唯一約束實作方式 |

### 功能模型的角色定位

**Gherkin Feature Files = 最終驗收標準（必須符合）**

- ✅ 這是 Owner 定義的「業務行為規格」
- ✅ 工程師實作後必須通過這些測試案例
- ✅ 這是 Owner 與工程師之間的「契約」

---

## 執行步驟

### 1. 從規格中萃取業務實體參考模型 (Business Entity Reference Model)

從原始規格文本中識別並萃取業務實體及其關係，依照 [`formulation-rules.md`](./formulation-rules.md) 中的「資料模型萃取規則」執行：

- A. 識別「業務實體 (Business Entity)」
- B. 萃取實體的「業務屬性 (Business Attribute)」
- C. 識別實體之間的「業務關係 (Business Relationship)」
- D. 記錄實體的業務說明與規則

**⚠️ 重要提醒**：DBML 中的資料型別、約束條件僅為「建議參考」，工程師可依技術需求調整。

### 2. 從規格中萃取功能階層：Feature > Rule > Example

依照 [`formulation-rules.md`](./formulation-rules.md) 中的「功能模型萃取規則」執行：

- A. 萃取「功能 (Feature)」
- B. 萃取功能的「規則 (Rule)」
- C. 萃取規則的「例子 (Example)」

### 3. 輸出規格檔案

依照 [`formulation-rules.md`](./formulation-rules.md) 中的「輸出格式規範」執行：

- A. 輸出業務實體參考模型（DBML 格式，供工程師參考）→ 依模組與業務領域分為 5 個檔案：
  - 機構模組（Organization）：
    - `spec/erm-core.dbml`（標註：業務參考，非強制實作）
    - `spec/erm-organization.dbml`
    - `spec/erm-classroom.dbml`
    - `spec/erm-subscription.dbml`
    - `spec/erm-content.dbml`
  - 個人教師模組（Individual Teacher）：
    - `spec/individual-teacher/erm-core.dbml`
    - `spec/individual-teacher/erm-organization.dbml`
    - `spec/individual-teacher/erm-classroom.dbml`
    - `spec/individual-teacher/erm-subscription.dbml`
    - `spec/individual-teacher/erm-content.dbml`
- B. 輸出功能驗收規格（Gherkin Language 格式，為最終驗收標準）→ 依模組放置：
  - 機構模組：`spec/features/<domain>/*.feature`
  - 個人教師模組：`spec/individual-teacher/features/<domain>/*.feature`

---

## 核心原則

**詳見 [`formulation-rules.md`](./formulation-rules.md)**，關鍵原則包括：

- **無腦補或任意假設原則**：嚴格遵守原始規格文本內容，不擅自假設或補充
- **規格表達格式**：DBML (資料模型) 與 Gherkin Language (功能模型)
- **原子化規則**：每個 Rule 只驗證一件事
- **句型一致性**：Feature File 中的 Step 定義保持句型一致

---

## Owner 開發原則對齊

本文件僅產出**規格模型**，不涉及實作或修復。若涉及 Bug 修復或程式變更，需遵守
[docs/OWNER_BUG_FIX_GUIDE.md](../../docs/OWNER_BUG_FIX_GUIDE.md) 的流程與範圍限制：

### Owner 的職責範圍

✅ **可以做的**：

- 用 DBML 描述業務實體和關係（作為參考建議）
- 用 Gherkin 定義功能規格和驗收標準（工程師必須遵守）
- 釐清業務規則和流程

❌ **不可以做的**：

- 決定資料庫表結構、資料型別、索引策略
- 修改 `backend/models/`、`backend/migrations/` 等資料庫相關檔案
- 決定技術實作細節（如：用 JSONB 還是關聯表、正規化程度等）

### 職責交接點

| 階段     | Owner                                 | 工程師             |
| -------- | ------------------------------------- | ------------------ |
| 需求釐清 | ✅ 主導                               | 協助釐清技術可行性 |
| 規格產出 | ✅ 產出 DBML（參考）+ Feature（驗收） | 審查業務邏輯正確性 |
| 技術設計 | 🔍 檢視（不決策）                     | ✅ 決定資料庫設計  |
| 實作開發 | ❌ 不參與                             | ✅ 負責實作        |
| 驗收測試 | ✅ 依 Feature 驗收                    | ✅ 確保通過測試    |

### 規格產出原則

- DBML 資料模型 = **業務參考建議**（工程師可調整）
- Gherkin Feature Files = **最終驗收標準**（工程師必須符合）
- 產出的規格需**完整明確**，避免工程師二次猜測業務邏輯
- 技術細節由工程師決定，Owner 不跨界
