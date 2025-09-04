#!/usr/bin/env python3
"""
測試新增班級功能
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def test_create_classroom():
    """測試新增班級"""
    session = requests.Session()

    # 1. 教師登入
    print("1. 教師登入...")
    response = session.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        print(response.text)
        return False

    teacher_data = response.json()
    token = teacher_data["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✅ 教師登入成功: {teacher_data['user']['name']}")

    # 2. 新增班級
    print("\n2. 新增班級...")
    classroom_data = {
        "name": f"測試班級 {datetime.now().strftime('%H:%M:%S')}",
        "description": "這是測試用的班級",
        "level": "A1",
    }

    print(f"   發送資料: {json.dumps(classroom_data, indent=2, ensure_ascii=False)}")

    response = session.post(f"{BASE_URL}/teachers/classrooms", json=classroom_data)

    print(f"   狀態碼: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")

    if response.status_code == 200:
        result = response.json()
        print("✅ 新增班級成功！")
        print(f"   班級ID: {result['id']}")
        print(f"   班級名稱: {result['name']}")
        print(f"   班級等級: {result['level']}")
        return result["id"]
    else:
        print(f"❌ 新增班級失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.text}")
        return None

    # 3. 驗證班級列表
    print("\n3. 驗證班級列表...")
    response = session.get(f"{BASE_URL}/teachers/classrooms")

    if response.status_code == 200:
        classrooms = response.json()
        new_classroom = [c for c in classrooms if c["name"].startswith("測試班級")]
        if new_classroom:
            print(f"✅ 確認班級已加入列表")
        else:
            print(f"⚠️  班級未出現在列表中")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 測試新增班級功能")
    print("=" * 60)
    test_create_classroom()
