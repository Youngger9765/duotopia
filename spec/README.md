# DUOTOPIA 規格文件結構

此目錄包含 DUOTOPIA 專案的完整規格文件，採用行為驅動開發（BDD）方法組織。

## 目錄結構

```
spec/
├── README.md                          # 本檔案
├── business-specs/                    # 業務規格（高層級）
│   ├── user-roles-and-permissions.md  # 用戶角色與權限體系
│   └── student-abilities-assessment.md # 學生能力評估體系
├── erm-*.dbml                         # 資料模型規格（DBML 格式）
│   ├── erm-organization.dbml          # 機構層級管理
│   ├── erm-core.dbml                  # 核心實體
│   ├── erm-classroom.dbml             # 班級與學習
│   ├── erm-subscription.dbml          # 訂閱與付費
│   └── erm-content.dbml               # 教材與內容
└── features/                          # 功能行為規格（Gherkin 格式）
    └── organization/                  # 機構管理功能
        ├── 建立機構.feature
        └── 管理機構成員.feature
```

## 規格層級說明

### 1. 業務規格（Business Specs）

**位置**：`business-specs/`  
**格式**：Markdown  
**目的**：定義跨領域的業務規則與概念  
**讀者**：所有團隊成員、產品經理、業務專家

**特點**：
- 使用自然語言描述
- 不涉及具體實作細節
- 作為資料模型和功能規格的參考依據
- 回答「是什麼」和「為什麼」

**範例文件**：
- `user-roles-and-permissions.md` - 定義所有角色的職責、權限、管理範圍
- `student-abilities-assessment.md` - 定義學生能力評估的五大象限

### 2. 資料模型規格（ERM - DBML）

**位置**：根目錄 `erm-*.dbml`  
**格式**：[DBML (Database Markup Language)](https://dbml.dbdiagram.io/)  
**目的**：定義資料結構、實體關係、約束條件  
**讀者**：後端工程師、資料庫設計師

**特點**：
- 可視覺化為 ER Diagram
- 定義 Table、欄位型別、關係、索引
- 使用中文 note 說明業務意義
- 回答「資料如何組織」

**命名規則**：`erm-<領域>.dbml`

### 3. 功能行為規格（Features - Gherkin）

**位置**：`features/<領域>/`  
**格式**：[Gherkin Language](https://cucumber.io/docs/gherkin/)  
**目的**：定義使用者與系統的互動行為  
**讀者**：所有團隊成員、QA 測試人員

**特點**：
- 使用 Given-When-Then 語法
- 每個 Feature 包含多個 Rule 和 Example
- 可作為自動化測試的基礎
- 回答「系統如何行為」

**範例**：
```gherkin
Feature: 建立機構
  Rule: 僅系統管理員可以建立機構
    Example: Platform Owner 成功建立機構
      Given 使用者「管理員」的 is_admin 為 true
      When 使用者「管理員」建立機構...
      Then 系統成功建立機構
```

## BDD 工作流程

1. **Discovery** - 掃描規格，識別歧義與遺漏（參考 `docs/references/bdd-prompts/basic/discovery.md`）
2. **Clarification** - 互動式釐清問題（參考 `docs/references/bdd-prompts/basic/clarify-and-translation.md`）
3. **Formulation** - 將釐清結果更新回規格檔案
4. **Implementation** - 根據規格進行開發
5. **Verification** - 使用 Feature 檔案進行測試驗證

## 規格引用規則

- **DBML 檔案**引用業務規格：`// 參照: spec/business-specs/user-roles-and-permissions.md`
- **Feature 檔案**引用業務規格與資料模型：
  ```gherkin
  背景資訊:
  - 參照資料模型: spec/erm-organization.dbml
  - 參照角色定義: spec/business-specs/user-roles-and-permissions.md
  ```

## 維護指南

### 新增規格檔案時
1. 業務概念變更 → 更新 `business-specs/*.md`
2. 資料結構變更 → 更新/新增 `erm-*.dbml`
3. 功能行為變更 → 更新/新增 `features/<領域>/*.feature`

### 確保一致性
- 所有技術規格必須參照對應的業務規格
- 資料模型與功能規格的術語必須一致
- 使用 `.clarify/` 流程來系統性釐清歧義

## 相關工具

- **DBML Editor**：https://dbdiagram.io/
- **Gherkin Formatter**：VS Code 插件 "Cucumber (Gherkin) Full Support"
- **BDD Prompts**：`docs/references/bdd-prompts/basic/`

## 版本歷史

- 2026-01-07：整合 `docs/specs/` 到 `spec/business-specs/`，統一規格管理
