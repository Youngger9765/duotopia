"""
Integration tests for Organization Teacher Management endpoints.

Target endpoints:
1. POST /{org_id}/teachers - Add teacher to organization
2. GET /stats - Get organization statistics

Coverage Impact: +187 lines (60% → 70%+)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from models import Teacher
from auth import create_access_token


# ============================================================================
# Fixtures
# ============================================================================

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


# ============================================================================
# Helper Functions
# ============================================================================

def create_org_via_api(client: TestClient, headers: dict, name: str, teacher_limit: int = None) -> dict:
    """Helper to create organization via API."""
    payload = {"name": name}
    if teacher_limit is not None:
        payload["teacher_limit"] = teacher_limit

    response = client.post("/api/organizations", json=payload, headers=headers)
    assert response.status_code in [200, 201], f"Failed to create org: {response.text}"
    return response.json()


def add_teacher_via_api(
    client: TestClient,
    headers: dict,
    org_id: str,
    teacher_id: int,
    role: str
):
    """Helper to add teacher to organization via API."""
    payload = {
        "teacher_id": teacher_id,
        "role": role
    }
    response = client.post(
        f"/api/organizations/{org_id}/teachers",
        json=payload,
        headers=headers
    )
    return response


def get_stats_via_api(client: TestClient, headers: dict) -> dict:
    """Helper to get organization stats via API."""
    response = client.get("/api/organizations/stats", headers=headers)
    assert response.status_code == 200, f"Failed to get stats: {response.text}"
    return response.json()


# ============================================================================
# Test Class: Add Teacher to Organization
# ============================================================================

class TestAddTeacherToOrganization:
    """Tests for POST /{org_id}/teachers endpoint (104 lines coverage)."""

    def test_add_teacher_success_org_admin(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test successfully adding teacher with org_admin role."""
        # Create organization
        org = create_org_via_api(test_client, auth_headers, "Test Org - Admin")
        org_id = org["id"]

        # Get current teacher ID (owner@duotopia.com = ID 1)
        # Create a second teacher via direct DB insert (simpler than API)
        from models import Teacher
        teacher2 = Teacher(
            name="Teacher Two",
            email="teacher2_add@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(teacher2)
        shared_test_session.commit()
        shared_test_session.refresh(teacher2)
        teacher2_id = teacher2.id

        # Add teacher as org_admin
        response = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teacher2_id,
            "org_admin"
        )

        # Assertions
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["teacher_id"] == teacher2_id
        assert data["role"] == "org_admin"

    def test_add_teacher_duplicate_rejected(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that adding duplicate teacher is rejected."""
        # Create organization
        org = create_org_via_api(test_client, auth_headers, "Test Org - Duplicate")
        org_id = org["id"]

        # Create second teacher
        from models import Teacher
        teacher2 = Teacher(
            name="Teacher Duplicate",
            email="teacher_dup@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(teacher2)
        shared_test_session.commit()
        shared_test_session.refresh(teacher2)
        teacher2_id = teacher2.id

        # Add teacher first time - success
        response1 = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teacher2_id,
            "org_admin"
        )
        assert response1.status_code in [200, 201]

        # Add same teacher second time - fail
        response2 = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teacher2_id,
            "org_admin"
        )
        assert response2.status_code == 400
        assert "already" in response2.text.lower()

    def test_add_teacher_org_owner_limit(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that only 1 org_owner is allowed per organization."""
        # Create organization (owner@duotopia.com is auto org_owner)
        org = create_org_via_api(test_client, auth_headers, "Test Org - Owner Limit")
        org_id = org["id"]

        # Create second teacher
        from models import Teacher
        teacher2 = Teacher(
            name="Second Owner",
            email="second_owner@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(teacher2)
        shared_test_session.commit()
        shared_test_session.refresh(teacher2)
        teacher2_id = teacher2.id

        # Try to add second org_owner - should fail
        response = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teacher2_id,
            "org_owner"
        )

        assert response.status_code == 400
        assert "owner" in response.text.lower()

    def test_add_teacher_teacher_limit_enforcement(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that teacher_limit is properly enforced."""
        # Create organization with limit of 2
        org = create_org_via_api(
            test_client,
            auth_headers,
            "Test Org - Limit",
            teacher_limit=2
        )
        org_id = org["id"]

        # Create 3 additional teachers
        from models import Teacher
        teachers = []
        for i in range(3):
            teacher = Teacher(
                name=f"Teacher Limit {i}",
                email=f"teacher_limit_{i}@test.com",
                password_hash="dummy",
                is_active=True
            )
            shared_test_session.add(teacher)
            teachers.append(teacher)

        shared_test_session.commit()
        for t in teachers:
            shared_test_session.refresh(t)

        # Add first teacher (count = 1, excluding owner) - should succeed
        response1 = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teachers[0].id,
            "org_admin"
        )
        assert response1.status_code in [200, 201]

        # Add second teacher (count = 2) - should succeed
        response2 = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teachers[1].id,
            "org_admin"
        )
        assert response2.status_code in [200, 201]

        # Add third teacher (count = 3, exceeds limit) - should fail
        response3 = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            teachers[2].id,
            "org_admin"
        )
        assert response3.status_code == 400
        assert "limit" in response3.text.lower() or "授權" in response3.text

    def test_add_teacher_to_nonexistent_org(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that adding teacher to nonexistent org fails (404)."""
        # Create teacher
        from models import Teacher
        teacher = Teacher(
            name="Teacher NoOrg",
            email="teacher_noorg@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(teacher)
        shared_test_session.commit()
        shared_test_session.refresh(teacher)

        # Try to add to nonexistent org (invalid UUID format will cause error)
        import uuid
        fake_org_id = str(uuid.uuid4())

        response = add_teacher_via_api(
            test_client,
            auth_headers,
            fake_org_id,
            teacher.id,
            "org_admin"
        )

        assert response.status_code in [403, 404]

    def test_add_teacher_nonexistent_teacher_id(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that adding nonexistent teacher_id fails (404)."""
        # Create organization
        org = create_org_via_api(test_client, auth_headers, "Test Org - No Teacher")
        org_id = org["id"]

        # Try to add nonexistent teacher
        response = add_teacher_via_api(
            test_client,
            auth_headers,
            org_id,
            99999,  # Nonexistent teacher_id
            "org_admin"
        )

        assert response.status_code == 404


# ============================================================================
# Test Class: Organization Stats
# ============================================================================

class TestOrganizationStats:
    """Tests for GET /stats endpoint (83 lines coverage)."""

    def test_get_stats_with_organizations(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test stats with multiple organizations and data."""
        # Create 2 organizations
        org1 = create_org_via_api(test_client, auth_headers, "Stats Org 1")
        org2 = create_org_via_api(test_client, auth_headers, "Stats Org 2")

        # Get stats
        stats = get_stats_via_api(test_client, auth_headers)

        # Assertions
        assert stats["total_organizations"] >= 2
        assert "total_schools" in stats
        assert "total_teachers" in stats
        assert "total_students" in stats

    def test_get_stats_empty(
        self,
        test_client: TestClient,
        shared_test_session: Session
    ):
        """Test stats return zeros when teacher has no organizations."""
        # Create new teacher with no orgs
        from models import Teacher
        new_teacher = Teacher(
            name="Empty Stats",
            email="empty_stats@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(new_teacher)
        shared_test_session.commit()
        shared_test_session.refresh(new_teacher)

        # Create auth token for new teacher
        from datetime import datetime, timedelta
        from core.security import create_access_token

        access_token = create_access_token(
            data={"sub": str(new_teacher.id)},
            expires_delta=timedelta(minutes=30)
        )
        new_headers = {"Authorization": f"Bearer {access_token}"}

        # Get stats
        stats = get_stats_via_api(test_client, new_headers)

        # Assertions - should all be zero
        assert stats["total_organizations"] == 0
        assert stats["total_schools"] == 0
        assert stats["total_teachers"] == 0
        assert stats["total_students"] == 0

    def test_get_stats_aggregation(
        self,
        test_client: TestClient,
        auth_headers: dict,
        shared_test_session: Session
    ):
        """Test that stats correctly aggregate across multiple orgs."""
        # Create 2 organizations
        org1 = create_org_via_api(test_client, auth_headers, "Agg Org 1")
        org2 = create_org_via_api(test_client, auth_headers, "Agg Org 2")

        # Add teacher to org1
        from models import Teacher
        teacher1 = Teacher(
            name="Agg Teacher 1",
            email="agg_teacher1@test.com",
            password_hash="dummy",
            is_active=True
        )
        shared_test_session.add(teacher1)
        shared_test_session.commit()
        shared_test_session.refresh(teacher1)

        add_teacher_via_api(
            test_client,
            auth_headers,
            org1["id"],
            teacher1.id,
            "org_admin"
        )

        # Get stats
        stats = get_stats_via_api(test_client, auth_headers)

        # Verify aggregation
        assert stats["total_organizations"] >= 2
        assert stats["total_teachers"] >= 2  # owner + agg_teacher1

    def test_get_stats_requires_auth(
        self,
        test_client: TestClient
    ):
        """Test that stats endpoint requires authentication."""
        # Try to get stats without auth headers
        response = test_client.get("/api/organizations/stats")

        # Should fail with 401 Unauthorized
        assert response.status_code == 401
