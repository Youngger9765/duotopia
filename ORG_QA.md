# 組織管理後台 QA 測試指南

## 📋 角色權限對照表

| 角色 | 英文名稱 | 中文名稱 | 組織管理 | 學校管理 | 教師管理 | 訂閱管理 | 查看範圍 |
|------|---------|---------|---------|---------|---------|---------|---------|
| org_owner | Organization Owner | 機構擁有者 | ✅ | ✅ | ✅ | ✅ | 所有組織 |
| org_admin | Organization Admin | 機構管理員 | ✅ | ✅ | ✅ | ❌ | 被授權的組織 |
| school_admin | School Principal | 校長 | ❌ | ✅ (自己的學校) | ✅ (自己的學校) | ❌ | 自己的學校 |
| school_director | School Director | 主任 | ❌ | ✅ (自己的學校) | ✅ (自己的學校) | ❌ | 自己的學校 |
| teacher | Teacher | 教師 | ❌ | ❌ | ❌ | ❌ | 自己的班級 |

---

## 🔐 詳細權限說明

### 1. org_owner (機構擁有者) 👑

**Casbin 權限：**
```
✅ manage_schools (write)       # 可管理學校
✅ manage_teachers (write)      # 可管理教師
✅ manage_students (read/write) # 可管理學生
✅ manage_classrooms (write)    # 可管理教室
✅ manage_subscription (write)  # 可管理訂閱 💰
✅ view_analytics (read)        # 可查看分析
```

**職責：**
- 組織的實際擁有人或老闆
- 擁有完整的財務控制權
- 可以授權其他人成為 org_admin

---

### 2. org_admin (機構管理員) 👔

**Casbin 權限：**
```
✅ manage_schools (write)       # 可管理學校
✅ manage_teachers (write)      # 可管理教師
✅ manage_students (read/write) # 可管理學生
✅ manage_classrooms (write)    # 可管理教室
❌ manage_subscription (write)  # 不能管理訂閱
✅ view_analytics (read)        # 可查看分析
```

**職責：**
- 負責組織的日常營運
- 類似總經理或執行長
- 無法更改訂閱方案或處理付費

**與 org_owner 差異：**
- ❌ 無法管理訂閱/付費
- ✅ 其他管理權限相同

---

### 3. school_admin (校長) 🏫

**Casbin 權限：**
```
✅ manage_teachers (write)      # 可管理教師（僅限自己的學校）
✅ manage_students (write)      # 可管理學生（僅限自己的學校）
✅ manage_classrooms (write)    # 可管理教室（僅限自己的學校）
✅ view_school_analytics (read) # 可查看學校分析
❌ manage_schools (write)       # 不能管理學校層級
❌ manage_subscription (write)  # 不能管理訂閱
```

**職責：**
- 負責單一學校的整體管理
- 學校的最高負責人
- 可以授權主任協助管理

---

### 4. school_director (主任) 🎓

**Casbin 權限：**
```
✅ manage_teachers (write)      # 可管理教師（僅限自己的學校）
✅ manage_students (write)      # 可管理學生（僅限自己的學校）
✅ manage_classrooms (write)    # 可管理教室（僅限自己的學校）
✅ view_school_analytics (read) # 可查看學校分析
❌ manage_schools (write)       # 不能管理學校層級
❌ manage_subscription (write)  # 不能管理訂閱
```

**職責：**
- 協助校長管理學校
- 學校的副手或行政主管
- 可以處理教師、學生、班級管理

**與 school_admin 差異：**
- ✅ 權限完全相同
- 📝 差異僅在職位名稱
- 🎨 UI 顯示不同顏色徽章（校長=紫色，主任=橘色）

---

### 5. teacher (教師) 👨‍🏫

**Casbin 權限：**
```
✅ manage_own_classrooms (write) # 只能管理自己的教室
✅ manage_students (read)         # 只能讀取學生資訊
✅ view_own_analytics (read)      # 只能查看自己的分析
❌ 無法訪問組織管理後台
```

**職責：**
- 負責自己的班級教學
- 無法訪問組織管理功能

---

## 🧪 測試帳號清單

| 角色 | 姓名 | 帳號 | 密碼 | 測試用途 |
|------|------|------|------|---------|
| org_owner | 張機構 | owner@duotopia.com | owner123 | 完整權限測試 |
| org_admin | 李管理 | orgadmin@duotopia.com | orgadmin123 | 受限權限測試 |
| school_admin | - | schooladmin@duotopia.com | schooladmin123 | 校長權限測試 |
| school_admin | 劉明華 | liu@dd.com | 12345678 | 校長權限測試（快速登入） |
| school_admin | - | teacher_test_main@duotopia.com | teacher123 | 測試補習班-總校 校長 |
| school_director | 柯建國 | kk@kk.com | 12345678 | 主任權限測試（快速登入） |
| school_director | - | teacher_test_main_director@duotopia.com | teacher123 | 測試補習班-總校 主任 |
| school_director | - | teacher_test_taichung_director@duotopia.com | teacher123 | 測試補習班-台中分校 主任 |
| school_director | - | teacher_excellence_central_director@duotopia.com | teacher123 | 卓越教育-中央校區 主任 |
| teacher | 陳美玲 | orgteacher@duotopia.com | 12345678 | 教師權限測試（快速登入） |
| teacher | 楊婷婷 | ytttt@dd.com | 12345678 | 教師權限測試（快速登入） |

---

## 🔄 自動重定向行為總覽

當用戶點擊「組織管理」或直接訪問 `/organization/dashboard` 時，系統會根據角色自動重定向：

| 角色 | 自動重定向行為 | 目標頁面 | Console 訊息 |
|------|--------------|---------|-------------|
| org_owner | ❌ 不重定向 | `/organization/dashboard` | `🏢 org_owner: staying on dashboard` |
| org_admin | ✅ 重定向 | `/organization/{org_id}` (第一個組織) | `🏢 org_admin: redirecting to first organization` |
| school_admin | ✅ 重定向 | `/organization/schools/{school_id}` (第一個學校) | `🏫 Redirecting to first school` |
| school_director | ✅ 重定向 | `/organization/schools/{school_id}` (第一個學校) | `🏫 Redirecting to first school` |
| teacher | ✅ 重定向 | `/teacher/dashboard` (在 OrganizationLayout 權限檢查時) | - |

**設計理念：**
- **org_owner** 可以看全貌 → 停留在 dashboard 查看所有組織
- **org_admin** 管單一組織 → 直接進入組織詳情頁
- **school-level** 管單一學校 → 直接進入學校詳情頁
- **teacher** 無權限 → 返回教師後台

---

## 📝 測試案例

### Test Case 1: org_owner 完整功能測試 (無自動重定向)

**測試帳號：** owner@duotopia.com / owner123

**測試步驟：**
1. 登入系統
2. **🔄 檢查不會自動重定向：**
   - ✅ 登入後自動進入 `/organization/dashboard`
   - ✅ **停留在 dashboard 頁面** (不會重定向)
   - ✅ Console 顯示：`🏢 org_owner: staying on dashboard`
   - ✅ 可以看到「組織架構總覽」頁面

3. 檢查 Header 右上角顯示：
   - ✅ 姓名：張機構
   - ✅ Email：owner@duotopia.com
   - ✅ 角色：機構擁有者

4. 檢查左側 Sidebar 顯示：
   - ✅ 「所有機構」連結存在（因為 is_admin）
   - ✅ 顯示 5 個組織：
     - 測試補習班
     - 卓越教育集團
     - 未來學苑
     - 智慧教育中心
     - 全球語言學院
   - ✅ 每個組織可展開顯示學校列表

5. 點擊「測試補習班」：
   - ✅ 導航到 `/organization/{org_id}`
   - ✅ 顯示組織詳情頁面
   - ✅ 顯示「工作人員」區塊
   - ✅ 顯示「學校列表」區塊

6. 測試「邀請教師」功能：
   - ✅ 點擊「邀請教師」按鈕
   - ✅ 彈出 Dialog
   - ✅ 可選擇角色：org_admin 或 teacher
   - ✅ 填寫姓名、Email
   - ✅ 成功邀請

7. 測試「新增學校」功能：
   - ✅ 點擊「新增學校」按鈕
   - ✅ 彈出 Dialog
   - ✅ 填寫學校資訊
   - ✅ 成功新增

8. 測試「編輯學校」功能：
   - ✅ 點擊學校的編輯按鈕
   - ✅ 彈出 Dialog
   - ✅ 修改學校資訊
   - ✅ 成功更新

9. 測試「指派校長」功能：
   - ✅ 點擊「指派校長」按鈕
   - ✅ 選擇教師
   - ✅ 成功指派
   - ✅ 可以更換校長

**預期結果：**
- ✅ 所有功能可正常使用
- ✅ 看到所有組織和學校
- ✅ 可以管理訂閱（未來功能）

---

### Test Case 2: org_admin 受限功能測試 + 自動重定向

**測試帳號：** orgadmin@duotopia.com / orgadmin123

**測試步驟：**
1. 登入系統
2. **🔄 檢查自動重定向：**
   - ✅ 登入後自動進入 `/organization/dashboard`
   - ✅ 然後**自動重定向**到 `/organization/{org_id}` (第一個可訪問的組織)
   - ✅ Console 顯示：`🏢 org_admin: redirecting to first organization`
   - ❌ **不應該停留**在 dashboard 頁面

3. 檢查組織詳情頁 Header 顯示：
   - ✅ 姓名：李管理
   - ✅ Email：orgadmin@duotopia.com
   - ✅ 角色：機構管理員

4. 檢查左側 Sidebar 顯示：
   - ❌ 「所有機構」連結不存在
   - ✅ 只顯示 1 個組織：測試補習班
   - ✅ 可展開顯示該組織的學校

5. 測試功能權限：
   - ✅ 可以新增/編輯學校
   - ✅ 可以邀請教師
   - ✅ 可以指派校長
   - ❌ 無法看到訂閱管理按鈕

6. **🔄 測試手動訪問 dashboard：**
   - ✅ 在瀏覽器輸入 `/organization/dashboard`
   - ✅ 應該再次自動重定向到組織詳情頁
   - ❌ 不應該能看到 dashboard 頁面

**預期結果：**
- ✅ 只能管理被授權的組織
- ❌ 無法管理訂閱
- ❌ 看不到其他組織
- ✅ **自動重定向到第一個組織** (不停留在 dashboard)

---

### Test Case 3: school_admin 校長權限測試 + 自動重定向

**測試帳號：**
- liu@dd.com / 12345678 (劉明華)
- teacher_test_main@duotopia.com / teacher123

**測試步驟：**
1. 登入系統
2. **🔄 檢查自動重定向：**
   - ✅ 登入後自動進入 `/organization/dashboard`
   - ✅ 然後**自動重定向**到 `/organization/schools/{school_id}` (第一個學校)
   - ✅ Console 顯示：`🏫 school-level user: fetching schools for redirect`
   - ✅ Console 顯示：`🏫 Redirecting to first school {school_id}`
   - ❌ **不應該停留**在 dashboard 頁面

3. 檢查學校詳情頁 Header 顯示：
   - ✅ 角色：學校管理員（校長）

4. 檢查學校詳情頁內容：
   - ✅ 可以看到學校詳情
   - ✅ 可以看到「教師團隊」列表
   - ✅ 自己顯示為校長（紫色徽章）

5. 測試「邀請教師」功能：
   - ✅ 點擊「邀請教師」按鈕
   - ✅ 彈出 Dialog 有兩個 Tab：
     - Tab 1: 從組織選擇
     - Tab 2: 獨立邀請
   - ✅ Tab 切換有藍色 active 效果
   - ✅ 可選擇角色：teacher 或 school_director
   - ✅ 成功邀請

6. 檢查教師列表排序：
   - ✅ 校長排在最前面（紫色徽章）
   - ✅ 主任排在中間（橘色徽章）
   - ✅ 教師排在最後（灰色徽章）

7. **🔄 測試手動訪問 dashboard：**
   - ✅ 在瀏覽器輸入 `/organization/dashboard`
   - ✅ 應該再次自動重定向到學校詳情頁
   - ❌ 不應該能看到 dashboard 頁面

**預期結果：**
- ✅ 可以管理自己的學校
- ✅ 可以邀請教師和主任
- ❌ 無法管理組織層級
- ❌ 無法新增/刪除學校
- ✅ **自動重定向到第一個學校** (不停留在 dashboard)

---

### Test Case 4: school_director 主任權限測試 + 自動重定向

**測試帳號：**
- kk@kk.com / 12345678 (柯建國)
- teacher_test_main_director@duotopia.com / teacher123

**測試步驟：**
1. 登入系統
2. **🔄 檢查自動重定向：**
   - ✅ 登入後自動進入 `/organization/dashboard`
   - ✅ 然後**自動重定向**到 `/organization/schools/{school_id}` (第一個學校)
   - ✅ Console 顯示：`🏫 school-level user: fetching schools for redirect`
   - ✅ 與 school_admin 行為完全相同

3. 檢查學校詳情頁自己的角色顯示：
   - ✅ 顯示為「主任」
   - ✅ 橘色徽章（amber badge）

4. 測試管理功能：
   - ✅ 可以邀請教師
   - ✅ 可以管理學生
   - ✅ 可以管理教室
   - ✅ 權限與校長相同

5. 與校長的差異：
   - ✅ 權限完全相同
   - ✅ 自動重定向行為相同
   - ✅ 只有職位名稱和徽章顏色不同
   - 校長：紫色徽章
   - 主任：橘色徽章
   - 教師：灰色徽章

**預期結果：**
- ✅ 權限與校長相同
- ✅ UI 顯示為「主任」（橘色）
- ✅ 可以協助校長管理學校
- ✅ **自動重定向到第一個學校** (與校長相同行為)

---

### Test Case 5: teacher 無權限測試

**測試帳號：** orgteacher@duotopia.com / orgteacher123

**測試步驟：**
1. 登入系統
2. 訪問 `http://localhost:5173/organization`
3. 檢查訪問結果：
   - ✅ 自動重定向到 `/teacher/dashboard`
   - ✅ 無法訪問組織管理頁面

**預期結果：**
- ❌ 無法訪問組織管理
- ✅ 重定向到教師後台

---

## 🎨 UI 設計規範

### 角色徽章顏色

| 角色 | 顏色 | Tailwind Class | 用途 |
|------|------|----------------|------|
| 校長 (school_admin) | 紫色 | `bg-purple-100 text-purple-800` | 學校最高負責人 |
| 主任 (school_director) | 橘色 | `bg-amber-100 text-amber-800` | 協助校長管理 |
| 教師 (teacher) | 灰色 | `bg-gray-100 text-gray-800` | 一般教師 |
| 組織擁有者 (org_owner) | - | - | 組織層級角色 |
| 組織管理員 (org_admin) | - | - | 組織層級角色 |

### Tab Active 樣式

- **Active 顏色：** 藍色 (`bg-blue-600`)
- **Active 文字：** 白色 (`text-white`)
- **陰影效果：** `shadow-md`
- **過渡動畫：** `transition-all`

### 教師列表排序

**優先級：**
1. 校長 (school_admin) - 優先級 1
2. 主任 (school_director) - 優先級 2
3. 教師 (teacher) - 優先級 3

---

## 🐛 已知問題與限制

### 1. school_admin 側邊欄顯示問題

**問題：**
- school_admin 可以進入組織管理頁面
- 但 Sidebar 可能是空的（因為 API 使用 `owner_only=true`）

**建議：**
- 為 school_admin 顯示他們所屬的學校
- 或限制 school_admin 只能訪問學校詳情頁

### 2. 角色與權限的對應

**org_owner vs org_admin：**
- 差異：訂閱管理權限
- 類比：老闆 vs 總經理

**school_admin vs school_director：**
- 差異：僅職位名稱
- 類比：正副手關係（權限相同）

---

## 📊 測試檢查清單

### 功能測試

- [ ] org_owner 可以看到所有組織
- [ ] org_admin 只能看到被授權的組織
- [ ] school_admin 可以管理自己的學校
- [ ] school_director 權限與 school_admin 相同
- [ ] teacher 無法訪問組織管理

### 角色顯示測試

- [ ] 校長顯示紫色徽章
- [ ] 主任顯示橘色徽章
- [ ] 教師顯示灰色徽章
- [ ] Header 正確顯示角色名稱

### UI 測試

- [ ] Tab active 顯示藍色
- [ ] 教師列表按角色排序
- [ ] 邀請教師可選擇角色
- [ ] Dialog 樣式正確

### 權限測試

- [ ] org_owner 可以管理訂閱（未來）
- [ ] org_admin 無法管理訂閱
- [ ] school_admin 無法新增/刪除學校
- [ ] teacher 被重定向

---

## 🔄 回歸測試

每次更新後，請執行以下回歸測試：

1. **角色權限測試**
   - 測試所有 5 種角色的訪問權限
   - 確認權限邊界正確

2. **UI 一致性測試**
   - 檢查徽章顏色正確
   - 檢查 Tab 樣式正確
   - 檢查排序功能正常

3. **功能完整性測試**
   - 邀請教師功能
   - 新增/編輯學校功能
   - 指派校長功能

---

## 📞 問題回報

如發現問題，請提供：
1. 測試帳號
2. 重現步驟
3. 預期結果
4. 實際結果
5. 截圖（如有）

---

**文件版本：** v1.0
**最後更新：** 2026-01-02
**維護者：** Duotopia 開發團隊
