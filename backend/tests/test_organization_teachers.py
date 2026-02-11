"""
TDD Tests for PUT /{org_id}/teachers/{teacher_id} endpoint.

Bug Fix: org_owner cannot re-edit staff roles
Test Coverage: 9 test scenarios
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from models import Teacher, Organization, TeacherOrganization
from auth import create_access_token, get_password_hash
from services.casbin_service import get_casbin_service


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_db(shared_test_session: Session):
    """Provide test database session"""
    return shared_test_session


@pytest.fixture
def org_owner(test_db: Session):
    """Create organization owner teacher"""
    teacher = Teacher(
        email=f"owner_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Org Owner",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin(test_db: Session):
    """Create org admin teacher"""
    teacher = Teacher(
        email=f"admin_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Org Admin",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(test_db: Session):
    """Create regular teacher"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Regular Teacher",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def test_org(test_db: Session, org_owner: Teacher):
    """Create test organization with owner"""
    org = Organization(
        name=f"Test Org {uuid.uuid4().hex[:8]}",
        display_name="Test Organization",
        is_active=True,
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)

    # Add owner relationship
    owner_rel = TeacherOrganization(
        teacher_id=org_owner.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    test_db.add(owner_rel)
    test_db.commit()

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
# Test Cases
# ============================================================================


class TestUpdateTeacherRole:
    """Test suite for PUT /{org_id}/teachers/{teacher_id} endpoint"""

    def test_org_owner_can_update_teacher_role_to_org_owner(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_owner: Teacher,
        regular_teacher: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner can transfer ownership to another teacher"""
        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Update regular teacher to org_owner
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_owner"},
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "org_owner"
        assert data["teacher_id"] == regular_teacher.id

        # Verify old owner is now org_admin
        old_owner_rel = (
            test_db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == org_owner.id,
                TeacherOrganization.organization_id == test_org.id,
            )
            .first()
        )
        assert old_owner_rel.role == "org_admin"

    def test_org_owner_can_demote_org_admin_to_teacher(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_admin: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner can demote org_admin to regular teacher"""
        # Add org_admin to org
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        test_db.add(admin_rel)
        test_db.commit()

        # Demote to teacher
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{org_admin.id}",
            json={"role": "teacher"},
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "teacher"
        assert data["teacher_id"] == org_admin.id

    def test_org_owner_can_promote_teacher_to_org_admin(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        regular_teacher: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner can promote teacher to org_admin"""
        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Promote to org_admin
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_admin"},
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "org_admin"
        assert data["teacher_id"] == regular_teacher.id

    def test_org_admin_can_update_roles_with_manage_teachers_permission(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_admin: Teacher,
        regular_teacher: Teacher,
        admin_headers: dict,
    ):
        """Test that org_admin with manage_teachers permission can update roles"""
        # Add org_admin to org
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        test_db.add(admin_rel)
        test_db.commit()

        # Grant manage_teachers permission
        casbin_service = get_casbin_service()
        casbin_service.add_role_for_user(
            org_admin.id, "org_admin", f"org-{test_org.id}"
        )

        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Update teacher role
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_admin"},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "org_admin"

    def test_org_admin_cannot_update_roles_without_permission(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_admin: Teacher,
        regular_teacher: Teacher,
        admin_headers: dict,
    ):
        """Test that org_admin without manage_teachers permission cannot update roles"""
        # Add org_admin to org WITHOUT manage_teachers permission
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="teacher",  # Regular teacher, not org_admin
            is_active=True,
        )
        test_db.add(admin_rel)
        test_db.commit()

        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Try to update teacher role - should fail
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_admin"},
            headers=admin_headers,
        )

        assert response.status_code == 403

    def test_cannot_change_own_role(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that a teacher cannot change their own role"""
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{org_owner.id}",
            json={"role": "teacher"},
            headers=owner_headers,
        )

        assert response.status_code == 400
        assert "own role" in response.json()["detail"].lower()

    def test_cannot_create_second_org_owner(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_owner: Teacher,
        regular_teacher: Teacher,
        owner_headers: dict,
    ):
        """Test that creating second org_owner transfers ownership"""
        # Add regular teacher to org
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Promote to org_owner
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_owner"},
            headers=owner_headers,
        )

        assert response.status_code == 200

        # Verify only one org_owner exists
        owners = (
            test_db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == test_org.id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .all()
        )
        assert len(owners) == 1
        assert owners[0].teacher_id == regular_teacher.id

    def test_regular_teacher_cannot_update_any_roles(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        regular_teacher: Teacher,
        teacher_headers: dict,
    ):
        """Test that regular teacher cannot update any roles"""
        # Add another teacher to update
        another_teacher = Teacher(
            email=f"another_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("password123"),
            name="Another Teacher",
            is_active=True,
        )
        test_db.add(another_teacher)
        test_db.commit()
        test_db.refresh(another_teacher)

        # Add both teachers to org
        for teacher in [regular_teacher, another_teacher]:
            rel = TeacherOrganization(
                teacher_id=teacher.id,
                organization_id=test_org.id,
                role="teacher",
                is_active=True,
            )
            test_db.add(rel)
        test_db.commit()

        # Try to update another teacher's role - should fail
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{another_teacher.id}",
            json={"role": "org_admin"},
            headers=teacher_headers,
        )

        assert response.status_code == 403


class TestUpdateTeacherStatus:
    """Test suite for is_active status changes in PUT /{org_id}/teachers/{teacher_id}"""

    def test_deactivate_and_reactivate_teacher(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        regular_teacher: Teacher,
        owner_headers: dict,
    ):
        """Test deactivating then re-activating a teacher"""
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Deactivate
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "teacher", "is_active": False},
            headers=owner_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        # Re-activate
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "teacher", "is_active": True},
            headers=owner_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is True

    def test_cannot_deactivate_org_owner(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        org_owner: Teacher,
        org_admin: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner cannot be deactivated (must transfer ownership first)"""
        # Add org_admin so they can make the request
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=test_org.id,
            role="org_admin",
            is_active=True,
        )
        test_db.add(admin_rel)
        test_db.commit()

        casbin_service = get_casbin_service()
        casbin_service.add_role_for_user(
            org_admin.id, "org_admin", f"org-{test_org.id}"
        )

        admin_token = create_access_token({"sub": str(org_admin.id), "type": "teacher"})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Try to deactivate org_owner
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{org_owner.id}",
            json={"role": "org_owner", "is_active": False},
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert "擁有者" in response.json()["detail"]

    def test_teacher_limit_enforced_on_reactivation(
        self,
        test_client: TestClient,
        test_db: Session,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that teacher_limit is checked when re-activating a teacher"""
        # Create org with teacher_limit=1
        org = Organization(
            name=f"Limited Org {uuid.uuid4().hex[:8]}",
            display_name="Limited Org",
            is_active=True,
            teacher_limit=1,
        )
        test_db.add(org)
        test_db.commit()
        test_db.refresh(org)

        # Add owner
        owner_rel = TeacherOrganization(
            teacher_id=org_owner.id,
            organization_id=org.id,
            role="org_owner",
            is_active=True,
        )
        test_db.add(owner_rel)
        test_db.commit()

        casbin_service = get_casbin_service()
        casbin_service.add_role_for_user(org_owner.id, "org_owner", f"org-{org.id}")

        # Add active teacher (fills the limit)
        active_teacher = Teacher(
            email=f"active_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("password123"),
            name="Active Teacher",
            is_active=True,
        )
        test_db.add(active_teacher)
        test_db.commit()
        test_db.refresh(active_teacher)

        active_rel = TeacherOrganization(
            teacher_id=active_teacher.id,
            organization_id=org.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(active_rel)
        test_db.commit()

        # Add inactive teacher
        inactive_teacher = Teacher(
            email=f"inactive_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("password123"),
            name="Inactive Teacher",
            is_active=True,
        )
        test_db.add(inactive_teacher)
        test_db.commit()
        test_db.refresh(inactive_teacher)

        inactive_rel = TeacherOrganization(
            teacher_id=inactive_teacher.id,
            organization_id=org.id,
            role="teacher",
            is_active=False,
        )
        test_db.add(inactive_rel)
        test_db.commit()

        # Try to re-activate - should fail (limit=1, already 1 active)
        response = test_client.put(
            f"/api/organizations/{org.id}/teachers/{inactive_teacher.id}",
            json={"role": "teacher", "is_active": True},
            headers=owner_headers,
        )
        assert response.status_code == 400
        assert "授權上限" in response.json()["detail"]

    def test_update_role_and_activate_together(
        self,
        test_client: TestClient,
        test_db: Session,
        test_org: Organization,
        regular_teacher: Teacher,
        owner_headers: dict,
    ):
        """Test that role change and activation can happen in a single request"""
        # Add inactive teacher
        teacher_rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=test_org.id,
            role="teacher",
            is_active=False,
        )
        test_db.add(teacher_rel)
        test_db.commit()

        # Activate and promote to org_admin in one request
        response = test_client.put(
            f"/api/organizations/{test_org.id}/teachers/{regular_teacher.id}",
            json={"role": "org_admin", "is_active": True},
            headers=owner_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "org_admin"
        assert data["is_active"] is True
