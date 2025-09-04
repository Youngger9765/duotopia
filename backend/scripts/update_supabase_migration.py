#!/usr/bin/env python3
"""
更新 Supabase 資料庫的 Alembic migration version
解決 revision ID 格式問題
"""
import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


def update_supabase_migration():
    """更新 Supabase 的 alembic_version 表"""

    # 載入環境變數
    load_dotenv(".env.staging")

    # 取得 Supabase DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ 錯誤：找不到 DATABASE_URL 環境變數")
        print("請確保 .env.staging 檔案包含 Supabase DATABASE_URL")
        sys.exit(1)

    # 確認是 Supabase URL
    if "supabase" not in database_url:
        print("⚠️  警告：DATABASE_URL 看起來不是 Supabase URL")
        response = input("繼續嗎？ (y/n): ")
        if response.lower() != "y":
            sys.exit(0)

    try:
        # 連接資料庫
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # 1. 檢查現有的 version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.fetchone()

            if current_version:
                print(f"📍 現有 version: {current_version[0]}")

                # 2. 更新為正確的 revision ID
                if current_version[0] == "13ed6b11e858" or current_version[0] == "001":
                    print("🔄 更新 alembic_version 到正確格式...")
                    conn.execute(
                        text("UPDATE alembic_version SET version_num = '624bfd9ff075'")
                    )
                    conn.commit()
                    print("✅ 已更新到初始 migration: 624bfd9ff075")
                elif current_version[0] == "624bfd9ff075":
                    print("✅ Version 已經是正確格式")
                else:
                    print(f"⚠️  未預期的 version: {current_version[0]}")
            else:
                print("❌ 找不到 alembic_version 記錄")
                print("建議先執行: alembic stamp 624bfd9ff075")

        print("\n📝 接下來的步驟：")
        print("1. 設定 Supabase DATABASE_URL:")
        print("   export DATABASE_URL='your-supabase-url'")
        print("2. 執行 migration:")
        print("   alembic upgrade head")
        print("3. 或使用 Makefile:")
        print("   make db-upgrade")

    except Exception as e:
        print(f"❌ 錯誤：{e}")
        sys.exit(1)


if __name__ == "__main__":
    update_supabase_migration()
