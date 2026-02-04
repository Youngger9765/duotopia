"""
TDD Tests for Admin Organization Points Management.

Tests admin endpoints can create/update organizations with points.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from models import Teacher, Organization
from auth import create_access_token, get_password_hash


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def admin_user(shared_test_session: Session):
    """Create admin teacher"""
    teacher = Teacher(
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Admin User",
        is_active=True,
        is_admin=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(shared_test_session: Session):
    """Create regular teacher for owner assignment"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Regular Teacher",
        is_active=True,
        is_admin=False,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def admin_headers(admin_user: Teacher):
    """Generate auth headers for admin"""
    token = create_access_token({"sub": str(admin_user.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_teacher_headers(regular_teacher: Teacher):
    """Generate auth headers for regular teacher"""
    token = create_access_token({"sub": str(regular_teacher.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Test Cases
# ============================================================================


class TestAdminOrganizationPoints:
    """Test suite for admin organization points management"""

    def test_create_organization_with_points(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        admin_headers: dict,
        regular_teacher: Teacher,
    ):
        """Test admin can create organization with initial points"""
        org_name = f"test_org_{uuid.uuid4().hex[:8]}"

        response = test_client.post(
            "/api/admin/organizations",
            json={
                "name": org_name,
                "display_name": "Test Organization",
                "owner_email": regular_teacher.email,
                "total_points": 10000,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "organization_id" in data

        # Verify in database
        org = (
            shared_test_session.query(Organization)
            .filter(Organization.name == org_name)
            .first()
        )
        assert org is not None
        assert org.total_points == 10000
        assert org.used_points == 0
        assert org.last_points_update is not None

    def test_create_organization_without_points_defaults_to_zero(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        admin_headers: dict,
        regular_teacher: Teacher,
    ):
        """Test organization defaults to 0 points if not specified"""
        org_name = f"test_org_{uuid.uuid4().hex[:8]}"

        response = test_client.post(
            "/api/admin/organizations",
            json={
                "name": org_name,
                "display_name": "Test Organization",
                "owner_email": regular_teacher.email,
            },
            headers=admin_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify in database
        org = (
            shared_test_session.query(Organization)
            .filter(Organization.name == org_name)
            .first()
        )
        assert org is not None
        assert org.total_points == 0
        assert org.used_points == 0
        assert org.last_points_update is None  # No update if points = 0

    def test_create_organization_points_negative_validation(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        admin_headers: dict,
        regular_teacher: Teacher,
    ):
        """Test cannot set negative points"""
        response = test_client.post(
            "/api/admin/organizations",
            json={
                "name": f"test_org_{uuid.uuid4().hex[:8]}",
                "display_name": "Test Organization",
                "owner_email": regular_teacher.email,
                "total_points": -1000,
            },
            headers=admin_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_non_admin_cannot_create_organization_with_points(
        self,
        test_client: TestClient,
        regular_teacher_headers: dict,
        regular_teacher: Teacher,
    ):
        """Test regular teacher cannot create organization with points"""
        response = test_client.post(
            "/api/admin/organizations",
            json={
                "name": f"test_org_{uuid.uuid4().hex[:8]}",
                "display_name": "Test",
                "owner_email": regular_teacher.email,
                "total_points": 10000,
            },
            headers=regular_teacher_headers,
        )

        assert response.status_code == 403  # Forbidden
