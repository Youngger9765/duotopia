# 釐清問題

Subscription 剩餘點數如何自動計算？是否有公式或特殊規則？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `subscriptions` - 欄位 `initial_points`、`points_transactions`

# 白話翻譯

- 問題：訂閱剩餘點數（可用點數）如何計算？
- 例子：合約初始點數 1000，已消耗 200，剩餘點數應為多少？

# 術語一致性

- "剩餘點數"：指 initial_points - Σ(points_transactions.used_points)
- "消耗"：指已使用的點數

# 決策

- 剩餘點數 = initial_points - Σ(points_transactions.used_points)
- 不允許負值
- 若有特殊合約條款，需人工調整

# 影響

- 系統需自動計算剩餘點數
- 需在 subscriptions 記錄剩餘點數
- 相關 API/邏輯需補充測試

# 狀態

已釐清，2026-01-11 決策歸檔
