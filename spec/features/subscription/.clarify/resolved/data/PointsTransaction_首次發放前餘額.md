# 釐清問題

首次發放點數前，PointsTransaction 餘額如何計算？是否有特殊規則？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `points_transactions` - 欄位 `balance`

# 白話翻譯

- 問題：第一次發放點數時，系統如何決定帳戶的初始餘額？
- 例子：機構訂閱開通，尚未有任何點數交易紀錄，首次發放時餘額應為多少？

# 術語一致性

- "首次發放"：指第一次有點數進帳的交易
- "餘額"：指 points_transactions.balance 欄位

# 決策

- 初始餘額 = 0，首次發放後餘額 = initial_points
- 不允許負餘額
- 若有特殊合約條款，需人工調整

# 影響

- 系統需自動判斷首次發放，正確計算餘額
- 需在 points_transactions 記錄初始餘額
- 相關 API/邏輯需補充測試

# 狀態

已釐清，2026-01-11 決策歸檔
