# Workspace Switcher Components

Teacher workspace switcher for dual-mode operation: Personal vs Organization.

## 元件結構

```
workspace/
├── WorkspaceSwitcher.tsx      # 主元件（Tabs 介面）
├── PersonalTab.tsx            # 個人工作區內容
├── OrganizationTab.tsx        # 機構工作區內容
├── SchoolList.tsx             # 機構+學校列表（Phase 1）
├── SchoolSwitcher.tsx         # 學校切換下拉選單（Phase 2）
├── PermissionBanner.tsx       # 權限限制橫幅
└── index.ts                   # 統一導出
```

## 使用方式

### 1. 安裝 Context Provider

在應用最上層包裹 `WorkspaceProvider`：

```tsx
import { WorkspaceProvider } from '@/contexts/WorkspaceContext';

<WorkspaceProvider teacherId={currentTeacher.id}>
  <App />
</WorkspaceProvider>
```

### 2. 在 Sidebar 中使用

```tsx
import { WorkspaceSwitcher } from '@/components/workspace';

function Sidebar() {
  return (
    <aside className="w-64 bg-white dark:bg-slate-900">
      {/* Workspace Switcher at top */}
      <WorkspaceSwitcher />

      {/* Rest of sidebar content... */}
    </aside>
  );
}
```

### 3. 使用 useWorkspace hook

```tsx
import { useWorkspace } from '@/contexts/WorkspaceContext';

function MyComponent() {
  const { mode, selectedSchool, selectSchool } = useWorkspace();

  if (mode === 'personal') {
    // Personal mode logic
  } else {
    // Organization mode logic
    // Check selectedSchool to determine context
  }
}
```

## 功能說明

### 個人模式（Personal Mode）
- 完整權限
- 管理自己的班級、學生、教材
- 無限制

### 機構模式（Organization Mode）

**Phase 1 - 選擇學校**：
- 顯示教師所屬的所有機構和學校
- 以機構為分組顯示學校列表
- 點擊學校進入 Phase 2

**Phase 2 - 學校工作區**：
- 顯示學校切換下拉選單（可快速切換學校）
- 顯示權限限制橫幅（可關閉，localStorage 記憶）
- 限制權限：
  - ✅ 可以：複製課程、派作業、改作業
  - ❌ 不能：管理班級、學生、教師關係

## 狀態管理

### WorkspaceContext

```typescript
interface WorkspaceContextState {
  mode: 'personal' | 'organization';
  organizations: Organization[];
  selectedOrganization: Organization | null;
  selectedSchool: School | null;
  loading: boolean;
  error: string | null;

  setMode: (mode) => void;
  selectSchool: (school, organization) => void;
  clearSelection: () => void;
  fetchOrganizations: () => Promise<void>;
}
```

### localStorage 持久化

- `workspace:mode` - 選擇的模式
- `workspace:organization` - 選擇的機構（JSON）
- `workspace:school` - 選擇的學校（JSON）
- `workspace:permission-banner-dismissed` - 橫幅是否已關閉

## API 整合

### GET /api/teachers/{teacher_id}/organizations

**Response**:
```json
{
  "organizations": [
    {
      "id": "uuid",
      "name": "Happy English School",
      "role": "org_admin",
      "schools": [
        {
          "id": "uuid",
          "name": "Nangang Branch",
          "roles": ["teacher"]
        }
      ]
    }
  ]
}
```

## 設計規範

- **Tab 高度**: 48px (h-12)
- **Active Tab**: `bg-white text-blue-600 border shadow-sm`
- **Inactive Tab**: `transparent text-slate-600 hover:bg-slate-200/50`
- **Transition**: 200ms ease-out
- **School item hover**: `bg-blue-50 text-blue-700`
- **School item active**: `bg-blue-100 border-l-3 border-blue-600`

## Accessibility

- ✅ Keyboard navigation (Tab, Arrow keys, Enter, Escape)
- ✅ Screen reader support (aria-live, role="status")
- ✅ Focus management (visible focus rings)
- ✅ Touch targets >= 44px

## 待辦事項

### 整合到現有 Sidebar
- [ ] 找到 TeacherDashboardWithSidebar 或其他 Sidebar 元件
- [ ] 在頂部加入 WorkspaceSwitcher
- [ ] 根據 mode 顯示對應的選單項目
- [ ] 在機構模式的選單項目加入唯讀標記（Eye icon）

### 鍵盤快捷鍵
- [ ] 實作 Cmd/Ctrl + 1 切換到個人模式
- [ ] 實作 Cmd/Ctrl + 2 切換到機構模式

### 額外功能
- [ ] Framer Motion 更流暢的轉場動畫（optional）
- [ ] Toast 通知（成功切換、錯誤提示）
- [ ] 無障礙測試（screen reader, keyboard only）

## 檔案結構

```
frontend/src/
├── contexts/
│   └── WorkspaceContext.tsx       # Context + Provider + Hook
├── components/
│   └── workspace/
│       ├── WorkspaceSwitcher.tsx  # 主元件
│       ├── PersonalTab.tsx        # 個人 Tab
│       ├── OrganizationTab.tsx    # 機構 Tab
│       ├── SchoolList.tsx         # 學校列表
│       ├── SchoolSwitcher.tsx     # 學校切換器
│       ├── PermissionBanner.tsx   # 權限橫幅
│       ├── index.ts               # 統一導出
│       └── README.md              # 本文件
```

## 相關文件

- 設計規範：`docs/plans/2026-01-26-teacher-workspace-switcher-design.md`
- 實作計畫：`docs/plans/2026-01-26-teacher-workspace-switcher-implementation.md`
- Backend API：`backend/routers/teachers/teacher_organizations.py`
- Backend Tests：`backend/tests/test_teacher_organizations.py`
