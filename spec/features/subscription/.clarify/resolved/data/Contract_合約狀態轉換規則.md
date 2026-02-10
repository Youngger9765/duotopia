# 釐清問題

合約狀態之間的轉換規則是什麼？哪些轉換是允許的？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `contracts` - 欄位 `status`

# 多選題

| 選項  | 描述                                                           |
| ----- | -------------------------------------------------------------- |
| A     | pending_payment → active → expired（線性轉換，不可逆）         |
| B     | pending_payment → active → expired/cancelled（可取消，不可逆） |
| C     | pending_payment ⇄ active ⇄ expired ⇄ cancelled（部分可逆）     |
| D     | 所有狀態都可互相轉換（完全靈活）                               |
| Short | 提供其他簡短答案（<=5 字）                                     |

# 影響範圍

- 影響合約狀態欄位的驗證邏輯
- 影響簽約與付款功能的狀態管理
- 影響訂閱開通邏輯
- 需要新增狀態轉換的 Feature Rules

# 優先級

High

理由：

- DBML Note 提到「pending_payment → active → expired/cancelled」
- 但未明確定義：
  - active 是否可以回到 pending_payment（如：付款失敗）
  - active 是否可以變成 cancelled（如：合約提前終止）
  - expired 是否可以變成 active（如：續約）
- 狀態轉換規則影響業務流程設計

---

# 解決方案（決策 #5）

**決策日期**: 2026-01-09

**答案**: 架構調整 - 移除合約狀態管理

**說明**:

- 合約改為檔案管理 (contract_files 表)，不需要狀態欄位
- 線下簽約流程無需系統追蹤狀態
- 訂閱狀態由 subscriptions.status 管理

**相關更新**:

- ✅ erm-subscription.dbml: 移除 contracts 表，新增 contract_files 表
- ✅ 新建「專案人員開立機構訂閱.feature」

**參考**: 架構重大調整決策.md
