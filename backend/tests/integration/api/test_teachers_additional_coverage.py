"""
Additional tests to improve teachers.py coverage from 55% to 90%+
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from models import Teacher, Classroom, Student, ClassroomStudent, Program
from auth import create_access_token
import json

client = TestClient(app)


@pytest.fixture
def teacher_with_data(db: Session):
    """Create a teacher with classroom, students and programs for testing"""
    # Create teacher
    teacher = Teacher(
        email="coverage@duotopia.com",
        hashed_password="hashedpassword",
        name="Coverage Teacher",
        is_active=True,
        is_demo=False,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    # Create classroom
    classroom = Classroom(
        name="Coverage Class",
        description="Test classroom",
        level="A1",
        teacher_id=teacher.id,
        is_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    # Create students
    for i in range(3):
        student = Student(
            email=f"student{i}@test.com",
            name=f"Student {i}",
            hashed_password="hashedpass",
            birthdate="2000-01-01",
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # Add to classroom
        cs = ClassroomStudent(
            classroom_id=classroom.id, student_id=student.id, is_active=True
        )
        db.add(cs)

    # Create program
    program = Program(
        name="Test Program",
        description="Test program description",
        level="A1",
        classroom_id=classroom.id,
        teacher_id=teacher.id,
        is_active=True,
        estimated_hours=20,
    )
    db.add(program)
    db.commit()

    return teacher


@pytest.fixture
def coverage_teacher_token(teacher_with_data):
    """Create token for coverage teacher"""
    return create_access_token(
        {
            "sub": str(teacher_with_data.id),
            "type": "teacher",
            "email": teacher_with_data.email,
        }
    )


class TestTeacherClassroomCRUD:
    """Test classroom CRUD operations to improve coverage"""

    def test_create_classroom_success(self, coverage_teacher_token: str):
        """Test successful classroom creation"""
        response = client.post(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "New Test Classroom",
                "description": "A test classroom",
                "level": "A2",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Test Classroom"
        assert data["description"] == "A test classroom"
        assert data["level"] == "A2"

    def test_create_classroom_minimal_data(self, coverage_teacher_token: str):
        """Test classroom creation with minimal required data"""
        response = client.post(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={"name": "Minimal Classroom", "level": "B1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Classroom"
        assert data["level"] == "B1"

    def test_update_classroom_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful classroom update"""
        # Get existing classroom
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        response = client.put(
            f"/api/teachers/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "Updated Classroom Name",
                "description": "Updated description",
                "level": "B2",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Classroom Name"
        assert data["description"] == "Updated description"
        assert data["level"] == "B2"

    def test_delete_classroom_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful classroom deletion"""
        # Create a classroom to delete
        classroom = Classroom(
            name="To Be Deleted",
            description="Will be deleted",
            level="A1",
            teacher_id=teacher_with_data.id,
            is_active=True,
        )
        db.add(classroom)
        db.commit()
        db.refresh(classroom)

        response = client.delete(
            f"/api/teachers/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200

        # Verify soft delete
        db.refresh(classroom)
        assert classroom.is_active is False

    def test_get_classroom_detail(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test getting classroom detail"""
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        response = client.get(
            f"/api/teachers/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == classroom.id
        assert data["name"] == classroom.name


class TestTeacherStudentCRUD:
    """Test student CRUD operations to improve coverage"""

    def test_create_student_success(self, coverage_teacher_token: str):
        """Test successful student creation"""
        response = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "email": "newstudent@test.com",
                "name": "New Student",
                "birthdate": "2000-05-15",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newstudent@test.com"
        assert data["name"] == "New Student"

    def test_batch_add_students(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test batch adding students to classroom"""
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        response = client.post(
            f"/api/teachers/classrooms/{classroom.id}/students/batch",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "students": [
                    {
                        "email": "batch1@test.com",
                        "name": "Batch Student 1",
                        "birthdate": "2000-01-01",
                    },
                    {
                        "email": "batch2@test.com",
                        "name": "Batch Student 2",
                        "birthdate": "2000-02-02",
                    },
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["added_students"]) == 2

    def test_update_student_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful student update"""
        # Get a student from the classroom
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        student_relation = (
            db.query(ClassroomStudent)
            .filter(ClassroomStudent.classroom_id == classroom.id)
            .first()
        )
        student = student_relation.student

        response = client.put(
            f"/api/teachers/students/{student.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "Updated Student Name",
                "email": student.email,
                "birthdate": "2001-01-01",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Student Name"


class TestTeacherProgramCRUD:
    """Test program CRUD operations to improve coverage"""

    def test_create_program_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful program creation"""
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        response = client.post(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "New Program",
                "description": "A new program",
                "level": "B1",
                "classroom_id": classroom.id,
                "estimated_hours": 30,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Program"
        assert data["estimated_hours"] == 30

    def test_update_program_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful program update"""
        program = (
            db.query(Program).filter(Program.teacher_id == teacher_with_data.id).first()
        )

        response = client.put(
            f"/api/teachers/programs/{program.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "Updated Program",
                "description": "Updated description",
                "level": "B2",
                "estimated_hours": 40,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Program"
        assert data["estimated_hours"] == 40

    def test_delete_program_success(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test successful program deletion"""
        # Create a program to delete
        classroom = (
            db.query(Classroom)
            .filter(Classroom.teacher_id == teacher_with_data.id)
            .first()
        )

        program = Program(
            name="To Be Deleted Program",
            description="Will be deleted",
            level="A1",
            classroom_id=classroom.id,
            teacher_id=teacher_with_data.id,
            is_active=True,
        )
        db.add(program)
        db.commit()
        db.refresh(program)

        response = client.delete(
            f"/api/teachers/programs/{program.id}",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200

        # Verify soft delete
        db.refresh(program)
        assert program.is_active is False


class TestAuthorizationAndErrors:
    """Test authorization and error handling to improve coverage"""

    def test_unauthorized_access(self):
        """Test accessing teacher endpoints without token"""
        response = client.get("/api/teachers/me")
        assert response.status_code == 401

    def test_invalid_token_format(self):
        """Test accessing with malformed token"""
        response = client.get(
            "/api/teachers/me", headers={"Authorization": "InvalidToken"}
        )
        assert response.status_code == 401

    def test_expired_token(self):
        """Test accessing with expired token"""
        from datetime import datetime, timedelta

        expired_token = create_access_token(
            {"sub": "1", "type": "teacher"},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        response = client.get(
            "/api/teachers/me", headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401

    def test_classroom_not_found(self, coverage_teacher_token: str):
        """Test accessing non-existent classroom"""
        response = client.get(
            "/api/teachers/classrooms/99999",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 404

    def test_student_not_found(self, coverage_teacher_token: str):
        """Test accessing non-existent student"""
        response = client.get(
            "/api/teachers/students/99999",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 404

    def test_program_not_found(self, coverage_teacher_token: str):
        """Test accessing non-existent program"""
        response = client.get(
            "/api/teachers/programs/99999",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 404


class TestInputValidation:
    """Test input validation to improve coverage"""

    def test_invalid_classroom_data(self, coverage_teacher_token: str):
        """Test creating classroom with invalid data"""
        response = client.post(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "name": "",  # Empty name should fail
                "level": "InvalidLevel",  # Invalid level
            },
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_invalid_student_data(self, coverage_teacher_token: str):
        """Test creating student with invalid data"""
        response = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "email": "not-an-email",  # Invalid email
                "name": "",  # Empty name
                "birthdate": "not-a-date",  # Invalid date
            },
        )
        assert response.status_code in [400, 422]  # Validation error

    def test_duplicate_email_student(
        self, db: Session, teacher_with_data: Teacher, coverage_teacher_token: str
    ):
        """Test creating student with duplicate email"""
        # Create first student
        response1 = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "email": "duplicate@test.com",
                "name": "First Student",
                "birthdate": "2000-01-01",
            },
        )
        assert response1.status_code == 200

        # Try to create second student with same email
        response2 = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
            json={
                "email": "duplicate@test.com",  # Same email
                "name": "Second Student",
                "birthdate": "2000-01-01",
            },
        )
        # Should fail with conflict or validation error
        assert response2.status_code in [400, 409, 422]


class TestPagination:
    """Test pagination and query parameters to improve coverage"""

    def test_get_classrooms_with_pagination(self, coverage_teacher_token: str):
        """Test getting classrooms with pagination parameters"""
        response = client.get(
            "/api/teachers/classrooms?page=1&size=10",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200

    def test_get_students_with_filters(self, coverage_teacher_token: str):
        """Test getting students with filter parameters"""
        response = client.get(
            "/api/teachers/students?search=test&classroom_id=1",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200

    def test_get_programs_with_sorting(self, coverage_teacher_token: str):
        """Test getting programs with sort parameters"""
        response = client.get(
            "/api/teachers/programs?sort_by=name&sort_order=desc",
            headers={"Authorization": f"Bearer {coverage_teacher_token}"},
        )
        assert response.status_code == 200
