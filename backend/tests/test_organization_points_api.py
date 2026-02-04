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


# ============================================================================
# Test Cases - Points Deduction Endpoint
# ============================================================================


class TestDeductPoints:
    """Test suite for POST /organizations/{org_id}/points/deduct endpoint"""

    def test_org_owner_can_deduct_points(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner can deduct points for AI usage"""
        # Verify log created
        from models import OrganizationPointsLog

        response = test_client.post(
            f"/api/organizations/{test_org.id}/points/deduct",
            json={
                "points": 500,
                "feature_type": "ai_generation",
                "description": "Generated 10 questions with AI",
            },
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["points_deducted"] == 500
        assert data["remaining_points"] == 7000  # 10000 - 2500 - 500
        assert "transaction_id" in data

        # Verify points updated in database
        shared_test_session.refresh(test_org)
        assert test_org.used_points == 3000  # 2500 + 500

        # Verify log created
        log = (
            shared_test_session.query(OrganizationPointsLog)
            .filter(OrganizationPointsLog.organization_id == test_org.id)
            .filter(OrganizationPointsLog.points_used == 500)
            .first()
        )
        assert log is not None
        assert log.feature_type == "ai_generation"
        assert log.teacher_id == org_owner.id

    def test_deduct_points_insufficient_balance(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that deducting more points than available returns 400"""
        # Create org with low balance
        low_balance_org = Organization(
            name=f"low_balance_{uuid.uuid4().hex[:8]}",
            display_name="Low Balance Org",
            is_active=True,
            total_points=100,
            used_points=0,
        )
        shared_test_session.add(low_balance_org)
        shared_test_session.commit()
        shared_test_session.refresh(low_balance_org)

        # Add owner relationship
        owner_rel = TeacherOrganization(
            teacher_id=org_owner.id,
            organization_id=low_balance_org.id,
            role="org_owner",
            is_active=True,
        )
        shared_test_session.add(owner_rel)
        shared_test_session.commit()

        # Setup Casbin
        from services.casbin_service import get_casbin_service

        casbin_service = get_casbin_service()
        casbin_service.add_role_for_user(
            org_owner.id, "org_owner", f"org-{low_balance_org.id}"
        )

        response = test_client.post(
            f"/api/organizations/{low_balance_org.id}/points/deduct",
            json={
                "points": 500,
                "feature_type": "ai_generation",
                "description": "Test",
            },
            headers=owner_headers,
        )

        assert response.status_code == 400
        assert "Insufficient points" in response.json()["detail"]

    def test_deduct_negative_points_returns_400(
        self,
        test_client: TestClient,
        test_org: Organization,
        owner_headers: dict,
    ):
        """Test that deducting negative points returns 400"""
        response = test_client.post(
            f"/api/organizations/{test_org.id}/points/deduct",
            json={
                "points": -100,
                "feature_type": "ai_generation",
                "description": "Test",
            },
            headers=owner_headers,
        )

        assert response.status_code == 400
        assert "Points must be positive" in response.json()["detail"]

    def test_non_member_cannot_deduct_points(
        self,
        test_client: TestClient,
        test_org: Organization,
        teacher_headers: dict,
    ):
        """Test that non-member cannot deduct points"""
        response = test_client.post(
            f"/api/organizations/{test_org.id}/points/deduct",
            json={
                "points": 100,
                "feature_type": "ai_generation",
                "description": "Test",
            },
            headers=teacher_headers,
        )

        assert response.status_code == 403


# ============================================================================
# Test Cases - Points History Endpoint
# ============================================================================


class TestPointsHistory:
    """Test suite for GET /organizations/{org_id}/points/history endpoint"""

    def test_org_owner_can_view_history(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that org_owner can view points usage history"""
        # Create some log entries
        from models import OrganizationPointsLog

        for i in range(3):
            log = OrganizationPointsLog(
                organization_id=test_org.id,
                teacher_id=org_owner.id,
                points_used=100 * (i + 1),
                feature_type="ai_generation",
                description=f"Test usage {i+1}",
            )
            shared_test_session.add(log)
        shared_test_session.commit()

        response = test_client.get(
            f"/api/organizations/{test_org.id}/points/history",
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 3
        assert data["total"] >= 3

        # Verify our test logs are present
        # Note: There might be existing logs from deduction tests
        recent_logs = [
            item
            for item in data["items"]
            if item["description"] and "Test usage" in item["description"]
        ]
        assert len(recent_logs) == 3

        # Verify all expected points values are present (order may vary due to timestamp precision)
        points_values = sorted(
            [log["points_used"] for log in recent_logs], reverse=True
        )
        assert points_values == [300, 200, 100]

    def test_history_includes_teacher_name(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that history includes teacher name via join"""
        from models import OrganizationPointsLog

        # Create a log entry
        log = OrganizationPointsLog(
            organization_id=test_org.id,
            teacher_id=org_owner.id,
            points_used=50,
            feature_type="ai_generation",
            description="Test with teacher name",
        )
        shared_test_session.add(log)
        shared_test_session.commit()

        response = test_client.get(
            f"/api/organizations/{test_org.id}/points/history",
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find our specific log entry
        our_log = next(
            (
                item
                for item in data["items"]
                if item["description"] == "Test with teacher name"
            ),
            None,
        )
        assert our_log is not None
        assert our_log["teacher_name"] == org_owner.name
        assert our_log["teacher_id"] == org_owner.id

    def test_history_pagination(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_org: Organization,
        org_owner: Teacher,
        owner_headers: dict,
    ):
        """Test that history supports pagination"""
        from models import OrganizationPointsLog

        # Create 15 log entries
        for i in range(15):
            log = OrganizationPointsLog(
                organization_id=test_org.id,
                teacher_id=org_owner.id,
                points_used=10,
                feature_type="ai_generation",
                description=f"Pagination test {i}",
            )
            shared_test_session.add(log)
        shared_test_session.commit()

        # Get first page
        response = test_client.get(
            f"/api/organizations/{test_org.id}/points/history?limit=10&offset=0",
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert data["total"] >= 15

        # Get second page
        response = test_client.get(
            f"/api/organizations/{test_org.id}/points/history?limit=10&offset=10",
            headers=owner_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 10
        # Second page should have remaining items
        assert len(data["items"]) >= 5

    def test_non_member_cannot_view_history(
        self,
        test_client: TestClient,
        test_org: Organization,
        teacher_headers: dict,
    ):
        """Test that non-member cannot view history"""
        response = test_client.get(
            f"/api/organizations/{test_org.id}/points/history",
            headers=teacher_headers,
        )

        assert response.status_code == 403
