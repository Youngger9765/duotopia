from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
)

# 🔧 延遲載入：只在實際使用時才建立資料庫連線
# 這樣 conftest.py 可以在沒有 DATABASE_URL 的情況下被載入（單元測試）
_engine = None
_SessionLocal = None


def get_engine():
    """延遲建立資料庫引擎

    Connection pool configuration (2024-12-10):
    - FIX #5: Reduced to safer values for Supabase Free Tier (~25 connection limit)
    - pool_size=10: Base pool always kept alive (was 15)
    - max_overflow=10: Additional connections created on demand (was 15)
    - Total: 20 connections per instance (safer for Supabase Free Tier)
    - pool_timeout=10: Faster failure feedback (down from default 30s)
    - pool_recycle=3600: Recycle connections every hour to avoid idle timeouts
    - pool_pre_ping=True: Health check before using connection

    This fixes production issue where 20 concurrent audio uploads exhausted
    the previous 15-connection limit, causing timeout errors.

    NOTE: If running multiple backend instances, total connections = pool_size × instances
    """
    global _engine
    if _engine is None:
        # FIX #5: Safer configuration for Supabase Free Tier
        # Read pool configuration from environment variables with safe defaults
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))  # Was 15
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))  # Was 15
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "10"))

        # SQLite vs PostgreSQL specific configurations
        connect_args = {}
        if DATABASE_URL.startswith("postgresql"):
            connect_args = {
                "connect_timeout": 10,  # 連線超時 10 秒
                "options": "-c statement_timeout=30000",  # SQL 執行超時 30 秒
            }
        elif DATABASE_URL.startswith("sqlite"):
            connect_args = {
                "check_same_thread": False  # SQLite: Allow multiple threads
            }

        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # 每次取得連線前先測試，防止使用斷線的連線
            pool_recycle=3600,  # 1小時回收連線，避免長時間閒置被關閉
            pool_size=pool_size,  # 連線池大小 (default: 10)
            max_overflow=max_overflow,  # 最大溢出連線數 (default: 10)
            pool_timeout=pool_timeout,  # 連線等待超時 (降低: 30s → 10s 快速失敗)
            connect_args=connect_args,
        )
    return _engine


def get_session_local():
    """延遲建立 Session maker"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=get_engine()
        )
    return _SessionLocal


# Backward compatibility for code expecting SessionLocal symbol
SessionLocal = get_session_local()

Base = declarative_base()


def get_db():
    """取得資料庫 session"""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化資料庫 - 應該使用 alembic 管理 schema"""
    import models  # noqa: F401 - Import models to register them

    # 🚨 不再直接使用 create_all，改用 alembic 管理
    # Base.metadata.create_all(bind=engine)

    print("⚠️  請使用 alembic upgrade head 來建立資料表")
    print("   不要直接使用 init_db() 繞過 alembic 管理")
