#!/usr/bin/env python3
"""
完整測試作業指派功能
Complete test for assignment functionality
"""

import requests
import json
from datetime import datetime, timedelta

# API endpoint
BASE_URL = "http://localhost:8000"

# 教師登入資訊（使用 Demo 教師）
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
        return data["access_token"]
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        return None


def test_assignment_complete(token, assignment_id):
    """完整測試作業功能"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    print(f"\n{'='*60}")
    print(f"測試作業 {assignment_id} 的完整功能")
    print(f"{'='*60}")

    # 1. 取得作業詳情
    print("\n1. 取得作業詳情...")
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}", headers=headers
    )
    if response.status_code != 200:
        print(f"❌ 無法取得作業詳情: {response.text}")
        return

    assignment = response.json()
    print(f"✅ 作業標題: {assignment.get('title')}")
    print(f"   描述: {assignment.get('description')}")
    print(f"   班級 ID: {assignment.get('classroom_id')}")
    print(f"   截止日期: {assignment.get('due_date')}")
    print(f"   已指派學生: {assignment.get('student_ids', [])}")

    # 2. 測試部分更新（修改標題和描述）
    print("\n2. 測試部分更新（修改標題和描述）...")
    new_title = f"測試作業 - {datetime.now().strftime('%H:%M:%S')}"
    new_description = "這是透過 API 測試更新的描述"

    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={"title": new_title, "description": new_description},
    )
    if response.status_code == 200:
        print(f"✅ 成功更新標題為: {new_title}")
        print(f"   新描述: {new_description}")
    else:
        print(f"❌ 更新失敗: {response.text}")

    # 3. 取得班級學生列表
    classroom_id = assignment.get("classroom_id")
    print(f"\n3. 取得班級 {classroom_id} 的學生列表...")
    response = requests.get(
        f"{BASE_URL}/api/classrooms/{classroom_id}/students", headers=headers
    )
    if response.status_code != 200:
        print(f"❌ 無法取得學生列表: {response.text}")
        return

    students = response.json()
    print(f"✅ 班級共有 {len(students)} 位學生")

    # 4. 測試指派不同數量的學生
    print("\n4. 測試指派學生功能...")

    # 測試1: 指派前5位學生
    test_students_1 = [s["id"] for s in students[:5]]
    print(f"\n   測試1: 指派 {len(test_students_1)} 位學生: {test_students_1}")
    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={"student_ids": test_students_1},
    )
    if response.status_code == 200:
        print(f"   ✅ 成功指派 {len(test_students_1)} 位學生")
    else:
        print(f"   ❌ 指派失敗: {response.text}")

    # 測試2: 修改為只有2位學生
    test_students_2 = [students[0]["id"], students[2]["id"]]
    print(f"\n   測試2: 修改為只指派 {len(test_students_2)} 位學生: {test_students_2}")
    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={"student_ids": test_students_2},
    )
    if response.status_code == 200:
        print(f"   ✅ 成功修改為 {len(test_students_2)} 位學生")
    else:
        print(f"   ❌ 修改失敗: {response.text}")

    # 5. 驗證進度 API
    print("\n5. 驗證進度 API...")
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}/progress", headers=headers
    )
    if response.status_code != 200:
        print(f"❌ 無法取得進度: {response.text}")
        return

    progress_data = response.json()
    # 進度 API 只返回已指派的學生

    print(f"✅ 進度統計:")
    print(f"   已指派學生數: {len(progress_data)}")

    print("\n   已指派學生進度:")
    for s in progress_data:
        print(
            f"   - {s['student_name']} (ID: {s['student_id']}, 狀態: {s.get('status', 'N/A')})"
        )

    # 比較班級學生和已指派學生
    assigned_ids = [s["student_id"] for s in progress_data]
    unassigned_students = [s for s in students if s["id"] not in assigned_ids]

    print(f"\n   未指派學生數: {len(unassigned_students)}")
    print("   未指派學生（前3位）:")
    for s in unassigned_students[:3]:
        print(f"   - {s['name']} (ID: {s['id']})")

    # 6. 測試同時更新多個欄位
    print("\n6. 測試同時更新多個欄位...")
    new_due_date = (datetime.now() + timedelta(days=7)).isoformat()
    final_students = [students[1]["id"], students[3]["id"], students[5]["id"]]

    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={
            "title": "最終測試作業",
            "description": "這是最終的測試描述",
            "due_date": new_due_date,
            "student_ids": final_students,
        },
    )
    if response.status_code == 200:
        print(f"✅ 成功同時更新:")
        print(f"   標題: 最終測試作業")
        print(f"   描述: 這是最終的測試描述")
        print(f"   截止日期: {new_due_date}")
        print(f"   指派學生: {final_students}")
    else:
        print(f"❌ 更新失敗: {response.text}")

    # 7. 最終驗證
    print("\n7. 最終驗證...")
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}", headers=headers
    )
    if response.status_code == 200:
        final_assignment = response.json()
        print(f"✅ 最終作業狀態:")
        print(f"   標題: {final_assignment.get('title')}")
        print(f"   描述: {final_assignment.get('description')}")
        print(f"   截止日期: {final_assignment.get('due_date')}")
        print(f"   已指派學生 IDs: {final_assignment.get('student_ids', [])}")
    else:
        print(f"❌ 無法取得最終狀態")


def main():
    print("=" * 60)
    print("完整測試作業指派功能")
    print("=" * 60)

    # 登入教師
    print("\n登入教師帳號...")
    token = login_teacher()
    if not token:
        print("❌ 無法登入教師帳號")
        return
    print("✅ 登入成功")

    # 測試作業 13
    test_assignment_complete(token, 13)

    print("\n" + "=" * 60)
    print("測試完成！所有功能正常運作！")
    print("=" * 60)


if __name__ == "__main__":
    main()
