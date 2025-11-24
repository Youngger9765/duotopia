"""
Global pytest configuration
統一的測試配置，確保所有測試使用相同的資料庫設置
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from database import Base, get_db
from main import app
import models  # noqa: F401 - Import models to register them
from models import (
    Teacher,
    Classroom,
    Assignment,
    AssignmentContent,
    Content,
    ContentType,
    Lesson,
    Program,
)
from auth import get_password_hash, create_access_token


# 全域引擎，確保所有測試使用同一個
_test_engine = None


def get_test_engine():
    """獲取全域測試引擎"""
    global _test_engine
    if _test_engine is None:
        # 🔧 使用 file-based SQLite 而不是 in-memory
        # in-memory database 在 FastAPI TestClient 的異步環境中可能無法正確共享
        _test_engine = create_engine(
            "sqlite:///./test.db", echo=False, connect_args={"check_same_thread": False}
        )
        # checkfirst=True: 避免平行測試時重複創建表
        Base.metadata.create_all(_test_engine, checkfirst=True)
    return _test_engine


@pytest.fixture(scope="session")
def test_engine(request):
    """Create a shared test database engine"""
    # Skip for tests that don't need database
    # This is checked at session level to avoid creating engine at all
    engine = get_test_engine()
    yield engine
    # 🧹 Cleanup: 刪除測試資料庫檔案
    import os

    if os.path.exists("./test.db"):
        os.remove("./test.db")


@pytest.fixture(scope="function", autouse=True)
def ensure_tables(test_engine, request):
    """🔧 Ensure tables exist before EVERY test (autouse)"""
    # Skip database setup for tests marked with no_db
    if "no_db" in request.keywords:
        yield
        return

    # checkfirst=True: 避免平行測試時重複創建表
    Base.metadata.create_all(bind=test_engine, checkfirst=True)
    yield
    # Cleanup happens in shared_test_session


@pytest.fixture(scope="function")
def shared_test_session(test_engine):
    """Create a shared test database session that will be used by both test_session and test_client"""
    # 🔧 確保 tables 存在（每個測試開始前都檢查）
    # checkfirst=True: 避免平行測試時重複創建表
    Base.metadata.create_all(bind=test_engine, checkfirst=True)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    # 🔧 清理所有資料（保留 schema）
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    except Exception:
        session.rollback()

    try:
        yield session
    finally:
        try:
            session.rollback()
        except Exception:
            pass
        finally:
            session.close()


@pytest.fixture(scope="function")
def test_session(shared_test_session):
    """Create a test database session that shares the same session as test_client"""
    return shared_test_session


@pytest.fixture(scope="function")
def test_client(shared_test_session):
    """Create a test client with database override using shared session"""

    def override_get_db():
        try:
            yield shared_test_session
        finally:
            pass  # Don't close the shared session here

    # 全域覆寫資料庫依賴
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            yield client
    finally:
        # 確保清理依賴覆寫
        app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """提供資料庫 session 的別名，支援舊有測試"""
    # 🔧 確保 tables 存在
    Base.metadata.create_all(bind=test_engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    # 🔧 清理所有資料（保留 schema）
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
    except Exception:
        session.rollback()

    try:
        yield session
    finally:
        try:
            session.rollback()
        except Exception:
            pass
        finally:
            session.close()


# Auth test fixtures
@pytest.fixture
def demo_teacher(shared_test_session):
    """Create a demo teacher for testing"""
    teacher = Teacher(
        email="test@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Test Teacher",
        is_active=True,
        is_demo=False,
        email_verified=True,  # Verified email
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def inactive_teacher(shared_test_session):
    """Create an inactive teacher for testing"""
    teacher = Teacher(
        email="inactive@duotopia.com",
        password_hash=get_password_hash("test123"),
        name="Inactive Teacher",
        is_active=False,  # Inactive account
        is_demo=False,
        email_verified=False,  # Not verified
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


# N+1 Query Test Fixtures
@pytest.fixture
def auth_headers_teacher(test_client, demo_teacher):
    """Create authentication headers for teacher"""
    access_token = create_access_token(
        data={"sub": str(demo_teacher.id), "type": "teacher"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_classroom(db_session, demo_teacher):
    """Create a test classroom"""
    classroom = Classroom(
        name="Test Classroom",
        teacher_id=demo_teacher.id,
        description="Test classroom for N+1 query tests",
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return {"id": classroom.id, "teacher_id": demo_teacher.id}


@pytest.fixture
def test_assignment(db_session, demo_teacher, test_classroom):
    """Create a test assignment with contents"""
    from datetime import datetime, timedelta

    # Create Program
    program = Program(
        name="Test Program",
        teacher_id=demo_teacher.id,
        classroom_id=test_classroom["id"],
        description="Test program for N+1 tests",
    )
    db_session.add(program)
    db_session.flush()

    # Create Lesson
    lesson = Lesson(
        program_id=program.id,
        name="Test Lesson",
        description="Test lesson for N+1 tests",
    )
    db_session.add(lesson)
    db_session.flush()

    # Create Assignment
    assignment = Assignment(
        title="Test Assignment",
        description="Test assignment for N+1 query tests",
        classroom_id=test_classroom["id"],
        teacher_id=demo_teacher.id,
        due_date=datetime.utcnow() + timedelta(days=7),
    )
    db_session.add(assignment)
    db_session.flush()

    # Create Contents and link to Assignment
    for i in range(3):
        content = Content(
            lesson_id=lesson.id,
            type=ContentType.READING_ASSESSMENT,
            title=f"Test Content {i+1}",
        )
        db_session.add(content)
        db_session.flush()

        assignment_content = AssignmentContent(
            assignment_id=assignment.id,
            content_id=content.id,
            order_index=i,
        )
        db_session.add(assignment_content)

    db_session.commit()
    db_session.refresh(assignment)

    return {
        "id": assignment.id,
        "teacher_id": demo_teacher.id,
        "classroom_id": test_classroom["id"],
    }
