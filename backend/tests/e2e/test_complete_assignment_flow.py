#!/usr/bin/env python3
"""
完整測試作業系統流程
"""
import requests
from datetime import datetime, timedelta  # noqa: F401

BASE_URL = "http://localhost:8000/api"


def test_complete_flow():
    print("=" * 60)
    print("🚀 開始測試完整作業系統流程")
    print("=" * 60)

    # 1. 教師登入
    print("\n1️⃣ 教師登入...")
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.text}")
        return

    teacher_token = response.json()["access_token"]
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
    print("✅ 教師登入成功")

    # 2. 查詢教室列表
    print("\n2️⃣ 查詢教室列表...")
    response = requests.get(f"{BASE_URL}/teachers/classrooms", headers=teacher_headers)

    if response.status_code != 200:
        print(f"❌ 查詢教室失敗: {response.text}")
        return

    classrooms = response.json()
    if not classrooms:
        print("⚠️ 沒有找到教室")
        return

    classroom = classrooms[0]
    classroom_id = classroom["id"]
    print(f"✅ 找到教室: {classroom['name']} (ID: {classroom_id})")

    # 3. 查詢學生列表
    print("\n3️⃣ 查詢學生列表...")
    response = requests.get(
        f"{BASE_URL}/classrooms/{classroom_id}/students", headers=teacher_headers
    )

    if response.status_code != 200:
        print(f"❌ 查詢學生失敗: {response.text}")
        return

    students = response.json()
    print(f"✅ 找到 {len(students)} 位學生")

    # 4. 查詢課程內容
    print("\n4️⃣ 查詢課程內容...")
    response = requests.get(
        f"{BASE_URL}/contents?classroom_id={classroom_id}", headers=teacher_headers
    )

    if response.status_code != 200:
        print(f"❌ 查詢課程內容失敗: {response.text}")
        return

    contents = response.json()
    if not contents:
        print("⚠️ 沒有找到課程內容")
        return

    content = contents[0]
    content_id = content["id"]
    print(f"✅ 找到課程內容: {content['title']} (ID: {content_id})")

    # 5. 創建作業
    print("\n5️⃣ 創建作業...")
    assignment_data = {
        "content_id": content_id,
        "classroom_id": classroom_id,
        "title": f"測試作業 - {datetime.now().strftime('%Y%m%d %H:%M')}",
        "instructions": "這是一個測試作業，請認真完成",
        "student_ids": [],  # 空陣列表示全班
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
    }

    response = requests.post(
        f"{BASE_URL}/assignments/create", json=assignment_data, headers=teacher_headers
    )

    if response.status_code != 200:
        print(f"❌ 創建作業失敗: {response.text}")
        return

    result = response.json()
    print(f"✅ 成功創建 {result['count']} 份作業")

    # 6. 查詢教師的作業列表
    print("\n6️⃣ 查詢教師的作業列表...")
    response = requests.get(
        f"{BASE_URL}/assignments/teacher?classroom_id={classroom_id}",
        headers=teacher_headers,
    )

    if response.status_code != 200:
        print(f"❌ 查詢作業列表失敗: {response.text}")
        return

    assignments = response.json()
    print(f"✅ 找到 {len(assignments)} 份作業")

    if assignments:
        assignment = assignments[0]
        print(f"   • 作業標題: {assignment['title']}")
        print(f"   • 狀態: {assignment.get('status', 'N/A')}")
        print(f"   • 學生: {assignment.get('student', {}).get('name', 'Unknown')}")

    # 7. 學生登入
    print("\n7️⃣ 學生登入...")
    if students:
        student = students[0]
        response = requests.post(
            f"{BASE_URL}/auth/student/login",
            json={
                "email": student["email"],
                "password": student["birthdate"].replace("-", ""),
            },
        )

        if response.status_code != 200:
            print(f"❌ 學生登入失敗: {response.text}")
            return

        student_token = response.json()["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}
        print(f"✅ 學生 {student['name']} 登入成功")

        # 8. 查詢學生的作業列表
        print("\n8️⃣ 查詢學生的作業列表...")
        response = requests.get(
            f"{BASE_URL}/assignments/student", headers=student_headers
        )

        if response.status_code != 200:
            print(f"❌ 查詢學生作業失敗: {response.text}")
            return

        student_assignments = response.json()
        print(f"✅ 學生有 {len(student_assignments)} 份作業")

        if student_assignments:
            sa = student_assignments[0]
            print(f"   • 作業標題: {sa['title']}")
            print(f"   • 狀態: {sa['status']}")
            print(f"   • 截止日期: {sa.get('due_date', 'None')}")

    print("\n" + "=" * 60)
    print("🎉 所有測試完成！作業系統運作正常")
    print("=" * 60)


if __name__ == "__main__":
    test_complete_flow()
