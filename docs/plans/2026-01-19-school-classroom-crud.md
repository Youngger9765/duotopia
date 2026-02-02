# School Classroom CRUD API Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable school administrators to create, update, and manage classrooms within their schools, with optional teacher assignment.

**Architecture:** Extend existing classroom API with school-scoped CRUD operations. Use existing `ClassroomSchool` relationship and `has_school_materials_permission` for authorization.

**Tech Stack:** FastAPI, SQLAlchemy, PostgreSQL, Pydantic

---

## Task 1: Modify Classroom Model (Allow Nullable Teacher)

**Files:**
- Modify: `backend/models/classroom.py:31`
- Modify: `backend/alembic/versions/*.py` (new migration)

**Background:** Currently `teacher_id` is `nullable=False`. School admins need to create classrooms before assigning teachers.

**Step 1: Update Classroom model**

In `backend/models/classroom.py` line 31:

```python
# Before:
teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)

# After:
teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
```

**Step 2: Create database migration**

Run:
```bash
cd backend
alembic revision -m "make classroom teacher_id nullable"
```

**Step 3: Write migration**

In the generated migration file:

```python
def upgrade():
    op.alter_column('classrooms', 'teacher_id',
                    existing_type=sa.INTEGER(),
                    nullable=True)

def downgrade():
    op.alter_column('classrooms', 'teacher_id',
                    existing_type=sa.INTEGER(),
                    nullable=False)
```

**Step 4: Run migration**

Run:
```bash
alembic upgrade head
```
Expected: Migration applied successfully

**Step 5: Commit**

```bash
git add backend/models/classroom.py backend/alembic/versions/*.py
git commit -m "feat: make classroom teacher_id nullable for school admin creation"
```

---

## Task 2: Create Request/Response Schemas

**Files:**
- Create: `backend/routers/schemas/classroom.py`

**Step 1: Create schemas file**

Create `backend/routers/schemas/classroom.py`:

```python
"""Classroom request/response schemas for school management"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SchoolClassroomCreate(BaseModel):
    """Request to create classroom in school"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    level: str = Field(default="A1", pattern="^(PREA|A1|A2|B1|B2|C1|C2)$")
    teacher_id: Optional[int] = None  # Optional: Can assign later

    class Config:
        json_schema_extra = {
            "example": {
                "name": "一年級 A 班",
                "description": "一年級英文基礎班",
                "level": "A1",
                "teacher_id": 123
            }
        }


class SchoolClassroomUpdate(BaseModel):
    """Request to update classroom"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    level: Optional[str] = Field(None, pattern="^(PREA|A1|A2|B1|B2|C1|C2)$")
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "一年級 A 班（進階）",
                "level": "A2"
            }
        }


class AssignTeacherRequest(BaseModel):
    """Request to assign/reassign teacher to classroom"""
    teacher_id: Optional[int] = None  # None = unassign

    class Config:
        json_schema_extra = {
            "example": {
                "teacher_id": 123
            }
        }
```

**Step 2: Commit**

```bash
git add backend/routers/schemas/classroom.py
git commit -m "feat: add classroom CRUD schemas for school management"
```

---

## Task 3: Write Tests for POST Endpoint (RED)

**Files:**
- Create: `backend/tests/test_school_classrooms_api.py`

**Step 1: Create test file**

Create `backend/tests/test_school_classrooms_api.py`:

```python
"""Tests for school classroom CRUD API"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from main import app
from models import Teacher, School, TeacherSchool, Classroom, ClassroomSchool
from database import get_db


client = TestClient(app)


@pytest.fixture
def db_session():
    """Get test database session"""
    db = next(get_db())
    yield db
    db.rollback()


@pytest.fixture
def school_admin_teacher(db_session: Session):
    """Create teacher with school_admin role"""
    teacher = Teacher(
        email="admin@test.com",
        name="School Admin",
        password_hash="hashed",
        is_active=True
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def school(db_session: Session):
    """Create test school"""
    org_id = uuid.uuid4()
    school = School(
        id=uuid.uuid4(),
        organization_id=org_id,
        name="Test School",
        is_active=True
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture
def link_teacher_to_school(db_session: Session, school_admin_teacher, school):
    """Link teacher to school with school_admin role"""
    link = TeacherSchool(
        teacher_id=school_admin_teacher.id,
        school_id=school.id,
        roles=["school_admin"],
        is_active=True
    )
    db_session.add(link)
    db_session.commit()


def test_create_classroom_without_teacher_assignment(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: School admin can create classroom without assigning teacher"""
    # This test will FAIL until we implement the endpoint
    response = client.post(
        f"/api/schools/{school.id}/classrooms",
        json={
            "name": "一年級 A 班",
            "description": "Test classroom",
            "level": "A1"
        },
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "一年級 A 班"
    assert data["level"] == "A1"
    assert data["teacher_id"] is None


def test_create_classroom_with_teacher_assignment(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: School admin can create classroom and assign teacher"""
    # Create another teacher to assign
    teacher = Teacher(email="teacher@test.com", name="Teacher", password_hash="hashed", is_active=True)
    db_session.add(teacher)
    db_session.commit()

    response = client.post(
        f"/api/schools/{school.id}/classrooms",
        json={
            "name": "一年級 B 班",
            "level": "A1",
            "teacher_id": teacher.id
        },
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["teacher_id"] == teacher.id


def test_create_classroom_without_permission_fails(db_session, school):
    """Test: Regular teacher cannot create classroom in school"""
    teacher = Teacher(email="regular@test.com", name="Regular", password_hash="hashed", is_active=True)
    db_session.add(teacher)
    db_session.commit()

    response = client.post(
        f"/api/schools/{school.id}/classrooms",
        json={"name": "Unauthorized", "level": "A1"},
        headers={"Authorization": f"Bearer {get_test_token(teacher.id)}"}
    )

    assert response.status_code == 403


def get_test_token(teacher_id: int) -> str:
    """Generate test JWT token"""
    from auth import create_access_token
    return create_access_token({"sub": str(teacher_id), "type": "teacher"})
```

**Step 2: Run tests to verify they fail**

Run:
```bash
cd backend
pytest tests/test_school_classrooms_api.py::test_create_classroom_without_teacher_assignment -v
```
Expected: FAIL with "404: Not Found" (endpoint doesn't exist)

**Step 3: Commit**

```bash
git add backend/tests/test_school_classrooms_api.py
git commit -m "test: add failing tests for POST /api/schools/{id}/classrooms"
```

---

## Task 4: Implement POST Endpoint (GREEN)

**Files:**
- Modify: `backend/routers/classroom_schools.py:398` (append)

**Step 1: Add POST endpoint**

At end of `backend/routers/classroom_schools.py`, add:

```python
@router.post(
    "/api/schools/{school_id}/classrooms",
    status_code=status.HTTP_201_CREATED,
    response_model=ClassroomInfo
)
async def create_school_classroom(
    school_id: uuid.UUID,
    classroom_data: SchoolClassroomCreate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Create a new classroom in school.
    Requires school_admin role or org-level manage_materials permission.
    """
    from utils.permissions import has_school_materials_permission
    from routers.schemas.classroom import SchoolClassroomCreate
    from models.base import ProgramLevel

    # Check permission
    if not has_school_materials_permission(teacher.id, school_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create classroom in this school"
        )

    # Verify school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )

    # Verify teacher exists if provided
    if classroom_data.teacher_id:
        assigned_teacher = db.query(Teacher).filter(
            Teacher.id == classroom_data.teacher_id,
            Teacher.is_active.is_(True)
        ).first()
        if not assigned_teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assigned teacher not found"
            )

    # Create classroom
    classroom = Classroom(
        name=classroom_data.name,
        description=classroom_data.description,
        level=getattr(ProgramLevel, classroom_data.level.upper(), ProgramLevel.A1),
        teacher_id=classroom_data.teacher_id,
        is_active=True
    )
    db.add(classroom)
    db.flush()  # Get classroom ID without committing

    # Link to school
    link = ClassroomSchool(
        classroom_id=classroom.id,
        school_id=school_id,
        is_active=True
    )
    db.add(link)
    db.commit()
    db.refresh(classroom)

    # Return with counts
    return ClassroomInfo.from_orm_with_counts(classroom, 0, 0)
```

**Step 2: Add import at top of file**

In `backend/routers/classroom_schools.py` after existing imports:

```python
from routers.schemas.classroom import SchoolClassroomCreate
```

**Step 3: Run tests**

Run:
```bash
pytest tests/test_school_classrooms_api.py::test_create_classroom_without_teacher_assignment -v
pytest tests/test_school_classrooms_api.py::test_create_classroom_with_teacher_assignment -v
pytest tests/test_school_classrooms_api.py::test_create_classroom_without_permission_fails -v
```
Expected: All tests PASS

**Step 4: Commit**

```bash
git add backend/routers/classroom_schools.py
git commit -m "feat: implement POST /api/schools/{id}/classrooms endpoint"
```

---

## Task 5: Write Tests for PUT Teacher Assignment (RED)

**Files:**
- Modify: `backend/tests/test_school_classrooms_api.py` (append)

**Step 1: Add tests**

Append to `backend/tests/test_school_classrooms_api.py`:

```python
def test_assign_teacher_to_classroom(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: Assign teacher to existing classroom"""
    # Create classroom without teacher
    classroom = Classroom(name="Test Class", level=ProgramLevel.A1, is_active=True)
    db_session.add(classroom)
    db_session.flush()

    # Link to school
    link = ClassroomSchool(classroom_id=classroom.id, school_id=school.id, is_active=True)
    db_session.add(link)
    db_session.commit()

    # Create teacher to assign
    teacher = Teacher(email="new@test.com", name="New Teacher", password_hash="hashed", is_active=True)
    db_session.add(teacher)
    db_session.commit()

    response = client.put(
        f"/api/classrooms/{classroom.id}/teacher",
        json={"teacher_id": teacher.id},
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["teacher_id"] == teacher.id


def test_unassign_teacher_from_classroom(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: Unassign teacher (set to null)"""
    teacher = Teacher(email="assigned@test.com", name="Assigned", password_hash="hashed", is_active=True)
    db_session.add(teacher)
    db_session.flush()

    classroom = Classroom(name="Test", level=ProgramLevel.A1, teacher_id=teacher.id, is_active=True)
    db_session.add(classroom)
    db_session.flush()

    link = ClassroomSchool(classroom_id=classroom.id, school_id=school.id, is_active=True)
    db_session.add(link)
    db_session.commit()

    response = client.put(
        f"/api/classrooms/{classroom.id}/teacher",
        json={"teacher_id": None},
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["teacher_id"] is None
```

**Step 2: Run tests**

Run:
```bash
pytest tests/test_school_classrooms_api.py::test_assign_teacher_to_classroom -v
```
Expected: FAIL with "404: Not Found"

**Step 3: Commit**

```bash
git add backend/tests/test_school_classrooms_api.py
git commit -m "test: add failing tests for PUT /api/classrooms/{id}/teacher"
```

---

## Task 6: Implement PUT Teacher Assignment (GREEN)

**Files:**
- Modify: `backend/routers/classroom_schools.py` (append)

**Step 1: Add endpoint**

Append to `backend/routers/classroom_schools.py`:

```python
@router.put(
    "/api/classrooms/{classroom_id}/teacher",
    response_model=ClassroomInfo
)
async def assign_teacher_to_classroom(
    classroom_id: int,
    request: AssignTeacherRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Assign or reassign teacher to classroom.
    Classroom must belong to a school.
    Requires school_admin or org-level permissions.
    """
    from utils.permissions import has_school_materials_permission
    from routers.schemas.classroom import AssignTeacherRequest

    # Get classroom and verify it belongs to a school
    link = db.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id == classroom_id,
        ClassroomSchool.is_active.is_(True)
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found in any school"
        )

    # Check permission
    if not has_school_materials_permission(teacher.id, link.school_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to assign teacher"
        )

    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )

    # Verify new teacher exists if provided
    if request.teacher_id:
        new_teacher = db.query(Teacher).filter(
            Teacher.id == request.teacher_id,
            Teacher.is_active.is_(True)
        ).first()
        if not new_teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Teacher not found"
            )

    # Update assignment
    classroom.teacher_id = request.teacher_id
    db.commit()
    db.refresh(classroom)

    # Get counts
    student_count = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).count()
    assignment_count = db.query(Assignment).filter(
        Assignment.classroom_id == classroom_id
    ).count()

    return ClassroomInfo.from_orm_with_counts(classroom, student_count, assignment_count)
```

**Step 2: Add import**

In `backend/routers/classroom_schools.py` imports:

```python
from routers.schemas.classroom import SchoolClassroomCreate, AssignTeacherRequest
```

**Step 3: Run tests**

Run:
```bash
pytest tests/test_school_classrooms_api.py::test_assign_teacher_to_classroom -v
pytest tests/test_school_classrooms_api.py::test_unassign_teacher_from_classroom -v
```
Expected: Both tests PASS

**Step 4: Commit**

```bash
git add backend/routers/classroom_schools.py
git commit -m "feat: implement PUT /api/classrooms/{id}/teacher endpoint"
```

---

## Task 7: Write Tests for PUT Classroom Update (RED)

**Files:**
- Modify: `backend/tests/test_school_classrooms_api.py` (append)

**Step 1: Add tests**

Append to test file:

```python
def test_update_classroom_details(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: Update classroom name, level, description"""
    classroom = Classroom(
        name="Old Name",
        description="Old description",
        level=ProgramLevel.A1,
        is_active=True
    )
    db_session.add(classroom)
    db_session.flush()

    link = ClassroomSchool(classroom_id=classroom.id, school_id=school.id, is_active=True)
    db_session.add(link)
    db_session.commit()

    response = client.put(
        f"/api/classrooms/{classroom.id}",
        json={
            "name": "New Name",
            "description": "New description",
            "level": "A2"
        },
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["program_level"] == "A2"


def test_deactivate_classroom(
    db_session, school_admin_teacher, school, link_teacher_to_school
):
    """Test: Deactivate classroom"""
    classroom = Classroom(name="Active", level=ProgramLevel.A1, is_active=True)
    db_session.add(classroom)
    db_session.flush()

    link = ClassroomSchool(classroom_id=classroom.id, school_id=school.id, is_active=True)
    db_session.add(link)
    db_session.commit()

    response = client.put(
        f"/api/classrooms/{classroom.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
```

**Step 2: Run tests**

Run:
```bash
pytest tests/test_school_classrooms_api.py::test_update_classroom_details -v
```
Expected: FAIL with "404: Not Found"

**Step 3: Commit**

```bash
git add backend/tests/test_school_classrooms_api.py
git commit -m "test: add failing tests for PUT /api/classrooms/{id}"
```

---

## Task 8: Implement PUT Classroom Update (GREEN)

**Files:**
- Modify: `backend/routers/classroom_schools.py` (append)

**Step 1: Add endpoint**

Append to `backend/routers/classroom_schools.py`:

```python
@router.put(
    "/api/classrooms/{classroom_id}",
    response_model=ClassroomInfo
)
async def update_classroom(
    classroom_id: int,
    update_data: SchoolClassroomUpdate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Update classroom details.
    Classroom must belong to a school.
    Requires school_admin or org-level permissions.
    """
    from utils.permissions import has_school_materials_permission
    from routers.schemas.classroom import SchoolClassroomUpdate
    from models.base import ProgramLevel

    # Get classroom and verify it belongs to a school
    link = db.query(ClassroomSchool).filter(
        ClassroomSchool.classroom_id == classroom_id,
        ClassroomSchool.is_active.is_(True)
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found in any school"
        )

    # Check permission
    if not has_school_materials_permission(teacher.id, link.school_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update classroom"
        )

    classroom = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Classroom not found"
        )

    # Update fields
    if update_data.name is not None:
        classroom.name = update_data.name
    if update_data.description is not None:
        classroom.description = update_data.description
    if update_data.level is not None:
        classroom.level = getattr(ProgramLevel, update_data.level.upper(), classroom.level)
    if update_data.is_active is not None:
        classroom.is_active = update_data.is_active

    db.commit()
    db.refresh(classroom)

    # Get counts
    student_count = db.query(ClassroomStudent).filter(
        ClassroomStudent.classroom_id == classroom_id
    ).count()
    assignment_count = db.query(Assignment).filter(
        Assignment.classroom_id == classroom_id
    ).count()

    return ClassroomInfo.from_orm_with_counts(classroom, student_count, assignment_count)
```

**Step 2: Add import**

In imports:

```python
from routers.schemas.classroom import (
    SchoolClassroomCreate,
    SchoolClassroomUpdate,
    AssignTeacherRequest
)
```

**Step 3: Run all tests**

Run:
```bash
pytest tests/test_school_classrooms_api.py -v
```
Expected: All 8 tests PASS

**Step 4: Commit**

```bash
git add backend/routers/classroom_schools.py
git commit -m "feat: implement PUT /api/classrooms/{id} endpoint"
```

---

## Task 9: Integration Test

**Files:**
- Create: `backend/tests/test_classroom_workflow.py`

**Step 1: Create end-to-end workflow test**

Create `backend/tests/test_classroom_workflow.py`:

```python
"""End-to-end workflow test for school classroom management"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from main import app
from models import Teacher, School, TeacherSchool, Organization, TeacherOrganization
from database import get_db


client = TestClient(app)


def test_complete_classroom_lifecycle():
    """
    Test complete classroom lifecycle:
    1. Create classroom without teacher
    2. Assign teacher
    3. Update details
    4. Reassign to different teacher
    5. Deactivate
    """
    db = next(get_db())

    # Setup: Create organization, school, and admin
    org_id = uuid.uuid4()
    org = Organization(id=org_id, name="Test Org", is_active=True)
    db.add(org)

    school_id = uuid.uuid4()
    school = School(id=school_id, organization_id=org_id, name="Test School", is_active=True)
    db.add(school)

    admin = Teacher(email="admin@test.com", name="Admin", password_hash="hashed", is_active=True)
    db.add(admin)
    db.flush()

    # Link admin to org and school
    org_link = TeacherOrganization(
        teacher_id=admin.id, organization_id=org_id, role="org_owner", is_active=True
    )
    school_link = TeacherSchool(
        teacher_id=admin.id, school_id=school_id, roles=["school_admin"], is_active=True
    )
    db.add_all([org_link, school_link])

    # Create teachers to assign
    teacher1 = Teacher(email="t1@test.com", name="Teacher 1", password_hash="hashed", is_active=True)
    teacher2 = Teacher(email="t2@test.com", name="Teacher 2", password_hash="hashed", is_active=True)
    db.add_all([teacher1, teacher2])
    db.commit()

    token = get_test_token(admin.id)

    # Step 1: Create classroom without teacher
    response = client.post(
        f"/api/schools/{school_id}/classrooms",
        json={"name": "一年級 A 班", "level": "A1"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    classroom_id = response.json()["id"]

    # Step 2: Assign teacher1
    response = client.put(
        f"/api/classrooms/{classroom_id}/teacher",
        json={"teacher_id": teacher1.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["teacher_id"] == teacher1.id

    # Step 3: Update details
    response = client.put(
        f"/api/classrooms/{classroom_id}",
        json={"name": "一年級 A 班（進階）", "level": "A2"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "一年級 A 班（進階）"
    assert data["program_level"] == "A2"

    # Step 4: Reassign to teacher2
    response = client.put(
        f"/api/classrooms/{classroom_id}/teacher",
        json={"teacher_id": teacher2.id},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["teacher_id"] == teacher2.id

    # Step 5: Deactivate
    response = client.put(
        f"/api/classrooms/{classroom_id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False

    # Verify classroom not in active list
    response = client.get(
        f"/api/schools/{school_id}/classrooms",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    active_classrooms = response.json()
    assert classroom_id not in [c["id"] for c in active_classrooms]

    db.rollback()


def get_test_token(teacher_id: int) -> str:
    from auth import create_access_token
    return create_access_token({"sub": str(teacher_id), "type": "teacher"})
```

**Step 2: Run workflow test**

Run:
```bash
pytest tests/test_classroom_workflow.py -v
```
Expected: PASS

**Step 3: Commit**

```bash
git add backend/tests/test_classroom_workflow.py
git commit -m "test: add end-to-end workflow test for classroom management"
```

---

## Task 10: Manual API Testing

**Files:**
- None (manual testing)

**Step 1: Start server**

Run:
```bash
cd backend
uvicorn main:app --reload
```

**Step 2: Test with curl**

```bash
# Get auth token (replace with real credentials)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/teacher/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@duotopia.com","password":"your_password"}' \
  | jq -r .access_token)

# Create classroom
curl -X POST "http://localhost:8000/api/schools/{SCHOOL_UUID}/classrooms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試班級",
    "description": "API 測試",
    "level": "A1"
  }'

# Assign teacher
curl -X PUT "http://localhost:8000/api/classrooms/{CLASSROOM_ID}/teacher" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"teacher_id": 123}'

# Update classroom
curl -X PUT "http://localhost:8000/api/classrooms/{CLASSROOM_ID}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "測試班級（更新）",
    "level": "A2"
  }'
```

**Step 3: Verify responses**

Expected:
- POST returns 201 with classroom data
- PUT /teacher returns 200 with updated teacher_id
- PUT returns 200 with updated fields

---

## Summary

**Endpoints Created:**
1. `POST /api/schools/{school_id}/classrooms` - Create classroom
2. `PUT /api/classrooms/{classroom_id}/teacher` - Assign/reassign teacher
3. `PUT /api/classrooms/{classroom_id}` - Update classroom details

**Key Features:**
- School admins can create classrooms before assigning teachers
- Proper permission checks using existing `has_school_materials_permission`
- Automatic linking to school via `ClassroomSchool`
- Full CRUD with activation/deactivation support

**Next Steps:**
- Frontend integration (SchoolClassroomsPage)
- Add teacher assignment dropdown in UI
- Add classroom creation dialog
