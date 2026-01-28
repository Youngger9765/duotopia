"""
Test server-side filtering for /api/teachers/students endpoint

This test validates the fix for Issue #112 where students were appearing
in the wrong workspace due to missing server-side filtering.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher, Classroom, ClassroomSchool, School, Organization, Student, ClassroomStudent
from models import TeacherSchool
import uuid
from datetime import date
from auth import get_password_hash


def test_students_returns_school_id_and_organization_id(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: /api/teachers/students should return school_id and organization_id

    Bug: Students displayed in wrong workspace mode
    Root cause: API didn't return school_id/organization_id, so frontend couldn't filter
    """
    # Create organization and school
    org = Organization(id=uuid.uuid4(), name="笨笨羊美語", is_active=True)
    test_session.add(org)
    test_session.flush()

    school = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="南港分校",
        is_active=True,
    )
    test_session.add(school)
    test_session.flush()

    # Create classroom belonging to school
    classroom = Classroom(
        name="Lion",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(classroom)
    test_session.flush()

    # Link classroom to school
    test_session.add(
        ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
    )

    # Create student in school classroom
    student = Student(
        name="Alice",
        email="alice@test.com",
        password_hash=get_password_hash("test123"),
        birthdate=date(2010, 1, 1),
        is_active=True,
    )
    test_session.add(student)
    test_session.flush()

    # Enroll student in classroom
    test_session.add(
        ClassroomStudent(
            student_id=student.id,
            classroom_id=classroom.id,
            is_active=True,
        )
    )

    # Create personal classroom (no school link)
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal_classroom)
    test_session.flush()

    # Create student in personal classroom
    personal_student = Student(
        name="Bob",
        email="bob@test.com",
        password_hash=get_password_hash("test123"),
        birthdate=date(2010, 1, 1),
        is_active=True,
    )
    test_session.add(personal_student)
    test_session.flush()

    test_session.add(
        ClassroomStudent(
            student_id=personal_student.id,
            classroom_id=personal_classroom.id,
            is_active=True,
        )
    )
    test_session.commit()

    # Call /api/teachers/students
    response = test_client.get(
        "/api/teachers/students",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Find students in response
    alice_in_response = next((s for s in data if s["name"] == "Alice"), None)
    bob_in_response = next((s for s in data if s["name"] == "Bob"), None)

    assert alice_in_response is not None, "Alice not found in response"
    assert bob_in_response is not None, "Bob not found in response"

    # CRITICAL: API must return school_id and organization_id
    assert "school_id" in alice_in_response, "school_id field missing from API response"
    assert "organization_id" in alice_in_response, "organization_id field missing"

    assert alice_in_response["school_id"] == str(school.id)
    assert alice_in_response["organization_id"] == str(org.id)

    # Personal student should have null school_id
    assert bob_in_response["school_id"] is None
    assert bob_in_response["organization_id"] is None


def test_students_mode_personal_returns_only_personal(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: mode=personal should return ONLY students without school_id

    Security: Server-side filtering prevents data leakage
    """
    # Create organization and school
    org = Organization(id=uuid.uuid4(), name="Test Org", is_active=True)
    test_session.add(org)
    test_session.flush()

    school = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Test School",
        is_active=True,
    )
    test_session.add(school)
    test_session.flush()

    # Create school classroom with 2 students
    school_classroom = Classroom(
        name="School Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(school_classroom)
    test_session.flush()

    test_session.add(
        ClassroomSchool(
            classroom_id=school_classroom.id,
            school_id=school.id,
            is_active=True,
        )
    )

    school_student1 = Student(name="School Student 1", email="s1@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    school_student2 = Student(name="School Student 2", email="s2@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    test_session.add_all([school_student1, school_student2])
    test_session.flush()

    test_session.add_all([
        ClassroomStudent(student_id=school_student1.id, classroom_id=school_classroom.id, is_active=True),
        ClassroomStudent(student_id=school_student2.id, classroom_id=school_classroom.id, is_active=True),
    ])

    # Create personal classroom with 1 student
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal_classroom)
    test_session.flush()

    personal_student = Student(name="Personal Student", email="p@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    test_session.add(personal_student)
    test_session.flush()

    test_session.add(
        ClassroomStudent(
            student_id=personal_student.id,
            classroom_id=personal_classroom.id,
            is_active=True,
        )
    )
    test_session.commit()

    # Call API with mode=personal
    response = test_client.get(
        "/api/teachers/students?mode=personal",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 student (personal)
    assert len(data) == 1, f"Expected 1 student, got {len(data)}"
    assert data[0]["name"] == "Personal Student"
    assert data[0].get("school_id") is None


def test_students_mode_school_returns_only_school_students(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: mode=school&school_id=XXX should return ONLY that school's students

    Security: Server-side filtering + authorization check
    """
    # Create organization and 2 schools
    org = Organization(id=uuid.uuid4(), name="Test Org", is_active=True)
    test_session.add(org)
    test_session.flush()

    school1 = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="School 1",
        is_active=True,
    )
    school2 = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="School 2",
        is_active=True,
    )
    test_session.add_all([school1, school2])
    test_session.flush()

    # Give teacher access to school1 only
    test_session.add(
        TeacherSchool(
            teacher_id=demo_teacher.id,
            school_id=school1.id,
            roles=["teacher"],
            is_active=True,
        )
    )

    # Create classrooms for both schools
    school1_classroom = Classroom(name="School 1 Class", teacher_id=demo_teacher.id, is_active=True)
    school2_classroom = Classroom(name="School 2 Class", teacher_id=demo_teacher.id, is_active=True)
    personal_classroom = Classroom(name="Personal Class", teacher_id=demo_teacher.id, is_active=True)
    test_session.add_all([school1_classroom, school2_classroom, personal_classroom])
    test_session.flush()

    # Link classrooms to schools
    test_session.add_all([
        ClassroomSchool(classroom_id=school1_classroom.id, school_id=school1.id, is_active=True),
        ClassroomSchool(classroom_id=school2_classroom.id, school_id=school2.id, is_active=True),
    ])

    # Create students
    s1_student = Student(name="School 1 Student", email="s1@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    s2_student = Student(name="School 2 Student", email="s2@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    personal_student = Student(name="Personal Student", email="p@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    test_session.add_all([s1_student, s2_student, personal_student])
    test_session.flush()

    test_session.add_all([
        ClassroomStudent(student_id=s1_student.id, classroom_id=school1_classroom.id, is_active=True),
        ClassroomStudent(student_id=s2_student.id, classroom_id=school2_classroom.id, is_active=True),
        ClassroomStudent(student_id=personal_student.id, classroom_id=personal_classroom.id, is_active=True),
    ])
    test_session.commit()

    # Call API with mode=school&school_id=school1.id
    response = test_client.get(
        f"/api/teachers/students?mode=school&school_id={school1.id}",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 student (school1's student)
    assert len(data) == 1, f"Expected 1 student, got {len(data)}"
    assert data[0]["name"] == "School 1 Student"
    assert data[0]["school_id"] == str(school1.id)


def test_students_mode_school_requires_authorization(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: Requesting school_id without access should return 403

    Security: Authorization check prevents data leakage
    """
    # Create organization and school
    org = Organization(id=uuid.uuid4(), name="Test Org", is_active=True)
    test_session.add(org)
    test_session.flush()

    school = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="Unauthorized School",
        is_active=True,
    )
    test_session.add(school)
    test_session.flush()

    # Create classroom for this school (teacher created it but no school access)
    classroom = Classroom(
        name="School Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(classroom)
    test_session.flush()

    test_session.add(
        ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
    )

    # Create student
    student = Student(name="Student", email="s@test.com", password_hash=get_password_hash("test123"), birthdate=date(2010, 1, 1), is_active=True)
    test_session.add(student)
    test_session.flush()

    test_session.add(
        ClassroomStudent(
            student_id=student.id,
            classroom_id=classroom.id,
            is_active=True,
        )
    )
    test_session.commit()

    # Call API with school_id teacher doesn't have access to
    response = test_client.get(
        f"/api/teachers/students?mode=school&school_id={school.id}",
        headers=auth_headers_teacher,
    )

    # Should return 403 Forbidden
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "Access denied" in response.json()["detail"] or \
           "permission" in response.json()["detail"].lower()
