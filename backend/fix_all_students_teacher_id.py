#!/usr/bin/env python3
"""
修復所有學生的 teacher_id
"""
from database import get_db
from models_dual_system import IndividualStudent, IndividualClassroom, IndividualEnrollment
from sqlalchemy.orm import Session, joinedload

def fix_all_students_teacher_id():
    db = next(get_db())
    
    print("=== 修復所有學生的 teacher_id ===\n")
    
    # 找出所有 teacher_id 為 null 的學生
    students_without_teacher = db.query(IndividualStudent).filter(
        IndividualStudent.teacher_id == None
    ).all()
    
    print(f"找到 {len(students_without_teacher)} 個學生沒有 teacher_id\n")
    
    # 透過 enrollment 找到每個學生所屬的老師
    for student in students_without_teacher:
        # 找到學生的第一個 enrollment
        enrollment = db.query(IndividualEnrollment).options(
            joinedload(IndividualEnrollment.classroom)
        ).filter(
            IndividualEnrollment.student_id == student.id,
            IndividualEnrollment.is_active == True
        ).first()
        
        if enrollment and enrollment.classroom:
            teacher_id = enrollment.classroom.teacher_id
            student.teacher_id = teacher_id
            print(f"✅ 更新學生 {student.full_name} (ID: {student.id}) 的 teacher_id 為 {teacher_id}")
        else:
            print(f"⚠️  學生 {student.full_name} (ID: {student.id}) 沒有找到有效的教室註冊")
    
    # 提交更改
    db.commit()
    print(f"\n✅ 更新完成！")
    
    # 驗證結果
    remaining_without_teacher = db.query(IndividualStudent).filter(
        IndividualStudent.teacher_id == None
    ).count()
    
    print(f"\n剩餘 {remaining_without_teacher} 個學生沒有 teacher_id")

if __name__ == "__main__":
    fix_all_students_teacher_id()