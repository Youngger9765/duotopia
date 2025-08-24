#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from models import User

def check_users():
    db = SessionLocal()
    try:
        # 列出所有使用者
        users = db.query(User).all()
        print("=== 所有使用者 ===")
        for user in users:
            print(f"Email: {user.email}")
            print(f"  Full Name: {user.full_name}")
            print(f"  Is Individual Teacher: {user.is_individual_teacher}")
            print(f"  Is Institutional Admin: {user.is_institutional_admin}")
            print("---")
        
        # 查找個體戶教師
        individual_teachers = db.query(User).filter(User.is_individual_teacher == True).all()
        print(f"\n找到 {len(individual_teachers)} 位個體戶教師")
        for teacher in individual_teachers:
            print(f"- {teacher.email}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_users()