# 釐清問題

分校管理人與分校校長的權限差異為何？

# 定位

角色定義：分校管理人（school_admin）的權限欄位，以及與分校校長的區別。
參考：spec/erm-organization.dbml 中 teacher_schools.roles 欄位的 school_admin 值。

# 多選題

| 選項  | 描述                                  |
| ----- | ------------------------------------- |
| A     | 無法新增/移除教師，其他功能與校長相同 |
| B     | 僅能查看資料，無修改權限              |
| C     | 可管理日常營運但無分校級重大決策權限  |
| Short | 列舉管理人「不能做」的具體項目        |

# 影響範圍

- School 相關的權限矩陣
- 分校管理功能的規格定義
- 分校管理 API 的權限驗證邏輯
- 與 school_principal 的權限對照表
- Casbin 權限策略的細化

# 優先級

High

---

# 解決記錄

- **回答**：分校管理人對應實作的 `school_director` 角色，與分校校長（school_admin）**權限完全相同**

- **權限對照**：

**兩者共有的權限（完全相同）**：
- ✅ `manage_teachers` - 管理分校內的教師
- ✅ `manage_students` - 管理分校內的學生
- ✅ `manage_classrooms` - 管理分校內的班級
- ✅ `view_school_analytics` - 查看分校數據分析

**語義差異**：
- `school_admin`（分校校長）：分校最高管理者
- `school_director`（分校管理人）：協助分校校長管理分校
- 權限層面無差異，僅職責名稱不同

**Casbin 策略確認**：
```csv
# school_admin permissions
p, school_admin, *, manage_teachers, write
p, school_admin, *, manage_students, write
p, school_admin, *, manage_classrooms, write
p, school_admin, *, view_school_analytics, read

# school_director permissions (same as school_admin)
p, school_director, *, manage_teachers, write
p, school_director, *, manage_students, write
p, school_director, *, manage_classrooms, write
p, school_director, *, view_school_analytics, read
```

- **更新的規格檔**：docs/specs/user-roles-and-permissions.md
- **變更內容**：在「機構類 > 分校管理人」章節說明與校長權限相同
- **實作參考**：
  - backend/config/casbin_policy.csv（school_director 與 school_admin 權限相同）
