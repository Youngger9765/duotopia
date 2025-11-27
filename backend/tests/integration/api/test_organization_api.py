"""
Integration tests for Organization API

Tests for CRUD operations on organizations with Casbin permission checks.
"""

import pytest
from sqlalchemy.orm import Session
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

    # Sync to Casbin (must be done AFTER test_client initialization to use same instance)
    casbin_service.add_role_for_user(test_teacher.id, "org_owner", f"org-{org.id}")
    print(
        f"[TEST] Added Casbin role: org_owner for teacher={test_teacher.id} in org-{org.id}"
    )

    return org


class TestOrganizationCreate:
    """Tests for POST /api/organizations"""

    def test_create_organization_success(
        self,
        test_client,
        auth_headers,
        shared_test_session: Session,
        test_teacher: Teacher,
    ):
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
        org = (
            shared_test_session.query(Organization)
            .filter(Organization.id == data["id"])
            .first()
        )
        assert org is not None
        assert org.name == "New Organization"

        # Verify teacher-organization relationship
        teacher_org = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == test_teacher.id,
                TeacherOrganization.organization_id == org.id,
            )
            .first()
        )
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

    def test_list_organizations_as_owner(self, test_client, auth_headers):
        """Test listing organizations as org owner"""
        # Create organization via API so it's visible to subsequent API calls
        create_response = test_client.post(
            "/api/organizations",
            json={
                "name": "My Test Org",
                "display_name": "My Organization",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        created_org = create_response.json()

        # Now list organizations
        response = test_client.get("/api/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our created org in the list
        org_ids = [org["id"] for org in data]
        assert created_org["id"] in org_ids

    def test_list_organizations_empty(
        self, test_client, auth_headers, shared_test_session: Session
    ):
        """Test listing organizations when user has no organizations"""
        response = test_client.get("/api/organizations", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestOrganizationGet:
    """Tests for GET /api/organizations/{org_id}"""

    def test_get_organization_success(self, test_client, auth_headers):
        """Test getting organization details successfully"""
        # Create organization via API
        create_response = test_client.post(
            "/api/organizations",
            json={
                "name": "Test Get Org",
                "display_name": "Get Org Display",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        created_org = create_response.json()

        # Get the created organization
        response = test_client.get(
            f"/api/organizations/{created_org['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_org["id"]
        assert data["name"] == "Test Get Org"
        assert data["display_name"] == "Get Org Display"

    def test_get_organization_not_found(self, test_client, auth_headers):
        """Test getting non-existent organization"""
        fake_id = uuid.uuid4()
        response = test_client.get(
            f"/api/organizations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_organization_without_permission(
        self, test_client, shared_test_session: Session
    ):
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

    def test_update_organization_success(
        self,
        test_client,
        auth_headers,
    ):
        """Test updating organization successfully"""
        # Create organization via API
        create_response = test_client.post(
            "/api/organizations",
            json={
                "name": "Update Test Org",
                "display_name": "Original Name",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        created_org = create_response.json()

        # Update the organization
        response = test_client.patch(
            f"/api/organizations/{created_org['id']}",
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

    def test_delete_organization_success(
        self,
        test_client,
        auth_headers,
    ):
        """Test deleting organization successfully (soft delete)"""
        # Create organization via API
        create_response = test_client.post(
            "/api/organizations",
            json={
                "name": "Delete Test Org",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        created_org = create_response.json()

        # Delete the organization
        response = test_client.delete(
            f"/api/organizations/{created_org['id']}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Organization deleted successfully"

        # Verify it's no longer in list (soft deleted)
        list_response = test_client.get("/api/organizations", headers=auth_headers)
        assert list_response.status_code == 200
        org_ids = [org["id"] for org in list_response.json()]
        assert (
            created_org["id"] not in org_ids
        )  # Soft deleted orgs don't appear in list

    def test_delete_organization_not_found(self, test_client, auth_headers):
        """Test deleting non-existent organization"""
        fake_id = uuid.uuid4()
        response = test_client.delete(
            f"/api/organizations/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
