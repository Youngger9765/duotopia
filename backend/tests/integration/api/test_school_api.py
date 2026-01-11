"""
Integration tests for School API

Tests for CRUD operations on schools with Casbin permission checks.
"""

import pytest
from sqlalchemy.orm import Session
import uuid

from models import Teacher, Organization, School, TeacherOrganization
from auth import create_access_token
from services.casbin_service import get_casbin_service


@pytest.fixture
def test_teacher(shared_test_session: Session):
    """Create a test teacher"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash="$2b$12$test_hash",
        name="Test Teacher",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(test_teacher: Teacher):
    """Generate auth headers for test teacher"""
    token = create_access_token({"sub": str(test_teacher.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_org(shared_test_session: Session, test_teacher: Teacher):
    """Create a test organization with test teacher as owner"""
    casbin_service = get_casbin_service()

    org = Organization(
        name="Test Organization",
        display_name="Test Org",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    # Add teacher-organization relationship
    teacher_org = TeacherOrganization(
        teacher_id=test_teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(teacher_org)
    shared_test_session.commit()

    # Add Casbin role
    casbin_service.add_role_for_user(test_teacher.id, "org_owner", f"org-{org.id}")

    return org


@pytest.fixture
def test_school(shared_test_session: Session, test_org: Organization):
    """Create a test school"""
    school = School(
        organization_id=test_org.id,
        name="Test School",
        display_name="Test School Display",
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    return school


class TestSchoolCreate:
    """Tests for POST /api/schools"""

    def test_create_school_success(
        self,
        test_client,
        auth_headers,
        test_org: Organization,
        shared_test_session: Session,
    ):
        """Test creating a school successfully as org_owner"""
        response = test_client.post(
            "/api/schools",
            json={
                "organization_id": str(test_org.id),
                "name": "New School",
                "display_name": "New School Display",
                "description": "A new test school",
                "contact_email": "school@test.com",
                "contact_phone": "123-456-7890",
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New School"
        assert data["display_name"] == "New School Display"
        assert data["organization_id"] == str(test_org.id)
        assert data["is_active"] is True

        # Verify school exists in database
        school = (
            shared_test_session.query(School).filter(School.id == data["id"]).first()
        )
        assert school is not None
        assert school.name == "New School"

    def test_create_school_without_auth(self, test_client, test_org: Organization):
        """Test creating school without authentication fails"""
        response = test_client.post(
            "/api/schools",
            json={"organization_id": str(test_org.id), "name": "Unauthorized School"},
        )
        assert response.status_code == 401

    def test_create_school_without_permission(
        self, test_client, shared_test_session: Session, test_org: Organization
    ):
        """Test creating school without org permission fails"""
        # Create another teacher without org access
        other_teacher = Teacher(
            email=f"other_{uuid.uuid4().hex[:8]}@test.com",
            password_hash="$2b$12$test_hash",
            name="Other Teacher",
            is_active=True,
        )
        shared_test_session.add(other_teacher)
        shared_test_session.commit()
        shared_test_session.refresh(other_teacher)

        token = create_access_token({"sub": str(other_teacher.id), "type": "teacher"})
        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.post(
            "/api/schools",
            json={"organization_id": str(test_org.id), "name": "Forbidden School"},
            headers=headers,
        )
        assert response.status_code == 403


class TestSchoolList:
    """Tests for GET /api/schools"""

    def test_list_schools_as_org_owner(
        self, test_client, auth_headers, test_school: School
    ):
        """Test listing schools as org owner"""
        response = test_client.get("/api/schools", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our test school
        school_ids = [s["id"] for s in data]
        assert str(test_school.id) in school_ids

    def test_list_schools_filter_by_org(
        self, test_client, auth_headers, test_org: Organization, test_school: School
    ):
        """Test listing schools filtered by organization"""
        response = test_client.get(
            f"/api/schools?organization_id={test_org.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(s["organization_id"] == str(test_org.id) for s in data)


class TestSchoolGet:
    """Tests for GET /api/schools/{school_id}"""

    def test_get_school_success(self, test_client, auth_headers, test_school: School):
        """Test getting school details successfully"""
        response = test_client.get(
            f"/api/schools/{test_school.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_school.id)
        assert data["name"] == test_school.name
        assert data["display_name"] == test_school.display_name

    def test_get_school_not_found(self, test_client, auth_headers):
        """Test getting non-existent school"""
        fake_id = uuid.uuid4()
        response = test_client.get(
            f"/api/schools/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_school_without_permission(
        self, test_client, shared_test_session: Session, test_school: School
    ):
        """Test getting school without permission"""
        # Create another teacher without access
        other_teacher = Teacher(
            email=f"other_{uuid.uuid4().hex[:8]}@test.com",
            password_hash="$2b$12$test_hash",
            name="Other Teacher",
            is_active=True,
        )
        shared_test_session.add(other_teacher)
        shared_test_session.commit()
        shared_test_session.refresh(other_teacher)

        token = create_access_token({"sub": str(other_teacher.id), "type": "teacher"})
        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.get(
            f"/api/schools/{test_school.id}",
            headers=headers,
        )
        assert response.status_code == 403


class TestSchoolUpdate:
    """Tests for PATCH /api/schools/{school_id}"""

    def test_update_school_success(
        self,
        test_client,
        auth_headers,
        test_school: School,
        shared_test_session: Session,
    ):
        """Test updating school successfully"""
        response = test_client.patch(
            f"/api/schools/{test_school.id}",
            json={
                "display_name": "Updated School Name",
                "contact_phone": "999-888-7777",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated School Name"
        assert data["contact_phone"] == "999-888-7777"

        # Verify in database
        shared_test_session.refresh(test_school)
        assert test_school.display_name == "Updated School Name"

    def test_update_school_not_found(self, test_client, auth_headers):
        """Test updating non-existent school"""
        fake_id = uuid.uuid4()
        response = test_client.patch(
            f"/api/schools/{fake_id}",
            json={"display_name": "New Name"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestSchoolDelete:
    """Tests for DELETE /api/schools/{school_id}"""

    def test_delete_school_success(
        self,
        test_client,
        auth_headers,
        test_school: School,
        shared_test_session: Session,
    ):
        """Test deleting school successfully (soft delete)"""
        response = test_client.delete(
            f"/api/schools/{test_school.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "School deleted successfully"

        # Verify soft delete
        shared_test_session.refresh(test_school)
        assert test_school.is_active is False

    def test_delete_school_not_found(self, test_client, auth_headers):
        """Test deleting non-existent school"""
        fake_id = uuid.uuid4()
        response = test_client.delete(
            f"/api/schools/{fake_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
