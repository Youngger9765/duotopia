#!/usr/bin/env python3
"""
Integration API Tests for Organization Portal Separation
Date: 2026-01-01
Purpose: Verify backend APIs before UI testing
"""

import requests
import json
import sys
from typing import Dict, Optional, List, Any

BASE_URL = "http://localhost:8000"

# Test accounts
ACCOUNTS = {
    "org_owner": {"email": "owner@duotopia.com", "password": "owner123", "name": "張機構"},
    "org_admin": {"email": "orgadmin@duotopia.com", "password": "orgadmin123", "name": "李管理"},
    "school_admin": {"email": "schooladmin@duotopia.com", "password": "schooladmin123", "name": "王校長"},
    "teacher": {"email": "orgteacher@duotopia.com", "password": "orgteacher123", "name": "陳老師"},
}

# Test results
test_results = []
total_tests = 0
passed_tests = 0
failed_tests = 0


def log_test(name: str, status: str, details: str = ""):
    """Log test result"""
    global total_tests, passed_tests, failed_tests

    total_tests += 1
    if status == "PASS":
        passed_tests += 1
        print(f"✓ PASS - {name}")
    else:
        failed_tests += 1
        print(f"✗ FAIL - {name}")

    if details:
        print(f"   Details: {details}")

    test_results.append({"name": name, "status": status, "details": details})
    print()


def login(role: str) -> Optional[str]:
    """Login and return access token"""
    account = ACCOUNTS.get(role)
    if not account:
        return None

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/teacher/login",
            json={"email": account["email"], "password": account["password"]},
            timeout=5,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("access_token")
        else:
            print(f"   Login failed for {role}: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"   Login error for {role}: {e}")
        return None


def test_authentication():
    """Stage 1: Test authentication for all roles"""
    print("=" * 60)
    print("Stage 1: Authentication Tests")
    print("=" * 60)
    print()

    tokens = {}

    for role, account in ACCOUNTS.items():
        print(f"Test 1.{list(ACCOUNTS.keys()).index(role) + 1}: Login as {role} ({account['email']})")
        token = login(role)

        if token:
            tokens[role] = token
            log_test(
                f"Login as {role}",
                "PASS",
                f"Token received, Expected name: {account['name']}",
            )
        else:
            log_test(f"Login as {role}", "FAIL", "No token received")

    return tokens


def test_organization_apis(tokens: Dict[str, str]):
    """Stage 2: Test organization APIs"""
    print("=" * 60)
    print("Stage 2: Organization API Tests")
    print("=" * 60)
    print()

    # Test 2.1: org_owner can list organizations
    print("Test 2.1: org_owner list organizations")
    if "org_owner" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/organizations",
                headers={"Authorization": f"Bearer {tokens['org_owner']}"},
                timeout=5,
            )

            if response.status_code == 200:
                orgs = response.json()
                log_test(
                    "org_owner list organizations",
                    "PASS",
                    f"HTTP 200, Organizations: {len(orgs)}",
                )
                return orgs  # Return for later tests
            else:
                log_test(
                    "org_owner list organizations",
                    "FAIL",
                    f"HTTP {response.status_code}: {response.text}",
                )
        except Exception as e:
            log_test("org_owner list organizations", "FAIL", f"Exception: {e}")
    else:
        log_test("org_owner list organizations", "FAIL", "No org_owner token")

    # Test 2.2: org_admin can list organizations
    print("Test 2.2: org_admin list organizations")
    if "org_admin" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/organizations",
                headers={"Authorization": f"Bearer {tokens['org_admin']}"},
                timeout=5,
            )

            if response.status_code == 200:
                orgs = response.json()
                log_test(
                    "org_admin list organizations",
                    "PASS",
                    f"HTTP 200, Organizations: {len(orgs)}",
                )
            else:
                log_test(
                    "org_admin list organizations",
                    "FAIL",
                    f"HTTP {response.status_code}",
                )
        except Exception as e:
            log_test("org_admin list organizations", "FAIL", f"Exception: {e}")
    else:
        log_test("org_admin list organizations", "FAIL", "No org_admin token")

    # Test 2.3: Pure teacher CANNOT list organizations (should get empty or minimal access)
    print("Test 2.3: Pure teacher cannot list organizations")
    if "teacher" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/organizations",
                headers={"Authorization": f"Bearer {tokens['teacher']}"},
                timeout=5,
            )

            if response.status_code == 200:
                orgs = response.json()
                # Teacher might get empty list or organizations they belong to
                # The key is they shouldn't get org management access
                log_test(
                    "Teacher organization access",
                    "PASS" if len(orgs) == 0 or all(org.get("role") == "teacher" for org in orgs if isinstance(org, dict)) else "WARN",
                    f"HTTP 200, Organizations visible: {len(orgs)} (Expected: 0 for pure teacher)",
                )
            elif response.status_code == 403:
                log_test(
                    "Teacher blocked from organizations", "PASS", "HTTP 403 (access denied)"
                )
            else:
                log_test(
                    "Teacher organization access", "FAIL", f"Unexpected HTTP {response.status_code}"
                )
        except Exception as e:
            log_test("Teacher organization access", "FAIL", f"Exception: {e}")
    else:
        log_test("Teacher organization access", "FAIL", "No teacher token")

    return []


def test_schools_api(tokens: Dict[str, str], organizations: List[Dict[str, Any]]):
    """Stage 3: Test schools API"""
    print("=" * 60)
    print("Stage 3: Schools API Tests")
    print("=" * 60)
    print()

    if not organizations:
        print("⚠ No organizations available, fetching...")
        if "org_owner" in tokens:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/organizations",
                    headers={"Authorization": f"Bearer {tokens['org_owner']}"},
                    timeout=5,
                )
                if response.status_code == 200:
                    organizations = response.json()
            except:
                pass

    if not organizations:
        log_test("Schools API tests", "SKIP", "No organizations available")
        return

    org_id = organizations[0]["id"]

    # Test 3.1: org_owner can list schools
    print(f"Test 3.1: org_owner list schools (org_id: {org_id})")
    if "org_owner" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/schools",
                headers={"Authorization": f"Bearer {tokens['org_owner']}"},
                params={"organization_id": org_id},
                timeout=5,
            )

            if response.status_code == 200:
                schools = response.json()
                log_test("org_owner list schools", "PASS", f"HTTP 200, Schools: {len(schools)}")
            else:
                log_test("org_owner list schools", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            log_test("org_owner list schools", "FAIL", f"Exception: {e}")
    else:
        log_test("org_owner list schools", "FAIL", "No org_owner token")

    # Test 3.2: Teacher CANNOT list schools (should have no access)
    print("Test 3.2: Teacher cannot list schools")
    if "teacher" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/schools",
                headers={"Authorization": f"Bearer {tokens['teacher']}"},
                params={"organization_id": org_id},
                timeout=5,
            )

            if response.status_code in [403, 401]:
                log_test("Teacher blocked from schools", "PASS", f"HTTP {response.status_code}")
            elif response.status_code == 200:
                schools = response.json()
                if len(schools) == 0:
                    log_test("Teacher school access", "PASS", "HTTP 200 with empty list")
                else:
                    log_test(
                        "Teacher school access",
                        "WARN",
                        f"Teacher can see {len(schools)} schools (may have school_admin role)",
                    )
            else:
                log_test("Teacher school access", "FAIL", f"Unexpected HTTP {response.status_code}")
        except Exception as e:
            log_test("Teacher school access", "FAIL", f"Exception: {e}")
    else:
        log_test("Teacher school access", "FAIL", "No teacher token")


def test_teachers_api(tokens: Dict[str, str], organizations: List[Dict[str, Any]]):
    """Stage 4: Test teachers API"""
    print("=" * 60)
    print("Stage 4: Teachers API Tests")
    print("=" * 60)
    print()

    if not organizations:
        print("⚠ No organizations available, fetching...")
        if "org_owner" in tokens:
            try:
                response = requests.get(
                    f"{BASE_URL}/api/organizations",
                    headers={"Authorization": f"Bearer {tokens['org_owner']}"},
                    timeout=5,
                )
                if response.status_code == 200:
                    organizations = response.json()
            except:
                pass

    if not organizations:
        log_test("Teachers API tests", "SKIP", "No organizations available")
        return

    org_id = organizations[0]["id"]

    # Test 4.1: org_owner can list teachers
    print(f"Test 4.1: org_owner list teachers (org_id: {org_id})")
    if "org_owner" in tokens:
        try:
            response = requests.get(
                f"{BASE_URL}/api/organizations/{org_id}/teachers",
                headers={"Authorization": f"Bearer {tokens['org_owner']}"},
                timeout=5,
            )

            if response.status_code == 200:
                teachers = response.json()
                log_test(
                    "org_owner list teachers", "PASS", f"HTTP 200, Teachers: {len(teachers)}"
                )
            else:
                log_test("org_owner list teachers", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            log_test("org_owner list teachers", "FAIL", f"Exception: {e}")
    else:
        log_test("org_owner list teachers", "FAIL", "No org_owner token")


def test_role_permissions(tokens: Dict[str, str]):
    """Stage 5: Test role-based permissions"""
    print("=" * 60)
    print("Stage 5: Role Permission Tests")
    print("=" * 60)
    print()

    # Test if each role can access teacher dashboard endpoint
    for role, token in tokens.items():
        print(f"Test 5.{list(tokens.keys()).index(role) + 1}: {role} access to teacher dashboard")
        try:
            response = requests.get(
                f"{BASE_URL}/api/teachers/dashboard",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )

            if response.status_code == 200:
                log_test(f"{role} teacher dashboard access", "PASS", "HTTP 200 (all teachers can access)")
            elif response.status_code in [401, 403]:
                log_test(
                    f"{role} teacher dashboard access",
                    "WARN",
                    f"HTTP {response.status_code} (may need subscription)",
                )
            else:
                log_test(
                    f"{role} teacher dashboard access",
                    "INFO",
                    f"HTTP {response.status_code}",
                )
        except Exception as e:
            log_test(f"{role} teacher dashboard access", "FAIL", f"Exception: {e}")


def print_summary():
    """Print test summary"""
    print("=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print()
    print(f"Total Tests: {total_tests}")
    print(f"✓ Passed: {passed_tests}")
    print(f"✗ Failed: {failed_tests}")
    print()

    if failed_tests == 0:
        print("✓ All tests passed! Backend is ready for UI testing.")
        return 0
    else:
        print(f"✗ {failed_tests} test(s) failed. Review issues before UI testing.")
        return 1


def main():
    """Main test execution"""
    print("\n")
    print("=" * 60)
    print("Organization Portal Integration API Testing")
    print("=" * 60)
    print()

    # Stage 1: Authentication
    tokens = test_authentication()

    if not tokens:
        print("✗ Authentication failed. Cannot proceed with API tests.")
        return 1

    # Stage 2: Organization APIs
    organizations = test_organization_apis(tokens)

    # Stage 3: Schools API
    test_schools_api(tokens, organizations)

    # Stage 4: Teachers API
    test_teachers_api(tokens, organizations)

    # Stage 5: Role Permissions
    test_role_permissions(tokens)

    # Print summary
    return print_summary()


if __name__ == "__main__":
    sys.exit(main())
