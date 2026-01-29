"""Tests for admin organization creation endpoint"""

import pytest
from models import Teacher, Organization, TeacherOrganization
from auth import get_password_hash, create_access_token


@pytest.fixture
def admin_teacher(shared_test_session):
    """Create an admin teacher for testing"""
    teacher = Teacher(
        email="admin@duotopia.com",
        password_hash=get_password_hash("admin_password"),
        name="Admin Teacher",
        is_active=True,
        is_admin=True,  # Admin user
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(shared_test_session):
    """Create a regular (non-admin) teacher for testing"""
    teacher = Teacher(
        email="regular@duotopia.com",
        password_hash=get_password_hash("regular_password"),
        name="Regular Teacher",
        is_active=True,
        is_admin=False,  # Not admin
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers_admin(admin_teacher):
    """Create authentication headers for admin teacher"""
    access_token = create_access_token(
        data={"sub": str(admin_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def auth_headers_regular(regular_teacher):
    """Create authentication headers for regular teacher"""
    access_token = create_access_token(
        data={"sub": str(regular_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


def test_create_organization_as_admin_success(shared_test_session, admin_teacher, regular_teacher, auth_headers_admin, test_client):
    """Admin can create organization and assign existing teacher as owner"""

    # Create organization
    response = test_client.post(
        "/api/admin/organizations",
        headers=auth_headers_admin,
        json={
            "name": "Test Org",
            "display_name": "測試機構",
            "tax_id": "12345678",
            "teacher_limit": 10,
            "owner_email": regular_teacher.email
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["organization_name"] == "Test Org"
    assert data["owner_email"] == regular_teacher.email
    assert "organization_id" in data

    # Verify organization created
    org = shared_test_session.query(Organization).filter(
        Organization.name == "Test Org"
    ).first()
    assert org is not None
    assert org.tax_id == "12345678"

    # Verify owner role assigned
    teacher_org = shared_test_session.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == org.id,
        TeacherOrganization.teacher_id == regular_teacher.id
    ).first()
    assert teacher_org is not None
    assert teacher_org.role == "org_owner"


def test_create_organization_non_admin_forbidden(shared_test_session, regular_teacher, auth_headers_regular, test_client):
    """Non-admin cannot create organization"""

    response = test_client.post(
        "/api/admin/organizations",
        headers=auth_headers_regular,
        json={
            "name": "Test Org",
            "owner_email": regular_teacher.email
        }
    )

    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


def test_create_organization_owner_not_found(shared_test_session, admin_teacher, auth_headers_admin, test_client):
    """Cannot create organization with non-existent owner email"""

    response = test_client.post(
        "/api/admin/organizations",
        headers=auth_headers_admin,
        json={
            "name": "Test Org",
            "owner_email": "nonexistent@example.com"
        }
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_organization_duplicate_name(shared_test_session, admin_teacher, regular_teacher, auth_headers_admin, test_client):
    """Cannot create organization with duplicate name"""

    # Create first org
    test_client.post(
        "/api/admin/organizations",
        headers=auth_headers_admin,
        json={"name": "Duplicate Org", "owner_email": regular_teacher.email}
    )

    # Try to create duplicate
    response = test_client.post(
        "/api/admin/organizations",
        headers=auth_headers_admin,
        json={"name": "Duplicate Org", "owner_email": regular_teacher.email}
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
