# 釐清問題

建立機構.feature 說明「僅 Platform Owner（Teacher.is_admin = True）」可建立機構，但 erm-organization.dbml 沒有提到 Teacher 表或 is_admin 欄位，兩者如何關聯？

# 定位

Feature: 建立機構.feature
Rule: 僅系統管理員可以建立機構
背景資訊: "建立機構權限: 僅 Platform Owner（Teacher.is_admin = True）"

ERM: erm-organization.dbml 中沒有定義 Teacher 表

# 多選題

| 選項 | 描述 |
|------|------|
| A | Teacher 表定義在其他 DBML 檔案中 |
| B | 應在 erm-organization.dbml 中引用 Teacher 表 |
| C | Platform Owner 與 Teacher 表分離管理 |
| D | 需建立 Teacher 表與 organizations 的關聯說明 |
| Short | 提供其他簡短答案（<=5 字） |

# 影響範圍

- 影響跨 DBML 檔案的一致性
- 影響權限檢查邏輯
- 影響 API 實作（建立機構的身份驗證）

# 優先級

Medium

- 影響規格完整性
- 需確保 Feature 與 DBML 一致性
