"""Tests for Teacher endpoint permissions - preventing operations on school classrooms/students

TDD Approach:
1. RED: Write failing tests
2. GREEN: Implement permission checks
3. REFACTOR: Clean up code
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import date

from main import app
from models import (
    Teacher,
    School,
    Organization,
    TeacherSchool,
    Classroom,
    ClassroomSchool,
    Student,
    ClassroomStudent,
)
from models.base import ProgramLevel
from database import get_db
from auth import create_access_token, get_password_hash


@pytest.fixture
def test_db(tmp_path):
    """Create test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base

    db_path = tmp_path / "test_teacher_permissions.db"
    engine = create_engine(
        f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(test_db):
    """Create test client with database override"""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def teacher(test_db: Session):
    """Create a test teacher"""
    teacher = Teacher(
        email="teacher@test.com",
        password_hash=get_password_hash("password123"),
        name="Test Teacher",
        is_active=True,
        email_verified=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def auth_token(teacher: Teacher):
    """Create auth token for teacher"""
    return create_access_token(
        data={"sub": str(teacher.id), "email": teacher.email, "type": "teacher"}
    )


@pytest.fixture
def organization(test_db: Session):
    """Create test organization"""
    org = Organization(
        id=uuid.uuid4(),
        name="Test Organization",
        is_active=True,
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)
    return org


@pytest.fixture
def school(test_db: Session, organization: Organization):
    """Create test school"""
    school = School(
        id=uuid.uuid4(),
        organization_id=organization.id,
        name="Test School",
        is_active=True,
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


@pytest.fixture
def personal_classroom(test_db: Session, teacher: Teacher):
    """Create a personal classroom (not belonging to school)"""
    classroom = Classroom(
        name="Personal Classroom",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_db.add(classroom)
    test_db.commit()
    test_db.refresh(classroom)
    return classroom


@pytest.fixture
def school_classroom(test_db: Session, teacher: Teacher, school: School):
    """Create a school classroom (belonging to school)"""
    classroom = Classroom(
        name="School Classroom",
        teacher_id=teacher.id,  # Teacher is assigned but classroom belongs to school
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_db.add(classroom)
    test_db.flush()

    # Create ClassroomSchool relationship
    classroom_school = ClassroomSchool(
        classroom_id=classroom.id,
        school_id=school.id,
        is_active=True,
    )
    test_db.add(classroom_school)
    test_db.commit()
    test_db.refresh(classroom)
    return classroom


class TestTeacherCreateStudentPermissions:
    """Test permission checks when creating students"""

    def test_create_student_in_personal_classroom_should_succeed(
        self, client: TestClient, auth_token: str, personal_classroom: Classroom
    ):
        """Teacher should be able to create student in personal classroom"""
        response = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Student",
                "birthdate": "2010-01-01",
                "classroom_id": personal_classroom.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Student"

    def test_create_student_in_school_classroom_should_fail(
        self, client: TestClient, auth_token: str, school_classroom: Classroom
    ):
        """Teacher should NOT be able to create student in school classroom"""
        response = client.post(
            "/api/teachers/students",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Test Student",
                "birthdate": "2010-01-01",
                "classroom_id": school_classroom.id,
            },
        )
        assert response.status_code == 403
        assert (
            "學校" in response.json()["detail"]
            or "school" in response.json()["detail"].lower()
        )


class TestTeacherUpdateClassroomPermissions:
    """Test permission checks when updating classrooms"""

    def test_update_personal_classroom_should_succeed(
        self, client: TestClient, auth_token: str, personal_classroom: Classroom
    ):
        """Teacher should be able to update personal classroom"""
        response = client.put(
            f"/api/teachers/classrooms/{personal_classroom.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Personal Classroom",
                "level": "A2",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Personal Classroom"

    def test_update_school_classroom_should_fail(
        self, client: TestClient, auth_token: str, school_classroom: Classroom
    ):
        """Teacher should NOT be able to update school classroom"""
        response = client.put(
            f"/api/teachers/classrooms/{school_classroom.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated School Classroom",
            },
        )
        assert response.status_code == 403
        assert (
            "學校" in response.json()["detail"]
            or "school" in response.json()["detail"].lower()
        )


class TestTeacherDeleteClassroomPermissions:
    """Test permission checks when deleting classrooms"""

    def test_delete_personal_classroom_should_succeed(
        self, client: TestClient, auth_token: str, personal_classroom: Classroom
    ):
        """Teacher should be able to delete personal classroom"""
        response = client.delete(
            f"/api/teachers/classrooms/{personal_classroom.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 200

    def test_delete_school_classroom_should_fail(
        self, client: TestClient, auth_token: str, school_classroom: Classroom
    ):
        """Teacher should NOT be able to delete school classroom"""
        response = client.delete(
            f"/api/teachers/classrooms/{school_classroom.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert response.status_code == 403
        assert (
            "學校" in response.json()["detail"]
            or "school" in response.json()["detail"].lower()
        )


class TestTeacherUpdateStudentPermissions:
    """Test permission checks when updating students"""

    @pytest.fixture
    def personal_student(
        self, test_db: Session, teacher: Teacher, personal_classroom: Classroom
    ):
        """Create a student in personal classroom"""
        student = Student(
            name="Personal Student",
            birthdate=date(2010, 1, 1),
            password_hash=get_password_hash("12345678"),
            is_active=True,
        )
        test_db.add(student)
        test_db.flush()

        enrollment = ClassroomStudent(
            classroom_id=personal_classroom.id,
            student_id=student.id,
            is_active=True,
        )
        test_db.add(enrollment)
        test_db.commit()
        test_db.refresh(student)
        return student

    def test_update_student_in_personal_classroom_should_succeed(
        self, client: TestClient, auth_token: str, personal_student: Student
    ):
        """Teacher should be able to update student in personal classroom"""
        response = client.put(
            f"/api/teachers/students/{personal_student.id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Updated Personal Student",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Personal Student"
