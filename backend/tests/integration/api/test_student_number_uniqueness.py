"""
Test student_number uniqueness validation within the same classroom (Issue #31)

Tests:
1. Create student with duplicate student_number in same classroom -> 409 error
2. Create student with same student_number in different classroom -> OK
3. Update student with duplicate student_number in same classroom -> 409 error
4. Move student to classroom where student_number already exists -> 409 error
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import timedelta

from models import Teacher, Classroom, Student, ClassroomStudent
from auth import get_password_hash, create_access_token


@pytest.fixture
def teacher(test_db_session: Session):
    """Create a test teacher"""
    teacher = Teacher(
        email="teacher@test.com",
        password_hash=get_password_hash("password123"),
        name="Test Teacher",
        is_active=True,
    )
    test_db_session.add(teacher)
    test_db_session.commit()
    test_db_session.refresh(teacher)
    return teacher


@pytest.fixture
def classroom_a(test_db_session: Session, teacher: Teacher):
    """Create classroom A"""
    classroom = Classroom(
        name="Classroom A",
        teacher_id=teacher.id,
        is_active=True,
    )
    test_db_session.add(classroom)
    test_db_session.commit()
    test_db_session.refresh(classroom)
    return classroom


@pytest.fixture
def classroom_b(test_db_session: Session, teacher: Teacher):
    """Create classroom B"""
    classroom = Classroom(
        name="Classroom B",
        teacher_id=teacher.id,
        is_active=True,
    )
    test_db_session.add(classroom)
    test_db_session.commit()
    test_db_session.refresh(classroom)
    return classroom


@pytest.fixture
def auth_headers(teacher: Teacher):
    """Get authentication headers for teacher"""
    token = create_access_token(
        data={"sub": str(teacher.id), "type": "teacher"},
        expires_delta=timedelta(minutes=30),
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_student_with_duplicate_student_number_same_classroom(
    test_db_session: Session,
    classroom_a: Classroom,
    auth_headers: dict,
    test_client: TestClient,
):
    """Test creating student with duplicate student_number in same classroom should fail"""

    # Create first student with student_number "S001"
    student_data_1 = {
        "name": "Student One",
        "birthdate": "2010-01-01",
        "student_number": "S001",
        "classroom_id": classroom_a.id,
    }

    response = test_client.post(
        "/api/teachers/students", json=student_data_1, headers=auth_headers
    )
    assert response.status_code == 200
    student1_id = response.json()["id"]

    # Try to create second student with same student_number in same classroom
    student_data_2 = {
        "name": "Student Two",
        "birthdate": "2010-01-02",
        "student_number": "S001",  # Same student_number
        "classroom_id": classroom_a.id,  # Same classroom
    }

    response = test_client.post(
        "/api/teachers/students", json=student_data_2, headers=auth_headers
    )

    # Should return 409 Conflict
    assert response.status_code == 409
    assert "學號" in response.json()["detail"]
    assert "已存在" in response.json()["detail"]

    # Clean up
    test_db_session.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student1_id
    ).delete()
    test_db_session.query(Student).filter(Student.id == student1_id).delete()
    test_db_session.commit()


def test_create_student_with_same_student_number_different_classroom(
    test_db_session: Session,
    classroom_a: Classroom,
    classroom_b: Classroom,
    auth_headers: dict,
    test_client: TestClient,
):
    """Test creating student with same student_number in different classroom should succeed"""
    # Using test_client fixture

    # Create first student with student_number "S002" in classroom A
    student_data_1 = {
        "name": "Student One",
        "birthdate": "2010-01-01",
        "student_number": "S002",
        "classroom_id": classroom_a.id,
    }

    response = test_client.post(
        "/api/teachers/students", json=student_data_1, headers=auth_headers
    )
    assert response.status_code == 200
    student1_id = response.json()["id"]

    # Create second student with same student_number "S002" in classroom B
    student_data_2 = {
        "name": "Student Two",
        "birthdate": "2010-01-02",
        "student_number": "S002",  # Same student_number
        "classroom_id": classroom_b.id,  # Different classroom
    }

    response = test_client.post(
        "/api/teachers/students", json=student_data_2, headers=auth_headers
    )

    # Should succeed (200 OK)
    assert response.status_code == 200
    student2_id = response.json()["id"]
    assert response.json()["student_id"] == "S002"

    # Clean up
    test_db_session.query(ClassroomStudent).filter(
        ClassroomStudent.student_id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.query(Student).filter(
        Student.id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.commit()


def test_update_student_with_duplicate_student_number_same_classroom(
    test_db_session: Session,
    classroom_a: Classroom,
    auth_headers: dict,
    test_client: TestClient,
):
    """Test updating student to have duplicate student_number in same classroom should fail"""
    # Using test_client fixture

    # Create first student with student_number "S003"
    student_data_1 = {
        "name": "Student One",
        "birthdate": "2010-01-01",
        "student_number": "S003",
        "classroom_id": classroom_a.id,
    }
    response = test_client.post(
        "/api/teachers/students", json=student_data_1, headers=auth_headers
    )
    assert response.status_code == 200
    student1_id = response.json()["id"]

    # Create second student with different student_number
    student_data_2 = {
        "name": "Student Two",
        "birthdate": "2010-01-02",
        "student_number": "S004",
        "classroom_id": classroom_a.id,
    }
    response = test_client.post(
        "/api/teachers/students", json=student_data_2, headers=auth_headers
    )
    assert response.status_code == 200
    student2_id = response.json()["id"]

    # Try to update second student to have same student_number as first
    update_data = {"student_number": "S003"}  # Same as student1

    response = test_client.put(
        f"/api/teachers/students/{student2_id}",
        json=update_data,
        headers=auth_headers,
    )

    # Should return 409 Conflict
    assert response.status_code == 409
    assert "學號" in response.json()["detail"]
    assert "已存在" in response.json()["detail"]

    # Clean up
    test_db_session.query(ClassroomStudent).filter(
        ClassroomStudent.student_id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.query(Student).filter(
        Student.id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.commit()


def test_move_student_to_classroom_with_duplicate_student_number(
    test_db_session: Session,
    classroom_a: Classroom,
    classroom_b: Classroom,
    auth_headers: dict,
    test_client: TestClient,
):
    """Test moving student to classroom where student_number already exists should fail"""
    # Using test_client fixture

    # Create first student with student_number "S005" in classroom A
    student_data_1 = {
        "name": "Student One",
        "birthdate": "2010-01-01",
        "student_number": "S005",
        "classroom_id": classroom_a.id,
    }
    response = test_client.post(
        "/api/teachers/students", json=student_data_1, headers=auth_headers
    )
    assert response.status_code == 200
    student1_id = response.json()["id"]

    # Create second student with same student_number "S005" in classroom B
    student_data_2 = {
        "name": "Student Two",
        "birthdate": "2010-01-02",
        "student_number": "S005",
        "classroom_id": classroom_b.id,
    }
    response = test_client.post(
        "/api/teachers/students", json=student_data_2, headers=auth_headers
    )
    assert response.status_code == 200
    student2_id = response.json()["id"]

    # Try to move second student to classroom A (where S005 already exists)
    update_data = {"classroom_id": classroom_a.id}

    response = test_client.put(
        f"/api/teachers/students/{student2_id}",
        json=update_data,
        headers=auth_headers,
    )

    # Should return 409 Conflict
    assert response.status_code == 409
    assert "學號" in response.json()["detail"]
    assert "已存在" in response.json()["detail"]

    # Clean up
    test_db_session.query(ClassroomStudent).filter(
        ClassroomStudent.student_id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.query(Student).filter(
        Student.id.in_([student1_id, student2_id])
    ).delete()
    test_db_session.commit()


def test_update_student_keep_same_student_number_should_succeed(
    test_db_session: Session,
    classroom_a: Classroom,
    auth_headers: dict,
    test_client: TestClient,
):
    """Test updating student while keeping the same student_number should succeed"""
    # Using test_client fixture

    # Create student with student_number "S006"
    student_data = {
        "name": "Student One",
        "birthdate": "2010-01-01",
        "student_number": "S006",
        "classroom_id": classroom_a.id,
    }
    response = test_client.post(
        "/api/teachers/students", json=student_data, headers=auth_headers
    )
    assert response.status_code == 200
    student_id = response.json()["id"]

    # Update name while keeping same student_number
    update_data = {"name": "Student One Updated", "student_number": "S006"}

    response = test_client.put(
        f"/api/teachers/students/{student_id}", json=update_data, headers=auth_headers
    )

    # Should succeed (200 OK)
    assert response.status_code == 200
    assert response.json()["name"] == "Student One Updated"
    assert response.json()["student_id"] == "S006"

    # Clean up
    test_db_session.query(ClassroomStudent).filter(
        ClassroomStudent.student_id == student_id
    ).delete()
    test_db_session.query(Student).filter(Student.id == student_id).delete()
    test_db_session.commit()
