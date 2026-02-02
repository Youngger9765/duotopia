"""
TDD Tests for Organization Points API.

Tests organization points query, deduction, and history endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone

from models import Teacher, Organization, TeacherOrganization
from auth import create_access_token, get_password_hash
from services.casbin_service import get_casbin_service


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def org_owner(shared_test_session: Session):
    """Create organization owner teacher"""
    teacher = Teacher(
        email=f"owner_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Org Owner",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin(shared_test_session: Session):
    """Create org admin teacher"""
    teacher = Teacher(
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Org Admin",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(shared_test_session: Session):
    """Create regular teacher"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Regular Teacher",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_org(shared_test_session: Session, org_owner: Teacher):
    """Create test organization with owner"""
    org = Organization(
        name=f"test_org_{uuid.uuid4().hex[:8]}",
        display_name="Test Organization",
        is_active=True,
        total_points=10000,
        used_points=2500,
        last_points_update=datetime.now(timezone.utc),
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    # Add owner relationship
    owner_rel = TeacherOrganization(
        teacher_id=org_owner.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(owner_rel)
    shared_test_session.commit()

    # Setup Casbin permissions
    casbin_service = get_casbin_service()
    casbin_service.add_role_for_user(org_owner.id, "org_owner", f"org-{org.id}")

    return org


@pytest.fixture
def owner_headers(org_owner: Teacher):
    """Generate auth headers for org owner"""
    token = create_access_token({"sub": str(org_owner.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(org_admin: Teacher):
    """Generate auth headers for org admin"""
    token = create_access_token({"sub": str(org_admin.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def teacher_headers(regular_teacher: Teacher):
    """Generate auth headers for regular teacher"""
    token = create_access_token({"sub": str(regular_teacher.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Test Cases - Points Query Endpoint
# ============================================================================


class TestGetPointsBalance:
    """Test suite for GET /organizations/{org_id}/points endpoint"""

    def test_org_owner_can_query_points(
        self,
        test_client: TestClient,
        test_org: Organization,
        owner_headers: dict,
    ):
        """Test that org_owner can query organization points balance"""
        response = test_client.get(
            f"/api/organizations/{test_org.id}/points",
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["organization_id"] == str(test_org.id)
        assert data["total_points"] == 10000
        assert data["used_points"] == 2500
        assert data["remaining_points"] == 7500
        assert "last_points_update" in data

    @pytest.mark.skip(reason="Casbin permission methods need updating")
    def test_org_admin_with_permission_can_query_points(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_admin: Teacher,
        admin_headers: dict,
    ):
        """Test that org_admin with manage_materials permission can query points"""
        # Add org_admin to org with manage_materials permission
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(admin_rel)
        shared_test_session.commit()

        # Grant manage_materials permission
        casbin_service = get_casbin_service()
        casbin_service.add_role_for_user(
            org_admin.id, "org_admin", f"org-{test_org.id}"
        )
        casbin_service.add_permission_for_user(
            org_admin.id,
            f"org-{test_org.id}",
            "materials",
            "manage",
        )

        response = test_client.get(
            f"/api/organizations/{test_org.id}/points",
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["remaining_points"] == 7500

    def test_org_admin_without_permission_cannot_query_points(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_admin: Teacher,
        admin_headers: dict,
    ):
        """Test that org_admin without manage_materials permission cannot query points"""
        # Add org_admin to org WITHOUT manage_materials permission
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(admin_rel)
        shared_test_session.commit()

        response = test_client.get(
            f"/api/organizations/{test_org.id}/points",
            headers=admin_headers,
        )

        assert response.status_code == 403

    def test_regular_teacher_cannot_query_points(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        regular_teacher: Teacher,
        teacher_headers: dict,
    ):
        """Test that regular teacher cannot query organization points"""
        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        shared_test_session.add(teacher_rel)
        shared_test_session.commit()

        response = test_client.get(
            f"/api/organizations/{test_org.id}/points",
            headers=teacher_headers,
        )

        assert response.status_code == 403

    def test_unauthenticated_cannot_query_points(
        self,
        test_client: TestClient,
        test_org: Organization,
    ):
        """Test that unauthenticated request cannot query points"""
        response = test_client.get(f"/api/organizations/{test_org.id}/points")

        assert response.status_code == 401

    def test_nonexistent_organization_returns_404(
        self,
        test_client: TestClient,
        owner_headers: dict,
    ):
        """Test that querying nonexistent organization returns 404"""
        fake_uuid = "00000000-0000-0000-0000-000000000999"
        response = test_client.get(
            f"/api/organizations/{fake_uuid}/points",
            headers=owner_headers,
        )

        assert response.status_code == 404
