#!/usr/bin/env python3
"""
測試422錯誤
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"


def test_422_error():
    """測試新增學生時的422錯誤"""
    session = requests.Session()

    # 1. 教師登入
    print("1. 教師登入...")
    response = session.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        return

    teacher_data = response.json()
    token = teacher_data["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✅ 教師登入成功")

    # 2. 測試有問題的資料
    print("\n2. 測試新增學生（有問題的資料）...")

    # 使用時間戳確保email唯一
    timestamp = int(datetime.now().timestamp())

    # 測試各種可能導致422的情況
    test_cases = [
        {
            "name": "缺少班級ID",
            "data": {
                "name": "sss",
                "email": f"student_{timestamp}_1@example.com",
                "birthdate": "2025-02-01",
                # 缺少 classroom_id
            },
        },
        {
            "name": "錯誤的日期格式",
            "data": {
                "name": "sss",
                "email": f"student_{timestamp}_2@example.com",
                "birthdate": "2025/02/01",  # 錯誤格式
                "classroom_id": 1,
            },
        },
        {
            "name": "正確的資料",
            "data": {
                "name": "sss",
                "email": f"student_{timestamp}_3@example.com",
                "birthdate": "2025-02-01",
                "classroom_id": 1,
                "student_id": "",  # 空字串
                "phone": "0912345678",
            },
        },
    ]

    for test_case in test_cases:
        print(f"\n測試: {test_case['name']}")
        print(f"資料: {json.dumps(test_case['data'], indent=2, ensure_ascii=False)}")

        response = session.post(f"{BASE_URL}/teachers/students", json=test_case["data"])

        print(f"狀態碼: {response.status_code}")

        if response.status_code == 422:
            print(f"422 錯誤詳情:")
            error_detail = response.json()
            print(json.dumps(error_detail, indent=2, ensure_ascii=False))
        elif response.status_code == 200:
            print("✅ 成功")
            result = response.json()
            print(f"   學生ID: {result.get('id')}")
        else:
            print(f"其他錯誤: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 測試422錯誤")
    print("=" * 60)
    test_422_error()
