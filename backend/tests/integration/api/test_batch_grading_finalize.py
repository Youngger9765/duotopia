"""
Integration tests for batch grading finalization endpoint

This test suite covers the finalize-batch-grade endpoint which:
1. Marks students as GRADED or RETURNED based on teacher selection
2. Does NOT re-calculate scores (already done in batch-grade)
3. Only updates StudentAssignment status and timestamps

Backend API endpoint: POST /api/teachers/assignments/{assignment_id}/finalize-batch-grade
"""

import pytest
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
    AssignmentStatus,
    Program,
    Lesson,
)
from auth import get_password_hash, create_access_token


@pytest.fixture
def auth_teacher(shared_test_session: Session):
    """Create authenticated teacher for all tests"""
    teacher = Teacher(
        email="teacher@test.com",
        name="Test Teacher",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def other_teacher(shared_test_session: Session):
    """Create another teacher for unauthorized access tests"""
    teacher = Teacher(
        email="other@test.com",
        name="Other Teacher",
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
    """Create auth headers for API requests"""
    access_token = create_access_token(
        data={"sub": str(auth_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def other_auth_headers(other_teacher: Teacher):
    """Create auth headers for unauthorized tests"""
    access_token = create_access_token(
        data={"sub": str(other_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def setup_test_data(shared_test_session: Session, auth_teacher: Teacher):
    """Setup classroom, assignment, and students with SUBMITTED status"""
    # Create classroom
    classroom = Classroom(name="Test Classroom", teacher_id=auth_teacher.id)
    shared_test_session.add(classroom)
    shared_test_session.commit()

    # Create students
    students = []
    for i in range(5):
        student = Student(
            email=f"student{i}@test.com",
            name=f"Student {i}",
            password_hash=get_password_hash("password123"),
            birthdate=date(2010, 1, 1),  # Required field
            is_active=True,
            email_verified=True,
        )
        shared_test_session.add(student)
        shared_test_session.commit()

        # Add to classroom
        classroom_student = ClassroomStudent(
            classroom_id=classroom.id, student_id=student.id
        )
        shared_test_session.add(classroom_student)
        students.append(student)

    shared_test_session.commit()

    # Create program and lesson (required for Content)
    program = Program(
        name="Test Program", teacher_id=auth_teacher.id, classroom_id=classroom.id
    )
    shared_test_session.add(program)
    shared_test_session.commit()

    lesson = Lesson(program_id=program.id, name="Test Lesson")
    shared_test_session.add(lesson)
    shared_test_session.commit()

    # Create content with items
    content = Content(
        lesson_id=lesson.id, title="Test Content", type="reading_assessment"
    )
    shared_test_session.add(content)
    shared_test_session.commit()

    for i in range(3):
        item = ContentItem(
            content_id=content.id,
            order_index=i,
            text=f"Test item {i + 1}",
            translation=f"測試 {i + 1}",
        )
        shared_test_session.add(item)

    shared_test_session.commit()

    # Create assignment
    assignment = Assignment(
        title="Test Assignment",
        classroom_id=classroom.id,
        teacher_id=auth_teacher.id,
        due_date=datetime.now(timezone.utc),
    )
    shared_test_session.add(assignment)
    shared_test_session.commit()

    # Link content to assignment
    assignment_content = AssignmentContent(
        assignment_id=assignment.id, content_id=content.id
    )
    shared_test_session.add(assignment_content)
    shared_test_session.commit()

    # Create student assignments with SUBMITTED status
    for student in students:
        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title=assignment.title,  # Required field
            due_date=assignment.due_date,  # Required field
            status=AssignmentStatus.SUBMITTED,
            score=85.0,  # Pre-graded score
        )
        shared_test_session.add(sa)

    shared_test_session.commit()

    return {
        "teacher": auth_teacher,
        "classroom": classroom,
        "assignment": assignment,
        "students": students,
        "content": content,
    }


class TestFinalizeBatchGrade:
    """Test finalize-batch-grade endpoint"""

    def test_finalize_no_returns(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: No students returned - all remain SUBMITTED"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]
        students = setup_test_data["students"]

        # Finalize with all students pending (empty decisions)
        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["returned_count"] == 0
        assert data["graded_count"] == 0
        assert data["unchanged_count"] == 5
        assert data["total_count"] == 5

        # Verify database status - all should still be SUBMITTED (no change)
        for student in students:
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=student.id, assignment_id=assignment.id)
                .first()
            )
            assert sa.status == AssignmentStatus.SUBMITTED
            assert sa.graded_at is None

    def test_finalize_partial_returns(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: Some students returned, others unchanged"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]
        students = setup_test_data["students"]

        # Return students 0 and 2 for correction, grade student 1, leave 3 and 4 pending
        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {
                    str(students[0].id): "RETURNED",
                    str(students[1].id): "GRADED",
                    str(students[2].id): "RETURNED",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["returned_count"] == 2  # Students 0, 2
        assert data["graded_count"] == 1  # Student 1
        assert data["unchanged_count"] == 2  # Students 3, 4
        assert data["total_count"] == 5

        # Verify database status - returned students
        for idx in [0, 2]:
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=students[idx].id, assignment_id=assignment.id)
                .first()
            )
            assert sa.status == AssignmentStatus.RETURNED
            assert sa.returned_at is not None

        # Verify database status - graded student
        sa = (
            shared_test_session.query(StudentAssignment)
            .filter_by(student_id=students[1].id, assignment_id=assignment.id)
            .first()
        )
        assert sa.status == AssignmentStatus.GRADED

        # Verify database status - unchanged students remain SUBMITTED
        for idx in [3, 4]:
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=students[idx].id, assignment_id=assignment.id)
                .first()
            )
            assert sa.status == AssignmentStatus.SUBMITTED
            assert sa.graded_at is None

    def test_finalize_all_returned(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: All students returned for correction"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]
        students = setup_test_data["students"]

        # Return all students
        decisions = {str(student.id): "RETURNED" for student in students}

        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": decisions,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["returned_count"] == 5
        assert data["graded_count"] == 0
        assert data["unchanged_count"] == 0
        assert data["total_count"] == 5

        # Verify all are returned
        for student in students:
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=student.id, assignment_id=assignment.id)
                .first()
            )
            assert sa.status == AssignmentStatus.RETURNED
            assert sa.returned_at is not None

    def test_finalize_unauthorized_teacher(
        self, test_client: TestClient, setup_test_data, other_auth_headers
    ):
        """Test: Unauthorized teacher cannot finalize"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]

        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {},
            },
            headers=other_auth_headers,
        )

        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]

    def test_finalize_assignment_not_found(
        self, test_client: TestClient, setup_test_data, auth_headers
    ):
        """Test: Assignment not found"""
        classroom = setup_test_data["classroom"]

        response = test_client.post(
            "/api/teachers/assignments/99999/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "Assignment not found" in response.json()["detail"]

    def test_finalize_no_students_submitted(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: No students have SUBMITTED status"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]

        # Change all students to GRADED status
        shared_test_session.query(StudentAssignment).filter_by(
            assignment_id=assignment.id
        ).update({StudentAssignment.status: AssignmentStatus.GRADED})
        shared_test_session.commit()

        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["returned_count"] == 0
        assert data["graded_count"] == 0
        assert data["unchanged_count"] == 0
        assert data["total_count"] == 0

    def test_finalize_with_resubmitted_status(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: Finalize works with RESUBMITTED status"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]
        students = setup_test_data["students"]

        # Change first 2 students to RESUBMITTED
        for i in range(2):
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=students[i].id, assignment_id=assignment.id)
                .first()
            )
            sa.status = AssignmentStatus.RESUBMITTED
        shared_test_session.commit()

        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["returned_count"] == 0
        assert data["graded_count"] == 0
        assert data["unchanged_count"] == 5  # All 5 remain unchanged
        assert data["total_count"] == 5

        # Verify: 2 students remain RESUBMITTED, 3 remain SUBMITTED
        resubmitted_count = 0
        submitted_count = 0
        for student in students:
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=student.id, assignment_id=assignment.id)
                .first()
            )
            if sa.status == AssignmentStatus.RESUBMITTED:
                resubmitted_count += 1
            elif sa.status == AssignmentStatus.SUBMITTED:
                submitted_count += 1

        assert resubmitted_count == 2
        assert submitted_count == 3

    def test_finalize_preserves_scores(
        self,
        test_client: TestClient,
        shared_test_session: Session,
        setup_test_data,
        auth_headers,
    ):
        """Test: Finalize does NOT modify existing scores"""
        assignment = setup_test_data["assignment"]
        classroom = setup_test_data["classroom"]
        students = setup_test_data["students"]

        # Set different scores for each student
        for idx, student in enumerate(students):
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=student.id, assignment_id=assignment.id)
                .first()
            )
            sa.score = 70.0 + idx * 5
        shared_test_session.commit()

        # Return student 0, grade student 1, leave others unchanged
        response = test_client.post(
            f"/api/teachers/assignments/{assignment.id}/finalize-batch-grade",
            json={
                "classroom_id": classroom.id,
                "teacher_decisions": {
                    str(students[0].id): "RETURNED",
                    str(students[1].id): "GRADED",
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify scores are preserved for all students
        for idx, student in enumerate(students):
            sa = (
                shared_test_session.query(StudentAssignment)
                .filter_by(student_id=student.id, assignment_id=assignment.id)
                .first()
            )
            assert sa.score == 70.0 + idx * 5  # Score unchanged
            # Student 0 should be RETURNED, student 1 should be GRADED, others remain SUBMITTED
            if idx == 0:
                assert sa.status == AssignmentStatus.RETURNED
            elif idx == 1:
                assert sa.status == AssignmentStatus.GRADED
            else:
                assert sa.status == AssignmentStatus.SUBMITTED
