#!/usr/bin/env python3
"""
檢查個體戶教師的學生資料
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from models import User, Student, Classroom, ClassroomStudent

def check_students():
    db = SessionLocal()
    try:
        # 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name} (ID: {teacher.id})")
        
        # 查詢教師的學生
        students = db.query(Student).filter(
            Student.teacher_id == teacher.id
        ).all()
        
        print(f"\n找到 {len(students)} 個學生：")
        for student in students:
            print(f"  - {student.name}")
            print(f"    ID: {student.id}")
            print(f"    Email: {student.email}")
            print(f"    Birth Date: {student.birth_date}")
            print(f"    Teacher ID: {student.teacher_id}")
            
            # 查詢學生所在的教室
            classrooms = db.query(Classroom).join(
                ClassroomStudent
            ).filter(
                ClassroomStudent.student_id == student.id
            ).all()
            
            if classrooms:
                print(f"    教室: {', '.join([c.name for c in classrooms])}")
            else:
                print(f"    教室: 無")
                
        # 如果沒有學生，建立一些
        if len(students) == 0:
            print("\n建立測試學生...")
            from datetime import date
            
            student1 = Student(
                name="測試學生一",
                email="test1@example.com",
                birth_date=date(2012, 1, 1),
                teacher_id=teacher.id
            )
            
            student2 = Student(
                name="測試學生二",
                email="test2@example.com",
                birth_date=date(2012, 2, 2),
                teacher_id=teacher.id
            )
            
            db.add(student1)
            db.add(student2)
            db.commit()
            
            print("✓ 建立了 2 個測試學生")
            
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    check_students()