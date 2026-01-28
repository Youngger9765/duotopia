# Fix MaterialsPage Reorder Bug - ProgramTreeView Architecture

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix reorder not persisting by implementing scope-aware reorder endpoints and building reorder functionality into ProgramTreeView.

**Architecture:** Move reorder logic from scattered page implementations into ProgramTreeView component. Backend provides 3 scope-aware reorder endpoints (`/api/programs/reorder`, `/api/programs/{id}/lessons/reorder`, `/api/programs/lessons/{id}/contents/reorder`) that accept `scope` query parameter. Frontend useProgramAPI provides scope-aware reorder methods. ProgramTreeView accepts scope props and handles all reorder operations internally.

**Tech Stack:** FastAPI (Python), PostgreSQL, React, TypeScript, @dnd-kit

---

## Task 1: Backend - Programs Reorder Endpoint

**Files:**
- Modify: `backend/routers/programs.py` (add after line 850)
- Test: `backend/tests/test_programs_reorder.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/test_programs_reorder.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Teacher, Program
from auth import create_access_token
import uuid

client = TestClient(app)

@pytest.fixture
def auth_teacher(db: Session):
    """Create test teacher and return auth token"""
    teacher = Teacher(
        email=f"test_{uuid.uuid4()}@example.com",
        name="Test Teacher",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    token = create_access_token({"sub": teacher.email})
    return {"teacher": teacher, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def test_programs(db: Session, auth_teacher):
    """Create 3 test programs with different scopes"""
    teacher = auth_teacher["teacher"]
    org_id = uuid.uuid4()

    # Teacher scope program
    p1 = Program(name="Teacher Program", teacher_id=teacher.id, is_template=True, order_index=0)
    # Organization scope program
    p2 = Program(name="Org Program", teacher_id=teacher.id, organization_id=org_id, is_template=True, order_index=1)
    p3 = Program(name="Org Program 2", teacher_id=teacher.id, organization_id=org_id, is_template=True, order_index=2)

    db.add_all([p1, p2, p3])
    db.commit()
    db.refresh(p1)
    db.refresh(p2)
    db.refresh(p3)

    return {"teacher": p1, "org": [p2, p3], "org_id": str(org_id)}

def test_reorder_teacher_programs(db: Session, auth_teacher, test_programs):
    """Test reordering teacher scope programs"""
    teacher_program = test_programs["teacher"]
    headers = auth_teacher["headers"]

    response = client.put(
        "/api/programs/reorder?scope=teacher",
        headers=headers,
        json=[{"id": teacher_program.id, "order_index": 5}]
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Programs reordered successfully"

    # Verify in database
    db.refresh(teacher_program)
    assert teacher_program.order_index == 5

def test_reorder_organization_programs(db: Session, auth_teacher, test_programs):
    """Test reordering organization scope programs"""
    org_programs = test_programs["org"]
    org_id = test_programs["org_id"]
    headers = auth_teacher["headers"]

    # Swap order
    response = client.put(
        f"/api/programs/reorder?scope=organization&organization_id={org_id}",
        headers=headers,
        json=[
            {"id": org_programs[1].id, "order_index": 0},
            {"id": org_programs[0].id, "order_index": 1}
        ]
    )

    assert response.status_code == 200

    # Verify swap
    db.refresh(org_programs[0])
    db.refresh(org_programs[1])
    assert org_programs[0].order_index == 1
    assert org_programs[1].order_index == 0

def test_reorder_requires_org_id_for_org_scope(auth_teacher):
    """Test that organization scope requires organization_id"""
    headers = auth_teacher["headers"]

    response = client.put(
        "/api/programs/reorder?scope=organization",
        headers=headers,
        json=[{"id": 1, "order_index": 0}]
    )

    assert response.status_code == 400
    assert "organization_id is required" in response.json()["detail"]

def test_reorder_only_affects_teacher_programs(db: Session, auth_teacher, test_programs):
    """Test that teacher can only reorder their own programs"""
    # Create program for different teacher
    other_teacher = Teacher(email="other@example.com", name="Other", hashed_password="hash")
    db.add(other_teacher)
    db.commit()

    other_program = Program(name="Other Program", teacher_id=other_teacher.id, is_template=True, order_index=0)
    db.add(other_program)
    db.commit()
    db.refresh(other_program)

    headers = auth_teacher["headers"]

    # Try to reorder other teacher's program
    response = client.put(
        "/api/programs/reorder?scope=teacher",
        headers=headers,
        json=[{"id": other_program.id, "order_index": 10}]
    )

    # Should succeed but not affect other teacher's program
    assert response.status_code == 200
    db.refresh(other_program)
    assert other_program.order_index == 0  # Unchanged
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd backend
pytest tests/test_programs_reorder.py::test_reorder_teacher_programs -v
```

Expected: `FAIL` with "404 Not Found" (endpoint doesn't exist)

**Step 3: Implement minimal backend endpoint**

Add to `backend/routers/programs.py` (after line 850):

```python
@router.put("/reorder")
async def reorder_programs(
    order_data: List[Dict[str, int]],  # [{"id": 1, "order_index": 1}, ...]
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Reorder programs based on scope.

    - scope=teacher: Reorder teacher's personal programs
    - scope=organization: Reorder organization programs (requires organization_id)
    - scope=school: Reorder school programs (requires school_id)
    """
    # Validate parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when scope=organization"
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id is required when scope=school"
        )

    # Build query based on scope
    program_ids = [item["id"] for item in order_data]
    query = db.query(Program).filter(Program.id.in_(program_ids))

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.is_template == True,
            Program.classroom_id.is_(None),
            Program.organization_id.is_(None),
            Program.school_id.is_(None)
        )
    elif scope == "organization":
        import uuid as uuid_module
        org_uuid = uuid_module.UUID(organization_id)
        query = query.filter(
            Program.organization_id == org_uuid,
            Program.is_template == True
        )
    elif scope == "school":
        import uuid as uuid_module
        sch_uuid = uuid_module.UUID(school_id)
        query = query.filter(
            Program.school_id == sch_uuid,
            Program.is_template == True
        )

    programs_list = query.all()
    programs_dict = {p.id: p for p in programs_list}

    # Update order_index
    for item in order_data:
        program = programs_dict.get(item["id"])
        if program:
            program.order_index = item["order_index"]

    db.commit()
    return {"message": "Programs reordered successfully"}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_programs_reorder.py -v
```

Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add backend/routers/programs.py backend/tests/test_programs_reorder.py
git commit -m "feat(backend): add scope-aware programs reorder endpoint

- Add PUT /api/programs/reorder with scope parameter
- Support teacher, organization, school scopes
- Add comprehensive test coverage (4 test cases)
- Validates scope-specific authorization"
```

---

## Task 2: Backend - Lessons Reorder Endpoint

**Files:**
- Modify: `backend/routers/programs.py` (add after Task 1 endpoint)
- Test: `backend/tests/test_lessons_reorder.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/test_lessons_reorder.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Teacher, Program, Lesson
from auth import create_access_token
import uuid

client = TestClient(app)

@pytest.fixture
def auth_teacher(db: Session):
    """Create test teacher and return auth token"""
    teacher = Teacher(
        email=f"test_{uuid.uuid4()}@example.com",
        name="Test Teacher",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    token = create_access_token({"sub": teacher.email})
    return {"teacher": teacher, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def test_program_with_lessons(db: Session, auth_teacher):
    """Create test program with lessons"""
    teacher = auth_teacher["teacher"]
    org_id = uuid.uuid4()

    program = Program(
        name="Test Program",
        teacher_id=teacher.id,
        organization_id=org_id,
        is_template=True
    )
    db.add(program)
    db.commit()
    db.refresh(program)

    lesson1 = Lesson(program_id=program.id, name="Lesson 1", order_index=0)
    lesson2 = Lesson(program_id=program.id, name="Lesson 2", order_index=1)
    lesson3 = Lesson(program_id=program.id, name="Lesson 3", order_index=2)

    db.add_all([lesson1, lesson2, lesson3])
    db.commit()

    return {
        "program": program,
        "lessons": [lesson1, lesson2, lesson3],
        "org_id": str(org_id)
    }

def test_reorder_lessons_organization_scope(db: Session, auth_teacher, test_program_with_lessons):
    """Test reordering lessons in organization scope"""
    program = test_program_with_lessons["program"]
    lessons = test_program_with_lessons["lessons"]
    org_id = test_program_with_lessons["org_id"]
    headers = auth_teacher["headers"]

    # Reverse order
    response = client.put(
        f"/api/programs/{program.id}/lessons/reorder?scope=organization&organization_id={org_id}",
        headers=headers,
        json=[
            {"id": lessons[2].id, "order_index": 0},
            {"id": lessons[1].id, "order_index": 1},
            {"id": lessons[0].id, "order_index": 2}
        ]
    )

    assert response.status_code == 200

    # Verify reorder
    for lesson in lessons:
        db.refresh(lesson)
    assert lessons[0].order_index == 2
    assert lessons[1].order_index == 1
    assert lessons[2].order_index == 0

def test_reorder_lessons_validates_program_ownership(db: Session, auth_teacher):
    """Test that user can only reorder lessons in their programs"""
    # Create program for different teacher
    other_teacher = Teacher(email="other@example.com", name="Other", hashed_password="hash")
    db.add(other_teacher)
    db.commit()

    other_program = Program(name="Other Program", teacher_id=other_teacher.id, is_template=True)
    db.add(other_program)
    db.commit()

    headers = auth_teacher["headers"]

    response = client.put(
        f"/api/programs/{other_program.id}/lessons/reorder?scope=teacher",
        headers=headers,
        json=[{"id": 1, "order_index": 0}]
    )

    assert response.status_code == 404
    assert "Program not found" in response.json()["detail"]
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_lessons_reorder.py::test_reorder_lessons_organization_scope -v
```

Expected: `FAIL` with "404 Not Found"

**Step 3: Implement minimal endpoint**

Add to `backend/routers/programs.py` (after programs reorder endpoint):

```python
@router.put("/{program_id}/lessons/reorder")
async def reorder_lessons(
    program_id: int,
    order_data: List[Dict[str, int]],
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Reorder lessons within a program (scope-aware)"""
    # Validate parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when scope=organization"
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id is required when scope=school"
        )

    # Verify program exists and matches scope
    query = db.query(Program).filter(Program.id == program_id)

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.is_template == True,
            Program.classroom_id.is_(None),
            Program.organization_id.is_(None),
            Program.school_id.is_(None)
        )
    elif scope == "organization":
        import uuid as uuid_module
        org_uuid = uuid_module.UUID(organization_id)
        query = query.filter(Program.organization_id == org_uuid)
    elif scope == "school":
        import uuid as uuid_module
        sch_uuid = uuid_module.UUID(school_id)
        query = query.filter(Program.school_id == sch_uuid)

    program = query.first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Reorder lessons
    lesson_ids = [item["id"] for item in order_data]
    lessons_list = db.query(Lesson).filter(
        Lesson.id.in_(lesson_ids),
        Lesson.program_id == program_id
    ).all()

    lessons_dict = {lesson.id: lesson for lesson in lessons_list}

    for item in order_data:
        lesson = lessons_dict.get(item["id"])
        if lesson:
            lesson.order_index = item["order_index"]

    db.commit()
    return {"message": "Lessons reordered successfully"}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_lessons_reorder.py -v
```

Expected: Both tests PASS

**Step 5: Commit**

```bash
git add backend/routers/programs.py backend/tests/test_lessons_reorder.py
git commit -m "feat(backend): add scope-aware lessons reorder endpoint

- Add PUT /api/programs/{id}/lessons/reorder with scope parameter
- Validates program ownership based on scope
- Add test coverage for authorization"
```

---

## Task 3: Backend - Contents Reorder Endpoint

**Files:**
- Modify: `backend/routers/programs.py` (add after Task 2 endpoint)
- Test: `backend/tests/test_contents_reorder.py` (create)

**Step 1: Write the failing test**

Create `backend/tests/test_contents_reorder.py`:

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Teacher, Program, Lesson, Content
from auth import create_access_token
import uuid

client = TestClient(app)

@pytest.fixture
def auth_teacher(db: Session):
    """Create test teacher and return auth token"""
    teacher = Teacher(
        email=f"test_{uuid.uuid4()}@example.com",
        name="Test Teacher",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    token = create_access_token({"sub": teacher.email})
    return {"teacher": teacher, "token": token, "headers": {"Authorization": f"Bearer {token}"}}

@pytest.fixture
def test_lesson_with_contents(db: Session, auth_teacher):
    """Create test lesson with contents"""
    teacher = auth_teacher["teacher"]
    org_id = uuid.uuid4()

    program = Program(
        name="Test Program",
        teacher_id=teacher.id,
        organization_id=org_id,
        is_template=True
    )
    db.add(program)
    db.commit()

    lesson = Lesson(program_id=program.id, name="Test Lesson", order_index=0)
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    content1 = Content(lesson_id=lesson.id, type="reading", title="Content 1", order_index=0)
    content2 = Content(lesson_id=lesson.id, type="reading", title="Content 2", order_index=1)
    content3 = Content(lesson_id=lesson.id, type="reading", title="Content 3", order_index=2)

    db.add_all([content1, content2, content3])
    db.commit()

    return {
        "program": program,
        "lesson": lesson,
        "contents": [content1, content2, content3],
        "org_id": str(org_id)
    }

def test_reorder_contents_organization_scope(db: Session, auth_teacher, test_lesson_with_contents):
    """Test reordering contents in organization scope"""
    lesson = test_lesson_with_contents["lesson"]
    contents = test_lesson_with_contents["contents"]
    org_id = test_lesson_with_contents["org_id"]
    headers = auth_teacher["headers"]

    # Reverse order
    response = client.put(
        f"/api/programs/lessons/{lesson.id}/contents/reorder?scope=organization&organization_id={org_id}",
        headers=headers,
        json=[
            {"id": contents[2].id, "order_index": 0},
            {"id": contents[1].id, "order_index": 1},
            {"id": contents[0].id, "order_index": 2}
        ]
    )

    assert response.status_code == 200

    # Verify reorder
    for content in contents:
        db.refresh(content)
    assert contents[0].order_index == 2
    assert contents[1].order_index == 1
    assert contents[2].order_index == 0
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/test_contents_reorder.py::test_reorder_contents_organization_scope -v
```

Expected: `FAIL` with "404 Not Found"

**Step 3: Implement minimal endpoint**

Add to `backend/routers/programs.py` (after lessons reorder endpoint):

```python
@router.put("/lessons/{lesson_id}/contents/reorder")
async def reorder_contents(
    lesson_id: int,
    order_data: List[Dict[str, int]],
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Reorder contents within a lesson (scope-aware)"""
    # Validate parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when scope=organization"
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id is required when scope=school"
        )

    # Verify lesson's program matches scope
    query = db.query(Lesson).join(Program).filter(Lesson.id == lesson_id)

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.is_template == True,
            Program.classroom_id.is_(None),
            Program.organization_id.is_(None),
            Program.school_id.is_(None)
        )
    elif scope == "organization":
        import uuid as uuid_module
        org_uuid = uuid_module.UUID(organization_id)
        query = query.filter(Program.organization_id == org_uuid)
    elif scope == "school":
        import uuid as uuid_module
        sch_uuid = uuid_module.UUID(school_id)
        query = query.filter(Program.school_id == sch_uuid)

    lesson = query.first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Reorder contents
    content_ids = [item["id"] for item in order_data]
    contents_list = db.query(Content).filter(
        Content.id.in_(content_ids),
        Content.lesson_id == lesson_id
    ).all()

    contents_dict = {content.id: content for content in contents_list}

    for item in order_data:
        content = contents_dict.get(item["id"])
        if content:
            content.order_index = item["order_index"]

    db.commit()
    return {"message": "Contents reordered successfully"}
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/test_contents_reorder.py -v
```

Expected: Test PASS

**Step 5: Commit**

```bash
git add backend/routers/programs.py backend/tests/test_contents_reorder.py
git commit -m "feat(backend): add scope-aware contents reorder endpoint

- Add PUT /api/programs/lessons/{id}/contents/reorder with scope parameter
- Validates lesson ownership through program scope
- Complete 3-layer reorder API (programs/lessons/contents)"
```

---

## Task 4: Frontend - Add Reorder Methods to useProgramAPI

**Files:**
- Modify: `frontend/src/hooks/useProgramAPI.ts` (add after line 118)

**Step 1: No test needed** (TypeScript compilation is the test)

**Step 2: Implement reorder methods**

Add to `frontend/src/hooks/useProgramAPI.ts` (after deleteContent method):

```typescript
    // Reorder operations (scope-aware)
    reorderPrograms: async (orderData: { id: number; order_index: number }[]) => {
      const response = await fetch(buildURL('/api/programs/reorder'), {
        method: 'PUT',
        headers,
        body: JSON.stringify(orderData),
      });
      if (!response.ok) throw new Error('Failed to reorder programs');
      return response.json();
    },

    reorderLessons: async (programId: number, orderData: { id: number; order_index: number }[]) => {
      const response = await fetch(buildURL(`/api/programs/${programId}/lessons/reorder`), {
        method: 'PUT',
        headers,
        body: JSON.stringify(orderData),
      });
      if (!response.ok) throw new Error('Failed to reorder lessons');
      return response.json();
    },

    reorderContents: async (lessonId: number, orderData: { id: number; order_index: number }[]) => {
      const response = await fetch(buildURL(`/api/programs/lessons/${lessonId}/contents/reorder`), {
        method: 'PUT',
        headers,
        body: JSON.stringify(orderData),
      });
      if (!response.ok) throw new Error('Failed to reorder contents');
      return response.json();
    },
```

**Step 3: Verify TypeScript compilation**

Run:
```bash
cd frontend
npm run typecheck
```

Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/hooks/useProgramAPI.ts
git commit -m "feat(frontend): add scope-aware reorder methods to useProgramAPI

- Add reorderPrograms, reorderLessons, reorderContents methods
- All methods use buildURL() for automatic scope injection
- Matches backend API signature"
```

---

## Task 5: Frontend - Add Scope Props to ProgramTreeView

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx` (interface at lines 28-39, component at lines 41-52)

**Step 1: Update ProgramTreeViewProps interface**

Modify interface at line 28:

```typescript
interface ProgramTreeViewProps {
  programs: ProgramTreeProgram[];
  onProgramsChange?: (programs: ProgramTreeProgram[]) => void;
  showCreateButton?: boolean;
  createButtonText?: string;
  onCreateClick?: () => void;
  onEdit?: (item: TreeItem, level: number, parentId?: string | number) => void;
  onDelete?: (item: TreeItem, level: number, parentId?: string | number) => void;
  onCreate?: (level: number, parentId: string | number) => void;
  onReorder?: (fromIndex: number, toIndex: number, level: number, parentId?: string | number) => void;
  onRefresh?: () => void;

  // Scope configuration (new)
  scope: 'teacher' | 'organization' | 'school';
  organizationId?: string;
  schoolId?: string;
}
```

**Step 2: Update component signature**

Modify component signature at line 41:

```typescript
export function ProgramTreeView({
  programs: externalPrograms,
  onProgramsChange,
  showCreateButton = false,
  createButtonText,
  onCreateClick,
  onEdit,
  onDelete,
  onCreate,
  onReorder,
  onRefresh,
  scope,
  organizationId,
  schoolId,
}: ProgramTreeViewProps) {
```

**Step 3: Verify TypeScript compilation**

Run:
```bash
npm run typecheck
```

Expected: Errors in MaterialsPage.tsx and SchoolMaterialsPage.tsx (missing required props) - we'll fix next

**Step 4: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "feat(frontend): add scope props to ProgramTreeView interface

- Add scope, organizationId, schoolId to props
- Required for scope-aware API calls
- Breaking change: requires pages to pass scope"
```

---

## Task 6: Frontend - Implement Internal Reorder Handlers in ProgramTreeView

**Files:**
- Modify: `frontend/src/components/shared/ProgramTreeView.tsx` (add after line 52)

**Step 1: Import useProgramAPI**

Add import at top of file:

```typescript
import { useProgramAPI } from "@/hooks/useProgramAPI";
```

**Step 2: Initialize useProgramAPI hook**

Add after line 52 (after component signature):

```typescript
  // Scope-aware API client
  const programAPI = useProgramAPI({ scope, organizationId });
```

**Step 3: Implement internal reorder handlers**

Add after useProgramAPI initialization:

```typescript
  // Internal reorder handlers (scope-aware)
  const handleInternalReorder = async (
    fromIndex: number,
    toIndex: number,
    level: number,
    parentId?: string | number
  ) => {
    // Call external handler if provided
    if (onReorder) {
      onReorder(fromIndex, toIndex, level, parentId);
      return;
    }

    // Otherwise, handle internally with scope-aware API
    try {
      if (level === 0) {
        // Program level reorder
        const newPrograms = [...programs];
        const [movedProgram] = newPrograms.splice(fromIndex, 1);
        newPrograms.splice(toIndex, 0, movedProgram);

        // Update order_index
        const orderData = newPrograms
          .filter((p) => p.id !== undefined)
          .map((p, index) => ({
            id: p.id!,
            order_index: index,
          }));

        // Optimistic update
        setPrograms(newPrograms);

        // API call
        await programAPI.reorderPrograms(orderData);

        // Notify parent
        if (onProgramsChange) {
          onProgramsChange(newPrograms);
        }
      } else if (level === 1 && parentId) {
        // Lesson level reorder
        const programId = typeof parentId === 'string' ? parseInt(parentId) : parentId;
        const program = programs.find((p) => p.id === programId);
        if (!program?.lessons) return;

        const newLessons = [...program.lessons];
        const [movedLesson] = newLessons.splice(fromIndex, 1);
        newLessons.splice(toIndex, 0, movedLesson);

        // Update order_index
        const orderData = newLessons
          .filter((l) => l.id !== undefined)
          .map((l, index) => ({
            id: l.id!,
            order_index: index,
          }));

        // Optimistic update
        const newPrograms = programs.map((p) =>
          p.id === programId ? { ...p, lessons: newLessons } : p
        );
        setPrograms(newPrograms);

        // API call
        await programAPI.reorderLessons(programId, orderData);

        // Notify parent
        if (onProgramsChange) {
          onProgramsChange(newPrograms);
        }
      } else if (level === 2 && parentId) {
        // Content level reorder
        const lessonId = typeof parentId === 'string' ? parseInt(parentId) : parentId;
        const program = programs.find((p) =>
          p.lessons?.some((l) => l.id === lessonId)
        );
        const lesson = program?.lessons?.find((l) => l.id === lessonId);
        if (!lesson?.items) return;

        const newContents = [...lesson.items];
        const [movedContent] = newContents.splice(fromIndex, 1);
        newContents.splice(toIndex, 0, movedContent);

        // Update order_index
        const orderData = newContents
          .filter((c) => c.id !== undefined)
          .map((c, index) => ({
            id: c.id!,
            order_index: index,
          }));

        // Optimistic update
        const newPrograms = programs.map((p) =>
          p.id === program?.id
            ? {
                ...p,
                lessons: p.lessons?.map((l) =>
                  l.id === lessonId ? { ...l, items: newContents } : l
                ),
              }
            : p
        );
        setPrograms(newPrograms);

        // API call
        await programAPI.reorderContents(lessonId, orderData);

        // Notify parent
        if (onProgramsChange) {
          onProgramsChange(newPrograms);
        }
      }
    } catch (error) {
      console.error('Reorder failed:', error);
      toast.error('排序失敗，請重試');
      // Rollback on error
      if (onRefresh) {
        onRefresh();
      }
    }
  };
```

**Step 4: Pass handler to RecursiveTreeAccordion**

Find where RecursiveTreeAccordion is rendered (around line 200+), update the onReorder prop:

```typescript
<RecursiveTreeAccordion
  // ... other props
  onReorder={handleInternalReorder}
/>
```

**Step 5: Verify TypeScript compilation**

Run:
```bash
npm run typecheck
```

Expected: No errors in ProgramTreeView.tsx

**Step 6: Commit**

```bash
git add frontend/src/components/shared/ProgramTreeView.tsx
git commit -m "feat(frontend): implement internal reorder handlers in ProgramTreeView

- Add scope-aware reorder logic for all 3 layers
- Use useProgramAPI for API calls
- Optimistic UI updates with rollback on error
- Toast notifications for user feedback"
```

---

## Task 7: Frontend - Simplify MaterialsPage to Use Internal Handlers

**Files:**
- Modify: `frontend/src/pages/organization/MaterialsPage.tsx` (remove lines 280-365, update ProgramTreeView props)

**Step 1: Remove direct reorder API calls**

Remove these methods (around lines 280-365):

```typescript
// DELETE: handleProgramReorder
// DELETE: handleLessonReorder
// DELETE: handleContentReorder
```

**Step 2: Update ProgramTreeView props**

Find ProgramTreeView usage (around line 490), update to:

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={handleProgramsChange}
  showCreateButton={true}
  createButtonText={t("organization.materials.createProgram")}
  onCreateClick={() => setIsCreateDialogOpen(true)}
  onEdit={handleEdit}
  onDelete={handleDelete}
  onCreate={handleCreate}
  onRefresh={refetchPrograms}
  scope="organization"
  organizationId={organizationId}
/>
```

**Step 3: Verify TypeScript compilation**

Run:
```bash
npm run typecheck
```

Expected: No errors

**Step 4: Test in browser**

Run:
```bash
npm run dev
```

Navigate to: `http://localhost:5173/organization/{org_id}/materials`

Test:
1. Drag-and-drop to reorder a program
2. Refresh page
3. Verify order persists ✅

**Step 5: Commit**

```bash
git add frontend/src/pages/organization/MaterialsPage.tsx
git commit -m "refactor(frontend): simplify MaterialsPage to use ProgramTreeView internal handlers

- Remove 85 lines of reorder logic
- Use ProgramTreeView's scope-aware handlers
- Pass scope='organization' and organizationId props
- Fixes reorder persistence bug"
```

---

## Task 8: Frontend - Simplify SchoolMaterialsPage

**Files:**
- Modify: `frontend/src/pages/organization/SchoolMaterialsPage.tsx` (remove reorder handlers, update ProgramTreeView props)

**Step 1: Remove direct reorder API calls**

Remove reorder handler methods (similar to MaterialsPage)

**Step 2: Update ProgramTreeView props**

Update to:

```typescript
<ProgramTreeView
  programs={programs}
  onProgramsChange={handleProgramsChange}
  showCreateButton={true}
  createButtonText={t("organization.materials.createProgram")}
  onCreateClick={() => setIsCreateDialogOpen(true)}
  onEdit={handleEdit}
  onDelete={handleDelete}
  onCreate={handleCreate}
  onRefresh={refetchPrograms}
  scope="school"
  schoolId={schoolId}
/>
```

**Step 3: Verify TypeScript compilation**

Run:
```bash
npm run typecheck
```

Expected: No errors

**Step 4: Test in browser**

Navigate to: `http://localhost:5173/organization/{org_id}/school/{school_id}/materials`

Test:
1. Drag-and-drop to reorder
2. Refresh page
3. Verify order persists ✅

**Step 5: Commit**

```bash
git add frontend/src/pages/organization/SchoolMaterialsPage.tsx
git commit -m "refactor(frontend): simplify SchoolMaterialsPage to use ProgramTreeView internal handlers

- Remove reorder logic duplication
- Use ProgramTreeView's scope-aware handlers
- Pass scope='school' and schoolId props
- Consistent with MaterialsPage refactoring"
```

---

## Task 9: Update TODO.md - Mark High Priority Task Complete

**Files:**
- Modify: `TODO.md` (lines 12-23)

**Step 1: Update checklist**

Update High Priority section:

```markdown
1. **修復：MaterialsPage/SchoolMaterialsPage Reorder 無法保存** 🔴
   - **問題**：拖曳排序後重新整理頁面，順序沒有保存
   - **Root Cause**：呼叫錯誤的 API scope
     - MaterialsPage（organization scope）→ 呼叫 `/api/teachers/programs/reorder`（teacher scope）❌
     - SchoolMaterialsPage（school scope）→ 呼叫 `/api/teachers/programs/reorder`（teacher scope）❌
   - **錯誤架構**：Reorder logic 散落在 3 個地方（TeacherTemplatePrograms, MaterialsPage, SchoolMaterialsPage）
   - **正確架構**：✅ **選項 A - Reorder 內建到 ProgramTreeView**
   - **當前狀態**：✅ **已完成**
     - [x] UI 拖曳功能正常（infinite loop 已修復）
     - [x] Backend: `/api/programs/reorder?scope=xxx` endpoint（已實作 3 層）
     - [x] ProgramTreeView: 內建 reorder 功能（已實作）
     - [x] MaterialsPage/SchoolMaterialsPage 簡化（已完成）
   - **完成日期**：2026-01-16
   - **優先級**：🔴 HIGH - ~~Blocking 用戶使用~~ **RESOLVED**
```

**Step 2: Commit**

```bash
git add TODO.md
git commit -m "docs: mark reorder bug fix as complete in TODO.md

- All backend endpoints implemented and tested
- ProgramTreeView has internal reorder handlers
- MaterialsPage and SchoolMaterialsPage refactored
- Bug verified fixed: order persists after refresh"
```

---

## Task 10: Verification - End-to-End Testing

**Files:**
- No modifications, just testing

**Step 1: Run all backend tests**

```bash
cd backend
pytest tests/test_programs_reorder.py tests/test_lessons_reorder.py tests/test_contents_reorder.py -v
```

Expected: All tests PASS (9 tests total)

**Step 2: Run frontend type check**

```bash
cd frontend
npm run typecheck
```

Expected: No errors

**Step 3: Manual browser testing - Teacher Scope**

Navigate to: `http://localhost:5173/teacher/programs`

Test:
1. Drag-and-drop to reorder programs
2. Refresh page → Order persists ✅
3. Drag-and-drop to reorder lessons
4. Refresh page → Order persists ✅
5. Drag-and-drop to reorder contents
6. Refresh page → Order persists ✅

**Step 4: Manual browser testing - Organization Scope**

Navigate to: `http://localhost:5173/organization/{org_id}/materials`

Test: Same 3-layer reorder + refresh verification ✅

**Step 5: Manual browser testing - School Scope**

Navigate to: `http://localhost:5173/organization/{org_id}/school/{school_id}/materials`

Test: Same 3-layer reorder + refresh verification ✅

**Step 6: Document verification results**

If all tests pass, proceed to final commit. If any fail, use @systematic-debugging skill to identify and fix issues before proceeding.

---

## Final Commit

**When all verification passes:**

```bash
git add .
git commit -m "feat: fix reorder persistence bug with scope-aware architecture

BREAKING CHANGE: ProgramTreeView now requires scope props

Summary:
- Backend: Add 3 scope-aware reorder endpoints (programs/lessons/contents)
- Frontend: useProgramAPI provides scope-aware reorder methods
- Frontend: ProgramTreeView has internal reorder handlers
- Frontend: MaterialsPage/SchoolMaterialsPage simplified (removed 170+ lines)

Testing:
- 9 backend tests (programs/lessons/contents × teacher/org/school)
- Manual E2E testing across all 3 scopes and 3 layers
- Verified: Order persists after page refresh

Fixes #112 (if tracking via GitHub issue)

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Notes for Implementation

**TDD Discipline:**
- ALWAYS write test first
- ALWAYS verify test fails before implementing
- ALWAYS verify test passes after implementing
- NEVER skip the red-green cycle

**DRY Principle:**
- Backend endpoints share validation logic (could extract to helper)
- Frontend reorder handlers share structure (could extract to utility)
- Only extract if you see repetition 3+ times (YAGNI)

**Commit Hygiene:**
- Commit after each green test
- Use conventional commits format
- Include "why" in commit messages when not obvious

**Error Handling:**
- Backend returns 400 for missing required params
- Backend returns 404 for unauthorized access
- Frontend shows toast on error
- Frontend rolls back optimistic updates on API failure

**Verification Before Completion:**
Use @verification-before-completion skill before claiming any task is "done". MUST show:
- Test output (green)
- TypeScript compilation success
- Browser verification screenshot/evidence

---

**End of Implementation Plan**

Plan complete and saved to `docs/plans/2026-01-16-reorder-fix-programtreeview.md`.

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
