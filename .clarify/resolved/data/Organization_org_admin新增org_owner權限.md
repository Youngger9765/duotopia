# 釐清問題

org_admin（機構管理人）是否可以新增 org_owner（機構負責人）？

# 定位

Feature: 管理機構成員 - Rule 3
權限邊界定義

# 多選題

| 選項 | 描述                           |
| ---- | ------------------------------ |
| A    | 可以新增                        |
| B    | 不可以新增（僅能新增 org_admin） |

# 影響範圍

- 新增成員 API 的權限檢查邏輯
- Casbin 權限策略細化
- 前端成員管理 UI（角色選擇下拉選單）
- 機構所有權控制安全性

# 優先級

Medium

---

# 解決記錄

- **回答**：B - 不可以新增（僅能新增 org_admin）
- **更新的規格檔**：spec/features/organization/管理機構成員.feature
- **變更內容**：修改 Rule 3 標題，新增 Example 「機構管理人不能新增 org_owner」，明確 org_admin 僅能新增 org_admin
