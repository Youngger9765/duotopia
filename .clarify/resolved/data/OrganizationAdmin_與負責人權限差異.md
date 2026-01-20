# 釐清問題

機構管理人與機構負責人的權限差異為何？

# 定位

角色定義：機構管理人（org_admin）的權限欄位，以及與機構負責人的區別。
參考：spec/erm-organization.dbml 中 teacher_organizations.role 欄位的 org_admin 值。

# 多選題

| 選項  | 描述                                                 |
| ----- | ---------------------------------------------------- |
| A     | 無法刪除機構、無法變更付費設定，其他功能與負責人相同 |
| B     | 僅能查看資料，無修改權限                             |
| C     | 可管理日常營運但無機構級重大決策權限                 |
| Short | 列舉管理人「不能做」的具體項目                       |

# 影響範圍

- Organization 相關的權限矩陣
- spec/features/organization/管理機構成員.feature 的規則定義
- 機構管理 API 的權限驗證邏輯
- 與 org_owner 的權限對照表
- Casbin 權限策略的細化

# 優先級

High

---

# 解決記錄

- **回答**：A - 無法查看訂閱方案，其他功能與負責人相同

- **具體差異**：

**org_admin 不能做的（僅 org_owner 可以）**：
- ✖️ `view_subscription` / `manage_subscription` - 查看/管理機構訂閱方案

**兩者都不能做的**：
- ✖️ `delete_organization` - 刪除機構（不開放此功能）

**兩者共有的權限**：
- ✅ `manage_schools` - 刪除/編輯/新增/管理學校（分校）
- ✅ `manage_teachers` - 管理教師
- ✅ `manage_students` - 管理學生
- ✅ `manage_classrooms` - 管理班級
- ✅ `view_analytics` - 查看分析數據
- ✅ `update_organization` - 編輯機構資訊
- ✅ 邀請/添加/移除教師
- ✅ 修改教師權限
- ✅ 指派教師到分校

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「機構類 > 機構管理人」章節補充與負責人的差異
- **實作參考**：
  - backend/config/casbin_policy.csv（org_admin 無 manage_subscription 權限）
  - backend/routers/organizations.py（機構管理 API）
