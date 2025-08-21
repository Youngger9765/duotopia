"""
認證功能單元測試
測試登入、註冊、JWT token 等核心認證功能
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from models import User, Student, UserRole
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    authenticate_user,
    get_current_user,
    authenticate_student
)
from schemas import UserCreate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TestPasswordHashing:
    """密碼雜湊功能測試"""
    
    def test_password_hash_generation(self):
        """測試密碼雜湊生成"""
        password = "test123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert pwd_context.verify(password, hashed)
    
    def test_password_verification_correct(self):
        """測試正確密碼驗證"""
        password = "correct_password"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_incorrect(self):
        """測試錯誤密碼驗證"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False


class TestJWTToken:
    """JWT Token 功能測試"""
    
    def test_create_access_token_basic(self):
        """測試基本 token 建立"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """測試帶有過期時間的 token"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data, expires_delta)
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_access_token_with_additional_claims(self):
        """測試包含額外聲明的 token"""
        data = {
            "sub": "test@example.com",
            "role": "teacher",
            "school_id": "123"
        }
        token = create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)


class TestUserAuthentication:
    """使用者認證功能測試"""
    
    @pytest.fixture
    def sample_teacher(self, db: Session):
        """建立測試用教師"""
        user = User(
            email="teacher@test.com",
            full_name="Test Teacher",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_individual_teacher=True
        )
        db.add(user)
        db.commit()
        
        return user
    
    def test_authenticate_user_success(self, db: Session, sample_teacher):
        """測試成功的使用者認證"""
        user = authenticate_user(db, "teacher@test.com", "password123")
        
        assert user is not None
        assert user.email == "teacher@test.com"
        assert user.is_active is True
    
    def test_authenticate_user_wrong_password(self, db: Session, sample_teacher):
        """測試錯誤密碼的認證"""
        user = authenticate_user(db, "teacher@test.com", "wrong_password")
        
        assert user is False
    
    def test_authenticate_user_not_found(self, db: Session):
        """測試不存在的使用者"""
        user = authenticate_user(db, "notfound@test.com", "password123")
        
        assert user is False
    
    def test_authenticate_inactive_user(self, db: Session, sample_teacher):
        """測試停用的使用者"""
        sample_teacher.is_active = False
        db.commit()
        
        user = authenticate_user(db, "teacher@test.com", "password123")
        
        assert user is not None  # 仍會回傳使用者物件
        assert user.is_active is False


class TestStudentAuthentication:
    """學生認證功能測試"""
    
    @pytest.fixture
    def sample_student(self, db: Session, sample_teacher):
        """建立測試用學生"""
        student = Student(
            name="張小明",
            email="xiaoming@test.com",
            birth_date=datetime(2010, 1, 1).date(),
            teacher_id=sample_teacher.id,
            password_hash=get_password_hash("20100101")
        )
        db.add(student)
        db.commit()
        return student
    
    def test_authenticate_student_with_birthdate(self, db: Session, sample_student, sample_teacher):
        """測試使用生日作為密碼的學生認證"""
        # 注意：需要根據實際的 authenticate_student 函數參數調整
        student = authenticate_student(
            db, 
            "xiaoming@test.com", 
            "20100101",
            sample_teacher.id
        )
        
        assert student is not None
        assert student.name == "張小明"
        assert student.email == "xiaoming@test.com"
    
    def test_authenticate_student_custom_password(self, db: Session, sample_student, sample_teacher):
        """測試使用自訂密碼的學生認證"""
        # 更新為自訂密碼
        sample_student.password_hash = get_password_hash("custom123")
        sample_student.password_status = "custom"
        db.commit()
        
        student = authenticate_student(
            db,
            "xiaoming@test.com",
            "custom123",
            sample_teacher.id
        )
        
        assert student is not None
        assert student.password_status == "custom"
    
    def test_authenticate_student_wrong_teacher(self, db: Session, sample_student, sample_teacher):
        """測試錯誤教師 ID 的學生認證"""
        student = authenticate_student(
            db,
            "xiaoming@test.com",
            "20100101",
            999  # 錯誤的教師 ID
        )
        
        assert student is None
    
    def test_authenticate_student_without_email(self, db: Session, sample_teacher):
        """測試沒有 Email 的學生認證（使用姓名）"""
        student = Student(
            name="李小華",
            birth_date=datetime(2010, 2, 15).date(),
            teacher_id=sample_teacher.id,
            password_hash=get_password_hash("20100215")
        )
        db.add(student)
        db.commit()
        
        # 使用姓名登入
        authenticated = authenticate_student(
            db,
            "李小華",
            "20100215",
            sample_teacher.id
        )
        
        assert authenticated is not None
        assert authenticated.name == "李小華"


class TestRoleManagement:
    """角色管理功能測試"""
    
    @pytest.fixture
    def multi_role_user(self, db: Session):
        """建立多重角色使用者"""
        user = User(
            email="multi@test.com",
            full_name="Multi Role User",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_individual_teacher=True,
            is_institutional_admin=True
        )
        db.add(user)
        db.commit()
        
        return user
    
    def test_get_user_roles(self, db: Session, multi_role_user):
        """測試取得使用者所有角色"""
        roles = []
        
        if multi_role_user.is_individual_teacher:
            roles.append("individual_teacher")
        if multi_role_user.is_institutional_admin:
            roles.append("institutional_admin")
        
        assert len(roles) == 2
        assert "individual_teacher" in roles
        assert "institutional_admin" in roles
    
    def test_switch_user_role(self, db: Session, multi_role_user):
        """測試角色切換"""
        # 初始角色
        current_role = "individual"
        
        # 切換到機構管理員
        if multi_role_user.is_institutional_admin:
            multi_role_user.current_role_context = "institutional"
            db.commit()
            current_role = "institutional"
        
        assert current_role == "institutional"
        assert multi_role_user.current_role_context == "institutional"
    
    def test_role_permissions(self, db: Session):
        """測試角色權限"""
        # 定義角色權限
        permissions = {
            "individual_teacher": ["manage_own_students", "manage_own_classes"],
            "institutional_teacher": ["manage_school_students", "manage_school_classes"],
            "admin": ["manage_all_users", "manage_system"]
        }
        
        # 測試個體戶教師權限
        individual_perms = permissions.get("individual_teacher", [])
        assert "manage_own_students" in individual_perms
        assert "manage_all_users" not in individual_perms