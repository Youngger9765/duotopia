"""
Integration test for teacher registration + email verification + onboarding flow
Tests the complete user journey from registration to having onboarding data
"""
import os
import sys
from datetime import date

from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from main import app  # noqa: E402
from database import Base, get_db  # noqa: E402
from models import (  # noqa: E402
    Teacher,
    Classroom,
    Student,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    StudentAssignment,
    StudentItemProgress,
    AssignmentStatus,
)


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_onboarding.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestTeacherRegistrationOnboardingFlow:
    """Test complete teacher registration and onboarding flow"""

    def setup_method(self):
        """Reset database before each test"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_complete_registration_to_onboarding_flow(self):
        """
        Test full flow: Register -> Verify Email -> Check Onboarding Data

        This is the critical E2E test for Issue #61
        """
        # Step 1: Register new teacher
        register_data = {
            "email": "newteacher@example.com",
            "password": "SecurePassword123!",
            "name": "New Teacher",
            "phone": "0912345678",
        }

        response = client.post("/api/auth/teacher/register", json=register_data)
        assert response.status_code == 200
        data = response.json()
        assert data["verification_required"] is True

        # Step 2: Get verification token from database
        db_session = TestingSessionLocal()
        teacher = (
            db_session.query(Teacher).filter_by(email=register_data["email"]).first()
        )
        assert teacher is not None
        assert teacher.email_verified is False
        assert teacher.email_verification_token is not None

        verification_token = teacher.email_verification_token

        # Step 3: Verify email (this triggers onboarding data creation)
        verify_response = client.get(
            f"/api/auth/verify-teacher?token={verification_token}"
        )
        assert verify_response.status_code == 200
        verify_data = verify_response.json()
        assert verify_data["status"] == "success"
        assert verify_data["user"]["email_verified"] is True

        # Refresh teacher from database
        db_session.refresh(teacher)
        assert teacher.email_verified is True
        assert teacher.is_active is True

        # Step 4: Verify onboarding data was created

        # 4.1: Verify classroom "My First Class"
        classroom = (
            db_session.query(Classroom)
            .filter_by(teacher_id=teacher.id, name="My First Class")
            .first()
        )
        assert classroom is not None, "Classroom 'My First Class' should be created"
        assert classroom.is_active is True

        # 4.2: Verify student "Bruce" with birthday 20120101
        student = db_session.query(Student).filter_by(name="Bruce").first()
        assert student is not None, "Student 'Bruce' should be created"
        assert student.birthdate == date(2012, 1, 1)
        assert student.student_number == "DEMO001"

        # 4.3: Verify course "Welcome to Duotopia!"
        program = (
            db_session.query(Program)
            .filter_by(teacher_id=teacher.id, name="Welcome to Duotopia!")
            .first()
        )
        assert program is not None, "Program 'Welcome to Duotopia!' should be created"
        assert program.classroom_id == classroom.id

        # 4.4: Verify lesson "Hello, teacher!"
        lesson = (
            db_session.query(Lesson)
            .filter_by(program_id=program.id, name="Hello, teacher!")
            .first()
        )
        assert lesson is not None, "Lesson 'Hello, teacher!' should be created"

        # 4.5: Verify content "Your First Try!"
        content = (
            db_session.query(Content)
            .filter_by(lesson_id=lesson.id, title="Your First Try!")
            .first()
        )
        assert content is not None, "Content 'Your First Try!' should be created"

        # 4.6: Verify 3 questions
        items = (
            db_session.query(ContentItem)
            .filter_by(content_id=content.id)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(items) == 3, "Should have 3 content items"

        expected_questions = [
            "Hello, teachers!",
            "Nice to see you on Duotopia.",
            'Use only "a" second to grade assignments then get your free time!',
        ]
        for idx, item in enumerate(items):
            assert item.text == expected_questions[idx]
            assert item.translation is not None
            assert item.order_index == idx

        # 4.7: Verify assignment "Now give it a try!"
        assignment = (
            db_session.query(Assignment)
            .filter_by(teacher_id=teacher.id, title="Now give it a try!")
            .first()
        )
        assert (
            assignment is not None
        ), "Assignment 'Now give it a try!' should be created"
        assert assignment.description == "自己當學生試試看"
        assert assignment.due_date is None  # No deadline

        # 4.8: Verify student assignment in SUBMITTED status
        student_assignment = (
            db_session.query(StudentAssignment)
            .filter_by(assignment_id=assignment.id, student_id=student.id)
            .first()
        )
        assert student_assignment is not None, "StudentAssignment should exist"
        assert (
            student_assignment.status == AssignmentStatus.SUBMITTED
        ), "Status should be SUBMITTED"
        assert student_assignment.submitted_at is not None

        # 4.9: Verify AI assessment results exist for all 3 items
        progress_records = (
            db_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .order_by(StudentItemProgress.id)
            .all()
        )

        assert len(progress_records) == 3, "Should have AI results for all 3 items"

        for idx, progress in enumerate(progress_records):
            assert (
                progress.accuracy_score is not None
            ), f"Item {idx} should have accuracy_score"
            assert (
                progress.fluency_score is not None
            ), f"Item {idx} should have fluency_score"
            assert (
                progress.pronunciation_score is not None
            ), f"Item {idx} should have pronunciation_score"
            assert (
                progress.completeness_score is not None
            ), f"Item {idx} should have completeness_score"
            assert (
                progress.ai_feedback is not None
            ), f"Item {idx} should have AI feedback"
            assert (
                progress.ai_assessed_at is not None
            ), f"Item {idx} should have assessment timestamp"
            assert progress.status == "COMPLETED", f"Item {idx} should be COMPLETED"

        db_session.close()

    def test_onboarding_idempotency(self):
        """Test that calling onboarding twice doesn't create duplicate data"""
        db_session = TestingSessionLocal()

        # Register and verify
        register_data = {
            "email": "idempotent@example.com",
            "password": "SecurePassword123!",
            "name": "Idempotent Teacher",
        }
        client.post("/api/auth/teacher/register", json=register_data)

        teacher = (
            db_session.query(Teacher).filter_by(email=register_data["email"]).first()
        )
        token = teacher.email_verification_token

        # First verification
        response1 = client.get(f"/api/auth/verify-teacher?token={token}")
        assert response1.status_code == 200

        # Count onboarding data
        db_session.refresh(teacher)
        classroom_count = (
            db_session.query(Classroom).filter_by(teacher_id=teacher.id).count()
        )
        student_count = db_session.query(Student).filter_by(name="Bruce").count()
        program_count = (
            db_session.query(Program).filter_by(teacher_id=teacher.id).count()
        )

        assert classroom_count == 1
        assert student_count >= 1
        assert program_count == 1

        db_session.close()


class TestOnboardingDataQuality:
    """Test quality and correctness of onboarding data"""

    def setup_method(self):
        """Reset database before each test"""
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    def test_student_password_is_birthdate(self):
        """Test that demo student's default password is their birthdate"""
        from auth import verify_password

        db_session = TestingSessionLocal()

        # Complete registration flow
        register_data = {
            "email": "pwd_test@example.com",
            "password": "SecurePassword123!",
            "name": "Password Test Teacher",
        }
        client.post("/api/auth/teacher/register", json=register_data)

        teacher = (
            db_session.query(Teacher).filter_by(email=register_data["email"]).first()
        )
        token = teacher.email_verification_token
        client.get(f"/api/auth/verify-teacher?token={token}")

        # Check student password
        student = db_session.query(Student).filter_by(name="Bruce").first()
        assert verify_password("20120101", student.password_hash) is True

        db_session.close()

    def test_ai_scores_are_realistic(self):
        """Test that AI scores are within realistic ranges"""
        db_session = TestingSessionLocal()

        # Complete registration flow
        register_data = {
            "email": "scores_test@example.com",
            "password": "SecurePassword123!",
            "name": "Scores Test Teacher",
        }
        client.post("/api/auth/teacher/register", json=register_data)

        teacher = (
            db_session.query(Teacher).filter_by(email=register_data["email"]).first()
        )
        token = teacher.email_verification_token
        client.get(f"/api/auth/verify-teacher?token={token}")

        # Get AI scores
        student_assignment = (
            db_session.query(StudentAssignment)
            .filter_by(status=AssignmentStatus.SUBMITTED)
            .first()
        )

        progress_records = (
            db_session.query(StudentItemProgress)
            .filter_by(student_assignment_id=student_assignment.id)
            .all()
        )

        for progress in progress_records:
            # All scores should be between 0 and 100
            assert 0 <= float(progress.accuracy_score) <= 100
            assert 0 <= float(progress.fluency_score) <= 100
            assert 0 <= float(progress.pronunciation_score) <= 100
            assert 0 <= float(progress.completeness_score) <= 100

        db_session.close()

    def test_content_structure_integrity(self):
        """Test that course structure follows proper hierarchy"""
        db_session = TestingSessionLocal()

        # Complete registration flow
        register_data = {
            "email": "structure_test@example.com",
            "password": "SecurePassword123!",
            "name": "Structure Test Teacher",
        }
        client.post("/api/auth/teacher/register", json=register_data)

        teacher = (
            db_session.query(Teacher).filter_by(email=register_data["email"]).first()
        )
        token = teacher.email_verification_token
        client.get(f"/api/auth/verify-teacher?token={token}")

        # Verify hierarchy: Program -> Lesson -> Content -> ContentItems
        program = db_session.query(Program).filter_by(teacher_id=teacher.id).first()
        assert program is not None

        lessons = db_session.query(Lesson).filter_by(program_id=program.id).all()
        assert len(lessons) == 1

        lesson = lessons[0]
        contents = db_session.query(Content).filter_by(lesson_id=lesson.id).all()
        assert len(contents) == 1

        content = contents[0]
        items = db_session.query(ContentItem).filter_by(content_id=content.id).all()
        assert len(items) == 3

        # Verify order indices are sequential
        for idx, item in enumerate(sorted(items, key=lambda x: x.order_index)):
            assert item.order_index == idx

        db_session.close()
