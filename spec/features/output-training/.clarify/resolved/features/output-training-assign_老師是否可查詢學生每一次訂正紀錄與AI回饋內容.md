# 釐清問題

老師是否可查詢學生每一次訂正紀錄與 AI 回饋內容？

# 定位

Feature：output-training-assign.feature 作業成績與統計 Scenario

# 多選題

| 選項  | 描述                     |
| ----- | ------------------------ |
| A     | 僅查詢最終訂正結果       |
| B     | 可查詢所有訂正與回饋紀錄 |
| C     | 由老師設定查詢範圍       |
| Short | 其他（請簡述，<=5 字）   |

# 影響範圍

影響老師端查詢介面、資料儲存設計、隱私與教學回饋。

# 優先級

Medium

- Medium：影響邊界條件或測試完整性

---

# 解決記錄

- **回答**：B - 可查詢所有訂正與回饋紀錄
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：在「作業成績與統計」Scenario 中新增步驟：「老師可查詢學生每一次訂正的文字紀錄與對應的 AI 回饋內容」。

---

# 解決記錄

- **回答**：B - 可查詢所有訂正與回饋紀錄（老師可查詢學生每一次訂正的文字紀錄與對應的 AI 回饋內容）
- **更新的規格檔**：spec/features/output-training/output-training-assign.feature
- **變更內容**：在「作業成績與統計」Scenario 的 Then 區段新增步驟「老師可查詢學生每一次訂正的文字紀錄與對應的 AI 回饋內容」，明確說明老師能查詢完整的訂正歷史。
