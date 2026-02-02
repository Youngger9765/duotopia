# 釐清問題

organizations 和 schools 都有 name 和 display_name 兩個欄位，兩者的用途差異是什麼？哪個用於顯示，哪個用於識別？

# 定位

ERM：organizations 表和 schools 表
欄位: name (varchar(100), not null), display_name (varchar(200), nullable)

# 多選題

| 選項 | 描述 |
|------|------|
| A | name 用於系統識別，display_name 用於前端顯示 |
| B | name 為簡稱，display_name 為全名 |
| C | display_name 可空，為選用的別名 |
| D | 兩者可互換，沒有明確差異 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響 API 文件說明
- 影響前端顯示邏輯
- 影響搜尋功能設計
- 影響表單驗證規則

# 優先級

Low

- 不影響核心功能
- 主要影響使用體驗與文件清晰度
