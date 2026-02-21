# 釐清問題

學生訂正次數是否有限制？

# 定位

Feature：output-training-assign.feature 學生作答與 AI 回饋 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 無限制，可無限訂正     |
| B     | 有最大訂正次數限制     |
| C     | 由老師自訂次數         |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響學生作答體驗、作業完成判斷、成績計算。

# 優先級

Medium

---

# 解決記錄

- **回答**：A - 無限制，可無限訂正，且學生不需立即訂正，可稍後再訂正。
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：明確規定學生訂正次數無限制，且訂正可延後進行，不需即時完成。
