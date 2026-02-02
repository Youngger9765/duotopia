"""
TDD Tests for School Scope - Unified Programs API

RED Phase: Write failing tests for school scope support
Following TDD RED-GREEN-REFACTOR cycle

Test Coverage:
- GET /api/programs?scope=school&school_id={id}
- POST /api/programs?scope=school&school_id={id}
"""

import os
import secrets
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from models import Teacher, Organization, School, TeacherSchool, Program
from auth import get_password_hash
from main import app


TEST_PASSWORD = os.environ.get("TEST_TEACHER_PASSWORD") or secrets.token_urlsafe(24)


@pytest.fixture
def school_admin_client(shared_test_session, school_admin_user):
    """Create test client authenticated as school_admin"""
    from routers.programs import get_current_teacher
    from database import get_db

    async def override_get_current_teacher():
        return school_admin_user

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
def school_admin_user(shared_test_session: Session):
    """Create school admin teacher"""
    teacher = Teacher(
        email=f"school_admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash(TEST_PASSWORD),
        name="School Admin",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_organization(shared_test_session: Session):
    """Create test organization"""
    org = Organization(
        id=uuid.uuid4(),
        name=f"Test Org {uuid.uuid4().hex[:6]}",
        display_name="Test Organization",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)
    return org


@pytest.fixture
def test_school(shared_test_session: Session, test_organization):
    """Create test school"""
    school = School(
        id=uuid.uuid4(),
        organization_id=test_organization.id,
        name=f"Test School {uuid.uuid4().hex[:6]}",
        display_name="Test School",
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    return school


@pytest.fixture
def school_admin_membership(
    shared_test_session: Session, school_admin_user, test_school
):
    """Create school admin membership"""
    membership = TeacherSchool(
        teacher_id=school_admin_user.id,
        school_id=test_school.id,
        roles=["school_admin"],
        is_active=True,
    )
    shared_test_session.add(membership)
    shared_test_session.commit()
    shared_test_session.refresh(membership)
    return membership


@pytest.fixture
def school_program(shared_test_session: Session, test_school, school_admin_user):
    """Create a school-scoped program for testing"""
    program = Program(
        name="School Program",
        description="Program for school",
        is_template=True,
        teacher_id=school_admin_user.id,
        school_id=test_school.id,
        organization_id=test_school.organization_id,
        is_active=True,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)
    return program


class TestSchoolScope:
    """Test school-scoped program operations"""

    def test_get_school_programs_with_scope(
        self,
        school_admin_client: TestClient,
        shared_test_session: Session,
        school_admin_membership,
        test_school,
        school_program,
    ):
        """
        RED: Test GET /api/programs?scope=school&school_id={id}

        Expected to FAIL: Backend doesn't support scope=school yet
        """
        response = school_admin_client.get(
            f"/api/programs?scope=school&school_id={test_school.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Verify school program is returned
        program_ids = [p["id"] for p in data]
        assert school_program.id in program_ids

        # Verify all returned programs belong to school
        for program in data:
            assert program.get("school_id") == str(test_school.id)

    def test_create_school_program_with_scope(
        self,
        school_admin_client: TestClient,
        shared_test_session: Session,
        school_admin_user,
        school_admin_membership,
        test_school,
    ):
        """
        RED: Test POST /api/programs with scope=school creates school program

        Expected to FAIL: Backend doesn't support scope=school yet
        """
        response = school_admin_client.post(
            f"/api/programs?scope=school&school_id={test_school.id}",
            json={"name": "New School Program", "description": "Created for school"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New School Program"
        assert data["school_id"] == str(test_school.id)
        assert data["organization_id"] == str(test_school.organization_id)
        assert data["is_template"] is True

        # Verify in database
        program = (
            shared_test_session.query(Program).filter(Program.id == data["id"]).first()
        )
        assert program is not None
        assert str(program.school_id) == str(test_school.id)
        assert str(program.organization_id) == str(test_school.organization_id)

    def test_school_teacher_cannot_manage_school_materials(
        self, school_admin_client: TestClient, shared_test_session: Session, test_school
    ):
        """
        RED: Test regular teacher (without school_admin role) cannot create school programs

        Expected to FAIL initially, then pass after permission check is added
        """
        # Create a regular teacher (no school_admin role)
        teacher = Teacher(
            email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash(TEST_PASSWORD),
            name="Regular Teacher",
            is_active=True,
        )
        shared_test_session.add(teacher)
        shared_test_session.commit()
        shared_test_session.refresh(teacher)

        # Create membership without school_admin role
        membership = TeacherSchool(
            teacher_id=teacher.id,
            school_id=test_school.id,
            roles=["teacher"],
            is_active=True,
        )
        shared_test_session.add(membership)
        shared_test_session.commit()

        # Override to use regular teacher
        from routers.programs import get_current_teacher
        from database import get_db

        async def override_get_current_teacher():
            return teacher

        def override_get_db():
            try:
                yield shared_test_session
            finally:
                pass

        app.dependency_overrides[get_current_teacher] = override_get_current_teacher
        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                response = client.post(
                    f"/api/programs?scope=school&school_id={test_school.id}",
                    json={"name": "Unauthorized Program", "description": "Should fail"},
                )

                assert response.status_code == 403
                assert "permission" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
