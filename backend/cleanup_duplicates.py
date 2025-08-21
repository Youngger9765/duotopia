#!/usr/bin/env python3
"""清理重複的註冊記錄"""
import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models_dual_system import IndividualEnrollment

async def cleanup_duplicate_enrollments():
    db = next(get_db())
    
    try:
        print("清理重複的學生註冊記錄...")
        print("=" * 50)
        
        # 查找重複的活躍註冊
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
        
        total_removed = 0
        
        for dup in duplicates:
            print(f"處理重複註冊：學生ID={dup.student_id}, 教室ID={dup.classroom_id}")
            
            # 獲取所有重複的記錄，按創建時間排序
            enrollments = db.query(IndividualEnrollment).filter(
                IndividualEnrollment.student_id == dup.student_id,
                IndividualEnrollment.classroom_id == dup.classroom_id,
                IndividualEnrollment.is_active == True
            ).order_by(IndividualEnrollment.enrolled_at.asc()).all()
            
            # 保留最早的記錄，移除其他的
            for enrollment in enrollments[1:]:
                print(f"  移除記錄：{enrollment.id}")
                db.delete(enrollment)
                total_removed += 1
        
        db.commit()
        print(f"\n✅ 清理完成！共移除 {total_removed} 個重複記錄")
        
    except Exception as e:
        print(f"❌ 清理失敗：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_enrollments())