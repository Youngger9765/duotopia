# 釐清問題

訂閱中的 available_teacher_licenses 是否自動計算？還是需要手動更新？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `subscriptions` - 欄位 `available_teacher_licenses`

# 多選題

| 選項  | 描述                                           |
| ----- | ---------------------------------------------- |
| A     | 自動計算（虛擬欄位）：available = total - used |
| B     | 每次 used 變動時自動更新（觸發器或應用層）     |
| C     | 需要手動呼叫計算函數更新                       |
| D     | 獨立設定，不自動計算                           |
| Short | 提供其他簡短答案（<=5 字）                     |

# 影響範圍

- 影響 `subscriptions` 表的欄位設計（實體欄位 vs 虛擬欄位）
- 影響資料一致性維護策略
- 影響訂閱查詢效能

# 優先級

Medium

理由：

- DBML 定義中有 `available_teacher_licenses` 欄位
- Note 說明「可用 = 總數 - 已使用」
- 但未明確定義計算時機
- 需確認是資料庫層級、應用層級、還是查詢時計算
