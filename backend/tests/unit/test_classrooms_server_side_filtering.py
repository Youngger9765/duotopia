"""
Test server-side filtering for /api/teachers/classrooms endpoint

This test validates the fix for Issue #112 where classrooms were appearing
in the wrong workspace due to missing server-side filtering.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher, Classroom, ClassroomSchool, School, Organization
from models import TeacherSchool
import uuid


def test_classrooms_returns_school_id_and_organization_id(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: /api/teachers/classrooms should return school_id and organization_id

    Bug: Lion and Rabbit classrooms (belonging to 南港分校) appeared in personal mode
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

    # Create Lion classroom belonging to school
    lion_classroom = Classroom(
        name="Lion",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(lion_classroom)
    test_session.flush()

    # Link Lion to school
    test_session.add(
        ClassroomSchool(
            classroom_id=lion_classroom.id,
            school_id=school.id,
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
    test_session.commit()

    # Call /api/teachers/classrooms
    response = test_client.get(
        "/api/teachers/classrooms",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Find Lion classroom in response
    lion_in_response = next((c for c in data if c["name"] == "Lion"), None)
    assert lion_in_response is not None, "Lion classroom not found in response"

    # CRITICAL: API must return school_id and organization_id
    assert "school_id" in lion_in_response, "school_id field missing from API response"
    assert "organization_id" in lion_in_response, "organization_id field missing"

    assert lion_in_response["school_id"] == str(school.id)
    assert lion_in_response["organization_id"] == str(org.id)

    # Personal classroom should have null school_id
    personal_in_response = next((c for c in data if c["name"] == "Personal Class"), None)
    assert personal_in_response is not None
    assert personal_in_response["school_id"] is None
    assert personal_in_response["organization_id"] is None


def test_classrooms_mode_personal_returns_only_personal(
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
    test_session.add_all([
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
    ])

    # Create 1 personal classroom
    personal_classroom = Classroom(
        name="Personal Class",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal_classroom)
    test_session.commit()

    # Call API with mode=personal
    response = test_client.get(
        "/api/teachers/classrooms?mode=personal",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 classroom (personal)
    assert len(data) == 1, f"Expected 1 classroom, got {len(data)}"
    assert data[0]["name"] == "Personal Class"
    assert data[0].get("school_id") is None


def test_classrooms_mode_school_returns_only_school_classrooms(
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
    test_session.add_all([
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
    ])
    test_session.commit()

    # Call API with mode=school&school_id=school1.id
    response = test_client.get(
        f"/api/teachers/classrooms?mode=school&school_id={school1.id}",
        headers=auth_headers_teacher,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return ONLY 1 classroom (school1's classroom)
    assert len(data) == 1, f"Expected 1 classroom, got {len(data)}"
    assert data[0]["name"] == "School 1 Class"
    assert data[0]["school_id"] == str(school1.id)


def test_classrooms_mode_school_requires_authorization(
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

    # Call API with school_id teacher doesn't have access to
    response = test_client.get(
        f"/api/teachers/classrooms?mode=school&school_id={school.id}",
        headers=auth_headers_teacher,
    )

    # Should return 403 Forbidden
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "Access denied" in response.json()["detail"] or \
           "permission" in response.json()["detail"].lower()
