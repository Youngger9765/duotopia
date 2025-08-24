#!/usr/bin/env python
"""
Complete seed script that ensures ALL teachers have classrooms, students, and courses
"""
import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from auth import get_password_hash

def create_complete_data(db: Session):
    """Create complete test data with proper relationships"""
    
    print("🌱 Starting complete database seed...")
    
    # Clear existing data in correct order
    print("🗑️  Clearing existing data...")
    db.query(models.ActivityResult).delete()
    db.query(models.StudentAssignment).delete()
    db.query(models.Lesson).delete()
    db.query(models.Enrollment).delete()
    db.query(models.ClassroomCourseMapping).delete()
    db.query(models.Student).delete()
    db.query(models.Course).delete()
    db.query(models.Class).delete()
    db.query(models.User).delete()
    db.query(models.School).delete()
    db.commit()
    
    # Create schools
    print("🏫 Creating schools...")
    schools = []
    school_data = [
        {"name": "台北市立大安國小", "code": "DAAN", "address": "台北市大安區信義路三段", "contact_phone": "02-2700-1234"},
        {"name": "新北市立永和國中", "code": "YONGHE", "address": "新北市永和區中正路", "contact_phone": "02-2923-4567"},
        {"name": "桃園市立中壢高中", "code": "ZHONGLI", "address": "桃園市中壢區中央路", "contact_phone": "03-422-8901"},
    ]
    
    for data in school_data:
        school = models.School(
            id=str(uuid.uuid4()),
            **data
        )
        schools.append(school)
        db.add(school)
    
    db.commit()
    
    # Create ALL teachers
    print("👩‍🏫 Creating teachers and admins...")
    teachers = []
    teacher_data = [
        {"email": "teacher1@duotopia.com", "full_name": "王老師", "role": models.UserRole.TEACHER},
        {"email": "teacher2@duotopia.com", "full_name": "李老師", "role": models.UserRole.TEACHER},
        {"email": "teacher3@duotopia.com", "full_name": "張老師", "role": models.UserRole.TEACHER},
        {"email": "admin@duotopia.com", "full_name": "系統管理員", "role": models.UserRole.ADMIN},
        {"email": "teacher@individual.com", "full_name": "個體戶老師", "role": models.UserRole.TEACHER, 
         "password": "test123", "is_individual_teacher": True},
        {"email": "admin@institution.com", "full_name": "機構管理員", "role": models.UserRole.ADMIN, 
         "password": "test123", "is_institutional_admin": True},
        {"email": "hybrid@test.com", "full_name": "雙重身份用戶", "role": models.UserRole.TEACHER, 
         "password": "test123", "is_individual_teacher": True, "is_institutional_admin": True},
    ]
    
    for data in teacher_data:
        password = data.get("password", "password123")
        
        teacher = models.User(
            id=str(uuid.uuid4()),
            email=data["email"],
            full_name=data["full_name"],
            hashed_password=get_password_hash(password),
            role=data.get("role", models.UserRole.TEACHER),
            is_active=True,
            is_individual_teacher=data.get("is_individual_teacher", False),
            is_institutional_admin=data.get("is_institutional_admin", False),
            current_role_context="individual" if data.get("is_individual_teacher") else "institutional"
        )
        
        # Assign to a school (except pure individual teachers)
        if not data.get("is_individual_teacher") or data.get("is_institutional_admin"):
            teacher.school_id = random.choice(schools).id
            
        teachers.append(teacher)
        db.add(teacher)
    
    db.commit()
    
    # Create classrooms - ENSURE EVERY TEACHER HAS AT LEAST ONE
    print("🎓 Creating classrooms for ALL teachers...")
    classrooms = []
    grade_levels = ["1年級", "2年級", "3年級", "4年級", "5年級", "6年級"]
    
    # First, make sure EVERY teacher has at least one classroom
    for teacher in teachers:
        if teacher.role == models.UserRole.TEACHER or \
           (teacher.role == models.UserRole.ADMIN and teacher.is_individual_teacher):
            
            # Individual teachers don't need school_id
            school_id = None if teacher.is_individual_teacher and not teacher.is_institutional_admin else (teacher.school_id or random.choice(schools).id)
            
            classroom = models.Class(
                id=str(uuid.uuid4()),
                name=f"{teacher.full_name}的班級 A",
                grade=random.choice(grade_levels),
                school_id=school_id,
                teacher_id=teacher.id,
                academic_year="2024",
                is_active=True
            )
            db.add(classroom)
            classrooms.append(classroom)
            
            # Give some teachers a second classroom
            if random.random() > 0.5:
                classroom2 = models.Class(
                    id=str(uuid.uuid4()),
                    name=f"{teacher.full_name}的班級 B",
                    grade=random.choice(grade_levels),
                    school_id=school_id,
                    teacher_id=teacher.id,
                    academic_year="2024",
                    is_active=True
                )
                db.add(classroom2)
                classrooms.append(classroom2)
    
    db.commit()
    print(f"  ✓ Created {len(classrooms)} classrooms for {len(teachers)} teachers")
    
    # Create students
    print("👦 Creating students...")
    students = []
    student_names = [
        "陳小明", "林小華", "黃小美", "張小強", "李小玲",
        "王小寶", "劉小芳", "吳小偉", "蔡小雯", "楊小杰",
        "許小婷", "鄭小龍", "謝小慧", "洪小文", "邱小君",
        "賴小安", "周小平", "徐小靜", "馬小光", "何小珍"
    ]
    
    # Distribute students across all classrooms
    for i, name in enumerate(student_names):
        classroom = classrooms[i % len(classrooms)]
        
        student = models.Student(
            id=str(uuid.uuid4()),
            email=f"student{i+1}@duotopia.com",
            name=name,
            birth_date="20090828",  # YYYYMMDD format
            grade=classroom.grade,
            parent_name=f"{name}的家長",
            parent_phone=f"09{random.randint(10000000, 99999999)}",
            school_id=classroom.school_id,
            class_id=classroom.id,
            is_active=True
        )
        students.append(student)
        db.add(student)
    
    # Add more students to ensure each classroom has at least 3
    extra_student_count = len(students)
    for classroom in classrooms:
        # Check how many students this classroom has
        classroom_students = [s for s in students if s.class_id == classroom.id]
        while len(classroom_students) < 3:
            extra_student_count += 1
            student = models.Student(
                id=str(uuid.uuid4()),
                email=f"student{extra_student_count}@duotopia.com",
                name=f"學生{extra_student_count}",
                birth_date="20090828",
                grade=classroom.grade,
                parent_name=f"學生{extra_student_count}的家長",
                parent_phone=f"09{random.randint(10000000, 99999999)}",
                school_id=classroom.school_id,
                class_id=classroom.id,
                is_active=True
            )
            students.append(student)
            db.add(student)
            classroom_students.append(student)
    
    db.commit()
    print(f"  ✓ Created {len(students)} students")
    
    # Create courses - ENSURE EVERY TEACHER HAS COURSES
    print("📚 Creating courses for ALL teachers...")
    courses = []
    course_templates = [
        {
            "title": "基礎英語會話",
            "description": "培養日常英語對話能力",
            "difficulty_level": models.DifficultyLevel.A1,
        },
        {
            "title": "進階閱讀理解", 
            "description": "提升英文閱讀理解與分析能力",
            "difficulty_level": models.DifficultyLevel.B1,
        },
        {
            "title": "英語聽力訓練",
            "description": "加強英語聽力理解能力",
            "difficulty_level": models.DifficultyLevel.A2,
        },
        {
            "title": "創意寫作基礎",
            "description": "學習基本英文寫作技巧",
            "difficulty_level": models.DifficultyLevel.A1,
        },
        {
            "title": "生活英語",
            "description": "學習日常生活中的實用英語",
            "difficulty_level": models.DifficultyLevel.PRE_A,
        }
    ]
    
    # Each teacher creates 2-3 courses
    for teacher in teachers:
        if teacher.role == models.UserRole.TEACHER or \
           (teacher.role == models.UserRole.ADMIN and teacher.is_individual_teacher):
            
            num_courses = random.randint(2, 3)
            teacher_templates = random.sample(course_templates, num_courses)
            
            for template in teacher_templates:
                course = models.Course(
                    id=str(uuid.uuid4()),
                    title=f"{template['title']} ({teacher.full_name})",
                    description=template["description"],
                    difficulty_level=template["difficulty_level"],
                    creator_id=teacher.id,
                    school_id=teacher.school_id,
                    is_public=teacher.is_individual_teacher,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                courses.append(course)
                db.add(course)
    
    db.commit()
    print(f"  ✓ Created {len(courses)} courses")
    
    # Assign courses to classrooms
    print("🔗 Assigning courses to classrooms...")
    for classroom in classrooms:
        # Get courses created by the classroom's teacher
        teacher_courses = [c for c in courses if c.creator_id == classroom.teacher_id]
        
        # If teacher has no courses, use random courses
        if not teacher_courses:
            teacher_courses = random.sample(courses, min(2, len(courses)))
        
        # Assign 1-2 courses to each classroom
        selected_courses = random.sample(teacher_courses, min(random.randint(1, 2), len(teacher_courses)))
        
        for course in selected_courses:
            mapping = models.ClassCourseMapping(
                id=str(uuid.uuid4()),
                class_id=classroom.id,
                course_id=course.id,
                assigned_at=datetime.utcnow()
            )
            db.add(mapping)
            
            # Also enroll all students in the classroom to the course
            classroom_students = [s for s in students if s.class_id == classroom.id]
            for student in classroom_students:
                enrollment = models.Enrollment(
                    id=str(uuid.uuid4()),
                    student_id=student.id,
                    course_id=course.id,
                    enrolled_at=datetime.utcnow()
                )
                db.add(enrollment)
    
    db.commit()
    
    # Create lessons
    print("📖 Creating lessons...")
    lessons = []
    activity_types = [
        models.ActivityType.READING_ASSESSMENT,
        models.ActivityType.SPEAKING_PRACTICE,
        models.ActivityType.LISTENING_CLOZE,
        models.ActivityType.SENTENCE_MAKING,
        models.ActivityType.SPEAKING_QUIZ,
        models.ActivityType.SPEAKING_SCENARIO
    ]
    
    for course in courses:
        # Create 3-5 lessons per course
        num_lessons = random.randint(3, 5)
        for i in range(num_lessons):
            lesson = models.Lesson(
                id=str(uuid.uuid4()),
                course_id=course.id,
                lesson_number=i+1,
                title=f"第 {i+1} 課",
                activity_type=random.choice(activity_types),
                content={
                    "type": "reading_practice",
                    "items": [
                        {
                            "id": f"item-{j+1}",
                            "text": f"Practice sentence {j+1}",
                            "order": j
                        } for j in range(3)
                    ]
                },
                time_limit_minutes=30,
                is_active=True,
                created_at=datetime.utcnow()
            )
            lessons.append(lesson)
            db.add(lesson)
    
    db.commit()
    
    # Create assignments
    print("📝 Creating assignments...")
    assignment_count = 0
    for classroom in classrooms:
        # Get courses for this classroom
        classroom_mappings = db.query(models.ClassCourseMapping).filter_by(class_id=classroom.id).all()
        
        for mapping in classroom_mappings:
            # Get lessons for this course
            course_lessons = [l for l in lessons if l.course_id == mapping.course_id]
            
            # Get students in this classroom
            classroom_students = [s for s in students if s.class_id == classroom.id]
            
            # Create assignments for first 2 lessons
            for lesson in course_lessons[:2]:
                for student in classroom_students:
                    assignment = models.StudentAssignment(
                        id=str(uuid.uuid4()),
                        student_id=student.id,
                        lesson_id=lesson.id,
                        assigned_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
                        due_date=datetime.utcnow() + timedelta(days=random.randint(7, 14)),
                        status=random.choice(["pending", "in_progress", "completed"]),
                    )
                    db.add(assignment)
                    assignment_count += 1
    
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
    print(f"  - Assignments: {assignment_count}")
    
    print("\n🔑 Test Accounts:")
    print("  Teachers:")
    for teacher in teachers:
        password = "test123" if teacher.email in ["teacher@individual.com", "admin@institution.com", "hybrid@test.com"] else "password123"
        print(f"    - Email: {teacher.email}, Password: {password}, Classrooms: {len([c for c in classrooms if c.teacher_id == teacher.id])}")
    
    print("\n  Students (first 5):")
    for i in range(min(5, len(students))):
        print(f"    - Email: {students[i].email}, Birth Date: 2009-08-28")
    print(f"  ... and {len(students) - 5} more students")

def main():
    """Main function to run the seed script"""
    db = SessionLocal()
    try:
        create_complete_data(db)
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()