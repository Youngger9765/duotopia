"""
測試作業時間戳記功能
特別測試 returned_at 和 resubmitted_at 欄位
"""

import pytest
from datetime import datetime, timedelta  # noqa: F401
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from main import app
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
    from database import Base, engine

    Base.metadata.create_all(bind=engine)
    db = Session(bind=engine)
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_teacher(test_db):
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
def test_classroom(test_db, test_teacher):
    """Create test classroom"""
    classroom = Classroom(
        name="Test Class",
        teacher_id=test_teacher.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_db.add(classroom)
    test_db.commit()
    test_db.refresh(classroom)
    return classroom


@pytest.fixture
def test_students(test_db, test_classroom):
    """Create test students"""
    students = []
    for i in range(3):
        student = Student(
            name=f"Student {i+1}",
            email=f"student{i+1}@example.com",
            password_hash=get_password_hash("password"),
            birthdate=datetime.now().date() - timedelta(days=4000),
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
def test_content(test_db, test_teacher, test_classroom):
    """Create test content"""
    # Create program and lesson first
    program = Program(
        name="Test Program",
        teacher_id=test_teacher.id,
        classroom_id=test_classroom.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_db.add(program)
    test_db.flush()

    lesson = Lesson(
        program_id=program.id, name="Test Lesson", order_index=1, is_active=True
    )
    test_db.add(lesson)
    test_db.flush()

    content = Content(
        lesson_id=lesson.id,
        type=ContentType.READING_ASSESSMENT,
        title="Test Content",
        order_index=1,
        is_active=True,
        items=[{"text": "Hello", "translation": "你好"}],
    )
    test_db.add(content)
    test_db.commit()
    test_db.refresh(content)
    return content


@pytest.fixture
def test_assignment(test_db, test_teacher, test_classroom, test_content):
    """Create test assignment"""
    assignment = Assignment(
        title="Test Assignment",
        description="Test Description",
        classroom_id=test_classroom.id,
        teacher_id=test_teacher.id,
        due_date=datetime.now() + timedelta(days=7),
        is_active=True,
    )
    test_db.add(assignment)
    test_db.flush()

    # Link content
    assignment_content = AssignmentContent(
        assignment_id=assignment.id, content_id=test_content.id, order_index=1
    )
    test_db.add(assignment_content)
    test_db.commit()
    test_db.refresh(assignment)
    return assignment


@pytest.fixture
def auth_headers(test_teacher):
    """Get auth headers for teacher"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": test_teacher.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_assignment_timestamps(test_db, test_assignment, test_students, auth_headers):
    """Test assignment timestamp fields"""

    # Create different status scenarios
    student1, student2, student3 = test_students

    # Student 1: RETURNED status
    sa1 = StudentAssignment(
        assignment_id=test_assignment.id,
        student_id=student1.id,
        classroom_id=test_assignment.classroom_id,
        title=test_assignment.title,
        instructions=test_assignment.description,
        due_date=test_assignment.due_date,
        status=AssignmentStatus.RETURNED,
        score=65,
        feedback="需要重新錄製",
        started_at=datetime.now() - timedelta(days=3),
        submitted_at=datetime.now() - timedelta(days=2),
        graded_at=datetime.now() - timedelta(days=1),
        returned_at=datetime.now() - timedelta(days=1),  # 關鍵：設置 returned_at
        is_active=True,
    )
    test_db.add(sa1)

    # Student 2: RESUBMITTED status
    sa2 = StudentAssignment(
        assignment_id=test_assignment.id,
        student_id=student2.id,
        classroom_id=test_assignment.classroom_id,
        title=test_assignment.title,
        instructions=test_assignment.description,
        due_date=test_assignment.due_date,
        status=AssignmentStatus.RESUBMITTED,
        started_at=datetime.now() - timedelta(days=4),
        submitted_at=datetime.now() - timedelta(days=3),
        graded_at=datetime.now() - timedelta(days=2),
        returned_at=datetime.now() - timedelta(days=2),  # 被退回
        resubmitted_at=datetime.now() - timedelta(hours=4),  # 重新提交
        is_active=True,
    )
    test_db.add(sa2)

    # Student 3: GRADED after resubmission
    sa3 = StudentAssignment(
        assignment_id=test_assignment.id,
        student_id=student3.id,
        classroom_id=test_assignment.classroom_id,
        title=test_assignment.title,
        instructions=test_assignment.description,
        due_date=test_assignment.due_date,
        status=AssignmentStatus.GRADED,
        score=88,
        feedback="訂正後表現很好",
        started_at=datetime.now() - timedelta(days=5),
        submitted_at=datetime.now() - timedelta(days=4),
        returned_at=datetime.now() - timedelta(days=3),  # 被退回
        resubmitted_at=datetime.now() - timedelta(days=2),  # 重新提交
        graded_at=datetime.now() - timedelta(days=1),  # 最終批改
        is_active=True,
    )
    test_db.add(sa3)
    test_db.commit()

    # Test API endpoint
    response = client.get(
        f"/api/assignments/{test_assignment.id}/progress", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Check each student's timestamps
    student_map = {item["student_id"]: item for item in data}

    # Student 1: RETURNED
    s1_data = student_map[student1.id]
    assert s1_data["status"] == "RETURNED"
    assert s1_data["timestamps"]["returned_at"] is not None
    assert s1_data["timestamps"]["resubmitted_at"] is None
    assert s1_data["score"] == 65

    # Student 2: RESUBMITTED
    s2_data = student_map[student2.id]
    assert s2_data["status"] == "RESUBMITTED"
    assert s2_data["timestamps"]["returned_at"] is not None
    assert s2_data["timestamps"]["resubmitted_at"] is not None
    # Verify resubmitted_at > returned_at
    returned_time = datetime.fromisoformat(
        s2_data["timestamps"]["returned_at"].replace("+00:00", "")
    )
    resubmitted_time = datetime.fromisoformat(
        s2_data["timestamps"]["resubmitted_at"].replace("+00:00", "")
    )
    assert resubmitted_time > returned_time

    # Student 3: GRADED (after resubmission)
    s3_data = student_map[student3.id]
    assert s3_data["status"] == "GRADED"
    assert s3_data["timestamps"]["returned_at"] is not None
    assert s3_data["timestamps"]["resubmitted_at"] is not None
    assert s3_data["timestamps"]["graded_at"] is not None
    assert s3_data["score"] == 88

    # Verify the progression order
    returned_time = datetime.fromisoformat(
        s3_data["timestamps"]["returned_at"].replace("+00:00", "")
    )
    resubmitted_time = datetime.fromisoformat(
        s3_data["timestamps"]["resubmitted_at"].replace("+00:00", "")
    )
    graded_time = datetime.fromisoformat(
        s3_data["timestamps"]["graded_at"].replace("+00:00", "")
    )
    assert resubmitted_time > returned_time
    assert graded_time > resubmitted_time


def test_status_progression_logic(test_db, test_assignment, test_students):
    """Test the logical progression of assignment statuses"""

    student = test_students[0]

    # Start with NOT_STARTED
    sa = StudentAssignment(
        assignment_id=test_assignment.id,
        student_id=student.id,
        classroom_id=test_assignment.classroom_id,
        title=test_assignment.title,
        instructions=test_assignment.description,
        due_date=test_assignment.due_date,
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    test_db.add(sa)
    test_db.commit()

    # Progress to IN_PROGRESS
    sa.status = AssignmentStatus.IN_PROGRESS
    sa.started_at = datetime.now()
    test_db.commit()

    # Submit
    sa.status = AssignmentStatus.SUBMITTED
    sa.submitted_at = datetime.now()
    test_db.commit()

    # Teacher returns for revision
    sa.status = AssignmentStatus.RETURNED
    sa.graded_at = datetime.now()
    sa.returned_at = datetime.now()
    sa.score = 70
    sa.feedback = "需要修正"
    test_db.commit()

    # Verify RETURNED state
    assert sa.returned_at is not None
    assert sa.resubmitted_at is None

    # Student resubmits
    sa.status = AssignmentStatus.RESUBMITTED
    sa.resubmitted_at = datetime.now()
    test_db.commit()

    # Verify RESUBMITTED state
    assert sa.returned_at is not None
    assert sa.resubmitted_at is not None
    assert sa.resubmitted_at > sa.returned_at

    # Final grading
    sa.status = AssignmentStatus.GRADED
    sa.graded_at = datetime.now()
    sa.score = 85
    sa.feedback = "改進良好"
    test_db.commit()

    # Verify final state
    assert sa.status == AssignmentStatus.GRADED
    assert sa.returned_at is not None
    assert sa.resubmitted_at is not None
    assert sa.graded_at > sa.resubmitted_at


def test_teacher_returns_after_resubmission(test_db, test_assignment, test_students):
    """Test when teacher returns assignment again after resubmission"""

    student = test_students[0]

    # Create assignment in RESUBMITTED state
    sa = StudentAssignment(
        assignment_id=test_assignment.id,
        student_id=student.id,
        classroom_id=test_assignment.classroom_id,
        title=test_assignment.title,
        instructions=test_assignment.description,
        due_date=test_assignment.due_date,
        status=AssignmentStatus.RESUBMITTED,
        started_at=datetime.now() - timedelta(days=4),
        submitted_at=datetime.now() - timedelta(days=3),
        returned_at=datetime.now() - timedelta(days=2),
        resubmitted_at=datetime.now() - timedelta(days=1),
        is_active=True,
    )
    test_db.add(sa)
    test_db.commit()

    # Teacher returns it again
    sa.status = AssignmentStatus.RETURNED
    sa.returned_at = datetime.now()
    sa.resubmitted_at = None  # Clear resubmitted_at for new round
    sa.score = 75
    sa.feedback = "還需要再修正"
    test_db.commit()

    # Verify state
    assert sa.status == AssignmentStatus.RETURNED
    assert sa.returned_at is not None
    assert sa.resubmitted_at is None  # Should be cleared

    # Student resubmits again
    sa.status = AssignmentStatus.RESUBMITTED
    sa.resubmitted_at = datetime.now()
    test_db.commit()

    # Verify new resubmission
    assert sa.resubmitted_at is not None
    assert sa.resubmitted_at > sa.returned_at
