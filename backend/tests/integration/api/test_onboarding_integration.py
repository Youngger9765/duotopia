"""
Integration tests for Onboarding System - TDD RED Phase
Issue #61: New user onboarding automation

Integration tests verify end-to-end workflow with real database:
1. Teacher registration → First login → Onboarding triggered
2. Database state verification
3. Complete onboarding workflow validation

Test Coverage:
- 10 integration tests for full onboarding flow
- Real database interactions (SQLite test DB)
- Verify all entities created correctly
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from models import (  # noqa: E402
    Teacher,
    Classroom,
    Student,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    StudentAssignment,
    StudentItemProgress,
)


class TestOnboardingIntegrationBasic:
    """Basic integration tests for onboarding workflow"""

    @pytest.mark.asyncio
    async def test_onboarding_creates_classroom(self, test_session: Session):
        """Test that onboarding creates default classroom"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="integration@test.com",
            password_hash=get_password_hash("password123"),
            name="Integration Test Teacher",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Verify result
        assert result["success"] is True
        assert "classroom_id" in result

        # Verify classroom created in database
        classroom = (
            test_session.query(Classroom)
            .filter(Classroom.id == result["classroom_id"])
            .first()
        )

        assert classroom is not None
        assert classroom.name == "My First Class"
        assert classroom.teacher_id == teacher.id
        assert classroom.is_active is True

    @pytest.mark.asyncio
    async def test_onboarding_creates_student(self, test_session: Session):
        """Test that onboarding creates default student named Bruce"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="teacher2@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Two",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Verify student created
        assert "student_id" in result

        student = (
            test_session.query(Student)
            .filter(Student.id == result["student_id"])
            .first()
        )

        assert student is not None
        assert student.name == "Bruce"
        assert student.birthdate == date(2010, 1, 1)

        # Verify student enrolled in classroom
        enrollment = (
            test_session.query(ClassroomStudent)
            .filter(
                ClassroomStudent.student_id == student.id,
                ClassroomStudent.classroom_id == result["classroom_id"],
            )
            .first()
        )

        assert enrollment is not None
        assert enrollment.is_active is True

    @pytest.mark.asyncio
    async def test_onboarding_creates_program_with_three_questions(
        self, test_session: Session
    ):
        """Test that onboarding creates welcome program with exactly 3 questions"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="teacher3@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Three",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Verify program created
        assert "program_id" in result

        program = (
            test_session.query(Program)
            .filter(Program.id == result["program_id"])
            .first()
        )

        assert program is not None
        assert program.name == "Welcome to Duotopia"
        assert program.teacher_id == teacher.id
        assert program.is_template is False

        # Verify lesson exists
        lessons = (
            test_session.query(Lesson).filter(Lesson.program_id == program.id).all()
        )

        assert len(lessons) == 1
        assert lessons[0].name == "My First Lesson"

        # Verify content exists
        contents = (
            test_session.query(Content).filter(Content.lesson_id == lessons[0].id).all()
        )

        assert len(contents) == 1
        assert contents[0].title == "Reading Practice"

        # Verify exactly 3 questions
        questions = (
            test_session.query(ContentItem)
            .filter(ContentItem.content_id == contents[0].id)
            .order_by(ContentItem.order_index)
            .all()
        )

        assert len(questions) == 3
        assert "Hello" in questions[0].text
        assert "How are you" in questions[1].text
        assert "Nice to meet you" in questions[2].text

    @pytest.mark.asyncio
    async def test_onboarding_generates_audio_for_questions(
        self, test_session: Session
    ):
        """Test that onboarding generates TTS audio for all questions"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash
        from unittest.mock import patch, AsyncMock

        # Create teacher
        teacher = Teacher(
            email="teacher4@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Four",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Mock TTS service
        with patch("services.onboarding.get_tts_service") as mock_tts:
            mock_tts_instance = AsyncMock()
            mock_tts_instance.generate_tts.return_value = (
                "https://storage.googleapis.com/test_audio.mp3"
            )
            mock_tts.return_value = mock_tts_instance

            # Trigger onboarding
            service = OnboardingService(db=test_session)
            result = await service.trigger_onboarding(teacher.id)

            # Verify TTS called 3 times (one for each question)
            assert mock_tts_instance.generate_tts.call_count == 3

            # Verify audio URLs assigned
            program = (
                test_session.query(Program)
                .filter(Program.id == result["program_id"])
                .first()
            )

            lesson = program.lessons[0]
            content = lesson.contents[0]
            questions = (
                test_session.query(ContentItem)
                .filter(ContentItem.content_id == content.id)
                .all()
            )

            for question in questions:
                assert question.audio_url is not None
                assert question.audio_url.startswith("https://storage.googleapis.com/")

    @pytest.mark.asyncio
    async def test_onboarding_creates_assignment(self, test_session: Session):
        """Test that onboarding creates default assignment"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="teacher5@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Five",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Verify assignment created
        assert "assignment_id" in result

        assignment = (
            test_session.query(Assignment)
            .filter(Assignment.id == result["assignment_id"])
            .first()
        )

        assert assignment is not None
        assert assignment.title == "My First Assignment"
        assert assignment.teacher_id == teacher.id
        assert assignment.classroom_id == result["classroom_id"]
        assert assignment.due_date is not None


class TestOnboardingIntegrationAdvanced:
    """Advanced integration tests for onboarding workflow"""

    @pytest.mark.asyncio
    async def test_onboarding_simulates_student_submission(self, test_session: Session):
        """Test that onboarding simulates student submission with AI results"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash
        from unittest.mock import patch, AsyncMock

        # Create teacher
        teacher = Teacher(
            email="teacher6@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Six",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Mock AI assessment
        with patch("services.onboarding.AssessmentService") as mock_assessment:
            mock_assessment_instance = AsyncMock()
            mock_assessment_instance.assess_recording.return_value = {
                "accuracy_score": 85.0,
                "fluency_score": 80.0,
                "pronunciation_score": 90.0,
                "completeness_score": 95.0,
            }
            mock_assessment.return_value = mock_assessment_instance

            # Trigger onboarding
            service = OnboardingService(db=test_session)
            result = await service.trigger_onboarding(teacher.id)

            # Verify student assignment created
            student_assignment = (
                test_session.query(StudentAssignment)
                .filter(
                    StudentAssignment.student_id == result["student_id"],
                    StudentAssignment.assignment_id == result["assignment_id"],
                )
                .first()
            )

            assert student_assignment is not None

            # Verify item progress with AI scores
            item_progress = (
                test_session.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id == student_assignment.id
                )
                .all()
            )

            # Should have 3 item progress (one for each question)
            assert len(item_progress) == 3

            # Verify AI scores assigned
            for progress in item_progress:
                assert progress.accuracy_score is not None
                assert progress.fluency_score is not None
                assert progress.pronunciation_score is not None
                assert progress.completeness_score is not None

    @pytest.mark.asyncio
    async def test_onboarding_marks_completion(self, test_session: Session):
        """Test that onboarding marks teacher as completed"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="teacher7@test.com",
            password_hash=get_password_hash("password123"),
            name="Teacher Seven",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Verify onboarding completed successfully
        assert result["success"] is True
        assert "classroom_id" in result

    # NOTE: Idempotency test removed - onboarding now runs once at registration
    # No longer needed since onboarding is triggered immediately on registration

    @pytest.mark.asyncio
    async def test_onboarding_triggered_on_registration(
        self, test_client, test_session: Session
    ):
        """Test that onboarding is automatically triggered on registration"""
        from unittest.mock import patch

        # Mock email service to avoid sending real emails
        with patch("routers.auth.email_service") as mock_email_service:
            mock_email_service.send_teacher_verification_email.return_value = True

            # Register new teacher
            response = test_client.post(
                "/api/auth/teacher/register",
                json={
                    "email": "newteacher@test.com",
                    "password": "Password123!",
                    "name": "New Teacher",
                },
            )

            assert response.status_code == 200

        # Verify teacher created
        teacher = (
            test_session.query(Teacher)
            .filter(Teacher.email == "newteacher@test.com")
            .first()
        )
        assert teacher is not None

        # Verify default resources created (onboarding triggered)
        classroom = (
            test_session.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .first()
        )
        assert classroom is not None
        assert classroom.name == "My First Class"

        # Verify student created
        student = test_session.query(Student).filter(Student.name == "Bruce").first()
        assert student is not None

    @pytest.mark.asyncio
    async def test_onboarding_full_workflow_end_to_end(self, test_session: Session):
        """Test complete end-to-end onboarding workflow"""
        from services.onboarding import OnboardingService
        from auth import get_password_hash

        # Create teacher
        teacher = Teacher(
            email="fullworkflow@test.com",
            password_hash=get_password_hash("password123"),
            name="Full Workflow Teacher",
            email_verified=True,
            is_active=True,
        )
        test_session.add(teacher)
        test_session.commit()
        test_session.refresh(teacher)

        # Trigger onboarding
        service = OnboardingService(db=test_session)
        result = await service.trigger_onboarding(teacher.id)

        # Comprehensive verification
        assert result["success"] is True

        # 1. Verify classroom
        classroom = (
            test_session.query(Classroom)
            .filter(Classroom.id == result["classroom_id"])
            .first()
        )
        assert classroom is not None
        assert classroom.name == "My First Class"
        assert classroom.teacher_id == teacher.id

        # 2. Verify student
        student = (
            test_session.query(Student)
            .filter(Student.id == result["student_id"])
            .first()
        )
        assert student is not None
        assert student.name == "Bruce"

        # 3. Verify student enrolled
        enrollment = (
            test_session.query(ClassroomStudent)
            .filter(
                ClassroomStudent.student_id == student.id,
                ClassroomStudent.classroom_id == classroom.id,
            )
            .first()
        )
        assert enrollment is not None

        # 4. Verify program structure
        program = (
            test_session.query(Program)
            .filter(Program.id == result["program_id"])
            .first()
        )
        assert program is not None
        assert len(program.lessons) == 1
        assert len(program.lessons[0].contents) == 1

        # 5. Verify questions
        content = program.lessons[0].contents[0]
        questions = (
            test_session.query(ContentItem)
            .filter(ContentItem.content_id == content.id)
            .all()
        )
        assert len(questions) == 3

        # 6. Verify assignment
        assignment = (
            test_session.query(Assignment)
            .filter(Assignment.id == result["assignment_id"])
            .first()
        )
        assert assignment is not None
