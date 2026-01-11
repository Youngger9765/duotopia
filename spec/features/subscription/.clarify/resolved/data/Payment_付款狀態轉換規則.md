# 釐清問題

付款記錄的狀態之間的轉換規則是什麼？

# 定位

ERM：`spec/erm-subscription.dbml` - Table `payments` - 欄位 `status`

# 多選題

| 選項  | 描述                                                       |
| ----- | ---------------------------------------------------------- |
| A     | pending → completed/failed（線性，不可逆）                 |
| B     | pending → completed/failed，completed → refunded（可退款） |
| C     | pending ⇄ failed（可重試），completed → refunded           |
| D     | 所有狀態可互相轉換                                         |
| Short | 提供其他簡短答案（<=5 字）                                 |

# 影響範圍

- 影響付款狀態欄位的驗證邏輯
- 影響付款處理功能的狀態管理
- 影響合約開通邏輯（需等待 completed）
- 需要新增付款狀態轉換的 Feature Rules

# 優先級

High

理由：

- 付款狀態直接影響合約生效
- 未明確定義：
  - failed 後是否可以重試（變回 pending）
  - completed 後是否可以退款（變成 refunded）
  - refunded 後合約如何處理
- 影響錯誤處理與退款流程

---

# 解決方案（決策 #6）

**決策日期**: 2026-01-09

**答案**: 架構調整 - 移除付款狀態欄位

**說明**:

- 付款改為線下記錄，移除 status 欄位
- 線下付款完成後才由專案人員記錄
- 無需追蹤 pending/failed/completed 狀態
- 訂閱開通不依賴付款狀態（線下已確認）

**相關更新**:

- ✅ erm-subscription.dbml: 簡化 payments 表，移除 status 欄位
- ✅ 新建「專案人員開立機構訂閱.feature」

**參考**: 架構重大調整決策.md
