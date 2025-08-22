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
    
    # Create schools
    schools = []
    
    # School for institutional users
    institution_school = models.School(
        id=str(uuid.uuid4()),
        name="陽光語言學院",
        code="SUNSHINE",
        address="台北市大安區和平東路",
        phone="02-2700-1111"
    )
    schools.append(institution_school)
    db.add(institution_school)
    
    # School for hybrid user
    hybrid_school = models.School(
        id=str(uuid.uuid4()),
        name="快樂學習中心",
        code="HAPPY",
        address="新北市板橋區文化路",
        phone="02-2960-2222"
    )
    schools.append(hybrid_school)
    db.add(hybrid_school)
    
    db.commit()
    
    # Create test users based on frontend login page
    teachers = []
    
    # 1. Individual teacher (個體戶教師)
    individual_teacher = models.User(
        id=str(uuid.uuid4()),
        email="teacher@individual.com",
        full_name="個體戶老師",
        hashed_password=get_password_hash("test123"),
        role=models.UserRole.TEACHER,
        is_active=True
    )
    teachers.append(individual_teacher)
    db.add(individual_teacher)
    
    # 2. Institution admin (機構管理員)
    institution_admin = models.User(
        id=str(uuid.uuid4()),
        email="admin@institution.com",
        full_name="機構管理員",
        hashed_password=get_password_hash("test123"),
        role=models.UserRole.ADMIN,
        is_active=True
    )
    teachers.append(institution_admin)
    db.add(institution_admin)
    
    # 3. Hybrid user (雙重身份 - both admin and teacher)
    hybrid_user = models.User(
        id=str(uuid.uuid4()),
        email="hybrid@test.com",
        full_name="雙重身份用戶",
        hashed_password=get_password_hash("test123"),
        role=models.UserRole.ADMIN,  # Primary role
        is_active=True
    )
    teachers.append(hybrid_user)
    db.add(hybrid_user)
    
    db.commit()
    
    # Create classrooms
    classrooms = []
    
    # Classroom for individual teacher
    individual_classroom = models.Classroom(
        id=str(uuid.uuid4()),
        name="個體戶小班",
        grade_level="6",
        teacher_id=individual_teacher.id,
        school_id=None  # Individual teacher doesn't belong to a school
    )
    classrooms.append(individual_classroom)
    db.add(individual_classroom)
    
    # Classrooms for institution
    institution_classroom1 = models.Classroom(
        id=str(uuid.uuid4()),
        name="陽光一班",
        grade_level="5",
        teacher_id=institution_admin.id,  # Admin can also be a teacher
        school_id=institution_school.id
    )
    classrooms.append(institution_classroom1)
    db.add(institution_classroom1)
    
    institution_classroom2 = models.Classroom(
        id=str(uuid.uuid4()),
        name="陽光二班",
        grade_level="6",
        teacher_id=institution_admin.id,
        school_id=institution_school.id
    )
    classrooms.append(institution_classroom2)
    db.add(institution_classroom2)
    
    # Classroom for hybrid user
    hybrid_classroom = models.Classroom(
        id=str(uuid.uuid4()),
        name="快樂英語班",
        grade_level="6",
        teacher_id=hybrid_user.id,
        school_id=hybrid_school.id
    )
    classrooms.append(hybrid_classroom)
    db.add(hybrid_classroom)
    
    db.commit()
    
    # Create students for each classroom
    students = []
    student_names = ["陳小明", "林小華", "黃美美", "張小強", "李小玲", "王小寶", "劉小芳", "吳小偉"]
    
    # Students for individual teacher (3 students)
    for i in range(1, 4):
        student = models.Student(
            id=str(uuid.uuid4()),
            email=f"student{i}@individual.com",
            full_name=student_names[i-1],
            birth_date="20100101",  # Easy to remember: 2010-01-01
            parent_email=f"parent{i}@individual.com",
            parent_phone=f"0912345{670+i}",
            is_active=True
        )
        students.append(student)
        db.add(student)
        
        # Add to individual classroom
        classroom_student = models.ClassroomStudent(
            classroom_id=individual_classroom.id,
            student_id=student.id
        )
        db.add(classroom_student)
    
    # Students for institution classrooms (5 students each)
    student_counter = 4
    for classroom in [institution_classroom1, institution_classroom2]:
        for j in range(2):  # 2 students per classroom
            student = models.Student(
                id=str(uuid.uuid4()),
                email=f"student{student_counter}@sunshine.com",
                full_name=student_names[student_counter-1] if student_counter <= len(student_names) else f"學生{student_counter}",
                birth_date="20100101",
                parent_email=f"parent{student_counter}@sunshine.com",
                parent_phone=f"0912345{670+student_counter}",
                is_active=True
            )
            students.append(student)
            db.add(student)
            
            classroom_student = models.ClassroomStudent(
                classroom_id=classroom.id,
                student_id=student.id
            )
            db.add(classroom_student)
            student_counter += 1
    
    # Students for hybrid classroom (3 students)
    for k in range(1, 4):
        student = models.Student(
            id=str(uuid.uuid4()),
            email=f"student{k}@happy.com",
            full_name=f"快樂學生{k}",
            birth_date="20100101",
            parent_email=f"parent{k}@happy.com",
            parent_phone=f"0922345{670+k}",
            is_active=True
        )
        students.append(student)
        db.add(student)
        
        classroom_student = models.ClassroomStudent(
            classroom_id=hybrid_classroom.id,
            student_id=student.id
        )
        db.add(classroom_student)
    
    db.commit()
    
    # Create courses for different teachers
    courses = []
    
    # Course for individual teacher
    individual_course = models.Course(
        id=str(uuid.uuid4()),
        title="個人英語家教班",
        description="一對一或小班制的個人化英語教學",
        course_code="IND101",
        grade_level=6,
        subject="English",
        max_students=5,
        difficulty_level=models.DifficultyLevel.A1,
        created_by=individual_teacher.id,
        is_active=True
    )
    courses.append(individual_course)
    db.add(individual_course)
    
    # Courses for institution
    institution_course1 = models.Course(
        id=str(uuid.uuid4()),
        title="陽光基礎英語",
        description="適合初學者的基礎英語課程",
        course_code="SUN101",
        grade_level=5,
        subject="English",
        max_students=20,
        difficulty_level=models.DifficultyLevel.A1,
        created_by=institution_admin.id,
        is_active=True
    )
    courses.append(institution_course1)
    db.add(institution_course1)
    
    institution_course2 = models.Course(
        id=str(uuid.uuid4()),
        title="陽光進階會話",
        description="提升口語表達能力的進階課程",
        course_code="SUN201",
        grade_level=6,
        subject="English",
        max_students=20,
        difficulty_level=models.DifficultyLevel.A2,
        created_by=institution_admin.id,
        is_active=True
    )
    courses.append(institution_course2)
    db.add(institution_course2)
    
    # Course for hybrid user
    hybrid_course = models.Course(
        id=str(uuid.uuid4()),
        title="快樂英語遊戲",
        description="透過遊戲和活動學習英語",
        course_code="HAPPY101",
        grade_level=6,
        subject="English",
        max_students=15,
        difficulty_level=models.DifficultyLevel.A1,
        created_by=hybrid_user.id,
        is_active=True
    )
    courses.append(hybrid_course)
    db.add(hybrid_course)
    
    db.commit()
    
    # Assign courses to classrooms
    # Individual classroom gets individual course
    mapping1 = models.ClassroomCourseMapping(
        classroom_id=individual_classroom.id,
        course_id=individual_course.id
    )
    db.add(mapping1)
    
    # Institution classrooms get institution courses
    mapping2 = models.ClassroomCourseMapping(
        classroom_id=institution_classroom1.id,
        course_id=institution_course1.id
    )
    db.add(mapping2)
    
    mapping3 = models.ClassroomCourseMapping(
        classroom_id=institution_classroom2.id,
        course_id=institution_course2.id
    )
    db.add(mapping3)
    
    # Hybrid classroom gets hybrid course
    mapping4 = models.ClassroomCourseMapping(
        classroom_id=hybrid_classroom.id,
        course_id=hybrid_course.id
    )
    db.add(mapping4)
    
    db.commit()
    
    # Create lessons for each course
    activity_types = [
        models.ActivityType.READING_ASSESSMENT,
        models.ActivityType.SPEAKING_PRACTICE
    ]
    
    for course in courses:
        for i, activity_type in enumerate(activity_types, 1):
            lesson = models.Lesson(
                id=str(uuid.uuid4()),
                course_id=course.id,
                lesson_number=i,
                title=f"{course.title} - Lesson {i}",
                activity_type=activity_type,
                content={
                    "type": "demo",
                    "instructions": f"這是 {course.title} 的第 {i} 課",
                    "text": "Welcome to this English lesson! Today we will practice speaking and reading."
                },
                time_limit_minutes=30,
                is_active=True
            )
            db.add(lesson)
    
    db.commit()
    
    logger.info("✅ Staging data created successfully!")
    logger.info("\n📊 Staging Data Summary:")
    logger.info(f"  - {len(schools)} Schools: 陽光語言學院, 快樂學習中心")
    logger.info(f"  - {len(teachers)} Teachers/Admins:")
    logger.info("    • teacher@individual.com / test123 (個體戶教師)")
    logger.info("    • admin@institution.com / test123 (機構管理員)")
    logger.info("    • hybrid@test.com / test123 (雙重身份)")
    logger.info(f"  - {len(classrooms)} Classrooms:")
    logger.info("    • 個體戶小班 (3 students)")
    logger.info("    • 陽光一班, 陽光二班 (4 students total)")
    logger.info("    • 快樂英語班 (3 students)")
    logger.info(f"  - {len(students)} Students (all use birth date: 20100101)")
    logger.info(f"  - {len(courses)} Courses")
    logger.info(f"  - {len(courses) * 2} Lessons")