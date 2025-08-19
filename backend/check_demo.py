#!/usr/bin/env python3
"""
Demo Data Checker for Duotopia
Checks and displays current database content
"""

from database import SessionLocal
from models import User, Student, School, Class, Course, Lesson, ClassStudent, ClassCourseMapping
from sqlalchemy import func

def check_data():
    print("🔍 Duotopia Database Content Check")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Schools
        schools = db.query(School).all()
        print(f"🏫 Schools ({len(schools)}):")
        for school in schools:
            print(f"   {school.id}: {school.name}")
            
        # Users  
        users = db.query(User).all()
        print(f"\n👥 Users ({len(users)}):")
        for user in users:
            print(f"   {user.id}: {user.full_name} ({user.role}) - {user.email}")
            
        # Students
        students = db.query(Student).all() 
        print(f"\n👨‍🎓 Students ({len(students)}):")
        for student in students:
            print(f"   {student.id}: {student.full_name} - {student.email}")
            
        # Classes
        classes = db.query(Class).all()
        print(f"\n🎓 Classes ({len(classes)}):")
        for cls in classes:
            teacher = db.query(User).filter(User.id == cls.teacher_id).first()
            teacher_name = teacher.full_name if teacher else "未分配"
            print(f"   {cls.id}: {cls.name} (年級 {cls.grade_level}) - {teacher_name}")
            
        # Courses
        courses = db.query(Course).all()
        print(f"\n📚 Courses ({len(courses)}):")
        for course in courses:
            print(f"   {course.id}: {course.title} (Grade {course.grade_level})")
            
        # Lessons
        lessons = db.query(Lesson).all()
        print(f"\n📋 Lessons ({len(lessons)}):")
        for lesson in lessons:
            course = db.query(Course).filter(Course.id == lesson.course_id).first()
            course_title = course.title if course else "未分配"
            print(f"   {lesson.id}: {lesson.title} - {course_title}")
            
        # Student Enrollments
        enrollments = db.query(ClassStudent).all()
        print(f"\n🔗 Student Enrollments ({len(enrollments)}):")
        for enrollment in enrollments:
            student = db.query(Student).filter(Student.id == enrollment.student_id).first()
            cls = db.query(Class).filter(Class.id == enrollment.class_id).first()
            student_name = student.full_name if student else "未知"
            class_name = cls.name if cls else "未知"
            print(f"   {student_name} -> {class_name}")
            
        # Class Course Mappings
        mappings = db.query(ClassCourseMapping).all()
        print(f"\n🎯 Class-Course Mappings ({len(mappings)}):")
        for mapping in mappings:
            cls = db.query(Class).filter(Class.id == mapping.class_id).first()
            course = db.query(Course).filter(Course.id == mapping.course_id).first()
            class_name = cls.name if cls else "未知"
            course_title = course.title if course else "未知"
            print(f"   {class_name} <- {course_title}")
            
        print("\n" + "=" * 50)
        print("✅ Database content check completed")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()