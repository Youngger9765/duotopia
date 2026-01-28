# 釐清問題

訂閱開通時，點數交易記錄中的 balance_before 應該是多少？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `points_transactions` - 欄位 `balance_before` 和 `balance_after`

# 多選題

| 選項  | 描述                                                    |
| ----- | ------------------------------------------------------- |
| A     | balance_before = 0（首次開通前餘額為 0）                |
| B     | balance_before = 上一筆交易的 balance_after（延續性）   |
| C     | balance_before = subscriptions.remaining_points（同步） |
| D     | 依交易類型不同而異                                      |
| Short | 提供其他簡短答案（<=5 字）                              |

# 影響範圍

- 影響點數交易記錄的建立邏輯
- 影響 `points_transactions` 與 `subscriptions` 的資料一致性
- 影響點數餘額的驗證規則

# 優先級

High

理由：

- Feature「點數加購」範例：加購前餘額 5000，加購後 15000
- 但未定義首次發放時的 balance_before
- DBML Note 定義「balance_after = balance_before + points_change」
- 需確保一致性維護機制
