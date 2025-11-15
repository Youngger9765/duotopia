"""
Pytest configuration for test isolation

確保測試使用獨立的測試資料庫，不污染生產環境
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import os


# 測試資料庫 URL（使用 SQLite in-memory 或獨立的測試資料庫）
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "sqlite:///./test.db"  # 使用獨立的測試資料庫檔案
)


@pytest.fixture(scope="session")
def test_engine():
    """創建測試資料庫引擎"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
        if "sqlite" in TEST_DATABASE_URL
        else {},
    )

    # 創建所有表
    Base.metadata.create_all(bind=engine)

    yield engine

    # 測試結束後清理
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """為每個測試函數提供獨立的資料庫 session"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # 創建新 session
    session = TestSessionLocal()

    yield session

    # 測試結束後 rollback 並關閉
    session.rollback()
    session.close()

    # 清理測試資料
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()


@pytest.fixture(autouse=True)
def override_get_db(test_db_session):
    """自動覆寫 get_db dependency，讓所有測試使用測試資料庫"""

    def _get_test_db():
        try:
            yield test_db_session
        finally:
            pass

    # 這裡不實際覆寫，而是在測試中手動傳入 test_db_session
    # 因為我們的測試直接呼叫函數而不是透過 FastAPI dependency injection
    pass
