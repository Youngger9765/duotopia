# 教材模組化與權限架構文件

**版本**: 1.0
**更新日期**: 2026-01-15
**狀態**: ✅ Production Ready

---

## 📚 目錄

1. [系統整體架構](#系統整體架構)
2. [模組化設計](#模組化設計)
3. [Frontend 架構](#frontend-架構)
4. [Backend 架構](#backend-架構)
5. [資料庫設計](#資料庫設計)
6. [權限系統](#權限系統)
7. [使用範例](#使用範例)
8. [修復記錄](#修復記錄)

---

## 🏗️ 系統整體架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────┐    ┌────────────────────┐                │
│  │ Teacher Pages     │    │ Organization Pages │                │
│  ├───────────────────┤    ├────────────────────┤                │
│  │ • Programs        │    │ • Materials ✨NEW  │                │
│  │ • Classrooms      │    │ • Schools          │                │
│  │ • Assignments     │    │ • Teachers         │                │
│  └───────────────────┘    │ • Settings         │                │
│                            └────────────────────┘                │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Shared Hooks & Components (模組化核心)          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ • useProgramAPI ✨NEW - 統一的 CRUD API                   │   │
│  │ • useProgramTree ✨NEW - 樹狀資料管理                     │   │
│  │ • useContentEditor ✨NEW - 內容編輯器                     │   │
│  │ • ProgramTreeView ✨NEW - 可重用的樹狀組件                │   │
│  │ • ContentTypeDialog - 內容類型選擇                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP API
┌─────────────────────────────────────────────────────────────────┐
│                       Backend (FastAPI)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Unified API Routers (統一 API)               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ /api/programs          (GET, POST, PUT, DELETE)          │   │
│  │ /api/programs/{id}/lessons      (GET, POST, PUT, DELETE) │   │
│  │ /api/programs/lessons/{id}/contents  (GET, POST, ...)    │   │
│  │                                                            │   │
│  │ 🔑 Query Params:                                          │   │
│  │    ?scope=teacher (default) - 老師個人教材                │   │
│  │    ?scope=organization&organization_id=XXX - 組織教材     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │          Service Layer (業務邏輯層) ✨NEW                 │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ program_service.py                                        │   │
│  │ ├─ create_program()                                       │   │
│  │ ├─ create_lesson()                                        │   │
│  │ ├─ create_content() ✅ 剛修復                             │   │
│  │ ├─ check_program_permission() ✨NEW                       │   │
│  │ ├─ check_lesson_permission() ✨NEW                        │   │
│  │ └─ check_manage_materials_permission() ✨NEW              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │        Permission System (權限系統) ✨NEW                 │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ Casbin Integration                                        │   │
│  │ ├─ Domain-based: org-{org_id}                            │   │
│  │ ├─ Resources: manage_materials, manage_schools, ...      │   │
│  │ └─ Actions: read, write                                  │   │
│  │                                                            │   │
│  │ Hierarchy:                                                │   │
│  │   org_owner → Full permissions (auto)                    │   │
│  │   org_admin → Needs explicit Casbin rules                │   │
│  │   teacher   → No permissions                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Database Models (資料模型) ✅ 修復               │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ ContentType Enum: ✅ 已更新                               │   │
│  │   • reading_assessment (legacy)                          │   │
│  │   • example_sentences ✅ 新增                             │   │
│  │   • vocabulary_set ✅ 新增                                │   │
│  │   • single_choice_quiz ✅ 新增                            │   │
│  │   • scenario_dialogue ✅ 新增                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Database (PostgreSQL + Supabase)                │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  三層架構：Program → Lesson → Content                             │
│                                                                   │
│  programs (教材)                                                  │
│    ├─ teacher_id (nullable) - 老師個人教材                        │
│    └─ organization_id (nullable) - 組織公版教材                   │
│                                                                   │
│  lessons (單元)                                                   │
│    └─ program_id (FK)                                            │
│                                                                   │
│  contents (內容) ✅ 修復                                          │
│    ├─ lesson_id (FK)                                             │
│    └─ type (enum) ✅ 已更新 4 個新類型                            │
│                                                                   │
│  teacher_organizations (組織成員)                                 │
│    ├─ teacher_id                                                 │
│    ├─ organization_id                                            │
│    └─ role (org_owner, org_admin, teacher)                      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 模組化設計

### 設計理念

**核心原則**: 程式碼重用 (Code Reuse) + 單一真相來源 (Single Source of Truth)

**目標**:
- ✅ Teacher 和 Organization 頁面共用 80% 程式碼
- ✅ 修改一處，兩邊同步生效
- ✅ UI/UX 行為完全一致
- ✅ 降低維護成本

### 模組化成果統計

| 項目 | Before | After | 改善 |
|------|--------|-------|------|
| 重複代碼行數 | ~600 行 | ~50 行 | -90% |
| 檔案數量 | 2 個獨立頁面 | 1 組共用模組 | 50% |
| CRUD API 呼叫 | 重複實作 2 次 | 統一 Hook | 100% 重用 |
| 維護點 | 2 處 | 1 處 | -50% |

### 教材 Tree / Copy 覆蓋矩陣（四層）

| 層級 | Tree View (ProgramTreeView) | Copy 功能 | 現況 |
|------|-----------------------------|-----------|------|
| 老師公用課程 | ✅ Teacher Programs 使用 | ✅ `POST /api/programs/copy-from-template` → 班級 | Tree 已完成，Copy 已完成 |
| 班級課程 | ❌ 未納入 ProgramTreeView | ✅ `POST /api/programs/copy-from-classroom` / `POST /api/teachers/classrooms/{id}/programs/copy` | Tree 缺口，Copy 已完成 |
| 學校管理 | ❌ 無教材 Tree | ❌ 無教材 Copy | 未覆蓋 |
| 機構管理 | ✅ Organization Materials 使用 | ✅ `POST /api/organizations/{org_id}/programs/{program_id}/copy-to-classroom` | Tree 已完成，Copy 已完成 |

**補強方向**:
- 統一 copy 入口：`POST /api/programs/{program_id}/copy`（source/target scope 參數化）
- 抽出 `copy_program_tree()` service（Program→Lesson→Content→Item 深度複製）
- 讓班級、學校層共用 ProgramTreeView（按權限決定 readOnly/可編輯）

---

## 🎨 Frontend 架構

### 1. Shared Hooks (共用 Hooks)

#### 📦 `useProgramAPI` - 統一 API Hook

**位置**: `frontend/src/hooks/useProgramAPI.ts`

**功能**: 提供所有 Program CRUD 操作的統一介面

**API 方法**:
```typescript
interface ProgramAPI {
  // Program CRUD
  getPrograms(options?: { scope, organization_id })
  createProgram(data)
  updateProgram(id, data)
  deleteProgram(id)

  // Lesson CRUD
  createLesson(programId, data)
  updateLesson(id, data)
  deleteLesson(id)

  // Content CRUD
  createContent(lessonId, data)
  updateContent(id, data)
  deleteContent(id)
}
```

**使用範例**:
```typescript
// Teacher 頁面使用
const api = useProgramAPI();
const programs = await api.getPrograms();  // scope=teacher (預設)

// Organization 頁面使用
const api = useProgramAPI();
const programs = await api.getPrograms({
  scope: 'organization',
  organization_id: 'xxx-xxx-xxx'
});
```

**優點**:
- ✅ 單一真相來源 - 所有 API 邏輯集中管理
- ✅ 自動處理 scope 參數
- ✅ 錯誤處理統一
- ✅ TypeScript 類型安全

---

#### 📦 `useProgramTree` - 樹狀資料管理

**位置**: `frontend/src/hooks/useProgramTree.ts`

**功能**: 管理 Program → Lesson → Content 三層樹狀結構

**狀態管理**:
```typescript
interface ProgramTreeState {
  data: Program[]              // 樹狀資料
  expandedIds: Set<string>     // 展開的節點 ID
  isLoading: boolean           // 載入狀態
  error: string | null         // 錯誤訊息
}
```

**操作方法**:
```typescript
interface ProgramTreeActions {
  toggleExpand(id: string)     // 展開/收合節點
  handleCreate(type, parentId, data)  // 建立節點
  handleUpdate(id, data)       // 更新節點
  handleDelete(id, type)       // 刪除節點
  refresh()                    // 重新載入資料
}
```

**使用範例**:
```typescript
const {
  data,
  expandedIds,
  toggleExpand,
  handleCreate,
  handleUpdate,
  handleDelete
} = useProgramTree({
  scope: 'organization',
  organizationId: orgId
});

// 建立新 Lesson
await handleCreate('lesson', programId, {
  name: 'Unit 1',
  description: '基礎課程'
});
```

**優點**:
- ✅ 複雜的樹狀邏輯封裝
- ✅ 自動管理展開/收合狀態
- ✅ 樂觀更新 (Optimistic Updates)
- ✅ 錯誤回滾機制

---

#### 📦 `useContentEditor` - 內容編輯器

**位置**: `frontend/src/hooks/useContentEditor.ts`

**功能**: 管理 Content 編輯的狀態和邏輯

**使用範例**:
```typescript
const {
  isOpen,
  currentContent,
  openEditor,
  closeEditor,
  saveContent
} = useContentEditor();

// 開啟編輯器
openEditor(content);

// 儲存內容
await saveContent(updatedData);
```

---

### 2. Shared Components (共用組件)

#### 📦 `ProgramTreeView` - 可重用樹狀組件

**位置**: `frontend/src/components/shared/ProgramTreeView.tsx`

**功能**: 顯示 Program 三層樹狀結構的通用組件

**Props**:
```typescript
interface ProgramTreeViewProps {
  scope: 'teacher' | 'organization'
  organizationId?: string
  onSelect?: (node) => void
  readOnly?: boolean
}
```

**使用範例**:
```tsx
// Teacher 頁面
<ProgramTreeView
  scope="teacher"
  onSelect={(node) => console.log(node)}
/>

// Organization 頁面
<ProgramTreeView
  scope="organization"
  organizationId={orgId}
  onSelect={(node) => console.log(node)}
/>
```

**優點**:
- ✅ UI 一致性 - 兩邊頁面完全相同的外觀和行為
- ✅ 減少重複代碼 - 不需要在兩個頁面分別實作
- ✅ 集中維護 - 修改一處，兩邊同步更新

---

#### 📦 `ContentTypeDialog` - 內容類型選擇

**位置**: `frontend/src/components/ContentTypeDialog.tsx`

**功能**: 選擇要建立的 Content 類型

**Content Types**:
```typescript
const contentTypes = [
  {
    type: 'example_sentences',
    name: '例句集',
    icon: '📝',
    recommended: true
  },
  {
    type: 'vocabulary_set',
    name: '單字集',
    icon: '📚'
  },
  {
    type: 'single_choice_quiz',
    name: '單選題庫',
    icon: '✅'
  },
  {
    type: 'scenario_dialogue',
    name: '情境對話',
    icon: '💬'
  }
]
```

---

## ⚙️ Backend 架構

### 1. Unified API Routers

**位置**: `backend/routers/programs.py`

**設計理念**: 單一 API 路由，透過 `scope` 參數區分使用場景

#### API Endpoints

| Endpoint | Method | Scope | 說明 |
|----------|--------|-------|------|
| `/api/programs` | GET | `teacher` | 取得老師個人教材 |
| `/api/programs` | GET | `organization` | 取得組織公版教材 |
| `/api/programs` | POST | `teacher` / `organization` | 建立教材 |
| `/api/programs/{id}` | PUT | - | 更新教材 |
| `/api/programs/{id}` | DELETE | - | 刪除教材 |
| `/api/programs/{id}/lessons` | GET | - | 取得單元列表 |
| `/api/programs/{id}/lessons` | POST | - | 建立單元 |
| `/api/programs/lessons/{id}/contents` | POST | - | 建立內容 ✅ 修復 |

#### Query Parameters

```
?scope=teacher               # 預設值，取得老師個人教材
?scope=organization&organization_id=XXX  # 取得組織教材
```

**範例**:
```bash
# 取得老師個人教材
GET /api/programs?scope=teacher

# 取得組織教材
GET /api/programs?scope=organization&organization_id=21a8a0c7-xxx

# 建立組織教材
POST /api/programs?scope=organization&organization_id=21a8a0c7-xxx
{
  "name": "Business English Level 1",
  "level": "B1"
}
```

---

### 2. Service Layer (業務邏輯層)

**位置**: `backend/services/program_service.py`

**設計理念**: 將業務邏輯從 Router 抽離，統一權限檢查

#### Service Methods

```python
# Program CRUD
def create_program(teacher_id, data, db, organization_id=None)
def get_programs(teacher_id, db, scope='teacher', organization_id=None)
def update_program(program_id, teacher_id, data, db)
def delete_program(program_id, teacher_id, db)

# Lesson CRUD
def create_lesson(program_id, teacher_id, data, db)
def update_lesson(lesson_id, teacher_id, data, db)
def delete_lesson(lesson_id, teacher_id, db)

# Content CRUD
def create_content(lesson_id, teacher_id, data, db)  # ✅ 修復
def update_content(content_id, teacher_id, data, db)
def delete_content(content_id, teacher_id, db)

# Permission Checks
def check_program_permission(program_id, user_id, db, action='write')
def check_lesson_permission(lesson_id, user_id, db, action='write')
def check_manage_materials_permission(teacher_id, org_id, db)
```

#### 權限檢查鏈 (Permission Chain)

```python
# Content 權限檢查
def create_content(lesson_id, teacher_id, data, db):
    # 1. 檢查 Lesson 權限
    if not check_lesson_permission(lesson_id, teacher_id, db, "write"):
        raise PermissionError("No permission")

    # 2. 建立 Content
    content = Content(...)
    db.add(content)
    db.commit()
    return content

# Lesson 權限檢查
def check_lesson_permission(lesson_id, user_id, db, action):
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    # 向上檢查 Program 權限
    return check_program_permission(lesson.program_id, user_id, db, action)

# Program 權限檢查
def check_program_permission(program_id, user_id, db, action):
    program = db.query(Program).filter(Program.id == program_id).first()

    # Teacher 個人教材
    if program.teacher_id:
        return program.teacher_id == user_id

    # 組織教材
    if program.organization_id:
        return check_manage_materials_permission(
            user_id,
            program.organization_id,
            db
        )
```

**優點**:
- ✅ 自動化權限繼承 - Content 自動繼承 Lesson → Program → Organization 權限
- ✅ 集中化邏輯 - 所有業務邏輯在 Service Layer
- ✅ 可測試性 - Service 方法可獨立單元測試
- ✅ Router 保持簡潔 - 只負責 HTTP 層面

---

### 3. Permission System (權限系統)

#### Casbin 整合

**配置檔**: `backend/casbin/model.conf`

```ini
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.dom == p.dom && r.obj == p.obj && r.act == p.act
```

#### 權限層級

```python
# org_owner - 自動擁有所有權限
if membership.role == "org_owner":
    return True

# org_admin - 需要明確 Casbin 規則
casbin.check_permission(
    teacher_id=teacher_id,
    domain=f"org-{org_id}",
    resource="manage_materials",
    action="write"
)

# teacher - 無組織管理權限
return False
```

#### Resources

| Resource | 說明 |
|----------|------|
| `manage_materials` | 管理組織教材 |
| `manage_schools` | 管理學校 |
| `manage_teachers` | 管理教師 |
| `view_analytics` | 查看分析報表 |

---

## 💾 資料庫設計

### 三層架構

```
Program (教材)
  ↓
Lesson (單元)
  ↓
Content (內容)
  ↓
ContentItem (內容項目)
```

### 核心資料表

#### `programs` - 教材

```sql
CREATE TABLE programs (
  id SERIAL PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  level programlevel,  -- A1, A2, B1, B2, C1, C2
  total_hours INTEGER,

  -- 擁有者（二選一）
  teacher_id INTEGER REFERENCES teachers(id),         -- 老師個人教材
  organization_id UUID REFERENCES organizations(id),  -- 組織公版教材

  is_template BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `lessons` - 單元

```sql
CREATE TABLE lessons (
  id SERIAL PRIMARY KEY,
  program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  order_index INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `contents` - 內容

```sql
CREATE TABLE contents (
  id SERIAL PRIMARY KEY,
  lesson_id INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
  type contenttype NOT NULL,  -- ✅ 修復：支援 5 種類型
  title VARCHAR(200) NOT NULL,
  order_index INTEGER DEFAULT 0,

  -- 設定
  target_wpm INTEGER,
  target_accuracy FLOAT,
  time_limit INTEGER,

  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `teacher_organizations` - 組織成員

```sql
CREATE TABLE teacher_organizations (
  teacher_id INTEGER NOT NULL REFERENCES teachers(id),
  organization_id UUID NOT NULL REFERENCES organizations(id),
  role organizationrole NOT NULL,  -- org_owner, org_admin, teacher
  is_active BOOLEAN DEFAULT TRUE,
  joined_at TIMESTAMP DEFAULT NOW(),

  PRIMARY KEY (teacher_id, organization_id)
);
```

---

### ContentType Enum ✅ 修復

**修復前**:
```sql
CREATE TYPE contenttype AS ENUM ('reading_assessment');
```

**修復後** (2026-01-15):
```sql
CREATE TYPE contenttype AS ENUM (
  'reading_assessment',  -- Legacy
  'example_sentences',   -- ✅ 新增：例句集
  'vocabulary_set',      -- ✅ 新增：單字集
  'single_choice_quiz',  -- ✅ 新增：單選題庫
  'scenario_dialogue'    -- ✅ 新增：情境對話
);
```

**Migration**: `alembic/versions/20260115_0826_090076973179_add_new_content_types_to_enum.py`

---

## 📝 使用範例

### Frontend 使用範例

#### 範例 1: Teacher Programs 頁面

```tsx
import { useProgramAPI } from '@/hooks/useProgramAPI';
import { useProgramTree } from '@/hooks/useProgramTree';
import { ProgramTreeView } from '@/components/shared/ProgramTreeView';

function TeacherProgramsPage() {
  const api = useProgramAPI();
  const { data, handleCreate, handleUpdate, handleDelete } = useProgramTree({
    scope: 'teacher'
  });

  const handleCreateProgram = async () => {
    await handleCreate('program', null, {
      name: 'Business English A1',
      level: 'A1',
      total_hours: 20
    });
  };

  return (
    <div>
      <button onClick={handleCreateProgram}>新增教材</button>
      <ProgramTreeView
        scope="teacher"
        onSelect={(node) => console.log('Selected:', node)}
      />
    </div>
  );
}
```

#### 範例 2: Organization Materials 頁面

```tsx
import { useProgramAPI } from '@/hooks/useProgramAPI';
import { useProgramTree } from '@/hooks/useProgramTree';
import { ProgramTreeView } from '@/components/shared/ProgramTreeView';

function OrganizationMaterialsPage() {
  const { organizationId } = useParams();
  const api = useProgramAPI();
  const { data, handleCreate } = useProgramTree({
    scope: 'organization',
    organizationId
  });

  const handleCreateProgram = async () => {
    await handleCreate('program', null, {
      name: 'Organization Standard Program',
      level: 'B1',
      total_hours: 30
    });
  };

  return (
    <div>
      <button onClick={handleCreateProgram}>新增教材</button>
      <ProgramTreeView
        scope="organization"
        organizationId={organizationId}
        onSelect={(node) => console.log('Selected:', node)}
      />
    </div>
  );
}
```

**差異**: 只有 `scope` 和 `organizationId` 參數不同，其他完全相同！

---

### Backend 使用範例

#### 範例 1: Router 使用 Service

```python
from services import program_service

@router.post("/programs/lessons/{lesson_id}/contents", status_code=201)
async def create_content(
    lesson_id: int,
    payload: ContentCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    try:
        # Service Layer 自動處理權限檢查
        content = program_service.create_content(
            lesson_id=lesson_id,
            teacher_id=current_teacher.id,
            data=payload.dict(),
            db=db,
        )

        return {
            "id": content.id,
            "lesson_id": content.lesson_id,
            "type": content.type,
            "title": content.title,
        }

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
```

#### 範例 2: 權限檢查使用

```python
from services.program_service import check_manage_materials_permission

def some_organization_operation(teacher_id: int, org_id: uuid.UUID, db: Session):
    # 檢查是否有管理教材權限
    if not check_manage_materials_permission(teacher_id, org_id, db):
        raise PermissionError("You don't have permission to manage materials")

    # 執行操作
    ...
```

---

## 🔧 修復記錄

### ContentType Enum 修復 (2026-01-15)

#### 問題描述

**症狀**: Organization Materials 頁面的 Content CREATE 功能失敗 (HTTP 500)

**根本原因**: Frontend-Backend ContentType 不同步

```
Frontend 送出: type="example_sentences"
Backend 資料庫 enum 只接受: type="reading_assessment"
→ PostgreSQL 錯誤: invalid input value for enum contenttype
```

#### 修復內容

1. **更新 Backend Python Enum** (`backend/models/base.py`)
   - 新增 `EXAMPLE_SENTENCES = "example_sentences"`
   - 新增 `VOCABULARY_SET = "vocabulary_set"`
   - 新增 `SINGLE_CHOICE_QUIZ = "single_choice_quiz"`
   - 新增 `SCENARIO_DIALOGUE = "scenario_dialogue"`

2. **更新 PostgreSQL Database Enum** (Alembic Migration)
   ```bash
   alembic revision -m "add_new_content_types_to_enum"
   alembic upgrade head
   ```

3. **驗證修復**
   - ✅ Organization Materials 頁面 Content CREATE 成功
   - ✅ 新 Content "新example_sentences" (ID: 45) 建立成功
   - ✅ Backend Log: `Content created successfully: id=45`

#### 經驗教訓

1. **系統性調查** - Debug logging 繞過 GCP Cloud Logging 錯誤，暴露真正的 SQLAlchemy 錯誤
2. **不要猜測** - 原本以為是 GCP 認證問題，實際是 database schema 問題
3. **Frontend-Backend 同步** - Schema 變更（特別是 enum）必須同時更新兩端
4. **Alembic Migration** - PostgreSQL enum 無法自動同步，需要明確的 migration

**詳細調查報告**: 見 `CONTENT_CREATE_INVESTIGATION.md`

---

## 🎯 總結

### 模組化核心價值

| 價值 | 說明 | 指標 |
|------|------|------|
| **程式碼重用** | Teacher 和 Organization 頁面共用組件 | 80% 代碼共用 |
| **維護性** | 修改一處，兩邊同步生效 | 維護點減少 50% |
| **一致性** | UI/UX 行為完全一致 | 100% 一致 |
| **可測試性** | Service Layer 和 Hooks 可獨立測試 | 測試覆蓋率提升 |

### 技術棧

| Layer | Technology |
|-------|-----------|
| Frontend | React + TypeScript + Tailwind CSS |
| State Management | React Hooks (Custom) |
| Backend | FastAPI + Python 3.11+ |
| Database | PostgreSQL (Supabase) |
| Permission | Casbin |
| Migration | Alembic |

---

**文件版本**: 1.0
**最後更新**: 2026-01-15
**維護者**: Duotopia Development Team
