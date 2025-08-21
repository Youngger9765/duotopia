"""
Pytest fixtures for dual system testing
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from database import Base
from models import User, School, UserRole
import models_v2  # 確保新模型的表也被創建
import uuid

# 使用內存資料庫進行測試
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db():
    """創建測試用的資料庫會話"""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # 創建所有表
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_school(db: Session):
    """創建測試用的學校"""
    school = School(
        id=str(uuid.uuid4()),
        name="測試國小",
        code="TEST001",
        address="台北市測試區"
    )
    db.add(school)
    db.commit()
    return school

@pytest.fixture
def sample_teacher(db: Session, sample_school):
    """創建測試用的機構教師"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="inst_teacher@test.com",
        full_name="機構老師",
        role=UserRole.TEACHER,
        is_individual_teacher=False,
        is_institutional_admin=True,
        current_role_context="institutional",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    return teacher

@pytest.fixture
def sample_individual_teacher(db: Session):
    """創建測試用的個體戶教師"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="individual_teacher@test.com",
        full_name="個體戶老師",
        role=UserRole.TEACHER,
        is_individual_teacher=True,
        is_institutional_admin=False,
        current_role_context="individual",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    return teacher

@pytest.fixture
def sample_hybrid_teacher(db: Session):
    """創建測試用的混合型教師"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="hybrid_teacher@test.com",
        full_name="混合型老師",
        role=UserRole.TEACHER,
        is_individual_teacher=True,
        is_institutional_admin=True,
        current_role_context="default",
        hashed_password="hashed"
    )
    db.add(teacher)
    db.commit()
    return teacher