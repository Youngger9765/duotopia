# 規格表達規則

## 核心原則：無腦補或任意假設原則

**嚴格遵守原始規格文本內容，如果需求中沒有明確寫出的欄位、規則、條件或行為，就不要加入。不要擅自假設、推測或補充任何需求中不存在的內容。**

---

# 規格表達格式

## DBML 格式（資料模型）

用於描述實體關係模型 (ERM)，依業務領域分別寫入不同的 DBML 檔案：

- `spec/erm-core.dbml`：核心用戶與認證相關實體
- `spec/erm-organization.dbml`：機構與組織相關實體
- `spec/erm-classroom.dbml`：班級與課程相關實體
- `spec/erm-subscription.dbml`：訂閱與付費相關實體
- `spec/erm-content.dbml`：內容與教材相關實體

基本結構：

**Table（表格）**

- 代表一個實體
- 必須包含 Note 說明實體用途
- 可在 Note 中條列跨屬性不變條件

**Column（欄位）**

- 包含名稱、資料型別、約束條件
- 支援的資料型別：
  - `int`：整數
  - `long`：長整數
  - `float`：浮點數
  - `bool`：布林值
  - `string`：字串
  - `text`：長文本
  - `datetime`：日期時間
  - `timestamp`：時間戳記
  - `enum`：列舉型別（需在規格中明確定義可選值）
- 約束標記：
  - `pk`：主鍵（Primary Key）
  - `not null`：不可為空
  - `unique`：唯一值
- 每個 Column 必須有 note 說明其定義、用途及限制條件

**Relationship（關聯）**

- 使用 `ref` 語法描述實體間的關聯
- 明確標示關聯類型：一對一 (1:1)、一對多 (1:N)、多對多 (N:M)
- 跨檔案關聯：使用完整路徑引用其他 DBML 檔案中的實體
  - 範例：`ref: erm-core.Teacher.id`

**範例格式：**

```dbml
Table Classroom {
  id int [pk, not null]
  name string [not null, note: '班級名稱']
  teacher_id int [not null, note: '教師 ID']
  created_at datetime [not null, note: '建立時間']

  Note: '班級實體，代表教師建立的教學班級'
}

// 跨檔案關聯範例
ref: Classroom.teacher_id > erm-core.Teacher.id
```

## Gherkin Language 格式（功能模型）

用於描述功能規格，採用三層式結構：Feature > Rule > Example。

**檔案組織：**

- 按業務領域分類，對應 DBML 檔案結構
- 每個功能獨立一份文件
- 檔案路徑格式：`spec/features/<domain>/<feature-name>.feature`
- 檔案名稱使用英文 kebab-case（小寫字母，單字間用 `-` 分隔）

**目錄結構：**

```
spec/features/
├── core/              # 核心用戶與認證功能
├── organization/      # 機構與組織功能
├── classroom/         # 班級與課程功能
├── subscription/      # 訂閱與付費功能
└── content/           # 內容與教材功能
```

### Feature（功能）

- 定義：使用者與系統的請求交互點，必須存在明確的交互時機
- 每個 Feature 對應一個業務功能

### Rule（規則）

- 每個功能涵蓋 1..\* 條規則
- 規則描述功能執行時必須遵守的條件

### Example（例子）

- 使用 Gherkin 語法 (Given-When-Then) 描述規則的具體案例
- 若規格文本中無可用例子，在 Rule 下標記 `#TODO`，該 Rule 狀態列為 Missing
- 應涵蓋邊界條件與不同值域類別

**範例格式：**

```gherkin
# spec/features/organization/create-campus.feature
Feature: 建立分校
  機構擁有人或機構管理人可以在機構內建立分校

  Rule: 分校名稱不可為空

    Example: 成功建立分校
      Given 使用者「王老師」已登入系統
      And 使用者「王老師」在機構「快樂補習班」的角色為「機構擁有人」
      And 系統中存在機構「快樂補習班」
      When 使用者在機構「快樂補習班」建立分校，資料如下
        | name    |
        | 永和分校 |
      Then 操作成功
      And 機構「快樂補習班」中存在分校資料如下
        | name    |
        | 永和分校 |

    Example: 分校名稱為空時無法建立
      Given 使用者「王老師」已登入系統
      And 使用者「王老師」在機構「快樂補習班」的角色為「機構擁有人」
      When 使用者在機構「快樂補習班」建立分校，資料如下
        | name |
        |      |
      Then 操作失敗
```

---

# 資料模型萃取規則

## A. 識別「實體 (Entity)」

每個實體都是系統中需要持久化的資料物件。

**核心原則：**

- 優先檢查 `backend/models.py` 中是否已有相同概念的實體
- 若既有實體可滿足需求，直接使用既有實體，不要創建重複實體
- 遵循專案既有的命名規範（參考 `backend/models.py`）

**萃取規則：**

- 只萃取規格中明確提到的實體
- 實體名稱使用規格中的術語，不要自行創造
- 不要添加規格中未提及的實體

## B. 萃取實體的「屬性 (Attribute)」

**核心原則：**

- 參考 `backend/models.py` 中既有實體的屬性命名慣例
- 新實體的常見字段（id, created_at, updated_at）應遵循既有模式

**萃取規則：**

- 只萃取規格中明確提到或可直接推導的屬性
- 每個屬性必須指定資料型別（參照 DBML 格式章節定義的型別）
- 每個屬性必須有 note 說明其定義與用途
- 如果規格中有提到屬性的限制條件（如 > 0, >= 0, 必須唯一等），在 note 中明確標註
- 不要添加規格中沒有提到的「預留欄位」或「可能需要的欄位」

## C. 識別實體之間的「關係 (Relationship)」

**核心原則：**

- 參考 `backend/models.py` 中既有實體之間的關聯模式
- 注意跨檔案關聯需使用完整路徑（如：`erm-core.Teacher.id`）

**萃取規則：**

- 只標註規格中明確提到的關聯關係
- 使用 DBML 的 ref 語法描述關聯
- 明確標示關聯類型（一對一、一對多、多對多）

## D. 記錄實體的整體說明

- 在 Table 的 Note 中簡述此實體的用途
- 如果實體之間有關聯，在 Note 中註明（如：Teacher 1:N Classroom）

---

# 功能模型萃取規則

## A. 萃取「功能 (Feature)」

每個功能都是使用者與系統的請求交互點，若沒有明確交互時機則不被視為功能。

- 好比說，教師可以建立班級、指派作業、批改作業，這三者都各為一道獨立的功能
- 只萃取規格中明確提到的功能，不要推測「可能需要的功能」
- 功能命名應清晰且反映使用者意圖

## B. 萃取功能的「規則 (Rule)」

針對每個功能，從原始規格文本中萃取其「規則 (Rule)」。規則為此功能在實際執行時系統必須遵守的條件。

### 規則分類

- **前置條件 (Pre-condition)**：功能執行前需做的驗證，若沒通過驗證則不履行功能
- **後置條件 (Post-condition)**：若通過前置條件，則系統必須保證達成的條件，好比系統狀態的更新

### 規則萃取原則

- 每個前置條件 or 後置條件都必須為一條獨立的 Rule
- **Rule 必須原子化**，分割到不可分割為止，每一個 Rule 只驗證一件事
- 每個功能至少萃取出一條規則
- 只萃取規格中明確提到的規則，不要添加「合理的驗證」或「應該要有的檢查」
- 規則描述必須可驗證，避免使用模糊的形容詞

## C. 萃取規則的「例子 (Example)」

針對每個規則，從原始規格文本中尋找是否有「例子 (Example)」能說明此規則。

- 使用 **Gherkin 語法 (Given-When-Then)** 描述此 Example
- 如果無法從文本中找到任何例子，則不要強硬給予任何例子，在 Rule 下標記 **#TODO** 即可
- 不要編造例子或假設測試情境
- Example 應涵蓋邊界條件與不同值域類別（若規格中有提供）
- 每個 Example 至少都有 "When step"，When 與該 Feature 的系統交互相關，好比如果該 Feature 為「登入」，則 When 必定是與此功能的交互時機，也就是「登入」。
- 每一個 step 必須容易被翻譯成測試的程式碼），不可以放入過度描述性質而非資料性質的字串。（好比在 then 中撰寫：`then 執行的順序應該如下：`，順序難以藉由測試自動化驗證。）
- Feature File 中的句型盡可能一致，避免句型不同而造成後續測試程式實作上亂章無序或「句型不同、語義卻相同，使得 StepDef 需重複實作」的困擾。
- `Then` 的語句中只能描述系統的實際狀態資料，不能撰寫描述性的語句。好比：
  - 錯誤示範：
    ```
      Then 學生成功完成朗讀作業
      And 朗讀發音非常標準
    ```
  - 正確示範：
    ```
    Then 學生朗讀作業狀態如下
      | status    | pronunciation_score |
      | COMPLETED | 92.5               |
    ```
- 如果在此場景下，此操作系統不允許、且需表達錯誤，則一律使用底下格式撰寫 Then：`Then 操作失敗`
- `Then` 必須用「資料」來描述業務功能的驗收，請勿用描述「應該」，而是描述「值必須為多少」。好比：
  - 錯誤示範：`Then 應成功提交 5 個朗讀項目`
  - 正確示範：
    ```
    Then 學生作業「基礎問候語練習」的已提交項目數為 5
    And 學生作業「基礎問候語練習」的總項目數為 5
    ```

---

# 輸出格式規範

## DBML 格式要求

將資料模型依業務領域分別輸出到對應的 DBML 檔案：

- `spec/erm-core.dbml`：核心用戶與認證相關實體
- `spec/erm-organization.dbml`：機構與組織相關實體
- `spec/erm-classroom.dbml`：班級與課程相關實體
- `spec/erm-subscription.dbml`：訂閱與付費相關實體
- `spec/erm-content.dbml`：內容與教材相關實體

**格式要求：**

- 檔案必須嚴格遵照 DBML 語法格式
- 每個 **Table** 代表一個實體
- 每個 **Column** 必須包含：
  - 名稱
  - 資料型別 (int, long, float, bool, string)
  - **note** 說明（定義、用途、限制條件）
- 每個 **Table** 必須有 **Note** 說明其用途
- 在 Table Note 中可額外條列跨屬性不變條件
- 使用 **ref** 描述實體之間的關聯關係

## Gherkin Language 格式要求

將每個 Feature 以及其涵蓋的 Rules/Examples，以 Gherkin Language 依序輸出到 `spec/features/<domain>/` 中。

**檔案組織：**

- 按業務領域分類到對應子目錄（core, organization, classroom, subscription, content）
- 每個功能獨立一份文件
- 檔案名稱使用英文 kebab-case：`<feature-name>.feature`
  - 範例：`create-organization.feature`, `manage-classroom.feature`

**格式要求：**

- 檔案必須嚴格遵照 Gherkin Language 的格式
- 階層結構：Feature > Rule > Example
- 使用英文版本的 Given/When/Then keyword
- 每個 step statement 主要以中文描述
- 如果有 DataTable，欄位名稱以英文描述
- 缺少 Example 的 Rule 必須標記 `#TODO`
