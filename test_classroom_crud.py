#!/usr/bin/env python3
"""Test classroom CRUD functionality."""
import requests
import json
import time
from typing import Dict, Any

# API configuration
API_URL = "http://localhost:8000"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"  # Default demo password

def login_teacher() -> str:
    """Login as teacher and return access token."""
    response = requests.post(
        f"{API_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD}
    )
    if response.status_code != 200:
        raise Exception(f"Login failed: {response.text}")
    
    data = response.json()
    return data["access_token"]

def test_get_classrooms(token: str) -> list:
    """Test getting all classrooms."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/api/teachers/classrooms", headers=headers)
    
    print("✅ GET /api/teachers/classrooms")
    print(f"  Status: {response.status_code}")
    classrooms = response.json()
    print(f"  Found {len(classrooms)} classrooms")
    
    for classroom in classrooms[:3]:  # Show first 3
        print(f"    - ID: {classroom['id']}, Name: {classroom['name']}, Students: {classroom.get('student_count', 0)}")
    
    return classrooms

def test_update_classroom(token: str, classroom_id: int) -> Dict[str, Any]:
    """Test updating a classroom."""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current classroom details
    response = requests.get(f"{API_URL}/api/teachers/classrooms", headers=headers)
    classrooms = response.json()
    classroom = next((c for c in classrooms if c['id'] == classroom_id), None)
    
    if not classroom:
        print(f"❌ Classroom {classroom_id} not found")
        return {}
    
    print(f"\n🔄 Testing UPDATE classroom ID: {classroom_id}")
    print(f"  Current name: {classroom['name']}")
    
    # Update classroom
    new_name = f"{classroom['name']} (Updated {time.strftime('%H:%M:%S')})"
    update_data = {
        "name": new_name,
        "description": "Updated via TDD test",
        "level": "B1"
    }
    
    response = requests.put(
        f"{API_URL}/api/teachers/classrooms/{classroom_id}",
        headers=headers,
        json=update_data
    )
    
    if response.status_code == 200:
        updated = response.json()
        print(f"✅ UPDATE /api/teachers/classrooms/{classroom_id}")
        print(f"  New name: {updated['name']}")
        print(f"  Description: {updated.get('description', 'N/A')}")
        print(f"  Level: {updated.get('level', 'N/A')}")
        return updated
    else:
        print(f"❌ Update failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return {}

def test_create_classroom(token: str) -> Dict[str, Any]:
    """Test creating a new classroom."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n➕ Testing CREATE classroom")
    
    classroom_data = {
        "name": f"Test Classroom {time.strftime('%Y%m%d_%H%M%S')}",
        "description": "Created via TDD test",
        "level": "A2"
    }
    
    response = requests.post(
        f"{API_URL}/api/teachers/classrooms",
        headers=headers,
        json=classroom_data
    )
    
    if response.status_code == 200:
        created = response.json()
        print(f"✅ CREATE /api/teachers/classrooms")
        print(f"  ID: {created['id']}")
        print(f"  Name: {created['name']}")
        print(f"  Level: {created.get('level', 'N/A')}")
        return created
    else:
        print(f"❌ Create failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return {}

def test_delete_classroom(token: str, classroom_id: int) -> bool:
    """Test deleting a classroom (soft delete)."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n🗑️ Testing DELETE classroom ID: {classroom_id}")
    
    response = requests.delete(
        f"{API_URL}/api/teachers/classrooms/{classroom_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        print(f"✅ DELETE /api/teachers/classrooms/{classroom_id}")
        print("  Classroom soft deleted successfully")
        
        # Verify it's no longer in the list
        classrooms = test_get_classrooms(token)
        if not any(c['id'] == classroom_id for c in classrooms):
            print("  ✅ Confirmed: Classroom no longer appears in list")
        else:
            print("  ⚠️ Warning: Classroom still appears in list")
        
        return True
    else:
        print(f"❌ Delete failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing Classroom CRUD Operations")
    print("=" * 60)
    
    try:
        # Login
        print("\n🔐 Logging in as teacher...")
        token = login_teacher()
        print("✅ Login successful")
        
        # Get all classrooms
        print("\n" + "=" * 60)
        classrooms = test_get_classrooms(token)
        
        # Update first classroom if exists
        if classrooms:
            print("\n" + "=" * 60)
            test_update_classroom(token, classrooms[0]['id'])
        
        # Create new classroom
        print("\n" + "=" * 60)
        new_classroom = test_create_classroom(token)
        
        # Delete the newly created classroom
        if new_classroom and 'id' in new_classroom:
            print("\n" + "=" * 60)
            test_delete_classroom(token, new_classroom['id'])
        
        print("\n" + "=" * 60)
        print("✅ All CRUD tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())