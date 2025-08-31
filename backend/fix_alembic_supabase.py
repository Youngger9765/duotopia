#!/usr/bin/env python3
"""
Fix Alembic version in Supabase database
This script updates the alembic_version table from '001' to the correct revision ID
"""

import os
import sys
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase DATABASE_URL from environment or command line
if len(sys.argv) > 1:
    DATABASE_URL = sys.argv[1]
else:
    # Try to get from environment
    DATABASE_URL = os.getenv('SUPABASE_DATABASE_URL') or os.getenv('DATABASE_URL')
    
if not DATABASE_URL or 'supabase' not in DATABASE_URL:
    print("❌ Error: Please provide Supabase DATABASE_URL as argument or set SUPABASE_DATABASE_URL environment variable")
    print("Usage: python fix_alembic_supabase.py 'postgresql://...'")
    sys.exit(1)

print(f"🔄 Connecting to Supabase database...")
print(f"   URL: {DATABASE_URL[:50]}...")

try:
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Check current alembic version
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        current_version = result.fetchone()
        
        if current_version:
            current = current_version[0]
            print(f"📍 Current alembic version: {current}")
            
            if current == '001':
                print("⚠️  Found incorrect version '001', updating to '624bfd9ff075'...")
                conn.execute(text("UPDATE alembic_version SET version_num = '624bfd9ff075' WHERE version_num = '001'"))
                conn.commit()
                print("✅ Successfully updated alembic version to '624bfd9ff075'")
            elif current == '624bfd9ff075':
                print("✅ Alembic version is already correct!")
            elif current == '87293915d363':
                print("✅ Alembic version is at the latest migration!")
            else:
                print(f"⚠️  Unknown version: {current}")
        else:
            print("⚠️  No alembic version found in database")
            print("   Initializing with correct version...")
            conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('624bfd9ff075')"))
            conn.commit()
            print("✅ Initialized alembic version to '624bfd9ff075'")
            
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n🎉 Done! You can now run migrations successfully.")