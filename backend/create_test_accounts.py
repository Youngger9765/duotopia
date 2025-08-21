#!/usr/bin/env python3
"""
創建三種測試帳號：
1. 個體戶教師 (只能管理自己的教室、課程、學生)
2. 機構管理員 (可以管理學校、教職員、所有教室等)
3. 混合型 (同時具有兩種角色，可切換)
"""
from database import SessionLocal, engine
from auth import get_password_hash
import models

def create_test_accounts():
    db = SessionLocal()
    
    try:
        # 測試帳號資料
        test_accounts = [
            {
                "email": "individual@test.com",
                "full_name": "個體戶老師",
                "role": models.UserRole.TEACHER,
                "is_individual_teacher": True,
                "is_institutional_admin": False,
                "current_role_context": "individual",
                "password": "test123"
            },
            {
                "email": "institutional@test.com", 
                "full_name": "機構管理員",
                "role": models.UserRole.ADMIN,
                "is_individual_teacher": False,
                "is_institutional_admin": True,
                "current_role_context": "institutional",
                "password": "test123"
            },
            {
                "email": "hybrid@test.com",
                "full_name": "混合型使用者",
                "role": models.UserRole.TEACHER,
                "is_individual_teacher": True,
                "is_institutional_admin": True,
                "current_role_context": "default",
                "password": "test123"
            }
        ]
        
        for account_data in test_accounts:
            # 檢查是否已存在
            existing_user = db.query(models.User).filter(
                models.User.email == account_data["email"]
            ).first()
            
            if existing_user:
                # 更新現有用戶
                existing_user.full_name = account_data["full_name"]
                existing_user.role = account_data["role"]
                existing_user.is_individual_teacher = account_data["is_individual_teacher"]
                existing_user.is_institutional_admin = account_data["is_institutional_admin"]
                existing_user.current_role_context = account_data["current_role_context"]
                existing_user.hashed_password = get_password_hash(account_data["password"])
                existing_user.is_active = True
                print(f"✓ 更新帳號: {account_data['email']}")
            else:
                # 創建新用戶
                new_user = models.User(
                    email=account_data["email"],
                    full_name=account_data["full_name"],
                    role=account_data["role"],
                    is_individual_teacher=account_data["is_individual_teacher"],
                    is_institutional_admin=account_data["is_institutional_admin"],
                    current_role_context=account_data["current_role_context"],
                    hashed_password=get_password_hash(account_data["password"]),
                    is_active=True
                )
                db.add(new_user)
                print(f"✓ 創建帳號: {account_data['email']}")
        
        db.commit()
        
        print("\n=== 測試帳號創建完成 ===")
        print("\n1. 個體戶教師:")
        print("   Email: individual@test.com")
        print("   密碼: test123")
        print("   權限: 只能管理個人教室、課程、學生")
        
        print("\n2. 機構管理員:")
        print("   Email: institutional@test.com")
        print("   密碼: test123")
        print("   權限: 可管理學校、教職員、所有教學資源")
        
        print("\n3. 混合型使用者:")
        print("   Email: hybrid@test.com")
        print("   密碼: test123")
        print("   權限: 可在個體戶和機構管理員角色間切換")
        
    except Exception as e:
        print(f"錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_accounts()