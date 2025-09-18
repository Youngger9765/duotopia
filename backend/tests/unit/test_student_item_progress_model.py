# Unit Tests for StudentItemProgress Model

import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import (
    User,
    Content,
    ContentItem,
    StudentAssignment,
    StudentItemProgress,
    Classroom,
)
from decimal import Decimal
from datetime import datetime


class TestStudentItemProgressModel:
    """Test StudentItemProgress model functionality"""

    def setup_method(self):
        """Setup common test data"""
        self.progress_data = {
            "recording_url": "https://example.com/recording.webm",
            "answer_text": "Hello world",
            "accuracy_score": Decimal("85.5"),
            "fluency_score": Decimal("78.9"),
            "pronunciation_score": Decimal("92.3"),
            "ai_feedback": "Good pronunciation!",
            "status": "COMPLETED",
            "attempts": 1,
        }

    def create_test_setup(self, db: Session, teacher: User, student: User):
        """Create basic test setup with assignment and content item"""
        # Create content and content item
        content = Content(
            title="Test Content", type="pronunciation", teacher_id=teacher.id
        )
        db.add(content)
        db.flush()

        content_item = ContentItem(
            content_id=content.id, order_index=0, text="Hello world", translation="你好世界"
        )
        db.add(content_item)
        db.flush()

        # Create classroom and assignment
        classroom = Classroom(name="Test Classroom", teacher_id=teacher.id)
        db.add(classroom)
        db.flush()

        assignment = StudentAssignment(
            student_id=student.id,
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            content_id=content.id,
            title="Test Assignment",
        )
        db.add(assignment)
        db.flush()

        return assignment, content_item

    def test_student_item_progress_creation(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test basic StudentItemProgress creation"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Create progress record
        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            **self.progress_data,
        )
        test_db.add(progress)
        test_db.commit()

        # Verify
        assert progress.id is not None
        assert progress.student_assignment_id == assignment.id
        assert progress.content_item_id == content_item.id
        assert progress.recording_url == "https://example.com/recording.webm"
        assert progress.answer_text == "Hello world"
        assert progress.accuracy_score == Decimal("85.5")
        assert progress.fluency_score == Decimal("78.9")
        assert progress.pronunciation_score == Decimal("92.3")
        assert progress.ai_feedback == "Good pronunciation!"
        assert progress.status == "COMPLETED"
        assert progress.attempts == 1
        assert progress.created_at is not None
        assert progress.updated_at is not None

    def test_student_item_progress_required_fields(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test that required fields are enforced"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Missing student_assignment_id should fail
        with pytest.raises(IntegrityError):
            progress = StudentItemProgress(
                content_item_id=content_item.id,
                # Missing student_assignment_id
            )
            test_db.add(progress)
            test_db.commit()

        test_db.rollback()

        # Missing content_item_id should fail
        with pytest.raises(IntegrityError):
            progress = StudentItemProgress(
                student_assignment_id=assignment.id,
                # Missing content_item_id
            )
            test_db.add(progress)
            test_db.commit()

    def test_student_item_progress_unique_constraint(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test unique constraint on (student_assignment_id, content_item_id)"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Create first progress record
        progress1 = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            status="IN_PROGRESS",
        )
        test_db.add(progress1)
        test_db.commit()

        # Try to create duplicate should fail
        with pytest.raises(IntegrityError):
            progress2 = StudentItemProgress(
                student_assignment_id=assignment.id,
                content_item_id=content_item.id,  # Same combination
                status="COMPLETED",
            )
            test_db.add(progress2)
            test_db.commit()

    def test_student_item_progress_defaults(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test default values are set correctly"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Create minimal progress record
        progress = StudentItemProgress(
            student_assignment_id=assignment.id, content_item_id=content_item.id
        )
        test_db.add(progress)
        test_db.commit()

        # Verify defaults
        assert progress.status == "NOT_STARTED"
        assert progress.attempts == 0
        assert progress.recording_url is None
        assert progress.answer_text is None
        assert progress.accuracy_score is None
        assert progress.fluency_score is None
        assert progress.pronunciation_score is None
        assert progress.ai_feedback is None
        assert progress.submitted_at is None
        assert progress.ai_assessed_at is None

    def test_student_item_progress_status_constraint(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test status field constraint"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Valid statuses should work
        valid_statuses = ["NOT_STARTED", "IN_PROGRESS", "COMPLETED", "SUBMITTED"]

        for i, status in enumerate(valid_statuses):
            # Create new content item for each test
            new_item = ContentItem(
                content_id=content_item.content_id,
                order_index=i + 1,
                text=f"Item {i + 1}",
            )
            test_db.add(new_item)
            test_db.flush()

            progress = StudentItemProgress(
                student_assignment_id=assignment.id,
                content_item_id=new_item.id,
                status=status,
            )
            test_db.add(progress)
            test_db.commit()
            assert progress.status == status

        # Invalid status should fail
        with pytest.raises(IntegrityError):
            invalid_item = ContentItem(
                content_id=content_item.content_id, order_index=99, text="Invalid item"
            )
            test_db.add(invalid_item)
            test_db.flush()

            progress = StudentItemProgress(
                student_assignment_id=assignment.id,
                content_item_id=invalid_item.id,
                status="INVALID_STATUS",
            )
            test_db.add(progress)
            test_db.commit()

    def test_student_item_progress_foreign_key_cascades(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test CASCADE DELETE for foreign keys"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Create progress record
        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            **self.progress_data,
        )
        test_db.add(progress)
        test_db.commit()

        progress_id = progress.id

        # Delete content_item should cascade delete progress
        test_db.delete(content_item)
        test_db.commit()

        # Verify progress is deleted
        deleted_progress = (
            test_db.query(StudentItemProgress).filter_by(id=progress_id).first()
        )
        assert deleted_progress is None

        # Reset and test assignment deletion
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            **self.progress_data,
        )
        test_db.add(progress)
        test_db.commit()

        progress_id = progress.id

        # Delete assignment should cascade delete progress
        test_db.delete(assignment)
        test_db.commit()

        # Verify progress is deleted
        deleted_progress = (
            test_db.query(StudentItemProgress).filter_by(id=progress_id).first()
        )
        assert deleted_progress is None

    def test_student_item_progress_relationships(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test relationships with other models"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            **self.progress_data,
        )
        test_db.add(progress)
        test_db.commit()

        # Test accessing related assignment
        assert progress.student_assignment.id == assignment.id
        assert progress.student_assignment.student_id == test_student.id
        assert progress.student_assignment.teacher_id == test_teacher.id

        # Test accessing related content item
        assert progress.content_item.id == content_item.id
        assert progress.content_item.text == "Hello world"
        assert progress.content_item.translation == "你好世界"

    def test_student_item_progress_score_precision(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test that score fields maintain precision"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        # Test with precise decimal values
        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            accuracy_score=Decimal("87.65"),
            fluency_score=Decimal("92.34"),
            pronunciation_score=Decimal("95.12"),
        )
        test_db.add(progress)
        test_db.commit()

        # Verify precision is maintained
        assert progress.accuracy_score == Decimal("87.65")
        assert progress.fluency_score == Decimal("92.34")
        assert progress.pronunciation_score == Decimal("95.12")

        # Test with edge cases
        progress.accuracy_score = Decimal("0.00")
        progress.fluency_score = Decimal("100.00")
        test_db.commit()

        assert progress.accuracy_score == Decimal("0.00")
        assert progress.fluency_score == Decimal("100.00")

    def test_student_item_progress_timestamps(
        self, test_db: Session, test_teacher: User, test_student: User
    ):
        """Test timestamp handling"""
        assignment, content_item = self.create_test_setup(
            test_db, test_teacher, test_student
        )

        progress = StudentItemProgress(
            student_assignment_id=assignment.id,
            content_item_id=content_item.id,
            status="IN_PROGRESS",
        )
        test_db.add(progress)
        test_db.commit()

        # Check initial timestamps
        created_at = progress.created_at
        updated_at = progress.updated_at
        assert created_at is not None
        assert updated_at is not None

        # Update progress with submission
        progress.status = "SUBMITTED"
        progress.submitted_at = datetime.utcnow()
        test_db.commit()

        # Verify submitted_at is set and updated_at changed
        test_db.refresh(progress)
        assert progress.submitted_at is not None
        assert progress.updated_at > updated_at

        # Update with AI assessment
        old_updated_at = progress.updated_at
        progress.accuracy_score = Decimal("88.5")
        progress.ai_assessed_at = datetime.utcnow()
        test_db.commit()

        # Verify ai_assessed_at is set and updated_at changed again
        test_db.refresh(progress)
        assert progress.ai_assessed_at is not None
        assert progress.updated_at > old_updated_at
