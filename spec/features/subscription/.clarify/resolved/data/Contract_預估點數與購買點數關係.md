# 釐清問題

「預估年度點數」與「購買點數」的關係是什麼？

# 決策

**選項**: C - 預估是單年，購買是合約總年數

## 決策說明

**欄位定義**：

- `estimated_annual_points`：**單年**預估點數
- `purchased_points`：合約期間的**總點數**

**計算公式**：

```
estimated_annual_points = 學生數 × 每週練習次數 × 每次句數 × 52 週
purchased_points = estimated_annual_points × 合約年數
```

**範例驗證**：

- 一年約：
  - estimated_annual_points = 50 × 3 × 15 × 52 = 117,000
  - purchased_points = 117,000 × 1 = 117,000
- 兩年約：
  - estimated_annual_points = 50 × 3 × 15 × 52 = 117,000（單年）
  - purchased_points = 117,000 × 2 = 234,000（兩年總計）

## 推斷依據

- Feature「機構簽約與付款.feature」兩年約範例明確註解：「兩年總點數: 117,000 × 2 = 234,000」
- 保留 `estimated_annual_points` 欄位可用於：
  - 比較不同年約的單年成本
  - 續約時參考前一年的使用模式
  - 展示兩年約的優惠（兩年總點數 vs 單年 × 2）

---

# 解決記錄

- **回答**：D - 實際購買點數可自由調整，無限制（由業務人工確認，報價計算機僅供參考）
- **更新的規格檔**：spec/features/subscription/機構報價計算.feature
- **變更內容**：預估點數僅供參考，實際購買點數由業務人工確認

### 檔案：[spec/erm-subscription.dbml](../../../../../erm-subscription.dbml)

當前定義已正確：

```dbml
estimated_annual_points bigint [not null, note: "預估年度總點數 = 學生數 × 每週練習次數 × 每次句數 × 52 週"]
purchased_points bigint [not null, note: "簽約時購買的總點數"]
```

**建議補充 Note**：

```dbml
- 點數計算:
  - estimated_annual_points: 單年預估（用於比較與展示）
  - purchased_points: 合約總點數 = estimated_annual_points × 合約年數
```

### 檔案：[spec/features/subscription/機構簽約與付款.feature](../../機構簽約與付款.feature)

當前範例已正確展示此邏輯。建議在一年約場景中也加入 `estimated_annual_points` 以保持一致性。

## 信心評分

**High**

理由：

- Feature 範例明確展示此邏輯
- 註解清楚說明計算方式
- 符合業務需求（展示年約差異）

## 決策日期

2026-01-09
