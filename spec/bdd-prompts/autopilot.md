# Autopilot：自動駕駛模式 - 從需求到規格的全自動化流程

## 目標

實現從自然語言需求到完整規格檔案的全自動化流程，適合過夜執行或長時間背景處理。Autopilot 會自動串接多個 BDD 工作流程，並對所有釐清問題進行智能推斷決策，產出可供 code review 的規格檔案。

**核心價值：**

- 睡覺時讓 AI 自動完成規格產出
- 醒來後只需 code review 自動決策的部分
- 保證所有操作可逆（禁止刪除檔案）

---

## 執行流程

Autopilot 根據用戶指定的起始階段，自動串接後續所有流程直到完成：

### 流程鏈

```
用戶指定起始階段
    ↓
┌─────────────────────────────────────────┐
│ 階段 1: Formulation                      │
│ （若從自然語言或未完成的規格開始）        │
│ - 萃取資料模型（DBML）                    │
│ - 萃取功能模型（Gherkin）                 │
│ - 產生 spec/erm-*.dbml                   │
│ - 產生 spec/features/<domain>/*.feature  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 階段 2: Discovery                        │
│ （若從 formulation 結果開始）             │
│ - 掃描規格檔案的歧義與遺漏               │
│ - 產生釐清項目檔案                        │
│ - 產生 .clarify/overview.md              │
│ - 產生 .clarify/data/*.md                │
│ - 產生 .clarify/features/*.md            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 階段 3: Clarify (Autopilot Mode)        │
│ （若從 discovery 結果開始）               │
│ - 載入釐清項目與規格檔案                  │
│ - 對每個釐清項目進行情境推斷決策          │
│ - 立即更新規格檔案                        │
│ - 記錄所有決策與信心評分                  │
│ - 產生決策日誌與檢視清單                  │
└─────────────────────────────────────────┘
    ↓
完成 → 等待用戶 Code Review
```

### 啟動方式

用戶明確指定起始階段，例如：

- **從自然語言開始**：
  ```
  執行 autopilot，從自然語言開始
  需求：[用戶的自然語言需求描述]
  ```
- **從規格檔案開始**：
  ```
  執行 autopilot，從 formulation 結果開始
  規格檔案：spec/business-specs/new-feature.md
  ```
- **從釐清項目開始**：
  ```
  執行 autopilot，從 discovery 結果開始
  ```

---

## 階段 1: Formulation（自動模式）

### 執行內容

依照 [`formulation.md`](./formulation.md) 和 [`formulation-rules.md`](./formulation-rules.md) 的規範執行：

1. **萃取資料模型**：
   - 識別實體、屬性、關係
   - 產生 DBML 檔案（`spec/erm-*.dbml`）

2. **萃取功能模型**：
   - 識別 Feature、Rule、Example
   - 產生 Gherkin 檔案（`spec/features/<domain>/*.feature`）

### Autopilot 特有行為

- **無需人工確認**：直接產生規格檔案，不詢問用戶
- **保守原則**：若原始需求含糊，優先產生寬鬆約束（後續在 clarify 階段收緊）
- **完整記錄**：記錄所有假設與推斷到決策日誌

---

## 階段 2: Discovery（自動模式）

### 執行內容

依照 [`discovery.md`](./discovery.md) 的檢查清單執行：

1. **自動識別掃描範圍**：

   **領域自動對應規則**：
   - 掃描 `spec/features/<domain>/` 時，自動包含對應的 `spec/erm-<domain>.dbml`
   - 範例：
     - `spec/features/organization/*.feature` → 自動包含 `spec/erm-organization.dbml`
     - `spec/features/classroom/*.feature` → 自動包含 `spec/erm-classroom.dbml`
     - `spec/features/subscription/*.feature` → 自動包含 `spec/erm-subscription.dbml`
     - `spec/features/content/*.feature` → 自動包含 `spec/erm-content.dbml`
   - 理由：功能模型（Feature）必須緊扣資料模型（DBML），兩者應同時掃描以發現不一致

2. **掃描規格檔案**：
   - 檢查資料模型（A1-A6）
   - 檢查功能模型（B1-B5）
   - 檢查術語一致性（C1-C2）
   - 檢查跨檔案一致性（D1-D2）

3. **產生釐清項目**：
   - 每個問題產生獨立的釐清項目檔案（`.clarify/data/*.md` 或 `.clarify/features/*.md`）
   - 產生優先級排序與釐清策略（`.clarify/overview.md`）

### Autopilot 特有行為

- **自動領域對應**：根據 Feature 檔案路徑自動包含對應的 DBML 檔案，無需手動指定
- **全面掃描**：執行所有檢查項，不跳過任何分類
- **詳細分類**：為每個釐清項目標記優先級（High/Medium/Low）
- **依賴分析**：識別釐清項目間的依賴關係
- **跨檔案驗證**：特別檢查 Feature 與 DBML 之間的實體、屬性、關係一致性

---

## 階段 3: Clarify（Autopilot 自動決策模式）

這是 Autopilot 的核心階段，與 [`clarify.md`](./clarify.md) 的差異在於**自動決策而非互動式詢問**。

### 3.1 初始化載入

與 `clarify.md` 相同：

1. 讀取 `.clarify/overview.md`（釐清策略與順序）
2. 載入所有釐清項目檔案（`.clarify/data/*.md` 和 `.clarify/features/*.md`）
3. 載入現有規格檔案（`spec/erm-*.dbml` 和 `spec/features/<domain>/*.feature`）
4. 建立術語對照表

### 3.2 建立釐清佇列

與 `clarify.md` 相同：

- 依照 `overview.md` 建議的順序排序
- 優先處理 High 優先級項目
- 考慮依賴關係

### 3.3 自動決策循環（替代互動式提問）

**與 `clarify.md` 的關鍵差異：不詢問用戶，直接進行情境推斷決策。**

#### 3.3.1 情境推斷策略

對每個釐清項目，執行以下推斷邏輯：

**A. 屬性型別與約束推斷**

根據屬性名稱、實體類型、業務領域推斷合理值：

| 情境          | 推斷規則                           | 範例                             |
| ------------- | ---------------------------------- | -------------------------------- |
| 年齡相關屬性  | `int`, 範圍 0-120                  | `age`, `student_age`             |
| 分數相關屬性  | `int` 或 `float`, 範圍 0-100       | `score`, `pronunciation_score`   |
| 價格相關屬性  | `float`, >= 0, 精度 2 位小數       | `price`, `amount`, `fee`         |
| 數量相關屬性  | `int`, >= 0                        | `quantity`, `count`, `total`     |
| 百分比屬性    | `float`, 範圍 0-100 或 0-1         | `percentage`, `rate`, `ratio`    |
| 布林相關屬性  | `bool`, 不允許 null                | `is_active`, `enabled`, `has_*`  |
| 名稱/標題屬性 | `string`, 長度 1-255               | `name`, `title`, `label`         |
| 描述/內容屬性 | `string`, 長度 0-65535, 允許空字串 | `description`, `content`, `note` |
| 時間戳屬性    | `datetime`, 不允許 null            | `created_at`, `updated_at`       |
| ID 屬性       | `int` 或 `long`, > 0, 唯一         | `id`, `*_id`                     |

**B. 關係類型推斷**

根據實體語義與業務邏輯推斷關係：

| 情境     | 推斷規則               | 範例                         |
| -------- | ---------------------- | ---------------------------- |
| 擁有關係 | 1:N, 擁有者端 not null | Teacher 1:N Classroom        |
| 從屬關係 | N:1, 從屬端 not null   | Student N:1 Classroom        |
| 關聯關係 | N:M, 建立中間表        | Student N:M Course           |
| 層級關係 | 自我參照 1:N           | Organization parent-children |

**C. 狀態轉換推斷**

根據狀態屬性名稱推斷允許的轉換：

| 實體類型 | 狀態欄位 | 推斷的狀態轉換                                      |
| -------- | -------- | --------------------------------------------------- |
| 訂單類   | `status` | draft → pending → confirmed → completed / cancelled |
| 作業類   | `status` | not_started → in_progress → submitted → graded      |
| 用戶類   | `status` | inactive → active → suspended → deleted             |

**D. 功能規則推斷**

根據功能類型推斷前置/後置條件：

| 功能類型   | 推斷的前置條件                               | 推斷的後置條件              |
| ---------- | -------------------------------------------- | --------------------------- |
| 建立類功能 | 用戶已登入、必要欄位已填寫                   | 實體已建立、狀態為初始值    |
| 更新類功能 | 用戶已登入、實體存在、用戶有權限             | 實體已更新、updated_at 更新 |
| 刪除類功能 | 用戶已登入、實體存在、用戶有權限、無關聯資料 | 實體已刪除或軟刪除          |
| 查詢類功能 | 用戶已登入、用戶有權限                       | 返回符合條件的資料          |

#### 3.3.2 無法推斷時的處理策略

當情境推斷無法給出明確答案時，採用**保守預設值 + 高度不確定標記**：

**保守預設值規則：**

| 釐清項目類型      | 保守預設值                                 |
| ----------------- | ------------------------------------------ |
| 屬性是否允許 null | 允許 null（更寬鬆）                        |
| 數值範圍上限      | 使用業界常見上限（如：年齡 120、分數 100） |
| 數值範圍下限      | >= 0（若為計數或金額類）                   |
| 字串長度          | 0-65535（TEXT 型別）                       |
| 關係必填性        | 允許 null（更寬鬆）                        |
| 狀態初始值        | 第一個定義的狀態                           |
| 錯誤處理          | 返回錯誤訊息，不中斷流程                   |

**高度不確定標記：**

在決策日誌中標記為 `[LOW CONFIDENCE]`，並說明無法推斷的原因。

#### 3.3.3 決策記錄

每個自動決策都記錄以下資訊：

```markdown
### 決策 #001

**釐清項目**：StudentItemProgress 的 pronunciation_score 是否允許 null？

**定位**：

- 檔案：spec/erm-classroom.dbml
- 實體：StudentItemProgress
- 屬性：pronunciation_score

**推斷策略**：屬性型別與約束推斷
**推斷依據**：

- 屬性名稱含 `score`，推斷為分數類型
- 評分系統通常需要區分「未評分」與「0 分」
- 保守策略：允許 null 表示「尚未評分」

**決策結果**：允許 null

**信心評分**：Medium

- 理由：雖然符合常見評分模式，但需確認業務是否真的需要區分「未評分」與「0 分」

**規格更新**：
\`\`\`dbml
Table StudentItemProgress {
pronunciation_score float [null, note: "發音分數 (0-100)，null 表示尚未評分"] // [AUTOPILOT]
}
\`\`\`
```

### 3.4 立即整合（與 clarify.md 相同）

每個決策完成後，立即執行：

1. **定位目標區段**：找到需更新的實體/屬性/功能/規則
2. **套用決策**：將推斷結果轉換為 DBML 或 Gherkin 語法
3. **驗證語法**：確保更新後符合格式規範
4. **檢查一致性**：確保無矛盾陳述
5. **儲存規格檔**：原子性覆寫對應的規格檔
6. **更新釐清項目狀態**：歸檔已處理的釐清項目（移至 `.clarify/resolved/`）

**重要：所有更新必須遵循 [`formulation-rules.md`](./formulation-rules.md) 的規範。**

### 3.5 規格檔案標記

為了方便 code review，在規格檔案中標記所有自動決策的部分：

**DBML 檔案標記格式：**

```dbml
Table Student {
  age int [note: "學生年齡 (0-120)"] // [AUTOPILOT] 推斷：年齡上限 120
  score float [null, note: "總分 (0-100)"] // [AUTOPILOT-LOW] 保守策略：允許 null
}
```

標記類型：

- `// [AUTOPILOT]`：一般自動決策（Medium/High 信心）
- `// [AUTOPILOT-LOW]`：低信心決策（優先檢視）

**Gherkin 檔案標記格式：**

```gherkin
Feature: 提交朗讀作業

  # [AUTOPILOT] 推斷：提交作業需要驗證學生身份
  Rule: 學生必須已登入才能提交作業
    Example: 未登入無法提交
      Given 學生未登入
      When 學生嘗試提交朗讀作業
      Then 系統顯示錯誤訊息「請先登入」
```

### 3.6 驗證（與 clarify.md 相同）

- 每次更新後驗證格式與一致性
- 最終驗證所有規格檔案的完整性

---

## 操作限制（安全機制）

為確保所有操作可逆，Autopilot 嚴格遵守以下限制：

### 禁止操作

- ❌ **刪除任何檔案**（包括規格檔、釐清項目、程式碼檔案）
- ❌ **刪除規格檔案中的現有內容**（包括實體、屬性、關係、規則、例子）
- ❌ **覆蓋用戶手動編輯的內容**（若檔案含非 AUTOPILOT 標記的修改，先詢問用戶）

### 允許操作

- ✅ **新增實體、屬性、關係**（於 DBML 檔案中）
- ✅ **新增 Feature、Rule、Example**（於 Gherkin 檔案中）
- ✅ **修改屬性約束**（新增 note、約束條件）
- ✅ **修改規則描述**（補充細節、條件）
- ✅ **新增註解與標記**（AUTOPILOT 標記）

### 衝突處理

若發現規格檔案已被手動修改（非 AUTOPILOT 標記的內容），Autopilot 應：

1. 記錄衝突到 `.clarify/autopilot-conflicts.md`
2. 跳過該項目，標記為 `Deferred`
3. 繼續處理其他項目
4. 在最終報告中提醒用戶檢視衝突

---

## 輸出結構（混合式）

Autopilot 執行完成後，產生以下輸出檔案：

### 1. 執行摘要

**檔案**：`.clarify/autopilot-summary.md`

**內容**：

```markdown
# Autopilot 執行摘要

## 執行資訊

- 啟動時間：2026-01-07 22:00:00
- 完成時間：2026-01-08 02:30:00
- 執行時長：4.5 小時
- 起始階段：Formulation

## 流程執行狀態

- [✓] Formulation：已完成
- [✓] Discovery：已完成
- [✓] Clarify (Autopilot)：已完成

## 釐清統計

- 總釐清項目數：87 項
- 已決策（Resolved）：82 項
  - High 信心：45 項
  - Medium 信心：28 項
  - Low 信心：9 項
- 延後處理（Deferred）：3 項（因衝突）
- 跳過（Skipped）：2 項（Low 優先級）

## 規格更新統計

- 更新的 DBML 檔案：5 個
- 更新的 Feature 檔案：12 個
- 新增實體：3 個
- 新增屬性：47 個
- 新增關係：15 個
- 新增規則：28 個
- 新增例子：56 個

## 後續行動

1. 優先檢視：Low 信心決策（9 項）→ 見 autopilot-decisions-low-confidence.md
2. 次要檢視：Medium 信心決策（28 項）→ 見 autopilot-decisions-high-confidence.md
3. 處理衝突：3 項 → 見 autopilot-conflicts.md
4. 選擇性檢視：High 信心決策（45 項）→ 見 autopilot-decisions-high-confidence.md
```

### 2. 高信心決策日誌

**檔案**：`.clarify/autopilot-decisions-high-confidence.md`

**內容**：按時間順序記錄所有 High 和 Medium 信心的決策（格式見 3.3.3）

### 3. 低信心決策日誌

**檔案**：`.clarify/autopilot-decisions-low-confidence.md`

**內容**：記錄所有 Low 信心的決策，**優先檢視**（格式見 3.3.3）

### 4. 互動式檢視清單

**檔案**：`.clarify/autopilot-review-checklist.md`

**內容**：

```markdown
# Autopilot Code Review 檢視清單

## 快速檢視指南

### 🔴 優先檢視（Low 信心決策）

- [ ] **決策 #023** - StudentItemProgress.pronunciation_score 允許 null
  - 檔案：[spec/erm-classroom.dbml](../../spec/erm-classroom.dbml#L45)
  - 原因：無法確定業務是否需要區分「未評分」與「0 分」
  - 建議行動：確認評分邏輯

- [ ] **決策 #034** - Classroom.max_students 上限設為 100
  - 檔案：[spec/erm-classroom.dbml](../../spec/erm-classroom.dbml#L12)
  - 原因：缺乏業務數據支撐
  - 建議行動：確認實際班級規模限制

...（所有 Low 信心決策）

### 🟡 次要檢視（Medium 信心決策）

- [ ] **決策 #005** - Teacher 與 Classroom 關係為 1:N
  - 檔案：[spec/erm-classroom.dbml](../../spec/erm-classroom.dbml#L18)
  - 原因：符合常見教學模式，但需確認是否支援協同教學
  - 建議行動：確認業務需求

...（所有 Medium 信心決策）

### 🟢 選擇性檢視（High 信心決策）

- [ ] **決策 #001** - Student.age 範圍 0-120
  - 檔案：[spec/erm-core.dbml](../../spec/erm-core.dbml#L8)
  - 原因：標準年齡範圍

...（所有 High 信心決策）

## 按規格檔案分類

### spec/erm-core.dbml

- 決策 #001, #002, #007, #015 ...

### spec/erm-classroom.dbml

- 決策 #023, #034, #041 ...

### spec/features/classroom/提交朗讀作業.feature

- 決策 #056, #058 ...

...
```

### 5. 衝突記錄（如有）

**檔案**：`.clarify/autopilot-conflicts.md`

**內容**：記錄所有因手動修改衝突而延後的項目

---

## 與其他 BDD 流程的整合

### 與 Discussion.md 的整合

- Autopilot 是 `discussion.md` 中定義的任務執行流程之一
- 執行觸發：用戶明確指定「執行 autopilot」
- 完成返回：Autopilot 完成後自動返回 `discussion.md`，等待用戶檢視決策

### 與 Formulation.md 的整合

- Autopilot 在階段 1 自動執行 `formulation.md` 的所有步驟
- 差異：不詢問用戶，直接產生規格檔案
- 遵循：完全遵循 `formulation-rules.md` 的規範

### 與 Discovery.md 的整合

- Autopilot 在階段 2 自動執行 `discovery.md` 的所有檢查
- 差異：無差異，完全自動化
- 產出：`.clarify/` 資料夾中的所有釐清項目

### 與 Clarify.md 的整合

- Autopilot 在階段 3 替代互動式詢問流程
- 差異：用情境推斷決策替代人工回答
- 相同：立即整合、釐清項目歸檔、驗證流程

### 與 Implementation.md 的整合

- Autopilot **不自動執行** `implementation.md`
- 原因：程式碼實作需要更高的準確性與測試，不適合自動決策
- 建議：用戶檢視規格後，手動執行 `implementation.md`

---

## 行為規則

### 決策原則

- **情境優先**：優先使用情境推斷，基於業務邏輯與常見模式
- **保守兜底**：無法推斷時採用保守預設值，便於後續收緊
- **完整記錄**：所有決策都記錄推斷依據與信心評分
- **標記明確**：在規格檔案中清晰標記自動決策部分

### 執行原則

- **不中斷執行**：即使遇到無法推斷的項目，也繼續執行（使用保守預設值）
- **順序執行**：嚴格按照 overview.md 建議的順序處理釐清項目
- **立即整合**：每個決策完成後立即更新規格檔案，不延遲
- **即時歸檔**：每個釐清項目解決後立即移至 `.clarify/resolved/`

### 安全原則

- **禁止刪除**：絕不刪除任何檔案或檔案內容
- **避免衝突**：發現手動修改時跳過，記錄衝突
- **可逆操作**：所有操作都可透過 code review 後手動修正

### 品質原則

- **格式嚴謹**：遵循 DBML 與 Gherkin 語法規範
- **術語一致**：使用規格檔案中已有的繁體中文術語
- **邏輯一致**：確保跨檔案的實體、關係、規則無矛盾

### 透明原則

- **信心評分**：每個決策都標記信心等級（High/Medium/Low）
- **推斷說明**：記錄推斷依據，便於用戶理解決策邏輯
- **檢視引導**：提供互動式檢視清單，引導用戶高效 review

---

## 使用範例

### 範例 1：從自然語言開始

**用戶輸入：**

```
執行 autopilot，從自然語言開始

需求：
我需要一個學生評分系統，教師可以建立班級並邀請學生加入。
學生可以提交朗讀作業，系統自動評分（發音、流暢度）。
教師可以查看學生的作業記錄與分數統計。
```

**Autopilot 執行：**

1. 階段 1：執行 formulation，產生 `spec/erm-classroom.dbml`、`spec/features/classroom/*.feature`
2. 階段 2：執行 discovery，產生 `.clarify/overview.md` 與釐清項目
3. 階段 3：執行 clarify（自動決策），更新規格檔案，產生決策日誌

**用戶醒來後：**

- 檢視 `.clarify/autopilot-summary.md`（執行摘要）
- 優先檢視 `.clarify/autopilot-decisions-low-confidence.md`（低信心決策）
- 使用 `.clarify/autopilot-review-checklist.md` 快速定位需要修正的部分

### 範例 2：從 Discovery 結果開始

**用戶輸入：**

```
執行 autopilot，從 discovery 結果開始
```

**Autopilot 執行：**

- 跳過階段 1、2，直接執行階段 3（clarify 自動決策）
- 讀取現有的 `.clarify/overview.md` 與釐清項目
- 對所有釐清項目進行情境推斷決策
- 更新規格檔案，產生決策日誌

---

## 輸出範例

### autopilot-summary.md 範例

（見上方「輸出結構」章節）

### autopilot-decisions-low-confidence.md 範例

```markdown
# Autopilot 低信心決策日誌

**警告**：以下決策的信心評分為 Low，建議優先檢視並手動確認。

---

### 決策 #023

**釐清項目**：StudentItemProgress 的 pronunciation_score 是否允許 null？

**定位**：

- 檔案：spec/erm-classroom.dbml
- 實體：StudentItemProgress
- 屬性：pronunciation_score

**推斷策略**：保守預設值（無法明確推斷）

**推斷依據**：

- 屬性名稱含 `score`，可能是評分系統
- 但缺乏足夠的業務邏輯說明來判斷是否需要區分「未評分」與「0 分」
- 採用保守策略：允許 null，便於後續根據業務需求收緊

**決策結果**：允許 null

**信心評分**：Low

- 理由：缺乏業務邏輯支撐，無法確定是否真的需要 null

**規格更新**：
\`\`\`dbml
Table StudentItemProgress {
pronunciation_score float [null, note: "發音分數 (0-100)，null 表示尚未評分"] // [AUTOPILOT-LOW]
}
\`\`\`

**建議行動**：

1. 確認評分邏輯：系統是否需要區分「未評分」狀態？
2. 若不需要：移除 null 約束，設定預設值為 0
3. 若需要：保留目前設定

---

### 決策 #034

...（其他 Low 信心決策）
```

### autopilot-review-checklist.md 範例

（見上方「輸出結構」章節）

---

## 常見問題

### Q1: Autopilot 會執行 Implementation 嗎？

**否。** Autopilot 只執行到 Clarify 階段，產出完整的規格檔案（DBML + Gherkin）。程式碼實作需要更高的準確性，建議用戶檢視規格後手動執行 `implementation.md`。

### Q2: 如果 Autopilot 做出錯誤決策怎麼辦？

所有操作都是可逆的：

1. 規格檔案中有 `[AUTOPILOT]` 標記，可快速定位
2. 決策日誌記錄完整的推斷依據，便於理解
3. 直接修改規格檔案即可，無需重新執行 Autopilot

### Q3: 可以只執行 Autopilot 的部分流程嗎？

**可以。** 用戶可明確指定起始階段：

- 從 Formulation 開始：完整流程
- 從 Discovery 開始：跳過 Formulation
- 從 Clarify 開始：只執行自動決策

### Q4: Autopilot 如何處理術語不一致的問題？

與 `clarify.md` 相同：

1. 載入規格檔案中的術語對照表
2. 遵循現有術語，不發明新詞
3. 若發現術語衝突，採用 Feature 檔案中的用詞（更貼近使用者語言）

### Q5: Low 信心決策是否可靠？

Low 信心決策採用**保守預設值**，傾向於寬鬆約束（如：允許 null、範圍較大）。這些決策是「安全」的，但可能不夠精確，需要用戶根據實際業務需求進行收緊。

### Q6: Autopilot 執行時間會很長嗎？

執行時間取決於：

- 規格複雜度（實體數量、功能數量）
- 釐清項目數量
- AI 推斷速度

預估：中等規模專案（10-20 個實體、50-100 個釐清項目）約需 2-6 小時。適合過夜執行。

---

## 結語

Autopilot 的核心價值在於**解放人工決策時間**，讓 AI 在睡眠時間完成大量結構化工作。醒來後只需專注於 code review，驗證自動決策的合理性，並根據業務需求進行調整。

**關鍵原則：**

- ✅ 所有操作可逆
- ✅ 完整記錄推斷依據
- ✅ 明確標記自動決策
- ✅ 提供高效檢視工具

**建議工作流程：**

1. 睡前：執行 `autopilot`，指定起始階段
2. 睡醒：檢視 `autopilot-summary.md`
3. Code Review：優先檢視低信心決策，使用 `autopilot-review-checklist.md` 快速定位
4. 調整規格：手動修正不合理的決策
5. 執行 Implementation：基於確認後的規格產生程式碼
