#!/usr/bin/env python3
"""
重新分配學生到教室
"""
import sys
import os
import uuid
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal
from models import User, Classroom, Student, ClassroomStudent

def redistribute_students():
    db = SessionLocal()
    try:
        print("=== 重新分配學生到教室 ===\n")
        
        # 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name}")
        
        # 獲取所有教室
        classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).order_by(Classroom.created_at).all()
        
        print(f"✓ 找到 {len(classrooms)} 個教室")
        for i, c in enumerate(classrooms):
            print(f"  {i+1}. {c.name}")
        
        # 獲取所有可用學生（不限制現有關聯）
        all_students = db.query(Student).all()
        print(f"\n✓ 找到 {len(all_students)} 個學生")
        
        # 清除現有的教室學生關聯
        print("\n🔄 清除現有教室學生關聯...")
        db.query(ClassroomStudent).filter(
            ClassroomStudent.classroom_id.in_([c.id for c in classrooms])
        ).delete(synchronize_session=False)
        db.flush()
        
        # 重新分配學生
        print("\n🔗 重新分配學生...")
        
        if len(classrooms) >= 5 and len(all_students) >= 12:
            assignments = [
                # (教室索引, 學生索引範圍)
                (0, slice(0, 3)),   # 小學英語基礎班
                (1, slice(3, 6)),   # 小學英語進階班  
                (2, slice(6, 9)),   # 國中英語會話班
                (3, slice(9, 11)),  # 國中英語閱讀班
                (4, slice(11, 12)), # 成人英語口說班
            ]
            
            for classroom_idx, student_slice in assignments:
                classroom = classrooms[classroom_idx]
                students_group = all_students[student_slice]
                
                for student in students_group:
                    classroom_student = ClassroomStudent(
                        id=str(uuid.uuid4()),
                        classroom_id=classroom.id,
                        student_id=student.id
                    )
                    db.add(classroom_student)
                
                print(f"  ✓ {classroom.name}: 分配 {len(students_group)} 個學生")
                for s in students_group:
                    print(f"    - {s.full_name}")
        
        # 把剩餘學生分配到第一個教室
        remaining_students = all_students[12:]
        if remaining_students and len(classrooms) > 0:
            first_classroom = classrooms[0]
            for student in remaining_students:
                classroom_student = ClassroomStudent(
                    id=str(uuid.uuid4()),
                    classroom_id=first_classroom.id,
                    student_id=student.id
                )
                db.add(classroom_student)
            
            print(f"  ✓ 額外分配 {len(remaining_students)} 個學生到 {first_classroom.name}")
        
        db.commit()
        
        # 顯示最終結果
        print("\n✅ 學生重新分配完成！\n")
        print("📊 最終分配結果：")
        
        for classroom in classrooms:
            student_count = db.query(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom.id
            ).count()
            
            students = db.query(Student).join(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom.id
            ).all()
            
            print(f"\n📚 {classroom.name} ({student_count} 學生):")
            for student in students:
                print(f"  - {student.full_name} ({student.email})")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    redistribute_students()