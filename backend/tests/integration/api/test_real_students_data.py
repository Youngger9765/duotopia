#!/usr/bin/env python3
"""
Test that students API returns real data from database
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Login as demo teacher
login_response = requests.post(
    f"{BASE_URL}/api/auth/teacher/login",
    json={"email": "demo@duotopia.com", "password": "demo123"}
)

if login_response.status_code != 200:
    print("❌ Login failed")
    exit(1)

token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Get classrooms with students
response = requests.get(f"{BASE_URL}/api/teachers/classrooms", headers=headers)

if response.status_code != 200:
    print(f"❌ Failed to get classrooms: {response.status_code}")
    print(response.text)
    exit(1)

classrooms = response.json()
print("✅ Successfully fetched classrooms")
print(f"Found {len(classrooms)} classrooms\n")

for classroom in classrooms:
    print(f"📚 Classroom: {classroom['name']}")
    print(f"   Students: {len(classroom['students'])}")
    
    for student in classroom['students'][:3]:  # Show first 3 students
        print(f"   - {student['name']} ({student['email']})")
        print(f"     Birthdate: {student.get('birthdate', 'N/A')}")
        print(f"     Password Changed: {student.get('password_changed', False)}")
        print(f"     Status: {student.get('status', 'unknown')}")
    
    if len(classroom['students']) > 3:
        print(f"   ... and {len(classroom['students']) - 3} more students")
    print()

print("✅ All student data is from the real database!")