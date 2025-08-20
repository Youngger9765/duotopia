#!/usr/bin/env python
"""
Seed script to populate the database with test data
Run with: python seed.py
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from auth import get_password_hash
import uuid
import random

def create_test_data(db: Session):
    """Create test data for development"""
    
    print("🌱 Starting database seed...")
    
    # Clear existing data
    print("🗑️  Clearing existing data...")
    db.query(models.ActivityResult).delete()
    db.query(models.StudentAssignment).delete()
    db.query(models.Lesson).delete()
    db.query(models.ClassroomCourseMapping).delete()
    db.query(models.ClassroomStudent).delete()
    db.query(models.Course).delete()
    db.query(models.Classroom).delete()
    db.query(models.Student).delete()
    db.query(models.User).delete()
    db.query(models.School).delete()
    db.commit()
    
    # Create schools/organizations
    print("🏫 Creating schools...")
    schools = []
    school_data = [
        {"name": "台北市立大安國小", "code": "DAAN", "address": "台北市大安區信義路三段", "phone": "02-2700-1234"},
        {"name": "新北市立永和國中", "code": "YONGHE", "address": "新北市永和區中正路", "phone": "02-2923-4567"},
        {"name": "桃園市立中壢高中", "code": "ZHONGLI", "address": "桃園市中壢區中央路", "phone": "03-422-8901"},
    ]
    
    for data in school_data:
        school = models.School(
            id=str(uuid.uuid4()),
            **data
        )
        schools.append(school)
        db.add(school)
    
    db.commit()
    
    # Create teachers
    print("👩‍🏫 Creating teachers...")
    teachers = []
    teacher_data = [
        {"email": "teacher1@duotopia.com", "full_name": "王老師", "role": models.UserRole.ADMIN},
        {"email": "teacher2@duotopia.com", "full_name": "李老師"},
        {"email": "teacher3@duotopia.com", "full_name": "張老師"},
        {"email": "admin@duotopia.com", "full_name": "系統管理員", "role": models.UserRole.ADMIN},
    ]
    
    for data in teacher_data:
        teacher = models.User(
            id=str(uuid.uuid4()),
            email=data["email"],
            full_name=data["full_name"],
            hashed_password=get_password_hash("password123"),  # Default password for all test users
            role=data.get("role", models.UserRole.TEACHER),
            is_active=True
        )
        teachers.append(teacher)
        db.add(teacher)
    
    db.commit()
    
    # Create classrooms
    print("🎓 Creating classrooms...")
    classrooms = []
    classroom_data = [
        {"name": "六年一班", "grade_level": "6", "teacher_id": teachers[0].id, "school_id": schools[0].id},
        {"name": "六年二班", "grade_level": "6", "teacher_id": teachers[0].id, "school_id": schools[0].id},
        {"name": "五年三班", "grade_level": "5", "teacher_id": teachers[1].id, "school_id": schools[0].id},
        {"name": "國一甲班", "grade_level": "7", "teacher_id": teachers[2].id, "school_id": schools[1].id},
    ]
    
    for data in classroom_data:
        classroom_obj = models.Classroom(
            id=str(uuid.uuid4()),
            **data
        )
        classrooms.append(classroom_obj)
        db.add(classroom_obj)
    
    db.commit()
    
    # Create students
    print("👦 Creating students...")
    students = []
    student_names = [
        "陳小明", "林小華", "黃小美", "張小強", "李小玲",
        "王小寶", "劉小芳", "吳小偉", "蔡小雯", "楊小杰",
        "許小婷", "鄭小龍", "謝小慧", "洪小文", "邱小君"
    ]
    
    for i, name in enumerate(student_names):
        # Randomly assign students to classrooms
        classroom_idx = random.randint(0, len(classrooms) - 1)
        birth_year = 2012 if classrooms[classroom_idx].grade_level == "6" else 2013
        
        # All students have the same birth date for easy testing
        birth_date = "20090828"
        
        student = models.Student(
            id=str(uuid.uuid4()),
            email=f"student{i+1}@duotopia.com",
            full_name=name,
            birth_date=birth_date,  # YYYYMMDD format
            parent_email=f"parent{i+1}@example.com",
            parent_phone=f"09{random.randint(10000000, 99999999)}",
            is_active=True
        )
        students.append(student)
        db.add(student)
        
        # Add student to classroom
        classroom_student = models.ClassroomStudent(
            classroom_id=classrooms[classroom_idx].id,
            student_id=student.id
        )
        db.add(classroom_student)
    
    db.commit()
    
    # Create courses
    print("📚 Creating courses...")
    courses = []
    course_data = [
        {
            "name": "基礎英語會話",
            "description": "培養日常英語對話能力",
            "difficulty_level": models.DifficultyLevel.A1,
            "tags": ["speaking", "conversation", "beginner"]
        },
        {
            "name": "進階閱讀理解",
            "description": "提升英文閱讀理解與分析能力",
            "difficulty_level": models.DifficultyLevel.B1,
            "tags": ["reading", "comprehension", "intermediate"]
        },
        {
            "name": "英語聽力訓練",
            "description": "加強英語聽力理解能力",
            "difficulty_level": models.DifficultyLevel.B1,
            "tags": ["listening", "comprehension"]
        },
        {
            "name": "創意寫作基礎",
            "description": "學習基本英文寫作技巧",
            "difficulty_level": models.DifficultyLevel.A1,
            "tags": ["writing", "creative", "beginner"]
        }
    ]
    
    for i, data in enumerate(course_data):
        course = models.Course(
            id=str(uuid.uuid4()),
            title=data["name"],
            description=data["description"],
            course_code=f"MATH{101 + i}",  # Generate course codes MATH101, MATH102, etc.
            grade_level=10,
            subject="Mathematics",
            max_students=30,
            difficulty_level=data["difficulty_level"],
            created_by=teachers[0].id,  # Created by first teacher
            is_active=True
        )
        courses.append(course)
        db.add(course)
    
    db.commit()
    
    # Assign courses to classrooms
    print("🔗 Assigning courses to classrooms...")
    for i, classroom_obj in enumerate(classrooms):
        # Each classroom gets 2-3 courses
        selected_courses = random.sample(courses, random.randint(2, 3))
        for course in selected_courses:
            mapping = models.ClassroomCourseMapping(
                classroom_id=classroom_obj.id,
                course_id=course.id
            )
            db.add(mapping)
    
    db.commit()
    
    # Create lessons
    print("📖 Creating lessons...")
    lessons = []
    for course in courses:
        # Create 3-5 lessons per course
        num_lessons = random.randint(3, 5)
        for i in range(num_lessons):
            lesson = models.Lesson(
                id=str(uuid.uuid4()),
                course_id=course.id,
                lesson_number=i+1,
                title=f"{course.title} - 第 {i+1} 課",
                activity_type=random.choice([
                    models.ActivityType.READING_ASSESSMENT,
                    models.ActivityType.SPEAKING_PRACTICE,
                    models.ActivityType.LISTENING_CLOZE,
                    models.ActivityType.SENTENCE_MAKING,
                    models.ActivityType.SPEAKING_QUIZ
                ]),
                content={
                    "type": "mixed",
                    "sections": [
                        {
                            "type": "reading",
                            "content": f"This is lesson {i+1} reading content for {course.title}."
                        },
                        {
                            "type": "vocabulary",
                            "words": ["apple", "book", "cat", "dog", "elephant"]
                        }
                    ]
                },
                time_limit_minutes=30,
                is_active=True
            )
            lessons.append(lesson)
            db.add(lesson)
    
    db.commit()
    
    # Create assignments
    print("📝 Creating assignments...")
    for classroom_obj in classrooms:
        # Get students in this classroom
        classroom_students = db.query(models.ClassroomStudent).filter_by(classroom_id=classroom_obj.id).all()
        
        # Get courses for this classroom
        classroom_courses = db.query(models.ClassroomCourseMapping).filter_by(classroom_id=classroom_obj.id).all()
        
        for mapping in classroom_courses:
            # Get lessons for this course
            course_lessons = [l for l in lessons if l.course_id == mapping.course_id]
            
            # Create assignment for first lesson
            if course_lessons:
                for student_mapping in classroom_students:
                    status = random.choice(["pending", "in_progress", "completed"])
                    assignment = models.StudentAssignment(
                        id=str(uuid.uuid4()),
                        student_id=student_mapping.student_id,
                        lesson_id=course_lessons[0].id,
                        assigned_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
                        due_date=datetime.utcnow() + timedelta(days=random.randint(7, 14)),
                        status=status,
                        completed_at=datetime.utcnow() if status == "completed" else None
                    )
                    db.add(assignment)
    
    db.commit()
    
    print("✅ Database seeded successfully!")
    print("\n📊 Summary:")
    print(f"  - Schools: {len(schools)}")
    print(f"  - Teachers: {len([t for t in teachers if t.role == models.UserRole.TEACHER])}")
    print(f"  - Admins: {len([t for t in teachers if t.role == models.UserRole.ADMIN])}")
    print(f"  - Classrooms: {len(classrooms)}")
    print(f"  - Students: {len(students)}")
    print(f"  - Courses: {len(courses)}")
    print(f"  - Lessons: {len(lessons)}")
    
    print("\n🔑 Test Accounts:")
    print("  Teachers:")
    for teacher in teachers:
        print(f"    - Email: {teacher.email}, Password: password123")
    print("\n  Students:")
    for i in range(min(5, len(students))):  # Show first 5 students
        birth_date_str = students[i].birth_date
        formatted_date = f"{birth_date_str[:4]}-{birth_date_str[4:6]}-{birth_date_str[6:8]}"
        print(f"    - Email: {students[i].email}, Birth Date: {formatted_date}")
    print("  ... and more students")

def main():
    """Main function to run the seed script"""
    db = SessionLocal()
    try:
        create_test_data(db)
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()