"""
Test server-side filtering for dashboard endpoint - Security enhancement

Code review finding: Client-side filtering creates security vulnerability.
This test validates server-side filtering with authorization checks.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher, Classroom, ClassroomSchool, School, Organization
from models import TeacherSchool
import uuid


def test_dashboard_mode_personal_returns_only_personal_classrooms(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: mode=personal should return ONLY classrooms without school_id

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

    # Create 2 school classrooms
    school_classroom1 = Classroom(
        name="School Class 1",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    school_classroom2 = Classroom(
        name="School Class 2",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add_all([school_classroom1, school_classroom2])
    test_session.flush()

    # Link to school
    test_session.add_all(
        [
            ClassroomSchool(
                classroom_id=school_classroom1.id,
                school_id=school.id,
                is_active=True,
            ),
            ClassroomSchool(
                classroom_id=school_classroom2.id,
                school_id=school.id,
                is_active=True,
            ),
        ]
    )

    # Create 1 personal classroom
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal_classroom)
    test_session.commit()

    # Call dashboard API with mode=personal
    response = test_client.get(
        "/api/teachers/dashboard?mode=personal",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 classroom (personal)
    assert (
        len(data["classrooms"]) == 1
    ), f"Expected 1 classroom, got {len(data['classrooms'])}"
    assert data["classrooms"][0]["name"] == "Personal Class"
    assert data["classrooms"][0]["school_id"] is None


def test_dashboard_mode_school_returns_only_school_classrooms(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: mode=school&school_id=XXX should return ONLY that school's classrooms

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
    school1_classroom = Classroom(
        name="School 1 Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    school2_classroom = Classroom(
        name="School 2 Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add_all([school1_classroom, school2_classroom, personal_classroom])
    test_session.flush()

    # Link classrooms to schools
    test_session.add_all(
        [
            ClassroomSchool(
                classroom_id=school1_classroom.id,
                school_id=school1.id,
                is_active=True,
            ),
            ClassroomSchool(
                classroom_id=school2_classroom.id,
                school_id=school2.id,
                is_active=True,
            ),
        ]
    )
    test_session.commit()

    # Call dashboard API with mode=school&school_id=school1.id
    response = test_client.get(
        f"/api/teachers/dashboard?mode=school&school_id={school1.id}",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 classroom (school1's classroom)
    assert (
        len(data["classrooms"]) == 1
    ), f"Expected 1 classroom, got {len(data['classrooms'])}"
    assert data["classrooms"][0]["name"] == "School 1 Class"
    assert data["classrooms"][0]["school_id"] == str(school1.id)


def test_dashboard_mode_school_requires_authorization(
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
    test_session.commit()

    # Call dashboard API with school_id teacher doesn't have access to
    response = test_client.get(
        f"/api/teachers/dashboard?mode=school&school_id={school.id}",
        headers=auth_headers_teacher,
    )

    # Should return 403 Forbidden
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert (
        "Access denied" in response.json()["detail"]
        or "permission" in response.json()["detail"].lower()
    )


def test_dashboard_no_mode_returns_all_classrooms_backward_compatible(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: No mode parameter should return all classrooms (backward compatibility)

    Ensures existing frontend code continues to work
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

    # Create 1 school classroom and 1 personal classroom
    school_classroom = Classroom(
        name="School Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add_all([school_classroom, personal_classroom])
    test_session.flush()

    test_session.add(
        ClassroomSchool(
            classroom_id=school_classroom.id,
            school_id=school.id,
            is_active=True,
        )
    )
    test_session.commit()

    # Call dashboard API WITHOUT mode parameter
    response = test_client.get(
        "/api/teachers/dashboard",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ALL classrooms (2)
    assert (
        len(data["classrooms"]) == 2
    ), f"Expected 2 classrooms, got {len(data['classrooms'])}"
