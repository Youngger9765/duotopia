"""
Manual Integration Test for Organization Hierarchy

This script performs a complete end-to-end test of the organization hierarchy
feature using the actual running API server.

Run this AFTER starting the development server:
1. cd backend
2. python seed_data.py  # Reset database with demo data
3. uvicorn main:app --reload  # Start server (in separate terminal)
4. python tests/manual_test_organization_hierarchy.py  # Run this test

Expected: All tests pass ✅
"""

import requests

BASE_URL = "http://localhost:8000"

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")


def print_error(msg):
    print(f"{RED}❌ {msg}{RESET}")


def print_info(msg):
    print(f"{YELLOW}ℹ️  {msg}{RESET}")


def login_as_demo_teacher():
    """Login as demo teacher and return auth headers"""
    print_info("Logging in as demo@duotopia.com...")
    response = requests.post(
        f"{BASE_URL}/api/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    print_success("Login successful")
    return {"Authorization": f"Bearer {token}"}


def test_list_organizations(headers):
    """Test GET /api/organizations"""
    print_info("Testing: List organizations...")
    response = requests.get(f"{BASE_URL}/api/organizations", headers=headers)

    if response.status_code == 200:
        orgs = response.json()
        if len(orgs) >= 1:
            print_success(f"Found {len(orgs)} organization(s)")
            return orgs[0]["id"]  # Return first org ID for subsequent tests
        else:
            print_error("No organizations found (expected at least 1)")
            return None
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None


def test_get_organization(org_id, headers):
    """Test GET /api/organizations/{org_id}"""
    print_info(f"Testing: Get organization {org_id}...")
    response = requests.get(f"{BASE_URL}/api/organizations/{org_id}", headers=headers)

    if response.status_code == 200:
        org = response.json()
        print_success(f"Retrieved organization: {org['name']}")
        print(f"  Display Name: {org['display_name']}")
        print(f"  Contact Email: {org.get('contact_email', 'N/A')}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_list_schools(headers):
    """Test GET /api/schools"""
    print_info("Testing: List schools...")
    response = requests.get(f"{BASE_URL}/api/schools", headers=headers)

    if response.status_code == 200:
        schools = response.json()
        if len(schools) >= 2:  # Seed data has 2 schools
            print_success(f"Found {len(schools)} school(s)")
            for school in schools:
                print(f"  - {school['display_name']} ({school['name']})")
            return schools[0]["id"]  # Return first school ID
        else:
            print_error(f"Expected at least 2 schools, found {len(schools)}")
            return None
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None


def test_get_school(school_id, headers):
    """Test GET /api/schools/{school_id}"""
    print_info(f"Testing: Get school {school_id}...")
    response = requests.get(f"{BASE_URL}/api/schools/{school_id}", headers=headers)

    if response.status_code == 200:
        school = response.json()
        print_success(f"Retrieved school: {school['display_name']}")
        print(f"  Organization: {school.get('organization_id')}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_get_organization_teachers(org_id, headers):
    """Test GET /api/organizations/{org_id}/teachers"""
    print_info("Testing: Get organization teachers...")
    response = requests.get(
        f"{BASE_URL}/api/organizations/{org_id}/teachers", headers=headers
    )

    if response.status_code == 200:
        teachers = response.json()
        print_success(f"Found {len(teachers)} teacher(s)")
        for teacher in teachers:
            print(
                f"  - {teacher['name']} ({teacher['email']}) - Role: {teacher['role']}"
            )
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_get_school_teachers(school_id, headers):
    """Test GET /api/schools/{school_id}/teachers"""
    print_info("Testing: Get school teachers...")
    response = requests.get(
        f"{BASE_URL}/api/schools/{school_id}/teachers", headers=headers
    )

    if response.status_code == 200:
        teachers = response.json()
        print_success(f"Found {len(teachers)} teacher(s)")
        for teacher in teachers:
            roles_str = ", ".join(teacher.get("roles", []))
            print(f"  - {teacher['name']} ({teacher['email']}) - Roles: {roles_str}")
        return True
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return False


def test_create_and_update_organization(headers):
    """Test POST /api/organizations and PATCH"""
    print_info("Testing: Create new organization...")
    response = requests.post(
        f"{BASE_URL}/api/organizations",
        json={
            "name": "test-manual-org",
            "display_name": "Manual Test Organization",
            "contact_email": "test@manual.com",
        },
        headers=headers,
    )

    if response.status_code == 201:
        org = response.json()
        print_success(f"Created organization: {org['id']}")

        # Test update
        print_info("Testing: Update organization...")
        update_response = requests.patch(
            f"{BASE_URL}/api/organizations/{org['id']}",
            json={"display_name": "Updated Manual Test Org"},
            headers=headers,
        )

        if update_response.status_code == 200:
            updated_org = update_response.json()
            if updated_org["display_name"] == "Updated Manual Test Org":
                print_success("Organization updated successfully")
                return org["id"]
            else:
                print_error("Update didn't persist")
                return None
        else:
            print_error(f"Update failed: {update_response.status_code}")
            return None
    else:
        print_error(f"Create failed: {response.status_code} - {response.text}")
        return None


def test_create_school(org_id, headers):
    """Test POST /api/schools"""
    print_info("Testing: Create new school...")
    response = requests.post(
        f"{BASE_URL}/api/schools",
        json={
            "organization_id": org_id,
            "name": "test-manual-school",
            "display_name": "Manual Test School",
        },
        headers=headers,
    )

    if response.status_code == 201:
        school = response.json()
        print_success(f"Created school: {school['id']}")
        return school["id"]
    else:
        print_error(f"Failed: {response.status_code} - {response.text}")
        return None


def main():
    print("\n" + "=" * 70)
    print("🧪 Organization Hierarchy Manual Integration Test")
    print("=" * 70 + "\n")

    try:
        # Step 1: Login
        headers = login_as_demo_teacher()

        # Step 2: Test organization listing
        org_id = test_list_organizations(headers)
        if not org_id:
            print_error("Cannot continue without organization ID")
            return

        # Step 3: Test get organization details
        test_get_organization(org_id, headers)

        # Step 4: Test get organization teachers
        test_get_organization_teachers(org_id, headers)

        # Step 5: Test school listing
        school_id = test_list_schools(headers)
        if school_id:
            test_get_school(school_id, headers)
            test_get_school_teachers(school_id, headers)

        # Step 6: Test create/update operations
        new_org_id = test_create_and_update_organization(headers)
        if new_org_id:
            # Create a school under the new org
            test_create_school(new_org_id, headers)

        print("\n" + "=" * 70)
        print_success("All manual tests completed!")
        print("=" * 70 + "\n")

    except Exception as e:
        print_error(f"Test failed with exception: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
