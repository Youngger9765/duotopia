"""
Unit tests for OnboardingService - TDD RED Phase
Issue #61: New user onboarding automation

Following TDD RED-GREEN-REFACTOR cycle:
1. RED: Write failing tests first
2. GREEN: Implement minimal code to pass
3. REFACTOR: Clean up and optimize

Test Coverage:
- 22 unit tests for OnboardingService methods
- Mock all external dependencies
- Test happy paths and error cases
"""
import os
import sys
from unittest.mock import Mock, patch, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import pytest  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

# Models will be imported after service exists
# from models import Teacher, Classroom, Student, Program, Lesson, Content, Assignment
# from services.onboarding import OnboardingService


class TestOnboardingServiceInit:
    """Test OnboardingService initialization"""

    def test_onboarding_service_init(self):
        """Test OnboardingService initializes correctly"""
        from services.onboarding import OnboardingService

        service = OnboardingService()

        # Service should have a database session dependency
        assert hasattr(service, "db")
        # Service should define default classroom name
        assert hasattr(service, "DEFAULT_CLASSROOM_NAME")
        assert service.DEFAULT_CLASSROOM_NAME == "My First Class"
        # Service should define default student name
        assert hasattr(service, "DEFAULT_STUDENT_NAME")
        assert service.DEFAULT_STUDENT_NAME == "Bruce"


class TestCreateDefaultClassroom:
    """Test _create_default_classroom method"""

    def test_create_default_classroom_success(self):
        """Test creating default classroom"""
        from services.onboarding import OnboardingService
        from models import Teacher  # noqa: F401

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        teacher = Teacher(id=1, email="test@teacher.com", name="Test Teacher")

        classroom = service._create_default_classroom(teacher)

        # Verify classroom properties
        assert classroom.name == "My First Class"
        assert classroom.teacher_id == teacher.id
        assert classroom.description is not None
        assert classroom.is_active is True

        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    def test_create_default_classroom_database_error(self):
        """Test database error during classroom creation"""
        from services.onboarding import OnboardingService
        from models import Teacher

        mock_db = Mock(spec=Session)
        mock_db.flush.side_effect = Exception("Database error")
        service = OnboardingService(db=mock_db)

        teacher = Teacher(id=1, email="test@teacher.com", name="Test Teacher")

        with pytest.raises(Exception) as exc_info:
            service._create_default_classroom(teacher)

        assert "Database error" in str(exc_info.value)


class TestCreateDefaultStudent:
    """Test _create_default_student method"""

    def test_create_default_student_success(self):
        """Test creating default student named Bruce"""
        from services.onboarding import OnboardingService
        from models import Classroom  # noqa: F401
        from datetime import date

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        classroom = Mock(spec=Classroom)
        classroom.id = 1

        student = service._create_default_student(classroom)

        # Verify student properties
        assert student.name == "Bruce"
        assert student.birthdate == date(2010, 1, 1)
        assert student.email is None
        assert student.password_hash is not None

        # Verify classroom enrollment created
        mock_db.add.assert_called()
        mock_db.flush.assert_called()


class TestCreateWelcomeProgram:
    """Test _create_welcome_program method"""

    def test_create_welcome_program_with_three_questions(self):
        """Test creating welcome program with 3 questions"""
        from services.onboarding import OnboardingService
        from models import Teacher

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        teacher = Mock(spec=Teacher)
        teacher.id = 1

        program = service._create_welcome_program(teacher)

        # Verify program structure
        assert program.name == "Welcome to Duotopia"
        assert program.is_template is False
        assert program.teacher_id == teacher.id

        # Verify lesson exists
        assert len(program.lessons) == 1
        lesson = program.lessons[0]
        assert lesson.name == "My First Lesson"

        # Verify exactly 3 content items (questions)
        assert len(lesson.contents) == 1
        content = lesson.contents[0]
        assert content.title == "Reading Practice"
        assert len(content.content_items) == 3

        # Verify question texts
        questions = content.content_items
        assert "Hello" in questions[0].text
        assert "How are you" in questions[1].text
        assert "Nice to meet you" in questions[2].text

    def test_create_welcome_program_database_error(self):
        """Test database error during program creation"""
        from services.onboarding import OnboardingService
        from models import Teacher

        mock_db = Mock(spec=Session)
        mock_db.flush.side_effect = Exception("Database error")
        service = OnboardingService(db=mock_db)

        teacher = Mock(spec=Teacher)
        teacher.id = 1

        with pytest.raises(Exception):
            service._create_welcome_program(teacher)


class TestGenerateQuestionAudio:
    """Test _generate_question_audio method"""

    @pytest.mark.asyncio
    async def test_generate_audio_for_three_questions(self):
        """Test generating TTS audio for 3 questions"""
        from services.onboarding import OnboardingService
        from models import ContentItem

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        # Create mock questions
        questions = [
            Mock(spec=ContentItem, id=1, text="Hello", audio_url=None),
            Mock(spec=ContentItem, id=2, text="How are you", audio_url=None),
            Mock(spec=ContentItem, id=3, text="Nice to meet you", audio_url=None),
        ]

        # Mock TTS service
        with patch("services.onboarding.get_tts_service") as mock_tts:
            mock_tts_instance = AsyncMock()
            mock_tts_instance.generate_tts.side_effect = [
                "https://storage.googleapis.com/audio1.mp3",
                "https://storage.googleapis.com/audio2.mp3",
                "https://storage.googleapis.com/audio3.mp3",
            ]
            mock_tts.return_value = mock_tts_instance

            await service._generate_question_audio(questions)

            # Verify TTS called for each question
            assert mock_tts_instance.generate_tts.call_count == 3

            # Verify audio URLs assigned
            assert questions[0].audio_url == "https://storage.googleapis.com/audio1.mp3"
            assert questions[1].audio_url == "https://storage.googleapis.com/audio2.mp3"
            assert questions[2].audio_url == "https://storage.googleapis.com/audio3.mp3"

            # Verify database flush
            assert mock_db.flush.call_count == 3

    @pytest.mark.asyncio
    async def test_generate_audio_tts_failure(self):
        """Test TTS generation failure - should log but not fail"""
        from services.onboarding import OnboardingService
        from models import ContentItem

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        questions = [Mock(spec=ContentItem, id=1, text="Hello", audio_url=None)]

        with patch("services.onboarding.get_tts_service") as mock_tts:
            mock_tts_instance = AsyncMock()
            mock_tts_instance.generate_tts.side_effect = Exception("TTS error")
            mock_tts.return_value = mock_tts_instance

            # Should not raise - TTS errors are logged but don't fail onboarding
            await service._generate_question_audio(questions)

            # Audio URL should be None (failed to generate)
            assert questions[0].audio_url is None


class TestCreateAndAssignDefaultAssignment:
    """Test _create_and_assign_default_assignment method"""

    def test_create_assignment_for_classroom(self):
        """Test creating default assignment"""
        from services.onboarding import OnboardingService
        from models import Teacher, Program, Classroom

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        teacher = Mock(spec=Teacher, id=1)
        program = Mock(spec=Program, id=1)
        classroom = Mock(spec=Classroom, id=1)

        assignment = service._create_and_assign_default_assignment(
            teacher, program, classroom
        )

        # Verify assignment properties
        assert assignment.title == "My First Assignment"
        assert assignment.teacher_id == teacher.id
        assert assignment.classroom_id == classroom.id
        assert assignment.due_date is not None

        # Verify database operations
        mock_db.add.assert_called()
        mock_db.flush.assert_called()


class TestSimulateStudentSubmission:
    """Test _simulate_student_submission method"""

    @pytest.mark.asyncio
    async def test_simulate_submission_with_ai_results(self):
        """Test simulating student submission with AI assessment"""
        from services.onboarding import OnboardingService
        from models import Assignment, Student  # noqa: F401

        mock_db = Mock(spec=Session)
        # Mock query to return empty results (simulates unit test without real DB)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = OnboardingService(db=mock_db)

        assignment = Mock(spec=Assignment, id=1)
        student = Mock(spec=Student, id=1)

        # Mock AI assessment service
        with patch("services.onboarding.AssessmentService") as mock_assessment:
            mock_assessment_instance = AsyncMock()
            mock_assessment_instance.assess_recording.return_value = {
                "accuracy_score": 85.0,
                "fluency_score": 80.0,
                "pronunciation_score": 90.0,
                "completeness_score": 95.0,
            }
            mock_assessment.return_value = mock_assessment_instance

            student_assignment = await service._simulate_student_submission(
                assignment, student
            )

            # Verify student assignment created
            assert student_assignment is not None
            assert student_assignment.student_id == student.id
            assert student_assignment.assignment_id == assignment.id

            # Verify database operations
            # commit() is called inside the method
            mock_db.add.assert_called()
            assert mock_db.commit.call_count >= 1


class TestTriggerOnboarding:
    """Test trigger_onboarding orchestrator method"""

    @pytest.mark.asyncio
    async def test_trigger_onboarding_full_workflow(self):
        """Test complete onboarding workflow"""
        from services.onboarding import OnboardingService
        from models import Teacher

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        teacher = Mock(spec=Teacher, id=1)

        # Mock all internal methods
        with patch.object(service, "_create_default_classroom") as mock_classroom:
            with patch.object(service, "_create_default_student") as mock_student:
                with patch.object(service, "_create_welcome_program") as mock_program:
                    with patch.object(
                        service, "_generate_question_audio"
                    ) as mock_audio:
                        with patch.object(
                            service,
                            "_create_and_assign_default_assignment",
                        ) as mock_assignment:
                            with patch.object(
                                service, "_simulate_student_submission"
                            ) as mock_submission:
                                mock_classroom.return_value = Mock(id=1)
                                mock_student.return_value = Mock(id=1)
                                mock_program.return_value = Mock(
                                    id=1,
                                    lessons=[Mock(contents=[Mock(content_items=[])])],
                                )
                                mock_assignment.return_value = Mock(id=1)

                                result = await service.trigger_onboarding(teacher.id)

                                # Verify all steps executed
                                mock_classroom.assert_called_once()
                                mock_student.assert_called_once()
                                mock_program.assert_called_once()
                                mock_audio.assert_called_once()
                                mock_assignment.assert_called_once()
                                mock_submission.assert_called_once()

                                # Verify result
                                assert result["success"] is True
                                assert "classroom_id" in result
                                assert "student_id" in result
                                assert "program_id" in result
                                assert "assignment_id" in result

    @pytest.mark.asyncio
    async def test_trigger_onboarding_teacher_not_found(self):
        """Test trigger onboarding with invalid teacher ID"""
        from services.onboarding import OnboardingService

        mock_db = Mock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None
        service = OnboardingService(db=mock_db)

        with pytest.raises(ValueError) as exc_info:
            await service.trigger_onboarding(999)

        assert "Teacher not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_trigger_onboarding_error_handling(self):
        """Test error handling in onboarding workflow"""
        from services.onboarding import OnboardingService
        from models import Teacher

        mock_db = Mock(spec=Session)
        service = OnboardingService(db=mock_db)

        teacher = Mock(spec=Teacher, id=1)

        with patch.object(
            service,
            "_create_default_classroom",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(Exception) as exc_info:
                await service.trigger_onboarding(teacher.id)

            assert "Database error" in str(exc_info.value)

            # Verify database rollback
            mock_db.rollback.assert_called()
