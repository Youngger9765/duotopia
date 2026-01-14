# 釐清問題

organizations.settings 和 schools.settings 定義為 jsonb，但沒有說明具體的 JSON 結構、必要欄位或預設值是什麼？

# 定位

ERM：organizations 表與 schools 表，settings 欄位
型別: jsonb, nullable

# 多選題

| 選項 | 描述 |
|------|------|
| A | 完全自由格式，由應用層定義 |
| B | 有標準 schema，需驗證格式 |
| C | 預設為空物件 {}，按需擴充 |
| D | 包含特定業務設定（如通知偏好、權限覆蓋等） |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響 API 文件（settings 欄位說明）
- 影響前端表單設計（設定頁面）
- 影響資料驗證邏輯
- 若有標準欄位，應在 DBML note 中說明

# 優先級

Medium

- 影響 API 設計與文件
- 影響前端實作
- 不阻礙核心流程，但影響功能完整性
