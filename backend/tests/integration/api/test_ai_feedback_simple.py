"""
Simple integration test for AI feedback display in teacher grading interface
Following TDD principle from CLAUDE.md

This test focuses on the core issue: API should include AI scores in submission response
"""

import pytest
from datetime import date
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
    Program,
    Lesson,
)
from routers.assignments import get_student_submission


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
        # Create test data
        teacher = Teacher(
            name="Test Teacher", email="teacher@test.com", password_hash="test_hash"
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
            password_hash="student_hash",
            birthdate=date(2000, 1, 1),
        )
        db_session.add(student)
        db_session.commit()

        # Create program first
        program = Program(
            name="Test Program", description="Test program", teacher_id=teacher.id
        )
        db_session.add(program)
        db_session.commit()

        # Create lesson
        lesson = Lesson(
            name="Test Lesson", description="Test lesson", program_id=program.id
        )
        db_session.add(lesson)
        db_session.commit()

        # Create content
        content = Content(
            lesson_id=lesson.id,
            title="Test Reading Assessment",
            type="READING_ASSESSMENT",
            items=[{"text": "Hello, how are you today?", "translation": "你好，你今天好嗎？"}],
        )
        db_session.add(content)
        db_session.commit()

        # Create assignment
        assignment = Assignment(
            title="Test Assignment",
            description="Test description",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
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
            classroom_id=classroom.id,
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
                "student_answer": "Hello how are you today",
                "transcript": "Hello how are you today",
            },
            # This is the key data that should appear in the API response
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
                ],
            },
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(progress)
        db_session.commit()

        # Call the API function directly (bypassing auth for testing)
        try:
            response = await get_student_submission(
                assignment_id=assignment.id,
                student_id=student.id,
                current_user=teacher,  # Mock authenticated teacher
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
        # Create minimal test data
        teacher = Teacher(name="Teacher", email="t@test.com", password_hash="hash")
        db_session.add(teacher)
        db_session.commit()

        classroom = Classroom(name="Classroom", teacher_id=teacher.id)
        db_session.add(classroom)
        db_session.commit()

        student = Student(
            name="Student",
            email="s@test.com",
            student_number="S001",
            password_hash="hash",
            birthdate=date(2000, 1, 1),
        )
        db_session.add(student)
        db_session.commit()

        # Create program and lesson for content
        program = Program(
            name="Test Program 2", description="Test program", teacher_id=teacher.id
        )
        db_session.add(program)
        db_session.commit()

        lesson = Lesson(
            name="Test Lesson 2", description="Test lesson", program_id=program.id
        )
        db_session.add(lesson)
        db_session.commit()

        content = Content(
            lesson_id=lesson.id,
            title="Content",
            type="READING_ASSESSMENT",
            items=[{"text": "test"}],
        )
        db_session.add(content)
        db_session.commit()

        assignment = Assignment(
            title="Assignment", classroom_id=classroom.id, teacher_id=teacher.id
        )
        db_session.add(assignment)
        db_session.commit()

        student_assignment = StudentAssignment(
            student_id=student.id,
            assignment_id=assignment.id,
            classroom_id=classroom.id,
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(student_assignment)
        db_session.commit()

        # Create progress with AI scores
        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=content.id,
            order_index=0,
            ai_scores={
                "accuracy_score": 90.0,
                "fluency_score": 85.0,
                "completeness_score": 95.0,
                "pronunciation_score": 87.5,
            },
            status=AssignmentStatus.SUBMITTED,
        )
        db_session.add(progress)
        db_session.commit()

        # Verify data is stored correctly
        retrieved = (
            db_session.query(StudentContentProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .first()
        )

        assert retrieved is not None
        assert retrieved.ai_scores is not None
        assert retrieved.ai_scores["accuracy_score"] == 90.0
        assert retrieved.ai_scores["fluency_score"] == 85.0

        print("✅ Database correctly stores AI scores data")
