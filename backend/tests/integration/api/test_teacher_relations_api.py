"""
Integration tests for Teacher Relationship Management API

Tests for managing teacher-organization and teacher-school relationships with Casbin sync.
"""

import pytest
from sqlalchemy.orm import Session
import uuid

from models import Teacher, Organization, School, TeacherOrganization, TeacherSchool
from auth import create_access_token
from services.casbin_service import get_casbin_service


@pytest.fixture
def owner_teacher(shared_test_session: Session):
    """Create org owner teacher"""
    teacher = Teacher(
        email=f"owner_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$test_hash",
        name="Owner Teacher",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def member_teacher(shared_test_session: Session):
    """Create member teacher (to be added to org/school)"""
    teacher = Teacher(
        email=f"member_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$test_hash",
        name="Member Teacher",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def owner_headers(owner_teacher: Teacher):
    """Auth headers for owner"""
    token = create_access_token({"sub": str(owner_teacher.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_org(shared_test_session: Session, owner_teacher: Teacher):
    """Create test organization with owner"""
    casbin_service = get_casbin_service()

    org = Organization(name="Test Org", is_active=True)
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    # Add owner
    teacher_org = TeacherOrganization(
        teacher_id=owner_teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(teacher_org)
    shared_test_session.commit()

    casbin_service.add_role_for_user(owner_teacher.id, "org_owner", f"org-{org.id}")
    return org


@pytest.fixture
def test_school(shared_test_session: Session, test_org: Organization):
    """Create test school"""
    school = School(
        organization_id=test_org.id,
        name="Test School",
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    return school


class TestAddTeacherToOrganization:
    """Tests for POST /api/organizations/{org_id}/teachers"""

    def test_add_org_admin_success(self, test_client, owner_headers, test_org: Organization, member_teacher: Teacher, shared_test_session: Session):
        """Test adding org_admin successfully"""
        response = test_client.post(
            f"/api/organizations/{test_org.id}/teachers",
            json={
                "teacher_id": member_teacher.id,
                "role": "org_admin"
            },
            headers=owner_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["teacher_id"] == member_teacher.id
        assert data["role"] == "org_admin"

        # Verify in database
        rel = shared_test_session.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == member_teacher.id,
            TeacherOrganization.organization_id == test_org.id
        ).first()
        assert rel is not None
        assert rel.role == "org_admin"

        # Verify Casbin role
        casbin_service = get_casbin_service()
        assert casbin_service.has_role(member_teacher.id, "org_admin", f"org-{test_org.id}")

    def test_add_second_org_owner_fails(self, test_client, owner_headers, test_org: Organization, member_teacher: Teacher):
        """Test that adding second org_owner fails"""
        response = test_client.post(
            f"/api/organizations/{test_org.id}/teachers",
            json={
                "teacher_id": member_teacher.id,
                "role": "org_owner"
            },
            headers=owner_headers,
        )

        assert response.status_code == 400
        assert "already has an owner" in response.json()["detail"]

    def test_add_teacher_duplicate_fails(self, test_client, owner_headers, test_org: Organization, member_teacher: Teacher, shared_test_session: Session):
        """Test that adding same teacher twice fails"""
        # Add first time
        teacher_org = TeacherOrganization(
            teacher_id=member_teacher.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(teacher_org)
        shared_test_session.commit()

        # Try to add again
        response = test_client.post(
            f"/api/organizations/{test_org.id}/teachers",
            json={
                "teacher_id": member_teacher.id,
                "role": "org_admin"
            },
            headers=owner_headers,
        )

        assert response.status_code == 400


class TestRemoveTeacherFromOrganization:
    """Tests for DELETE /api/organizations/{org_id}/teachers/{teacher_id}"""

    def test_remove_org_admin_success(self, test_client, owner_headers, test_org: Organization, member_teacher: Teacher, shared_test_session: Session):
        """Test removing org_admin successfully"""
        casbin_service = get_casbin_service()

        # Add org_admin first
        teacher_org = TeacherOrganization(
            teacher_id=member_teacher.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(teacher_org)
        shared_test_session.commit()
        casbin_service.add_role_for_user(member_teacher.id, "org_admin", f"org-{test_org.id}")

        # Remove
        response = test_client.delete(
            f"/api/organizations/{test_org.id}/teachers/{member_teacher.id}",
            headers=owner_headers,
        )

        assert response.status_code == 200

        # Verify soft delete in database
        shared_test_session.refresh(teacher_org)
        assert teacher_org.is_active is False

        # Verify Casbin role removed
        assert not casbin_service.has_role(member_teacher.id, "org_admin", f"org-{test_org.id}")


class TestAddTeacherToSchool:
    """Tests for POST /api/schools/{school_id}/teachers"""

    def test_add_school_admin_success(self, test_client, owner_headers, test_school: School, member_teacher: Teacher, shared_test_session: Session):
        """Test adding school_admin successfully"""
        response = test_client.post(
            f"/api/schools/{test_school.id}/teachers",
            json={
                "teacher_id": member_teacher.id,
                "roles": ["school_admin"]
            },
            headers=owner_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["teacher_id"] == member_teacher.id
        assert "school_admin" in data["roles"]

        # Verify in database
        rel = shared_test_session.query(TeacherSchool).filter(
            TeacherSchool.teacher_id == member_teacher.id,
            TeacherSchool.school_id == test_school.id
        ).first()
        assert rel is not None
        assert "school_admin" in rel.roles

        # Verify Casbin role
        casbin_service = get_casbin_service()
        assert casbin_service.has_role(member_teacher.id, "school_admin", f"school-{test_school.id}")

    def test_add_teacher_with_multiple_roles(self, test_client, owner_headers, test_school: School, member_teacher: Teacher, shared_test_session: Session):
        """Test adding teacher with multiple roles"""
        response = test_client.post(
            f"/api/schools/{test_school.id}/teachers",
            json={
                "teacher_id": member_teacher.id,
                "roles": ["school_admin", "teacher"]
            },
            headers=owner_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "school_admin" in data["roles"]
        assert "teacher" in data["roles"]

        # Verify Casbin roles
        casbin_service = get_casbin_service()
        assert casbin_service.has_role(member_teacher.id, "school_admin", f"school-{test_school.id}")
        assert casbin_service.has_role(member_teacher.id, "teacher", f"school-{test_school.id}")


class TestUpdateTeacherSchoolRoles:
    """Tests for PATCH /api/schools/{school_id}/teachers/{teacher_id}"""

    def test_update_roles_success(self, test_client, owner_headers, test_school: School, member_teacher: Teacher, shared_test_session: Session):
        """Test updating teacher roles successfully"""
        casbin_service = get_casbin_service()

        # Add teacher first
        teacher_school = TeacherSchool(
            teacher_id=member_teacher.id,
            school_id=test_school.id,
            roles=["teacher"],
            is_active=True,
        )
        shared_test_session.add(teacher_school)
        shared_test_session.commit()
        casbin_service.add_role_for_user(member_teacher.id, "teacher", f"school-{test_school.id}")

        # Update to school_admin
        response = test_client.patch(
            f"/api/schools/{test_school.id}/teachers/{member_teacher.id}",
            json={"roles": ["school_admin", "teacher"]},
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "school_admin" in data["roles"]
        assert "teacher" in data["roles"]

        # Verify Casbin roles updated
        assert casbin_service.has_role(member_teacher.id, "school_admin", f"school-{test_school.id}")
        assert casbin_service.has_role(member_teacher.id, "teacher", f"school-{test_school.id}")


class TestRemoveTeacherFromSchool:
    """Tests for DELETE /api/schools/{school_id}/teachers/{teacher_id}"""

    def test_remove_teacher_success(self, test_client, owner_headers, test_school: School, member_teacher: Teacher, shared_test_session: Session):
        """Test removing teacher from school successfully"""
        casbin_service = get_casbin_service()

        # Add teacher first
        teacher_school = TeacherSchool(
            teacher_id=member_teacher.id,
            school_id=test_school.id,
            roles=["teacher"],
            is_active=True,
        )
        shared_test_session.add(teacher_school)
        shared_test_session.commit()
        casbin_service.add_role_for_user(member_teacher.id, "teacher", f"school-{test_school.id}")

        # Remove
        response = test_client.delete(
            f"/api/schools/{test_school.id}/teachers/{member_teacher.id}",
            headers=owner_headers,
        )

        assert response.status_code == 200

        # Verify soft delete
        shared_test_session.refresh(teacher_school)
        assert teacher_school.is_active is False

        # Verify Casbin role removed
        assert not casbin_service.has_role(member_teacher.id, "teacher", f"school-{test_school.id}")
