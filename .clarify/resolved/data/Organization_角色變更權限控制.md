# 釐清問題

哪些角色可以變更機構成員的角色？

# 定位

Feature: 管理機構成員 - Rule 7: 編輯成員角色
API: PUT /api/organizations/{org_id}/teachers/{teacher_id}/permissions

# 多選題

| 選項 | 描述                               |
| ---- | ---------------------------------- |
| A    | 僅 org_owner                        |
| B    | org_owner 和 org_admin              |
| C    | 僅 Platform Owner                   |
| D    | org_owner 可變更所有，org_admin 可變更下級 |

# 影響範圍

- 更新成員權限 API 的權限驗證邏輯
- 前端成員管理 UI（編輯按鈕顯示/隱藏）
- Casbin 權限策略定義
- 機構管理安全性控制

# 優先級

Medium

---

# 解決記錄

- **回答**：B - org_owner 和 org_admin
- **更新的規格檔**：spec/features/organization/管理機構成員.feature
- **變更內容**：修改 Rule 7 Example 2，允許 org_admin 變更角色（但不能提升為 org_owner），新增 Example 展示 org_admin 可以降級成員角色
