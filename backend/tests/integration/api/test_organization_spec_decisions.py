"""
Integration tests for Organization Spec Decisions (#151)

Tests all spec decisions:
1. Soft Delete Strategy (is_active=False, hidden from queries)
2. tax_id Partial Unique Index (reuse after soft delete)
3. org_owner Uniqueness Constraint (one active org_owner per org)
4. Teacher Limit Enforcement (sequential + concurrent)
5. Race Condition Prevention (SELECT FOR UPDATE)

Migrated from live API tests to pytest fixtures for local execution.
"""

import pytest
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from typing import Optional

from models import Teacher, Organization, TeacherOrganization
from auth import create_access_token, get_password_hash


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_owner(shared_test_session: Session):
    """Create a test organization owner"""
    teacher = Teacher(
        email=f"owner_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("owner123"),
        name="Test Org Owner",
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(test_owner: Teacher):
    """Generate auth headers for test owner"""
    token = create_access_token({"sub": str(test_owner.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Helper Functions
# ============================================================================


def create_org_via_api(
    test_client,
    auth_headers,
    name: str,
    tax_id: Optional[str] = None,
    teacher_limit: Optional[int] = None,
):
    """Helper: Create organization via API"""
    payload = {"name": name}
    if tax_id:
        payload["tax_id"] = tax_id
    if teacher_limit is not None:
        payload["teacher_limit"] = teacher_limit

    response = test_client.post(
        "/api/organizations",
        json=payload,
        headers=auth_headers,
    )
    return response


def delete_org_via_api(test_client, auth_headers, org_id: str):
    """Helper: Delete organization via API (soft delete)"""
    response = test_client.delete(
        f"/api/organizations/{org_id}",
        headers=auth_headers,
    )
    return response


def list_orgs_via_api(test_client, auth_headers):
    """Helper: List organizations via API"""
    response = test_client.get(
        "/api/organizations",
        headers=auth_headers,
    )
    return response


def invite_teacher_via_api(
    test_client, auth_headers, org_id: str, email: str, name: str, role: str = "teacher"
):
    """Helper: Invite teacher to organization via API"""
    response = test_client.post(
        f"/api/organizations/{org_id}/teachers/invite",
        json={
            "email": email,
            "name": name,
            "role": role,
        },
        headers=auth_headers,
    )
    return response


# ============================================================================
# Test Decision #1: Soft Delete Strategy
# ============================================================================


class TestDecision1SoftDelete:
    """
    Decision #1: Soft Delete Strategy
    - Delete should set is_active=False
    - Deleted orgs should not appear in queries
    """

    def test_soft_delete_hides_from_list(self, test_client, auth_headers):
        """Test that soft deleted orgs don't appear in organization list"""
        # Create test org
        create_resp = create_org_via_api(
            test_client, auth_headers, "Soft Delete Test Org"
        )
        assert create_resp.status_code == 201
        org_data = create_resp.json()
        org_id = org_data["id"]

        # Verify it appears in list
        list_resp = list_orgs_via_api(test_client, auth_headers)
        assert list_resp.status_code == 200
        org_ids_before = [org["id"] for org in list_resp.json()]
        assert org_id in org_ids_before, "Org should appear in list before delete"

        # Soft delete
        delete_resp = delete_org_via_api(test_client, auth_headers, org_id)
        assert delete_resp.status_code == 200, f"Delete failed: {delete_resp.text}"

        # Verify it does NOT appear in list
        time.sleep(0.1)  # Small delay for consistency
        list_resp = list_orgs_via_api(test_client, auth_headers)
        assert list_resp.status_code == 200
        org_ids_after = [org["id"] for org in list_resp.json()]
        assert (
            org_id not in org_ids_after
        ), "Org should NOT appear in list after soft delete"


# ============================================================================
# Test Decision #2: tax_id Partial Unique Index
# ============================================================================


class TestDecision2TaxIdReuse:
    """
    Decision #2: tax_id Partial Unique Index
    - Active orgs cannot share tax_id
    - After soft delete, tax_id can be reused
    """

    def test_tax_id_unique_for_active_orgs(self, test_client, auth_headers):
        """Test that active orgs cannot share the same tax_id"""
        test_tax_id = f"TAX{uuid.uuid4().hex[:8]}"

        # Create first org with tax_id
        resp1 = create_org_via_api(
            test_client, auth_headers, "Tax ID Test Org 1", tax_id=test_tax_id
        )
        assert resp1.status_code == 201
        org1 = resp1.json()

        # Try to create second org with SAME tax_id (should fail)
        resp2 = create_org_via_api(
            test_client, auth_headers, "Tax ID Test Org 2", tax_id=test_tax_id
        )
        assert resp2.status_code in [
            400,
            409,
        ], f"Expected 400/409, got {resp2.status_code}: {resp2.text}"
        assert (
            "tax_id" in resp2.text.lower()
            or "統一編號" in resp2.text
            or "duplicate" in resp2.text.lower()
            or "已被使用" in resp2.text
        )

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org1["id"])

    def test_tax_id_reusable_after_soft_delete(self, test_client, auth_headers):
        """Test that tax_id can be reused after soft delete"""
        test_tax_id = f"TAX{uuid.uuid4().hex[:8]}"

        # Create first org with tax_id
        resp1 = create_org_via_api(
            test_client, auth_headers, "Tax ID Reuse Test 1", tax_id=test_tax_id
        )
        assert resp1.status_code == 201
        org1 = resp1.json()

        # Soft delete org1
        delete_resp = delete_org_via_api(test_client, auth_headers, org1["id"])
        assert delete_resp.status_code == 200

        # Now create org with SAME tax_id (should succeed)
        time.sleep(0.1)  # Small delay
        resp2 = create_org_via_api(
            test_client, auth_headers, "Tax ID Reuse Test 2", tax_id=test_tax_id
        )
        assert (
            resp2.status_code == 201
        ), f"Expected 201, got {resp2.status_code}: {resp2.text}"
        org2 = resp2.json()
        assert org2["tax_id"] == test_tax_id

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org2["id"])


# ============================================================================
# Test Decision #3: org_owner Uniqueness
# ============================================================================


class TestDecision3OrgOwnerUniqueness:
    """
    Decision #3: org_owner Unique Constraint
    - Each org can only have ONE active org_owner
    """

    def test_org_has_single_org_owner(
        self, test_client, auth_headers, shared_test_session: Session
    ):
        """Test that organization has exactly one org_owner after creation"""
        # Create test org
        create_resp = create_org_via_api(test_client, auth_headers, "Org Owner Test")
        assert create_resp.status_code == 201
        org_data = create_resp.json()
        org_id = org_data["id"]

        # Query database to verify exactly 1 org_owner
        owner_count = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == org_id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .count()
        )
        assert owner_count == 1, f"Expected 1 org_owner, found {owner_count}"

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org_id)


# ============================================================================
# Test Decision #4: Teacher Limit Enforcement
# ============================================================================


class TestDecision4TeacherLimit:
    """
    Decision #4: Teacher Limit Enforcement
    - Sequential invitations respect teacher_limit
    - Limit enforcement is consistent
    """

    def test_sequential_teacher_limit_enforcement(self, test_client, auth_headers):
        """Test that teacher limit is enforced in sequential invitations"""
        teacher_limit = 2

        # Create org with teacher_limit
        create_resp = create_org_via_api(
            test_client, auth_headers, "Teacher Limit Test", teacher_limit=teacher_limit
        )
        assert create_resp.status_code == 201
        org_data = create_resp.json()
        org_id = org_data["id"]

        # Try to invite 3 teachers (limit is 2)
        results = []
        for i in range(1, 4):
            email = f"teacher{i}_{uuid.uuid4().hex[:8]}@test.com"
            name = f"Test Teacher {i}"
            resp = invite_teacher_via_api(
                test_client, auth_headers, org_id, email, name
            )
            results.append(
                {
                    "request": i,
                    "status": resp.status_code,
                    "success": resp.status_code in [200, 201],
                }
            )

            # Small delay between requests
            time.sleep(0.1)

        # Verify: First 2 succeed, 3rd fails
        assert results[0]["success"], "First invitation should succeed"
        assert results[1]["success"], "Second invitation should succeed"
        assert not results[2]["success"], "Third invitation should fail (limit reached)"

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org_id)


# ============================================================================
# Test Decision #5: Race Condition Prevention
# ============================================================================


class TestDecision5RaceConditionPrevention:
    """
    Decision #5: Race Condition Prevention
    - Concurrent invitations handled correctly
    - SELECT FOR UPDATE prevents race conditions
    - Success count never exceeds teacher_limit
    """

    def test_concurrent_teacher_invitations_prevent_race_condition(
        self, test_client, auth_headers
    ):
        """Test that concurrent invitations don't bypass teacher_limit"""
        teacher_limit = 2
        concurrent_requests = 5

        # Create org with teacher_limit
        create_resp = create_org_via_api(
            test_client,
            auth_headers,
            "Concurrent Test Org",
            teacher_limit=teacher_limit,
        )
        assert create_resp.status_code == 201
        org_data = create_resp.json()
        org_id = org_data["id"]

        # Prepare concurrent requests
        def invite_concurrent(request_num: int):
            """Helper to make concurrent invite request"""
            email = f"concurrent{request_num}_{uuid.uuid4().hex[:8]}@test.com"
            name = f"Concurrent Teacher {request_num}"
            start_time = time.time()
            resp = invite_teacher_via_api(
                test_client, auth_headers, org_id, email, name
            )
            duration = time.time() - start_time

            return {
                "request": request_num,
                "status": resp.status_code,
                "success": resp.status_code in [200, 201],
                "duration": duration,
            }

        # Execute concurrent invitations
        results = []
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [
                executor.submit(invite_concurrent, i)
                for i in range(1, concurrent_requests + 1)
            ]

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

        # Sort by request number
        results.sort(key=lambda x: x["request"])

        # Count successes
        success_count = sum(1 for r in results if r["success"])
        failure_count = sum(1 for r in results if not r["success"])

        # Verify: Success count should NOT exceed teacher_limit
        assert success_count <= teacher_limit, (
            f"Race condition detected! Success count ({success_count}) exceeded limit ({teacher_limit}). "
            f"SELECT FOR UPDATE should prevent this."
        )

        # At least some requests should fail
        assert failure_count > 0, "Some requests should fail when limit is reached"

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org_id)


# ============================================================================
# Comprehensive Integration Test
# ============================================================================


class TestOrganizationSpecDecisionsE2E:
    """End-to-end test covering all spec decisions"""

    def test_complete_organization_workflow(
        self, test_client, auth_headers, shared_test_session: Session
    ):
        """
        Complete workflow testing all spec decisions:
        1. Create org with tax_id and teacher_limit
        2. Verify org_owner uniqueness
        3. Test teacher limit enforcement
        4. Soft delete and verify
        5. Reuse tax_id after soft delete
        """
        test_tax_id = f"E2E{uuid.uuid4().hex[:8]}"
        teacher_limit = 2

        # Step 1: Create organization
        create_resp = create_org_via_api(
            test_client,
            auth_headers,
            "E2E Test Organization",
            tax_id=test_tax_id,
            teacher_limit=teacher_limit,
        )
        assert create_resp.status_code == 201
        org = create_resp.json()
        org_id = org["id"]

        # Step 2: Verify org_owner uniqueness
        owner_count = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == org_id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .count()
        )
        assert owner_count == 1

        # Step 3: Test teacher limit
        for i in range(1, 3):  # Invite 2 teachers (at limit)
            email = f"e2e_teacher{i}_{uuid.uuid4().hex[:8]}@test.com"
            resp = invite_teacher_via_api(
                test_client, auth_headers, org_id, email, f"E2E Teacher {i}"
            )
            assert resp.status_code in [200, 201]

        # 3rd invitation should fail
        email = f"e2e_teacher3_{uuid.uuid4().hex[:8]}@test.com"
        resp = invite_teacher_via_api(
            test_client, auth_headers, org_id, email, "E2E Teacher 3"
        )
        assert resp.status_code not in [
            200,
            201,
        ], "3rd invitation should fail (limit reached)"

        # Step 4: Soft delete
        delete_resp = delete_org_via_api(test_client, auth_headers, org_id)
        assert delete_resp.status_code == 200

        # Verify not in list
        list_resp = list_orgs_via_api(test_client, auth_headers)
        org_ids = [o["id"] for o in list_resp.json()]
        assert org_id not in org_ids

        # Step 5: Reuse tax_id
        create_resp2 = create_org_via_api(
            test_client, auth_headers, "E2E Reuse Org", tax_id=test_tax_id
        )
        assert create_resp2.status_code == 201
        org2 = create_resp2.json()
        assert org2["tax_id"] == test_tax_id

        # Cleanup
        delete_org_via_api(test_client, auth_headers, org2["id"])
