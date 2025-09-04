#!/usr/bin/env python3
"""
重置 Alembic 版本並重新執行遷移
"""
import os
import psycopg2
from dotenv import load_dotenv

# 載入環境變數
load_dotenv('.env.staging')

DATABASE_URL = os.getenv('DATABASE_URL')
print(f"連接到: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

# 清空 alembic_version
cursor.execute("DELETE FROM alembic_version;")
conn.commit()

print("✅ 已清空 alembic_version 表")

cursor.close()
conn.close()
