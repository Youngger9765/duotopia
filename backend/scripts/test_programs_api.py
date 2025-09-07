#!/usr/bin/env python3
"""
測試公版課程 API 功能
"""

import requests
from datetime import datetime  # noqa: F401

BASE_URL = "http://localhost:8000"

# 教師登入資料
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """教師登入取得 token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )

    if response.status_code != 200:
        print(f"登入失敗: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    return data["access_token"]


def test_create_template(token):
    """測試建立公版課程模板"""
    headers = {"Authorization": f"Bearer {token}"}

    program_data = {
        "name": "公版英語會話課程",
        "description": "適合初學者的英語會話課程模板",
        "level": "A1",
        "estimated_hours": 20,
        "tags": ["speaking", "beginner", "conversation"],
    }

    response = requests.post(f"{BASE_URL}/api/programs/templates", headers=headers, json=program_data)

    print("\n=== 建立公版課程模板 ===")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"ID: {data['id']}")
        print(f"Name: {data['name']}")
        print(f"Is Template: {data['is_template']}")
        print(f"Classroom ID: {data['classroom_id']}")
        print(f"Source Metadata: {data['source_metadata']}")
        return data["id"]
    else:
        print(f"Error: {response.text}")
        return None


def test_get_templates(token):
    """測試取得公版課程列表"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/programs/templates", headers=headers)

    print("\n=== 取得公版課程列表 ===")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        templates = response.json()
        print(f"找到 {len(templates)} 個公版課程")
        for template in templates[:3]:  # 只顯示前3個
            print(f"- {template['name']} (ID: {template['id']}, Template: {template['is_template']})")
    else:
        print(f"Error: {response.text}")


def test_copy_from_template(token, template_id):
    """測試從公版複製到班級"""
    headers = {"Authorization": f"Bearer {token}"}

    # 先取得班級列表
    classrooms_response = requests.get(f"{BASE_URL}/api/teacher/classrooms", headers=headers)

    if classrooms_response.status_code != 200:
        print("無法取得班級列表")
        return

    classrooms = classrooms_response.json()
    if not classrooms:
        print("沒有可用的班級")
        return

    classroom_id = classrooms[0]["id"]

    copy_data = {
        "template_id": template_id,
        "classroom_id": classroom_id,
        "name": "班級版英語會話課程",
    }

    response = requests.post(f"{BASE_URL}/api/programs/copy-from-template", headers=headers, json=copy_data)

    print("\n=== 從公版複製到班級 ===")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"新課程 ID: {data['id']}")
        print(f"Name: {data['name']}")
        print(f"Is Template: {data['is_template']}")
        print(f"Classroom ID: {data['classroom_id']}")
        print(f"Source Type: {data['source_type']}")
        print(f"Source Metadata: {data['source_metadata']}")
    else:
        print(f"Error: {response.text}")


def test_get_copyable(token):
    """測試取得可複製的課程列表"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/programs/copyable", headers=headers)

    print("\n=== 取得可複製的課程列表 ===")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        programs = response.json()
        print(f"找到 {len(programs)} 個可複製課程")
        for program in programs[:5]:  # 只顯示前5個
            print(f"- {program['name']} (Template: {program['is_template']}, Classroom: {program['classroom_id']})")
    else:
        print(f"Error: {response.text}")


def main():
    # 1. 登入
    print("=== 教師登入 ===")
    token = login_teacher()

    if not token:
        print("無法登入，結束測試")
        return

    print(f"Token 取得成功")

    # 2. 建立公版課程模板
    template_id = test_create_template(token)

    # 3. 取得公版課程列表
    test_get_templates(token)

    # 4. 如果成功建立模板，測試複製功能
    if template_id:
        test_copy_from_template(token, template_id)

    # 5. 取得可複製的課程列表
    test_get_copyable(token)

    print("\n=== 測試完成 ===")


if __name__ == "__main__":
    main()
