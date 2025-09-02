"""
Unit tests for Assignment system schemas
Tests Pydantic schemas validation and serialization
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from schemas import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    StudentAssignmentCreate,
    StudentAssignmentUpdate,
    StudentContentProgressCreate,
    StudentContentProgressUpdate,
    AssignmentWithDetails,
    StudentAssignmentWithProgress,
    StudentAssignmentResponse,
    StudentContentProgressResponse,
    AssignmentStatusEnum,
)


class TestAssignmentCreateSchema:
    def test_valid_assignment_create(self):
        """Test creating a valid assignment schema"""
        data = {
            "title": "Test Assignment",
            "description": "Test description",
            "classroom_id": 1,
            "content_ids": [1, 2, 3],
            "student_ids": [1, 2],
            "due_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        assignment = AssignmentCreate(**data)

        assert assignment.title == "Test Assignment"
        assert assignment.description == "Test description"
        assert len(assignment.content_ids) == 3
        assert len(assignment.student_ids) == 2

    def test_assignment_create_minimal(self):
        """Test creating assignment with minimal required fields"""
        data = {
            "title": "Minimal Assignment",
            "classroom_id": 1,
            "content_ids": [1],
            "student_ids": [],
        }
        assignment = AssignmentCreate(**data)

        assert assignment.title == "Minimal Assignment"
        assert assignment.description is None
        assert assignment.due_date is None
        assert len(assignment.student_ids) == 0

    def test_assignment_create_validation_errors(self):
        """Test validation errors for invalid data"""
        # Missing required fields
        with pytest.raises(ValidationError) as exc_info:
            AssignmentCreate(title="Test")
        assert "classroom_id" in str(exc_info.value)

        # Empty content_ids
        with pytest.raises(ValidationError) as exc_info:
            AssignmentCreate(
                title="Test", classroom_id=1, content_ids=[], student_ids=[]
            )
        assert "content_ids" in str(exc_info.value)

    def test_assignment_create_type_validation(self):
        """Test type validation for fields"""
        # Invalid classroom_id type
        with pytest.raises(ValidationError):
            AssignmentCreate(
                title="Test", classroom_id="not_an_int", content_ids=[1], student_ids=[]
            )

        # Invalid content_ids type
        with pytest.raises(ValidationError):
            AssignmentCreate(
                title="Test", classroom_id=1, content_ids="not_a_list", student_ids=[]
            )


class TestAssignmentUpdateSchema:
    def test_valid_assignment_update(self):
        """Test updating assignment with valid data"""
        data = {
            "title": "Updated Assignment",
            "description": "Updated description",
            "content_ids": [4, 5, 6],
            "student_ids": [3, 4],
            "due_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
        }
        update = AssignmentUpdate(**data)

        assert update.title == "Updated Assignment"
        assert update.description == "Updated description"
        assert len(update.content_ids) == 3

    def test_assignment_update_partial(self):
        """Test partial update with only some fields"""
        data = {"title": "New Title Only"}
        update = AssignmentUpdate(**data)

        assert update.title == "New Title Only"
        assert update.description is None
        assert update.content_ids is None
        assert update.student_ids is None

    def test_assignment_update_empty(self):
        """Test update with no fields (should be valid)"""
        update = AssignmentUpdate()

        assert update.title is None
        assert update.description is None
        assert update.content_ids is None


class TestAssignmentResponseSchema:
    def test_assignment_response_serialization(self):
        """Test serialization of assignment response"""
        data = {
            "id": 1,
            "title": "Test Assignment",
            "description": "Test description",
            "classroom_id": 1,
            "teacher_id": 1,
            "due_date": datetime.utcnow() + timedelta(days=7),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        response = AssignmentResponse(**data)

        assert response.id == 1
        assert response.title == "Test Assignment"
        assert response.is_active is True

        # Test JSON serialization
        json_data = response.model_dump()
        assert json_data["id"] == 1
        assert json_data["title"] == "Test Assignment"

    def test_assignment_response_with_relations(self):
        """Test response with nested relationships"""
        data = {
            "id": 1,
            "title": "Test Assignment",
            "classroom_id": 1,
            "teacher_id": 1,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "contents": [
                {"id": 1, "title": "Content 1"},
                {"id": 2, "title": "Content 2"},
            ],
            "student_assignments": [
                {"id": 1, "student_id": 1, "status": "NOT_STARTED"},
                {"id": 2, "student_id": 2, "status": "IN_PROGRESS"},
            ],
        }
        response = AssignmentWithDetails(**data)

        assert len(response.contents) == 2
        assert len(response.student_assignments) == 2
        assert response.contents[0]["title"] == "Content 1"


class TestStudentAssignmentSchemas:
    def test_student_assignment_create(self):
        """Test creating student assignment schema"""
        data = {
            "assignment_id": 1,
            "student_id": 1,
            "classroom_id": 1,
            "title": "Student Assignment",
            "status": "NOT_STARTED",
        }
        sa = StudentAssignmentCreate(**data)

        assert sa.assignment_id == 1
        assert sa.student_id == 1
        assert sa.status == "NOT_STARTED"

    def test_student_assignment_update(self):
        """Test updating student assignment"""
        data = {"status": "IN_PROGRESS", "score": 85.5, "feedback": "Good work!"}
        update = StudentAssignmentUpdate(**data)

        assert update.status == "IN_PROGRESS"
        assert update.score == 85.5
        assert update.feedback == "Good work!"

    def test_student_assignment_status_validation(self):
        """Test status enum validation"""
        # Valid statuses
        valid_statuses = [
            "NOT_STARTED",
            "IN_PROGRESS",
            "SUBMITTED",
            "GRADED",
            "RETURNED",
            "RESUBMITTED",
        ]

        for status in valid_statuses:
            data = {
                "assignment_id": 1,
                "student_id": 1,
                "classroom_id": 1,
                "title": "Test",
                "status": status,
            }
            sa = StudentAssignmentCreate(**data)
            assert sa.status == status

        # Invalid status
        with pytest.raises(ValidationError):
            StudentAssignmentCreate(
                assignment_id=1,
                student_id=1,
                classroom_id=1,
                title="Test",
                status="INVALID_STATUS",
            )


class TestStudentContentProgressSchemas:
    def test_content_progress_create(self):
        """Test creating content progress schema"""
        data = {
            "student_assignment_id": 1,
            "content_id": 1,
            "status": "NOT_STARTED",
            "order_index": 0,
        }
        progress = StudentContentProgressCreate(**data)

        assert progress.student_assignment_id == 1
        assert progress.content_id == 1
        assert progress.status == "NOT_STARTED"

    def test_content_progress_update(self):
        """Test updating content progress"""
        data = {
            "status": "GRADED",
            "score": 92.0,
            "checked": True,
            "feedback": "Excellent!",
            "response_data": {"audio_url": "test.mp3"},
            "ai_scores": {"wpm": 85, "accuracy": 0.95},
        }
        update = StudentContentProgressUpdate(**data)

        assert update.status == "GRADED"
        assert update.score == 92.0
        assert update.checked is True
        assert update.ai_scores["wpm"] == 85

    def test_content_progress_with_response(self):
        """Test progress with student response data"""
        data = {
            "student_assignment_id": 1,
            "content_id": 1,
            "status": "SUBMITTED",
            "response_data": {
                "audio_url": "recording.mp3",
                "duration": 45,
                "submitted_at": datetime.utcnow().isoformat(),
            },
        }
        progress = StudentContentProgressCreate(**data)

        assert progress.response_data["audio_url"] == "recording.mp3"
        assert progress.response_data["duration"] == 45


class TestComplexSchemas:
    def test_assignment_with_full_details(self):
        """Test assignment with all nested details"""
        data = {
            "id": 1,
            "title": "Complex Assignment",
            "description": "Test with full details",
            "classroom_id": 1,
            "teacher_id": 1,
            "due_date": datetime.utcnow() + timedelta(days=7),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "contents": [
                {
                    "id": 1,
                    "title": "Reading Content",
                    "type": "READING_ASSESSMENT",
                    "items": [
                        {"text": "Hello", "translation": "你好"},
                        {"text": "World", "translation": "世界"},
                    ],
                }
            ],
            "student_assignments": [
                {
                    "id": 1,
                    "student_id": 1,
                    "status": "IN_PROGRESS",
                    "student": {
                        "id": 1,
                        "name": "John Doe",
                        "email": "john@example.com",
                    },
                }
            ],
        }

        response = AssignmentWithDetails(**data)

        assert response.id == 1
        assert len(response.contents) == 1
        assert response.contents[0]["type"] == "READING_ASSESSMENT"
        assert len(response.student_assignments) == 1
        assert response.student_assignments[0]["student"]["name"] == "John Doe"

    def test_student_assignment_with_progress(self):
        """Test student assignment with content progress"""
        data = {
            "id": 1,
            "assignment_id": 1,
            "student_id": 1,
            "classroom_id": 1,
            "title": "Student's Assignment",
            "status": "IN_PROGRESS",
            "score": 75.0,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "content_progress": [
                {
                    "id": 1,
                    "content_id": 1,
                    "status": "GRADED",
                    "score": 90.0,
                    "checked": True,
                },
                {
                    "id": 2,
                    "content_id": 2,
                    "status": "IN_PROGRESS",
                    "score": None,
                    "checked": False,
                },
            ],
        }

        response = StudentAssignmentWithProgress(**data)

        assert response.id == 1
        assert response.status == "IN_PROGRESS"
        assert len(response.content_progress) == 2
        assert response.content_progress[0]["status"] == "GRADED"
        assert response.content_progress[1]["checked"] is False


class TestSchemaValidation:
    def test_date_validation(self):
        """Test date field validation"""
        # Valid ISO format
        valid_date = datetime.utcnow().isoformat()
        data = {
            "title": "Test",
            "classroom_id": 1,
            "content_ids": [1],
            "student_ids": [],
            "due_date": valid_date,
        }
        assignment = AssignmentCreate(**data)
        assert assignment.due_date is not None

        # Invalid date format
        with pytest.raises(ValidationError):
            AssignmentCreate(
                title="Test",
                classroom_id=1,
                content_ids=[1],
                student_ids=[],
                due_date="not-a-date",
            )

    def test_score_validation(self):
        """Test score field validation"""
        # Valid score
        update = StudentAssignmentUpdate(score=85.5)
        assert update.score == 85.5

        # Negative score (should be allowed but flagged in business logic)
        update = StudentAssignmentUpdate(score=-10)
        assert update.score == -10

        # Score over 100 (should be allowed but flagged in business logic)
        update = StudentAssignmentUpdate(score=150)
        assert update.score == 150

    def test_json_field_validation(self):
        """Test JSON field validation"""
        # Valid JSON data
        progress = StudentContentProgressUpdate(
            response_data={"key": "value", "nested": {"data": 123}},
            ai_scores={"wpm": 80, "accuracy": 0.9},
        )
        assert progress.response_data["key"] == "value"
        assert progress.ai_scores["wpm"] == 80

        # Complex JSON structure
        complex_data = {
            "recordings": [
                {"url": "rec1.mp3", "duration": 30},
                {"url": "rec2.mp3", "duration": 45},
            ],
            "metadata": {"device": "iPhone", "app_version": "1.0.0"},
        }
        progress = StudentContentProgressUpdate(response_data=complex_data)
        assert len(progress.response_data["recordings"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
