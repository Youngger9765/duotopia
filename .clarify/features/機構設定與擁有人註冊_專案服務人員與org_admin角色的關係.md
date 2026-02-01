# 釐清問題

機構設定與擁有人註冊.feature 說明「專案服務人員應獲得 org_admin 角色」，但沒有說明：
- 專案服務人員是否為 Duotopia 內部員工？
- 是否可同時為多個機構的服務人員？
- 與一般 org_admin 的權限差異？
- 如何在資料模型中區分？

# 定位

Feature: 機構設定與擁有人註冊.feature
規則: 設定專案服務人員
場景: 指派專案服務人員為機構管理人
Then: "'林服務' 應獲得 'org_admin' 角色"

ERM: teacher_organizations 表（role: org_admin）

# 多選題

| 選項 | 描述 |
|------|------|
| A | 專案服務人員就是 org_admin，無差異 |
| B | 專案服務人員有額外標記（如 is_staff 欄位） |
| C | 專案服務人員使用不同的角色（project_manager） |
| D | 使用 teacher.is_admin 或其他欄位標記 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響角色設計與權限管理
- 影響 teacher_organizations 表結構
- 影響權限檢查邏輯
- 若有差異，需在 DBML 中補充

# 優先級

Medium

- 影響角色體系設計
- 影響權限管理邏輯
- 需明確定義專案服務人員的身份
