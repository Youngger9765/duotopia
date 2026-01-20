# 釐清問題

機構負責人的具體權限為何？

# 定位

角色定義：機構負責人（org_owner）的權限欄位。
參考：spec/erm-organization.dbml 中 teacher_organizations.role 欄位的 org_owner 值。

# 多選題

| 選項  | 描述                                                        |
| ----- | ----------------------------------------------------------- |
| Short | 新增/刪除分校、指派機構管理人、管理所有教師與學生等具體權限 |

Format: Short answer (comma-separated permission list)

# 影響範圍

- Organization 相關的權限矩陣
- spec/features/organization/ 中的功能規格
- 機構管理 API 的權限驗證
- 與 org_admin 的權限對照表
- Casbin 權限策略的定義

# 優先級

High

---

# 解決記錄

- **回答**：根據現有專案實作，機構負責人（org_owner）具有以下權限：

**機構層級管理**：
- `manage_schools`（創建/編輯/刪除分校）
- `manage_teachers`（邀請/編輯/移除機構內教師）
- `manage_students`（查看/管理機構內所有學生）
- `manage_classrooms`（管理機構內所有班級）
- `manage_subscription`（管理機構訂閱方案）
- `view_analytics`（查看機構級數據分析）

**教師權限管理**：
- `add_teacher_to_organization`（邀請教師加入機構）
- `update_teacher_permissions`（修改教師權限）
- `remove_teacher_from_organization`（移除教師）
- `assign_teacher_to_school`（指派教師到分校）

**分校管理**：
- `create_school`（創建分校）
- `update_school`（編輯分校資訊）
- `delete_school`（刪除分校）
- `view_school_list`（查看所有分校）

**機構資訊管理**：
- `update_organization`（編輯機構基本資訊）
- `delete_organization`（刪除機構 - soft delete）
- `view_organization_teachers`（查看機構內所有教師）

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「機構類 > 機構負責人」章節補充具體權限列表
- **實作參考**：
  - backend/config/casbin_policy.csv（Casbin RBAC 權限定義）
  - backend/routers/organizations.py（機構 CRUD、教師管理）
  - backend/routers/schools.py（分校管理）
  - backend/services/casbin_service.py（權限檢查服務）
