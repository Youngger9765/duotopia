#!/usr/bin/env python3
"""清除 demo 老師的訂閱資格，讓 pricing 頁面可以正常顯示"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime, timedelta, timezone  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from models import Teacher  # noqa: E402
from database import DATABASE_URL  # noqa: E402


def clear_demo_subscription():
    """清除 demo@duotopia.com 的訂閱資格"""

    # Create database connection
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Find demo teacher
        demo = db.query(Teacher).filter_by(email="demo@duotopia.com").first()

        if not demo:
            print("❌ demo@duotopia.com 老師不存在")
            return

        print("📋 當前訂閱狀態:")
        print(f"  - 訂閱類型: {demo.subscription_type}")
        print(f"  - 訂閱到期日: {demo.subscription_end_date}")
        print(f"  - 剩餘天數: {demo.days_remaining}")

        # Set subscription to expired (yesterday)
        now = datetime.now(timezone.utc)
        demo.subscription_end_date = now - timedelta(days=1)
        demo.subscription_type = None

        db.commit()

        print("\n✅ 已清除 demo 老師訂閱:")
        print(f"  - 訂閱到期日: {demo.subscription_end_date}")
        print(f"  - 剩餘天數: {demo.days_remaining}")
        print("\n現在可以訪問 http://localhost:5173/pricing 測試付款流程了！")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    clear_demo_subscription()
