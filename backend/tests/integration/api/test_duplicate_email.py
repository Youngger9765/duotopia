#!/usr/bin/env python3
"""
測試email重複的錯誤處理
"""

import requests
import json  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_duplicate_email():
    """測試email重複"""
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
    print("✅ 教師登入成功")

    # 2. 測試重複的email
    print("\n2. 測試重複的email...")

    # 使用已存在的email
    student_data = {
        "name": "測試重複",
        "email": "student@example.com",  # 這個email已經存在
        "birthdate": "2025-02-01",
        "classroom_id": 1,
        "phone": "0912345678",
    }

    print(f"資料: {json.dumps(student_data, indent=2, ensure_ascii=False)}")

    response = session.post(f"{BASE_URL}/teachers/students", json=student_data)

    print(f"狀態碼: {response.status_code}")

    if response.status_code == 422:
        print("✅ 正確返回422錯誤")
        error_detail = response.json()
        print(f"錯誤訊息: {error_detail.get('detail', error_detail)}")
    elif response.status_code == 200:
        print("❌ 不應該成功")
    else:
        print(f"其他錯誤: {response.text}")


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 測試email重複錯誤處理")
    print("=" * 60)
    test_duplicate_email()
