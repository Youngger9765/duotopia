#!/usr/bin/env python3
"""
直接在 Supabase 建立所有表格
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

from sqlalchemy import create_engine
from database import Base
import models  # 確保所有模型都被載入

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"🔄 連接到 Supabase...")
print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")

# 建立引擎
engine = create_engine(DATABASE_URL)

# 建立所有表格
print("📊 建立資料庫表格...")
Base.metadata.create_all(bind=engine)

print("✅ 所有表格已建立！")

# 驗證
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\n📋 已建立的表格 ({len(tables)} 個):")
for table in sorted(tables):
    print(f"   - {table}")

engine.dispose()