# 釐清問題

organizations.tax_id 設定為 unique，若機構被停用（is_active=false）或刪除後，同一統編是否可重新註冊？

# 定位

ERM：organizations 表，tax_id 欄位
約束: unique, not null

# 多選題

| 選項 | 描述 |
|------|------|
| A | 永久唯一，即使機構停用也不可重複 |
| B | 僅在 is_active=true 時唯一（部分唯一索引） |
| C | 機構刪除後統編可重用（硬刪除） |
| D | 機構停用一段時間後統編可重用 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響索引設計（unique vs partial unique index）
- 影響機構刪除策略（軟刪除 vs 硬刪除）
- 影響業務邏輯（機構重新啟用流程）
- 影響 Example 設計（停用與重新啟用測試）

# 優先級

High

- 影響資料庫索引設計
- 影響核心業務規則（機構生命週期）
