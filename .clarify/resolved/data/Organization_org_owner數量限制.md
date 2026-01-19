# 釐清問題

一個機構最多可以有幾個 org_owner（機構負責人）？

# 定位

Feature: 管理機構成員
參考：backend/routers/organizations.py 實作中限制為 1 個

# 多選題

| 選項 | 描述                           |
| ---- | ------------------------------ |
| A    | 僅 1 個（目前實作）            |
| B    | 無限制                          |
| C    | 可設定上限（如 3 個）           |

# 影響範圍

- 新增機構成員時的驗證邏輯
- 角色變更 API 的檢查規則
- 機構所有權轉移流程設計
- 前端成員管理 UI 設計

# 優先級

Medium

---

# 解決記錄

- **回答**：A - 僅 1 個（目前實作）
- **更新的規格檔**：spec/features/organization/管理機構成員.feature, spec/erm-organization.dbml
- **變更內容**：新增 Rule「一個機構僅能有一個機構負責人」，並在 TeacherOrganization 資料模型的 Note 中記錄此限制
