"""
Pytest configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, get_db
from main import app
from models import Teacher, Student, Classroom
from auth import get_password_hash

# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create test client with test database"""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def demo_teacher(db):
    """Create a demo teacher for testing"""
    teacher = Teacher(
        email="test@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Test Teacher",
        is_active=True,
        is_demo=False,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def inactive_teacher(db):
    """Create an inactive teacher for testing"""
    teacher = Teacher(
        email="inactive@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Inactive Teacher",
        is_active=False,
        is_demo=False,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher
