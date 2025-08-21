"""
基礎認證功能單元測試
測試密碼雜湊、JWT token 和基本認證功能
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os

# 設置測試環境變數
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-tests"

from models import User, Student, UserRole
from auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    authenticate_user,
    authenticate_student
)

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
            is_active=True
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


class TestStudentAuthentication:
    """學生認證功能測試"""
    
    @pytest.fixture
    def sample_student(self, db: Session):
        """建立測試用學生"""
        student = Student(
            email="student@test.com",
            full_name="測試學生",
            birth_date="20100101",
            name="測試學生"
        )
        db.add(student)
        db.commit()
        return student
    
    def test_authenticate_student_with_birthdate(self, db: Session, sample_student):
        """測試使用生日作為密碼的學生認證"""
        student = authenticate_student(db, "student@test.com", "20100101")
        
        assert student is not None
        assert student.email == "student@test.com"
        assert student.birth_date == "20100101"