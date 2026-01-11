# 釐清問題

Subscription 授權數如何自動計算？是否有公式或特殊規則？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `subscriptions` - 欄位 `purchased_teachers`, `bonus_teachers`

# 白話翻譯

- 問題：訂閱授權教師數（可用名額）如何計算？
- 例子：合約購買 10 名教師，贈送 2 名，授權數應為多少？

# 術語一致性

- "授權數"：指 purchased_teachers + bonus_teachers
- "名額"：指可分配教師數

# 決策

- 授權數 = purchased_teachers + bonus_teachers
- 不允許負值
- 贈送名額由業務人員人工填入

# 影響

- 系統需自動計算授權數
- 需在 subscriptions 記錄授權數
- 相關 API/邏輯需補充測試

# 狀態

已釐清，2026-01-11 決策歸檔
