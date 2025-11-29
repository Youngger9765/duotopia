"""
Integration tests for Issue #34: Assignment Start Date
Tests that assignments with future start_date don't appear to students until that date
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestAssignmentStartDate:
    """Test assignment start_date functionality"""

    def test_create_assignment_with_future_start_date(
        self, client: TestClient, db: Session, teacher_token: str, classroom_id: int, content_id: int
    ):
        """
        Issue #34: Test creating assignment with future start_date
        Verify that assigned_at is set to start_date, not current time
        """
        # Arrange: Set start_date to 7 days in the future
        future_date = datetime.now(timezone.utc) + timedelta(days=7)

        # Act: Create assignment with future start_date
        response = client.post(
            "/api/teachers/assignments/create",
            json={
                "title": "Future Assignment",
                "description": "This assignment starts next week",
                "classroom_id": classroom_id,
                "content_ids": [content_id],
                "due_date": (future_date + timedelta(days=7)).isoformat(),
                "start_date": future_date.isoformat(),  # Key field
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        # Assert: Assignment created successfully
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assignment_id = data["assignment_id"]

        # Verify: assigned_at matches start_date in database
        from models import StudentAssignment
        student_assignment = db.query(StudentAssignment).filter(
            StudentAssignment.assignment_id == assignment_id
        ).first()

        assert student_assignment is not None
        assert student_assignment.assigned_at is not None

        # Allow 1 second tolerance for datetime comparison
        time_diff = abs((student_assignment.assigned_at - future_date).total_seconds())
        assert time_diff < 1, f"Expected assigned_at to be {future_date}, got {student_assignment.assigned_at}"

    def test_create_assignment_without_start_date_uses_current_time(
        self, client: TestClient, db: Session, teacher_token: str, classroom_id: int, content_id: int
    ):
        """
        Test backward compatibility: If start_date is not provided,
        assigned_at should default to current time
        """
        # Arrange
        before_create = datetime.now(timezone.utc)

        # Act: Create assignment WITHOUT start_date
        response = client.post(
            "/api/teachers/assignments/create",
            json={
                "title": "Immediate Assignment",
                "description": "This assignment starts now",
                "classroom_id": classroom_id,
                "content_ids": [content_id],
                # No start_date provided
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        after_create = datetime.now(timezone.utc)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assignment_id = data["assignment_id"]

        # Verify: assigned_at is between before_create and after_create
        from models import StudentAssignment
        student_assignment = db.query(StudentAssignment).filter(
            StudentAssignment.assignment_id == assignment_id
        ).first()

        assert student_assignment is not None
        assert student_assignment.assigned_at is not None
        assert before_create <= student_assignment.assigned_at <= after_create

    def test_student_cannot_see_future_assignment(
        self, client: TestClient, db: Session, teacher_token: str, student_token: str,
        classroom_id: int, content_id: int
    ):
        """
        Issue #34 Core Test: Students should NOT see assignments with future start_date
        This test relies on PR #35's filtering logic in /api/students/assignments
        """
        # Arrange: Create assignment with future start_date
        future_date = datetime.now(timezone.utc) + timedelta(days=7)

        response = client.post(
            "/api/teachers/assignments/create",
            json={
                "title": "Future Assignment",
                "classroom_id": classroom_id,
                "content_ids": [content_id],
                "start_date": future_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200
        future_assignment_id = response.json()["assignment_id"]

        # Act: Student queries their assignments
        response = client.get(
            "/api/students/assignments",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Assert: Future assignment should NOT be in the list
        assert response.status_code == 200
        assignments = response.json()
        assignment_ids = [a["id"] for a in assignments]

        assert future_assignment_id not in assignment_ids, \
            "Student should NOT see assignment with future start_date"

    def test_student_can_see_past_assignment(
        self, client: TestClient, db: Session, teacher_token: str, student_token: str,
        classroom_id: int, content_id: int
    ):
        """
        Test that students CAN see assignments with past start_date
        """
        # Arrange: Create assignment with past start_date
        past_date = datetime.now(timezone.utc) - timedelta(days=7)

        response = client.post(
            "/api/teachers/assignments/create",
            json={
                "title": "Past Assignment",
                "classroom_id": classroom_id,
                "content_ids": [content_id],
                "start_date": past_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200
        past_assignment_id = response.json()["assignment_id"]

        # Act: Student queries their assignments
        response = client.get(
            "/api/students/assignments",
            headers={"Authorization": f"Bearer {student_token}"},
        )

        # Assert: Past assignment SHOULD be in the list
        assert response.status_code == 200
        assignments = response.json()
        assignment_ids = [a["id"] for a in assignments]

        assert past_assignment_id in assignment_ids, \
            "Student SHOULD see assignment with past start_date"

    def test_patch_assignment_with_start_date(
        self, client: TestClient, db: Session, teacher_token: str, classroom_id: int,
        content_id: int, student_id: int
    ):
        """
        Test updating assignment (PATCH) with start_date when adding new students
        """
        # Arrange: Create base assignment
        response = client.post(
            "/api/teachers/assignments/create",
            json={
                "title": "Base Assignment",
                "classroom_id": classroom_id,
                "content_ids": [content_id],
                "student_ids": [],  # No students initially
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert response.status_code == 200
        assignment_id = response.json()["assignment_id"]

        # Act: Add students with future start_date via PATCH
        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        response = client.patch(
            f"/api/teachers/assignments/{assignment_id}",
            json={
                "student_ids": [student_id],
                "start_date": future_date.isoformat(),
            },
            headers={"Authorization": f"Bearer {teacher_token}"},
        )

        # Assert
        assert response.status_code == 200

        # Verify: New student assignment has correct assigned_at
        from models import StudentAssignment
        student_assignment = db.query(StudentAssignment).filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        ).first()

        assert student_assignment is not None
        time_diff = abs((student_assignment.assigned_at - future_date).total_seconds())
        assert time_diff < 1, f"Expected assigned_at to be {future_date}"
