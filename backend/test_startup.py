#!/usr/bin/env python3
"""測試啟動流程"""
import os
import sys

print("=" * 50)
print("Testing Duotopia Backend Startup")
print("=" * 50)

# 1. 檢查環境變數
print("\n1. Checking environment variables:")
print(f"   DATABASE_URL: {'✅ Set' if os.getenv('DATABASE_URL') else '❌ Not set'}")
print(f"   JWT_SECRET: {'✅ Set' if os.getenv('JWT_SECRET') else '❌ Not set'}")
print(f"   PORT: {os.getenv('PORT', 'Not set (default 8080)')}")

# 2. 測試 imports
print("\n2. Testing imports:")
try:
    import fastapi
    print("   ✅ FastAPI imported")
except Exception as e:
    print(f"   ❌ FastAPI import failed: {e}")
    sys.exit(1)

try:
    import uvicorn
    print("   ✅ Uvicorn imported")
except Exception as e:
    print(f"   ❌ Uvicorn import failed: {e}")
    sys.exit(1)

try:
    import sqlalchemy
    print("   ✅ SQLAlchemy imported")
except Exception as e:
    print(f"   ❌ SQLAlchemy import failed: {e}")
    sys.exit(1)

# 3. 測試 main.py
print("\n3. Testing main.py import:")
try:
    import main
    print("   ✅ main.py imported successfully")
except Exception as e:
    print(f"   ❌ main.py import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 4. 測試 app 創建
print("\n4. Testing FastAPI app creation:")
try:
    app = main.app
    print("   ✅ FastAPI app created")
except Exception as e:
    print(f"   ❌ App creation failed: {e}")
    sys.exit(1)

print("\n✅ All startup tests passed!")
print("=" * 50)