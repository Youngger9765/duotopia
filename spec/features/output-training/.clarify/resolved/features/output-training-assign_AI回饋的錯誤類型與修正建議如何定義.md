# 釐清問題

AI 回饋的錯誤類型與修正建議如何定義？

# 定位

Feature：output-training-assign.feature 學生作答與 AI 回饋 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 僅語法錯誤與修正       |
| B     | 語法＋語意錯誤與修正   |
| C     | 語音辨識錯誤也需回饋   |
| D     | 由老師自訂錯誤類型     |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響 AI 回饋模組、學生訂正流程、作業完成判斷與成績計算。

# 優先級

High

---

# 解決記錄

- **回答**：C - 語音辨識錯誤也需回饋
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：AI 回饋需包含語音辨識相關錯誤（如發音不清、AI 聽錯單字等），不僅限於語法或語意錯誤。
