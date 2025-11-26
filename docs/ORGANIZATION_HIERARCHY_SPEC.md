# 機構層級管理系統設計規格

## 🎯 目標
建立多層級組織架構，支援機構 → 分校 → 老師 → 班級的層級管理，並保留現有的教學與學習功能。

---

## 📊 組織架構層級

```
機構 (Organization)
  └── 分校 (Branch/Campus)
       └── 老師 (Teacher)
            └── 班級 (Classroom)
                 └── 學生 (Student)
```

---

## 🏗️ 資料模型設計

### 1. Organization (機構)
**新增資料表**: `organizations`

| 欄位 | 類型 | 說明 | 備註 |
|------|------|------|------|
| id | UUID | 主鍵 | |
| name | VARCHAR(200) | 機構名稱 | 如：「均一教育平台」 |
| display_name | VARCHAR(200) | 顯示名稱 | |
| slug | VARCHAR(100) | URL 識別碼 | unique, 用於多租戶路由 |
| plan_type | ENUM | 方案類型 | 'free', 'basic', 'premium', 'enterprise' |
| max_branches | INTEGER | 分校數量上限 | null = 無限制 |
| max_teachers_per_branch | INTEGER | 每分校老師數上限 | null = 無限制 |
| max_students_per_branch | INTEGER | 每分校學生數上限 | null = 無限制 |
| subscription_status | ENUM | 訂閱狀態 | 'active', 'suspended', 'cancelled' |
| billing_email | VARCHAR(255) | 帳務聯絡信箱 | |
| contact_person | VARCHAR(100) | 聯絡人 | |
| contact_phone | VARCHAR(20) | 聯絡電話 | |
| created_at | TIMESTAMP | 建立時間 | |
| updated_at | TIMESTAMP | 更新時間 | |

### 2. Branch (分校)
**新增資料表**: `branches`

| 欄位 | 類型 | 說明 | 備註 |
|------|------|------|------|
| id | UUID | 主鍵 | |
| organization_id | UUID | 所屬機構 | FK → organizations.id |
| name | VARCHAR(200) | 分校名稱 | 如：「台北校區」 |
| slug | VARCHAR(100) | URL 識別碼 | unique within organization |
| address | TEXT | 地址 | |
| manager_name | VARCHAR(100) | 分校主管 | |
| manager_email | VARCHAR(255) | 主管信箱 | |
| status | ENUM | 狀態 | 'active', 'inactive' |
| created_at | TIMESTAMP | 建立時間 | |
| updated_at | TIMESTAMP | 更新時間 | |

### 3. Teacher (老師) - 修改現有資料表
**修改資料表**: `teachers`

新增欄位：
- `organization_id` (UUID, FK → organizations.id)
- `branch_id` (UUID, FK → branches.id)

### 4. Classroom (班級) - 保持現有資料表
**現有資料表**: `classrooms`

新增欄位：
- `branch_id` (UUID, FK → branches.id) - 用於快速查詢

---

## 🔐 權限管理

### 1. Organization Admin (機構管理員)
**新增角色**: `organization_admin`

**權限範圍**:
- ✅ 管理所有分校
- ✅ 新增/編輯/停用分校
- ✅ 查看所有分校的老師、學生、班級
- ✅ 查看整體營運數據
- ✅ 管理訂閱與帳單
- ❌ 不能直接操作教學內容（需透過分校/老師）

### 2. Branch Manager (分校主管)
**新增角色**: `branch_manager`

**權限範圍**:
- ✅ 管理該分校內所有老師
- ✅ 邀請/移除老師
- ✅ 查看該分校內所有班級、學生
- ✅ 查看該分校營運數據
- ❌ 不能跨分校操作
- ❌ 不能修改機構層級設定

### 3. Teacher (老師) - 現有角色
**權限範圍**: 保持不變
- ✅ 管理自己的班級
- ✅ 管理班級內學生
- ✅ 建立作業、課程
- ❌ 不能跨班級操作（除非被授權）

### 4. Student (學生) - 現有角色
**權限範圍**: 保持不變

### 5. System Admin (系統管理員) - 現有角色
**權限範圍**: 保持不變，最高權限

---

## 💰 金流與收費設計

### 方案層級對照表

| 方案 | 分校數 | 每分校老師數 | 每分校學生數 | 月費 | 計費方式 |
|------|--------|-------------|-------------|------|---------|
| **Free** | 1 | 5 | 50 | $0 | - |
| **Basic** | 3 | 20 | 500 | $299 | 機構層級月繳 |
| **Premium** | 10 | 50 | 2000 | $999 | 機構層級月繳 |
| **Enterprise** | 無限制 | 無限制 | 無限制 | 議價 | 年約 |

### 收費策略

1. **機構層級計費**:
   - 以 Organization 為單位收費
   - 一個機構一張訂閱，涵蓋所有分校

2. **超量計費** (Premium/Enterprise):
   - 超過方案限制時，每增加 1 個分校 +$99/月
   - 每增加 10 位老師 +$49/月
   - 每增加 100 位學生 +$29/月

3. **現有個人老師** (保持不變):
   - 不屬於任何機構的老師，維持現有計費模式
   - organization_id = NULL, branch_id = NULL

---

## 🔄 資料遷移策略

### 階段 1: Schema 變更
1. 新增 `organizations` 和 `branches` 資料表
2. 在 `teachers` 新增 `organization_id`, `branch_id` (nullable)
3. 在 `classrooms` 新增 `branch_id` (nullable)

### 階段 2: 現有資料處理
- 現有老師的 `organization_id` 和 `branch_id` 維持 NULL
- 保持現有功能 100% 相容

### 階段 3: 新機構建立
- 新註冊的機構使用新架構
- 逐步邀請現有老師加入機構

---

## 🎨 UI/UX 設計

### 1. Organization Admin Dashboard
- 機構總覽（分校數、老師數、學生數）
- 分校列表與管理
- 訂閱與帳單管理
- 營運數據儀表板

### 2. Branch Manager Dashboard
- 分校總覽（老師數、班級數、學生數）
- 老師列表與管理
- 班級與學生總覽（唯讀）
- 分校營運數據

### 3. Teacher Dashboard (保持不變)
- 現有功能完全保留

---

## 🚀 實作優先順序

### Phase 1: 資料模型與基礎架構 (2 weeks)
- [ ] 建立 `organizations` 資料表
- [ ] 建立 `branches` 資料表
- [ ] 修改 `teachers` 資料表
- [ ] 修改 `classrooms` 資料表
- [ ] 建立 Alembic migration
- [ ] 建立基礎 API endpoints

### Phase 2: 權限與認證 (1 week)
- [ ] 實作 Organization Admin 角色
- [ ] 實作 Branch Manager 角色
- [ ] 實作多租戶 Row Level Security (RLS)
- [ ] 修改現有 API 權限檢查

### Phase 3: Organization Admin 功能 (2 weeks)
- [ ] 機構總覽頁面
- [ ] 分校 CRUD 功能
- [ ] 老師邀請與管理
- [ ] 營運數據儀表板

### Phase 4: Branch Manager 功能 (1 week)
- [ ] 分校總覽頁面
- [ ] 老師管理功能
- [ ] 分校數據儀表板

### Phase 5: 訂閱與金流 (2 weeks)
- [ ] 方案選擇與升級
- [ ] TapPay 整合（機構層級）
- [ ] 發票與帳單管理
- [ ] 超量計費邏輯

### Phase 6: 測試與優化 (1 week)
- [ ] E2E 測試
- [ ] 效能優化
- [ ] 安全性審查

---

## 🔍 待討論問題

### 1. 多租戶路由設計
**選項 A**: Subdomain
- `org-name.duotopia.com/branch-name/`
- 優點: 清楚區分, SEO 友善
- 缺點: DNS/SSL 設定複雜

**選項 B**: Path-based
- `duotopia.com/org/org-name/branch/branch-name/`
- 優點: 簡單實作
- 缺點: URL 較長

**建議**: ?

### 2. 老師轉移
- 現有個人老師想加入機構時，如何處理？
- 資料遷移？
- 權限變更？

### 3. 跨分校班級
- 是否允許老師建立跨分校的班級？
- 如：線上課程同時給多個分校學生

### 4. 資料隔離層級
- 是否需要實體資料庫分離？
- 還是 RLS 即可？

---

## 📝 Notes
- 此規格為初稿，需與產品、業務團隊討論確認
- 金流數字為參考值，需根據市場調研調整
- UI/UX 需設計團隊產出 wireframe 和 mockup

---

**建立日期**: 2025-11-26
**版本**: v0.1
**狀態**: Draft
**負責人**: [待指派]
