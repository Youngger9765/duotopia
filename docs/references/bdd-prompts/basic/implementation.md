# BDD 規格實作指南

## 文件目的

本文件說明如何將 `formulation-rules.md` 中產出的規格（DBML 和 Gherkin）轉換為可執行的程式碼和測試。

**與 formulation-rules.md 的關係：**

- **formulation-rules.md**：定義如何「撰寫規格」（從需求文本 → DBML/Gherkin）
- **implementation.md**（本文件）：定義如何「實作規格」（從 DBML/Gherkin → 程式碼/測試）

---

## 實作流程概述

### 階段 1：資料模型實作

從 `spec/erm-*.dbml` 檔案轉換為實際資料庫結構：

1. **建立 SQLAlchemy 模型**（`backend/models.py`）
2. **產生 Alembic 遷移檔案**
3. **執行遷移更新資料庫**

**詳細步驟：** ⚠️ 待完善

---

### 階段 2：功能測試實作

從 `spec/features/**/*.feature` 檔案轉換為可執行測試：

1. **撰寫 Step Definitions**（將 Given/When/Then 轉換為 Python 函數）
2. **建立測試資料準備機制**
3. **執行 BDD 測試**

**詳細步驟：** ⚠️ 待完善

---

### 階段 3：API 實作

根據功能規格實作對應的 API endpoints：

1. **建立 Router**（`backend/routers/*.py`）
2. **實作業務邏輯**（`backend/services/*.py`）
3. **整合測試驗證**

**詳細步驟：** ⚠️ 待完善

---

## 驗證檢查清單

### 資料模型驗證

- [ ] 所有 DBML 實體都已轉換為 SQLAlchemy 模型
- [ ] 所有欄位屬性和約束都已正確對應
- [ ] 所有關聯關係都已建立
- [ ] Alembic 遷移已執行成功

### 功能測試驗證

- [ ] 所有 Feature 都有對應的測試檔案
- [ ] 所有 Example 都能成功執行
- [ ] 測試覆蓋率符合專案標準

### API 驗證

- [ ] 所有功能都有對應的 API endpoint
- [ ] API 行為符合 Gherkin 規格描述
- [ ] 錯誤處理符合規格定義

---

## 工具與框架

**DUOTOPIA 專案使用：**

- **資料庫**：PostgreSQL + SQLAlchemy ORM + Alembic
- **BDD 測試**：⚠️ 待確認（Behave? pytest-bdd?）
- **API 框架**：FastAPI
- **測試框架**：pytest

**工具設定與使用：** ⚠️ 待完善

---

## 注意事項

1. **新功能開發流程**：

   - 先撰寫規格（DBML + Gherkin）
   - 再實作程式碼
   - 最後驗證測試通過

2. **既有功能修改**：

   - 先更新規格
   - 確認測試失敗（red）
   - 修改程式碼
   - 驗證測試通過（green）

3. **規格與實作同步**：
   - 規格是單一真實來源（Single Source of Truth）
   - 程式碼必須符合規格
   - 不符合時優先修正程式碼，除非規格有誤

---

**本文件狀態：** 🚧 初稿，待後續討論細部內容
