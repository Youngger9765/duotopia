#!/usr/bin/env python3
"""
Reset database - drop all tables and recreate
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import engine, Base, SessionLocal
from models import *


def reset_database():
    """Drop all tables and recreate"""
    print("⚠️  正在重置資料庫...")

    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    print("✅ 所有表格已刪除")

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ 所有表格已重建")

    # Test connection
    db = SessionLocal()
    try:
        # Test query
        db.execute("SELECT 1")
        print("✅ 資料庫連接正常")
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
    print("\n🎯 資料庫已重置完成！")
    print("現在可以執行 seed_data.py 來載入測試資料")
