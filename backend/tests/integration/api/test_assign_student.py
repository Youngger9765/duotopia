#!/usr/bin/env python3
"""
測試學生指派功能是否正確更新資料庫
Test assign student functionality and database updates
"""

import requests
import json
from datetime import datetime

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


def get_assignment_detail(token, assignment_id):
    """取得作業詳情"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}", headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get assignment: {response.status_code} - {response.text}")
        return None


def get_classroom_students(token, classroom_id):
    """取得班級學生列表"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/classrooms/{classroom_id}/students", headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get students: {response.status_code} - {response.text}")
        return None


def test_assign_student(token, assignment_id, student_ids):
    """測試指派學生功能"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 使用 PATCH 更新 student_ids
    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={"student_ids": student_ids},
    )

    print(f"\n=== 測試指派學生 ===")
    print(f"Assignment ID: {assignment_id}")
    print(f"Student IDs to assign: {student_ids}")
    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        print("✅ 成功更新學生指派")
        return True
    else:
        print(f"❌ 更新失敗: {response.text}")
        return False


def get_assignment_progress(token, assignment_id):
    """取得作業進度（檢查哪些學生被指派）"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}/progress", headers=headers
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get progress: {response.status_code} - {response.text}")
        return None


def main():
    print("=" * 50)
    print("測試學生指派功能")
    print("=" * 50)

    # 1. 登入教師
    print("\n1. 登入教師帳號...")
    token = login_teacher()
    if not token:
        print("❌ 無法登入教師帳號")
        return
    print("✅ 登入成功")

    # 2. 取得作業詳情（假設作業 ID 13）
    assignment_id = 13
    print(f"\n2. 取得作業 {assignment_id} 的詳情...")
    assignment = get_assignment_detail(token, assignment_id)
    if not assignment:
        print("❌ 無法取得作業詳情")
        return

    print(f"✅ 作業標題: {assignment.get('title', 'N/A')}")
    print(f"   班級 ID: {assignment.get('classroom_id', 'N/A')}")
    print(f"   目前指派學生: {assignment.get('student_ids', [])}")

    # 3. 取得班級學生列表
    classroom_id = assignment.get("classroom_id")
    print(f"\n3. 取得班級 {classroom_id} 的學生列表...")
    students = get_classroom_students(token, classroom_id)
    if not students:
        print("❌ 無法取得學生列表")
        return

    print(f"✅ 班級共有 {len(students)} 位學生")
    for student in students[:5]:  # 顯示前5位
        print(f"   - ID: {student['id']}, 姓名: {student['name']}")

    # 4. 測試指派學生
    # 根據當前狀態決定要指派的學生
    current_assigned = assignment.get("student_ids", [])

    if len(current_assigned) == 0:
        # 第一次指派：選擇前3位學生
        print("目前沒有指派任何學生，將指派前3位學生")
        if len(students) >= 3:
            new_student_ids = [students[0]["id"], students[1]["id"], students[2]["id"]]
        else:
            new_student_ids = [s["id"] for s in students]
    elif len(current_assigned) < 5:
        # 已有指派：增加更多學生
        print(f"目前已指派 {len(current_assigned)} 位學生，將增加更多學生")
        # 加入第4和第5位學生（如果有的話）
        new_student_ids = current_assigned.copy()
        for student in students:
            if student["id"] not in new_student_ids:
                new_student_ids.append(student["id"])
                if len(new_student_ids) >= 5:
                    break
    else:
        # 測試移除學生：只保留前2位
        print(f"目前已指派 {len(current_assigned)} 位學生，將減少到只有2位")
        new_student_ids = current_assigned[:2]

    print(f"\n4. 測試指派學生...")
    success = test_assign_student(token, assignment_id, new_student_ids)

    if success:
        # 5. 驗證更新結果
        print(f"\n5. 驗證更新結果...")

        # 重新取得作業詳情
        updated_assignment = get_assignment_detail(token, assignment_id)
        if updated_assignment:
            print(f"✅ 更新後的指派學生: {updated_assignment.get('student_ids', [])}")

            # 檢查進度
            progress = get_assignment_progress(token, assignment_id)
            if progress and "students" in progress:
                assigned_count = len(
                    [s for s in progress["students"] if s.get("is_assigned")]
                )
                print(f"✅ 已指派學生數: {assigned_count}/{len(progress['students'])}")

                # 顯示前幾位學生的狀態
                print("\n學生指派狀態:")
                for student in progress["students"][:8]:
                    status = "✅ 已指派" if student.get("is_assigned") else "⚪ 未指派"
                    assignment_status = student.get("status", "N/A")
                    print(
                        f"   {status} {student['name']} (ID: {student['id']}) - 狀態: {assignment_status}"
                    )

    print("\n" + "=" * 50)
    print("測試完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
