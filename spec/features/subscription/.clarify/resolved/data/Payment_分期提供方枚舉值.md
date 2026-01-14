# 釐清問題

付款記錄中「分期提供方」的完整枚舉值有哪些？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `payments` - 欄位 `installment_provider`

# 多選題

| 選項  | 描述                                                  |
| ----- | ----------------------------------------------------- |
| A     | 僅 'aftee'（目前階段只支援 AFTEE）                    |
| B     | 'aftee'、'yushan_bank'、'ctbc'（AFTEE + 兩家銀行）    |
| C     | 'aftee'、'yushan_bank'、'ctbc'、'other'（含其他選項） |
| D     | 開放字串，不限定枚舉值                                |
| Short | 提供其他簡短答案（<=5 字）                            |

# 影響範圍

- 影響 `payments.installment_provider` 欄位的約束條件
- 影響付款方式選擇功能的選項
- 影響第三方整合的範圍

# 優先級

Medium

理由：

- DBML Note 提到 'aftee'、'yushan_bank'、'ctbc'
- 但未定義為 enum 約束
- 需確認是否要限制為枚舉值，或保持彈性
- 影響資料驗證規則

---

# 解決方案（決策 #6）

**決策日期**: 2026-01-09

**答案**: 保持彈性，作為記錄欄位

**說明**:

- 分期提供方改為專案人員手動填寫
- 建議參考值：
  - 'aftee'（AFTEE）
  - 'yushan_bank'（玉山銀行）
  - 'ctbc'（中信銀行）
  - 'other'（其他）
- 不強制限制為 enum，保留彈性供未來新增提供方

**相關更新**:

- ✅ erm-subscription.dbml: payments.installment_provider 保持為 varchar
- ✅ 新建「專案人員開立機構訂閱.feature」- 包含分期記錄場景

**參考**: 架構重大調整決策.md
