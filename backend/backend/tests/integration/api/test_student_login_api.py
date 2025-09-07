#!/usr/bin/env python3
"""Test student login API functionality"""
import requests

BASE_URL = "http://localhost:8000"


def test_student_login():
    """Test the complete student login flow"""

    print("=" * 60)
    print("Testing Student Login API")
    print("=" * 60)

    # Step 1: Test public teacher validation
    print("\n1. Testing teacher validation...")
    teacher_email = "demo@duotopia.com"

    response = requests.post(f"{BASE_URL}/api/public/validate-teacher", json={"email": teacher_email})

    if response.status_code == 200:
        teacher_data = response.json()
        print(f"✓ Teacher found: {teacher_data.get('name')}")
    else:
        print(f"✗ Teacher validation failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 2: Get classrooms for teacher
    print("\n2. Getting classrooms for teacher...")
    response = requests.get(f"{BASE_URL}/api/public/teacher-classrooms", params={"email": teacher_email})

    if response.status_code == 200:
        classrooms = response.json()
        print(f"✓ Found {len(classrooms)} classrooms")
        if classrooms:
            classroom = classrooms[0]
            classroom_id = classroom["id"]
            print(f"  Using classroom: {classroom['name']} (ID: {classroom_id})")
        else:
            print("✗ No classrooms found")
            return
    else:
        print(f"✗ Failed to get classrooms: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 3: Get students in classroom
    print("\n3. Getting students in classroom...")
    response = requests.get(f"{BASE_URL}/api/public/classroom-students/{classroom_id}")

    if response.status_code == 200:
        students = response.json()
        print(f"✓ Found {len(students)} students")
        if students:
            student = students[0]
            student_email = student["email"]
            student_name = student["name"]
            print(f"  Using student: {student_name} ({student_email})")
        else:
            print("✗ No students found")
            return
    else:
        print(f"✗ Failed to get students: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 4: Test student login
    print("\n4. Testing student login...")
    login_data = {"email": student_email, "password": "20120101"}  # Demo password

    response = requests.post(f"{BASE_URL}/api/auth/student/login", json=login_data)

    if response.status_code == 200:
        auth_data = response.json()
        print("✓ Student login successful!")
        print(f"  Token: {auth_data['access_token'][:20]}...")
        print(f"  User: {auth_data['user']}")
        token = auth_data["access_token"]
    else:
        print(f"✗ Student login failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return

    # Step 5: Test authenticated endpoints
    print("\n5. Testing authenticated endpoints...")
    headers = {"Authorization": f"Bearer {token}"}

    # Test profile endpoint
    print("  Testing /api/students/profile...")
    response = requests.get(f"{BASE_URL}/api/students/profile", headers=headers)

    if response.status_code == 200:
        profile = response.json()
        print(f"  ✓ Profile retrieved: {profile}")
    else:
        print(f"  ✗ Failed to get profile: {response.status_code}")
        print(f"    Response: {response.text}")

    # Test assignments endpoint
    print("\n  Testing /api/students/assignments...")
    response = requests.get(f"{BASE_URL}/api/students/assignments", headers=headers)

    if response.status_code == 200:
        assignments = response.json()
        print(f"  ✓ Assignments retrieved: Found {len(assignments)} assignments")
        if assignments:
            print(f"    First assignment: {assignments[0].get('title')}")
    else:
        print(f"  ✗ Failed to get assignments: {response.status_code}")
        print(f"    Response: {response.text}")

    print("\n" + "=" * 60)
    print("Student Login API Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_student_login()
