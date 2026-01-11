# 釐清問題

合約與訂閱是否一定是 1:1 關係？還是一個合約可以有多個訂閱？

# 定位

ERM：`spec/erm-subscription.dbml` - `contracts` 與 `subscriptions` 的關聯關係

# 多選題

| 選項  | 描述                                   |
| ----- | -------------------------------------- |
| A     | 1:1 關係（一個合約對應一個訂閱）       |
| B     | 1:N 關係（一個合約可續約產生多個訂閱） |
| C     | 1:N 關係（一個合約可拆分為多個子訂閱） |
| D     | N:1 關係（多個小合約合併為一個訂閱）   |
| Short | 提供其他簡短答案（<=5 字）             |

# 影響範圍

- 影響 DBML 中的關聯關係定義
- 影響訂閱開通邏輯
- 影響合約到期後的續約流程

# 優先級

Medium

理由：

- 目前 DBML 定義 `subscription.contract_id` → `contracts.id`
- 未明確標示為 unique（暗示可能 N:1）
- 但業務邏輯上通常是 1:1
- 需確認是否支援續約場景

---

# 解決方案（決策 #7）

**決策日期**: 2026-01-09

**答案**: 架構調整 - 改為多對多關聯

**說明**:

- 移除 subscriptions.contract_id
- contract_files 表新增 subscription_id（可選）
- 一個訂閱可關聯多份合約檔案（續約、補充協議）
- 訂閱條款快照儲存在 subscriptions 表（purchased_teachers, bonus_teachers, initial_points）

**相關更新**:

- ✅ erm-subscription.dbml:
  - 移除 subscriptions.contract_id
  - contract_files 新增 subscription_id 欄位
  - subscriptions 新增條款快照欄位

**參考**: 架構重大調整決策.md
