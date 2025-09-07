#!/usr/bin/env python3
"""
測試學生登入流程
"""
import requests
import json  # noqa: F401

BASE_URL = "http://localhost:8000"


def test_student_login_flow():
    print("🚀 測試學生登入流程")
    print("=" * 50)

    # Step 1: 驗證教師
    print("\n1. 驗證教師 Email")
    teacher_email = "demo@duotopia.com"
    response = requests.post(f"{BASE_URL}/api/public/validate-teacher", json={"email": teacher_email})
    print("   請求: POST /api/public/validate-teacher")
    print(f"   資料: {{email: '{teacher_email}'}}")
    print(f"   回應: {response.status_code} - {response.json()}")

    if response.status_code == 200 and response.json()["valid"]:
        print("   ✅ 教師驗證成功")
    else:
        print("   ❌ 教師驗證失敗")
        return

    # Step 2: 取得教師的班級
    print("\n2. 取得教師的班級列表")
    response = requests.get(f"{BASE_URL}/api/public/teacher-classrooms", params={"email": teacher_email})
    print(f"   請求: GET /api/public/teacher-classrooms?email={teacher_email}")
    print(f"   回應: {response.status_code}")

    if response.status_code == 200:
        classrooms = response.json()
        print(f"   找到 {len(classrooms)} 個班級:")
        for classroom in classrooms:
            print(f"     - {classroom['name']} (ID: {classroom['id']}, 學生數: {classroom['studentCount']})")

        if classrooms:
            print("   ✅ 取得班級成功")
            selected_classroom = classrooms[0]
        else:
            print("   ⚠️ 沒有找到班級")
            return
    else:
        print(f"   ❌ 取得班級失敗: {response.text}")
        return

    # Step 3: 取得班級的學生
    print(f"\n3. 取得班級 '{selected_classroom['name']}' 的學生列表")
    response = requests.get(f"{BASE_URL}/api/public/classroom-students/{selected_classroom['id']}")
    print(f"   請求: GET /api/public/classroom-students/{selected_classroom['id']}")
    print(f"   回應: {response.status_code}")

    if response.status_code == 200:
        students = response.json()
        print(f"   找到 {len(students)} 位學生:")
        for student in students:
            print(f"     - {student['name']} (Email: {student['email']})")

        if students:
            print("   ✅ 取得學生成功")
            selected_student = students[0]
        else:
            print("   ⚠️ 班級沒有學生")
            return
    else:
        print(f"   ❌ 取得學生失敗: {response.text}")
        return

    # Step 4: 學生登入
    print("\n4. 學生登入測試")
    print(f"   選擇學生: {selected_student['name']}")

    # 測試正確密碼 (預設生日 20120101)
    login_data = {
        "email": selected_student["email"],
        "password": "20120101",
    }  # 預設密碼
    response = requests.post(f"{BASE_URL}/api/auth/student/login", json=login_data)
    print("   請求: POST /api/auth/student/login")
    print(f"   資料: {{email: '{login_data['email']}', password: '20120101'}}")
    print(f"   回應: {response.status_code}")

    if response.status_code == 200:
        auth_data = response.json()
        print("   ✅ 學生登入成功!")
        print(f"   Token: {auth_data['access_token'][:50]}...")
        print(f"   用戶資訊: {auth_data['user']}")
    else:
        print(f"   ❌ 學生登入失敗: {response.text}")

    print("\n" + "=" * 50)
    print("測試完成！")


if __name__ == "__main__":
    test_student_login_flow()
