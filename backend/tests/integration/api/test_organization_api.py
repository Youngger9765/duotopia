"""
Integration tests for Organization API

Tests for CRUD operations on organizations with Casbin permission checks.
"""

import pytest
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from models import Teacher, Organization, TeacherOrganization
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
        display_name="Test Org Display",
        description="Test organization description",
        contact_email="test@org.com",
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
    casbin_service.add_role_for_user(
        test_teacher.id,
        "org_owner",
        f"org-{org.id}"
    )

    return org


class TestOrganizationCreate:
    """Tests for POST /api/organizations"""

    def test_create_organization_success(self, test_client, auth_headers, shared_test_session: Session, test_teacher: Teacher):
        """Test creating an organization successfully"""
        response = test_client.post(
            "/api/organizations",
            json={
                "name": "New Organization",
                "display_name": "New Org",
                "description": "A new test organization",
                "contact_email": "new@org.com",
                "contact_phone": "123-456-7890",
            },
            headers=auth_headers,
        )

        # Debug: print response if not 201
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Organization"
        assert data["display_name"] == "New Org"
        assert data["is_active"] is True
        assert "id" in data

        # Verify organization exists in database
        org = shared_test_session.query(Organization).filter(Organization.id == data["id"]).first()
        assert org is not None
        assert org.name == "New Organization"

        # Verify teacher-organization relationship
        teacher_org = shared_test_session.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == test_teacher.id,
            TeacherOrganization.organization_id == org.id
        ).first()
        assert teacher_org is not None
        assert teacher_org.role == "org_owner"

        # Verify Casbin role
        casbin_service = get_casbin_service()
        assert casbin_service.has_role(test_teacher.id, "org_owner", f"org-{org.id}")

    def test_create_organization_without_auth(self, test_client):
        """Test creating organization without authentication fails"""
        response = test_client.post(
            "/api/organizations",
            json={"name": "Unauthorized Org"},
        )

        assert response.status_code == 401


class TestOrganizationList:
    """Tests for GET /api/organizations"""

    def test_list_organizations_as_owner(self, test_client, auth_headers, test_org: Organization):
        """Test listing organizations as org owner"""
        response = test_client.get("/api/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our test org in the list
        org_ids = [org["id"] for org in data]
        assert str(test_org.id) in org_ids

    def test_list_organizations_empty(self, test_client, auth_headers, shared_test_session: Session):
        """Test listing organizations when user has no organizations"""
        response = test_client.get("/api/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestOrganizationGet:
    """Tests for GET /api/organizations/{org_id}"""

    def test_get_organization_success(self, test_client, auth_headers, test_org: Organization):
        """Test getting organization details successfully"""
        response = test_client.get(
            f"/api/organizations/{test_org.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_org.id)
        assert data["name"] == test_org.name
        assert data["display_name"] == test_org.display_name

    def test_get_organization_not_found(self, test_client, auth_headers):
        """Test getting non-existent organization"""
        fake_id = uuid.uuid4()
        response = test_client.get(
            f"/api/organizations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_organization_without_permission(self, test_client, shared_test_session: Session):
        """Test getting organization without permission"""
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

        # Create an org (without adding other_teacher as member)
        org = Organization(name="Private Org", is_active=True)
        shared_test_session.add(org)
        shared_test_session.commit()
        shared_test_session.refresh(org)

        response = test_client.get(
            f"/api/organizations/{org.id}",
            headers=headers,
        )

        assert response.status_code == 403


class TestOrganizationUpdate:
    """Tests for PATCH /api/organizations/{org_id}"""

    def test_update_organization_success(self, test_client, auth_headers, test_org: Organization, shared_test_session: Session):
        """Test updating organization successfully"""
        response = test_client.patch(
            f"/api/organizations/{test_org.id}",
            json={
                "display_name": "Updated Display Name",
                "contact_phone": "999-888-7777",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Updated Display Name"
        assert data["contact_phone"] == "999-888-7777"

        # Verify in database
        shared_test_session.refresh(test_org)
        assert test_org.display_name == "Updated Display Name"
        assert test_org.contact_phone == "999-888-7777"

    def test_update_organization_not_found(self, test_client, auth_headers):
        """Test updating non-existent organization"""
        fake_id = uuid.uuid4()
        response = test_client.patch(
            f"/api/organizations/{fake_id}",
            json={"display_name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestOrganizationDelete:
    """Tests for DELETE /api/organizations/{org_id}"""

    def test_delete_organization_success(self, test_client, auth_headers, test_org: Organization, shared_test_session: Session):
        """Test deleting organization successfully (soft delete)"""
        response = test_client.delete(
            f"/api/organizations/{test_org.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Organization deleted successfully"

        # Verify soft delete in database
        shared_test_session.refresh(test_org)
        assert test_org.is_active is False

    def test_delete_organization_not_found(self, test_client, auth_headers):
        """Test deleting non-existent organization"""
        fake_id = uuid.uuid4()
        response = test_client.delete(
            f"/api/organizations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
