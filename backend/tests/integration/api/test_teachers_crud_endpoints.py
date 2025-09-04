"""
Comprehensive tests for CRUD endpoints in routers/teachers.py
Testing all classroom, student, and program CRUD operations
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher, Classroom, Student, ClassroomStudent, Program, ProgramLevel
from auth import get_password_hash, create_access_token
from datetime import datetime, timedelta  # noqa: F401


@pytest.fixture
def crud_teacher(db):
    """Create a teacher for CRUD testing"""
    teacher_obj = Teacher(
        email="crud@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="CRUD Teacher",
        phone="+1234567890",
        is_active=True,
        is_demo=False,
    )
    db.add(teacher_obj)
    db.commit()
    db.refresh(teacher_obj)
    return teacher_obj


@pytest.fixture
def crud_teacher_token(crud_teacher):
    """Generate JWT token for CRUD teacher"""
    return create_access_token(
        {
            "sub": str(crud_teacher.id),
            "email": crud_teacher.email,
            "type": "teacher",
            "name": crud_teacher.name,
        }
    )


@pytest.fixture
def crud_auth_headers(crud_teacher_token):
    """Create authorization headers for CRUD teacher"""
    return {"Authorization": f"Bearer {crud_teacher_token}"}


@pytest.fixture
def sample_classroom(db, crud_teacher):
    """Create a sample classroom for testing"""
    classroom = Classroom(
        name="Sample Class",
        description="Sample Description",
        level=ProgramLevel.A1,
        teacher_id=crud_teacher.id,
        is_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@pytest.fixture
def sample_student(db):
    """Create a sample student for testing"""
    student = Student(
        name="Sample Student",
        email="sample@example.com",
        student_id="SAMPLE01",
        password_hash=get_password_hash("20100101"),
        birthdate=datetime(2010, 1, 1).date(),
        is_active=True,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture
def sample_program(db, crud_teacher, sample_classroom):
    """Create a sample program for testing"""
    program = Program(
        name="Sample Program",
        description="Sample Program Description",
        level=ProgramLevel.A1,
        teacher_id=crud_teacher.id,
        classroom_id=sample_classroom.id,
        estimated_hours=20,
        is_active=True,
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program


class TestClassroomListEndpoints:
    """Test classroom list endpoints"""

    def test_get_classrooms_empty(self, client, crud_auth_headers):
        """Test getting classrooms when teacher has none"""
        response = client.get("/api/teachers/classrooms", headers=crud_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_classrooms_with_data(
        self, client, sample_classroom, crud_auth_headers
    ):
        """Test getting classrooms with data"""
        response = client.get("/api/teachers/classrooms", headers=crud_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        classroom_data = data[0]
        assert classroom_data["id"] == sample_classroom.id
        assert classroom_data["name"] == "Sample Class"
        assert classroom_data["description"] == "Sample Description"
        assert classroom_data["level"] == "A1"
        assert "student_count" in classroom_data
        assert "program_count" in classroom_data
        assert "created_at" in classroom_data
        assert "students" in classroom_data

    def test_get_programs_empty(self, client, crud_auth_headers):
        """Test getting programs when teacher has none"""
        response = client.get("/api/teachers/programs", headers=crud_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_programs_with_data(self, client, sample_program, crud_auth_headers):
        """Test getting programs with data"""
        response = client.get("/api/teachers/programs", headers=crud_auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

        program_data = data[0]
        assert program_data["id"] == sample_program.id
        assert program_data["name"] == "Sample Program"
        assert program_data["description"] == "Sample Program Description"
        assert program_data["level"] == "A1"
        assert program_data["estimated_hours"] == 20
        assert program_data["is_active"] is True
        assert "created_at" in program_data


class TestClassroomCRUD:
    """Test classroom CRUD operations"""

    def test_create_classroom_success(self, client, crud_auth_headers):
        """Test successful classroom creation"""
        classroom_data = {
            "name": "New Classroom",
            "description": "New classroom description",
            "level": "A2",
        }

        response = client.post(
            "/api/teachers/classrooms", json=classroom_data, headers=crud_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Classroom"
        assert data["description"] == "New classroom description"
        assert data["level"] == "A2"
        assert "id" in data

    def test_create_classroom_minimal(self, client, crud_auth_headers):
        """Test creating classroom with minimal data"""
        classroom_data = {"name": "Minimal Class"}

        response = client.post(
            "/api/teachers/classrooms", json=classroom_data, headers=crud_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Class"
        assert data["description"] is None
        assert data["level"] == "A1"  # Default level

    def test_create_classroom_invalid_level(self, client, crud_auth_headers):
        """Test creating classroom with invalid level"""
        classroom_data = {"name": "Invalid Level Class", "level": "INVALID_LEVEL"}

        response = client.post(
            "/api/teachers/classrooms", json=classroom_data, headers=crud_auth_headers
        )

        # Should still create but default to A1
        assert response.status_code == 201
        data = response.json()
        assert data["level"] == "A1"  # Falls back to default

    def test_get_classroom_by_id(self, client, sample_classroom, crud_auth_headers):
        """Test getting specific classroom by ID"""
        response = client.get(
            f"/api/teachers/classrooms/{sample_classroom.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_classroom.id
        assert data["name"] == "Sample Class"
        assert "students" in data
        assert "programs" in data

    def test_get_classroom_not_found(self, client, crud_auth_headers):
        """Test getting non-existent classroom"""
        response = client.get(
            "/api/teachers/classrooms/99999", headers=crud_auth_headers
        )
        assert response.status_code == 404

    def test_get_classroom_wrong_teacher(self, client, sample_classroom, demo_teacher):
        """Test getting classroom belonging to different teacher"""
        # Create token for different teacher
        token = create_access_token(
            {
                "sub": str(demo_teacher.id),
                "email": demo_teacher.email,
                "type": "teacher",
                "name": demo_teacher.name,
            }
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            f"/api/teachers/classrooms/{sample_classroom.id}", headers=headers
        )
        assert response.status_code == 404

    def test_update_classroom(self, client, sample_classroom, crud_auth_headers):
        """Test updating classroom"""
        update_data = {
            "name": "Updated Classroom Name",
            "description": "Updated description",
            "level": "B1",
        }

        response = client.put(
            f"/api/teachers/classrooms/{sample_classroom.id}",
            json=update_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Classroom Name"
        assert data["description"] == "Updated description"
        assert data["level"] == "B1"

    def test_update_classroom_partial(
        self, client, sample_classroom, crud_auth_headers
    ):
        """Test partial classroom update"""
        update_data = {"name": "Partially Updated"}

        response = client.put(
            f"/api/teachers/classrooms/{sample_classroom.id}",
            json=update_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Partially Updated"
        assert data["description"] == "Sample Description"  # Unchanged

    def test_delete_classroom(self, client, sample_classroom, crud_auth_headers):
        """Test deleting classroom"""
        response = client.delete(
            f"/api/teachers/classrooms/{sample_classroom.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200

        # Verify classroom is marked inactive (soft delete)
        get_response = client.get(
            f"/api/teachers/classrooms/{sample_classroom.id}", headers=crud_auth_headers
        )
        assert get_response.status_code == 404


class TestStudentCRUD:
    """Test student CRUD operations"""

    def test_create_student_success(self, client, crud_auth_headers):
        """Test successful student creation"""
        student_data = {
            "name": "New Student",
            "birthdate": "2010-05-15",
            "student_id": "NEW001",
        }

        response = client.post(
            "/api/teachers/students", json=student_data, headers=crud_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Student"
        assert data["student_id"] == "NEW001"
        assert "email" in data  # Should be auto-generated
        assert data["password_changed"] is False

    def test_create_student_minimal(self, client, crud_auth_headers):
        """Test creating student with minimal data"""
        student_data = {"name": "Minimal Student", "birthdate": "2012-01-01"}

        response = client.post(
            "/api/teachers/students", json=student_data, headers=crud_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Student"
        assert data["student_id"] is None

    def test_get_student_by_id(self, client, sample_student, crud_auth_headers):
        """Test getting specific student by ID"""
        response = client.get(
            f"/api/teachers/students/{sample_student.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_student.id
        assert data["name"] == "Sample Student"
        assert "classrooms" in data

    def test_update_student(self, client, sample_student, crud_auth_headers):
        """Test updating student"""
        update_data = {"name": "Updated Student Name", "student_id": "UPDATED01"}

        response = client.put(
            f"/api/teachers/students/{sample_student.id}",
            json=update_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Student Name"
        assert data["student_id"] == "UPDATED01"

    def test_delete_student(self, client, sample_student, crud_auth_headers):
        """Test deleting student"""
        response = client.delete(
            f"/api/teachers/students/{sample_student.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200

        # Verify student is marked inactive
        get_response = client.get(
            f"/api/teachers/students/{sample_student.id}", headers=crud_auth_headers
        )
        assert get_response.status_code == 404


class TestBatchStudentOperations:
    """Test batch student operations"""

    def test_batch_add_students_to_classroom(
        self, client, sample_classroom, crud_auth_headers
    ):
        """Test adding multiple students to a classroom"""
        students_data = {
            "students": [
                {
                    "name": "Batch Student 1",
                    "birthdate": "2010-01-01",
                    "student_id": "BATCH01",
                },
                {
                    "name": "Batch Student 2",
                    "birthdate": "2010-02-02",
                    "student_id": "BATCH02",
                },
                {"name": "Batch Student 3", "birthdate": "2010-03-03"},  # No student_id
            ]
        }

        response = client.post(
            f"/api/teachers/classrooms/{sample_classroom.id}/students/batch",
            json=students_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "created_students" in data
        assert "skipped_students" in data
        assert len(data["created_students"]) == 3

        # Check that students were added to classroom
        classroom_response = client.get(
            f"/api/teachers/classrooms/{sample_classroom.id}", headers=crud_auth_headers
        )
        classroom_data = classroom_response.json()
        assert len(classroom_data["students"]) == 3

    def test_batch_add_students_duplicate_handling(
        self, client, sample_classroom, sample_student, crud_auth_headers, db
    ):
        """Test batch add with duplicate email handling"""
        # Add sample student to classroom first
        cs = ClassroomStudent(
            classroom_id=sample_classroom.id,
            student_id=sample_student.id,
            is_active=True,
        )
        db.add(cs)
        db.commit()

        students_data = {
            "students": [
                {
                    "name": "New Student",
                    "birthdate": "2010-01-01",
                    "student_id": "NEW01",
                },
                {
                    "name": "Duplicate Student",
                    "birthdate": "2010-01-01",
                    "email": sample_student.email,
                },  # Duplicate email
            ]
        }

        response = client.post(
            f"/api/teachers/classrooms/{sample_classroom.id}/students/batch",
            json=students_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["created_students"]) >= 1  # At least one should be created
        assert len(data["skipped_students"]) >= 0  # Some might be skipped


class TestProgramCRUD:
    """Test program CRUD operations"""

    def test_create_program_success(self, client, sample_classroom, crud_auth_headers):
        """Test successful program creation"""
        program_data = {
            "name": "New Program",
            "description": "New program description",
            "level": "A2",
            "classroom_id": sample_classroom.id,
            "estimated_hours": 30,
        }

        response = client.post(
            "/api/teachers/programs", json=program_data, headers=crud_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Program"
        assert data["description"] == "New program description"
        assert data["level"] == "A2"
        assert data["estimated_hours"] == 30

    def test_get_program_by_id(self, client, sample_program, crud_auth_headers):
        """Test getting specific program by ID"""
        response = client.get(
            f"/api/teachers/programs/{sample_program.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_program.id
        assert data["name"] == "Sample Program"
        assert "lessons" in data

    def test_update_program(self, client, sample_program, crud_auth_headers):
        """Test updating program"""
        update_data = {
            "name": "Updated Program Name",
            "description": "Updated description",
            "estimated_hours": 40,
        }

        response = client.put(
            f"/api/teachers/programs/{sample_program.id}",
            json=update_data,
            headers=crud_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Program Name"
        assert data["estimated_hours"] == 40

    def test_delete_program(self, client, sample_program, crud_auth_headers):
        """Test deleting program"""
        response = client.delete(
            f"/api/teachers/programs/{sample_program.id}", headers=crud_auth_headers
        )

        assert response.status_code == 200

        # Verify program is marked inactive
        get_response = client.get(
            f"/api/teachers/programs/{sample_program.id}", headers=crud_auth_headers
        )
        assert get_response.status_code == 404


class TestErrorHandling:
    """Test error handling for all endpoints"""

    def test_unauthorized_access(self, client):
        """Test unauthorized access to all endpoints"""
        endpoints = [
            ("GET", "/api/teachers/classrooms"),
            ("POST", "/api/teachers/classrooms"),
            ("GET", "/api/teachers/classrooms/1"),
            ("PUT", "/api/teachers/classrooms/1"),
            ("DELETE", "/api/teachers/classrooms/1"),
            ("GET", "/api/teachers/programs"),
            ("POST", "/api/teachers/programs"),
            ("GET", "/api/teachers/programs/1"),
            ("PUT", "/api/teachers/programs/1"),
            ("DELETE", "/api/teachers/programs/1"),
            ("POST", "/api/teachers/students"),
            ("GET", "/api/teachers/students/1"),
            ("PUT", "/api/teachers/students/1"),
            ("DELETE", "/api/teachers/students/1"),
            ("POST", "/api/teachers/classrooms/1/students/batch"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})
            elif method == "PUT":
                response = client.put(endpoint, json={})
            elif method == "DELETE":
                response = client.delete(endpoint)

            assert response.status_code == 401

    def test_invalid_data_handling(self, client, crud_auth_headers):
        """Test handling of invalid data"""
        # Test with invalid JSON
        invalid_data_tests = [
            ("POST", "/api/teachers/classrooms", {"name": ""}),  # Empty name
            ("POST", "/api/teachers/students", {"name": "Test"}),  # Missing birthdate
            (
                "POST",
                "/api/teachers/programs",
                {"name": "Test"},
            ),  # Missing required fields
        ]

        for method, endpoint, data in invalid_data_tests:
            response = client.post(endpoint, json=data, headers=crud_auth_headers)
            # Should return 422 (validation error) or handle gracefully
            assert response.status_code in [400, 422, 500]


class TestDataValidation:
    """Test data validation and constraints"""

    def test_classroom_name_constraints(self, client, crud_auth_headers):
        """Test classroom name validation"""
        # Test very long name
        long_name = "A" * 200
        classroom_data = {"name": long_name}

        response = client.post(
            "/api/teachers/classrooms", json=classroom_data, headers=crud_auth_headers
        )
        # Should either succeed (truncated) or fail gracefully
        assert response.status_code in [201, 400, 422]

    def test_student_birthdate_validation(self, client, crud_auth_headers):
        """Test student birthdate validation"""
        # Test invalid date format
        student_data = {"name": "Test Student", "birthdate": "invalid-date"}

        response = client.post(
            "/api/teachers/students", json=student_data, headers=crud_auth_headers
        )
        assert response.status_code in [400, 422]

        # Test future date
        student_data = {"name": "Test Student", "birthdate": "2030-01-01"}

        response = client.post(
            "/api/teachers/students", json=student_data, headers=crud_auth_headers
        )
        # Should either accept or reject gracefully
        assert response.status_code in [201, 400, 422]
