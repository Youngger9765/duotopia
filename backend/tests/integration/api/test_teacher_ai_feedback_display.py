"""
Test for AI feedback display in teacher grading interface
Following TDD principle from CLAUDE.md
"""

import pytest
from fastapi import status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import (
    Teacher,
    Student,
    Assignment,
    StudentAssignment,
    Content,
    StudentContentProgress,
    AssignmentContent,
    Classroom,
    AssignmentStatus,
)
from main import app


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Create test client with database override"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[app.dependencies[0]] = override_get_db

    from httpx import AsyncClient

    return AsyncClient(app=app, base_url="http://test")


class TestTeacherAIFeedbackDisplay:
    """Test AI feedback display functionality for teachers"""

    @pytest.mark.asyncio
    async def test_submission_api_includes_ai_scores(self, client, db_session):
        """
        Test that the student submission API includes AI scores data for teachers
        This verifies the current state before implementing the frontend feature
        """
        # Create test data
        teacher = Teacher(
            name="Test Teacher", email="teacher@test.com", hashed_password="test_hash"
        )
        db_session.add(teacher)
        db_session.commit()

        classroom = Classroom(name="Test Classroom", teacher_id=teacher.id)
        db_session.add(classroom)
        db_session.commit()

        student = Student(
            name="Test Student",
            email="student@test.com",
            student_number="S001",
            classroom_id=classroom.id,
        )
        db_session.add(student)
        db_session.commit()

        # Create content with items
        content = Content(
            title="Test Content",
            type="READING_ASSESSMENT",
            items=[{"text": "Hello, how are you?", "translation": "你好，你好嗎？"}],
        )
        db_session.add(content)
        db_session.commit()

        # Create assignment
        assignment = Assignment(
            title="Test Assignment",
            description="Test description",
            classroom_id=classroom.id,
        )
        db_session.add(assignment)
        db_session.commit()

        # Link content to assignment
        assignment_content = AssignmentContent(
            assignment_id=assignment.id, content_id=content.id, order_index=0
        )
        db_session.add(assignment_content)
        db_session.commit()

        # Create student assignment
        student_assignment = StudentAssignment(
            student_id=student.id,
            assignment_id=assignment.id,
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(student_assignment)
        db_session.commit()

        # Create progress with AI scores (simulating speech assessment result)
        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=content.id,
            order_index=0,
            response_data={
                "audio_url": "https://storage.googleapis.com/test-bucket/recording.webm",
                "student_answer": "Hello how are you",
                "transcript": "Hello how are you",
            },
            ai_scores={
                "accuracy_score": 85.5,
                "fluency_score": 78.2,
                "completeness_score": 92.0,
                "pronunciation_score": 88.7,
                "word_details": [
                    {"word": "Hello", "accuracy_score": 95.0, "error_type": None},
                    {
                        "word": "how",
                        "accuracy_score": 82.5,
                        "error_type": "slight_mispronunciation",
                    },
                    {"word": "are", "accuracy_score": 88.0, "error_type": None},
                    {"word": "you", "accuracy_score": 90.5, "error_type": None},
                ],
            },
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(progress)
        db_session.commit()

        # Get teacher auth headers (mock authentication)
        headers = {"Authorization": f"Bearer teacher_token_{teacher.id}"}

        # Make API request to get student submission
        response = await client.get(
            f"/api/teachers/teachers/assignments/{assignment.id}/submissions/{student.id}",
            headers=headers,
        )

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Check that submissions exist
        assert "submissions" in data
        assert len(data["submissions"]) > 0

        submission = data["submissions"][0]

        # Verify basic submission data
        assert submission["question_text"] == "Hello, how are you?"
        assert (
            submission["student_audio_url"]
            == "https://storage.googleapis.com/test-bucket/recording.webm"
        )

        # CRITICAL TEST: AI scores should be included in the response
        # This is what we need to implement
        assert (
            "ai_scores" in submission
        ), "AI scores should be included in submission response for teacher grading"

        ai_scores = submission["ai_scores"]
        assert ai_scores["accuracy_score"] == 85.5
        assert ai_scores["fluency_score"] == 78.2
        assert ai_scores["completeness_score"] == 92.0
        assert ai_scores["pronunciation_score"] == 88.7
        assert "word_details" in ai_scores
        assert len(ai_scores["word_details"]) == 4

        # Verify word-level details
        word_details = ai_scores["word_details"]
        assert word_details[0]["word"] == "Hello"
        assert word_details[0]["accuracy_score"] == 95.0
        assert word_details[1]["error_type"] == "slight_mispronunciation"

    @pytest.mark.asyncio
    async def test_submission_without_ai_scores_handles_gracefully(
        self, client, db_session
    ):
        """
        Test that submissions without AI scores are handled gracefully
        (e.g., text-only assignments or pending speech assessments)
        """
        # Create basic test data
        teacher = Teacher(
            name="Test Teacher 2",
            email="teacher2@test.com",
            hashed_password="test_hash",
        )
        db_session.add(teacher)
        db_session.commit()

        classroom = Classroom(name="Test Classroom 2", teacher_id=teacher.id)
        db_session.add(classroom)
        db_session.commit()

        student = Student(
            name="Test Student 2",
            email="student2@test.com",
            student_number="S002",
            classroom_id=classroom.id,
        )
        db_session.add(student)
        db_session.commit()

        content = Content(
            title="Text Only Content",
            type="READING_ASSESSMENT",
            items=[{"text": "Write an essay", "type": "text"}],
        )
        db_session.add(content)
        db_session.commit()

        assignment = Assignment(
            title="Text Assignment", description="Text only", classroom_id=classroom.id
        )
        db_session.add(assignment)
        db_session.commit()

        assignment_content = AssignmentContent(
            assignment_id=assignment.id, content_id=content.id, order_index=0
        )
        db_session.add(assignment_content)
        db_session.commit()

        student_assignment = StudentAssignment(
            student_id=student.id,
            assignment_id=assignment.id,
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(student_assignment)
        db_session.commit()

        # Progress without AI scores
        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=content.id,
            order_index=0,
            response_data={"student_answer": "This is my essay response..."},
            ai_scores=None,  # No AI scores
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(progress)
        db_session.commit()

        headers = {"Authorization": f"Bearer teacher_token_{teacher.id}"}

        response = await client.get(
            f"/api/teachers/teachers/assignments/{assignment.id}/submissions/{student.id}",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        submission = data["submissions"][0]

        # Should handle missing AI scores gracefully
        assert submission.get("ai_scores") is None or submission.get("ai_scores") == {}
        assert submission["student_answer"] == "This is my essay response..."
