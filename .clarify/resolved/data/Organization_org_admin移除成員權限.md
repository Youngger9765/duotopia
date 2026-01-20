# 釐清問題

org_admin（機構管理人）是否可以移除同級的 org_admin？

# 定位

Feature: 管理機構成員
目前規格明確：org_admin 不能移除 org_owner
但未說明：org_admin 能否移除 org_admin

# 多選題

| 選項 | 描述                           |
| ---- | ------------------------------ |
| A    | 可以移除同級 org_admin          |
| B    | 不可以移除任何成員               |
| C    | 僅能移除自己新增的 org_admin     |

# 影響範圍

- 移除成員 API 的權限檢查邏輯
- Casbin 權限策略定義
- 前端成員列表 UI（刪除按鈕顯示/隱藏）
- 機構成員管理靈活性

# 優先級

Medium

---

# 解決記錄

- **回答**：A - 可以移除同級 org_admin
- **更新的規格檔**：spec/features/organization/管理機構成員.feature
- **變更內容**：在 Rule 4 新增 Example 「機構管理人可以移除同級的機構管理人」，明確 org_admin 可以移除 org_admin
