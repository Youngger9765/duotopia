"""
Simple integration test for AI feedback display in teacher grading interface
Following TDD principle from CLAUDE.md

This test focuses on the core issue: API should include AI scores in submission response
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base
from models import StudentContentProgress, AssignmentStatus
from routers.assignments import get_student_submission
from tests.factories import TestDataFactory


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


class TestAIFeedbackIntegration:
    """Test AI feedback integration in submission API"""

    @pytest.mark.asyncio
    async def test_api_response_should_include_ai_scores(self, db_session):
        """
        Test the current API response structure
        This test should FAIL initially - demonstrating the missing AI scores feature
        """
        # Create test data using factory - 1 line instead of 50+!
        data = TestDataFactory.create_full_assignment_chain(
            db_session,
            with_ai_scores=True,
            content_items=[
                {"text": "Hello, how are you today?", "translation": "你好，你今天好嗎？"}
            ],
        )

        # The progress data is already set in the factory, no need to override

        # Call the API function directly (bypassing auth for testing)
        try:
            response = await get_student_submission(
                assignment_id=data["assignment"].id,
                student_id=data["student"].id,
                current_user=data["teacher"],  # Mock authenticated teacher
                db=db_session,
            )

            # Verify response structure
            assert "submissions" in response
            assert len(response["submissions"]) > 0

            submission = response["submissions"][0]

            # Check basic submission data exists
            assert submission["question_text"] == "Hello, how are you today?"
            assert (
                submission["student_audio_url"]
                == "https://storage.googleapis.com/test-bucket/recording.webm"
            )

            # CRITICAL TEST: AI scores should be included
            # This assertion will FAIL with current implementation
            # This demonstrates the missing feature we need to implement
            assert (
                "ai_scores" in submission
            ), f"AI scores missing from submission response. Available keys: {list(submission.keys())}"

            ai_scores = submission["ai_scores"]
            assert ai_scores is not None
            assert ai_scores["accuracy_score"] == 85.5
            assert ai_scores["fluency_score"] == 78.2
            assert ai_scores["completeness_score"] == 92.0
            assert ai_scores["pronunciation_score"] == 88.7
            assert "word_details" in ai_scores

        except AssertionError as e:
            # This is expected to fail initially - this proves the test is working
            print(f"✅ Test correctly identified missing AI scores feature: {e}")
            raise e

        except Exception as e:
            pytest.fail(f"Unexpected error in API call: {e}")

    def test_progress_has_ai_scores_in_database(self, db_session):
        """
        Verify that ai_scores data exists in the database
        This confirms our test data setup is correct
        """
        # Create test data using factory - much simpler!
        data = TestDataFactory.create_full_assignment_chain(db_session)

        # Update progress with specific AI scores
        progress = data["progress"]
        progress.ai_scores = {
            "accuracy_score": 90.0,
            "fluency_score": 85.0,
            "completeness_score": 95.0,
            "pronunciation_score": 87.5,
        }
        progress.status = AssignmentStatus.SUBMITTED
        db_session.commit()

        # Verify data is stored correctly
        retrieved = (
            db_session.query(StudentContentProgress)
            .filter_by(student_assignment_id=data["student_assignment"].id)
            .first()
        )

        assert retrieved is not None
        assert retrieved.ai_scores is not None
        assert retrieved.ai_scores["accuracy_score"] == 90.0
        assert retrieved.ai_scores["fluency_score"] == 85.0

        print("✅ Database correctly stores AI scores data")
