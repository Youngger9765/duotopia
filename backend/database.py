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


def get_pool_config():
    """獲取連線池配置參數

    根據部署環境返回最佳的連線池配置：
    - Cloud Run Production: 較大的連線池 (20+10)
    - Supabase Free Tier: 較小的連線池 (10+10)
    - Local Development: 最小連線池 (5+5)

    Issue #93: Optimized connection pool configuration
    """
    # 檢測部署環境
    environment = os.getenv("ENVIRONMENT", "local")

    if environment == "production":
        # Cloud Run Production: 優化高並發處理
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "10")),
        }
    elif environment == "staging":
        # Staging: 中等配置
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "15")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "10")),
        }
    else:
        # Local: 最小配置
        return {
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "5")),
            "pool_timeout": int(os.getenv("DB_POOL_TIMEOUT", "10")),
        }


def get_engine():
    """延遲建立資料庫引擎

    Connection pool configuration (Issue #93 - 2024-12-11):
    - Production (Cloud Run): pool_size=20, max_overflow=10 (total: 30)
    - Staging: pool_size=15, max_overflow=10 (total: 25)
    - Local: pool_size=5, max_overflow=5 (total: 10)
    - pool_pre_ping=True: Health check before using connection
    - pool_recycle=3600: Recycle connections every hour to avoid idle timeouts
    - pool_timeout=10: Faster failure feedback

    Previous history:
    - FIX #5 (2024-12-10): Reduced to 10+10 for Supabase Free Tier
    - Issue #93 (2024-12-11): Optimized for Cloud Run with environment-based config

    NOTE: If running multiple backend instances, total connections = pool_size × instances
    """
    global _engine
    if _engine is None:
        # Issue #93: Environment-based pool configuration
        pool_config = get_pool_config()

        _engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,  # 每次取得連線前先測試，防止使用斷線的連線
            pool_recycle=3600,  # 1小時回收連線，避免長時間閒置被關閉
            pool_size=pool_config["pool_size"],  # 連線池大小 (環境自適應)
            max_overflow=pool_config["max_overflow"],  # 最大溢出連線數 (環境自適應)
            pool_timeout=pool_config["pool_timeout"],  # 連線等待超時
            connect_args={
                "connect_timeout": 10,  # 連線超時 10 秒
                "options": "-c statement_timeout=30000",  # SQL 執行超時 30 秒
            },
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
