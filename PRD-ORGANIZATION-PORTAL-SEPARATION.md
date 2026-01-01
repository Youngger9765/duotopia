# PRD: 組織管理後台分離

**Date**: 2026-01-01 | **Status**: Planning
**Issue**: Refactoring | **Priority**: P0 (Blocker)

---

## Overview

將組織管理功能從教師後台 (`/teacher/*`) 完全分離，建立獨立的組織管理後台 (`/organization/*`)。

**現狀問題:**
- 教師後台混雜教學功能和組織管理功能
- 權限控制複雜，容易出現「尚無機構」混淆訊息
- UI/UX 不清晰，組織管理員和教師使用同一套介面

**目標:**
- 清晰分離兩種使用場景
- 教師後台專注於教學功能
- 組織管理後台專注於組織架構和人員管理

---

## User Stories

### Story 1: 教師使用教師後台
```
As a 教師 (teacher)
I want 登入後看到純粹的教學功能（班級、學生、作業）
So that 我不會被組織管理功能困惑
```

### Story 2: 組織管理員使用組織後台
```
As a 組織管理員 (org_owner/org_admin)
I want 登入後進入專門的組織管理介面
So that 我可以管理組織架構、學校和人員
```

### Story 3: 雙重角色自動導向
```
As a 同時擁有教學和組織管理權限的用戶
I want 系統根據我的角色自動導向正確的後台
So that 我可以快速進入我需要的功能
```

---

## Requirements

### Functional Requirements

#### FR1: 路由分離
- [x] **教師後台路由**: `/teacher/*`
  - `/teacher/dashboard` - 教師儀表板（純教學統計）
  - `/teacher/classrooms` - 我的班級
  - `/teacher/students` - 所有學生
  - `/teacher/programs` - 我的課程
  - `/teacher/profile` - 個人資料
  - `/teacher/subscription` - 訂閱管理

- [ ] **組織管理後台路由**: `/organization/*`
  - `/organization/dashboard` - 組織儀表板（組織架構圖）
  - `/organization/list` - 我的組織列表（如有多個）
  - `/organization/:id` - 組織詳情
  - `/organization/:id/schools` - 學校管理
  - `/organization/:id/teachers` - 人員管理
  - `/organization/:id/settings` - 組織設定

#### FR2: Layout 分離
- [x] **TeacherLayout** - 教師後台 Layout
  - 左側選單: 教學相關功能
  - 不顯示組織管理選項

- [ ] **OrganizationLayout** - 組織管理 Layout
  - 左側選單: 組織管理功能
  - 頂部: 組織切換器（如有多個組織）
  - 主區域: 組織架構視覺化 + CRUD 操作

#### FR3: 權限控制重構
- [ ] **教師後台**: 所有已登入教師可訪問
- [ ] **組織後台**: 僅 `org_owner`, `org_admin`, `school_admin` 可訪問
- [ ] **自動導向**:
  - 登入後根據角色導向正確的首頁
  - 無組織角色 → `/teacher/dashboard`
  - 有組織角色 → `/organization/dashboard`（優先）

#### FR4: 組織架構視覺化
- [ ] **左側 Sidebar**:
  - 組織層級樹狀結構
  - 可展開/收合學校
  - 點擊切換當前選中的組織/學校

- [ ] **右側 Body**:
  - 根據左側選擇顯示對應的管理介面
  - 組織 CRUD
  - 學校 CRUD
  - 人員管理

### Non-Functional Requirements

#### NFR1: 性能
- [ ] 首次載入 < 2s
- [ ] 組織架構圖渲染 < 500ms
- [ ] 路由切換 < 300ms

#### NFR2: 可用性
- [ ] 清晰的視覺層級（組織 → 學校 → 教師）
- [ ] 麵包屑導航
- [ ] 明確的權限提示訊息

#### NFR3: 相容性
- [ ] 保持現有 API 不變
- [ ] 向後相容舊的 `/teacher` 路由（逐步遷移）

---

## Technical Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   Teacher Portal     │      │  Organization Portal │    │
│  │   /teacher/*         │      │  /organization/*     │    │
│  ├──────────────────────┤      ├──────────────────────┤    │
│  │ - TeacherLayout      │      │ - OrganizationLayout │    │
│  │ - Dashboard (教學)   │      │ - Dashboard (組織圖) │    │
│  │ - Classrooms         │      │ - Organizations CRUD │    │
│  │ - Students           │      │ - Schools CRUD       │    │
│  │ - Programs           │      │ - Teachers Mgmt      │    │
│  └──────────────────────┘      └──────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      Backend API (不變)                      │
├─────────────────────────────────────────────────────────────┤
│  /api/teachers/dashboard        - 教師儀表板                │
│  /api/teachers/me/roles         - 角色查詢                  │
│  /api/organizations             - 組織 CRUD                 │
│  /api/schools                   - 學校 CRUD                 │
│  /api/organizations/:id/teachers - 人員管理                │
└─────────────────────────────────────────────────────────────┘
```

### Component Structure

```
frontend/src/
├── layouts/
│   ├── TeacherLayout.tsx          # 教師後台 Layout (已存在)
│   └── OrganizationLayout.tsx     # 組織管理 Layout (NEW)
│       ├── OrganizationSidebar.tsx   # 組織樹狀選單
│       └── OrganizationHeader.tsx    # 組織切換器
│
├── pages/
│   ├── teacher/                   # 教師後台頁面
│   │   ├── Dashboard.tsx          # 教學儀表板 (保留)
│   │   ├── ClassroomManagement.tsx
│   │   ├── StudentManagement.tsx
│   │   └── ProgramManagement.tsx
│   │
│   └── organization/              # 組織管理頁面 (NEW)
│       ├── Dashboard.tsx          # 組織儀表板 + 架構圖
│       ├── OrganizationList.tsx   # 組織列表（多組織時）
│       ├── OrganizationDetail.tsx # 組織詳情
│       ├── SchoolManagement.tsx   # 學校 CRUD (搬移)
│       └── TeacherManagement.tsx  # 人員管理 (搬移)
│
├── components/
│   └── organization/              # 組織相關元件 (NEW)
│       ├── OrganizationTree.tsx   # 組織架構樹
│       ├── SchoolCard.tsx         # 學校卡片
│       └── TeacherTable.tsx       # 教師列表
│
└── routes/
    ├── teacherRoutes.tsx          # /teacher/* 路由
    └── organizationRoutes.tsx     # /organization/* 路由 (NEW)
```

### Routing Logic

```typescript
// App.tsx
function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />

      {/* Teacher Portal - 所有教師可訪問 */}
      <Route path="/teacher" element={<TeacherLayout />}>
        <Route path="dashboard" element={<TeacherDashboard />} />
        <Route path="classrooms" element={<ClassroomManagement />} />
        {/* ... */}
      </Route>

      {/* Organization Portal - 僅組織角色可訪問 */}
      <Route
        path="/organization"
        element={
          <ProtectedRoute requiredRoles={['org_owner', 'org_admin', 'school_admin']}>
            <OrganizationLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<OrganizationDashboard />} />
        <Route path="list" element={<OrganizationList />} />
        <Route path=":id" element={<OrganizationDetail />} />
        <Route path=":id/schools" element={<SchoolManagement />} />
        <Route path=":id/teachers" element={<TeacherManagement />} />
      </Route>

      {/* Default redirect based on role */}
      <Route path="/" element={<RoleBasedRedirect />} />
    </Routes>
  );
}

// RoleBasedRedirect.tsx
function RoleBasedRedirect() {
  const { userRoles } = useTeacherAuthStore();

  const hasOrgRole = userRoles.some(r =>
    ['org_owner', 'org_admin', 'school_admin'].includes(r)
  );

  return <Navigate to={hasOrgRole ? '/organization/dashboard' : '/teacher/dashboard'} />;
}
```

### Data Flow

```typescript
// Organization Portal - 組織架構數據流

1. 載入組織列表
   GET /api/organizations
   → 返回用戶有權限的所有組織

2. 選擇組織後載入架構
   GET /api/organizations/:id
   GET /api/schools?organization_id=:id
   → 組合成樹狀結構

3. 點擊學校後載入人員
   GET /api/organizations/:org_id/teachers
   GET /api/schools/:school_id/teachers
   → 顯示教師列表

4. CRUD 操作
   POST/PATCH/DELETE /api/schools
   POST/DELETE /api/organizations/:id/teachers
```

---

## Acceptance Criteria

### AC1: 教師後台純淨化
- [ ] `/teacher/dashboard` 不顯示任何組織管理相關內容
- [ ] 左側選單完全沒有「組織管理」選項
- [ ] 普通教師訪問 `/organization/*` 被重定向到 `/teacher/dashboard`

### AC2: 組織管理後台完整性
- [ ] `/organization/dashboard` 顯示組織架構視覺化
- [ ] 左側 Sidebar 顯示組織樹狀結構
- [ ] 可展開/收合學校節點
- [ ] 點擊組織/學校後右側顯示對應的 CRUD 介面

### AC3: 權限控制正確
- [ ] `org_owner` 可訪問所有組織管理功能
- [ ] `org_admin` 可訪問指定組織的管理功能
- [ ] `school_admin` 可訪問指定學校的管理功能
- [ ] 普通 `teacher` 無法訪問組織管理後台

### AC4: 登入後自動導向
- [ ] 只有教學角色 → `/teacher/dashboard`
- [ ] 有組織管理角色 → `/organization/dashboard`
- [ ] 同時擁有兩種角色 → `/organization/dashboard`（優先組織管理）

### AC5: 現有功能不受影響
- [ ] 所有 API 端點保持不變
- [ ] 現有教學功能（班級、學生、作業）正常運作
- [ ] 訂閱管理功能正常運作

---

## Implementation Plan

### Phase 1: 路由和 Layout 基礎架構 (2-3 hours)
- [ ] 創建 `OrganizationLayout.tsx`
- [ ] 創建 `organizationRoutes.tsx`
- [ ] 實作 `ProtectedRoute` 權限檢查
- [ ] 實作 `RoleBasedRedirect` 自動導向
- [ ] 測試: 不同角色登入後導向正確頁面

### Phase 2: 組織架構視覺化 (3-4 hours)
- [ ] 創建 `OrganizationTree.tsx` 元件
  - [ ] 遞迴渲染組織 → 學校層級
  - [ ] 展開/收合功能
  - [ ] 選中狀態管理
- [ ] 創建 `OrganizationDashboard.tsx`
  - [ ] 左側: OrganizationTree
  - [ ] 右側: 根據選中節點顯示內容
- [ ] 測試: 組織架構正確顯示

### Phase 3: CRUD 功能搬遷 (2-3 hours)
- [ ] 搬移 `SchoolManagement.tsx` 到 `/organization/:id/schools`
- [ ] 搬移 `TeacherManagement.tsx` 到 `/organization/:id/teachers`
- [ ] 更新所有內部路由連結
- [ ] 測試: CRUD 操作正常（CREATE, READ, UPDATE, DELETE）

### Phase 4: 教師後台清理 (1-2 hours)
- [ ] 移除 `TeacherLayout` 中的組織管理選單項
- [ ] 移除 `TeacherDashboard` 中的組織相關統計
- [ ] 更新 `useSidebarRoles.ts` 邏輯
- [ ] 測試: 教師後台不顯示組織管理

### Phase 5: UI/UX 優化 (2-3 hours)
- [ ] 麵包屑導航
- [ ] 組織切換器（如有多個組織）
- [ ] 載入狀態優化
- [ ] 錯誤處理和提示訊息
- [ ] 測試: 使用者體驗流暢

### Phase 6: 整合測試 (1-2 hours)
- [ ] 測試所有角色的完整流程
- [ ] 測試權限邊界（無權限訪問被拒絕）
- [ ] 測試 CRUD 操作完整性
- [ ] 性能測試（首次載入 < 2s）

### Phase 7: Chrome UI 測試 (1 hour)
- [ ] Demo 教師 - 確認看不到組織管理
- [ ] Owner - 確認組織後台完整功能
- [ ] Org Admin - 確認權限正確
- [ ] School Admin - 確認只能管理學校
- [ ] 截圖記錄所有測試結果

---

## Risks & Mitigations

### Risk 1: 現有用戶習慣改變
**風險**: 用戶習慣在 `/teacher` 路由下管理組織
**影響**: 中等
**緩解**:
- 提供清楚的提示訊息
- 在教師後台放置「前往組織管理」按鈕（如有權限）
- 舊路由自動重定向到新路由

### Risk 2: 開發時間超出預期
**風險**: UI 元件複雜度高於預期
**影響**: 低
**緩解**:
- 使用現有 UI 元件庫（shadcn/ui）
- 先實作核心功能，再優化 UI

### Risk 3: 權限邏輯出錯
**風險**: 用戶能訪問不該訪問的頁面
**影響**: 高（安全風險）
**緩解**:
- 前端和後端雙重權限檢查
- 完整的 E2E 測試
- Code review 重點檢查權限邏輯

---

## Testing Strategy

### Unit Tests
- [ ] `RoleBasedRedirect` 導向邏輯
- [ ] `ProtectedRoute` 權限檢查
- [ ] `OrganizationTree` 展開/收合邏輯

### Integration Tests
- [ ] 登入後自動導向流程
- [ ] 組織架構數據載入
- [ ] CRUD 操作完整流程

### E2E Tests (Chrome)
- [ ] 7 個角色的完整流程測試
- [ ] 權限邊界測試（無權限訪問被拒絕）
- [ ] CRUD 操作視覺驗證

---

## Success Metrics

### 功能完整性
- ✅ 100% 的組織管理功能可在新後台訪問
- ✅ 0 個組織管理功能殘留在教師後台

### 權限正確性
- ✅ 100% 的權限測試通過
- ✅ 0 個安全漏洞

### 使用者體驗
- ✅ 登入後 < 2s 載入首頁
- ✅ 組織架構圖渲染 < 500ms
- ✅ 用戶滿意度 > 90%（無混淆訊息）

---

## Timeline

**總預估時間**: 12-17 小時

| Phase | 時間 | 完成日期 |
|-------|------|---------|
| Phase 1: 路由和 Layout | 2-3h | TBD |
| Phase 2: 組織架構視覺化 | 3-4h | TBD |
| Phase 3: CRUD 功能搬遷 | 2-3h | TBD |
| Phase 4: 教師後台清理 | 1-2h | TBD |
| Phase 5: UI/UX 優化 | 2-3h | TBD |
| Phase 6: 整合測試 | 1-2h | TBD |
| Phase 7: Chrome UI 測試 | 1h | TBD |

---

## Status

- [x] Planning
- [ ] Implementation
- [ ] Testing
- [ ] Completed

---

## Completion Notes

(待完成後填寫)

---

**Related Documents:**
- ORG_IMPLEMENTATION_SPEC.md - 組織層級系統規格
- issue-112-QA.md - QA 測試記錄
- CLAUDE.md - 專案配置

**Version**: 1.0
**Last Updated**: 2026-01-01
**Author**: Claude Code + Happy
