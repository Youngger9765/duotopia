#!/usr/bin/env python3
"""
Seed Supabase 資料庫
建立 Demo 教師、學生、班級、課程、作業
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('.env.staging')

# 添加 backend 到 Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# 設定環境變數給 SQLAlchemy
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL')

def seed_database():
    """執行資料庫 seed"""
    print("🌱 開始 Seed Supabase 資料庫...")

    DATABASE_URL = os.getenv('DATABASE_URL')
    if not DATABASE_URL:
        print("❌ DATABASE_URL 未設定")
        return False

    print(f"📊 連接到: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")

    # 切換到 backend 目錄執行 seed
    os.chdir(backend_path)

    # 執行原本的 seed_data.py
    os.system("python seed_data.py")

    print("✅ Supabase 資料庫 Seed 完成！")
    return True

if __name__ == "__main__":
    seed_database()
