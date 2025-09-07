"""
Comprehensive tests for routers/public.py
Testing all public API endpoints that don't require authentication
"""

import pytest
from models import Teacher, Classroom, Student, ClassroomStudent, ProgramLevel
from auth import get_password_hash
from datetime import datetime  # noqa: F401


@pytest.fixture
def public_teacher(db):
    """Create a teacher for public API testing"""
    teacher = Teacher(
        email="public@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Public Teacher",
        phone="+1234567890",
        is_active=True,
        is_demo=False,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def public_teacher_with_data(db, public_teacher):
    """Create a teacher with classrooms and students"""
    # Create classrooms
    classroom1 = Classroom(
        name="Public Class 1",
        description="First public class",
        level=ProgramLevel.A1,
        teacher_id=public_teacher.id,
        is_active=True,
    )
    classroom2 = Classroom(
        name="Public Class 2",
        description="Second public class",
        level=ProgramLevel.A2,
        teacher_id=public_teacher.id,
        is_active=True,
    )
    # Create inactive classroom
    classroom3 = Classroom(
        name="Inactive Class",
        description="This is inactive",
        level=ProgramLevel.A1,
        teacher_id=public_teacher.id,
        is_active=False,
    )

    db.add_all([classroom1, classroom2, classroom3])
    db.commit()
    db.refresh(classroom1)
    db.refresh(classroom2)
    db.refresh(classroom3)

    # Create students
    students = []
    for i in range(5):
        student = Student(
            name=f"Public Student {i+1}",
            email=f"pubstudent{i+1}@example.com",
            student_id=f"PUB{i+1:03d}",
            password_hash=get_password_hash("20100101"),
            birthdate=datetime(2010, 1, 1).date(),
            is_active=True,
        )
        students.append(student)

    db.add_all(students)
    db.commit()
    for student in students:
        db.refresh(student)

    # Assign students to classrooms
    # Classroom1: 3 students, Classroom2: 2 students, Classroom3: 0 students
    classroom_assignments = [
        ClassroomStudent(classroom_id=classroom1.id, student_id=students[0].id, is_active=True),
        ClassroomStudent(classroom_id=classroom1.id, student_id=students[1].id, is_active=True),
        ClassroomStudent(classroom_id=classroom1.id, student_id=students[2].id, is_active=True),
        ClassroomStudent(classroom_id=classroom2.id, student_id=students[3].id, is_active=True),
        ClassroomStudent(classroom_id=classroom2.id, student_id=students[4].id, is_active=True),
    ]

    db.add_all(classroom_assignments)
    db.commit()

    return {
        "teacher": public_teacher,
        "classrooms": [classroom1, classroom2, classroom3],
        "students": students,
    }


class TestValidateTeacher:
    """Test teacher validation endpoint"""

    def test_validate_teacher_exists(self, client, public_teacher):
        """Test validating existing teacher"""
        request_data = {"email": "public@duotopia.com"}

        response = client.post("/api/public/validate-teacher", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["name"] == "Public Teacher"
        assert data["id"] == public_teacher.id

    def test_validate_teacher_not_exists(self, client):
        """Test validating non-existent teacher"""
        request_data = {"email": "nonexistent@duotopia.com"}

        response = client.post("/api/public/validate-teacher", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["name"] is None
        assert data["id"] is None

    def test_validate_teacher_case_insensitive(self, client, public_teacher):
        """Test that email validation is case insensitive"""
        test_cases = [
            "PUBLIC@DUOTOPIA.COM",
            "Public@Duotopia.Com",
            "public@DUOTOPIA.COM",
            "PUBLIC@duotopia.com",
        ]

        for email in test_cases:
            request_data = {"email": email}
            response = client.post("/api/public/validate-teacher", json=request_data)

            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["name"] == "Public Teacher"
            assert data["id"] == public_teacher.id

    def test_validate_teacher_invalid_email(self, client):
        """Test with invalid email format"""
        request_data = {"email": "invalid-email"}

        response = client.post("/api/public/validate-teacher", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_validate_teacher_missing_email(self, client):
        """Test with missing email field"""
        request_data = {}

        response = client.post("/api/public/validate-teacher", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_validate_teacher_empty_email(self, client):
        """Test with empty email"""
        request_data = {"email": ""}

        response = client.post("/api/public/validate-teacher", json=request_data)

        # Should return validation error
        assert response.status_code == 422

    def test_validate_teacher_inactive_teacher(self, client, db):
        """Test validating inactive teacher"""
        # Create inactive teacher
        inactive_teacher = Teacher(
            email="inactive@duotopia.com",
            password_hash=get_password_hash("test123"),
            name="Inactive Teacher",
            is_active=False,
            is_demo=False,
        )
        db.add(inactive_teacher)
        db.commit()

        request_data = {"email": "inactive@duotopia.com"}

        response = client.post("/api/public/validate-teacher", json=request_data)

        assert response.status_code == 200
        data = response.json()
        # Current implementation still returns valid=True for inactive teachers
        # This might be a design decision to allow inactive teachers to be referenced
        assert data["valid"] is True
        assert data["name"] == "Inactive Teacher"


class TestGetTeacherClassrooms:
    """Test get teacher classrooms endpoint"""

    def test_get_classrooms_success(self, client, public_teacher_with_data):
        """Test successful retrieval of teacher classrooms"""
        email = "public@duotopia.com"

        response = client.get(f"/api/public/teacher-classrooms?email={email}")

        assert response.status_code == 200
        data = response.json()

        # Should return only active classrooms (2 out of 3)
        assert len(data) == 2

        # Check classroom data structure and content
        classroom_names = [c["name"] for c in data]
        assert "Public Class 1" in classroom_names
        assert "Public Class 2" in classroom_names
        assert "Inactive Class" not in classroom_names  # Inactive should be excluded

        # Check student counts
        for classroom_data in data:
            if classroom_data["name"] == "Public Class 1":
                assert classroom_data["studentCount"] == 3
            elif classroom_data["name"] == "Public Class 2":
                assert classroom_data["studentCount"] == 2

            # Check required fields
            assert "id" in classroom_data
            assert "name" in classroom_data
            assert "studentCount" in classroom_data

    def test_get_classrooms_teacher_not_found(self, client):
        """Test with non-existent teacher"""
        email = "nonexistent@duotopia.com"

        response = client.get(f"/api/public/teacher-classrooms?email={email}")

        assert response.status_code == 404
        data = response.json()
        assert "Teacher not found" in data["detail"]

    def test_get_classrooms_case_insensitive(self, client, public_teacher_with_data):
        """Test that email lookup is case insensitive"""
        test_emails = [
            "PUBLIC@DUOTOPIA.COM",
            "Public@Duotopia.Com",
            "public@DUOTOPIA.COM",
        ]

        for email in test_emails:
            response = client.get(f"/api/public/teacher-classrooms?email={email}")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2  # Should find the same classrooms

    def test_get_classrooms_no_classrooms(self, client, public_teacher):
        """Test teacher with no classrooms"""
        email = "public@duotopia.com"

        response = client.get(f"/api/public/teacher-classrooms?email={email}")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_classrooms_missing_email(self, client):
        """Test with missing email parameter"""
        response = client.get("/api/public/teacher-classrooms")

        # Should return validation error
        assert response.status_code == 422

    def test_get_classrooms_empty_email(self, client):
        """Test with empty email parameter"""
        response = client.get("/api/public/teacher-classrooms?email=")

        assert response.status_code == 404  # Empty email won't match any teacher


class TestGetClassroomStudents:
    """Test get classroom students endpoint"""

    def test_get_students_success(self, client, public_teacher_with_data):
        """Test successful retrieval of classroom students"""
        classroom = public_teacher_with_data["classrooms"][0]  # Public Class 1

        response = client.get(f"/api/public/classroom-students/{classroom.id}")

        assert response.status_code == 200
        data = response.json()

        # Should return 3 students
        assert len(data) == 3

        # Check student data structure
        for student_data in data:
            assert "id" in student_data
            assert "name" in student_data
            assert "email" in student_data
            assert "avatar" in student_data

            # Avatar should be None in current implementation
            assert student_data["avatar"] is None

            # Check that we're getting the right students
            assert student_data["name"].startswith("Public Student")
            assert student_data["email"].startswith("pubstudent")
            assert student_data["email"].endswith("@example.com")

    def test_get_students_different_classroom(self, client, public_teacher_with_data):
        """Test getting students from second classroom"""
        classroom = public_teacher_with_data["classrooms"][1]  # Public Class 2

        response = client.get(f"/api/public/classroom-students/{classroom.id}")

        assert response.status_code == 200
        data = response.json()

        # Should return 2 students
        assert len(data) == 2

    def test_get_students_empty_classroom(self, client, public_teacher_with_data):
        """Test classroom with no students"""
        classroom = public_teacher_with_data["classrooms"][2]  # Inactive Class (no students)

        # This classroom is inactive, so it should return 404
        response = client.get(f"/api/public/classroom-students/{classroom.id}")
        assert response.status_code == 404

    def test_get_students_classroom_not_found(self, client):
        """Test with non-existent classroom ID"""
        response = client.get("/api/public/classroom-students/99999")

        assert response.status_code == 404
        data = response.json()
        assert "Classroom not found" in data["detail"]

    def test_get_students_invalid_classroom_id(self, client):
        """Test with invalid classroom ID format"""
        response = client.get("/api/public/classroom-students/invalid")

        # Should return validation error
        assert response.status_code == 422

    def test_get_students_inactive_classroom(self, client, public_teacher_with_data):
        """Test with inactive classroom"""
        inactive_classroom = public_teacher_with_data["classrooms"][2]  # Inactive class

        response = client.get(f"/api/public/classroom-students/{inactive_classroom.id}")

        assert response.status_code == 404
        data = response.json()
        assert "Classroom not found" in data["detail"]


class TestDataIntegrityPublic:
    """Test data integrity and edge cases for public endpoints"""

    def test_student_count_accuracy(self, client, public_teacher_with_data, db):
        """Test that student counts are accurate"""
        email = "public@duotopia.com"

        response = client.get(f"/api/public/teacher-classrooms?email={email}")

        assert response.status_code == 200
        classrooms = response.json()

        # Verify counts by checking actual database
        for classroom_data in classrooms:
            actual_count = (
                db.query(ClassroomStudent).filter(ClassroomStudent.classroom_id == classroom_data["id"]).count()
            )

            assert classroom_data["studentCount"] == actual_count

    def test_only_active_classrooms_returned(self, client, public_teacher_with_data):
        """Test that only active classrooms are returned"""
        email = "public@duotopia.com"

        response = client.get(f"/api/public/teacher-classrooms?email={email}")

        assert response.status_code == 200
        classrooms = response.json()

        # Should only return 2 active classrooms, not the inactive one
        assert len(classrooms) == 2
        classroom_names = [c["name"] for c in classrooms]
        assert "Inactive Class" not in classroom_names

    def test_students_from_correct_classroom(self, client, public_teacher_with_data):
        """Test that students returned belong to the correct classroom"""
        classroom = public_teacher_with_data["classrooms"][0]  # Public Class 1
        expected_student_ids = []

        # Get expected student IDs from our test data
        for student in public_teacher_with_data["students"][:3]:  # First 3 students are in classroom 1
            expected_student_ids.append(student.id)

        response = client.get(f"/api/public/classroom-students/{classroom.id}")

        assert response.status_code == 200
        students = response.json()

        returned_student_ids = [s["id"] for s in students]
        assert set(returned_student_ids) == set(expected_student_ids)

    def test_no_sensitive_data_exposed(self, client, public_teacher_with_data):
        """Test that no sensitive student data is exposed"""
        classroom = public_teacher_with_data["classrooms"][0]

        response = client.get(f"/api/public/classroom-students/{classroom.id}")

        assert response.status_code == 200
        students = response.json()

        for student_data in students:
            # Should NOT contain sensitive fields
            sensitive_fields = [
                "password_hash",
                "birthdate",
                "parent_email",
                "parent_phone",
                "last_login",
                "student_id",
            ]

            for field in sensitive_fields:
                assert field not in student_data

            # Should contain only safe public fields
            expected_fields = {"id", "name", "email", "avatar"}
            actual_fields = set(student_data.keys())
            assert actual_fields == expected_fields


class TestErrorHandlingPublic:
    """Test error handling for public endpoints"""

    def test_malformed_requests(self, client):
        """Test handling of malformed requests"""
        # Invalid JSON for validate-teacher
        response = client.post(
            "/api/public/validate-teacher",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_sql_injection_protection(self, client, public_teacher):
        """Test that endpoints are protected against SQL injection"""
        # Try SQL injection in email parameter
        malicious_emails = [
            "test@test.com'; DROP TABLE teachers; --",
            "test@test.com' OR '1'='1",
            "test@test.com'; SELECT * FROM students; --",
        ]

        for email in malicious_emails:
            # Test validate-teacher endpoint
            response = client.post("/api/public/validate-teacher", json={"email": email})
            # Should either return validation error or valid=False, not crash
            assert response.status_code in [200, 422]

            # Test teacher-classrooms endpoint
            response = client.get(f"/api/public/teacher-classrooms?email={email}")
            # Should either return 404 or validation error, not crash
            assert response.status_code in [404, 422]

    def test_large_classroom_id(self, client):
        """Test with very large classroom ID"""
        large_id = 999999999999999

        response = client.get(f"/api/public/classroom-students/{large_id}")

        assert response.status_code == 404
        data = response.json()
        assert "Classroom not found" in data["detail"]

    def test_concurrent_requests(self, client, public_teacher):
        """Test that endpoints handle concurrent requests correctly"""
        # This is a basic test - real concurrency testing would need threading
        email = "public@duotopia.com"

        # Make multiple requests in sequence (simulating concurrency)
        responses = []
        for _ in range(5):
            response = client.get(f"/api/public/teacher-classrooms?email={email}")
            responses.append(response)

        # All responses should be consistent
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)  # Should always return a list
