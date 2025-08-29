#!/usr/bin/env python3
"""
測試 Supabase 連接
"""
import psycopg2
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('.env.staging')

def test_connection():
    """測試資料庫連接"""
    try:
        # Supabase 連接字串
        DATABASE_URL = os.getenv('DATABASE_URL')
        
        if not DATABASE_URL:
            print("❌ DATABASE_URL 未設定")
            return False
            
        print(f"🔄 連接到 Supabase...")
        print(f"   URL: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")
        
        # 建立連接
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # 測試查詢
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ 連接成功！")
        print(f"   PostgreSQL 版本: {version[0].split(',')[0]}")
        
        # 檢查現有表格
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"\n📊 現有表格 ({len(tables)} 個):")
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = cursor.fetchone()[0]
                print(f"   - {table[0]}: {count} 筆資料")
        else:
            print("\n📊 資料庫是空的（需要初始化）")
        
        # 關閉連接
        cursor.close()
        conn.close()
        
        print("\n🎉 Supabase 連接測試成功！")
        print("💡 提示：這是免費的 Supabase，不會產生費用")
        return True
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return False

def show_connection_info():
    """顯示連接資訊"""
    print("\n" + "="*50)
    print("📋 Supabase 連接資訊")
    print("="*50)
    print(f"Project URL: {os.getenv('SUPABASE_URL', 'Not set')}")
    print(f"Database Type: {os.getenv('DATABASE_TYPE', 'Not set')}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'Not set')}")
    print(f"Daily Cost: $0.00 (Supabase Free Tier)")
    print("="*50)

if __name__ == "__main__":
    show_connection_info()
    test_connection()