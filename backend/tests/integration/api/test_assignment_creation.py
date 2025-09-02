"""
測試作業創建功能 (Phase 1)
測試教師為學生或整個班級派發作業的功能
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from database import get_db
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentType,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    AssignmentStatus,
    ProgramLevel,
)
from auth import get_password_hash


client = TestClient(app)


@pytest.fixture
def test_db(tmpdir):
    """Create a test database"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base

    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{tmpdir}/test.db"
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

    db = TestingSessionLocal()
    yield db
    db.close()

    app.dependency_overrides.clear()


@pytest.fixture
def test_teacher(test_db: Session):
    """Create test teacher"""
    teacher = Teacher(
        email="test_teacher@example.com",
        password_hash=get_password_hash("password123"),
        name="Test Teacher",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def test_classroom(test_db: Session, test_teacher):
    """Create test classroom"""
    classroom = Classroom(
        name=f"作業測試班級_{datetime.now().strftime('%H%M%S')}",
        description="用於測試作業功能",
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
    for i in range(3):
        student = Student(
            name=f"作業測試學生{i+1}",
            email=f"assignment_student{i+1}_{int(datetime.now().timestamp())}@test.local",
            password_hash=get_password_hash("password"),
            birthdate=datetime(2012, 1, 1).date(),
            is_active=True,
        )
        test_db.add(student)
        test_db.flush()

        # Add to classroom
        enrollment = ClassroomStudent(
            classroom_id=test_classroom.id, student_id=student.id, is_active=True
        )
        test_db.add(enrollment)
        students.append(student)

    test_db.commit()
    return students


@pytest.fixture
def test_content(test_db: Session, test_teacher, test_classroom):
    """Create test content"""
    # Create program first
    program = Program(
        name=f"作業測試課程_{datetime.now().strftime('%H%M%S')}",
        teacher_id=test_teacher.id,
        classroom_id=test_classroom.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_db.add(program)
    test_db.flush()

    # Create lesson
    lesson = Lesson(
        program_id=program.id,
        name="Unit 1 - Test Assignment",
        description="用於測試作業的課程單元",
        order_index=1,
        is_active=True,
    )
    test_db.add(lesson)
    test_db.flush()

    # Create content - 朗讀評測
    content = Content(
        lesson_id=lesson.id,
        type=ContentType.READING_ASSESSMENT,
        title="Reading Practice 1",
        order_index=1,
        is_active=True,
        items=[
            {"text": "Hello, my name is John.", "order": 1},
            {"text": "I am a student.", "order": 2},
            {"text": "Nice to meet you.", "order": 3},
        ],
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


@pytest.fixture
def auth_headers(test_teacher):
    """Get auth headers for teacher"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": test_teacher.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestAssignmentCreation:
    """作業創建功能測試"""

    def test_create_assignment_for_individual_student(
        self, test_db, test_classroom, test_students, test_content, auth_headers
    ):
        """測試為個別學生創建作業"""
        student = test_students[0]

        # Create assignment using the new endpoint
        assignment_data = {
            "title": "個人朗讀作業 - Reading Practice 1",
            "description": "請仔細朗讀每一句話，注意發音的準確性。",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": [student.id],
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert "id" in result
        assert result["title"] == assignment_data["title"]

        # Verify student assignment was created
        student_assignments = (
            test_db.query(StudentAssignment)
            .filter_by(student_id=student.id, assignment_id=result["id"])
            .all()
        )
        assert len(student_assignments) == 1

    def test_create_assignment_for_multiple_students(
        self, test_db, test_classroom, test_students, test_content, auth_headers
    ):
        """測試為多個學生創建作業"""
        student_ids = [s.id for s in test_students[:2]]  # 選擇前兩個學生

        assignment_data = {
            "title": "多人朗讀作業 - Reading Practice 1",
            "description": "這是給多位學生的朗讀練習作業。",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": student_ids,
            "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
        }

        response = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Verify student assignments were created for both students
        student_assignments = (
            test_db.query(StudentAssignment).filter_by(assignment_id=result["id"]).all()
        )
        assert len(student_assignments) == 2
        assert set(sa.student_id for sa in student_assignments) == set(student_ids)

    def test_create_assignment_for_entire_classroom(
        self, test_db, test_classroom, test_students, test_content, auth_headers
    ):
        """測試為整個班級創建作業"""
        assignment_data = {
            "title": "班級朗讀作業 - Reading Practice 1",
            "description": "這是給整個班級的朗讀練習作業，每位同學都要完成。",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": [],  # 空陣列表示全班
            "due_date": (datetime.now() + timedelta(days=10)).isoformat(),
        }

        response = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        assert response.status_code == 200
        result = response.json()

        # Verify student assignments were created for all students
        student_assignments = (
            test_db.query(StudentAssignment).filter_by(assignment_id=result["id"]).all()
        )
        assert len(student_assignments) == len(test_students)  # Should be 3
        student_ids_in_assignments = {sa.student_id for sa in student_assignments}
        expected_student_ids = {s.id for s in test_students}
        assert student_ids_in_assignments == expected_student_ids

    def test_create_assignment_validation_errors(
        self, test_classroom, test_students, test_content, auth_headers
    ):
        """測試作業創建的驗證錯誤"""

        # Test 1: Missing required field (classroom_id)
        invalid_data = {
            "title": "無效作業",
            "description": "測試無效資料",
            "content_ids": [test_content.id],
            "student_ids": [],
        }

        response = client.post(
            "/api/assignments", json=invalid_data, headers=auth_headers
        )

        assert response.status_code == 422, "Should return validation error"

        # Test 2: Non-existent content ID
        invalid_data = {
            "title": "無效內容作業",
            "description": "測試不存在的內容",
            "classroom_id": test_classroom.id,
            "content_ids": [99999],
            "student_ids": [test_students[0].id],
        }

        response = client.post(
            "/api/assignments", json=invalid_data, headers=auth_headers
        )

        assert response.status_code in [
            400,
            404,
        ], "Should return content not found error"

        # Test 3: Non-existent student ID
        invalid_data = {
            "title": "無效學生作業",
            "description": "測試不存在的學生",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": [99999],
        }

        response = client.post(
            "/api/assignments", json=invalid_data, headers=auth_headers
        )

        assert (
            response.status_code == 400
        ), "Should return student not in classroom error"

    def test_create_assignment_with_past_due_date(
        self, test_classroom, test_students, test_content, auth_headers
    ):
        """測試使用過去日期作為截止日期"""
        assignment_data = {
            "title": "過期作業測試",
            "description": "測試過期日期處理",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": [test_students[0].id],
            "due_date": (datetime.now() - timedelta(days=1)).isoformat(),  # Yesterday
        }

        response = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        # API may allow past due dates (business requirement)
        # or reject them (validation)
        assert response.status_code in [
            200,
            422,
        ], "API behavior: allow or reject past dates"

    def test_duplicate_assignment_handling(
        self, test_db, test_classroom, test_students, test_content, auth_headers
    ):
        """測試重複作業的處理"""
        student = test_students[0]

        assignment_data = {
            "title": "重複作業測試",
            "description": "測試重複作業處理",
            "classroom_id": test_classroom.id,
            "content_ids": [test_content.id],
            "student_ids": [student.id],
            "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        }

        # First creation - should succeed
        response1 = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        assert response1.status_code == 200, "First creation should succeed"
        assignment_id = response1.json()["id"]

        # Second creation with same data - should create a new assignment
        # (different from the original script's expectation)
        response2 = client.post(
            "/api/assignments", json=assignment_data, headers=auth_headers
        )

        assert response2.status_code == 200, "Second creation should also succeed"
        assignment_id2 = response2.json()["id"]

        # They should be different assignments
        assert assignment_id != assignment_id2, "Should create separate assignments"
