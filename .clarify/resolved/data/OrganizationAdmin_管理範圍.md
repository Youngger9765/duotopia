# 釐清問題

機構管理人的管理範圍為整個機構或特定分校？

# 定位

ERM：teacher_organizations 實體的設計，org_admin 角色是否需要額外的 scope 欄位。

# 多選題

| 選項 | 描述                                                       |
| ---- | ---------------------------------------------------------- |
| A    | 整個機構（與 org_owner 管理範圍相同）                      |
| B    | 特定分校（需在 teacher_organizations 增加 school_id 欄位） |
| C    | 可彈性指派（既可管理整個機構也可限定特定分校）             |

# 影響範圍

- teacher_organizations 實體的結構設計
- org_admin 權限驗證時的範圍檢查
- 分校管理功能的權限邏輯
- 機構與分校的權限層級設計
- Casbin 權限策略的資源範圍定義

# 優先級

High

---

# 解決記錄

- **回答**：A - 整個機構（與 org_owner 管理範圍相同）

- **說明**：
  - 現有實作中，`teacher_organizations` 表**沒有** `school_id` 欄位
  - org_admin 和 org_owner 都是透過 `teacher_organizations` 表與機構關聯
  - 兩者的管理範圍相同，差異僅在於權限內容（訂閱方案）
  - 若未來需要「特定分校管理人」，使用 `teacher_schools` 表中的 `school_admin` 角色

- **資料結構確認**：
  - `teacher_organizations`: teacher_id + organization_id + role (org_owner/org_admin)
  - `teacher_schools`: teacher_id + school_id + role (school_admin/school_director/teacher)
  - 機構級角色（org_owner/org_admin）管理整個機構
  - 分校級角色（school_admin 等）管理特定分校

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：確認機構管理人的管理範圍為整個機構
- **實作參考**：
  - backend/models/organization.py#L125 - TeacherOrganization 表結構（無 school_id）
