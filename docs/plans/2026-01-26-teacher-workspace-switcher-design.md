# Teacher Workspace Switcher - Design Specification

**Date**: 2026-01-26
**Feature**: 個人/機構工作區切換器
**Status**: Design Phase
**Designer**: UI Design Expert (Agent a6bad49)

---

## 1. Feature Overview

### Problem Statement
老師登入後需要清楚區分兩種工作模式：
- **個人模式**：管理自己的班級、學生、教材（完整權限）
- **機構學校模式**：作為某機構某學校的老師工作（限制權限）

目前兩種模式混在一起，介面不清楚，容易混淆。

### Solution
在 Sidebar 頂部新增 Tab 切換器，清楚分離「個人」和「機構」兩種工作環境。

---

## 2. User Flow

```
老師登入
    ↓
Sidebar 頂部顯示 [個人] [機構] 兩個 Tab
    ↓
┌─────────────────┬──────────────────────┐
│  [個人] Tab     │   [機構] Tab         │
├─────────────────┼──────────────────────┤
│ ├─ 我的班級     │ 階段 1: 機構+學校列表 │
│ ├─ 我的學生     │ ├─ 笑笑羊美語         │
│ └─ 我的教材     │ │  ├─ 南港分校      │
│                 │ │  └─ 信義分校      │
│                 │ └─ 快樂學習          │
│                 │    └─ 台北校區      │
│                 │                      │
│                 │ 階段 2: 選擇學校後    │
│                 │ ┌─────────────────┐ │
│                 │ │ [南港分校 ▼]    │ │
│                 │ └─────────────────┘ │
│                 │ ├─ 班級（唯讀）     │
│                 │ ├─ 學校公版教材     │
│                 │ └─ 作業管理         │
└─────────────────┴──────────────────────┘
```

---

## 3. Design Principles

### Clarity Over Cleverness
- 清楚的視覺層級區分個人/機構模式
- 隨時顯示目前的工作環境
- 權限限制明確呈現

### Contextual Awareness
- 始終顯示目前的工作區上下文
- 個人/機構模式視覺差異化
- 權限限制清楚溝通

### Seamless Transitions
- 流暢的切換動畫，不拖慢工作流程
- 切換時保留滾動位置
- 快速切換不重新載入頁面

### Progressive Disclosure
- 先顯示機構列表，選擇後才顯示學校選單
- 避免一次顯示太多學校造成混亂

---

## 4. Visual Specifications

### 4.1 Tab Switcher

**位置**: Sidebar 頂部

**尺寸**:
- 容器高度: `h-12` (48px)
- 下方間距: `mb-4` (16px)
- Grid: 2 欄平均分配

**顏色**:

**Inactive Tab**:
- Background: Transparent
- Text: `text-slate-600 dark:text-slate-400`
- Hover Background: `bg-slate-200/50 dark:bg-slate-700/50`

**Active Tab**:
- Background: `bg-white dark:bg-slate-700`
- Text: `text-blue-600 dark:text-blue-400`
- Border: `border border-slate-200 dark:border-slate-600`
- Shadow: `shadow-sm`

**Animation**:
- Duration: 200ms
- Easing: `ease-out`
- Scale on click: `scale-[0.98]`

---

### 4.2 Organization + School List (Phase 1)

**結構**: 機構作為標題，學校作為可點擊項目

**Organization Header**:
- Font: `text-xs font-semibold uppercase tracking-wide`
- Color: `text-slate-500 dark:text-slate-400`
- Padding: `px-3 py-1`

**School Item**:
- Padding: `px-3 py-2.5`
- Border radius: `rounded-md`
- Font: `text-sm`
- Gap: `gap-3` (icon 和文字間距)

**States**:

**Idle**:
- Background: Transparent
- Text: `text-slate-700 dark:text-slate-300`
- Icon: `text-slate-500 dark:text-slate-400`

**Hover**:
- Background: `bg-blue-50 dark:bg-blue-900/20`
- Text: `text-blue-700 dark:text-blue-300`
- Icon: `text-blue-600 dark:text-blue-400`
- Chevron 從右側滑入

**Active/Selected**:
- Background: `bg-blue-100 dark:bg-blue-900/40`
- Text: `text-blue-800 dark:text-blue-200`
- Border Left: `border-l-3 border-blue-600`

**Scrolling** (學校很多時):
- 使用 shadcn `ScrollArea`
- 最大高度: `h-[calc(100vh-280px)]`
- 滾動條: `scrollbar-thin scrollbar-thumb-slate-300`
- 底部淡出漸層提示更多內容

---

### 4.3 School Switcher Dropdown (Phase 2)

**位置**: 選擇學校後，顯示在機構 Tab 內容頂部

**Trigger 尺寸**:
- Height: `h-14` (56px)
- Padding: `px-3 py-2`
- Border: `border-2 border-blue-200 dark:border-blue-700`
- Border radius: `rounded-lg`

**Trigger 內容**:

**機構名稱**:
- Font: `text-xs uppercase tracking-wide`
- Color: `text-slate-500 dark:text-slate-400`

**學校名稱**:
- Font: `text-sm font-semibold`
- Color: `text-slate-900 dark:text-slate-100`

**Icon**:
- Size: `h-4 w-4`
- Color: `text-blue-600`

**Hover State**:
- Border: `border-blue-400 dark:border-blue-500`

**Focus State**:
- Ring: `ring-2 ring-blue-500 ring-offset-2`

**Dropdown Content**:
- Max height: `max-h-[300px]`
- Overflow: `overflow-y-auto`
- Shadow: `shadow-lg`
- Border: `border border-slate-200 dark:border-slate-600`

**Dropdown Items**:
- Padding: `py-2.5 px-3`
- Hover: `bg-blue-50 dark:bg-blue-900/20`
- Selected: `bg-blue-100 dark:bg-blue-900/40` + checkmark

---

### 4.4 Permission Restriction Banner

**位置**: School 選擇後，功能選單上方

**尺寸**:
- Margin: `mx-3 mb-4`
- Border Left: `border-l-4 border-amber-400`
- Background: `bg-amber-50 dark:bg-amber-900/20`

**內容**:

**Icon**:
- Type: `AlertCircle` (Lucide)
- Size: `h-4 w-4`
- Color: `text-amber-600 dark:text-amber-400`

**Title**:
- Text: "機構教師模式"
- Font: `text-sm font-medium`
- Color: `text-amber-800 dark:text-amber-300`

**Description**:
- Text: "可複製課程、派作業、改作業。無法管理班師生關係。"
- Font: `text-xs`
- Color: `text-amber-700 dark:text-amber-400`

**Dismissible**: 可關閉，使用 localStorage 記住偏好

---

### 4.5 Read-Only Menu Items

**視覺標記**:

**Icon**:
- Type: `Eye` (Lucide)
- Size: `h-3.5 w-3.5`
- Color: `text-slate-400 dark:text-slate-500`
- Position: Menu item 右側

**Tooltip**:
- Text: "唯讀權限"
- Trigger: Hover on Eye icon

**Disabled Buttons** (在頁面內容中):
- Opacity: `opacity-50`
- Cursor: `cursor-not-allowed`
- Icon: `Lock` (Lucide) `h-4 w-4`
- Toast on click: "機構教師無此權限"

---

## 5. Animation Timings

| Interaction | Duration | Easing |
|-------------|----------|--------|
| Tab 切換 | 200ms | ease-out |
| Dropdown 開關 | 150ms | ease-in-out |
| Hover 效果 | 150ms | linear |
| 學校上下文切換 | 250ms | ease-out |
| List item hover | 100ms | linear |

---

## 6. Accessibility

### Keyboard Navigation
- `Tab`: 在 tab triggers 之間移動
- `Arrow Keys`: 在列表內導航
- `Enter/Space`: 啟動選擇
- `Escape`: 關閉 dropdown

### Screen Reader
```tsx
<div role="status" aria-live="polite" className="sr-only">
  {selectedSchool ? `已切換至 ${selectedSchool.name}` : ''}
</div>
```

### Focus Management
- Dropdown 開啟時 trap focus
- 選擇後 focus 返回 trigger
- 可見的 focus ring: `ring-2 ring-blue-500`

### Mobile Optimization
- Tabs 在小螢幕堆疊
- 學校列表使用全寬
- 觸控目標最小 44px 高度
- 使用 bottom sheet 取代 dropdown（mobile）

---

## 7. Component Structure

```tsx
WorkspaceSwitcher/
├── index.tsx                 // Main component
├── PersonalTab.tsx          // 個人 Tab 內容
├── OrganizationTab.tsx      // 機構 Tab 內容
├── SchoolList.tsx           // 機構+學校列表 (Phase 1)
├── SchoolSwitcher.tsx       // 學校切換器 (Phase 2)
├── PermissionBanner.tsx     // 權限限制橫幅
└── types.ts                 // TypeScript types
```

---

## 8. Data Structure

```typescript
interface Organization {
  id: string;
  name: string;
  schools: School[];
}

interface School {
  id: string;
  name: string;
  organizationId: string;
}

interface WorkspaceContext {
  mode: 'personal' | 'organization';
  selectedOrganization?: Organization;
  selectedSchool?: School;
}

interface TeacherPermissions {
  canManageClasses: boolean;      // false in org mode
  canManageStudents: boolean;     // false in org mode
  canCopyMaterials: boolean;      // true
  canAssignHomework: boolean;     // true
  canGradeHomework: boolean;      // true
}
```

---

## 9. Implementation Checklist

### Phase 1: Basic Structure
- [ ] Create `WorkspaceSwitcher` component
- [ ] Implement Tabs with personal/organization modes
- [ ] Build `SchoolList` component (organization + school list)
- [ ] Add `ScrollArea` for long lists
- [ ] Implement school selection logic

### Phase 2: School Selection
- [ ] Create `SchoolSwitcher` dropdown component
- [ ] Add `PermissionBanner` component
- [ ] Implement read-only indicators on menu items
- [ ] Build menu items with permission-based restrictions

### Phase 3: State Management
- [ ] Create `useWorkspaceContext` hook
- [ ] Implement context switching logic
- [ ] Persist selected school in localStorage
- [ ] Handle re-render on school change

### Phase 4: Polish
- [ ] Add smooth transitions (Framer Motion)
- [ ] Implement keyboard navigation
- [ ] Add tooltips for restricted items
- [ ] Test dark mode variants
- [ ] Add loading states

### Phase 5: Testing
- [ ] Test with 1 org, 1 school
- [ ] Test with 5+ orgs, 20+ schools
- [ ] Test permission banners show correctly
- [ ] Mobile responsive testing
- [ ] Screen reader testing
- [ ] Keyboard navigation testing

---

## 10. Integration Points

### Backend API Requirements

**GET /api/teachers/organizations**
```typescript
Response: {
  organizations: Array<{
    id: string;
    name: string;
    role: 'org_owner' | 'org_admin' | 'teacher';
    schools: Array<{
      id: string;
      name: string;
      role?: 'school_admin' | 'school_director' | 'teacher';
    }>;
  }>;
}
```

**Permissions Check**
- Frontend queries current permissions based on `WorkspaceContext`
- Backend enforces permissions on API endpoints
- Consistent permission logic between frontend (UI) and backend (enforcement)

---

## 11. Success Metrics

**User Experience**:
- [ ] 老師能在 < 2 秒內切換工作環境
- [ ] 0 confusion about current context (從用戶測試確認)
- [ ] 100% 權限限制清楚呈現（不會嘗試執行無權限操作）

**Technical**:
- [ ] < 100ms 切換延遲
- [ ] 0 full page reloads on context switch
- [ ] Lighthouse Accessibility score > 95

---

## 12. Future Enhancements

**Phase 2+ Features** (Not in initial scope):
- Multiple school selection (split screen)
- Recent workspaces quick access
- Workspace search/filter (for 20+ schools)
- Custom workspace names/colors
- Workspace-specific notifications

---

## 13. Design Decisions & Rationale

### Why Tab-based switching?
- **Clarity**: 清楚的視覺層級，立即知道目前模式
- **Familiarity**: 類似 Notion、Slack 等工具的 workspace 切換
- **Performance**: 不需要重新載入頁面
- **Accessibility**: 符合 WAI-ARIA tabs pattern

### Why two-phase organization list?
- **Progressive Disclosure**: 避免一次顯示太多資訊
- **Visual Hierarchy**: 機構 → 學校的清楚層級
- **Scalability**: 支援多機構多學校場景

### Why permission banner?
- **Transparency**: 明確告知目前權限限制
- **Error Prevention**: 減少嘗試無權限操作的次數
- **User Education**: 幫助理解個人/機構模式的差異

---

**Next Steps**:
1. Review this design with stakeholders
2. Create implementation plan (using `writing-plans` skill)
3. Set up git worktree for isolated development
4. Begin Phase 1 implementation

**Reference Implementation**: See `agent-ui-design-expert` output for complete code examples
