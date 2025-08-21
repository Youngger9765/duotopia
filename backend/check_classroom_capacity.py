#!/usr/bin/env python3
"""檢查教室容量狀態"""
import asyncio
from sqlalchemy.orm import Session
from database import get_db
from models_dual_system import IndividualClassroom, IndividualEnrollment

async def check_classroom_capacity():
    # 獲取資料庫連接
    db = next(get_db())
    
    try:
        # 獲取所有教室
        classrooms = db.query(IndividualClassroom).all()
        
        print("教室容量檢查：")
        print("=" * 50)
        
        for classroom in classrooms:
            # 計算當前學生數
            current_count = db.query(IndividualEnrollment).filter(
                IndividualEnrollment.classroom_id == classroom.id,
                IndividualEnrollment.is_active == True
            ).count()
            
            print(f"教室：{classroom.name}")
            print(f"  容量：{current_count}/{classroom.max_students}")
            print(f"  狀態：{'已滿' if current_count >= classroom.max_students else '可用'}")
            print(f"  ID：{classroom.id}")
            print("-" * 30)
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(check_classroom_capacity())