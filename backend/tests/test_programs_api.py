"""
Comprehensive TDD Tests for Unified Programs API

Test Coverage: Unified Programs API with scope parameter (teacher|organization)
Following TDD RED-GREEN-REFACTOR cycle

API Design:
- GET    /api/programs?scope={teacher|organization}&organization_id={id}
- POST   /api/programs
- PUT    /api/programs/{program_id}
- DELETE /api/programs/{program_id}
- POST   /api/programs/{program_id}/lessons
- PUT    /api/lessons/{lesson_id}
- DELETE /api/lessons/{lesson_id}
- POST   /api/lessons/{lesson_id}/contents
- DELETE /api/contents/{content_id}

Test Strategy:
- Test teacher scope isolation
- Test organization scope with permissions
- Test cross-scope access denial
- Test lesson/content CRUD with automatic permission checking
- Coverage target: >70%
"""

import os
import secrets
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from models import (
    Teacher,
    Organization,
    TeacherOrganization,
    Program,
    Lesson,
    Content,
    ContentItem,
    ContentType,
    Classroom,
)
from auth import create_access_token, get_password_hash
from services.casbin_service import get_casbin_service
from main import app


# ============================================================================
# Fixtures
# ============================================================================

TEST_PASSWORD = os.environ.get("TEST_TEACHER_PASSWORD") or secrets.token_urlsafe(24)

@pytest.fixture
def test_db(shared_test_session: Session):
    """Provide test database session"""
    return shared_test_session


@pytest.fixture
def authenticated_client(shared_test_session, teacher_user):
    """Create test client with authentication dependency override for teacher_user"""
    from routers.programs import get_current_teacher
    from database import get_db

    # Override get_current_teacher to return the test teacher directly
    async def override_get_current_teacher():
        return teacher_user

    # Override get_db to use shared test session
    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    # Apply overrides
    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


@pytest.fixture
def org_owner_client(shared_test_session, org_owner_user):
    """Create test client authenticated as org_owner"""
    from routers.programs import get_current_teacher
    from database import get_db

    async def override_get_current_teacher():
        return org_owner_user

    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def org_admin_client(shared_test_session, org_admin_user):
    """Create test client authenticated as org_admin"""
    from routers.programs import get_current_teacher
    from database import get_db

    async def override_get_current_teacher():
        return org_admin_user

    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def teacher_user(test_db: Session):
    """Create a regular teacher user"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        name="Teacher User",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_owner_user(test_db: Session):
    """Create organization owner teacher"""
    teacher = Teacher(
        email=f"org_owner_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        name="Org Owner",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin_user(test_db: Session):
    """Create org admin teacher"""
    teacher = Teacher(
        email=f"org_admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        name="Org Admin",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def test_organization(test_db: Session):
    """Create test organization"""
    org = Organization(
        id=uuid.uuid4(),
        name=f"Test Org {uuid.uuid4().hex[:6]}",
        display_name="Test Organization",
        type="school_group",
        is_active=True,
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org


@pytest.fixture
def org_owner_membership(test_db: Session, org_owner_user, test_organization):
    """Create org_owner membership"""
    membership = TeacherOrganization(
        teacher_id=org_owner_user.id,
        organization_id=test_organization.id,
        role="org_owner",
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()
    test_db.refresh(membership)
    return membership


@pytest.fixture
def org_admin_membership(test_db: Session, org_admin_user, test_organization):
    """Create org_admin membership with manage_materials permission"""
    membership = TeacherOrganization(
        teacher_id=org_admin_user.id,
        organization_id=test_organization.id,
        role="org_admin",
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()

    # Grant manage_materials permission
    casbin = get_casbin_service()
    casbin.add_permission(
        teacher_id=org_admin_user.id,
        domain=f"org-{test_organization.id}",
        resource="manage_materials",
        action="write",
    )

    test_db.refresh(membership)
    return membership


@pytest.fixture
def teacher_token(teacher_user):
    """Generate auth token for teacher"""
    return create_access_token(data={"sub": teacher_user.id, "type": "teacher"})


@pytest.fixture
def org_owner_token(org_owner_user):
    """Generate auth token for org owner"""
    return create_access_token(data={"sub": org_owner_user.id, "type": "teacher"})


@pytest.fixture
def org_admin_token(org_admin_user):
    """Generate auth token for org admin"""
    return create_access_token(data={"sub": org_admin_user.id, "type": "teacher"})


@pytest.fixture
def teacher_program(test_db: Session, teacher_user):
    """Create a teacher-owned program"""
    program = Program(
        name="Teacher's Program",
        description="Personal teaching material",
        is_template=True,
        teacher_id=teacher_user.id,
        organization_id=None,
        classroom_id=None,
        is_active=True,
    )
    test_db.add(program)
    test_db.commit()
    test_db.refresh(program)
    return program


@pytest.fixture
def org_program(test_db: Session, org_owner_user, test_organization):
    """Create an organization-owned program"""
    program = Program(
        name="Organization's Program",
        description="Organizational teaching material",
        is_template=True,
        teacher_id=org_owner_user.id,
        organization_id=test_organization.id,
        classroom_id=None,
        is_active=True,
    )
    test_db.add(program)
    test_db.commit()
    test_db.refresh(program)
    return program


@pytest.fixture
def program_with_lesson(test_db: Session, teacher_user):
    """Create a program with a lesson"""
    program = Program(
        name="Program with Lesson",
        description="Test program",
        is_template=True,
        teacher_id=teacher_user.id,
        is_active=True,
    )
    test_db.add(program)
    test_db.flush()

    lesson = Lesson(
        program_id=program.id,
        name="Test Lesson",
        description="Test lesson description",
        order_index=1,
        is_active=True,
    )
    test_db.add(lesson)
    test_db.commit()
    test_db.refresh(program)
    test_db.refresh(lesson)

    program._lesson = lesson  # Attach for easy access
    return program


@pytest.fixture
def lesson_with_content(test_db: Session, teacher_user):
    """Create a lesson with content"""
    program = Program(
        name="Program",
        is_template=True,
        teacher_id=teacher_user.id,
        is_active=True,
    )
    test_db.add(program)
    test_db.flush()

    lesson = Lesson(
        program_id=program.id,
        name="Lesson",
        order_index=1,
        is_active=True,
    )
    test_db.add(lesson)
    test_db.flush()

    content = Content(
        lesson_id=lesson.id,
        type=ContentType.VOCABULARY,
        title="Test Content",
        order_index=1,
        is_active=True,
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(lesson)
    test_db.refresh(content)

    lesson._content = content  # Attach for easy access
    lesson._program = program
    return lesson


# ============================================================================
# Phase 1: Teacher Scope Tests
# ============================================================================


class TestTeacherScope:
    """Test teacher-scoped program operations"""

    def test_get_teacher_programs_with_scope(self, authenticated_client: TestClient, test_db: Session, teacher_program):
        """Test GET /api/programs?scope=teacher returns only teacher's programs"""
        response = authenticated_client.get(
            "/api/programs?scope=teacher"
        )

        print(f"\n=== RESPONSE STATUS: {response.status_code} ===")
        print(f"=== RESPONSE BODY: {response.json()} ===")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Verify returned program belongs to teacher
        program_ids = [p["id"] for p in data]
        assert teacher_program.id in program_ids

        # Verify no organization programs returned
        for program in data:
            assert program.get("organization_id") is None

    def test_create_teacher_program_with_scope(self, authenticated_client: TestClient, test_db: Session, teacher_user):
        """Test POST /api/programs with scope=teacher creates teacher program"""
        response = authenticated_client.post(
            "/api/programs?scope=teacher",
            json={
                "name": "New Teacher Program",
                "description": "Created via API"
            }
        )

        assert response.status_code == 201
        data = response.json()
        print(f"\n=== RESPONSE DATA ===")
        print(f"Keys: {data.keys()}")
        print(f"Data: {data}")
        assert data["name"] == "New Teacher Program"
        assert data["teacher_id"] == teacher_user.id
        assert data.get("organization_id") is None
        assert data.get("is_template") is True

        # Verify in database
        program = test_db.query(Program).filter(Program.id == data["id"]).first()
        assert program is not None
        assert program.teacher_id == teacher_user.id
        assert program.organization_id is None

    def test_teacher_cannot_access_org_programs(self, authenticated_client: TestClient, test_db: Session, org_program):
        """Test teacher cannot access organization programs via teacher scope"""
        response = authenticated_client.get(
            "/api/programs?scope=teacher"
        )

        assert response.status_code == 200
        data = response.json()

        # Organization program should NOT be in teacher's list
        program_ids = [p["id"] for p in data]
        assert org_program.id not in program_ids


# ============================================================================
# Phase 2: Organization Scope Tests
# ============================================================================


class TestOrganizationScope:
    """Test organization-scoped program operations"""

    def test_get_org_programs_with_scope(
        self,
        org_owner_client: TestClient,
        test_db: Session,
        org_owner_membership,
        test_organization,
        org_program
    ):
        """Test GET /api/programs?scope=organization&organization_id={id}"""
        response = org_owner_client.get(
            f"/api/programs?scope=organization&organization_id={test_organization.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Verify org program is returned
        program_ids = [p["id"] for p in data]
        assert org_program.id in program_ids

        # Verify all returned programs belong to organization
        for program in data:
            assert program.get("organization_id") == str(test_organization.id)

    def test_create_org_program_with_scope(
        self,
        test_client: TestClient,
        test_db: Session,
        org_owner_token,
        org_owner_user,
        org_owner_membership,
        test_organization
    ):
        """Test POST /api/programs with scope=organization creates org program"""
        response = test_client.post(
            f"/api/programs?scope=organization&organization_id={test_organization.id}",
            headers={"Authorization": f"Bearer {org_owner_token}"},
            json={
                "name": "New Org Program",
                "description": "Created for organization"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Org Program"
        assert data["organization_id"] == str(test_organization.id)
        assert data["is_template"] is True

        # Verify in database
        program = test_db.query(Program).filter(Program.id == data["id"]).first()
        assert program is not None
        assert program.organization_id == test_organization.id

    def test_org_admin_can_manage_org_materials(
        self,
        test_client: TestClient,
        test_db: Session,
        org_admin_token,
        org_admin_membership,
        test_organization
    ):
        """Test org_admin with manage_materials permission can create programs"""
        response = test_client.post(
            f"/api/programs?scope=organization&organization_id={test_organization.id}",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={
                "name": "Admin Created Program",
                "description": "Created by org admin"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Admin Created Program"

    def test_teacher_cannot_manage_org_materials(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        test_organization
    ):
        """Test regular teacher cannot create organization programs"""
        response = test_client.post(
            f"/api/programs?scope=organization&organization_id={test_organization.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "name": "Unauthorized Program",
                "description": "Should fail"
            }
        )

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


# ============================================================================
# Phase 3: Lesson CRUD Tests (scope-agnostic)
# ============================================================================


class TestLessonCRUD:
    """Test lesson CRUD operations with automatic permission checking"""

    def test_create_lesson_in_teacher_program(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        teacher_program
    ):
        """Test POST /api/programs/{program_id}/lessons for teacher program"""
        response = test_client.post(
            f"/api/programs/{teacher_program.id}/lessons",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "name": "New Lesson",
                "description": "Test lesson",
                "order_index": 1
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Lesson"
        assert data["program_id"] == teacher_program.id

        # Verify in database
        lesson = test_db.query(Lesson).filter(Lesson.id == data["id"]).first()
        assert lesson is not None
        assert lesson.program_id == teacher_program.id

    def test_create_lesson_in_org_program(
        self,
        test_client: TestClient,
        test_db: Session,
        org_owner_token,
        org_owner_membership,
        org_program
    ):
        """Test POST /api/programs/{program_id}/lessons for org program"""
        response = test_client.post(
            f"/api/programs/{org_program.id}/lessons",
            headers={"Authorization": f"Bearer {org_owner_token}"},
            json={
                "name": "Org Lesson",
                "description": "Lesson in org program",
                "order_index": 1
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Org Lesson"

    def test_update_lesson_checks_program_permission(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        program_with_lesson
    ):
        """Test PUT /api/lessons/{lesson_id} checks program ownership"""
        lesson = program_with_lesson._lesson

        response = test_client.put(
            f"/api/lessons/{lesson.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "name": "Updated Lesson",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Lesson"

    def test_delete_lesson_checks_program_permission(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        program_with_lesson
    ):
        """Test DELETE /api/lessons/{lesson_id} checks program ownership"""
        lesson = program_with_lesson._lesson

        response = test_client.delete(
            f"/api/lessons/{lesson.id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 200

        # Verify soft delete
        deleted_lesson = test_db.query(Lesson).filter(Lesson.id == lesson.id).first()
        assert deleted_lesson.is_active is False


# ============================================================================
# Phase 4: Content CRUD Tests (scope-agnostic)
# ============================================================================


class TestContentCRUD:
    """Test content CRUD operations with automatic permission checking"""

    def test_create_content_in_lesson(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        program_with_lesson
    ):
        """Test POST /api/lessons/{lesson_id}/contents"""
        lesson = program_with_lesson._lesson

        response = test_client.post(
            f"/api/lessons/{lesson.id}/contents",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={
                "type": "vocabulary",
                "title": "New Content",
                "order_index": 1
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Content"
        assert data["lesson_id"] == lesson.id

    def test_delete_content_checks_lesson_program_permission(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        lesson_with_content
    ):
        """Test DELETE /api/contents/{content_id} checks lesson->program permission"""
        content = lesson_with_content._content

        response = test_client.delete(
            f"/api/contents/{content.id}",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 200

        # Verify soft delete
        deleted_content = test_db.query(Content).filter(Content.id == content.id).first()
        assert deleted_content.is_active is False


# ============================================================================
# Phase 5: Cross-Permission Tests
# ============================================================================


class TestCrossPermissionDenial:
    """Test that users cannot access resources they don't own"""

    def test_teacher_cannot_update_org_program(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        org_program
    ):
        """Test teacher cannot update organization program"""
        response = test_client.put(
            f"/api/programs/{org_program.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"name": "Hacked Program"}
        )

        assert response.status_code == 403

    def test_teacher_cannot_create_lesson_in_org_program(
        self,
        test_client: TestClient,
        test_db: Session,
        teacher_token,
        org_program
    ):
        """Test teacher cannot create lesson in organization program"""
        response = test_client.post(
            f"/api/programs/{org_program.id}/lessons",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json={"name": "Unauthorized Lesson", "order_index": 1}
        )

        assert response.status_code == 403


# ============================================================================
# Phase 6: Edge Cases and Validation
# ============================================================================


class TestEdgeCases:
    """Test edge cases and validation"""

    def test_missing_scope_parameter_returns_400(self, test_client: TestClient, teacher_token):
        """Test GET /api/programs without scope parameter returns 400"""
        response = test_client.get(
            "/api/programs",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 400
        assert "scope" in response.json()["detail"].lower()

    def test_organization_scope_requires_org_id(self, test_client: TestClient, org_owner_token):
        """Test scope=organization requires organization_id parameter"""
        response = test_client.get(
            "/api/programs?scope=organization",
            headers={"Authorization": f"Bearer {org_owner_token}"}
        )

        assert response.status_code == 400
        assert "organization_id" in response.json()["detail"].lower()

    def test_invalid_scope_returns_400(self, test_client: TestClient, teacher_token):
        """Test invalid scope value returns 400"""
        response = test_client.get(
            "/api/programs?scope=invalid",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )

        assert response.status_code == 400
