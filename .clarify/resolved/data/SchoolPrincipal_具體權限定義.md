# 釐清問題

分校校長的具體權限為何？

# 定位

角色定義：分校校長（school_principal）的權限欄位。
參考：spec/erm-organization.dbml 中 teacher_schools.roles 欄位的 school_principal 值。

# 多選題

| 選項  | 描述                                           |
| ----- | ---------------------------------------------- |
| Short | 管理分校教師、查看分校所有班級與學生等具體權限 |

Format: Short answer (comma-separated permission list)

# 影響範圍

- School 相關的權限矩陣
- spec/features/organization/ 中分校管理功能的規格
- 分校管理 API 的權限驗證
- 與 school_admin 的權限對照表
- Casbin 權限策略的定義

# 優先級

High

---

# 解決記錄

- **回答**：根據現有專案實作，分校校長對應實作的 `school_admin` 角色，具有以下權限：

**分校層級管理**：
- `manage_teachers` - 管理分校內的教師
- `manage_students` - 管理分校內的學生
- `manage_classrooms` - 管理分校內的班級
- `view_school_analytics` - 查看分校數據分析

**管理範圍**：
- 僅限單一分校（透過 teacher_schools 表關聯）
- 無法管理學校（分校）本身的創建/刪除（僅 org_owner/org_admin 可以）
- 無法查看機構訂閱方案

**實作方式**：
- teacher_schools.roles 包含 'school_admin'
- 基於 Casbin RBAC 模型，domain 為 'school-{uuid}'

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「機構類 > 分校校長」章節補充具體權限列表，對應實作的 school_admin
- **實作參考**：
  - backend/config/casbin_policy.csv（school_admin 權限定義）
  - backend/models/organization.py#L186（TeacherSchool 表結構）
  - backend/routers/schools.py（分校管理 API）
