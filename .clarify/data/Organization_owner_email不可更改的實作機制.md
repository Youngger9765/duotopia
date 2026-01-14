# 釐清問題

organizations.owner_email 標記為「無法更改」，但 DBML 中沒有技術約束或觸發器說明，具體的實作機制是什麼？

# 定位

ERM：organizations 表，owner_email 欄位
Note: "機構擁有人 Email（無法更改）"

# 多選題

| 選項 | 描述 |
|------|------|
| A | 僅在應用層控制，API 拒絕更新此欄位 |
| B | 資料庫層設定為 immutable/readonly（PostgreSQL 觸發器） |
| C | 允許更新但需額外驗證流程（如 Email 驗證） |
| D | 此欄位不應被更新，但無技術限制 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響 API 設計（PUT/PATCH organizations）
- 影響資料遷移策略（若擁有人 Email 變更需求）
- 影響安全性設計（防止非授權變更）

# 優先級

Medium

- 影響 API 實作設計
- 影響資料完整性保護策略
