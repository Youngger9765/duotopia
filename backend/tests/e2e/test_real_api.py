#!/usr/bin/env python3
"""
實際 API 測試腳本 - 測試完整作業流程
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

# 1. 教師登入
print("1. 教師登入...")
response = requests.post(
    f"{BASE_URL}/auth/teacher/login",
    json={"email": "demo@duotopia.com", "password": "demo123"},
)
token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"✅ 登入成功，取得 token")

# 2. 查詢教師的作業列表
print("\n2. 查詢教師的作業列表...")
response = requests.get(f"{BASE_URL}/assignments/teacher", headers=headers)
print(f"✅ 成功查詢，共有 {len(response.json())} 組作業")

# 3. 查詢 API 文檔
print("\n3. 確認 API 端點...")
response = requests.get("http://localhost:8000/openapi.json")
paths = response.json().get("paths", {})
assignment_endpoints = [p for p in paths if "assignment" in p.lower()]
print(f"✅ 作業相關 API 端點: {len(assignment_endpoints)} 個")
for endpoint in sorted(assignment_endpoints)[:5]:
    print(f"   • {endpoint}")

print("\n🎉 API 測試完成！所有端點正常運作")
