#!/usr/bin/env python3
"""檢查重複的註冊記錄"""
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models_dual_system import IndividualEnrollment, IndividualStudent, IndividualClassroom

async def check_duplicate_enrollments():
    db = next(get_db())
    
    try:
        print("檢查重複的學生註冊記錄...")
        print("=" * 60)
        
        # 查找同一學生在同一教室有多個活躍註冊的情況
        duplicates = db.query(
            IndividualEnrollment.student_id,
            IndividualEnrollment.classroom_id,
            func.count(IndividualEnrollment.id).label('count')
        ).filter(
            IndividualEnrollment.is_active == True
        ).group_by(
            IndividualEnrollment.student_id,
            IndividualEnrollment.classroom_id
        ).having(
            func.count(IndividualEnrollment.id) > 1
        ).all()
        
        if duplicates:
            print("發現重複註冊：")
            for dup in duplicates:
                student = db.query(IndividualStudent).filter(
                    IndividualStudent.id == dup.student_id
                ).first()
                classroom = db.query(IndividualClassroom).filter(
                    IndividualClassroom.id == dup.classroom_id
                ).first()
                
                print(f"學生：{student.full_name} ({student.email})")
                print(f"教室：{classroom.name}")
                print(f"重複次數：{dup.count}")
                
                # 顯示所有重複的記錄
                enrollments = db.query(IndividualEnrollment).filter(
                    IndividualEnrollment.student_id == dup.student_id,
                    IndividualEnrollment.classroom_id == dup.classroom_id,
                    IndividualEnrollment.is_active == True
                ).all()
                
                for i, enrollment in enumerate(enrollments):
                    print(f"  記錄 {i+1}: ID={enrollment.id}, 創建時間={enrollment.enrolled_at}, 付款狀態={enrollment.payment_status}")
                
                print("-" * 40)
        else:
            print("✅ 沒有發現重複的註冊記錄")
            
        # 檢查特定教室的學生
        classroom_id = "dcf8d937-f28e-4aec-be78-c69472695d0b"
        print(f"\n檢查教室 {classroom_id} 的學生：")
        print("=" * 60)
        
        enrollments = db.query(IndividualEnrollment).filter(
            IndividualEnrollment.classroom_id == classroom_id,
            IndividualEnrollment.is_active == True
        ).all()
        
        student_counts = {}
        for enrollment in enrollments:
            student_id = enrollment.student_id
            if student_id in student_counts:
                student_counts[student_id] += 1
            else:
                student_counts[student_id] = 1
        
        for student_id, count in student_counts.items():
            student = db.query(IndividualStudent).filter(
                IndividualStudent.id == student_id
            ).first()
            print(f"學生：{student.full_name} ({student.email}) - 出現 {count} 次")
            if count > 1:
                print("  ⚠️  重複出現！")
                
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_duplicate_enrollments())