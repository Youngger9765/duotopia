"""
測試作業 API 功能
Test assignment API functionality with TDD approach
"""

import pytest
from datetime import datetime, timedelta, timezone  # noqa: F401
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from database import get_db
from models import (
    Teacher,
    Student,
    Classroom,
    Assignment,
    StudentAssignment,
    AssignmentStatus,
    ClassroomStudent,
    ProgramLevel,
)
from auth import create_access_token


@pytest.fixture
def test_db(tmp_path):
    """Create a test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base

    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{tmp_path}/test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestingSessionLocal()

    app.dependency_overrides.clear()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_teacher(test_db: Session):
    """Create a test teacher"""
    teacher = Teacher(
        email="test.teacher@example.com",
        password_hash="hashed_password",
        name="Test Teacher",
        is_demo=False,
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def test_classroom(test_db: Session, test_teacher):
    """Create a test classroom"""
    classroom = Classroom(
        name="Test Classroom",
        description="Test classroom for testing",
        level=ProgramLevel.A1,
        teacher_id=test_teacher.id,
        is_active=True,
    )
    test_db.add(classroom)
    test_db.commit()
    test_db.refresh(classroom)
    return classroom


@pytest.fixture
def test_students(test_db: Session, test_classroom):
    """Create test students"""
    students = []
    for i in range(5):
        student = Student(
            name=f"Student {i+1}",
            email=f"student{i+1}@example.com",
            password_hash="hashed_password",
            birthdate=datetime(2010, 1, 1),
            is_active=True,
        )
        test_db.add(student)
        test_db.flush()

        # Add to classroom
        classroom_student = ClassroomStudent(
            classroom_id=test_classroom.id, student_id=student.id, is_active=True
        )
        test_db.add(classroom_student)
        students.append(student)

    test_db.commit()
    return students


@pytest.fixture
def test_assignment(test_db: Session, test_teacher, test_classroom):
    """Create a test assignment"""
    assignment = Assignment(
        title="Test Assignment",
        description="Test assignment description",
        classroom_id=test_classroom.id,
        teacher_id=test_teacher.id,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    test_db.add(assignment)
    test_db.commit()
    test_db.refresh(assignment)
    return assignment


@pytest.fixture
def auth_headers(test_teacher):
    """Create authentication headers"""
    token = create_access_token(data={"sub": str(test_teacher.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


class TestAssignmentAPI:
    """Test assignment API endpoints"""

    def test_get_assignment_detail(self, client, test_assignment, auth_headers):
        """測試取得作業詳情"""
        response = client.get(
            f"/api/assignments/{test_assignment.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_assignment.id
        assert data["title"] == "Test Assignment"
        assert "student_ids" in data
        assert isinstance(data["student_ids"], list)

    def test_patch_assignment_title(self, client, test_assignment, auth_headers):
        """測試更新作業標題"""
        new_title = "Updated Assignment Title"
        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json={"title": new_title},
        )
        assert response.status_code == 200

        # Verify the update
        response = client.get(
            f"/api/assignments/{test_assignment.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == new_title

    def test_patch_assignment_student_ids(
        self, client, test_assignment, test_students, auth_headers, test_db
    ):
        """測試更新作業的學生指派"""
        student_ids = [test_students[0].id, test_students[1].id]

        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json={"student_ids": student_ids},
        )
        assert response.status_code == 200

        # Verify students are assigned
        response = client.get(
            f"/api/assignments/{test_assignment.id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data["student_ids"]) == set(student_ids)

        # Verify StudentAssignment records exist
        student_assignments = (
            test_db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == test_assignment.id)
            .all()
        )
        assert len(student_assignments) == 2
        assigned_student_ids = [sa.student_id for sa in student_assignments]
        assert set(assigned_student_ids) == set(student_ids)

    def test_patch_assignment_remove_students(
        self, client, test_assignment, test_students, auth_headers, test_db
    ):
        """測試移除學生指派"""
        # First assign 3 students
        initial_student_ids = [
            test_students[0].id,
            test_students[1].id,
            test_students[2].id,
        ]
        client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json={"student_ids": initial_student_ids},
        )

        # Then reduce to 1 student
        final_student_ids = [test_students[0].id]
        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json={"student_ids": final_student_ids},
        )
        assert response.status_code == 200

        # Verify only 1 student remains
        response = client.get(
            f"/api/assignments/{test_assignment.id}", headers=auth_headers
        )
        data = response.json()
        assert data["student_ids"] == final_student_ids

        # Verify database records
        student_assignments = (
            test_db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == test_assignment.id)
            .all()
        )
        assert len(student_assignments) == 1
        assert student_assignments[0].student_id == test_students[0].id

    def test_patch_assignment_multiple_fields(
        self, client, test_assignment, test_students, auth_headers
    ):
        """測試同時更新多個欄位"""
        new_data = {
            "title": "Multi-Update Title",
            "description": "Multi-Update Description",
            "due_date": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "student_ids": [test_students[1].id, test_students[3].id],
        }

        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json=new_data,
        )
        assert response.status_code == 200

        # Verify all updates
        response = client.get(
            f"/api/assignments/{test_assignment.id}", headers=auth_headers
        )
        data = response.json()
        assert data["title"] == new_data["title"]
        assert data["description"] == new_data["description"]
        assert set(data["student_ids"]) == set(new_data["student_ids"])

    def test_get_assignment_progress(
        self, client, test_assignment, test_students, auth_headers, test_db
    ):
        """測試取得作業進度"""
        # Assign students first
        student_ids = [test_students[0].id, test_students[2].id]
        for student_id in student_ids:
            sa = StudentAssignment(
                assignment_id=test_assignment.id,
                student_id=student_id,
                classroom_id=test_assignment.classroom_id,
                title=test_assignment.title,
                instructions=test_assignment.description,
                due_date=test_assignment.due_date,
                status=AssignmentStatus.NOT_STARTED,
                assigned_at=datetime.now(timezone.utc),
                is_active=True,
            )
            test_db.add(sa)
        test_db.commit()

        # Get progress
        response = client.get(
            f"/api/assignments/{test_assignment.id}/progress", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 2

        student_ids_in_progress = [item["student_id"] for item in data]
        assert set(student_ids_in_progress) == set(student_ids)

        for item in data:
            assert item["status"] == "NOT_STARTED"
            assert "student_name" in item
            assert "student_id" in item

    def test_get_classroom_students(
        self, client, test_classroom, test_students, auth_headers
    ):
        """測試取得班級學生列表"""
        response = client.get(
            f"/api/classrooms/{test_classroom.id}/students", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == len(test_students)

        student_ids = [s["id"] for s in data]
        expected_ids = [s.id for s in test_students]
        assert set(student_ids) == set(expected_ids)

    def test_unauthorized_access(self, client, test_assignment):
        """測試未授權存取"""
        # Without auth headers
        response = client.get(f"/api/assignments/{test_assignment.id}")
        assert response.status_code == 401

        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            json={"title": "Unauthorized Update"},
        )
        assert response.status_code == 401

    def test_assignment_not_found(self, client, auth_headers):
        """測試作業不存在"""
        response = client.get("/api/assignments/99999", headers=auth_headers)
        assert response.status_code == 404

        response = client.patch(
            "/api/assignments/99999",
            headers=auth_headers,
            json={"title": "Update Non-existent"},
        )
        assert response.status_code == 404

    def test_patch_preserves_started_assignments(
        self, client, test_assignment, test_students, auth_headers, test_db
    ):
        """測試更新時保留已開始的作業"""
        # Create assignments with different statuses
        for i, student in enumerate(test_students[:3]):
            status = (
                AssignmentStatus.IN_PROGRESS if i == 0 else AssignmentStatus.NOT_STARTED
            )
            sa = StudentAssignment(
                assignment_id=test_assignment.id,
                student_id=student.id,
                classroom_id=test_assignment.classroom_id,
                title=test_assignment.title,
                instructions=test_assignment.description,
                due_date=test_assignment.due_date,
                status=status,
                assigned_at=datetime.now(timezone.utc),
                is_active=True,
            )
            test_db.add(sa)
        test_db.commit()

        # Update to only keep student 0 and add student 3
        new_student_ids = [test_students[0].id, test_students[3].id]
        response = client.patch(
            f"/api/assignments/{test_assignment.id}",
            headers=auth_headers,
            json={"student_ids": new_student_ids},
        )
        assert response.status_code == 200

        # Verify student 0 (IN_PROGRESS) is preserved
        sa = (
            test_db.query(StudentAssignment)
            .filter(
                StudentAssignment.assignment_id == test_assignment.id,
                StudentAssignment.student_id == test_students[0].id,
            )
            .first()
        )
        assert sa is not None
        assert sa.status == AssignmentStatus.IN_PROGRESS

        # Verify total count
        total = (
            test_db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == test_assignment.id)
            .count()
        )
        assert total == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
