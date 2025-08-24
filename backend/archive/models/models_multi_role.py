"""
多重角色系統的數據模型
"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, JSON, Enum, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum
import uuid

class PlatformRole(str, enum.Enum):
    """平台級角色"""
    SUPER_ADMIN = "super_admin"  # 系統超級管理員
    PLATFORM_USER = "platform_user"  # 一般平台用戶

class InstitutionRole(str, enum.Enum):
    """機構級角色"""
    ADMIN = "admin"          # 機構管理員
    TEACHER = "teacher"      # 教師
    STUDENT = "student"      # 學生  
    ASSISTANT = "assistant"  # 助教/助理
    PARENT = "parent"        # 家長（預留）

class User(Base):
    """用戶表 - 修改版本支援多重角色"""
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String)
    
    # 平台級角色（單一）
    platform_role = Column(Enum(PlatformRole), default=PlatformRole.PLATFORM_USER, nullable=False)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    institution_roles = relationship("UserInstitutionRole", back_populates="user")
    created_classes = relationship("Class", back_populates="teacher")
    created_courses = relationship("Course", back_populates="creator")

class UserInstitutionRole(Base):
    """用戶機構角色關聯表 - 支援一個用戶在一個機構內的多重角色"""
    __tablename__ = "user_institution_roles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    institution_id = Column(String, ForeignKey("schools.id"), nullable=False)
    
    # 多重角色存儲為 JSON 數組
    roles = Column(JSON, nullable=False)  # ["admin", "teacher", "student"]
    
    # 權限配置存儲為 JSON 對象
    permissions = Column(JSON, default=dict)  # {"can_create_class": true, "can_grade": true}
    
    # 角色狀態和有效期
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, default=func.current_date())
    end_date = Column(Date, nullable=True)  # null 表示永久有效
    
    # 審計字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, ForeignKey("users.id"), nullable=False)  # 誰分配的角色
    
    # Relationships
    user = relationship("User", back_populates="institution_roles")
    institution = relationship("School", back_populates="user_roles")
    creator = relationship("User", foreign_keys=[created_by])
    
    # 約束：每個用戶在每個機構只能有一條記錄
    __table_args__ = (
        {"extend_existing": True}
    )

# 更新 School 模型以支援角色關聯
class School(Base):
    """學校/機構表"""
    __tablename__ = "schools"
    __table_args__ = {"extend_existing": True}
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)  # 機構代碼
    address = Column(String)
    phone = Column(String)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user_roles = relationship("UserInstitutionRole", back_populates="institution")
    classes = relationship("Class", back_populates="school")
    courses = relationship("Course", back_populates="school")

# 權限檢查輔助函數
class RoleChecker:
    """角色權限檢查器"""
    
    @staticmethod
    def has_platform_admin(user: User) -> bool:
        """檢查是否為平台管理員"""
        return user.platform_role == PlatformRole.SUPER_ADMIN
    
    @staticmethod
    def get_user_institution_roles(user_id: str, institution_id: str) -> UserInstitutionRole:
        """獲取用戶在特定機構的角色"""
        from database import SessionLocal
        db = SessionLocal()
        try:
            return db.query(UserInstitutionRole).filter(
                UserInstitutionRole.user_id == user_id,
                UserInstitutionRole.institution_id == institution_id,
                UserInstitutionRole.is_active == True,
                # 檢查有效期
                UserInstitutionRole.start_date <= func.current_date(),
                (UserInstitutionRole.end_date.is_(None) | 
                 (UserInstitutionRole.end_date >= func.current_date()))
            ).first()
        finally:
            db.close()
    
    @staticmethod 
    def has_institution_role(user_id: str, institution_id: str, required_role: str) -> bool:
        """檢查用戶在特定機構是否有指定角色"""
        role_record = RoleChecker.get_user_institution_roles(user_id, institution_id)
        if not role_record:
            return False
        return required_role in role_record.roles
    
    @staticmethod
    def has_any_institution_role(user_id: str, required_role: str) -> bool:
        """檢查用戶在任何機構是否有指定角色"""
        from database import SessionLocal
        db = SessionLocal()
        try:
            role_records = db.query(UserInstitutionRole).filter(
                UserInstitutionRole.user_id == user_id,
                UserInstitutionRole.is_active == True,
                UserInstitutionRole.start_date <= func.current_date(),
                (UserInstitutionRole.end_date.is_(None) | 
                 (UserInstitutionRole.end_date >= func.current_date()))
            ).all()
            
            return any(required_role in record.roles for record in role_records)
        finally:
            db.close()
    
    @staticmethod
    def can_access_resource(user: User, institution_id: str, action: str) -> bool:
        """檢查用戶是否能執行特定操作"""
        # 1. 平台管理員擁有所有權限
        if RoleChecker.has_platform_admin(user):
            return True
        
        # 2. 獲取機構角色
        role_record = RoleChecker.get_user_institution_roles(user.id, institution_id)
        if not role_record:
            return False
        
        # 3. 根據操作類型檢查權限
        user_roles = role_record.roles
        permissions = role_record.permissions or {}
        
        # 定義操作權限映射
        action_permissions = {
            "create_class": lambda: ("admin" in user_roles or "teacher" in user_roles),
            "manage_students": lambda: ("admin" in user_roles or "teacher" in user_roles),
            "view_grades": lambda: any(role in user_roles for role in ["admin", "teacher", "student"]),
            "manage_users": lambda: "admin" in user_roles,
            "create_course": lambda: ("admin" in user_roles or "teacher" in user_roles),
            "grade_assignments": lambda: ("teacher" in user_roles or permissions.get("can_grade", False)),
        }
        
        permission_check = action_permissions.get(action)
        return permission_check() if permission_check else False

# 數據遷移輔助函數
class RoleMigration:
    """角色系統遷移輔助"""
    
    @staticmethod
    def migrate_legacy_roles():
        """將舊的單一角色系統遷移到新的多重角色系統"""
        from database import SessionLocal
        db = SessionLocal()
        try:
            # 獲取所有現有用戶
            legacy_users = db.query(User).all()
            
            for user in legacy_users:
                # 假設舊系統有 role 字段
                if hasattr(user, 'role'):
                    legacy_role = user.role
                    
                    # 創建默認機構角色記錄
                    # 這裡需要根據實際業務邏輯調整
                    default_institution = db.query(School).first()
                    if default_institution:
                        role_record = UserInstitutionRole(
                            user_id=user.id,
                            institution_id=default_institution.id,
                            roles=[legacy_role],  # 轉換為數組
                            permissions={},
                            created_by=user.id  # 自己創建
                        )
                        db.add(role_record)
            
            db.commit()
            print("角色遷移完成！")
            
        except Exception as e:
            db.rollback() 
            print(f"角色遷移失敗: {e}")
        finally:
            db.close()

# 示例用法
if __name__ == "__main__":
    # 檢查權限示例
    user_id = "user-123"
    institution_id = "institution-456"
    
    # 檢查是否可以創建班級
    can_create = RoleChecker.can_access_resource(user_id, institution_id, "create_class")
    print(f"Can create class: {can_create}")
    
    # 檢查是否有教師角色
    is_teacher = RoleChecker.has_institution_role(user_id, institution_id, "teacher")
    print(f"Is teacher: {is_teacher}")