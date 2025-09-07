#!/usr/bin/env python3
"""測試新的批改頁面 API"""

import requests

# API 基礎 URL
BASE_URL = "http://localhost:8000"

# 教師登入憑證
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """登入教師帳號"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 教師登入成功: {data['user']['name']}")
        return data["access_token"]
    else:
        print(f"❌ 教師登入失敗: {response.status_code}")
        print(response.text)
        return None


def test_get_assignment_students(token, assignment_id=2):
    """測試取得作業的學生列表"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/teachers/assignments/{assignment_id}/students", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print("\n✅ 成功取得學生列表")
        print(f"學生總數: {len(data.get('students', []))}")

        for student in data.get("students", []):
            status_icon = "✅" if student["status"] == "GRADED" else "📝"
            print(f"  {status_icon} {student['student_name']} (ID: {student['student_id']}) - {student['status']}")

        return data
    else:
        print(f"❌ 取得學生列表失敗: {response.status_code}")
        print(response.text)
        return None


def test_grading_page_navigation(token):
    """測試批改頁面導航功能"""
    # 先取得學生列表
    students_data = test_get_assignment_students(token, assignment_id=2)

    if not students_data or not students_data.get("students"):
        print("\n❌ 無法測試導航，沒有學生資料")
        return

    students = students_data["students"]
    print("\n測試導航功能：")
    print(f"可以在 {len(students)} 個學生之間切換")

    # 測試訪問第一個學生
    first_student = students[0]
    print(f"\n訪問 URL: /teacher/grading/2/{first_student['student_id']}")
    print(f"學生: {first_student['student_name']}")

    # 測試訪問最後一個學生
    if len(students) > 1:
        last_student = students[-1]
        print(f"\n訪問 URL: /teacher/grading/2/{last_student['student_id']}")
        print(f"學生: {last_student['student_name']}")


def main():
    print("=" * 50)
    print("測試批改頁面 API")
    print("=" * 50)

    # 1. 登入教師
    token = login_teacher()
    if not token:
        print("\n⚠️ 無法登入，測試中止")
        return

    # 2. 測試取得學生列表
    print("\n" + "=" * 50)
    print("測試取得學生列表 API")
    print("=" * 50)
    test_get_assignment_students(token)

    # 3. 測試導航功能
    print("\n" + "=" * 50)
    print("測試批改頁面導航")
    print("=" * 50)
    test_grading_page_navigation(token)

    print("\n" + "=" * 50)
    print("✅ 新的批改頁面 URL 格式:")
    print("/teacher/grading/{assignmentId}/{studentId}")
    print("例如: /teacher/grading/2/1")
    print("=" * 50)


if __name__ == "__main__":
    main()
