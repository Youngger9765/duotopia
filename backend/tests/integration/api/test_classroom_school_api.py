"""
Integration tests for Classroom-School relationship API.

Tests the linking of classrooms to schools with proper permission checks.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from models import Teacher, Organization, School, Classroom, TeacherOrganization, ClassroomSchool
from auth import create_access_token
from database import get_db


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def test_data(db_session: Session):
    """Create all test data in one fixture"""
    # Create teacher
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:8]}@test.com",
        name="Test Teacher",
        password_hash="dummy_hash",
        is_active=True,
    )
    db_session.add(teacher)
    db_session.flush()

    # Create organization
    org = Organization(
        name=f"test-org-{uuid.uuid4().hex[:8]}",
        display_name="Test Organization",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    # Add teacher as org_owner
    teacher_org = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    db_session.add(teacher_org)
    db_session.flush()

    # Create school
    school = School(
        organization_id=org.id,
        name=f"test-school-{uuid.uuid4().hex[:8]}",
        display_name="Test School",
        is_active=True,
    )
    db_session.add(school)
    db_session.flush()

    # Create classroom
    classroom = Classroom(
        name=f"Test Classroom {uuid.uuid4().hex[:4]}",
        teacher_id=teacher.id,
        is_active=True,
    )
    db_session.add(classroom)
    db_session.commit()

    return {
        "teacher": teacher,
        "organization": org,
        "school": school,
        "classroom": classroom,
    }


@pytest.fixture
def auth_headers(test_data):
    """Generate auth headers for test teacher"""
    token = create_access_token({"sub": str(test_data["teacher"].id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


class TestClassroomSchoolLinking:
    """Tests for linking classrooms to schools"""

    def test_link_classroom_to_school_success(
        self,
        test_client: TestClient,
        db_session: Session,
        test_data: dict,
        auth_headers: dict,
    ):
        """Test successfully linking a classroom to a school"""
        classroom = test_data["classroom"]
        school = test_data["school"]

        response = test_client.post(
            f"/api/classrooms/{classroom.id}/school",
            json={"school_id": str(school.id)},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["classroom_id"] == classroom.id
        assert data["school_id"] == str(school.id)
        assert data["is_active"] is True

        # Verify database record
        link = db_session.query(ClassroomSchool).filter(
            ClassroomSchool.classroom_id == classroom.id,
            ClassroomSchool.school_id == school.id,
        ).first()
        assert link is not None
        assert link.is_active is True

    def test_link_classroom_already_linked(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_classroom: Classroom,
        test_school: School,
        auth_headers: dict,
    ):
        """Test linking a classroom that's already linked to a school"""
        # First link
        test_client.post(
            f"/api/classrooms/{test_classroom.id}/school",
            json={"school_id": str(test_school.id)},
            headers=auth_headers,
        )

        # Try to link again
        response = test_client.post(
            f"/api/classrooms/{test_classroom.id}/school",
            json={"school_id": str(test_school.id)},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "already linked" in response.json()["detail"].lower()

    def test_get_classroom_school(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_classroom: Classroom,
        test_school: School,
        auth_headers: dict,
    ):
        """Test getting classroom's school information"""
        # Link classroom to school
        link = ClassroomSchool(
            classroom_id=test_classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(link)
        shared_test_session.commit()

        # Get classroom's school
        response = test_client.get(
            f"/api/classrooms/{test_classroom.id}/school",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_school.id)
        assert data["name"] == test_school.name
        assert data["display_name"] == test_school.display_name

    def test_get_classroom_school_not_linked(
        self,
        test_client: TestClient,
        test_classroom: Classroom,
        auth_headers: dict,
    ):
        """Test getting school for classroom that's not linked"""
        response = test_client.get(
            f"/api/classrooms/{test_classroom.id}/school",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not linked" in response.json()["detail"].lower()

    def test_unlink_classroom_from_school(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_classroom: Classroom,
        test_school: School,
        auth_headers: dict,
    ):
        """Test unlinking classroom from school"""
        # Link classroom to school
        link = ClassroomSchool(
            classroom_id=test_classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(link)
        shared_test_session.commit()

        # Unlink
        response = test_client.delete(
            f"/api/classrooms/{test_classroom.id}/school",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "unlinked" in response.json()["message"].lower()

        # Verify soft delete
        shared_test_session.refresh(link)
        assert link.is_active is False

    def test_list_classrooms_by_school(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_school: School,
        test_teacher: Teacher,
        auth_headers: dict,
    ):
        """Test listing all classrooms in a school"""
        # Create multiple classrooms and link to school
        classrooms = []
        for i in range(3):
            classroom = Classroom(
                name=f"Classroom {i}",
                teacher_id=test_teacher.id,
                is_active=True,
            )
            shared_test_session.add(classroom)
            shared_test_session.commit()
            shared_test_session.refresh(classroom)

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            shared_test_session.add(link)
            classrooms.append(classroom)

        shared_test_session.commit()

        # Get classrooms in school
        response = test_client.get(
            f"/api/schools/{test_school.id}/classrooms",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        classroom_ids = [c["id"] for c in data]
        for classroom in classrooms:
            assert classroom.id in classroom_ids

    def test_one_classroom_one_school_constraint(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        test_classroom: Classroom,
        test_organization: Organization,
        auth_headers: dict,
    ):
        """Test that a classroom can only be linked to one school at a time"""
        # Create two schools
        school1 = School(
            organization_id=test_organization.id,
            name="school-1",
            is_active=True,
        )
        school2 = School(
            organization_id=test_organization.id,
            name="school-2",
            is_active=True,
        )
        shared_test_session.add_all([school1, school2])
        shared_test_session.commit()
        shared_test_session.refresh(school1)
        shared_test_session.refresh(school2)

        # Link to school1
        response = test_client.post(
            f"/api/classrooms/{test_classroom.id}/school",
            json={"school_id": str(school1.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201

        # Try to link to school2
        response = test_client.post(
            f"/api/classrooms/{test_classroom.id}/school",
            json={"school_id": str(school2.id)},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already linked" in response.json()["detail"].lower()
