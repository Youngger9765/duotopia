"""
Onboarding Service - Create default data for new registered teachers

This service creates demo data when a teacher completes email verification:
1. A default class: "My First Class"
2. A demo student: Bruce (birthdate: 20120101)
3. A template course: "Welcome to Duotopia!"
4. A pre-assigned demo assignment with AI assessment results
"""

import logging
from datetime import datetime, date
from sqlalchemy.orm import Session

from models import (
    Teacher,
    Classroom,
    Student,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    StudentItemProgress,
    AssignmentStatus,
    ContentType,
    ProgramLevel,
)
from auth import get_password_hash

logger = logging.getLogger(__name__)


class OnboardingService:
    """Service to create default onboarding data for new teachers"""

    def __init__(self):
        pass

    def create_onboarding_data(self, db: Session, teacher: Teacher) -> bool:
        """
        Create complete onboarding data for a newly verified teacher.

        This creates:
        1. A default classroom
        2. A demo student
        3. A welcome course with content
        4. A pre-assigned demo assignment with AI results

        Args:
            db: Database session
            teacher: The teacher who just verified their email

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if onboarding data already exists (idempotency)
            existing_classroom = (
                db.query(Classroom)
                .filter(
                    Classroom.teacher_id == teacher.id,
                    Classroom.name == "My First Class",
                )
                .first()
            )

            if existing_classroom:
                logger.info(
                    f"Onboarding data already exists for teacher {teacher.id}, skipping"
                )
                return True

            # 1. Create default classroom
            classroom = self._create_default_classroom(db, teacher)

            # 2. Create demo student
            student = self._create_demo_student(db, teacher)

            # 3. Enroll student in classroom
            self._enroll_student(db, classroom, student)

            # 4. Create welcome course
            program = self._create_welcome_course(db, teacher, classroom)

            # 5. Create and assign demo assignment with AI results
            self._create_demo_assignment(db, teacher, classroom, program, student)

            db.commit()
            logger.info(
                f"Successfully created onboarding data for teacher {teacher.id}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to create onboarding data for teacher {teacher.id}: {str(e)}"
            )
            db.rollback()
            return False

    def _create_default_classroom(self, db: Session, teacher: Teacher) -> Classroom:
        """Create the default 'My First Class' classroom"""
        classroom = Classroom(
            name="My First Class",
            description="Your first classroom on Duotopia! Start exploring here.",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()  # Get the ID
        logger.info(
            f"Created classroom '{classroom.name}' (ID: {classroom.id}) for teacher {teacher.id}"
        )
        return classroom

    def _create_demo_student(self, db: Session, teacher: Teacher) -> Student:
        """Create demo student 'Bruce' with birthdate 20120101"""
        # Password is birthdate: 20120101
        birthdate = date(2012, 1, 1)
        default_password = "20120101"

        student = Student(
            name="Bruce",
            student_number="DEMO001",
            email=None,  # No email for demo student
            password_hash=get_password_hash(default_password),
            birthdate=birthdate,
            password_changed=False,
            email_verified=False,
            is_active=True,
            target_wpm=80,
            target_accuracy=0.8,
        )
        db.add(student)
        db.flush()
        logger.info(f"Created demo student 'Bruce' (ID: {student.id})")
        return student

    def _enroll_student(
        self, db: Session, classroom: Classroom, student: Student
    ) -> ClassroomStudent:
        """Enroll student in classroom"""
        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id,
            is_active=True,
        )
        db.add(enrollment)
        db.flush()
        logger.info(f"Enrolled student {student.id} in classroom {classroom.id}")
        return enrollment

    def _create_welcome_course(
        self, db: Session, teacher: Teacher, classroom: Classroom
    ) -> Program:
        """
        Create welcome course: 'Welcome to Duotopia!'
        With unit 'Hello, teacher!' and content 'Your First Try!'
        """
        # Create Program (Course)
        program = Program(
            name="Welcome to Duotopia!",
            description="Your first course to help you understand how Duotopia works",
            level=ProgramLevel.A1,
            is_template=False,
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            source_type="custom",
            source_metadata={"created_by": "onboarding"},
            is_active=True,
            order_index=1,
        )
        db.add(program)
        db.flush()
        logger.info(f"Created program '{program.name}' (ID: {program.id})")

        # Create Lesson (Unit)
        lesson = Lesson(
            program_id=program.id,
            name="Hello, teacher!",
            description="Your first lesson to get started",
            order_index=0,
            estimated_minutes=5,
            is_active=True,
        )
        db.add(lesson)
        db.flush()
        logger.info(f"Created lesson '{lesson.name}' (ID: {lesson.id})")

        # Create Content (Reading Assessment)
        content = Content(
            lesson_id=lesson.id,
            type=ContentType.READING_ASSESSMENT,
            title="Your First Try!",
            order_index=0,
            is_active=True,
            target_wpm=80,
            target_accuracy=0.8,
            time_limit_seconds=120,
            level="A1",
            tags=["onboarding", "demo"],
            is_public=False,
            is_assignment_copy=False,
        )
        db.add(content)
        db.flush()
        logger.info(f"Created content '{content.title}' (ID: {content.id})")

        # Create 3 ContentItems (Questions)
        questions = [
            {
                "text": "Hello, teachers!",
                "translation": "老師們好！",
                "audio_url": None,  # Will be generated later if needed
            },
            {
                "text": "Nice to see you on Duotopia.",
                "translation": "很高興在 Duotopia 見到您。",
                "audio_url": None,
            },
            {
                "text": 'Use only "a" second to grade assignments then get your free time!',
                "translation": "只需「一」秒鐘批改作業，然後獲得您的自由時間！",
                "audio_url": None,
            },
        ]

        for idx, q in enumerate(questions):
            item = ContentItem(
                content_id=content.id,
                order_index=idx,
                text=q["text"],
                translation=q["translation"],
                audio_url=q["audio_url"],
                item_metadata={},
            )
            db.add(item)

        db.flush()
        logger.info(f"Created 3 content items for content {content.id}")

        return program

    def _create_demo_assignment(
        self,
        db: Session,
        teacher: Teacher,
        classroom: Classroom,
        program: Program,
        student: Student,
    ) -> Assignment:
        """
        Create demo assignment 'Now give it a try!' with pre-filled AI assessment results.
        Status should be SUBMITTED.
        """
        # Get the content we just created
        lesson = program.lessons[0] if program.lessons else None
        if not lesson:
            raise ValueError("No lesson found in program")

        content = lesson.contents[0] if lesson.contents else None
        if not content:
            raise ValueError("No content found in lesson")

        # Create Assignment
        now = datetime.utcnow()
        assignment = Assignment(
            title="Now give it a try!",
            description="自己當學生試試看",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            due_date=None,  # No deadline
            created_at=now,
            is_active=True,
        )
        db.add(assignment)
        db.flush()
        logger.info(f"Created assignment '{assignment.title}' (ID: {assignment.id})")

        # Link assignment to content
        assignment_content = AssignmentContent(
            assignment_id=assignment.id,
            content_id=content.id,
            order_index=0,
        )
        db.add(assignment_content)
        db.flush()

        # Create StudentAssignment (already submitted)
        student_assignment = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title=assignment.title,
            instructions=assignment.description,
            due_date=assignment.due_date,
            status=AssignmentStatus.SUBMITTED,
            assigned_at=now,
            started_at=now,
            submitted_at=now,
            is_active=True,
        )
        db.add(student_assignment)
        db.flush()
        logger.info(
            f"Created student assignment (ID: {student_assignment.id}) in SUBMITTED status"
        )

        # Create StudentItemProgress with AI assessment results for each content item
        content_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == content.id)
            .order_by(ContentItem.order_index)
            .all()
        )

        # Simulated AI assessment scores (good performance to encourage teacher)
        ai_scores = [
            {
                "accuracy_score": 95.0,
                "fluency_score": 88.0,
                "pronunciation_score": 92.0,
                "completeness_score": 100.0,
                "feedback": "Excellent pronunciation and fluency! Very clear delivery.",
            },
            {
                "accuracy_score": 90.0,
                "fluency_score": 85.0,
                "pronunciation_score": 88.0,
                "completeness_score": 100.0,
                "feedback": "Great job! Natural rhythm and good word stress.",
            },
            {
                "accuracy_score": 87.0,
                "fluency_score": 82.0,
                "pronunciation_score": 85.0,
                "completeness_score": 100.0,
                "feedback": "Well done! A longer sentence handled confidently.",
            },
        ]

        for idx, item in enumerate(content_items):
            scores = ai_scores[idx] if idx < len(ai_scores) else ai_scores[0]

            progress = StudentItemProgress(
                student_assignment_id=student_assignment.id,
                content_item_id=item.id,
                recording_url=None,  # Demo - no actual recording
                answer_text=item.text,  # Simulated perfect transcription
                transcription=item.text,
                submitted_at=now,
                accuracy_score=scores["accuracy_score"],
                fluency_score=scores["fluency_score"],
                pronunciation_score=scores["pronunciation_score"],
                completeness_score=scores["completeness_score"],
                ai_feedback=scores["feedback"],
                ai_assessed_at=now,
                status="COMPLETED",
                attempts=1,
            )
            db.add(progress)

        db.flush()
        logger.info(
            f"Created {len(content_items)} student item progress records with AI assessments"
        )

        return assignment


# Singleton instance
onboarding_service = OnboardingService()
