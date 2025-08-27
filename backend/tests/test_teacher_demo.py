#!/usr/bin/env python3
"""
Test teacher demo login and API endpoints
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_teacher_login():
    """Test demo teacher login"""
    print("Testing demo teacher login...")
    
    # Login with demo account
    login_data = {
        "email": "demo@duotopia.com",
        "password": "demo123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/teacher/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Login successful!")
        print(f"   Access token: {data['access_token'][:20]}...")
        return data['access_token']
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_teacher_dashboard(token):
    """Test teacher dashboard endpoint"""
    print("\nTesting teacher dashboard...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teacher/dashboard", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Dashboard loaded successfully!")
        print(f"   Teacher: {data['teacher']['name']} ({data['teacher']['email']})")
        print(f"   Total classrooms: {data['statistics']['total_classrooms']}")
        print(f"   Total students: {data['statistics']['total_students']}")
        print(f"   Total programs: {data['statistics']['total_programs']}")
    else:
        print(f"❌ Dashboard failed: {response.status_code}")
        print(f"   Response: {response.text}")

def test_teacher_classrooms(token):
    """Test teacher classrooms endpoint"""
    print("\nTesting teacher classrooms...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teacher/classrooms", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Classrooms loaded successfully!")
        for classroom in data:
            print(f"   - {classroom['name']}: {len(classroom.get('students', []))} students")
        return data
    else:
        print(f"❌ Classrooms failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return []

def test_teacher_programs(token):
    """Test teacher programs endpoint"""
    print("\nTesting teacher programs...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teacher/programs", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Programs loaded successfully!")
        for program in data:
            print(f"   - {program['name']} (Level: {program['level']})")
            print(f"     Classroom: {program.get('classroom_name', 'Unknown')}")
        return data
    else:
        print(f"❌ Programs failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return []

def main():
    print("=" * 50)
    print("Testing Teacher Demo Account & APIs")
    print("=" * 50)
    
    # Step 1: Login
    token = test_teacher_login()
    if not token:
        print("\n❌ Cannot proceed without login token")
        return 1
    
    # Step 2: Test dashboard
    test_teacher_dashboard(token)
    
    # Step 3: Test classrooms
    classrooms = test_teacher_classrooms(token)
    
    # Step 4: Test programs
    programs = test_teacher_programs(token)
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"✅ Found {len(classrooms)} classrooms")
    print(f"✅ Found {len(programs)} programs")
    
    if len(classrooms) == 0:
        print("⚠️  No classrooms found - seed data may not be loaded")
    if len(programs) == 0:
        print("⚠️  No programs found - seed data may not be loaded")
    
    print("=" * 50)
    return 0

if __name__ == "__main__":
    sys.exit(main())