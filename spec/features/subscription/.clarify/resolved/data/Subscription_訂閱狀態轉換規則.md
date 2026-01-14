# 釐清問題

訂閱狀態之間的轉換規則是什麼？哪些轉換是允許的？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `subscriptions` - 欄位 `status`

# 多選題

| 選項  | 描述                                                         |
| ----- | ------------------------------------------------------------ |
| A     | active → expired（單向，自動根據日期）                       |
| B     | active → expired/suspended/cancelled（可手動暫停或取消）     |
| C     | active ⇄ suspended，active → expired/cancelled（暫停可恢復） |
| D     | 所有狀態可互相轉換                                           |
| Short | 提供其他簡短答案（<=5 字）                                   |

# 影響範圍

- 影響訂閱狀態欄位的驗證邏輯
- 影響訂閱管理功能的操作選項
- 影響系統自動更新訂閱狀態的邏輯
- 需要新增訂閱狀態轉換的 Feature Rules

# 優先級

High

理由：

- DBML Note 提到「訂閱狀態會自動根據期間更新」
- 但未明確定義：
  - 是否支援手動暫停 (suspended)
  - 是否支援提前取消 (cancelled)
  - suspended 是否可以恢復為 active
- 影響訂閱管理功能的設計

---

# 解決方案（決策 #11）

**決策日期**: 2026-01-09

**答案**: 僅支援自動到期，不支援暫停與提前取消

**說明**:

- 訂閱狀態僅允許：
  - active → expired（自動根據合約/訂閱結束日期）
- 不支援手動暫停（suspended）
- 不支援提前取消（cancelled）
- 不允許任何狀態恢復為 active
- 訂閱狀態完全由系統自動管理，無人工干預

**影響**:

- 訂閱管理介面不提供暫停/取消/恢復操作
- 僅根據日期自動切換狀態
- 使用者體驗單純明確

**信心評分**: High
