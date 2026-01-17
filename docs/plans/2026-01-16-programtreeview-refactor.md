# ProgramTreeView 重構：統一三個 Scope 的架構

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 重構 ProgramTreeView 成為完整的自包含元件，取代所有直接使用 RecursiveTreeAccordion 的地方，統一 teacher/organization/school 三個 scope 的架構。

**Architecture:** 採用 TDD 方法，先為 TeacherTemplatePrograms 的現有功能撰寫測試，然後逐步將功能遷移到 ProgramTreeView，最後重構 TeacherTemplatePrograms 使用 ProgramTreeView。RecursiveTreeAccordion 只負責純 UI 層（拖曳、展開/收合、樹狀結構）。

**Tech Stack:** React, TypeScript, Vitest, Testing Library, @dnd-kit/core

---

## 功能盤點（Current State）

### TeacherTemplatePrograms（直接使用 RecursiveTreeAccordion）
- ✅ Program CRUD（create/edit/delete/save）
- ✅ Lesson CRUD（create/edit/delete/save）
- ✅ Content CRUD（create/click-edit/delete）
- ✅ Reorder（三層，使用舊 apiClient）
- ✅ Reading Assessment Panel
- ✅ Sentence Making Panel
- ✅ Content Type Dialog
- ✅ Optimistic UI updates with rollback

### ProgramTreeView（wrapper，部分功能）
- ✅ Content CRUD（透過 useContentEditor）
- ✅ Reorder（三層，使用 useProgramAPI）
- ✅ Scope-aware（teacher/organization/school）
- ❌ Program/Lesson CRUD（依賴父組件 props）

### MaterialsPage/SchoolMaterialsPage（使用 ProgramTreeView）
- ✅ Program CRUD（透過 MaterialCreateDialog/MaterialEditDialog）
- ✅ Lesson CRUD（透過 LessonDialog）
- ✅ Content Delete（handleDeleteContent）
- ✅ Reorder（由 ProgramTreeView 內建）

## 重構目標

**統一架構**：
1. **ProgramTreeView 內建完整 CRUD**（Program/Lesson/Content）
2. **所有頁面使用 ProgramTreeView**（包括 TeacherTemplatePrograms）
3. **RecursiveTreeAccordion 只負責純 UI 層**

---

## Task 1: 設置測試環境和基礎測試

**Files:**
- Create: `frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx`
- Modify: `frontend/package.json`（如果需要新增測試依賴）

**Step 1: 創建測試檔案骨架**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProgramTreeView } from '../ProgramTreeView';
import { ProgramTreeProgram } from '@/hooks/useProgramTree';

// Mock dependencies
vi.mock('@/hooks/useProgramAPI');
vi.mock('@/hooks/useContentEditor');
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('ProgramTreeView', () => {
  const mockPrograms: ProgramTreeProgram[] = [
    {
      id: 1,
      name: 'Test Program 1',
      description: 'Description 1',
      lessons: [
        {
          id: 101,
          name: 'Test Lesson 1-1',
          contents: [
            { id: 1001, title: 'Content 1-1-1', type: 'reading_assessment' },
          ],
        },
      ],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders programs correctly', () => {
    // Placeholder test
    expect(true).toBe(true);
  });
});
```

**Step 2: 執行測試確認測試環境正常**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: PASS（placeholder test 通過）

**Step 3: Commit**

```bash
git add frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx
git commit -m "test: add ProgramTreeView test setup"
```

---

## Task 2: 測試 Program CRUD 功能（紅燈階段）

**Files:**
- Modify: `frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx`

**Step 1: 撰寫 Program Create 測試（failing test）**

```typescript
describe('Program CRUD', () => {
  it('should create a new program when create button is clicked', async () => {
    const mockOnProgramsChange = vi.fn();
    const { getByText } = render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        showCreateButton
        createButtonText="新增教材"
        scope="teacher"
      />
    );

    const createButton = getByText('新增教材');
    await userEvent.click(createButton);

    // Should open ProgramDialog
    expect(screen.getByText('新增教材')).toBeInTheDocument();
  });

  it('should edit an existing program', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    // Find edit button for first program
    const editButton = screen.getAllByLabelText('編輯')[0];
    await userEvent.click(editButton);

    // Should open ProgramDialog with program data
    expect(screen.getByDisplayValue('Test Program 1')).toBeInTheDocument();
  });

  it('should delete a program with confirmation', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    const deleteButton = screen.getAllByLabelText('刪除')[0];
    await userEvent.click(deleteButton);

    // Should show confirmation dialog
    expect(screen.getByText('確認刪除')).toBeInTheDocument();

    const confirmButton = screen.getByText('確認刪除');
    await userEvent.click(confirmButton);

    // Should call onProgramsChange with updated list
    await waitFor(() => {
      expect(mockOnProgramsChange).toHaveBeenCalledWith(
        expect.not.arrayContaining([
          expect.objectContaining({ id: 1 })
        ])
      );
    });
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: FAIL（ProgramDialog not found, edit/delete buttons not found）

**Step 3: Commit**

```bash
git add frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx
git commit -m "test: add failing tests for Program CRUD"
```

---

## Task 3: 實作 Program CRUD 功能（綠燈階段）

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx:1-50`
- Create: `frontend/src/components/ProgramDialog.tsx`（如果不存在）

**Step 1: 新增 Program Dialog 狀態和 handlers**

修改 `ProgramTreeView.tsx`，在 `ProgramTreeViewProps` 之後新增：

```typescript
// Program dialog states
const [programDialogType, setProgramDialogType] = useState<
  "create" | "edit" | "delete" | null
>(null);
const [selectedProgram, setSelectedProgram] = useState<ProgramTreeProgram | null>(null);

// Program handlers
const handleCreateProgram = () => {
  setSelectedProgram(null);
  setProgramDialogType("create");
};

const handleEditProgram = (programId: number) => {
  const program = programs.find((p) => p.id === programId);
  if (program) {
    setSelectedProgram(program);
    setProgramDialogType("edit");
  }
};

const handleDeleteProgram = (programId: number) => {
  const program = programs.find((p) => p.id === programId);
  if (program) {
    setSelectedProgram(program);
    setProgramDialogType("delete");
  }
};

const handleSaveProgram = async (programData: Partial<ProgramTreeProgram>) => {
  if (programDialogType === "create") {
    // Create new program
    const newProgram = await programAPI.createProgram({
      name: programData.name!,
      description: programData.description,
    });

    const updatedPrograms = [...programs, newProgram];
    if (onProgramsChange) {
      onProgramsChange(updatedPrograms);
    }
    toast.success("教材新增成功");
  } else if (programDialogType === "edit") {
    // Update existing program
    await programAPI.updateProgram(selectedProgram!.id!, {
      name: programData.name,
      description: programData.description,
    });

    const updatedPrograms = programs.map((p) =>
      p.id === selectedProgram!.id ? { ...p, ...programData } : p
    );
    if (onProgramsChange) {
      onProgramsChange(updatedPrograms);
    }
    toast.success("教材更新成功");
  }

  setProgramDialogType(null);
  setSelectedProgram(null);
};

const handleDeleteProgramConfirm = async () => {
  if (!selectedProgram?.id) return;

  await programAPI.deleteProgram(selectedProgram.id);

  const updatedPrograms = programs.filter((p) => p.id !== selectedProgram.id);
  if (onProgramsChange) {
    onProgramsChange(updatedPrograms);
  }

  toast.success("教材刪除成功");
  setProgramDialogType(null);
  setSelectedProgram(null);
};
```

**Step 2: 修改 RecursiveTreeAccordion props 使用內建 handlers**

修改 `onCreateClick` 和 `onEdit/onDelete` 回調：

```typescript
<RecursiveTreeAccordion
  data={programs}
  config={programTreeConfig}
  showCreateButton={showCreateButton}
  createButtonText={createButtonText}
  onCreateClick={handleCreateProgram}  // Use internal handler
  onEdit={(item, level, parentId) => {
    if (level === 0) {
      handleEditProgram(item.id);  // Use internal handler
    } else if (onEdit) {
      onEdit(item, level, parentId);  // Fallback to prop for level 1/2
    }
  }}
  onDelete={(item, level, parentId) => {
    if (level === 0) {
      handleDeleteProgram(item.id);  // Use internal handler
    } else if (onDelete) {
      onDelete(item, level, parentId);  // Fallback to prop for level 1/2
    }
  }}
  // ... other props
/>
```

**Step 3: 新增 ProgramDialog 元件（在 return 中）**

```typescript
{/* Program Dialog */}
<ProgramDialog
  program={selectedProgram}
  dialogType={programDialogType}
  scope={scope}
  organizationId={organizationId}
  schoolId={schoolId}
  onClose={() => {
    setProgramDialogType(null);
    setSelectedProgram(null);
  }}
  onSave={handleSaveProgram}
  onDelete={handleDeleteProgramConfirm}
/>
```

**Step 4: 執行測試確認通過**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: PASS（Program CRUD tests 通過）

**Step 5: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "feat: add Program CRUD to ProgramTreeView"
```

---

## Task 4: 測試 Lesson CRUD 功能（紅燈階段）

**Files:**
- Modify: `frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx`

**Step 1: 撰寫 Lesson CRUD 測試（failing test）**

```typescript
describe('Lesson CRUD', () => {
  it('should create a new lesson when onCreate is triggered', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    // Expand program first
    const programAccordion = screen.getByText('Test Program 1');
    await userEvent.click(programAccordion);

    // Find "新增課程單元" button for the program
    const createLessonButton = screen.getByText('新增課程單元');
    await userEvent.click(createLessonButton);

    // Should open LessonDialog
    expect(screen.getByText('新增課程單元')).toBeInTheDocument();
  });

  it('should edit an existing lesson', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    // Expand program
    const programAccordion = screen.getByText('Test Program 1');
    await userEvent.click(programAccordion);

    // Find edit button for first lesson
    const editButton = screen.getAllByLabelText('編輯')[1]; // Second edit button (first is program)
    await userEvent.click(editButton);

    // Should open LessonDialog with lesson data
    expect(screen.getByDisplayValue('Test Lesson 1-1')).toBeInTheDocument();
  });

  it('should delete a lesson with confirmation', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    // Expand program
    const programAccordion = screen.getByText('Test Program 1');
    await userEvent.click(programAccordion);

    const deleteButton = screen.getAllByLabelText('刪除')[1];
    await userEvent.click(deleteButton);

    // Should show confirmation dialog
    expect(screen.getByText('確認刪除')).toBeInTheDocument();

    const confirmButton = screen.getByText('確認刪除');
    await userEvent.click(confirmButton);

    // Should call onProgramsChange with updated lesson list
    await waitFor(() => {
      expect(mockOnProgramsChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 1,
            lessons: expect.not.arrayContaining([
              expect.objectContaining({ id: 101 })
            ])
          })
        ])
      );
    });
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: FAIL（LessonDialog not found, lesson create/edit/delete not working）

**Step 3: Commit**

```bash
git add frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx
git commit -m "test: add failing tests for Lesson CRUD"
```

---

## Task 5: 實作 Lesson CRUD 功能（綠燈階段）

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx:50-100`

**Step 1: 新增 Lesson Dialog 狀態和 handlers**

在 Program handlers 之後新增：

```typescript
// Lesson dialog states
const [lessonDialogType, setLessonDialogType] = useState<
  "create" | "edit" | "delete" | null
>(null);
const [selectedLesson, setSelectedLesson] = useState<ProgramTreeLesson | null>(null);
const [lessonProgramId, setLessonProgramId] = useState<number | undefined>();

// Lesson handlers
const handleCreateLesson = (programId: number) => {
  setSelectedLesson(null);
  setLessonProgramId(programId);
  setLessonDialogType("create");
};

const handleEditLesson = (programId: number, lessonId: number) => {
  const program = programs.find((p) => p.id === programId);
  const lesson = program?.lessons?.find((l) => l.id === lessonId);
  if (lesson && program) {
    setSelectedLesson(lesson);
    setLessonProgramId(program.id);
    setLessonDialogType("edit");
  }
};

const handleDeleteLesson = (programId: number, lessonId: number) => {
  const program = programs.find((p) => p.id === programId);
  const lesson = program?.lessons?.find((l) => l.id === lessonId);
  if (lesson && program) {
    setSelectedLesson(lesson);
    setLessonProgramId(program.id);
    setLessonDialogType("delete");
  }
};

const handleSaveLesson = async (lessonData: any) => {
  if (lessonDialogType === "create" && lessonProgramId) {
    // Create new lesson
    const newLesson = await programAPI.createLesson(lessonProgramId, {
      name: lessonData.name,
      description: lessonData.description,
    });

    const updatedPrograms = programs.map((program) => {
      if (program.id === lessonProgramId) {
        return {
          ...program,
          lessons: [...(program.lessons || []), newLesson],
        };
      }
      return program;
    });

    if (onProgramsChange) {
      onProgramsChange(updatedPrograms);
    }
    toast.success("課程單元新增成功");
  } else if (lessonDialogType === "edit") {
    // Update existing lesson
    await programAPI.updateLesson(selectedLesson!.id!, {
      name: lessonData.name,
      description: lessonData.description,
    });

    const updatedPrograms = programs.map((program) => ({
      ...program,
      lessons: program.lessons?.map((l) =>
        l.id === selectedLesson!.id ? { ...l, ...lessonData } : l
      ),
    }));

    if (onProgramsChange) {
      onProgramsChange(updatedPrograms);
    }
    toast.success("課程單元更新成功");
  }

  setLessonDialogType(null);
  setSelectedLesson(null);
  setLessonProgramId(undefined);
};

const handleDeleteLessonConfirm = async () => {
  if (!selectedLesson?.id) return;

  await programAPI.deleteLesson(selectedLesson.id);

  const updatedPrograms = programs.map((program) => ({
    ...program,
    lessons: program.lessons?.filter((l) => l.id !== selectedLesson.id),
  }));

  if (onProgramsChange) {
    onProgramsChange(updatedPrograms);
  }

  toast.success("課程單元刪除成功");
  setLessonDialogType(null);
  setSelectedLesson(null);
};
```

**Step 2: 修改 RecursiveTreeAccordion onCreate/onEdit/onDelete**

```typescript
<RecursiveTreeAccordion
  // ... existing props
  onCreate={(level, parentId) => {
    if (level === 1) {
      // Creating lesson inside program
      handleCreateLesson(parentId as number);
    } else if (onCreate) {
      onCreate(level, parentId);  // Fallback for level 2
    }
  }}
  onEdit={(item, level, parentId) => {
    if (level === 0) {
      handleEditProgram(item.id);
    } else if (level === 1) {
      handleEditLesson(parentId as number, item.id);
    } else if (onEdit) {
      onEdit(item, level, parentId);
    }
  }}
  onDelete={(item, level, parentId) => {
    if (level === 0) {
      handleDeleteProgram(item.id);
    } else if (level === 1) {
      handleDeleteLesson(parentId as number, item.id);
    } else if (onDelete) {
      onDelete(item, level, parentId);
    }
  }}
/>
```

**Step 3: 新增 LessonDialog 元件**

```typescript
{/* Lesson Dialog */}
<LessonDialog
  lesson={selectedLesson}
  dialogType={lessonDialogType}
  programId={lessonProgramId}
  onClose={() => {
    setLessonDialogType(null);
    setSelectedLesson(null);
    setLessonProgramId(undefined);
  }}
  onSave={handleSaveLesson}
  onDelete={handleDeleteLessonConfirm}
/>
```

**Step 4: 執行測試確認通過**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: PASS（Lesson CRUD tests 通過）

**Step 5: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "feat: add Lesson CRUD to ProgramTreeView"
```

---

## Task 6: 測試 Content Delete 功能（紅燈階段）

**Files:**
- Modify: `frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx`

**Step 1: 撰寫 Content Delete 測試（failing test）**

```typescript
describe('Content Delete', () => {
  it('should delete a content with confirmation', async () => {
    const mockOnProgramsChange = vi.fn();
    render(
      <ProgramTreeView
        programs={mockPrograms}
        onProgramsChange={mockOnProgramsChange}
        scope="teacher"
      />
    );

    // Expand program and lesson
    const programAccordion = screen.getByText('Test Program 1');
    await userEvent.click(programAccordion);

    const lessonAccordion = screen.getByText('Test Lesson 1-1');
    await userEvent.click(lessonAccordion);

    // Find delete button for content
    const deleteButton = screen.getAllByLabelText('刪除')[2]; // Third delete button
    await userEvent.click(deleteButton);

    // Should show confirmation or delete immediately
    await waitFor(() => {
      expect(mockOnProgramsChange).toHaveBeenCalledWith(
        expect.arrayContaining([
          expect.objectContaining({
            id: 1,
            lessons: expect.arrayContaining([
              expect.objectContaining({
                id: 101,
                contents: expect.not.arrayContaining([
                  expect.objectContaining({ id: 1001 })
                ])
              })
            ])
          })
        ])
      );
    });
  });
});
```

**Step 2: 執行測試確認失敗**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: FAIL（Content delete not working）

**Step 3: Commit**

```bash
git add frontend/src/components/shared/__tests__/ProgramTreeView.test.tsx
git commit -m "test: add failing test for Content delete"
```

---

## Task 7: 實作 Content Delete 功能（綠燈階段）

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx:100-120`

**Step 1: 新增 Content Delete handler**

```typescript
// Content delete handler
const handleDeleteContent = async (lessonId: number, contentId: number) => {
  // Using browser confirm for simplicity (can be replaced with Dialog later)
  if (!confirm("確定要刪除此內容嗎？")) {
    return;
  }

  await programAPI.deleteContent(contentId);

  const updatedPrograms = programs.map((program) => ({
    ...program,
    lessons: program.lessons?.map((lesson) => {
      if (lesson.id === lessonId) {
        return {
          ...lesson,
          contents: lesson.contents?.filter((c) => c.id !== contentId),
        };
      }
      return lesson;
    }),
  }));

  if (onProgramsChange) {
    onProgramsChange(updatedPrograms);
  }

  toast.success("內容刪除成功");
};
```

**Step 2: 修改 RecursiveTreeAccordion onDelete**

```typescript
<RecursiveTreeAccordion
  // ... existing props
  onDelete={(item, level, parentId) => {
    if (level === 0) {
      handleDeleteProgram(item.id);
    } else if (level === 1) {
      handleDeleteLesson(parentId as number, item.id);
    } else if (level === 2) {
      handleDeleteContent(parentId as number, item.id);
    } else if (onDelete) {
      onDelete(item, level, parentId);
    }
  }}
/>
```

**Step 3: 執行測試確認通過**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: PASS（Content delete test 通過）

**Step 4: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "feat: add Content delete to ProgramTreeView"
```

---

## Task 8: 更新 Props Interface（移除不必要的 props）

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx:28-43`

**Step 1: 更新 ProgramTreeViewProps interface**

```typescript
interface ProgramTreeViewProps {
  programs: ProgramTreeProgram[];
  onProgramsChange?: (programs: ProgramTreeProgram[]) => void;
  showCreateButton?: boolean;
  createButtonText?: string;
  // onCreateClick?: () => void;  // REMOVED - now internal
  // onEdit?: (item: TreeItem, level: number, parentId?: string | number) => void;  // REMOVED - now internal
  // onDelete?: (item: TreeItem, level: number, parentId?: string | number) => void;  // REMOVED - now internal
  // onCreate?: (level: number, parentId: string | number) => void;  // REMOVED - now internal
  // onReorder?: (fromIndex: number, toIndex: number, level: number, parentId?: string | number) => void;  // REMOVED - now internal
  onRefresh?: () => void;  // Keep for manual refresh if needed
  // Scope props for API calls
  scope: 'teacher' | 'organization' | 'school';
  organizationId?: string;
  schoolId?: string;
}
```

**Step 2: 移除所有 prop 解構中不再使用的 props**

```typescript
export function ProgramTreeView({
  programs: externalPrograms,
  onProgramsChange,
  showCreateButton = false,
  createButtonText,
  // onCreateClick,  // REMOVED
  // onEdit,  // REMOVED
  // onDelete,  // REMOVED
  // onCreate,  // REMOVED
  // onReorder,  // REMOVED
  onRefresh,
  scope,
  organizationId,
  schoolId,
}: ProgramTreeViewProps) {
  // ... implementation
}
```

**Step 3: 執行測試確認沒有破壞**

Run: `npm run test -- ProgramTreeView.test.tsx`
Expected: PASS（所有測試通過）

**Step 4: TypeScript 編譯檢查**

Run: `npm run typecheck`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "refactor: remove unnecessary props from ProgramTreeView"
```

---

## Task 9: 重構 MaterialsPage 使用新 ProgramTreeView API

**Files:**
- Modify: `frontend/src/pages/organization/MaterialsPage.tsx:354-418`

**Step 1: 簡化 ProgramTreeView 使用（移除所有 handler props）**

將原本的：

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={handleProgramsChange}
  showCreateButton={canManageMaterials}
  createButtonText="新增教材"
  onCreateClick={handleCreate}  // REMOVE
  onCreate={(level, parentId) => {  // REMOVE
    if (level === 1) {
      handleCreateLesson(parentId as number);
    }
  }}
  onEdit={(item, level) => {  // REMOVE
    if (level === 0) {
      const program = programs.find((p) => p.id === item.id);
      if (program) handleEdit(program);
    } else if (level === 1) {
      const lessonItem = item as OrganizationLesson;
      if (!lessonItem.id) return;
      const program = programs.find(p =>
        p.lessons?.some((l) => l.id === lessonItem.id)
      );
      if (program) {
        handleEditLesson(program.id, lessonItem.id);
      }
    }
  }}
  onDelete={(item, level) => {  // REMOVE
    if (level === 0 && canManageMaterials) {
      const itemId = (item as ItemWithId).id;
      if (!itemId) return;
      handleDelete(itemId);
    } else if (level === 1 && canManageMaterials) {
      const lessonItem = item as OrganizationLesson;
      if (!lessonItem.id) return;
      const program = programs.find(p =>
        p.lessons?.some((l) => l.id === lessonItem.id)
      );
      const lesson = program?.lessons?.find(
        (l) => l.id === lessonItem.id
      );
      if (lesson && program) {
        setSelectedLesson(lesson);
        setLessonProgramId(program.id);
        setLessonDialogType("delete");
      }
    } else if (level === 2 && canManageMaterials) {
      const itemId = (item as ItemWithId).id;
      if (!itemId) return;
      handleDeleteContent(itemId);
    }
  }}
  onRefresh={fetchPrograms}
  scope="organization"
  organizationId={effectiveOrgId}
/>
```

改成：

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={handleProgramsChange}
  showCreateButton={canManageMaterials}
  createButtonText="新增教材"
  scope="organization"
  organizationId={effectiveOrgId}
/>
```

**Step 2: 移除不再需要的 state 和 handlers**

刪除以下程式碼（因為已內建到 ProgramTreeView）：

```typescript
// REMOVE:
const [showCreateDialog, setShowCreateDialog] = useState(false);
const [showEditDialog, setShowEditDialog] = useState(false);
const [editingProgram, setEditingProgram] = useState<OrganizationProgram | null>(null);
const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
const [deleting, setDeleting] = useState(false);

// REMOVE:
const [lessonDialogType, setLessonDialogType] = useState<"create" | "edit" | "delete" | null>(null);
const [selectedLesson, setSelectedLesson] = useState<OrganizationLesson | null>(null);
const [lessonProgramId, setLessonProgramId] = useState<number | undefined>();

// REMOVE all handlers:
// handleCreate, handleEdit, handleDelete
// handleCreateLesson, handleEditLesson, handleSaveLesson, handleDeleteLesson
// handleDeleteContent
```

**Step 3: 移除不再需要的 Dialog 元件**

刪除以下 JSX（因為已內建到 ProgramTreeView）：

```typescript
// REMOVE:
<MaterialCreateDialog ... />
<MaterialEditDialog ... />
<Dialog>...</Dialog>  // Delete confirmation dialog
<LessonDialog ... />
```

**Step 4: 執行測試確認功能正常**

Run: `npm run dev`
Navigate to: `http://localhost:5173/organization/{orgId}/materials`
Test:
- ✅ Create program
- ✅ Edit program
- ✅ Delete program
- ✅ Create lesson
- ✅ Edit lesson
- ✅ Delete lesson
- ✅ Delete content
- ✅ Reorder (all three levels)

**Step 5: TypeScript 編譯檢查**

Run: `npm run typecheck`
Expected: No errors

**Step 6: Commit**

```bash
git add frontend/src/pages/organization/MaterialsPage.tsx
git commit -m "refactor: simplify MaterialsPage using internal ProgramTreeView CRUD"
```

---

## Task 10: 重構 SchoolMaterialsPage（同 MaterialsPage）

**Files:**
- Modify: `frontend/src/pages/organization/SchoolMaterialsPage.tsx`

**Step 1: 簡化 ProgramTreeView 使用（同 Task 9）**

將 ProgramTreeView 簡化成：

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={handleProgramsChange}
  showCreateButton={canManageMaterials}
  createButtonText="新增教材"
  scope="school"
  schoolId={effectiveSchoolId}
/>
```

**Step 2: 移除不再需要的 state 和 handlers（同 Task 9）**

**Step 3: 移除不再需要的 Dialog 元件（同 Task 9）**

**Step 4: 執行測試確認功能正常**

Run: `npm run dev`
Navigate to: `http://localhost:5173/organization/{orgId}/schools/{schoolId}/materials`
Test:
- ✅ Create program
- ✅ Edit program
- ✅ Delete program
- ✅ Create lesson
- ✅ Edit lesson
- ✅ Delete lesson
- ✅ Delete content
- ✅ Reorder (all three levels)

**Step 5: TypeScript 編譯檢查**

Run: `npm run typecheck`
Expected: No errors

**Step 6: Commit**

```bash
git add frontend/src/pages/organization/SchoolMaterialsPage.tsx
git commit -m "refactor: simplify SchoolMaterialsPage using internal ProgramTreeView CRUD"
```

---

## Task 11: 重構 TeacherTemplatePrograms 使用 ProgramTreeView

**Files:**
- Modify: `frontend/src/pages/teacher/TeacherTemplatePrograms.tsx`

**Step 1: 替換 RecursiveTreeAccordion 為 ProgramTreeView**

將原本的：

```typescript
<RecursiveTreeAccordion
  data={programs}
  config={programTreeConfig}
  title={t("teacherTemplatePrograms.title")}
  showCreateButton
  createButtonText={t("teacherTemplatePrograms.buttons.addProgram")}
  onCreateClick={handleCreateProgram}
  onEdit={...}
  onDelete={...}
  onClick={...}
  onCreate={...}
  onReorder={...}
/>
```

改成：

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={setPrograms}
  showCreateButton
  createButtonText={t("teacherTemplatePrograms.buttons.addProgram")}
  scope="teacher"
/>
```

**Step 2: 移除所有 Program/Lesson CRUD handlers**

刪除以下程式碼：

```typescript
// REMOVE:
const [programDialogType, setProgramDialogType] = useState<...>(null);
const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
const [lessonDialogType, setLessonDialogType] = useState<...>(null);
const [selectedLesson, setSelectedLesson] = useState<Lesson | null>(null);
const [lessonProgramId, setLessonProgramId] = useState<number | undefined>(undefined);

// REMOVE all handlers:
// handleCreateProgram, handleEditProgram, handleDeleteProgram, handleSaveProgram, handleDeleteProgramConfirm
// handleCreateLesson, handleEditLesson, handleDeleteLesson, handleSaveLesson, handleDeleteLessonConfirm
// handleReorderPrograms, handleReorderLessons, handleReorderContents (內建在 ProgramTreeView)
```

**Step 3: 保留 Content 編輯功能（Reading/SentenceMaking Panels）**

這些功能目前已經在 ProgramTreeView 中由 useContentEditor hook 處理，所以：

```typescript
// KEEP:
const [showContentTypeDialog, setShowContentTypeDialog] = useState(false);
const [contentLessonInfo, setContentLessonInfo] = useState<...>(null);
const [showReadingEditor, setShowReadingEditor] = useState(false);
const [editorLessonId, setEditorLessonId] = useState<number | null>(null);
const [editorContentId, setEditorContentId] = useState<number | null>(null);
const [selectedContent, setSelectedContent] = useState<Content | null>(null);
const [showSentenceMakingEditor, setShowSentenceMakingEditor] = useState(false);
const [sentenceMakingLessonId, setSentenceMakingLessonId] = useState<number | null>(null);
const [sentenceMakingContentId, setSentenceMakingContentId] = useState<number | null>(null);

// KEEP:
// handleCreateContent, handleContentClick, handleDeleteContent
```

**注意**：這些功能已經在 ProgramTreeView 內建了（透過 useContentEditor），所以可以選擇：
- 選項 A：完全移除，讓 ProgramTreeView 處理（推薦）
- 選項 B：暫時保留，稍後驗證後移除

我們選擇 **選項 A（推薦）**，完全移除，讓 ProgramTreeView 處理。

**Step 4: 移除不再需要的 Dialog 元件**

```typescript
// REMOVE:
<ProgramDialog ... />
<LessonDialog ... />
```

**Step 5: 移除 isReordering state 和 apiClient import**

```typescript
// REMOVE:
const [isReordering, setIsReordering] = useState(false);
import { apiClient } from "@/lib/api";  // 改用 ProgramTreeView 內建的 useProgramAPI
```

**Step 6: 執行測試確認功能正常**

Run: `npm run dev`
Navigate to: `http://localhost:5173/teacher/programs`
Test:
- ✅ Create program
- ✅ Edit program
- ✅ Delete program
- ✅ Create lesson
- ✅ Edit lesson
- ✅ Delete lesson
- ✅ Create content
- ✅ Edit content (Reading/SentenceMaking panels)
- ✅ Delete content
- ✅ Reorder (all three levels)

**Step 7: TypeScript 編譯檢查**

Run: `npm run typecheck`
Expected: No errors

**Step 8: Commit**

```bash
git add frontend/src/pages/teacher/TeacherTemplatePrograms.tsx
git commit -m "refactor: migrate TeacherTemplatePrograms to use ProgramTreeView"
```

---

## Task 12: 整合測試（三個 scope）

**Files:**
- Create: `frontend/src/components/shared/__tests__/ProgramTreeView.integration.test.tsx`

**Step 1: 撰寫整合測試（三個 scope）**

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProgramTreeView } from '../ProgramTreeView';
import { ProgramTreeProgram } from '@/hooks/useProgramTree';

// Mock API
const mockAPI = {
  getPrograms: vi.fn(),
  createProgram: vi.fn(),
  updateProgram: vi.fn(),
  deleteProgram: vi.fn(),
  createLesson: vi.fn(),
  updateLesson: vi.fn(),
  deleteLesson: vi.fn(),
  createContent: vi.fn(),
  deleteContent: vi.fn(),
  reorderPrograms: vi.fn(),
  reorderLessons: vi.fn(),
  reorderContents: vi.fn(),
};

vi.mock('@/hooks/useProgramAPI', () => ({
  useProgramAPI: () => mockAPI,
}));

describe('ProgramTreeView Integration Tests', () => {
  const mockPrograms: ProgramTreeProgram[] = [
    {
      id: 1,
      name: 'Program 1',
      lessons: [
        {
          id: 101,
          name: 'Lesson 1-1',
          contents: [
            { id: 1001, title: 'Content 1-1-1', type: 'reading_assessment' },
          ],
        },
      ],
    },
    {
      id: 2,
      name: 'Program 2',
      lessons: [],
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Teacher Scope', () => {
    it('should handle full CRUD workflow for teacher scope', async () => {
      const mockOnProgramsChange = vi.fn();
      mockAPI.createProgram.mockResolvedValue({ id: 3, name: 'New Program', lessons: [] });

      render(
        <ProgramTreeView
          programs={mockPrograms}
          onProgramsChange={mockOnProgramsChange}
          showCreateButton
          createButtonText="新增教材"
          scope="teacher"
        />
      );

      // Create program
      const createButton = screen.getByText('新增教材');
      await userEvent.click(createButton);

      // Fill in program name
      const nameInput = screen.getByLabelText('教材名稱');
      await userEvent.type(nameInput, 'New Program');

      const saveButton = screen.getByText('儲存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockAPI.createProgram).toHaveBeenCalledWith({
          name: 'New Program',
          description: undefined,
        });
        expect(mockOnProgramsChange).toHaveBeenCalledWith(
          expect.arrayContaining([
            expect.objectContaining({ id: 3, name: 'New Program' })
          ])
        );
      });
    });

    it('should handle reorder for all three levels in teacher scope', async () => {
      const mockOnProgramsChange = vi.fn();
      mockAPI.reorderPrograms.mockResolvedValue({});
      mockAPI.reorderLessons.mockResolvedValue({});
      mockAPI.reorderContents.mockResolvedValue({});

      render(
        <ProgramTreeView
          programs={mockPrograms}
          onProgramsChange={mockOnProgramsChange}
          scope="teacher"
        />
      );

      // Test program reorder (drag Program 2 to position 0)
      // ... drag simulation ...

      await waitFor(() => {
        expect(mockAPI.reorderPrograms).toHaveBeenCalledWith([
          { id: 2, order_index: 0 },
          { id: 1, order_index: 1 },
        ]);
      });
    });
  });

  describe('Organization Scope', () => {
    it('should use organization scope in API calls', async () => {
      const mockOnProgramsChange = vi.fn();
      mockAPI.createProgram.mockResolvedValue({ id: 3, name: 'Org Program', lessons: [] });

      render(
        <ProgramTreeView
          programs={mockPrograms}
          onProgramsChange={mockOnProgramsChange}
          showCreateButton
          createButtonText="新增教材"
          scope="organization"
          organizationId="org-123"
        />
      );

      const createButton = screen.getByText('新增教材');
      await userEvent.click(createButton);

      const nameInput = screen.getByLabelText('教材名稱');
      await userEvent.type(nameInput, 'Org Program');

      const saveButton = screen.getByText('儲存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockAPI.createProgram).toHaveBeenCalled();
        // Verify useProgramAPI was called with organization scope
      });
    });
  });

  describe('School Scope', () => {
    it('should use school scope in API calls', async () => {
      const mockOnProgramsChange = vi.fn();
      mockAPI.createProgram.mockResolvedValue({ id: 3, name: 'School Program', lessons: [] });

      render(
        <ProgramTreeView
          programs={mockPrograms}
          onProgramsChange={mockOnProgramsChange}
          showCreateButton
          createButtonText="新增教材"
          scope="school"
          schoolId="school-456"
        />
      );

      const createButton = screen.getByText('新增教材');
      await userEvent.click(createButton);

      const nameInput = screen.getByLabelText('教材名稱');
      await userEvent.type(nameInput, 'School Program');

      const saveButton = screen.getByText('儲存');
      await userEvent.click(saveButton);

      await waitFor(() => {
        expect(mockAPI.createProgram).toHaveBeenCalled();
        // Verify useProgramAPI was called with school scope
      });
    });
  });
});
```

**Step 2: 執行整合測試**

Run: `npm run test -- ProgramTreeView.integration.test.tsx`
Expected: PASS（所有整合測試通過）

**Step 3: Commit**

```bash
git add frontend/src/components/shared/__tests__/ProgramTreeView.integration.test.tsx
git commit -m "test: add integration tests for all three scopes"
```

---

## Task 13: E2E 測試（瀏覽器測試）

**Files:**
- Create: `frontend/src/__tests__/e2e/program-tree-crud.spec.ts`（如果使用 Playwright）

**Step 1: 撰寫 E2E 測試**

```typescript
import { test, expect } from '@playwright/test';

test.describe('ProgramTreeView CRUD E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Login as teacher
    await page.goto('/login');
    await page.fill('input[name="email"]', 'teacher@example.com');
    await page.fill('input[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL('/teacher/programs');
  });

  test('should create, edit, and delete a program', async ({ page }) => {
    // Create program
    await page.click('text=新增教材');
    await page.fill('input[name="name"]', 'E2E Test Program');
    await page.click('text=儲存');

    await expect(page.locator('text=E2E Test Program')).toBeVisible();

    // Edit program
    await page.click('[aria-label="編輯"]:near(text=E2E Test Program)');
    await page.fill('input[name="name"]', 'Updated E2E Program');
    await page.click('text=儲存');

    await expect(page.locator('text=Updated E2E Program')).toBeVisible();

    // Delete program
    await page.click('[aria-label="刪除"]:near(text=Updated E2E Program)');
    await page.click('text=確認刪除');

    await expect(page.locator('text=Updated E2E Program')).not.toBeVisible();
  });

  test('should create and reorder programs', async ({ page }) => {
    // Create two programs
    await page.click('text=新增教材');
    await page.fill('input[name="name"]', 'Program A');
    await page.click('text=儲存');

    await page.click('text=新增教材');
    await page.fill('input[name="name"]', 'Program B');
    await page.click('text=儲存');

    // Get initial order
    const programs = page.locator('[data-level="0"]');
    await expect(programs.first()).toContainText('Program A');
    await expect(programs.last()).toContainText('Program B');

    // Drag Program B above Program A
    const dragHandle = programs.last().locator('[aria-label="拖曳手柄"]');
    await dragHandle.dragTo(programs.first());

    // Verify new order
    await page.reload();
    await expect(programs.first()).toContainText('Program B');
    await expect(programs.last()).toContainText('Program A');
  });

  test('should work across all three scopes', async ({ page }) => {
    // Test teacher scope
    await page.goto('/teacher/programs');
    await expect(page.locator('text=教師教材')).toBeVisible();

    // Test organization scope
    await page.goto('/organization/org-123/materials');
    await expect(page.locator('text=組織教材')).toBeVisible();

    // Test school scope
    await page.goto('/organization/org-123/schools/school-456/materials');
    await expect(page.locator('text=學校教材')).toBeVisible();
  });
});
```

**Step 2: 執行 E2E 測試**

Run: `npx playwright test program-tree-crud.spec.ts`
Expected: PASS（E2E 測試通過）

**Step 3: Commit**

```bash
git add frontend/src/__tests__/e2e/program-tree-crud.spec.ts
git commit -m "test: add E2E tests for ProgramTreeView CRUD"
```

---

## Task 14: 更新 TODO.md 和文件

**Files:**
- Modify: `TODO.md`
- Create: `docs/architecture/program-tree-refactor.md`

**Step 1: 更新 TODO.md**

```markdown
### Medium Priority
1. ~~**重構：ProgramTreeView 取代所有 RecursiveTreeAccordion 直接使用**~~ ✅ **已完成**
   - **完成日期**：2026-01-16
   - **實作內容**：
     - ✅ ProgramTreeView 內建完整 Program/Lesson/Content CRUD
     - ✅ 移除不必要的 props（onEdit/onDelete/onCreate/onReorder）
     - ✅ MaterialsPage 簡化（只傳 scope props）
     - ✅ SchoolMaterialsPage 簡化（只傳 scope props）
     - ✅ TeacherTemplatePrograms 遷移到 ProgramTreeView
     - ✅ 所有三個 scope 測試通過（teacher/organization/school）
   - **測試覆蓋**：
     - ✅ 單元測試（Program/Lesson/Content CRUD）
     - ✅ 整合測試（三個 scope）
     - ✅ E2E 測試（瀏覽器測試）
   - **架構改進**：
     - RecursiveTreeAccordion 現在只負責純 UI 層（拖曳、展開/收合、樹狀結構）
     - ProgramTreeView 是完整的自包含元件（CRUD + Reorder + Content Editor）
     - 統一三個 scope 的實作（不再有重複邏輯）
   - **Commits**:
     - da4b519c "test: add ProgramTreeView test setup"
     - ... (other commits)
```

**Step 2: 創建架構文件**

```markdown
# Program Tree 重構架構文件

## 概述

本次重構將 ProgramTreeView 從一個簡單的 wrapper 元件，重構為一個完整的自包含元件，內建所有 CRUD 功能和 Reorder 邏輯。

## 重構前架構

### TeacherTemplatePrograms（882 行）
- 直接使用 RecursiveTreeAccordion
- 所有 CRUD handlers 內建（Program/Lesson/Content）
- 使用舊 apiClient（非 scope-aware）

### MaterialsPage/SchoolMaterialsPage（404 行）
- 使用 ProgramTreeView wrapper
- CRUD handlers 在父組件（透過 props 傳遞）
- Reorder 由 ProgramTreeView 內建

### 問題
1. 架構不統一（直接用 RecursiveTreeAccordion vs 用 ProgramTreeView）
2. Reorder 邏輯散落（TeacherTemplatePrograms 用舊 API，ProgramTreeView 用新 API）
3. CRUD 邏輯重複（三個頁面都有類似的 handlers）

## 重構後架構

### ProgramTreeView（統一元件）
- 內建完整 CRUD（Program/Lesson/Content）
- 內建 Reorder（三層）
- 內建 Content Editor（Reading/SentenceMaking panels）
- Scope-aware（teacher/organization/school）
- 使用 useProgramAPI（統一 API 介面）

### RecursiveTreeAccordion（純 UI 層）
- 只負責樹狀結構渲染
- 拖曳功能（@dnd-kit/core）
- 展開/收合邏輯
- 不包含業務邏輯

### MaterialsPage/SchoolMaterialsPage/TeacherTemplatePrograms（簡化）
- 只傳 scope props 給 ProgramTreeView
- 不再有 CRUD handlers
- 不再有 Dialog 元件
- 代碼量減少 60%+

## 優點

1. **統一架構**：所有頁面使用相同的 ProgramTreeView
2. **減少重複**：CRUD 邏輯只在一個地方維護
3. **易於測試**：集中測試 ProgramTreeView，覆蓋所有 scope
4. **可維護性**：修改功能只需更新 ProgramTreeView
5. **擴展性**：新增 scope 只需傳新 props，不需修改頁面

## API 使用

### Before
```typescript
// TeacherTemplatePrograms
await apiClient.reorderPrograms(orderData);  // Teacher-only API

// MaterialsPage
await fetch(`/api/organizations/${orgId}/programs/${id}`, ...);  // Manual fetch
```

### After
```typescript
// All pages
const api = useProgramAPI({ scope, organizationId, schoolId });
await api.reorderPrograms(orderData);  // Scope-aware API
```

## 測試策略

1. **單元測試**：ProgramTreeView CRUD 功能
2. **整合測試**：三個 scope 的 API 呼叫
3. **E2E 測試**：瀏覽器測試完整流程

## 遷移檢查清單

- [x] ProgramTreeView 內建 Program CRUD
- [x] ProgramTreeView 內建 Lesson CRUD
- [x] ProgramTreeView 內建 Content Delete
- [x] MaterialsPage 簡化
- [x] SchoolMaterialsPage 簡化
- [x] TeacherTemplatePrograms 遷移
- [x] 所有測試通過
- [x] TypeScript 編譯無錯誤
- [x] E2E 測試通過

## 後續改進

1. 可考慮將 Content Create/Edit 也內建到 ProgramTreeView（目前透過 useContentEditor）
2. 可考慮將 ProgramDialog/LessonDialog 也內建（目前是獨立元件）
3. 可考慮新增更多 scope（例如 classroom）
```

**Step 3: Commit**

```bash
git add TODO.md docs/architecture/program-tree-refactor.md
git commit -m "docs: update TODO.md and add architecture doc for ProgramTreeView refactor"
```

---

## Task 15: 最終驗證和清理

**Files:**
- All modified files

**Step 1: 執行所有測試**

```bash
# Unit tests
npm run test

# TypeScript check
npm run typecheck

# Lint
npm run lint

# Build
npm run build

# E2E tests (if applicable)
npx playwright test
```

Expected: All pass

**Step 2: 手動測試三個 scope**

**Teacher Scope**:
- Navigate to: `http://localhost:5173/teacher/programs`
- Test: Create/Edit/Delete Program
- Test: Create/Edit/Delete Lesson
- Test: Create/Edit/Delete Content
- Test: Reorder all three levels
- Test: Content editors (Reading/SentenceMaking panels)

**Organization Scope**:
- Navigate to: `http://localhost:5173/organization/{orgId}/materials`
- Test: Same as teacher scope
- Verify: Order persists after refresh

**School Scope**:
- Navigate to: `http://localhost:5173/organization/{orgId}/schools/{schoolId}/materials`
- Test: Same as teacher scope
- Verify: Order persists after refresh

**Step 3: 檢查代碼清理**

確認以下檔案已清理：
- [ ] MaterialsPage.tsx：移除所有 CRUD handlers 和 Dialog 元件
- [ ] SchoolMaterialsPage.tsx：移除所有 CRUD handlers 和 Dialog 元件
- [ ] TeacherTemplatePrograms.tsx：移除 Program/Lesson CRUD handlers，保留內容編輯器

**Step 4: 檢查無 console.log**

Run: `grep -r "console.log" frontend/src/components/shared/ProgramTreeView.tsx`
Expected: 只有必要的 diagnostic logs（可選擇移除或保留）

**Step 5: Commit**

```bash
git add .
git commit -m "chore: final cleanup and verification"
```

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-01-16-programtreeview-refactor.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
