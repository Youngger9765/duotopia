#!/usr/bin/env python3
"""
Simple Demo Data Seeder for Duotopia
Creates basic demo data without complex relationships
"""

from database import SessionLocal
from models import User, Student, School
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def create_simple_demo_data():
    print("🌱 Creating Simple Demo Data...")
    print("=" * 40)
    
    db = SessionLocal()
    
    try:
        # Create schools
        print("🏫 Creating schools...")
        schools_data = [
            {"name": "台北總校", "code": "TP001", "address": "台北市中正區重慶南路一段122號", "phone": "02-2388-1234"},
            {"name": "新竹分校", "code": "HC002", "address": "新竹市東區光復路二段101號", "phone": "03-571-2345"},
            {"name": "台中補習班", "code": "TC003", "address": "台中市西屯區台灣大道三段99號", "phone": "04-2251-3456"}
        ]
        
        created_schools = []
        for school_data in schools_data:
            school = School(**school_data)
            db.add(school)
            created_schools.append(school)
        
        db.commit()
        print(f"✅ Created {len(created_schools)} schools")
        
        # Create admin and teachers
        print("👥 Creating users...")
        users_data = [
            {"email": "admin@duotopia.com", "hashed_password": hash_password("admin123"), "full_name": "系統管理員", "role": "admin"},
            {"email": "teacher1@duotopia.com", "hashed_password": hash_password("teacher123"), "full_name": "王老師", "role": "teacher"},
            {"email": "teacher2@duotopia.com", "hashed_password": hash_password("teacher123"), "full_name": "李老師", "role": "teacher"},
            {"email": "teacher3@duotopia.com", "hashed_password": hash_password("teacher123"), "full_name": "張老師", "role": "teacher"},
        ]
        
        created_users = []
        for user_data in users_data:
            user = User(**user_data)
            db.add(user)
            created_users.append(user)
        
        db.commit()
        print(f"✅ Created {len(created_users)} users")
        
        # Create students
        print("👨‍🎓 Creating students...")
        students_data = [
            {"email": "student1@duotopia.com", "full_name": "陳小明", "birth_date": "20090828", "phone_number": "0900-000-001", "grade": 6, "school": "台北總校"},
            {"email": "student2@duotopia.com", "full_name": "林小華", "birth_date": "20090828", "phone_number": "0900-000-002", "grade": 6, "school": "台北總校"},
            {"email": "student3@duotopia.com", "full_name": "王小美", "birth_date": "20090828", "phone_number": "0900-000-003", "grade": 6, "school": "台北總校"},
            {"email": "student4@duotopia.com", "full_name": "張小強", "birth_date": "20090828", "phone_number": "0900-000-004", "grade": 5, "school": "新竹分校"},
            {"email": "student5@duotopia.com", "full_name": "李小芳", "birth_date": "20090828", "phone_number": "0900-000-005", "grade": 5, "school": "新竹分校"},
            {"email": "student6@duotopia.com", "full_name": "黃小志", "birth_date": "20090828", "phone_number": "0900-000-006", "grade": 7, "school": "台中補習班"}
        ]
        
        created_students = []
        for student_data in students_data:
            student = Student(**student_data)
            db.add(student)
            created_students.append(student)
        
        db.commit()
        print(f"✅ Created {len(created_students)} students")
        
        print("\n" + "=" * 40)
        print("✅ Simple demo data creation completed!")
        print(f"🏫 Schools: {len(created_schools)}")
        print(f"👥 Users: {len(created_users)}")
        print(f"👨‍🎓 Students: {len(created_students)}")
        print("\n🔑 Login Credentials:")
        print("   Admin: admin@duotopia.com / admin123")
        print("   Teacher: teacher1@duotopia.com / teacher123")
        print("   Student: student1@duotopia.com / 20090828")
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_simple_demo_data()