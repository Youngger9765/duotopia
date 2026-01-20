"""Tests for school student management API

TDD Approach:
1. RED: Write failing tests
2. GREEN: Implement features (already done, verifying)
3. REFACTOR: Clean up code

Test Coverage:
- Permission tests (school_admin, org_admin, org_owner, teacher)
- CRUD operations (create, read, update, delete)
- Many-to-many relationships (student-school, student-classroom)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from datetime import date

from main import app
from models import (
    Teacher, School, Organization, TeacherSchool, TeacherOrganization,
    Classroom, ClassroomSchool, Student, StudentSchool, ClassroomStudent
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

    db_path = tmp_path / "test_school_students.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
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
def school_admin_teacher(test_db: Session):
    """Create teacher with school_admin role"""
    teacher = Teacher(
        email="admin@test.com",
        name="School Admin",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin_teacher(test_db: Session):
    """Create teacher with org_admin role"""
    teacher = Teacher(
        email="orgadmin@test.com",
        name="Org Admin",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(test_db: Session):
    """Create regular teacher (no admin role)"""
    teacher = Teacher(
        email="teacher@test.com",
        name="Regular Teacher",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def link_school_admin(test_db: Session, school_admin_teacher, school):
    """Link teacher to school with school_admin role"""
    link = TeacherSchool(
        teacher_id=school_admin_teacher.id,
        school_id=school.id,
        roles=["school_admin"],
        is_active=True,
    )
    test_db.add(link)
    test_db.commit()


@pytest.fixture
def link_org_admin(test_db: Session, org_admin_teacher, organization):
    """Link teacher to organization with org_admin role"""
    link = TeacherOrganization(
        teacher_id=org_admin_teacher.id,
        organization_id=organization.id,
        role="org_admin",
        is_active=True,
    )
    test_db.add(link)
    test_db.commit()


def get_test_token(teacher_id: int) -> str:
    """Generate test JWT token"""
    return create_access_token({"sub": str(teacher_id), "type": "teacher"})


class TestSchoolStudentPermissions:
    """Test permission checks for school student management"""

    def test_school_admin_can_list_students(
        self, client: TestClient, school_admin_teacher, school, link_school_admin
    ):
        """School admin should be able to list students"""
        response = client.get(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_org_admin_can_list_students(
        self, client: TestClient, org_admin_teacher, school, link_org_admin
    ):
        """Org admin should be able to list students"""
        response = client.get(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(org_admin_teacher.id)}"}
        )
        assert response.status_code == 200

    def test_regular_teacher_cannot_list_students(
        self, client: TestClient, regular_teacher, school
    ):
        """Regular teacher should NOT be able to list students"""
        response = client.get(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(regular_teacher.id)}"}
        )
        assert response.status_code == 403

    def test_school_admin_can_create_student(
        self, client: TestClient, school_admin_teacher, school, link_school_admin
    ):
        """School admin should be able to create student"""
        response = client.post(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={
                "name": "Test Student",
                "birthdate": "2010-01-01",
                "student_number": "001",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Student"
        assert "default_password" in data

    def test_regular_teacher_cannot_create_student(
        self, client: TestClient, regular_teacher, school
    ):
        """Regular teacher should NOT be able to create student"""
        response = client.post(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(regular_teacher.id)}"},
            json={
                "name": "Test Student",
                "birthdate": "2010-01-01",
            }
        )
        assert response.status_code == 403


class TestSchoolStudentCRUD:
    """Test CRUD operations for school students"""

    @pytest.fixture
    def student(self, test_db: Session, school_admin_teacher, school, link_school_admin):
        """Create a test student in school"""
        # Create student via API would require full request setup
        # Instead create directly for other tests
        student = Student(
            name="Test Student",
            birthdate=date(2010, 1, 1),
            password_hash=get_password_hash("12345678"),
            is_active=True,
        )
        test_db.add(student)
        test_db.flush()
        
        student_school = StudentSchool(
            student_id=student.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(student_school)
        test_db.commit()
        test_db.refresh(student)
        return student

    def test_create_student_in_school(
        self, client: TestClient, school_admin_teacher, school, link_school_admin
    ):
        """Test creating a student in school"""
        response = client.post(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={
                "name": "New Student",
                "birthdate": "2011-02-15",
                "student_number": "002",
                "email": "student@test.com",
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Student"
        assert data["student_number"] == "002"
        assert "id" in data
        assert "default_password" in data

    def test_get_school_students(
        self, client: TestClient, school_admin_teacher, school, link_school_admin, student
    ):
        """Test listing students in school"""
        response = client.get(
            f"/api/schools/{school.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
        )
        assert response.status_code == 200
        students = response.json()
        assert len(students) >= 1
        assert any(s["id"] == student.id for s in students)

    def test_update_student(
        self, client: TestClient, school_admin_teacher, school, link_school_admin, student
    ):
        """Test updating student information"""
        response = client.put(
            f"/api/schools/{school.id}/students/{student.id}",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={
                "name": "Updated Student",
                "email": "updated@test.com",
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Student"
        assert data["email"] == "updated@test.com"

    def test_remove_student_from_school(
        self, client: TestClient, school_admin_teacher, school, link_school_admin, student
    ):
        """Test removing student from school (soft delete)"""
        response = client.delete(
            f"/api/schools/{school.id}/students/{student.id}",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()


class TestStudentClassroomRelationship:
    """Test many-to-many relationship between students and classrooms"""

    @pytest.fixture
    def classroom(self, test_db: Session, school_admin_teacher, school, link_school_admin):
        """Create a test classroom in school"""
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=school_admin_teacher.id,
            level=ProgramLevel.A1,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.flush()
        
        classroom_school = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(classroom_school)
        test_db.commit()
        test_db.refresh(classroom)
        return classroom

    @pytest.fixture
    def student(self, test_db: Session, school_admin_teacher, school, link_school_admin):
        """Create a test student in school"""
        student = Student(
            name="Test Student",
            birthdate=date(2010, 1, 1),
            password_hash=get_password_hash("12345678"),
            is_active=True,
        )
        test_db.add(student)
        test_db.flush()
        
        student_school = StudentSchool(
            student_id=student.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(student_school)
        test_db.commit()
        test_db.refresh(student)
        return student

    def test_add_student_to_classroom(
        self, client: TestClient, school_admin_teacher, school, link_school_admin,
        student, classroom
    ):
        """Test adding student to classroom"""
        response = client.post(
            f"/api/schools/{school.id}/students/{student.id}/classrooms",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={"classroom_id": classroom.id}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["classrooms"]) >= 1
        assert any(c["id"] == classroom.id for c in data["classrooms"])

    def test_student_can_belong_to_multiple_classrooms(
        self, client: TestClient, school_admin_teacher, school, link_school_admin,
        student, classroom
    ):
        """Test that a student can belong to multiple classrooms"""
        # Create second classroom
        classroom2 = Classroom(
            name="Test Classroom 2",
            teacher_id=school_admin_teacher.id,
            level=ProgramLevel.A2,
            is_active=True,
        )
        test_db = client.app.dependency_overrides[get_db]().__next__()
        test_db.add(classroom2)
        test_db.flush()
        
        classroom_school2 = ClassroomSchool(
            classroom_id=classroom2.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(classroom_school2)
        test_db.commit()
        test_db.refresh(classroom2)
        
        # Add student to first classroom
        response1 = client.post(
            f"/api/schools/{school.id}/students/{student.id}/classrooms",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={"classroom_id": classroom.id}
        )
        assert response1.status_code == 200
        
        # Add student to second classroom
        response2 = client.post(
            f"/api/schools/{school.id}/students/{student.id}/classrooms",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={"classroom_id": classroom2.id}
        )
        assert response2.status_code == 200
        data = response2.json()
        assert len(data["classrooms"]) >= 2
        classroom_ids = [c["id"] for c in data["classrooms"]]
        assert classroom.id in classroom_ids
        assert classroom2.id in classroom_ids

    def test_remove_student_from_classroom(
        self, client: TestClient, school_admin_teacher, school, link_school_admin,
        student, classroom
    ):
        """Test removing student from classroom"""
        # First add student to classroom
        client.post(
            f"/api/schools/{school.id}/students/{student.id}/classrooms",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={"classroom_id": classroom.id}
        )
        
        # Then remove
        response = client.delete(
            f"/api/schools/{school.id}/students/{student.id}/classrooms/{classroom.id}",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
        )
        assert response.status_code == 200
        assert "removed" in response.json()["message"].lower()

    def test_get_classroom_students(
        self, client: TestClient, school_admin_teacher, school, link_school_admin,
        student, classroom
    ):
        """Test getting students in a classroom"""
        # Add student to classroom
        client.post(
            f"/api/schools/{school.id}/students/{student.id}/classrooms",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"},
            json={"classroom_id": classroom.id}
        )
        
        # Get classroom students
        response = client.get(
            f"/api/schools/{school.id}/classrooms/{classroom.id}/students",
            headers={"Authorization": f"Bearer {get_test_token(school_admin_teacher.id)}"}
        )
        assert response.status_code == 200
        students = response.json()
        assert len(students) >= 1
        assert any(s["id"] == student.id for s in students)

