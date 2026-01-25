import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy.orm import Session

from main import app
from models.organization import Organization, School, TeacherOrganization, TeacherSchool
from models.user import Teacher
from database import get_db


@pytest.fixture
def test_data(shared_test_session: Session):
    """Create test data for teacher organizations endpoint."""
    db = shared_test_session
    # Create teacher (id auto-increments, name, email, password_hash required)
    teacher = Teacher(
        name="Test Teacher",
        email="test_teacher_org@test.com",
        password_hash="hashed_password"
    )
    db.add(teacher)
    db.flush()

    # Create organization 1
    org1 = Organization(
        id=str(uuid4()),
        name="Happy English School",
        description="Test org 1"
    )
    db.add(org1)
    db.flush()

    # Create organization 2
    org2 = Organization(
        id=str(uuid4()),
        name="Fast Learning",
        description="Test org 2"
    )
    db.add(org2)
    db.flush()

    # Create schools for org1
    school1_1 = School(
        id=str(uuid4()),
        name="Nangang Branch",
        organization_id=org1.id
    )
    school1_2 = School(
        id=str(uuid4()),
        name="Xinyi Branch",
        organization_id=org1.id
    )
    db.add_all([school1_1, school1_2])
    db.flush()

    # Create school for org2
    school2_1 = School(
        id=str(uuid4()),
        name="Taipei Campus",
        organization_id=org2.id
    )
    db.add(school2_1)
    db.flush()

    # Link teacher to org1 as org_admin (ACTIVE)
    teacher_org1 = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org1.id,
        role="org_admin",
        is_active=True
    )
    db.add(teacher_org1)

    # Link teacher to school1_1 as teacher (ACTIVE)
    teacher_school1 = TeacherSchool(
        teacher_id=teacher.id,
        school_id=school1_1.id,
        roles=["teacher"],
        is_active=True
    )
    db.add(teacher_school1)

    # Link teacher to org2 as teacher (ACTIVE)
    teacher_org2 = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org2.id,
        role="teacher",
        is_active=True
    )
    db.add(teacher_org2)

    # Link teacher to school2_1 as school_admin (ACTIVE)
    teacher_school2 = TeacherSchool(
        teacher_id=teacher.id,
        school_id=school2_1.id,
        roles=["school_admin"],
        is_active=True
    )
    db.add(teacher_school2)

    db.commit()

    return {
        "teacher": teacher,
        "org1": org1,
        "org2": org2,
        "school1_1": school1_1,
        "school1_2": school1_2,
        "school2_1": school2_1,
    }


@pytest.fixture
def authenticated_client(shared_test_session: Session, test_data):
    """Create test client with authentication dependency override."""
    from routers.teachers.dependencies import get_current_teacher

    # Override get_current_teacher to return the test teacher
    async def override_get_current_teacher():
        return test_data["teacher"]

    # Override get_db to use shared test session
    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    # Apply overrides
    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        # Clean up overrides
        app.dependency_overrides.clear()


def test_get_teacher_organizations_success(test_data, authenticated_client):
    """Test GET /api/teachers/organizations returns correct structure."""
    teacher_id = test_data["teacher"].id

    response = authenticated_client.get(f"/api/teachers/{teacher_id}/organizations")

    assert response.status_code == 200
    data = response.json()

    assert "organizations" in data
    assert len(data["organizations"]) == 2

    # Check org1 structure
    org1_data = next(o for o in data["organizations"] if o["name"] == "Happy English School")
    assert org1_data["role"] == "org_admin"
    assert len(org1_data["schools"]) == 2

    # Check schools under org1
    school_names = [s["name"] for s in org1_data["schools"]]
    assert "Nangang Branch" in school_names
    assert "Xinyi Branch" in school_names

    nangang = next(s for s in org1_data["schools"] if s["name"] == "Nangang Branch")
    assert nangang["roles"] == ["teacher"]

    # Check org2 structure
    org2_data = next(o for o in data["organizations"] if o["name"] == "Fast Learning")
    assert org2_data["role"] == "teacher"
    assert len(org2_data["schools"]) == 1

    taipei = org2_data["schools"][0]
    assert taipei["name"] == "Taipei Campus"
    assert taipei["roles"] == ["school_admin"]


def test_get_teacher_organizations_no_orgs(shared_test_session: Session):
    """Test GET /api/teachers/organizations when teacher has no organizations."""
    db = shared_test_session
    # Create teacher with no organization memberships
    teacher = Teacher(
        name="Solo Teacher",
        email="solo_teacher_org@test.com",
        password_hash="hashed_password"
    )
    db.add(teacher)
    db.commit()

    from routers.teachers.dependencies import get_current_teacher

    # Override get_current_teacher
    async def override_get_current_teacher():
        return teacher

    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            response = client.get(f"/api/teachers/{teacher.id}/organizations")

        assert response.status_code == 200
        data = response.json()
        assert "organizations" in data
        assert data["organizations"] == []
    finally:
        app.dependency_overrides.clear()


def test_get_teacher_organizations_forbidden(shared_test_session: Session, test_data):
    """Test that a teacher cannot view another teacher's organizations (403 Forbidden)."""
    db = shared_test_session

    # Create second teacher
    other_teacher = Teacher(
        name="Other Teacher",
        email="other_teacher_org@test.com",
        password_hash="hashed_password"
    )
    db.add(other_teacher)
    db.commit()

    from routers.teachers.dependencies import get_current_teacher

    # Authenticate as first teacher but try to access second teacher's data
    async def override_get_current_teacher():
        return test_data["teacher"]

    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass

    app.dependency_overrides[get_current_teacher] = override_get_current_teacher
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            # Try to access other teacher's organizations (horizontal privilege escalation attempt)
            response = client.get(f"/api/teachers/{other_teacher.id}/organizations")

        assert response.status_code == 403
        assert "only view your own" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_get_teacher_organizations_unauthorized():
    """Test GET /api/teachers/organizations requires authentication."""
    fake_teacher_id = 99999

    with TestClient(app) as client:
        response = client.get(f"/api/teachers/{fake_teacher_id}/organizations")

    assert response.status_code == 401
