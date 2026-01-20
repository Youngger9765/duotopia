# 釐清問題

角色的資料結構應採用哪種設計方式？

# 定位

ERM：User 實體與角色的關聯設計方式，影響所有角色相關的表結構。

# 多選題

| 選項 | 描述                                                            |
| ---- | --------------------------------------------------------------- |
| A    | 單一用戶表 + 角色欄位（role ENUM），每個用戶只能有一種角色      |
| B    | 教師表 + 學生表分離設計，不同類型用戶使用不同表                 |
| C    | 角色繼承體系（User > Teacher > InstitutionTeacher），使用表繼承 |
| D    | 多角色關聯表（User-Role 多對多關係），支援一個用戶擁有多種角色  |
| E    | 混合模式（User 主表 + 角色特定表 + User-Role 關聯表）           |

# 影響範圍

- 所有角色相關的實體設計（User, Teacher, Student, Organization, School）
- 權限查詢邏輯的複雜度
- 跨類型角色的支援方式
- 角色切換機制的實作難度
- 資料庫查詢效能

# 優先級

High

---

# 解決記錄

- **回答**：B + 部分 E - Teacher/Student 分離設計 + 使用關聯表處理機構角色（teacher_organizations, teacher_schools）
- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「資料模型考量 > 角色的資料結構」章節記錄現有架構設計決策
