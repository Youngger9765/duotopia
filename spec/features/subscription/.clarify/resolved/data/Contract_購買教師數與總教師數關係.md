# 釐清問題

合約中的「購買教師數」與「總教師數」的關係是什麼？

# 決策

**選項**: A - total_teachers = purchased_teachers + bonus_teachers（總數 = 購買 + 贈送）

## 決策說明

基於專案擁有人澄清：

**關係公式**：

```
total_teachers = purchased_teachers + bonus_teachers
```

**欄位定義**：

- `total_teachers`：最終開通的授權總數（實際可使用的教師席位）
- `purchased_teachers`：標記為「購買」的教師數（業務記錄用）
- `bonus_teachers`：標記為「贈送」的教師數（業務記錄用）

**計費邏輯**：

- 費用計算基礎：`total_teachers`（總授權數）
- 公式：`teacher_cost = total_teachers × teacher_monthly_price × 合約月數`
- **重要**：以總授權數計費，而非僅購買數

**設定方式**：

- 三個欄位皆由業務人員在簽約時**手動輸入**
- 系統驗證：`total_teachers = purchased_teachers + bonus_teachers`
- `purchased_teachers` 和 `bonus_teachers` 的拆分僅供內部記錄

---

# 解決記錄

- **回答**：B - 總教師授權數 = 購買教師數，贈送教師數不計入授權
- **更新的規格檔**：spec/erm-subscription.dbml
- **變更內容**：contracts 表 total_teacher_licenses 欄位 note 改為「教師授權總數 = purchased_teachers，不含贈送教師數」
- 拆分記錄方便追蹤商務談判結果

## 規格更新

### 更新檔案：[spec/erm-subscription.dbml](../../../../../erm-subscription.dbml)

已在 Note 中說明：

```dbml
- 購買與贈送拆分: 由業務人員根據商務談判結果手動決定
  - total_teachers = purchased_teachers + bonus_teachers
  - 建議參考值: 一年約贈 3 位，兩年約贈 5 位（可調整）
```

### 資料驗證規則

需在應用層或資料庫層加入檢查約束：

```sql
CHECK (total_teachers = purchased_teachers + bonus_teachers)
```

### Feature 更新

「機構報價計算.feature」已簡化，不再涉及購買/贈送拆分。

## 信心評分

**High**

理由：

- 基於專案擁有人的明確說明
- 關係公式清晰明確
- 符合資料完整性原則

## 決策日期

2026-01-09
