# 釐清問題

付款記錄中「付款方式」的完整枚舉值有哪些？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `payments` - 欄位 `payment_method`

# 多選題

| 選項  | 描述                                                                                  |
| ----- | ------------------------------------------------------------------------------------- |
| A     | 'aftee_installment'、'bank_transfer'、'credit_card'（三種固定方式）                   |
| B     | 'aftee_installment'、'bank_transfer'、'credit_card'、'bank_installment'（含銀行分期） |
| C     | 'aftee_installment'、'bank_transfer'、'credit_card'、'bank_installment'、'other'      |
| D     | 開放字串，不限定枚舉值                                                                |
| Short | 提供其他簡短答案（<=5 字）                                                            |

# 影響範圍

- 影響 `payments.payment_method` 欄位的約束條件
- 影響付款方式選擇功能的 UI 與邏輯
- 影響付款處理流程的分支邏輯

# 優先級

Medium

理由：

- DBML Note 列出了四種方式，但未定義為 enum
- Feature 文件只涵蓋三種（AFTEE、轉帳、刷卡）
- 「信用卡分期」(bank_installment) 只在 Note 中提到
- 需確認完整的支援範圍

---

# 解決方案（決策 #6）

**決策日期**: 2026-01-09

**答案**: 簡化為線下付款方式記錄

**說明**:

- 付款方式改為專案人員手動記錄
- 建議枚舉值：
  - 'bank_transfer'（銀行轉帳）
  - 'aftee_installment'（AFTEE 分期）
  - 'credit_card_installment'（信用卡分期）
  - 'other'（其他）
- 不涉及線上付款整合，無需嚴格限制

**相關更新**:

- ✅ erm-subscription.dbml: payments.payment_method Note 更新
- ✅ 新建「專案人員開立機構訂閱.feature」- 包含記錄付款方式場景

**參考**: 架構重大調整決策.md
