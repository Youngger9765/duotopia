"""
Integration tests for student authentication with organization hierarchy.

Tests student login endpoint returns correct organization and school information.
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from models import Student, Teacher, Classroom, ClassroomStudent
from models.organization import (
    Organization,
    School,
    ClassroomSchool,
    TeacherOrganization,
)
from auth import get_password_hash as hash_password


@pytest.fixture
def test_teacher(db_session: Session):
    """Create a test teacher."""
    teacher = Teacher(
        email="teacher@test.com",
        password_hash=hash_password("password123"),
        name="Test Teacher",
        phone="0912345678",
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_organization(db_session: Session):
    """Create a test organization."""
    org = Organization(
        name="ABC補習班",
        display_name="ABC Cram School",
        description="Test organization",
        contact_email="org@abc.com",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def test_school(db_session: Session, test_organization: Organization):
    """Create a test school under organization."""
    school = School(
        organization_id=test_organization.id,
        name="台北校區",
        display_name="Taipei Campus",
        description="Test school",
        contact_email="taipei@abc.com",
        is_active=True,
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture
def test_classroom_with_org(
    db_session: Session, test_teacher: Teacher, test_school: School
):
    """Create a classroom linked to school/organization."""
    classroom = Classroom(
        name="國小英文班",
        description="Elementary English Class",
        teacher_id=test_teacher.id,
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)

    # Link classroom to school
    classroom_school = ClassroomSchool(
        classroom_id=classroom.id, school_id=test_school.id, is_active=True
    )
    db_session.add(classroom_school)
    db_session.commit()

    return classroom


@pytest.fixture
def test_classroom_without_org(db_session: Session, test_teacher: Teacher):
    """Create a classroom without organization (independent teacher)."""
    classroom = Classroom(
        name="王老師的班級",
        description="Independent teacher classroom",
        teacher_id=test_teacher.id,
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom


@pytest.fixture
def test_student_with_org(db_session: Session, test_classroom_with_org: Classroom):
    """Create a student in a classroom with organization."""
    student = Student(
        name="張小明",
        email="student_org@test.com",
        student_number="S001",
        birthdate=datetime(2010, 5, 15).date(),
        password_hash=hash_password("20100515"),  # Birthdate as password
        parent_phone="0987654321",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    # Enroll student in classroom
    enrollment = ClassroomStudent(
        classroom_id=test_classroom_with_org.id,
        student_id=student.id,
        is_active=True,
    )
    db_session.add(enrollment)
    db_session.commit()

    return student


@pytest.fixture
def test_student_without_org(
    db_session: Session, test_classroom_without_org: Classroom
):
    """Create a student in a classroom without organization."""
    student = Student(
        name="李小華",
        email="student_no_org@test.com",
        student_number="S002",
        birthdate=datetime(2011, 8, 20).date(),
        password_hash=hash_password("20110820"),
        parent_phone="0912345679",
    )
    db_session.add(student)
    db_session.commit()
    db_session.refresh(student)

    # Enroll student in classroom
    enrollment = ClassroomStudent(
        classroom_id=test_classroom_without_org.id,
        student_id=student.id,
        is_active=True,
    )
    db_session.add(enrollment)
    db_session.commit()

    return student


def test_student_login_with_organization(test_client, test_student_with_org: Student):
    """Test student login returns organization and school information."""
    response = test_client.post(
        "/api/students/validate",
        json={"email": "student_org@test.com", "password": "20100515"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify token
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify student data
    student = data["student"]
    assert student["id"] == test_student_with_org.id
    assert student["name"] == "張小明"
    assert student["email"] == "student_org@test.com"
    assert student["student_number"] == "S001"

    # Verify classroom
    assert student["classroom_id"] is not None
    assert student["classroom_name"] == "國小英文班"

    # Verify school information
    assert student["school_id"] is not None
    assert student["school_name"] == "台北校區"

    # Verify organization information
    assert student["organization_id"] is not None
    assert student["organization_name"] == "ABC補習班"


def test_student_login_without_organization(
    test_client, test_student_without_org: Student
):
    """Test student login without organization returns null for org/school fields."""
    response = test_client.post(
        "/api/students/validate",
        json={"email": "student_no_org@test.com", "password": "20110820"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify token
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Verify student data
    student = data["student"]
    assert student["id"] == test_student_without_org.id
    assert student["name"] == "李小華"
    assert student["email"] == "student_no_org@test.com"
    assert student["student_number"] == "S002"

    # Verify classroom
    assert student["classroom_id"] is not None
    assert student["classroom_name"] == "王老師的班級"

    # Verify school and organization are None
    assert student["school_id"] is None
    assert student["school_name"] is None
    assert student["organization_id"] is None
    assert student["organization_name"] is None


def test_student_login_invalid_password(test_client, test_student_with_org: Student):
    """Test student login with invalid password."""
    response = test_client.post(
        "/api/students/validate",
        json={"email": "student_org@test.com", "password": "wrong_password"},
    )

    assert response.status_code == 400
    assert "Invalid password" in response.json()["detail"]


def test_student_login_nonexistent_email(test_client):
    """Test student login with non-existent email."""
    response = test_client.post(
        "/api/students/validate",
        json={"email": "nonexistent@test.com", "password": "password123"},
    )

    assert response.status_code == 404
    assert "Student not found" in response.json()["detail"]


def test_student_login_inactive_classroom_school(
    db_session: Session,
    test_client,
    test_student_with_org: Student,
    test_classroom_with_org: Classroom,
):
    """Test student login when ClassroomSchool is inactive."""
    # Mark ClassroomSchool as inactive
    classroom_school = (
        db_session.query(ClassroomSchool)
        .filter(ClassroomSchool.classroom_id == test_classroom_with_org.id)
        .first()
    )
    classroom_school.is_active = False
    db_session.commit()

    response = test_client.post(
        "/api/students/validate",
        json={"email": "student_org@test.com", "password": "20100515"},
    )

    assert response.status_code == 200
    data = response.json()
    student = data["student"]

    # Should still have classroom, but no school/org
    assert student["classroom_id"] is not None
    assert student["classroom_name"] == "國小英文班"
    assert student["school_id"] is None
    assert student["school_name"] is None
    assert student["organization_id"] is None
    assert student["organization_name"] is None
