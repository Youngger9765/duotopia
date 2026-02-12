# 釐清問題

訂正後的作答是否需再次經 AI 評分？

# 定位

Feature：output-training-assign.feature 學生作答與 AI 回饋 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 每次訂正都需評分       |
| B     | 僅最終訂正需評分       |
| C     | 由老師設定評分策略     |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響 AI 評分模組、成績計算、學生訂正體驗。

# 優先級

Medium

- Medium：影響邊界條件或測試完整性

---

# 解決記錄

- **回答**：A - 每次訂正都需評分，總分 = 初次評分 + 訂正加分
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：更新「學生作答與 AI 回饋」Scenario，明確說明每次提交都進行 AI 評分，訂正後給予加分；更新「作業成績與統計」Scenario，說明總分計算方式為「初次評分 + 訂正加分」，並補充 AI 評分策略由老師設定（學生年齡、程度、額外說明）。
