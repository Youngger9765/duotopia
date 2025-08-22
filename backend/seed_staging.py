#!/usr/bin/env python
"""
Staging-specific seed data
Minimal test data for QA and demos
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models
from auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

def create_staging_data(db: Session):
    """Create minimal test data for staging environment"""
    
    logger.info("🌱 Creating staging test data...")
    
    # Create one school
    school = models.School(
        id=str(uuid.uuid4()),
        name="Duotopia Demo School",
        code="DEMO",
        address="Taipei, Taiwan",
        phone="02-2700-0000"
    )
    db.add(school)
    db.commit()
    
    # Create demo teacher
    teacher = models.User(
        id=str(uuid.uuid4()),
        email="demo@duotopia.com",
        full_name="Demo Teacher",
        hashed_password=get_password_hash("DemoTeacher2024"),
        role=models.UserRole.TEACHER,
        is_active=True
    )
    db.add(teacher)
    db.commit()
    
    # Create one classroom
    classroom = models.Classroom(
        id=str(uuid.uuid4()),
        name="Demo Class",
        grade_level="6",
        teacher_id=teacher.id,
        school_id=school.id
    )
    db.add(classroom)
    db.commit()
    
    # Create 5 demo students
    students = []
    for i in range(1, 6):
        student = models.Student(
            id=str(uuid.uuid4()),
            email=f"student{i}@demo.duotopia.com",
            full_name=f"Demo Student {i}",
            birth_date="20100101",  # Easy to remember: 2010-01-01
            parent_email=f"parent{i}@demo.duotopia.com",
            parent_phone=f"0912345{670+i}",
            is_active=True
        )
        students.append(student)
        db.add(student)
        
        # Add to classroom
        classroom_student = models.ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student.id
        )
        db.add(classroom_student)
    
    db.commit()
    
    # Create one demo course
    course = models.Course(
        id=str(uuid.uuid4()),
        title="Demo English Course",
        description="A demonstration course for testing",
        course_code="DEMO101",
        grade_level=6,
        subject="English",
        max_students=30,
        difficulty_level=models.DifficultyLevel.A1,
        created_by=teacher.id,
        is_active=True
    )
    db.add(course)
    db.commit()
    
    # Assign course to classroom
    mapping = models.ClassroomCourseMapping(
        classroom_id=classroom.id,
        course_id=course.id
    )
    db.add(mapping)
    db.commit()
    
    # Create 2 demo lessons
    activity_types = [
        models.ActivityType.READING_ASSESSMENT,
        models.ActivityType.SPEAKING_PRACTICE
    ]
    
    for i, activity_type in enumerate(activity_types, 1):
        lesson = models.Lesson(
            id=str(uuid.uuid4()),
            course_id=course.id,
            lesson_number=i,
            title=f"Demo Lesson {i}",
            activity_type=activity_type,
            content={
                "type": "demo",
                "instructions": f"This is demo lesson {i}",
                "text": "Hello, world! This is a demo lesson."
            },
            time_limit_minutes=30,
            is_active=True
        )
        db.add(lesson)
    
    db.commit()
    
    logger.info("✅ Staging data created successfully!")
    logger.info("\n📊 Staging Data Summary:")
    logger.info("  - 1 School")
    logger.info("  - 1 Teacher (demo@duotopia.com / DemoTeacher2024)")
    logger.info("  - 1 Classroom")
    logger.info("  - 5 Students (student1-5@demo.duotopia.com / 20100101)")
    logger.info("  - 1 Course")
    logger.info("  - 2 Lessons")