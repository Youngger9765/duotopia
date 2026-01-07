# 釐清問題

Note 說明「一個機構僅能有一個 org_owner」，但 DBML 沒有定義此約束（如 unique index on (organization_id, role) where role='org_owner'），如何強制執行？

# 定位

ERM：teacher_organizations 表
Note: "一個機構僅能有一個 org_owner"
Feature: 管理機構成員.feature, Rule: 一個機構僅能有一個機構負責人

# 多選題

| 選項 | 描述 |
|------|------|
| A | 僅在應用層檢查（API 邏輯） |
| B | 資料庫部分唯一索引（organization_id, is_active) where role='org_owner' |
| C | 使用資料庫觸發器強制執行 |
| D | 允許多個但只有一個 is_active=true |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響資料庫索引設計
- 影響 API 驗證邏輯
- 影響機構擁有人轉移流程（管理機構成員.feature Example）
- 影響資料完整性保護

# 優先級

High

- 核心業務規則
- 影響資料完整性
- 需在資料庫或應用層明確實作
