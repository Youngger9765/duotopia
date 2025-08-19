#!/usr/bin/env python3
"""
Test script to verify the login flow
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_teacher_login():
    print("Testing Teacher Login...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "teacher1@duotopia.com",
            "password": "password123"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Teacher login successful!")
        print(f"Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Teacher login failed: {response.text}")
        return None

def test_student_flow():
    print("\nTesting Student Login Flow...")
    
    # Step 1: Search teacher
    print("1. Searching for teacher...")
    response = requests.get(f"{BASE_URL}/api/students/teachers/search?email=teacher1@duotopia.com")
    if response.status_code != 200:
        print(f"❌ Teacher search failed: {response.text}")
        return
    
    teacher = response.json()
    print(f"✅ Found teacher: {teacher['full_name']} (ID: {teacher['id']})")
    
    # Step 2: Get classes
    print("\n2. Getting teacher's classes...")
    response = requests.get(f"{BASE_URL}/api/students/teachers/{teacher['id']}/classes")
    if response.status_code != 200:
        print(f"❌ Get classes failed: {response.text}")
        return
    
    classes = response.json()
    print(f"✅ Found {len(classes)} classes:")
    for cls in classes:
        print(f"   - {cls['name']} (ID: {cls['id']})")
    
    if not classes:
        print("❌ No classes found")
        return
    
    # Step 3: Get students
    class_id = classes[0]['id']
    print(f"\n3. Getting students in {classes[0]['name']}...")
    response = requests.get(f"{BASE_URL}/api/students/classes/{class_id}/students")
    if response.status_code != 200:
        print(f"❌ Get students failed: {response.text}")
        return
    
    students = response.json()
    print(f"✅ Found {len(students)} students:")
    for student in students[:3]:  # Show first 3
        print(f"   - {student['full_name']} ({student['email']})")
    
    if not students:
        print("❌ No students found")
        return
    
    # Step 4: Verify password
    student_id = students[0]['id']
    print(f"\n4. Verifying password for {students[0]['full_name']}...")
    
    # Get the student's birth date from database to test
    # In real scenario, user would know their birth date
    response = requests.post(
        f"{BASE_URL}/api/students/verify-password",
        json={
            "student_id": student_id,
            "password": "20120512"  # First student's birth date from seed
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Student login successful!")
        print(f"Token: {data['access_token'][:50]}...")
        print(f"Student: {data['student']['name']} ({data['student']['email']})")
    else:
        print(f"❌ Student login failed: {response.text}")

def test_frontend_access():
    print("\nTesting Frontend Access...")
    
    # Test frontend
    try:
        response = requests.get("http://localhost:5174/")
        if response.status_code == 200:
            print("✅ Frontend is accessible at http://localhost:5174/")
        else:
            print(f"❌ Frontend returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Frontend is not running on port 5174")
        
    # Test backend docs
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print(f"✅ API docs are accessible at {BASE_URL}/docs")
        else:
            print(f"❌ API docs returned status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")

if __name__ == "__main__":
    print("🧪 Duotopia Login Test\n")
    
    test_frontend_access()
    test_teacher_login()
    test_student_flow()
    
    print("\n✅ All tests completed!")
    print("\nYou can now:")
    print("1. Access the frontend at http://localhost:5174/")
    print("2. Login as teacher: teacher1@duotopia.com / password123")
    print("3. Login as student: Follow the 4-step flow with teacher email")
    print("   - Student passwords are their birth dates in YYYYMMDD format")