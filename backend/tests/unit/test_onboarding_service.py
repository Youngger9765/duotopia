"""
Unit tests for OnboardingService
Test all onboarding data creation for new registered teachers
"""
import os
import sys
from datetime import date
from unittest.mock import patch
from decimal import Decimal

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from database import Base  # noqa: E402
from services.onboarding_service import OnboardingService  # noqa: E402
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
    AssignmentStatus,
    ProgramLevel,
)


# Test database setup
@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def teacher(db_session):
    """Create a test teacher"""
    teacher = Teacher(
        email="test@example.com",
        password_hash="hashed_password",
        name="Test Teacher",
        is_active=True,
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher


@pytest.fixture
def onboarding_service():
    """Create OnboardingService instance"""
    return OnboardingService()


class TestOnboardingServiceInit:
    """Test OnboardingService initialization"""

    def test_init_onboarding_service(self):
        """Test service initialization"""
        service = OnboardingService()
        assert service is not None


class TestCreateOnboardingData:
    """Test complete onboarding data creation"""

    def test_create_onboarding_data_success(
        self, db_session, teacher, onboarding_service
    ):
        """Test successful creation of all onboarding data"""
        result = onboarding_service.create_onboarding_data(db_session, teacher)

        assert result is True

        # Verify classroom created
        classroom = db_session.query(Classroom).filter_by(teacher_id=teacher.id).first()
        assert classroom is not None
        assert classroom.name == "My First Class"
        assert classroom.is_active is True

        # Verify student created
        student = db_session.query(Student).filter_by(name="Bruce").first()
        assert student is not None
        assert student.birthdate == date(2012, 1, 1)
        assert student.student_number == "DEMO001"

        # Verify enrollment
        enrollment = (
            db_session.query(ClassroomStudent)
            .filter_by(classroom_id=classroom.id, student_id=student.id)
            .first()
        )
        assert enrollment is not None

        # Verify program/course created
        program = db_session.query(Program).filter_by(teacher_id=teacher.id).first()
        assert program is not None
        assert program.name == "Welcome to Duotopia!"
        assert program.classroom_id == classroom.id

        # Verify lesson created
        lesson = db_session.query(Lesson).filter_by(program_id=program.id).first()
        assert lesson is not None
        assert lesson.name == "Hello, teacher!"

        # Verify content created
        content = db_session.query(Content).filter_by(lesson_id=lesson.id).first()
        assert content is not None
        assert content.title == "Your First Try!"

        # Verify 3 content items created
        items = db_session.query(ContentItem).filter_by(content_id=content.id).all()
        assert len(items) == 3
        assert items[0].text == "Hello, teachers!"
        assert items[1].text == "Nice to see you on Duotopia."
        assert (
            items[2].text
            == 'Use only "a" second to grade assignments then get your free time!'
        )

        # Verify assignment created
        assignment = (
            db_session.query(Assignment).filter_by(teacher_id=teacher.id).first()
        )
        assert assignment is not None
        assert assignment.title == "Now give it a try!"
        assert assignment.description == "自己當學生試試看"

        # Verify student assignment in SUBMITTED status
        student_assignment = (
            db_session.query(StudentAssignment)
            .filter_by(assignment_id=assignment.id, student_id=student.id)
            .first()
        )
        assert student_assignment is not None
        assert student_assignment.status == AssignmentStatus.SUBMITTED

        # Verify AI assessment results exist
        progress_records = (
            db_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .all()
        )
        assert len(progress_records) == 3

        # Verify AI scores
        for progress in progress_records:
            assert progress.accuracy_score is not None
            assert progress.fluency_score is not None
            assert progress.pronunciation_score is not None
            assert progress.completeness_score is not None
            assert progress.ai_feedback is not None
            assert progress.ai_assessed_at is not None
            assert progress.status == "COMPLETED"

    def test_create_onboarding_data_idempotency(
        self, db_session, teacher, onboarding_service
    ):
        """Test that calling twice doesn't create duplicate data"""
        # First call
        result1 = onboarding_service.create_onboarding_data(db_session, teacher)
        assert result1 is True

        # Count records
        classroom_count = (
            db_session.query(Classroom).filter_by(teacher_id=teacher.id).count()
        )
        student_count = db_session.query(Student).filter_by(name="Bruce").count()

        # Second call
        result2 = onboarding_service.create_onboarding_data(db_session, teacher)
        assert result2 is True

        # Verify no duplicates
        assert (
            db_session.query(Classroom).filter_by(teacher_id=teacher.id).count()
            == classroom_count
        )
        assert (
            db_session.query(Student).filter_by(name="Bruce").count() == student_count
        )

    def test_create_onboarding_data_rollback_on_error(
        self, db_session, teacher, onboarding_service
    ):
        """Test that errors trigger rollback"""
        with patch.object(
            onboarding_service,
            "_create_default_classroom",
            side_effect=Exception("Test error"),
        ):
            result = onboarding_service.create_onboarding_data(db_session, teacher)

        assert result is False
        # Verify no data was created
        assert db_session.query(Classroom).filter_by(teacher_id=teacher.id).count() == 0


class TestCreateDefaultClassroom:
    """Test classroom creation"""

    def test_create_default_classroom(self, db_session, teacher, onboarding_service):
        """Test default classroom creation"""
        classroom = onboarding_service._create_default_classroom(db_session, teacher)

        assert classroom is not None
        assert classroom.name == "My First Class"
        assert classroom.teacher_id == teacher.id
        assert classroom.level == ProgramLevel.A1
        assert classroom.is_active is True
        assert (
            classroom.description
            == "Your first classroom on Duotopia! Start exploring here."
        )


class TestCreateDemoStudent:
    """Test demo student creation"""

    def test_create_demo_student(self, db_session, teacher, onboarding_service):
        """Test demo student Bruce creation"""
        student = onboarding_service._create_demo_student(db_session, teacher)

        assert student is not None
        assert student.name == "Bruce"
        assert student.student_number == "DEMO001"
        assert student.birthdate == date(2012, 1, 1)
        assert student.password_changed is False
        assert student.email_verified is False
        assert student.is_active is True
        assert student.target_wpm == 80
        assert student.target_accuracy == 0.8

        # Verify password is hashed (not plaintext)
        assert student.password_hash != "20120101"
        assert len(student.password_hash) > 20


class TestEnrollStudent:
    """Test student enrollment"""

    def test_enroll_student(self, db_session, teacher, onboarding_service):
        """Test enrolling student in classroom"""
        classroom = onboarding_service._create_default_classroom(db_session, teacher)
        student = onboarding_service._create_demo_student(db_session, teacher)

        enrollment = onboarding_service._enroll_student(db_session, classroom, student)

        assert enrollment is not None
        assert enrollment.classroom_id == classroom.id
        assert enrollment.student_id == student.id
        assert enrollment.is_active is True


class TestCreateWelcomeCourse:
    """Test welcome course creation"""

    def test_create_welcome_course_structure(
        self, db_session, teacher, onboarding_service
    ):
        """Test complete course structure creation"""
        classroom = onboarding_service._create_default_classroom(db_session, teacher)
        program = onboarding_service._create_welcome_course(
            db_session, teacher, classroom
        )

        # Verify program
        assert program is not None
        assert program.name == "Welcome to Duotopia!"
        assert program.classroom_id == classroom.id
        assert program.teacher_id == teacher.id
        assert program.is_template is False
        assert program.level == ProgramLevel.A1

        # Verify lesson
        lesson = db_session.query(Lesson).filter_by(program_id=program.id).first()
        assert lesson is not None
        assert lesson.name == "Hello, teacher!"

        # Verify content
        content = db_session.query(Content).filter_by(lesson_id=lesson.id).first()
        assert content is not None
        assert content.title == "Your First Try!"
        assert content.target_wpm == 80
        assert content.target_accuracy == 0.8

        # Verify 3 questions
        items = (
            db_session.query(ContentItem)
            .filter_by(content_id=content.id)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(items) == 3

        # Check each question
        assert items[0].text == "Hello, teachers!"
        assert items[0].translation == "老師們好！"
        assert items[0].order_index == 0

        assert items[1].text == "Nice to see you on Duotopia."
        assert items[1].translation == "很高興在 Duotopia 見到您。"
        assert items[1].order_index == 1

        assert (
            items[2].text
            == 'Use only "a" second to grade assignments then get your free time!'
        )
        assert items[2].translation == "只需「一」秒鐘批改作業，然後獲得您的自由時間！"
        assert items[2].order_index == 2


class TestCreateDemoAssignment:
    """Test demo assignment creation with AI results"""

    def test_create_demo_assignment_with_ai_results(
        self, db_session, teacher, onboarding_service
    ):
        """Test assignment creation with pre-filled AI assessment"""
        classroom = onboarding_service._create_default_classroom(db_session, teacher)
        student = onboarding_service._create_demo_student(db_session, teacher)
        onboarding_service._enroll_student(db_session, classroom, student)
        program = onboarding_service._create_welcome_course(
            db_session, teacher, classroom
        )

        assignment = onboarding_service._create_demo_assignment(
            db_session, teacher, classroom, program, student
        )

        # Verify assignment
        assert assignment is not None
        assert assignment.title == "Now give it a try!"
        assert assignment.description == "自己當學生試試看"
        assert assignment.due_date is None  # No deadline

        # Verify student assignment status
        student_assignment = (
            db_session.query(StudentAssignment)
            .filter_by(assignment_id=assignment.id, student_id=student.id)
            .first()
        )
        assert student_assignment is not None
        assert student_assignment.status == AssignmentStatus.SUBMITTED

        # Verify AI assessment for all 3 items
        progress_records = (
            db_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .order_by(StudentItemProgress.id)
            .all()
        )

        assert len(progress_records) == 3

        # Check first item
        assert progress_records[0].accuracy_score == Decimal("95.0")
        assert progress_records[0].fluency_score == Decimal("88.0")
        assert progress_records[0].pronunciation_score == Decimal("92.0")
        assert progress_records[0].completeness_score == Decimal("100.0")
        assert "Excellent" in progress_records[0].ai_feedback
        assert progress_records[0].status == "COMPLETED"

        # Check second item
        assert progress_records[1].accuracy_score == Decimal("90.0")
        assert progress_records[1].fluency_score == Decimal("85.0")

        # Check third item
        assert progress_records[2].accuracy_score == Decimal("87.0")
        assert progress_records[2].fluency_score == Decimal("82.0")

    def test_create_demo_assignment_missing_content_raises_error(
        self, db_session, teacher, onboarding_service
    ):
        """Test that missing content raises appropriate error"""
        classroom = onboarding_service._create_default_classroom(db_session, teacher)
        student = onboarding_service._create_demo_student(db_session, teacher)

        # Create program without lessons/content
        program = Program(
            name="Empty Program",
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            is_template=False,
        )
        db_session.add(program)
        db_session.flush()

        with pytest.raises(ValueError, match="No lesson found"):
            onboarding_service._create_demo_assignment(
                db_session, teacher, classroom, program, student
            )


class TestOnboardingDataCompleteness:
    """Test that all requirements from Issue #61 are met"""

    def test_all_requirements_met(self, db_session, teacher, onboarding_service):
        """
        Verify all requirements from Issue #61:
        1. Class: "My First Class"
        2. Student: "Bruce" with birthday 20120101
        3. Course: "Welcome to Duotopia!" with unit and content
        4. Assignment: Pre-assigned with AI results in SUBMITTED status
        """
        result = onboarding_service.create_onboarding_data(db_session, teacher)
        assert result is True

        # Requirement 1: Class
        classroom = (
            db_session.query(Classroom)
            .filter_by(teacher_id=teacher.id, name="My First Class")
            .first()
        )
        assert classroom is not None

        # Requirement 2: Student
        student = db_session.query(Student).filter_by(name="Bruce").first()
        assert student is not None
        assert student.birthdate == date(2012, 1, 1)

        # Requirement 3: Course structure
        program = (
            db_session.query(Program)
            .filter_by(teacher_id=teacher.id, name="Welcome to Duotopia!")
            .first()
        )
        assert program is not None

        lesson = (
            db_session.query(Lesson)
            .filter_by(program_id=program.id, name="Hello, teacher!")
            .first()
        )
        assert lesson is not None

        content = (
            db_session.query(Content)
            .filter_by(lesson_id=lesson.id, title="Your First Try!")
            .first()
        )
        assert content is not None

        # 3 questions
        items = db_session.query(ContentItem).filter_by(content_id=content.id).count()
        assert items == 3

        # Requirement 4: Pre-assigned assignment with AI results
        assignment = (
            db_session.query(Assignment)
            .filter_by(teacher_id=teacher.id, title="Now give it a try!")
            .first()
        )
        assert assignment is not None

        student_assignment = (
            db_session.query(StudentAssignment)
            .filter_by(
                assignment_id=assignment.id,
                student_id=student.id,
                status=AssignmentStatus.SUBMITTED,
            )
            .first()
        )
        assert student_assignment is not None

        # Verify AI assessment exists
        ai_results = (
            db_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .all()
        )
        assert len(ai_results) == 3

        for result in ai_results:
            assert result.ai_assessed_at is not None
            assert result.accuracy_score is not None
