#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from database import SessionLocal
from models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_password():
    db = SessionLocal()
    try:
        # 找到個體戶教師
        user = db.query(User).filter(User.email == "teacher@individual.com").first()
        if user:
            print(f"找到使用者: {user.email}")
            print(f"Full Name: {user.full_name}")
            
            # 測試密碼
            test_password = "password123"
            is_valid = pwd_context.verify(test_password, user.hashed_password)
            print(f"密碼驗證 ('{test_password}'): {'成功' if is_valid else '失敗'}")
            
            # 如果失敗，重設密碼
            if not is_valid:
                print("\n重設密碼...")
                user.hashed_password = pwd_context.hash(test_password)
                db.commit()
                print("密碼已重設為 'password123'")
        else:
            print("未找到使用者")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_password()