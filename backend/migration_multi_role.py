#!/usr/bin/env python3
"""
多重角色系統遷移腳本
將現有的單一角色系統遷移到多重角色系統
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from database import get_db, DATABASE_URL
from models import User as LegacyUser, UserRole, School
from models_multi_role import User as NewUser, UserInstitutionRole, PlatformRole, InstitutionRole
import uuid
from datetime import date

def create_migration_tables():
    """創建新的多重角色相關表"""
    engine = create_engine(DATABASE_URL)
    
    # 創建 user_institution_roles 表的 SQL
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_institution_roles (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL,
        institution_id VARCHAR NOT NULL,
        roles JSON NOT NULL,
        permissions JSON DEFAULT '{}',
        is_active BOOLEAN DEFAULT true,
        start_date DATE DEFAULT CURRENT_DATE,
        end_date DATE NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE NULL,
        created_by VARCHAR NOT NULL,
        
        CONSTRAINT fk_user_institution_roles_user 
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        CONSTRAINT fk_user_institution_roles_institution 
            FOREIGN KEY (institution_id) REFERENCES schools(id) ON DELETE CASCADE,
        CONSTRAINT fk_user_institution_roles_creator 
            FOREIGN KEY (created_by) REFERENCES users(id),
        
        UNIQUE(user_id, institution_id)
    );
    """
    
    # 創建索引
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_user_institution_roles_user ON user_institution_roles(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_institution_roles_institution ON user_institution_roles(institution_id);",
        "CREATE INDEX IF NOT EXISTS idx_user_institution_roles_active ON user_institution_roles(user_id, institution_id, is_active);"
    ]
    
    with engine.connect() as conn:
        # 創建表
        conn.execute(text(create_table_sql))
        
        # 創建索引
        for index_sql in create_indexes_sql:
            conn.execute(text(index_sql))
        
        conn.commit()
    
    print("✅ 多重角色數據表創建完成")

def add_platform_role_column():
    """為 users 表添加 platform_role 列"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # 檢查列是否已存在
            check_column_sql = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'platform_role'
            """
            result = conn.execute(text(check_column_sql)).fetchone()
            
            if not result:
                # 添加新列
                add_column_sql = """
                ALTER TABLE users 
                ADD COLUMN platform_role VARCHAR DEFAULT 'platform_user'
                """
                conn.execute(text(add_column_sql))
                conn.commit()
                print("✅ 已為 users 表添加 platform_role 列")
            else:
                print("ℹ️  platform_role 列已存在，跳過添加")
                
        except Exception as e:
            print(f"❌ 添加 platform_role 列失敗: {e}")

def migrate_user_roles():
    """遷移現有用戶角色到新系統"""
    db = next(get_db())
    
    try:
        # 獲取所有現有用戶
        users = db.query(LegacyUser).all()
        print(f"📋 找到 {len(users)} 個用戶需要遷移")
        
        # 獲取默認機構（如果沒有特定機構關聯）
        default_school = db.query(School).first()
        if not default_school:
            print("❌ 未找到任何機構，無法進行遷移")
            return
        
        migration_count = 0
        
        for user in users:
            try:
                # 更新平台角色
                if hasattr(user, 'role') and user.role == UserRole.ADMIN:
                    platform_role = PlatformRole.SUPER_ADMIN
                else:
                    platform_role = PlatformRole.PLATFORM_USER
                
                # 更新用戶的平台角色
                db.execute(
                    text("UPDATE users SET platform_role = :platform_role WHERE id = :user_id"),
                    {"platform_role": platform_role.value, "user_id": user.id}
                )
                
                # 轉換機構角色
                if hasattr(user, 'role'):
                    legacy_role = user.role.value
                    
                    # 將舊角色映射到新的機構角色
                    role_mapping = {
                        "admin": [InstitutionRole.ADMIN.value],
                        "teacher": [InstitutionRole.TEACHER.value],
                        "student": [InstitutionRole.STUDENT.value]
                    }
                    
                    new_roles = role_mapping.get(legacy_role, [InstitutionRole.STUDENT.value])
                    
                    # 檢查是否已有角色記錄
                    existing_role = db.query(UserInstitutionRole).filter(
                        UserInstitutionRole.user_id == user.id,
                        UserInstitutionRole.institution_id == default_school.id
                    ).first()
                    
                    if not existing_role:
                        # 創建新的機構角色記錄
                        role_record = UserInstitutionRole(
                            id=str(uuid.uuid4()),
                            user_id=user.id,
                            institution_id=default_school.id,
                            roles=new_roles,
                            permissions={},
                            start_date=date.today(),
                            created_by=user.id  # 自己創建
                        )
                        
                        db.add(role_record)
                        migration_count += 1
                        
                        print(f"✅ 遷移用戶: {user.email} ({legacy_role} -> {new_roles})")
                    else:
                        print(f"ℹ️  用戶 {user.email} 已有角色記錄，跳過")
                
            except Exception as e:
                print(f"❌ 遷移用戶 {user.email} 失敗: {e}")
                continue
        
        db.commit()
        print(f"🎉 成功遷移 {migration_count} 個用戶的角色")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 角色遷移失敗: {e}")
    finally:
        db.close()

def create_sample_multi_roles():
    """創建一些示例多重角色用戶"""
    db = next(get_db())
    
    try:
        # 獲取現有機構
        schools = db.query(School).all()
        if len(schools) < 2:
            print("❌ 至少需要 2 個機構才能創建多重角色示例")
            return
        
        # 查找一個現有用戶
        sample_user = db.query(LegacyUser).filter(LegacyUser.email.like("%teacher%")).first()
        if not sample_user:
            print("❌ 未找到教師用戶來創建多重角色示例")
            return
        
        print(f"📝 為用戶 {sample_user.email} 創建多重角色示例...")
        
        # 為用戶在第一個機構創建教師角色
        role1 = UserInstitutionRole(
            id=str(uuid.uuid4()),
            user_id=sample_user.id,
            institution_id=schools[0].id,
            roles=[InstitutionRole.TEACHER.value],
            permissions={"can_create_class": True, "can_grade": True},
            created_by=sample_user.id
        )
        
        # 為用戶在第二個機構創建學生+助教角色
        role2 = UserInstitutionRole(
            id=str(uuid.uuid4()),
            user_id=sample_user.id,
            institution_id=schools[1].id,
            roles=[InstitutionRole.STUDENT.value, InstitutionRole.ASSISTANT.value],
            permissions={"can_grade": False, "can_assist": True},
            created_by=sample_user.id
        )
        
        # 檢查是否已存在
        existing1 = db.query(UserInstitutionRole).filter(
            UserInstitutionRole.user_id == sample_user.id,
            UserInstitutionRole.institution_id == schools[0].id
        ).first()
        
        existing2 = db.query(UserInstitutionRole).filter(
            UserInstitutionRole.user_id == sample_user.id,
            UserInstitutionRole.institution_id == schools[1].id
        ).first()
        
        if not existing1:
            db.add(role1)
            print(f"✅ 在 {schools[0].name} 創建教師角色")
        
        if not existing2:
            db.add(role2)
            print(f"✅ 在 {schools[1].name} 創建學生+助教角色")
        
        db.commit()
        print("🎉 多重角色示例創建完成")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 創建多重角色示例失敗: {e}")
    finally:
        db.close()

def verify_migration():
    """驗證遷移結果"""
    db = next(get_db())
    
    try:
        # 統計信息
        total_users = db.query(LegacyUser).count()
        total_role_records = db.query(UserInstitutionRole).count()
        
        print("📊 遷移結果統計:")
        print(f"   總用戶數: {total_users}")
        print(f"   角色記錄數: {total_role_records}")
        
        # 檢查多重角色用戶
        multi_role_users = db.execute(
            text("""
            SELECT u.email, u.full_name, COUNT(r.id) as role_count
            FROM users u
            JOIN user_institution_roles r ON u.id = r.user_id
            WHERE r.is_active = true
            GROUP BY u.id, u.email, u.full_name
            HAVING COUNT(r.id) > 1
            """)
        ).fetchall()
        
        print(f"   多重角色用戶數: {len(multi_role_users)}")
        
        for user in multi_role_users:
            print(f"   - {user.full_name} ({user.email}): {user.role_count} 個角色")
        
        # 顯示所有角色分配
        print("\n📋 角色分配詳情:")
        role_details = db.execute(
            text("""
            SELECT u.full_name, u.email, s.name as school_name, r.roles, r.is_active
            FROM users u
            JOIN user_institution_roles r ON u.id = r.user_id
            JOIN schools s ON r.institution_id = s.id
            ORDER BY u.full_name, s.name
            """)
        ).fetchall()
        
        for detail in role_details:
            status = "✅" if detail.is_active else "❌"
            print(f"   {status} {detail.full_name} @ {detail.school_name}: {detail.roles}")
        
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
    finally:
        db.close()

def main():
    """主遷移流程"""
    print("🚀 開始多重角色系統遷移...")
    print("=" * 50)
    
    # 步驟 1: 創建新表
    print("步驟 1: 創建多重角色數據表")
    create_migration_tables()
    
    # 步驟 2: 添加平台角色列
    print("\n步驟 2: 更新用戶表結構")
    add_platform_role_column()
    
    # 步驟 3: 遷移現有角色
    print("\n步驟 3: 遷移現有用戶角色")
    migrate_user_roles()
    
    # 步驟 4: 創建多重角色示例
    print("\n步驟 4: 創建多重角色示例")
    create_sample_multi_roles()
    
    # 步驟 5: 驗證遷移結果
    print("\n步驟 5: 驗證遷移結果")
    verify_migration()
    
    print("\n" + "=" * 50)
    print("🎉 多重角色系統遷移完成！")
    print("\n接下來的步驟:")
    print("1. 更新應用代碼使用新的角色檢查邏輯")
    print("2. 測試所有功能是否正常工作")
    print("3. 考慮移除舊的 role 列（可選）")

if __name__ == "__main__":
    main()