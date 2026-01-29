"""Tests for admin organization creation endpoint"""

import pytest
from models import Teacher, Organization, TeacherOrganization, School, TeacherSchool
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


def test_organization_stats_teacher_deduplication(shared_test_session, admin_teacher, regular_teacher, test_client):
    """
    Test that organization stats correctly deduplicate teachers with multiple roles.

    Scenario:
    - Create org with owner (Teacher A)
    - Create school under org
    - Add Teacher A to school (now has org_owner + school role)
    - Create Teacher B and add to school only
    - Expected teacher count: 2 (not 3)

    This tests the fix for Issue #112 Error 6.
    """
    # Create auth headers for regular teacher (will be org owner)
    access_token = create_access_token(
        data={"sub": str(regular_teacher.id), "type": "teacher"}
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Create organization with regular_teacher as owner
    org_response = test_client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {create_access_token(data={'sub': str(admin_teacher.id), 'type': 'teacher'})}"},
        json={
            "name": "Test Dedup Org",
            "display_name": "測試去重組織",
            "owner_email": regular_teacher.email
        }
    )
    assert org_response.status_code == 201
    org_id = org_response.json()["organization_id"]

    # Create a school under this organization
    school = School(
        organization_id=org_id,
        name="Test School",
        display_name="測試學校",
        is_active=True
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)

    # Add regular_teacher to the school (now has org_owner + school role)
    teacher_school = TeacherSchool(
        teacher_id=regular_teacher.id,
        school_id=school.id,
        roles=["school_admin"],
        is_active=True
    )
    shared_test_session.add(teacher_school)

    # Create another teacher and add to school only
    teacher_b = Teacher(
        email="teacherb@example.com",
        password_hash=get_password_hash("password"),
        name="Teacher B",
        is_active=True,
        email_verified=True
    )
    shared_test_session.add(teacher_b)
    shared_test_session.commit()
    shared_test_session.refresh(teacher_b)

    teacher_school_b = TeacherSchool(
        teacher_id=teacher_b.id,
        school_id=school.id,
        roles=["teacher"],
        is_active=True
    )
    shared_test_session.add(teacher_school_b)
    shared_test_session.commit()

    # Get organization stats
    stats_response = test_client.get(
        "/api/organizations/stats",
        headers=auth_headers
    )

    assert stats_response.status_code == 200
    data = stats_response.json()

    # Assert counts
    assert data["total_organizations"] == 1, "Should have 1 organization"
    assert data["total_schools"] == 1, "Should have 1 school"
    assert data["total_teachers"] == 2, f"Should have 2 unique teachers (got {data['total_teachers']}). Teacher A has both org_owner and school_admin roles, Teacher B has school role only."

    print(f"✅ Test passed: Teacher count correctly deduplicated to {data['total_teachers']}")


def test_get_organization_statistics_as_admin(shared_test_session, admin_teacher, regular_teacher, auth_headers_admin, test_client):
    """Test admin can get organization statistics"""
    # Create organization
    org_data = {
        "name": "Test Org Stats",
        "owner_email": regular_teacher.email,
        "teacher_limit": 10
    }
    create_response = test_client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    org_id = create_response.json()["organization_id"]

    # Add 3 more teachers to organization
    from models import Teacher, TeacherOrganization
    teacher1 = Teacher(email="t1@test.com", password_hash=get_password_hash("password"), name="T1", email_verified=True, is_active=True)
    teacher2 = Teacher(email="t2@test.com", password_hash=get_password_hash("password"), name="T2", email_verified=True, is_active=True)
    teacher3 = Teacher(email="t3@test.com", password_hash=get_password_hash("password"), name="T3", email_verified=True, is_active=True)
    shared_test_session.add_all([teacher1, teacher2, teacher3])
    shared_test_session.flush()

    shared_test_session.add_all([
        TeacherOrganization(teacher_id=teacher1.id, organization_id=org_id, role="teacher", is_active=True),
        TeacherOrganization(teacher_id=teacher2.id, organization_id=org_id, role="teacher", is_active=True),
        TeacherOrganization(teacher_id=teacher3.id, organization_id=org_id, role="org_admin", is_active=True),
    ])
    shared_test_session.commit()

    # Get statistics
    response = test_client.get(
        f"/api/admin/organizations/{org_id}/statistics",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_count"] == 4  # 1 owner + 3 added
    assert data["teacher_limit"] == 10
    assert data["usage_percentage"] == 40.0


def test_get_organization_statistics_no_limit(shared_test_session, admin_teacher, regular_teacher, auth_headers_admin, test_client):
    """Test statistics when teacher_limit is None (unlimited)"""
    org_data = {
        "name": "Test Org Unlimited",
        "owner_email": regular_teacher.email,
        # No teacher_limit
    }
    create_response = test_client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=auth_headers_admin
    )
    assert create_response.status_code == 201
    org_id = create_response.json()["organization_id"]

    response = test_client.get(
        f"/api/admin/organizations/{org_id}/statistics",
        headers=auth_headers_admin
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_count"] == 1
    assert data["teacher_limit"] is None
    assert data["usage_percentage"] == 0.0  # 0% when unlimited
