#!/usr/bin/env python3
"""Create a test program for a classroom."""
import requests
import json  # noqa: F401

# API configuration
API_URL = "http://localhost:8000"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """Login as teacher and return access token."""
    response = requests.post(
        f"{API_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")

    data = response.json()
    return data["access_token"]


def create_program(token, classroom_id):
    """Create a test program for a classroom."""
    headers = {"Authorization": f"Bearer {token}"}

    program_data = {
        "name": "測試英語課程",
        "description": "包含基礎英語對話和閱讀練習",
        "level": "A1",
        "classroom_id": classroom_id,
        "estimated_hours": 10,
    }

    response = requests.post(
        f"{API_URL}/api/teachers/programs", headers=headers, json=program_data
    )

    if response.status_code == 200:
        program = response.json()
        print(f"✅ Created program: {program['name']} (ID: {program['id']})")
        return program
    else:
        print(f"❌ Failed to create program: {response.status_code}")
        print(f"  Error: {response.text}")
        return None


def main():
    print("🔐 Logging in as teacher...")
    token = login_teacher()

    # Get classrooms to find one to add program to
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/teachers/classrooms", headers=headers)
    classrooms = response.json()

    if classrooms:
        # Use first classroom
        classroom = classrooms[0]
        print(
            f"\n📚 Creating program for classroom: {classroom['name']} (ID: {classroom['id']})"
        )

        program = create_program(token, classroom["id"])

        if program:
            # Check classroom again to see updated program count
            response = requests.get(
                f"{API_URL}/api/teachers/classrooms", headers=headers
            )
            updated_classrooms = response.json()
            updated = next(
                (c for c in updated_classrooms if c["id"] == classroom["id"]), None
            )

            if updated:
                print(f"\n✅ Classroom now has {updated['program_count']} program(s)")
    else:
        print("No classrooms found")


if __name__ == "__main__":
    main()
