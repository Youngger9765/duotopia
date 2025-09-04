#!/usr/bin/env python3
"""
Test CRUD operations for teacher's classrooms, students, and programs
Following TDD approach - write tests first, then implement
"""
import requests
import json  # noqa: F401
import sys
from typing import Dict, Any  # noqa: F401

BASE_URL = "http://localhost:8000"


class TeacherCRUDTest:
    def __init__(self):
        self.token = None
        self.teacher_id = None

    def login(self) -> bool:
        """Login as demo teacher"""
        print("🔐 Logging in as demo teacher...")
        response = requests.post(
            f"{BASE_URL}/api/auth/teacher/login",
            json={"email": "demo@duotopia.com", "password": "demo123"},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            print("✅ Login successful")
            return True
        print(f"❌ Login failed: {response.text}")
        return False

    def headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.token}"}

    def test_classroom_crud(self):
        """Test classroom CRUD operations"""
        print("\n📚 Testing Classroom CRUD Operations")
        print("=" * 50)

        # 1. CREATE - Create new classroom
        print("\n1️⃣ CREATE: Creating new classroom...")
        new_classroom = {"name": "測試班級", "description": "這是一個測試班級", "level": "A1"}
        response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms",
            json=new_classroom,
            headers=self.headers(),
        )
        if response.status_code == 200:
            classroom = response.json()
            classroom_id = classroom["id"]
            print(f"✅ Created classroom: {classroom['name']} (ID: {classroom_id})")
        else:
            print(f"❌ Failed to create classroom: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        # 2. READ - Get single classroom
        print(f"\n2️⃣ READ: Getting classroom {classroom_id}...")
        response = requests.get(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}", headers=self.headers()
        )
        if response.status_code == 200:
            classroom = response.json()
            print(f"✅ Retrieved classroom: {classroom['name']}")
        else:
            print(f"❌ Failed to get classroom: {response.status_code}")
            print(f"   Response: {response.text}")

        # 3. UPDATE - Update classroom
        print(f"\n3️⃣ UPDATE: Updating classroom {classroom_id}...")
        update_data = {"name": "更新的測試班級", "description": "這是更新後的描述", "level": "A2"}
        response = requests.put(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}",
            json=update_data,
            headers=self.headers(),
        )
        if response.status_code == 200:
            classroom = response.json()
            print(f"✅ Updated classroom: {classroom['name']}")
        else:
            print(f"❌ Failed to update classroom: {response.status_code}")
            print(f"   Response: {response.text}")

        # 4. DELETE - Delete classroom
        print(f"\n4️⃣ DELETE: Deleting classroom {classroom_id}...")
        response = requests.delete(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}", headers=self.headers()
        )
        if response.status_code == 200:
            print("✅ Classroom deleted successfully")
        else:
            print(f"❌ Failed to delete classroom: {response.status_code}")
            print(f"   Response: {response.text}")

        return True

    def test_student_crud(self):
        """Test student CRUD operations"""
        print("\n👥 Testing Student CRUD Operations")
        print("=" * 50)

        # First create a classroom for the student
        classroom_response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms",
            json={"name": "學生測試班級", "description": "用於學生CRUD測試", "level": "A1"},
            headers=self.headers(),
        )
        if classroom_response.status_code != 200:
            print("❌ Failed to create test classroom for students")
            return False
        classroom_id = classroom_response.json()["id"]

        # 1. CREATE - Create new student
        print("\n1️⃣ CREATE: Creating new student...")
        new_student = {
            "name": "測試學生",
            "email": "test_student@duotopia.com",
            "birthdate": "2012-05-15",  # 預設密碼將是 20120515
            "classroom_id": classroom_id,
            "student_id": "TEST001",
        }
        response = requests.post(
            f"{BASE_URL}/api/teachers/students",
            json=new_student,
            headers=self.headers(),
        )
        if response.status_code == 200:
            student = response.json()
            student_id = student["id"]
            print(f"✅ Created student: {student['name']} (ID: {student_id})")
            print(f"   Default password: {student.get('default_password', 'N/A')}")
        else:
            print(f"❌ Failed to create student: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        # 2. READ - Get single student
        print(f"\n2️⃣ READ: Getting student {student_id}...")
        response = requests.get(
            f"{BASE_URL}/api/teachers/students/{student_id}", headers=self.headers()
        )
        if response.status_code == 200:
            student = response.json()
            print(f"✅ Retrieved student: {student['name']}")
            print(f"   Password changed: {student.get('password_changed', False)}")
        else:
            print(f"❌ Failed to get student: {response.status_code}")
            print(f"   Response: {response.text}")

        # 3. UPDATE - Update student
        print(f"\n3️⃣ UPDATE: Updating student {student_id}...")
        update_data = {"name": "更新的測試學生", "student_id": "TEST002"}
        response = requests.put(
            f"{BASE_URL}/api/teachers/students/{student_id}",
            json=update_data,
            headers=self.headers(),
        )
        if response.status_code == 200:
            student = response.json()
            print(f"✅ Updated student: {student['name']}")
        else:
            print(f"❌ Failed to update student: {response.status_code}")
            print(f"   Response: {response.text}")

        # 4. BATCH CREATE - Create multiple students
        print("\n4️⃣ BATCH: Creating multiple students...")
        batch_students = [
            {
                "name": "批次學生1",
                "email": "batch1@duotopia.com",
                "birthdate": "2012-06-01",
            },
            {
                "name": "批次學生2",
                "email": "batch2@duotopia.com",
                "birthdate": "2012-06-02",
            },
            {
                "name": "批次學生3",
                "email": "batch3@duotopia.com",
                "birthdate": "2012-06-03",
            },
        ]
        response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}/students/batch",
            json={"students": batch_students},
            headers=self.headers(),
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Created {result.get('created_count', 0)} students in batch")
        else:
            print(f"❌ Failed to batch create students: {response.status_code}")
            print(f"   Response: {response.text}")

        # 5. DELETE - Delete student
        print(f"\n5️⃣ DELETE: Deleting student {student_id}...")
        response = requests.delete(
            f"{BASE_URL}/api/teachers/students/{student_id}", headers=self.headers()
        )
        if response.status_code == 200:
            print("✅ Student deleted successfully")
        else:
            print(f"❌ Failed to delete student: {response.status_code}")
            print(f"   Response: {response.text}")

        # Clean up - delete test classroom
        requests.delete(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}", headers=self.headers()
        )

        return True

    def test_program_crud(self):
        """Test program CRUD operations"""
        print("\n📖 Testing Program CRUD Operations")
        print("=" * 50)

        # First create a classroom for the program
        classroom_response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms",
            json={"name": "課程測試班級", "description": "用於課程CRUD測試", "level": "B1"},
            headers=self.headers(),
        )
        if classroom_response.status_code != 200:
            print("❌ Failed to create test classroom for programs")
            return False
        classroom_id = classroom_response.json()["id"]

        # 1. CREATE - Create new program
        print("\n1️⃣ CREATE: Creating new program...")
        new_program = {
            "name": "測試課程計畫",
            "description": "這是一個測試課程",
            "level": "B1",
            "classroom_id": classroom_id,
            "estimated_hours": 30,
        }
        response = requests.post(
            f"{BASE_URL}/api/teachers/programs",
            json=new_program,
            headers=self.headers(),
        )
        if response.status_code == 200:
            program = response.json()
            program_id = program["id"]
            print(f"✅ Created program: {program['name']} (ID: {program_id})")
        else:
            print(f"❌ Failed to create program: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        # 2. READ - Get single program
        print(f"\n2️⃣ READ: Getting program {program_id}...")
        response = requests.get(
            f"{BASE_URL}/api/teachers/programs/{program_id}", headers=self.headers()
        )
        if response.status_code == 200:
            program = response.json()
            print(f"✅ Retrieved program: {program['name']}")
            print(f"   Lessons: {len(program.get('lessons', []))}")
        else:
            print(f"❌ Failed to get program: {response.status_code}")
            print(f"   Response: {response.text}")

        # 3. ADD LESSON - Add lesson to program
        print(f"\n3️⃣ ADD LESSON: Adding lesson to program {program_id}...")
        new_lesson = {
            "name": "Unit 1: Test Lesson",
            "description": "測試課程單元",
            "order_index": 1,
            "estimated_minutes": 45,
        }
        response = requests.post(
            f"{BASE_URL}/api/teachers/programs/{program_id}/lessons",
            json=new_lesson,
            headers=self.headers(),
        )
        if response.status_code == 200:
            lesson = response.json()
            lesson_id = lesson["id"]
            print(f"✅ Added lesson: {lesson['name']} (ID: {lesson_id})")
        else:
            print(f"❌ Failed to add lesson: {response.status_code}")
            print(f"   Response: {response.text}")

        # 4. UPDATE - Update program
        print(f"\n4️⃣ UPDATE: Updating program {program_id}...")
        update_data = {
            "name": "更新的測試課程",
            "description": "這是更新後的課程描述",
            "estimated_hours": 40,
        }
        response = requests.put(
            f"{BASE_URL}/api/teachers/programs/{program_id}",
            json=update_data,
            headers=self.headers(),
        )
        if response.status_code == 200:
            program = response.json()
            print(f"✅ Updated program: {program['name']}")
        else:
            print(f"❌ Failed to update program: {response.status_code}")
            print(f"   Response: {response.text}")

        # 5. DELETE - Delete program
        print(f"\n5️⃣ DELETE: Deleting program {program_id}...")
        response = requests.delete(
            f"{BASE_URL}/api/teachers/programs/{program_id}", headers=self.headers()
        )
        if response.status_code == 200:
            print("✅ Program deleted successfully")
        else:
            print(f"❌ Failed to delete program: {response.status_code}")
            print(f"   Response: {response.text}")

        # Clean up - delete test classroom
        requests.delete(
            f"{BASE_URL}/api/teachers/classrooms/{classroom_id}", headers=self.headers()
        )

        return True


def main():
    print("=" * 60)
    print("🧪 Teacher CRUD Operations Test Suite")
    print("=" * 60)

    tester = TeacherCRUDTest()

    # Login first
    if not tester.login():
        print("\n❌ Cannot proceed without authentication")
        return 1

    # Run all CRUD tests
    tests_passed = 0
    tests_total = 3

    if tester.test_classroom_crud():
        tests_passed += 1

    if tester.test_student_crud():
        tests_passed += 1

    if tester.test_program_crud():
        tests_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
