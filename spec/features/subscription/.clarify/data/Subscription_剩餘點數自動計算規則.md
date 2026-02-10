# 釐清問題

訂閱中的 remaining_points 是否自動計算？還是需要手動更新？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `subscriptions` - 欄位 `remaining_points`

# 多選題

| 選項  | 描述                                                |
| ----- | --------------------------------------------------- |
| A     | 自動計算（虛擬欄位）：remaining = total - used      |
| B     | 每次 used 或 total 變動時自動更新（觸發器或應用層） |
| C     | 每次點數交易時同步更新                              |
| D     | 需要手動呼叫計算函數更新                            |
| Short | 提供其他簡短答案（<=5 字）                          |

# 影響範圍

- 影響 `subscriptions` 表的欄位設計
- 影響點數交易處理邏輯
- 影響資料一致性維護策略
- 與 `points_transactions` 表的同步機制

# 優先級

High

理由：

- 點數餘額是訂閱系統的核心資料
- DBML 定義「剩餘 = 總數 - 已使用」
- Feature「點數加購」依賴正確的剩餘點數
- 需確認與 `points_transactions.balance_after` 的一致性維護機制
