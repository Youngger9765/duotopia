# 釐清問題

teacher_schools.roles 定義為 jsonb 陣列，有效值為 ['school_principal', 'school_admin', 'teacher']，但沒有說明如何驗證與防止無效值？

# 定位

ERM：teacher_schools 表，roles 欄位
Note: "學校角色列表（JSON 陣列）: ['school_principal', 'school_admin', 'teacher']"

# 多選題

| 選項 | 描述 |
|------|------|
| A | 僅在應用層驗證（API schema validation） |
| B | 使用 PostgreSQL CHECK 約束驗證陣列值 |
| C | 使用 ENUM 型別 + 陣列 |
| D | 無強制驗證，信任應用層 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響資料庫約束設計
- 影響 API 驗證邏輯
- 影響角色管理功能的實作
- 影響資料完整性

# 優先級

Medium

- 影響資料驗證策略
- 影響角色管理的正確性
