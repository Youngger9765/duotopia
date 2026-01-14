# 釐清問題

classroom_schools 表明「一個班級只能屬於一個學校」，當學校被刪除或停用時，班級應如何處理？CASCADE 刪除或標記為孤立？

# 定位

ERM：classroom_schools 表
關聯: classroom_id ref > classrooms.id, school_id ref > schools.id
Note: "CASCADE 刪除"

# 多選題

| 選項 | 描述 |
|------|------|
| A | CASCADE 刪除班級（完全刪除） |
| B | 設定 is_active=false（軟刪除） |
| C | 將班級轉為獨立教師班級（移除關聯） |
| D | 阻止刪除學校（若有班級存在） |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響資料庫外鍵約束設計
- 影響學校刪除流程
- 影響班級生命週期管理
- 影響學生資料保留策略

# 優先級

High

- 影響資料完整性
- 影響業務流程（學校關閉情境）
- 需在 Feature 中補充刪除場景
