#!/usr/bin/env python3
"""
Demo Data Seeder for Duotopia
Seeds the database with comprehensive demo data extracted from frontend MOCK data
"""

from datetime import datetime, date
from database import SessionLocal, get_db
from models import (
    User, Student, School, Class, Course, ClassStudent, 
    ClassCourseMapping, StudentAssignment, Enrollment, Lesson
)
from passlib.context import CryptContext
import argparse

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def clear_all_data(db):
    """Clear all existing data from the database"""
    print("🗑️  Clearing existing data...")
    
    # Delete in reverse dependency order
    db.query(ClassCourseMapping).delete()
    db.query(ClassStudent).delete()
    db.query(StudentAssignment).delete()
    db.query(Lesson).delete()
    db.query(Enrollment).delete()
    db.query(Student).delete()
    db.query(Class).delete()
    db.query(Course).delete()
    db.query(User).delete()
    db.query(School).delete()
    
    db.commit()
    print("✅ All existing data cleared")

def seed_schools(db):
    """Seed schools/institutions data"""
    print("🏫 Seeding schools...")
    
    schools_data = [
        {
            "name": "台北總校",
            "code": "TP001",
            "address": "台北市中正區重慶南路一段122號",
            "phone": "02-2388-1234",
        },
        {
            "name": "新竹分校", 
            "code": "HC002",
            "address": "新竹市東區光復路二段101號",
            "phone": "03-571-2345",
        },
        {
            "name": "台中補習班",
            "code": "TC003",
            "address": "台中市西屯區台灣大道三段99號", 
            "phone": "04-2251-3456",
        }
    ]
    
    for school_data in schools_data:
        school = School(**school_data)
        db.add(school)
    
    db.commit()
    print(f"✅ Added {len(schools_data)} schools")

def seed_users(db):
    """Seed users (teachers/admin/staff) data"""
    print("👥 Seeding users...")
    
    # Get schools for reference
    schools = {school.name: school.id for school in db.query(School).all()}
    
    users_data = [
        # Admin users
        {
            "email": "admin@duotopia.com",
            "hashed_password": hash_password("admin123"),
            "full_name": "系統管理員",
            "role": "admin",
            "is_active": True
        },
        # Teachers from TeacherManagement mock data
        {
            "email": "teacher1@duotopia.com",
            "hashed_password": hash_password("teacher123"),
            "full_name": "王老師", 
            "role": "teacher",
            "is_active": True
        },
        {
            "email": "teacher2@duotopia.com",
            "hashed_password": hash_password("teacher123"),
            "full_name": "李老師",
            "role": "teacher", 
            "is_active": True
        },
        {
            "email": "teacher3@duotopia.com",
            "hashed_password": hash_password("teacher123"),
            "full_name": "張老師",
            "role": "teacher",
            "is_active": True
        },
        {
            "email": "teacher4@duotopia.com", 
            "hashed_password": hash_password("teacher123"),
            "full_name": "陳老師",
            "role": "teacher",
            "is_active": True
        },
        # Additional staff
        {
            "email": "wang.principal@duotopia.com",
            "hashed_password": hash_password("principal123"),
            "full_name": "王校長",
            "role": "admin",
            "is_active": True
        },
        {
            "email": "li.director@duotopia.com", 
            "hashed_password": hash_password("director123"),
            "full_name": "李主任",
            "role": "admin",
            "is_active": True
        },
        {
            "email": "zhang.teacher@duotopia.com",
            "hashed_password": hash_password("teacher123"),
            "full_name": "張老師",
            "role": "admin",
            "is_active": True
        }
    ]
    
    for user_data in users_data:
        user = User(**user_data)
        db.add(user)
    
    db.commit()
    print(f"✅ Added {len(users_data)} users")

def seed_classes(db):
    """Seed class data"""
    print("🎓 Seeding classes...")
    
    # Get schools and teachers for reference
    schools = {school.name: school.id for school in db.query(School).all()}
    teachers = {user.full_name: user.id for user in db.query(User).filter(User.role == "teacher").all()}
    
    classes_data = [
        {
            "name": "六年一班",
            "grade_level": "6",
            "difficulty_level": "intermediate",
            "school_id": schools["台北總校"],
            "teacher_id": teachers["王老師"]
        },
        {
            "name": "六年二班", 
            "grade_level": "6",
            "difficulty_level": "intermediate",
            "school_id": schools["台北總校"],
            "teacher_id": teachers["王老師"]
        },
        {
            "name": "五年三班",
            "grade_level": "5", 
            "difficulty_level": "beginner",
            "school_id": schools["新竹分校"],
            "teacher_id": teachers["李老師"]
        },
        {
            "name": "國一甲班",
            "grade_level": "7",
            "difficulty_level": "advanced",
            "school_id": schools["台中補習班"],
            "teacher_id": teachers["張老師"]
        }
    ]
    
    for class_data in classes_data:
        class_obj = Class(**class_data)
        db.add(class_obj)
    
    db.commit()
    print(f"✅ Added {len(classes_data)} classes")

def seed_students(db):
    """Seed student data"""
    print("👨‍🎓 Seeding students...")
    
    # Get schools and classes for reference
    schools = {school.name: school.id for school in db.query(School).all()}
    classes = {cls.name: cls.id for cls in db.query(Class).all()}
    
    students_data = [
        # Students from StudentManagement mock data
        {
            "email": "student1@duotopia.com",
            "full_name": "陳小明",
            "birth_date": "20090828",
            "phone_number": "0900-000-001",
            "grade": 6,
            "school": "台北總校"
        },
        {
            "email": "student2@duotopia.com",
            "full_name": "林小華", 
            "birth_date": "20090828",
            "phone_number": "0900-000-002",
            "grade": 6,
            "school": "台北總校"
        },
        {
            "email": "student3@duotopia.com",
            "full_name": "王小美",
            "birth_date": "20090828",
            "phone_number": "0900-000-003",
            "grade": 6,
            "school": "台北總校"
        },
        {
            "email": "student4@duotopia.com", 
            "full_name": "張小強",
            "birth_date": "20090828",
            "phone_number": "0900-000-004",
            "grade": 5,
            "school": "新竹分校"
        },
        {
            "email": "student5@duotopia.com",
            "full_name": "李小芳",
            "birth_date": "20090828",
            "phone_number": "0900-000-005",
            "grade": 5,
            "school": "新竹分校"
        },
        {
            "email": "student6@duotopia.com",
            "full_name": "黃小志",
            "birth_date": "20090828",
            "phone_number": "0900-000-006",
            "grade": 7,
            "school": "台中補習班"
        }
    ]
    
    for student_data in students_data:
        student = Student(**student_data)
        db.add(student)
    
    db.commit()
    print(f"✅ Added {len(students_data)} students")

def seed_courses(db):
    """Seed course data"""
    print("📚 Seeding courses...")
    
    # Get teachers for reference
    teachers = {user.full_name: user.id for user in db.query(User).filter(User.role == "teacher").all()}
    
    courses_data = [
        # From CourseManagement mock data
        {
            "title": "第一課 - 活動管理",
            "description": "學習基本的活動管理技巧",
            "course_code": "MGT101",
            "grade_level": 6,
            "subject": "管理",
            "difficulty_level": "beginner",
            "created_by": teachers["王老師"]
        },
        {
            "title": "聽力克漏字", 
            "description": "提升聽力理解能力",
            "course_code": "ENG201",
            "grade_level": 6,
            "subject": "英語",
            "difficulty_level": "intermediate",
            "created_by": teachers["王老師"]
        },
        {
            "title": "造句活動",
            "description": "練習句型結構與文法",
            "course_code": "ENG202",
            "grade_level": 5,
            "subject": "英語",
            "difficulty_level": "intermediate",
            "created_by": teachers["李老師"]
        },
        # Additional courses from ClassManagement
        {
            "title": "English Conversation 101",
            "description": "基礎英語會話課程",
            "course_code": "CONV101",
            "grade_level": 6,
            "subject": "英語會話",
            "difficulty_level": "beginner",
            "created_by": teachers["王老師"]
        },
        {
            "title": "Advanced Grammar",
            "description": "進階文法課程", 
            "course_code": "GRAM301",
            "grade_level": 6,
            "subject": "英語文法",
            "difficulty_level": "advanced",
            "created_by": teachers["王老師"]
        },
        {
            "title": "Business English",
            "description": "商業英語課程",
            "course_code": "BIZ201",
            "grade_level": 7,
            "subject": "商業英語",
            "difficulty_level": "advanced",
            "created_by": teachers["張老師"]
        },
        {
            "title": "Pronunciation Practice",
            "description": "發音練習課程",
            "course_code": "PRON101",
            "grade_level": 5,
            "subject": "發音",
            "difficulty_level": "intermediate",
            "created_by": teachers["李老師"]
        },
        {
            "title": "Writing Skills", 
            "description": "寫作技巧課程",
            "course_code": "WRIT201",
            "grade_level": 5,
            "subject": "寫作",
            "difficulty_level": "intermediate",
            "created_by": teachers["李老師"]
        },
        {
            "title": "Test Preparation",
            "description": "考試準備課程",
            "course_code": "TEST301",
            "grade_level": 7,
            "subject": "測驗",
            "difficulty_level": "advanced",
            "created_by": teachers["張老師"]
        }
    ]
    
    for course_data in courses_data:
        course = Course(**course_data)
        db.add(course)
    
    db.commit()
    print(f"✅ Added {len(courses_data)} courses")

def seed_lessons(db):
    """Seed lesson data"""
    print("📋 Seeding lessons...")
    
    # Get courses for reference
    courses = {course.title: course.id for course in db.query(Course).all()}
    
    lessons_data = [
        # From CourseManagement mock data
        {
            "title": "Unit 3 - Speaking Practice",
            "content": "錄音練習：課文朗讀與對話",
            "course_id": courses["第一課 - 活動管理"],
            "difficulty_level": "beginner",
            "activity_type": "speaking"
        },
        {
            "title": "Reading Comprehension Test",
            "content": "閱讀理解測驗：第三單元", 
            "course_id": courses["聽力克漏字"],
            "difficulty_level": "intermediate",
            "activity_type": "reading"
        },
        {
            "title": "造句練習 - 過去式",
            "content": "使用過去式動詞造句，每個動詞造兩個句子",
            "course_id": courses["造句活動"],
            "difficulty_level": "intermediate",
            "activity_type": "writing"
        }
    ]
    
    for lesson_data in lessons_data:
        lesson = Lesson(**lesson_data)
        db.add(lesson)
    
    db.commit()
    print(f"✅ Added {len(lessons_data)} lessons")

def seed_enrollments(db):
    """Seed student-class enrollments"""
    print("🔗 Seeding student enrollments...")
    
    # Get students and classes
    students = {student.full_name: student.id for student in db.query(Student).all()}
    classes = {cls.name: cls.id for cls in db.query(Class).all()}
    
    # Based on StudentManagement mock data status
    enrollments_data = [
        # 已分班 students
        {"student_id": students["陳小明"], "class_id": classes["六年一班"], "is_active": True},
        {"student_id": students["王小美"], "class_id": classes["六年二班"], "is_active": True}, 
        {"student_id": students["李小芳"], "class_id": classes["五年三班"], "is_active": True},
        {"student_id": students["黃小志"], "class_id": classes["國一甲班"], "is_active": True},
        # 待分班 students (林小華, 張小強) are not enrolled yet
    ]
    
    for enrollment_data in enrollments_data:
        class_student = ClassStudent(**enrollment_data)
        db.add(class_student)
    
    db.commit()
    print(f"✅ Added {len(enrollments_data)} student enrollments")

def seed_class_course_mappings(db):
    """Seed class-course assignments"""
    print("🎯 Seeding class-course mappings...")
    
    # Get classes and courses
    classes = {cls.name: cls.id for cls in db.query(Class).all()}
    courses = {course.title: course.id for course in db.query(Course).all()}
    
    # Assign courses to classes based on school and grade level
    mappings_data = [
        # 台北總校 classes
        {"class_id": classes["六年一班"], "course_id": courses["English Conversation 101"]},
        {"class_id": classes["六年一班"], "course_id": courses["第一課 - 活動管理"]},
        {"class_id": classes["六年二班"], "course_id": courses["Advanced Grammar"]},
        {"class_id": classes["六年二班"], "course_id": courses["聽力克漏字"]},
        
        # 新竹分校 classes
        {"class_id": classes["五年三班"], "course_id": courses["造句活動"]},
        {"class_id": classes["五年三班"], "course_id": courses["Pronunciation Practice"]},
        
        # 台中補習班 classes
        {"class_id": classes["國一甲班"], "course_id": courses["Test Preparation"]},
    ]
    
    for mapping_data in mappings_data:
        mapping = ClassCourseMapping(**mapping_data)
        db.add(mapping)
    
    db.commit()
    print(f"✅ Added {len(mappings_data)} class-course mappings")

def print_summary(db):
    """Print seeding summary"""
    print("\n" + "="*50)
    print("📊 SEEDING SUMMARY")
    print("="*50)
    
    schools_count = db.query(School).count()
    users_count = db.query(User).count()
    students_count = db.query(Student).count() 
    classes_count = db.query(Class).count()
    courses_count = db.query(Course).count()
    lessons_count = db.query(Lesson).count()
    enrollments_count = db.query(ClassStudent).count()
    mappings_count = db.query(ClassCourseMapping).count()
    
    print(f"🏫 Schools:           {schools_count}")
    print(f"👥 Users (Teachers):  {users_count}")
    print(f"👨‍🎓 Students:          {students_count}")
    print(f"🎓 Classes:           {classes_count}")
    print(f"📚 Courses:           {courses_count}")
    print(f"📋 Lessons:           {lessons_count}")
    print(f"🔗 Enrollments:       {enrollments_count}")
    print(f"🎯 Course Mappings:   {mappings_count}")
    print("="*50)
    print("✅ Demo data seeding completed successfully!")
    print("\n🔑 Login Credentials:")
    print("   Admin: admin@duotopia.com / admin123")
    print("   Teacher: teacher1@duotopia.com / teacher123") 
    print("   Student: student1@duotopia.com / 20090828")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Seed Duotopia database with demo data')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')
    args = parser.parse_args()
    
    print("🌱 Starting Duotopia Demo Data Seeding...")
    print("="*50)
    
    db = SessionLocal()
    
    try:
        if args.clear:
            clear_all_data(db)
        
        # Seed data in dependency order
        seed_schools(db)
        seed_users(db) 
        seed_classes(db)
        seed_students(db)
        seed_courses(db)
        seed_lessons(db)
        seed_enrollments(db)
        seed_class_course_mappings(db)
        
        print_summary(db)
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()