#!/usr/bin/env python3
"""
初始化 Supabase 資料庫架構
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# 載入環境變數
load_dotenv('.env.staging')

# 添加 backend 到 Python path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

def init_database():
    """初始化資料庫架構"""
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        print("❌ DATABASE_URL 未設定")
        return False
    
    print(f"🔄 連接到 Supabase...")
    print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")
    
    try:
        # 建立連接
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # 建立 Alembic 版本表（如果不存在）
        print("📊 建立資料庫架構...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
        """)
        
        # 檢查是否需要初始化
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        table_count = cursor.fetchone()[0]
        
        if table_count <= 1:  # 只有 alembic_version
            print("📦 執行資料庫遷移...")
            os.chdir(backend_path)
            os.system("alembic upgrade head")
            print("✅ 資料庫架構建立完成")
        else:
            print("ℹ️ 資料庫已有表格，跳過初始化")
        
        # 驗證表格
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 現有表格 ({len(tables)} 個):")
        for table in tables:
            print(f"   - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Supabase 資料庫初始化成功！")
        return True
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return False

if __name__ == "__main__":
    init_database()