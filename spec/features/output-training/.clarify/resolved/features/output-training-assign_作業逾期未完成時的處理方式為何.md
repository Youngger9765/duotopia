# 釐清問題

作業逾期未完成時的處理方式為何？

# 定位

Feature：output-training-assign.feature 作業成績與統計 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 逾期自動標記為未完成   |
| B     | 逾期可補交但扣分       |
| C     | 由老師設定逾期策略     |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響作業狀態、成績計算、學生體驗。

# 優先級

Medium

- Medium：影響邊界條件或測試完整性

---

# 解決記錄

- **回答**：B - 逾期可補交但扣分
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：在「作業成績與統計」Scenario 中新增步驟：「若學生逾期未完成，仍可補交但分數會扣分」。
