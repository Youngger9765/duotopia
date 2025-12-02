"""
Test Suite for Single-Student Grading Mode (Status Filter Skip)

Issue: Teachers want to use "Apply AI Suggestions" in single-student grading mode
regardless of the student's current status (GRADED, IN_PROGRESS, etc.)

Solution: When exactly one student_id is provided, skip status filtering
to allow re-grading or applying AI suggestions to any student at any time.

Backend API: POST /api/teachers/assignments/{assignment_id}/batch-grade
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Assignment,
    Content,
    ContentItem,
    AssignmentContent,
    StudentAssignment,
    StudentItemProgress,
    AssignmentStatus,
    Program,
    Lesson,
)
from auth import get_password_hash, create_access_token


@pytest.fixture
def auth_teacher(shared_test_session: Session):
    """Create authenticated teacher"""
    teacher = Teacher(
        email="teacher_single@test.com",
        name="Single Mode Test Teacher",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(auth_teacher: Teacher):
    """Create auth headers"""
    access_token = create_access_token(
        data={"sub": str(auth_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def setup_test_env(shared_test_session: Session, auth_teacher: Teacher):
    """Setup test environment with classroom, assignment, and content"""
    # Create classroom
    classroom = Classroom(
        name="Single Student Mode Test Classroom",
        teacher_id=auth_teacher.id,
    )
    shared_test_session.add(classroom)
    shared_test_session.commit()
    shared_test_session.refresh(classroom)

    # Create assignment
    assignment = Assignment(
        title="Single Student Mode Test Assignment",
        classroom_id=classroom.id,
        teacher_id=auth_teacher.id,
        due_date=datetime.now(timezone.utc),
    )
    shared_test_session.add(assignment)
    shared_test_session.commit()
    shared_test_session.refresh(assignment)

    # Create Program and Lesson
    program = Program(
        name="Test Program",
        teacher_id=auth_teacher.id,
        classroom_id=classroom.id,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)

    lesson = Lesson(
        program_id=program.id,
        name="Test Lesson",
    )
    shared_test_session.add(lesson)
    shared_test_session.commit()
    shared_test_session.refresh(lesson)

    # Create content with 3 items
    content = Content(
        lesson_id=lesson.id,
        title="Test Content",
        type="reading_assessment",
    )
    shared_test_session.add(content)
    shared_test_session.commit()
    shared_test_session.refresh(content)

    # Link assignment to content
    ac = AssignmentContent(
        assignment_id=assignment.id,
        content_id=content.id,
        order_index=1,
    )
    shared_test_session.add(ac)
    shared_test_session.commit()

    # Create 3 content items
    items = []
    for i in range(3):
        item = ContentItem(
            content_id=content.id,
            order_index=i,
            text=f"Test sentence {i+1}",
            translation=f"測試句子 {i+1}",
        )
        shared_test_session.add(item)
        items.append(item)
    shared_test_session.commit()

    for item in items:
        shared_test_session.refresh(item)

    return {
        "teacher": auth_teacher,
        "classroom": classroom,
        "assignment": assignment,
        "content": content,
        "items": items,
    }


def create_student_with_status(
    db: Session,
    classroom: Classroom,
    assignment: Assignment,
    items: list[ContentItem],
    student_name: str,
    student_number: str,
    status: AssignmentStatus,
) -> tuple[Student, StudentAssignment]:
    """Helper: Create student with specific assignment status"""
    student = Student(
        email=f"{student_number}@single.test",
        name=student_name,
        student_number=student_number,
        password_hash=get_password_hash("password123"),
        birthdate=date(2010, 1, 1),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Add to classroom
    cs = ClassroomStudent(
        classroom_id=classroom.id,
        student_id=student.id,
    )
    db.add(cs)
    db.commit()

    # Create student assignment with specific status
    sa = StudentAssignment(
        student_id=student.id,
        assignment_id=assignment.id,
        classroom_id=classroom.id,
        title=assignment.title,
        status=status,
        submitted_at=datetime.now(timezone.utc)
        if status != AssignmentStatus.NOT_STARTED
        else None,
    )
    db.add(sa)
    db.commit()
    db.refresh(sa)

    # Add item progress with scores
    for item in items:
        progress = StudentItemProgress(
            student_assignment_id=sa.id,
            content_item_id=item.id,
            recording_url=f"https://example.com/recording_{item.id}.mp3",
            pronunciation_score=Decimal("85.0"),
            accuracy_score=Decimal("88.0"),
            fluency_score=Decimal("90.0"),
            completeness_score=Decimal("87.0"),
            ai_assessed_at=datetime.now(timezone.utc),
            status="SUBMITTED",
        )
        db.add(progress)
    db.commit()

    return student, sa


# ============================================================================
# TEST 1: Single-Student Mode with GRADED Status
# ============================================================================
def test_single_student_mode_graded_status(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Single-student mode should allow grading GRADED students

    Scenario:
    - Student has status GRADED (previously graded)
    - Teacher wants to apply AI suggestions again
    - Should succeed (not filtered by status)
    """
    data = setup_test_env

    student, sa = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Already Graded Student",
        "SS001",
        AssignmentStatus.GRADED,  # Already graded
    )

    # Call batch-grade API with single student_id
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student.id],  # Single student
        },
    )

    # Should succeed
    assert response.status_code == 200, f"API failed: {response.text}"
    result = response.json()

    # Verify student was processed
    assert result["total_students"] == 1
    assert result["processed"] == 1
    assert len(result["results"]) == 1

    student_result = result["results"][0]
    assert student_result["student_id"] == student.id
    assert student_result["student_name"] == "Already Graded Student"
    assert student_result["completed_items"] == 3
    assert student_result["missing_items"] == 0
    assert student_result["total_score"] is not None


# ============================================================================
# TEST 2: Single-Student Mode with IN_PROGRESS Status
# ============================================================================
def test_single_student_mode_in_progress_status(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Single-student mode should allow grading IN_PROGRESS students

    Scenario:
    - Student has status IN_PROGRESS (teacher is reviewing)
    - Teacher wants to apply AI suggestions
    - Should succeed
    """
    data = setup_test_env

    student, sa = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "In Progress Student",
        "SS002",
        AssignmentStatus.IN_PROGRESS,
    )

    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student.id],
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert result["processed"] == 1
    assert len(result["results"]) == 1
    assert result["results"][0]["student_id"] == student.id


# ============================================================================
# TEST 3: Single-Student Mode with RETURNED Status
# ============================================================================
def test_single_student_mode_returned_status(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Single-student mode should allow grading RETURNED students

    Scenario:
    - Student has status RETURNED (teacher returned for revision)
    - Teacher wants to re-apply AI suggestions
    - Should succeed
    """
    data = setup_test_env

    student, sa = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Returned Student",
        "SS003",
        AssignmentStatus.RETURNED,
    )

    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student.id],
        },
    )

    assert response.status_code == 200
    result = response.json()

    assert result["processed"] == 1
    assert result["results"][0]["student_id"] == student.id


# ============================================================================
# TEST 4: Batch Mode Still Filters by Status (SUBMITTED/RESUBMITTED only)
# ============================================================================
def test_batch_mode_filters_by_status(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Batch mode (no student_ids) should ONLY process SUBMITTED/RESUBMITTED

    Scenario:
    - Create 5 students with different statuses
    - Call batch-grade without student_ids
    - Should only process SUBMITTED and RESUBMITTED students
    """
    data = setup_test_env

    # Create students with different statuses
    students = []
    statuses = [
        AssignmentStatus.SUBMITTED,  # Should process
        AssignmentStatus.RESUBMITTED,  # Should process
        AssignmentStatus.GRADED,  # Should skip
        AssignmentStatus.IN_PROGRESS,  # Should skip
        AssignmentStatus.RETURNED,  # Should skip
    ]

    for i, status in enumerate(statuses):
        student, sa = create_student_with_status(
            shared_test_session,
            data["classroom"],
            data["assignment"],
            data["items"],
            f"Student {status.value}",
            f"SS10{i}",
            status,
        )
        students.append((student, sa, status))

    # Call batch-grade WITHOUT student_ids (batch mode)
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            # No student_ids - batch mode
        },
    )

    assert response.status_code == 200
    result = response.json()

    # Should only process SUBMITTED and RESUBMITTED (2 students)
    assert result["total_students"] == 2, f"Expected 2, got {result['total_students']}"
    assert result["processed"] == 2

    # Verify only SUBMITTED and RESUBMITTED were processed
    processed_names = {r["student_name"] for r in result["results"]}
    assert "Student SUBMITTED" in processed_names
    assert "Student RESUBMITTED" in processed_names
    assert "Student GRADED" not in processed_names
    assert "Student IN_PROGRESS" not in processed_names
    assert "Student RETURNED" not in processed_names


# ============================================================================
# TEST 5: Multi-Student Mode with Specific IDs (Still Filters by Status)
# ============================================================================
def test_multi_student_mode_filters_by_status(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Multi-student mode (multiple student_ids) should still filter by status

    Scenario:
    - Provide 3 student_ids
    - 1 is SUBMITTED, 2 are GRADED
    - Should only process the SUBMITTED student
    """
    data = setup_test_env

    # Create 3 students
    student1, sa1 = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Multi Student 1 SUBMITTED",
        "SS201",
        AssignmentStatus.SUBMITTED,
    )

    student2, sa2 = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Multi Student 2 GRADED",
        "SS202",
        AssignmentStatus.GRADED,
    )

    student3, sa3 = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Multi Student 3 GRADED",
        "SS203",
        AssignmentStatus.GRADED,
    )

    # Call with multiple student_ids
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student1.id, student2.id, student3.id],  # 3 students
        },
    )

    assert response.status_code == 200
    result = response.json()

    # Should only process student1 (SUBMITTED)
    assert result["total_students"] == 1
    assert result["processed"] == 1
    assert result["results"][0]["student_name"] == "Multi Student 1 SUBMITTED"


# ============================================================================
# TEST 6: Single-Student Mode vs Batch Mode Comparison
# ============================================================================
def test_single_student_vs_batch_mode_comparison(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Direct Comparison Test:
    - Create GRADED student
    - Batch mode: Should skip
    - Single-student mode: Should process
    """
    data = setup_test_env

    student, sa = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Comparison Student GRADED",
        "SS301",
        AssignmentStatus.GRADED,
    )

    # Test 1: Batch mode (should skip GRADED student)
    response_batch = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            # No student_ids
        },
    )

    assert response_batch.status_code == 200
    result_batch = response_batch.json()
    assert result_batch["total_students"] == 0, "Batch mode should skip GRADED student"

    # Test 2: Single-student mode (should process GRADED student)
    response_single = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student.id],  # Single student
        },
    )

    assert response_single.status_code == 200
    result_single = response_single.json()
    assert (
        result_single["total_students"] == 1
    ), "Single-student mode should process GRADED student"
    assert result_single["processed"] == 1
    assert result_single["results"][0]["student_id"] == student.id


# ============================================================================
# TEST 7: Verify Database Updates in Single-Student Mode
# ============================================================================
def test_single_student_mode_database_updates(
    test_client: TestClient,
    shared_test_session: Session,
    setup_test_env,
    auth_headers,
):
    """
    Test: Verify that single-student mode properly updates database

    Scenario:
    - GRADED student with existing score
    - Apply AI suggestions (re-grade)
    - Verify score and feedback are updated
    """
    data = setup_test_env

    student, sa = create_student_with_status(
        shared_test_session,
        data["classroom"],
        data["assignment"],
        data["items"],
        "Database Update Student",
        "SS401",
        AssignmentStatus.GRADED,
    )

    # Set initial score and feedback
    sa.score = Decimal("75.0")
    sa.feedback = "Old feedback"
    shared_test_session.commit()

    # Call single-student batch grade
    response = test_client.post(
        f"/api/teachers/assignments/{data['assignment'].id}/batch-grade",
        headers=auth_headers,
        json={
            "classroom_id": data["classroom"].id,
            "student_ids": [student.id],
        },
    )

    assert response.status_code == 200
    result = response.json()

    # Verify API response
    student_result = result["results"][0]
    new_score = student_result["total_score"]
    _ = student_result["feedback"]

    # Expected new score: (85 + 88 + 90 + 87) / 4 = 87.5
    expected_score = (85 + 88 + 90 + 87) / 4
    assert abs(new_score - expected_score) < 0.5

    # Verify database was updated
    shared_test_session.refresh(sa)
    assert sa.score is not None
    assert abs(float(sa.score) - expected_score) < 0.5
    assert sa.feedback != "Old feedback"
    assert sa.feedback is not None
    assert len(sa.feedback) > 0

    # Verify item comments were generated
    item_progress_list = (
        shared_test_session.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == sa.id)
        .all()
    )

    for item_progress in item_progress_list:
        assert item_progress.teacher_feedback is not None
        assert len(item_progress.teacher_feedback) > 0
