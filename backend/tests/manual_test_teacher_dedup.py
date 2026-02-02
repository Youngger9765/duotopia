"""
Manual test to verify teacher count deduplication fix for Issue #112 Error 6

This script demonstrates the bug and the fix:
- Creates an organization with one teacher as owner
- Creates a school under that organization
- Adds the same teacher to the school (giving them dual roles)
- Checks if the teacher count is correctly deduplicated (should be 1, not 2)

Run with: python -m pytest backend/tests/manual_test_teacher_dedup.py -v -s
"""

import pytest
from models import Teacher, Organization, TeacherOrganization, School, TeacherSchool
from auth import get_password_hash, create_access_token


def test_teacher_deduplication_scenario(shared_test_session, test_client):
    """
    Reproduce Issue #112 Error 6: Teacher count duplication bug

    SCENARIO:
    1. Teacher A creates an organization (becomes org_owner)
    2. Create a school under the organization
    3. Add Teacher A to the school as school_admin
    4. Check organization stats

    EXPECTED: teacher_count = 1 (Teacher A counted once)
    BUG (before fix): teacher_count = 2 (Teacher A counted twice)
    """
    print("\n" + "=" * 70)
    print("Testing Issue #112 Error 6: Teacher Count Deduplication")
    print("=" * 70)

    # Step 1: Create Teacher A
    teacher_a = Teacher(
        email="teacher_a@example.com",
        password_hash=get_password_hash("password"),
        name="Teacher A",
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher_a)
    shared_test_session.commit()
    shared_test_session.refresh(teacher_a)
    print(f"✓ Created Teacher A (id={teacher_a.id})")

    # Step 2: Create organization with Teacher A as owner
    org = Organization(
        name="Test Organization",
        display_name="測試組織",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    teacher_org = TeacherOrganization(
        teacher_id=teacher_a.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(teacher_org)
    shared_test_session.commit()
    print(f"✓ Created organization (id={org.id}) with Teacher A as org_owner")

    # Step 3: Create school under organization
    school = School(
        organization_id=org.id,
        name="Test School",
        display_name="測試學校",
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    print(f"✓ Created school (id={school.id}) under organization")

    # Step 4: Add Teacher A to school (now has dual roles)
    teacher_school = TeacherSchool(
        teacher_id=teacher_a.id,
        school_id=school.id,
        roles=["school_admin"],
        is_active=True,
    )
    shared_test_session.add(teacher_school)
    shared_test_session.commit()
    print(f"✓ Added Teacher A to school as school_admin")
    print(f"  → Teacher A now has roles: org_owner + school_admin")

    # Step 5: Get organization stats
    access_token = create_access_token(
        data={"sub": str(teacher_a.id), "type": "teacher"}
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    response = test_client.get("/api/organizations/stats", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    print("\n" + "-" * 70)
    print("Organization Stats:")
    print(f"  Organizations: {data['total_organizations']}")
    print(f"  Schools: {data['total_schools']}")
    print(f"  Teachers: {data['total_teachers']}")
    print(f"  Students: {data['total_students']}")
    print("-" * 70)

    # Verification
    print("\n" + "=" * 70)
    print("VERIFICATION:")
    print("=" * 70)
    print(f"Expected teacher count: 1 (Teacher A with dual roles)")
    print(f"Actual teacher count: {data['total_teachers']}")

    if data["total_teachers"] == 1:
        print("✅ PASS: Teacher correctly deduplicated!")
    else:
        print("❌ FAIL: Teacher counted multiple times (bug not fixed)")

    assert data["total_teachers"] == 1, (
        f"Teacher count should be 1 (unique teachers), "
        f"but got {data['total_teachers']}. "
        f"This indicates the deduplication fix is not working."
    )

    print("=" * 70 + "\n")


def test_multiple_teachers_with_overlapping_roles(shared_test_session, test_client):
    """
    More complex scenario: Multiple teachers with overlapping roles

    SCENARIO:
    - Teacher A: org_owner + school_admin (School 1)
    - Teacher B: school_admin (School 1) + teacher (School 2)
    - Teacher C: teacher (School 2)

    EXPECTED: teacher_count = 3 (A, B, C counted once each)
    """
    print("\n" + "=" * 70)
    print("Testing Complex Scenario: Multiple Teachers with Overlapping Roles")
    print("=" * 70)

    # Create teachers
    teachers = []
    for i, name in enumerate(["Teacher A", "Teacher B", "Teacher C"]):
        teacher = Teacher(
            email=f"teacher_{chr(97+i)}@example.com",
            password_hash=get_password_hash("password"),
            name=name,
            is_active=True,
            email_verified=True,
        )
        shared_test_session.add(teacher)
        teachers.append(teacher)
    shared_test_session.commit()
    print(f"✓ Created 3 teachers")

    # Create organization
    org = Organization(
        name="Multi-Teacher Org",
        display_name="多教師組織",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    # Teacher A as org_owner
    teacher_org = TeacherOrganization(
        teacher_id=teachers[0].id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(teacher_org)
    print(f"✓ Teacher A: org_owner")

    # Create School 1
    school1 = School(
        organization_id=org.id,
        name="School 1",
        is_active=True,
    )
    shared_test_session.add(school1)
    shared_test_session.commit()
    shared_test_session.refresh(school1)

    # Create School 2
    school2 = School(
        organization_id=org.id,
        name="School 2",
        is_active=True,
    )
    shared_test_session.add(school2)
    shared_test_session.commit()
    shared_test_session.refresh(school2)
    print(f"✓ Created 2 schools")

    # Teacher A: also school_admin at School 1
    shared_test_session.add(
        TeacherSchool(
            teacher_id=teachers[0].id,
            school_id=school1.id,
            roles=["school_admin"],
            is_active=True,
        )
    )
    print(f"✓ Teacher A: also school_admin at School 1")

    # Teacher B: school_admin at School 1
    shared_test_session.add(
        TeacherSchool(
            teacher_id=teachers[1].id,
            school_id=school1.id,
            roles=["school_admin"],
            is_active=True,
        )
    )
    print(f"✓ Teacher B: school_admin at School 1")

    # Teacher B: also teacher at School 2
    shared_test_session.add(
        TeacherSchool(
            teacher_id=teachers[1].id,
            school_id=school2.id,
            roles=["teacher"],
            is_active=True,
        )
    )
    print(f"✓ Teacher B: also teacher at School 2")

    # Teacher C: teacher at School 2
    shared_test_session.add(
        TeacherSchool(
            teacher_id=teachers[2].id,
            school_id=school2.id,
            roles=["teacher"],
            is_active=True,
        )
    )
    print(f"✓ Teacher C: teacher at School 2")

    shared_test_session.commit()

    # Get stats
    access_token = create_access_token(
        data={"sub": str(teachers[0].id), "type": "teacher"}
    )
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    response = test_client.get("/api/organizations/stats", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    print("\n" + "-" * 70)
    print("Organization Stats:")
    print(f"  Teachers: {data['total_teachers']}")
    print(f"  Schools: {data['total_schools']}")
    print("-" * 70)

    print("\n" + "=" * 70)
    print("VERIFICATION:")
    print("=" * 70)
    print("Role Summary:")
    print("  Teacher A: org_owner + school_admin (School 1)")
    print("  Teacher B: school_admin (School 1) + teacher (School 2)")
    print("  Teacher C: teacher (School 2)")
    print(f"\nExpected teacher count: 3")
    print(f"Actual teacher count: {data['total_teachers']}")

    if data["total_teachers"] == 3:
        print("✅ PASS: All teachers correctly deduplicated!")
    else:
        print("❌ FAIL: Teachers not properly deduplicated")

    assert (
        data["total_teachers"] == 3
    ), f"Should count 3 unique teachers, got {data['total_teachers']}"

    print("=" * 70 + "\n")
