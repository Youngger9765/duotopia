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


# 全域引擎，確保所有測試使用同一個
_test_engine = None


def get_test_engine():
    """獲取全域測試引擎"""
    global _test_engine
    if _test_engine is None:
        _test_engine = create_engine(
            "sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(_test_engine)
    return _test_engine


@pytest.fixture(scope="session")
def test_engine():
    """Create a shared test database engine"""
    return get_test_engine()


@pytest.fixture(scope="function")
def shared_test_session(test_engine):
    """Create a shared test database session that will be used by both test_session and test_client"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    # 在每個測試開始前清理所有資料
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.rollback()
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
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    # 在每個測試開始前清理所有資料
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
