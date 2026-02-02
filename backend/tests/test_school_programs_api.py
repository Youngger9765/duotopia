"""
School Programs API Tests
測試學校教材 CRUD 和權限控制
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from main import app
from database import get_db
from models import (
    Teacher,
    Organization,
    School,
    TeacherOrganization,
    TeacherSchool,
    Program,
)
from auth import create_access_token


@pytest.fixture
def test_db(tmp_path):
    """Create test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base

    db_path = tmp_path / "test_school_programs.db"
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
def org_owner(test_db):
    """Create org_owner teacher"""
    teacher = Teacher(
        email="owner@test.com",
        name="Test Owner",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin(test_db):
    """Create org_admin teacher"""
    teacher = Teacher(
        email="admin@test.com",
        name="Test Admin",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def school_admin(test_db):
    """Create school_admin teacher"""
    teacher = Teacher(
        email="schooladmin@test.com",
        name="School Admin",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(test_db):
    """Create regular teacher"""
    teacher = Teacher(
        email="teacher@test.com",
        name="Regular Teacher",
        password_hash="hashed",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def organization(test_db):
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
def school(test_db, organization):
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
def setup_org_owner(test_db, org_owner, organization):
    """Setup org_owner membership"""
    membership = TeacherOrganization(
        teacher_id=org_owner.id,
        organization_id=organization.id,
        role="org_owner",
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()
    return org_owner


@pytest.fixture
def setup_org_admin(test_db, org_admin, organization):
    """Setup org_admin membership"""
    membership = TeacherOrganization(
        teacher_id=org_admin.id,
        organization_id=organization.id,
        role="org_admin",
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()
    return org_admin


@pytest.fixture
def setup_school_admin(test_db, school_admin, school):
    """Setup school_admin membership"""
    membership = TeacherSchool(
        teacher_id=school_admin.id,
        school_id=school.id,
        roles=["school_admin"],
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()
    return school_admin


@pytest.fixture
def setup_regular_teacher(test_db, regular_teacher, school):
    """Setup regular teacher membership"""
    membership = TeacherSchool(
        teacher_id=regular_teacher.id,
        school_id=school.id,
        roles=["teacher"],
        is_active=True,
    )
    test_db.add(membership)
    test_db.commit()
    return regular_teacher


def get_token(teacher):
    """Generate JWT token for teacher"""
    return create_access_token(
        data={
            "sub": str(teacher.id),
            "email": teacher.email,
            "type": "teacher",
            "name": teacher.name,
            "role": "teacher",
        }
    )


class TestSchoolProgramsAccess:
    """測試學校教材存取權限"""

    def test_org_owner_can_access_school_programs(
        self, client, school, setup_org_owner
    ):
        """org_owner 可以存取學校教材"""
        token = get_token(setup_org_owner)
        response = client.get(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_org_admin_can_access_school_programs(
        self, client, school, setup_org_admin
    ):
        """org_admin 可以存取學校教材"""
        token = get_token(setup_org_admin)
        response = client.get(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_school_admin_can_access_school_programs(
        self, client, school, setup_school_admin
    ):
        """school_admin 可以存取學校教材"""
        token = get_token(setup_school_admin)
        response = client.get(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_regular_teacher_can_access_school_programs(
        self, client, school, setup_regular_teacher
    ):
        """一般教師可以存取學校教材"""
        token = get_token(setup_regular_teacher)
        response = client.get(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_unauthorized_teacher_cannot_access(self, client, school, regular_teacher):
        """未加入學校的教師無法存取"""
        token = get_token(regular_teacher)
        response = client.get(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403


class TestSchoolProgramsCRUD:
    """測試學校教材 CRUD 操作"""

    def test_org_owner_can_create_program(self, client, school, setup_org_owner):
        """org_owner 可以建立教材"""
        token = get_token(setup_org_owner)
        response = client.post(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Test Program", "description": "Test Description"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Program"
        assert data["description"] == "Test Description"

    def test_org_admin_can_create_program(self, client, school, setup_org_admin):
        """org_admin 可以建立教材"""
        token = get_token(setup_org_admin)
        response = client.post(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Admin Program"},
        )
        assert response.status_code == 201

    def test_school_admin_can_create_program(self, client, school, setup_school_admin):
        """school_admin 可以建立教材"""
        token = get_token(setup_school_admin)
        response = client.post(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "School Program"},
        )
        assert response.status_code == 201

    def test_regular_teacher_cannot_create_program(
        self, client, school, setup_regular_teacher
    ):
        """一般教師無法建立教材"""
        token = get_token(setup_regular_teacher)
        response = client.post(
            f"/api/schools/{school.id}/programs",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Teacher Program"},
        )
        assert response.status_code == 403

    def test_update_program(self, client, test_db, school, setup_org_owner):
        """測試更新教材"""
        # Create program first
        program = Program(
            name="Original Name",
            school_id=school.id,
            teacher_id=setup_org_owner.id,
            is_template=True,
            is_active=True,
        )
        test_db.add(program)
        test_db.commit()
        test_db.refresh(program)

        token = get_token(setup_org_owner)
        response = client.put(
            f"/api/schools/{school.id}/programs/{program.id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Updated Name", "description": "Updated Desc"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_program(self, client, test_db, school, setup_org_owner):
        """測試刪除教材"""
        # Create program first
        program = Program(
            name="To Delete",
            school_id=school.id,
            teacher_id=setup_org_owner.id,
            is_template=True,
            is_active=True,
        )
        test_db.add(program)
        test_db.commit()
        test_db.refresh(program)

        token = get_token(setup_org_owner)
        response = client.delete(
            f"/api/schools/{school.id}/programs/{program.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        # Verify soft delete
        test_db.refresh(program)
        assert program.is_active is False
