from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
)

# 修復 Supabase 的 DATABASE_URL 格式問題
# Supabase 提供 postgres:// 但 SQLAlchemy 需要 postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
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
