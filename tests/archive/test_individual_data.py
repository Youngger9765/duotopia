#!/usr/bin/env python3
"""
測試個體戶教師的資料
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from models import User
from models_dual_system import IndividualClassroom, IndividualStudent, IndividualEnrollment

def test_individual_data():
    db = SessionLocal()
    try:
        # 1. 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name} (ID: {teacher.id})")
        print(f"  是否為個體戶教師: {teacher.is_individual_teacher}")
        
        # 2. 檢查教室
        classrooms = db.query(IndividualClassroom).filter(
            IndividualClassroom.teacher_id == teacher.id
        ).all()
        
        print(f"\n📚 教室數量: {len(classrooms)}")
        for classroom in classrooms:
            print(f"  - {classroom.name}")
            print(f"    年級: {classroom.grade_level}")
            print(f"    地點: {classroom.location}")
            print(f"    價格: ${classroom.pricing}/堂")
            print(f"    最大學生數: {classroom.max_students}")
            
            # 檢查學生數
            enrollments = db.query(IndividualEnrollment).filter(
                IndividualEnrollment.classroom_id == classroom.id,
                IndividualEnrollment.is_active == True
            ).count()
            print(f"    目前學生數: {enrollments}")
        
        # 3. 檢查學生
        students = db.query(IndividualStudent).filter(
            IndividualStudent.teacher_id == teacher.id
        ).all()
        
        print(f"\n👥 學生總數: {len(students)}")
        for student in students[:5]:  # 只顯示前5個
            print(f"  - {student.full_name}")
            print(f"    Email: {student.email}")
            print(f"    生日: {student.birth_date}")
            
        # 4. 如果沒有資料，建立測試資料
        if len(classrooms) == 0:
            print("\n⚠️  沒有找到教室，建立測試資料...")
            
            # 建立教室
            classroom1 = IndividualClassroom(
                name="六年級英語進階班",
                grade_level="六年級",
                location="台北市大安區",
                pricing=800,
                max_students=10,
                teacher_id=teacher.id
            )
            
            classroom2 = IndividualClassroom(
                name="國中英語會話班",
                grade_level="國中",
                location="線上授課",
                pricing=1000,
                max_students=8,
                teacher_id=teacher.id
            )
            
            db.add(classroom1)
            db.add(classroom2)
            db.commit()
            db.refresh(classroom1)
            db.refresh(classroom2)
            
            print("✓ 建立了 2 個教室")
            
            # 建立學生
            student1 = IndividualStudent(
                full_name="林小明",
                email="xiaoming@example.com",
                birth_date="2012-05-15",
                teacher_id=teacher.id
            )
            
            student2 = IndividualStudent(
                full_name="陳小華",
                email="xiaohua@example.com",
                birth_date="2011-08-20",
                teacher_id=teacher.id
            )
            
            db.add(student1)
            db.add(student2)
            db.commit()
            
            # 註冊學生到教室
            enrollment1 = IndividualEnrollment(
                student_id=student1.id,
                classroom_id=classroom1.id,
                payment_status="paid"
            )
            
            enrollment2 = IndividualEnrollment(
                student_id=student2.id,
                classroom_id=classroom1.id,
                payment_status="pending"
            )
            
            db.add(enrollment1)
            db.add(enrollment2)
            db.commit()
            
            print("✓ 建立了 2 個學生並註冊到教室")
            
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_individual_data()