"""
Test dashboard classroom filtering - Issue: Lion/Rabbit appearing in personal mode
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Teacher, Classroom, ClassroomSchool, School, Organization
from models import TeacherSchool, TeacherOrganization
import uuid


def test_dashboard_returns_classroom_with_school_id(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    RED TEST: Verify dashboard API returns school_id and organization_id for classrooms

    Bug: Lion and Rabbit classrooms (belonging to 南港分校) appear in personal mode
    Root cause: Dashboard API doesn't return school_id/organization_id
    """
    # Create organization and school
    org = Organization(
        id=uuid.uuid4(),
        name="笨笨羊美語",
        display_name="笨笨羊美語補習班",
        is_active=True,
    )
    test_session.add(org)
    test_session.flush()

    school = School(
        id=uuid.uuid4(),
        organization_id=org.id,
        name="南港分校",
        display_name="南港分校",
        is_active=True,
    )
    test_session.add(school)
    test_session.flush()

    # Create classroom belonging to school
    classroom = Classroom(
        name="Lion",
        description="暫無描述",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(classroom)
    test_session.flush()

    # Link classroom to school
    classroom_school = ClassroomSchool(
        classroom_id=classroom.id,
        school_id=school.id,
        is_active=True,
    )
    test_session.add(classroom_school)

    # Create personal classroom (no school)
    personal_classroom = Classroom(
        name="Personal Class",
        description="個人班級",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal_classroom)

    test_session.commit()

    # Call dashboard API
    response = test_client.get("/api/teachers/dashboard", headers=auth_headers_teacher)

    assert response.status_code == 200
    data = response.json()

    # Find Lion classroom in response
    lion_classroom = next(
        (c for c in data["classrooms"] if c["name"] == "Lion"),
        None
    )
    personal_class = next(
        (c for c in data["classrooms"] if c["name"] == "Personal Class"),
        None
    )

    assert lion_classroom is not None, "Lion classroom should be in response"
    assert personal_class is not None, "Personal classroom should be in response"

    # This test will FAIL because current API doesn't return these fields
    assert "school_id" in lion_classroom, "school_id should be present"
    assert "organization_id" in lion_classroom, "organization_id should be present"

    # Lion should have school_id
    assert lion_classroom["school_id"] == str(school.id), \
        f"Lion should have school_id={school.id}"

    # Lion should have organization_id
    assert lion_classroom["organization_id"] == str(org.id), \
        f"Lion should have organization_id={org.id}"

    # Personal classroom should NOT have school_id or organization_id
    assert personal_class.get("school_id") is None, \
        "Personal classroom should not have school_id"
    assert personal_class.get("organization_id") is None, \
        "Personal classroom should not have organization_id"


def test_personal_mode_filter_logic(
    test_client: TestClient,
    test_session: Session,
    demo_teacher: Teacher,
    auth_headers_teacher: dict,
):
    """
    Test that personal mode ONLY shows classrooms without school_id/organization_id

    This is a documentation test - the actual filtering happens in frontend
    But backend must provide the data for frontend to filter correctly
    """
    # Create organization and school
    org = Organization(
        id=uuid.uuid4(),
        name="笨笨羊美語",
        is_active=True,
    )
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

    # Create 2 school classrooms
    lion = Classroom(name="Lion", teacher_id=demo_teacher.id, is_active=True)
    rabbit = Classroom(name="Rabbit", teacher_id=demo_teacher.id, is_active=True)
    test_session.add_all([lion, rabbit])
    test_session.flush()

    # Link to school
    test_session.add_all([
        ClassroomSchool(classroom_id=lion.id, school_id=school.id, is_active=True),
        ClassroomSchool(classroom_id=rabbit.id, school_id=school.id, is_active=True),
    ])

    # Create 1 personal classroom
    personal = Classroom(
        name="Personal",
        teacher_id=demo_teacher.id,
        is_active=True,
    )
    test_session.add(personal)
    test_session.commit()

    # Get dashboard
    response = test_client.get("/api/teachers/dashboard", headers=auth_headers_teacher)
    assert response.status_code == 200
    data = response.json()

    # All 3 classrooms should be returned
    assert len(data["classrooms"]) == 3

    # Frontend should filter based on school_id/organization_id
    # Personal mode: show only classrooms where school_id is None AND organization_id is None
    personal_mode_classrooms = [
        c for c in data["classrooms"]
        if c.get("school_id") is None and c.get("organization_id") is None
    ]

    # Should only return Personal classroom
    assert len(personal_mode_classrooms) == 1, \
        f"Personal mode should show 1 classroom, got {len(personal_mode_classrooms)}"
    assert personal_mode_classrooms[0]["name"] == "Personal"
