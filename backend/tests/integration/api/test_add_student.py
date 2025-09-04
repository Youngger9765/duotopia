#!/usr/bin/env python3
"""
測試新增學生功能
"""

import requests
import json
from datetime import datetime  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_add_student():
    """測試新增學生"""
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
        return

    teacher_data = response.json()
    token = teacher_data["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✅ 教師登入成功: {teacher_data['user']['name']}")

    # 2. 取得班級列表
    print("\n2. 取得班級列表...")
    response = session.get(f"{BASE_URL}/teachers/classrooms")

    if response.status_code != 200:
        print(f"❌ 取得班級失敗: {response.status_code}")
        return

    classrooms = response.json()
    if not classrooms:
        print("❌ 沒有班級")
        return

    classroom_id = classrooms[0]["id"]
    print(f"✅ 使用班級: {classrooms[0]['name']} (ID: {classroom_id})")

    # 3. 新增學生
    print("\n3. 新增學生...")
    student_data = {
        "name": "測試學生",
        "email": f"test_student_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-01-01",
        "classroom_id": classroom_id,
        "student_id": "TEST123",
    }

    print(f"   發送資料: {json.dumps(student_data, indent=2, ensure_ascii=False)}")

    response = session.post(f"{BASE_URL}/teachers/students", json=student_data)

    print(f"   狀態碼: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("✅ 新增學生成功！")
        print(f"   學生ID: {result['id']}")
        print(f"   姓名: {result['name']}")
        print(f"   Email: {result['email']}")
        print(f"   預設密碼: {result.get('default_password', 'N/A')}")
    else:
        print(f"❌ 新增學生失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.text}")

    # 4. 驗證學生是否真的被加入
    print("\n4. 驗證學生列表...")
    response = session.get(f"{BASE_URL}/classrooms/{classroom_id}/students")

    if response.status_code == 200:
        students = response.json()
        new_student = [s for s in students if s["name"] == "測試學生"]
        if new_student:
            print("✅ 確認學生已加入班級")
        else:
            print("⚠️  學生未出現在班級列表中")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 測試新增學生功能")
    print("=" * 60)
    test_add_student()
