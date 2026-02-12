# 釐清問題

學生作答內容（錄音/文字）是否需保存所有版本？

# 定位

ERM：OutputTrainingSubmission.content, OutputTrainingSubmission.audio_url
Feature：output-training-assign.feature 學生作答與 AI 回饋 Scenario

# 多選題

| 選項  | 描述                   |
| ----- | ---------------------- |
| A     | 僅保存最終版本         |
| B     | 保存所有訂正版本       |
| C     | 由老師設定保存策略     |
| Short | 其他（請簡述，<=5 字） |

# 影響範圍

影響資料儲存設計、隱私政策、老師查詢與教學回饋。

# 優先級

Medium

---

# 解決記錄

# 解決記錄

- **回答**：B - 保存所有訂正版本（文字紀錄都需保存每次訂正的版本）
- **更新的規格檔**：spec/features/output-training/output-training-data.dbml, spec/features/output-training/output-training-assign.feature
- **變更內容**：移除 OutputTrainingSubmission 的 audio_url 欄位；content 欄位保存「所有訂正版本」的文字紀錄；更新 output-training-assign.feature 的學生作答情境。
- **補充澄清（2025-01-28）**：本模組不需要保存錄音檔，全部過程保留僅限文字紀錄。已移除 OutputTrainingSubmission 和 OutputTrainingFeedback 的錄音檔相關欄位。
