# 釐清問題

點數交易記錄的交易類型 (transaction_type) 完整枚舉值有哪些？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `points_transactions` - 欄位 `transaction_type`

# 多選題

| 選項  | 描述                                                                                         |
| ----- | -------------------------------------------------------------------------------------------- |
| A     | 'grant'（發放）、'purchase'（加購）、'usage'（使用）、'refund'（退款）、'adjustment'（調整） |
| B     | 僅 'grant'、'purchase'、'usage'（不支援退款與調整）                                          |
| C     | A 的五種 + 'expire'（點數過期）、'transfer'（轉移）                                          |
| D     | 開放字串，不限定枚舉值                                                                       |
| Short | 提供其他簡短答案（<=5 字）                                                                   |

# 影響範圍

- 影響 `points_transactions.transaction_type` 欄位的約束條件
- 影響點數交易處理邏輯的分支
- 影響點數餘額計算規則

# 優先級

Medium

理由：

- DBML Note 列出五種類型
- Feature 文件只涵蓋 'grant' 和 'purchase'
- 未定義 'usage'、'refund'、'adjustment' 的觸發時機
- 需確認是否需要更多類型（如：過期、轉移）

---

# 決策紀錄（2026-01-10）

## 決策

- grant（發放）
- purchase（加購）
- usage（使用）
- refund（退款）
- adjustment（手動調整）

**這些類型已足夠，無需新增。**

## 討論重點

- 已涵蓋所有業務情境
- 未來如有新需求可再擴充

## 信心評分

High
