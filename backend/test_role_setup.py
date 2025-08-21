#!/usr/bin/env python3
"""
Setup a test user with multiple roles
"""
from database import SessionLocal, engine
import models

def setup_test_user_with_multiple_roles():
    db = SessionLocal()
    
    try:
        # Find the first teacher
        teacher = db.query(models.User).filter(
            models.User.role == models.UserRole.TEACHER
        ).first()
        
        if teacher:
            # Give them both individual teacher and institutional admin capabilities
            teacher.is_individual_teacher = True
            teacher.is_institutional_admin = True
            teacher.current_role_context = "default"
            
            db.commit()
            print(f"Updated user {teacher.email} with multiple roles:")
            print(f"  - is_individual_teacher: {teacher.is_individual_teacher}")
            print(f"  - is_institutional_admin: {teacher.is_institutional_admin}")
            print(f"  - has_multiple_roles: {teacher.has_multiple_roles}")
        else:
            print("No teacher found to update")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_test_user_with_multiple_roles()