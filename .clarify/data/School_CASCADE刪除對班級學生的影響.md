# 釐清問題

schools 表與 organizations 表的關聯設定為 CASCADE 刪除，當 organization 被刪除時：
- schools 會被 CASCADE 刪除
- classrooms（透過 classroom_schools）是否同時刪除？
- students 是否同時刪除？
- 刪除行為的完整鏈路是什麼？

# 定位

ERM: schools 表
關聯: organization_id uuid [not null, ref: > organizations.id, note: "所屬機構 ID，CASCADE 刪除"]

連鎖影響: classroom_schools, classrooms, students

# 多選題

| 選項 | 描述 |
|------|------|
| A | 完整 CASCADE：organization → schools → classrooms → students 全部刪除 |
| B | 僅刪除關聯表，保留 classrooms 與 students |
| C | 軟刪除策略（設定 is_active=false） |
| D | 阻止刪除（若有資料存在） |
| E | 分階段刪除（需確認流程） |

# 影響範圍

- 影響所有外鍵 CASCADE 設定
- 影響資料保護策略
- 影響機構關閉流程
- 影響歷史資料保留
- 需在 Feature 中補充刪除場景

# 優先級

High

- 影響資料完整性
- 影響業務關鍵流程
- 需明確定義刪除策略
