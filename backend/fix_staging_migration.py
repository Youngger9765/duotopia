#!/usr/bin/env python3
"""
Fix Supabase staging migration revision issue
"""
import os
import sys
from sqlalchemy import create_engine, text

# Supabase staging DATABASE_URL 需要從 GitHub Secrets 或環境變數取得
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ 請設定 DATABASE_URL 環境變數")
    print("使用方式:")
    print("export DATABASE_URL='postgresql://...' && python fix_staging_migration.py")
    sys.exit(1)


def fix_migration():
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        try:
            # 先檢查 alembic_version 表是否存在
            result = conn.execute(
                text(
                    """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'alembic_version'
                )
            """
                )
            )
            table_exists = result.fetchone()[0]

            if table_exists:
                # 清空舊的 revision
                conn.execute(text("DELETE FROM alembic_version"))
                print("✅ 已清空舊的 migration revision")

                # 設定為我們最新的 revision
                conn.execute(
                    text(
                        """
                    INSERT INTO alembic_version (version_num)
                    VALUES ('6c42743b461f')
                """
                    )
                )
                conn.commit()
                print("✅ 已設定新的 migration revision: 6c42743b461f")
            else:
                print("⚠️ alembic_version 表不存在，將由 alembic upgrade head 自動建立")

        except Exception as e:
            print(f"❌ 錯誤: {e}")
            sys.exit(1)


if __name__ == "__main__":
    fix_migration()
    print("\n現在可以執行:")
    print("alembic upgrade head")
