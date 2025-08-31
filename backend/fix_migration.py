#!/usr/bin/env python3
"""
自動修復 Alembic migration revision 格式問題
避免手動操作錯誤
"""
import os
import sys
from sqlalchemy import create_engine, text
from pathlib import Path

# 正確的 revision 映射
REVISION_MAPPING = {
    '001': '624bfd9ff075',  # 初始 schema
    '13ed6b11e858': '624bfd9ff075',  # 錯誤的 revision
}

def fix_migration_version(database_url: str, env_name: str = "Unknown"):
    """修復特定資料庫的 migration version"""
    try:
        engine = create_engine(database_url)
        with engine.connect() as conn:
            # 檢查 alembic_version 表是否存在
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alembic_version'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                print(f"   ⚠️  {env_name}: No alembic_version table found")
                print(f"      Creating table with correct revision...")
                # 建立 alembic_version 表
                conn.execute(text("""
                    CREATE TABLE alembic_version (
                        version_num VARCHAR(32) NOT NULL PRIMARY KEY
                    )
                """))
                conn.execute(text("INSERT INTO alembic_version VALUES ('624bfd9ff075')"))
                conn.commit()
                print(f"   ✅ {env_name}: Created alembic_version table with correct revision")
                return True
            
            # 檢查現有 version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
            
            if current in REVISION_MAPPING:
                new_version = REVISION_MAPPING[current]
                conn.execute(text(f"UPDATE alembic_version SET version_num = '{new_version}'"))
                conn.commit()
                print(f"   ✅ {env_name}: Fixed revision {current} → {new_version}")
                return True
            elif current == '624bfd9ff075':
                print(f"   ✅ {env_name}: Already has correct revision")
                return True
            elif current == '87293915d363':
                print(f"   ✅ {env_name}: Already migrated to latest")
                return True
            else:
                print(f"   ⚠️  {env_name}: Unknown revision {current}")
                return False
                
    except Exception as e:
        print(f"   ❌ {env_name}: {str(e)}")
        return False

def fix_local():
    """修復本地資料庫"""
    local_url = "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"
    return fix_migration_version(local_url, "Local")

def fix_staging(staging_url=None):
    """修復 staging 資料庫"""
    if not staging_url:
        # 嘗試從 .env.staging 讀取
        env_file = Path(__file__).parent / '.env.staging'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('DATABASE_URL='):
                        staging_url = line.split('=', 1)[1].strip()
                        break
    
    if not staging_url:
        print("   ❌ Staging: No DATABASE_URL provided")
        return False
    
    return fix_migration_version(staging_url, "Staging")

def main():
    """主程式：修復所有環境"""
    print("🔧 Fixing Alembic migration revision format...")
    print("")
    
    # 修復本地
    print("1. Local database:")
    fix_local()
    print("")
    
    # 修復 staging
    print("2. Staging database:")
    staging_url = os.getenv('DATABASE_URL')
    fix_staging(staging_url)
    print("")
    
    print("✅ Migration fix complete!")
    print("")
    print("Next steps:")
    print("  - Local: alembic upgrade head")
    print("  - Staging: make db-upgrade-staging")

if __name__ == "__main__":
    main()