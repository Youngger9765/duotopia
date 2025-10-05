#!/usr/bin/env python3
"""設置兩個測試帳號用於 pricing 頁面測試"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from passlib.context import CryptContext  # noqa: E402

from models import Teacher  # noqa: E402
from database import DATABASE_URL  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def setup_test_accounts():
    """設置測試帳號"""

    # Create database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        now = datetime.now(timezone.utc)

        # 1. Demo 老師 - 有訂閱身份（已充值 30 天）
        demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        if not demo:
            demo = Teacher(
                email="demo@duotopia.com",
                name="Demo Teacher",
                password_hash=pwd_context.hash("demo123"),
                email_verified=True,
                created_at=now,
            )
            db.add(demo)
        else:
            # 更新密碼（如果帳號已存在）
            demo.password_hash = pwd_context.hash("demo123")

        # 設置有效訂閱
        demo.subscription_end_date = now + timedelta(days=30)
        demo.subscription_type = "Tutor Teachers"

        print("✅ Demo 老師設置完成:")
        print("   Email: demo@duotopia.com")
        print("   Password: demo123")
        print(f"   訂閱到期日: {demo.subscription_end_date}")
        print(f"   剩餘天數: {demo.days_remaining}")

        # 2. Expired 老師 - 訂閱已過期
        expired = db.query(Teacher).filter_by(email="expired@duotopia.com").first()
        if not expired:
            expired = Teacher(
                email="expired@duotopia.com",
                name="Expired Teacher",
                password_hash=pwd_context.hash("demo123"),  # 統一使用 demo123
                email_verified=True,
                created_at=now,
            )
            db.add(expired)
        else:
            # 更新密碼（如果帳號已存在）
            expired.password_hash = pwd_context.hash("demo123")  # 統一使用 demo123

        # 設置為過期狀態（昨天到期）
        expired.subscription_end_date = now - timedelta(days=1)
        expired.subscription_type = None

        print("\n✅ Expired 老師設置完成:")
        print("   Email: expired@duotopia.com")
        print("   Password: demo123")
        print(f"   訂閱到期日: {expired.subscription_end_date}")
        print(f"   剩餘天數: {expired.days_remaining}")

        db.commit()

        print("\n🎉 測試帳號設置完成！")
        print("\n可用帳號（密碼統一為 demo123）：")
        print("1. demo@duotopia.com / demo123 (有訂閱)")
        print("2. expired@duotopia.com / demo123 (訂閱過期)")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    setup_test_accounts()
