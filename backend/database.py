from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
)

# 🔧 資料庫連線池優化 - 防止 SSL SYSCALL EOF 錯誤
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 每次取得連線前先測試，防止使用斷線的連線
    pool_recycle=3600,  # 1小時回收連線，避免長時間閒置被關閉
    pool_size=5,  # 連線池大小
    max_overflow=10,  # 最大溢出連線數
    connect_args={
        "connect_timeout": 10,  # 連線超時 10 秒
        "options": "-c statement_timeout=30000",  # SQL 執行超時 30 秒
    },
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
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
