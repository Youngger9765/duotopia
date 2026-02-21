# 釐清問題

AI 回饋內容是否需保存所有版本？

# 定位

ERM：OutputTrainingFeedback.ai_feedback, OutputTrainingFeedback.correction_suggestion
Feature：output-training-assign.feature 學生作答與 AI 回饋 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 僅保存最終回饋         |
| B     | 保存所有訂正回饋       |
| C     | 由老師設定保存策略     |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響資料儲存設計、老師查詢、教學回饋。

# 優先級

Medium

- Medium：影響邊界條件或測試完整性

---

# 解決記錄

- **回答**：B - 保存所有訂正回饋（ai_feedback 和 correction_suggestion 都需保存每次訂正對應的版本）
- **更新的規格檔**：spec/features/output-training/output-training-data.dbml, spec/features/output-training/output-training-assign.feature
- **變更內容**：更新 OutputTrainingFeedback 表的欄位定義，移除 corrected_audio_url；更新 output-training-assign.feature 的學生作答情節。
- **補充澄清（2025-01-28）**：本模組不需要保存錄音檔，全部過程保留僅限文字紀錄。已移除 OutputTrainingFeedback 的 corrected_audio_url 欄位。
