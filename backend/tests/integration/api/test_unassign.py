#!/usr/bin/env python3
"""
測試取消指派功能
Test unassign functionality with different student progress states
"""

import requests
import json
from datetime import datetime, timedelta  # noqa: F401

BASE_URL = "http://localhost:8000"
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"


def login_teacher():
    """登入教師帳號"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": TEACHER_EMAIL, "password": TEACHER_PASSWORD},
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None


def create_test_assignment(token):
    """創建測試作業"""
    headers = {"Authorization": f"Bearer {token}"}

    # 取得班級
    response = requests.get(f"{BASE_URL}/api/teachers/classrooms", headers=headers)
    if response.status_code != 200:
        print("Failed to get classrooms")
        return None

    classrooms = response.json()
    if not classrooms:
        print("No classrooms found")
        return None

    classroom_id = classrooms[0]["id"]

    # 創建作業
    assignment_data = {
        "title": f"取消指派測試 - {datetime.now().strftime('%H:%M:%S')}",
        "description": "測試取消指派功能",
        "classroom_id": classroom_id,
        "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "content_ids": [],
        "student_ids": [],  # 先不指派
    }

    response = requests.post(
        f"{BASE_URL}/api/assignments/create", headers=headers, json=assignment_data
    )

    if response.status_code in [200, 201]:
        return response.json()["assignment_id"], classroom_id
    else:
        print(f"Failed to create assignment: {response.text}")
        return None


def simulate_student_progress(assignment_id, student_id, status):
    """模擬學生作業進度（直接更新資料庫）"""
    import sys

    sys.path.append("/Users/young/project/duotopia/backend")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import StudentAssignment, AssignmentStatus
    import os
    from dotenv import load_dotenv
    from datetime import datetime, timezone

    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # 更新學生作業狀態
    sa = (
        session.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if sa:
        if status == "IN_PROGRESS":
            sa.status = AssignmentStatus.IN_PROGRESS
            sa.started_at = datetime.now(timezone.utc)
        elif status == "SUBMITTED":
            sa.status = AssignmentStatus.SUBMITTED
            sa.submitted_at = datetime.now(timezone.utc)
        elif status == "GRADED":
            sa.status = AssignmentStatus.GRADED
            sa.completed_at = datetime.now(timezone.utc)

        session.commit()
        print(f"  ✅ 設定學生 {student_id} 狀態為 {status}")
    else:
        print("  ❌ 找不到學生作業記錄")

    session.close()


def test_unassign_scenarios(token, assignment_id, classroom_id):
    """測試各種取消指派場景"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "=" * 60)
    print("測試取消指派功能")
    print("=" * 60)

    # 1. 取得班級學生
    response = requests.get(
        f"{BASE_URL}/api/classrooms/{classroom_id}/students", headers=headers
    )
    students = response.json()

    if len(students) < 4:
        print("❌ 需要至少 4 位學生進行測試")
        return

    # 2. 指派 4 位學生
    student_ids = [s["id"] for s in students[:4]]
    print(f"\n1. 指派 4 位學生: {student_ids}")

    response = requests.patch(
        f"{BASE_URL}/api/assignments/{assignment_id}",
        headers=headers,
        json={"student_ids": student_ids},
    )

    if response.status_code != 200:
        print(f"❌ 指派失敗: {response.text}")
        return
    print("✅ 成功指派 4 位學生")

    # 3. 模擬不同的學生進度
    print("\n2. 模擬學生進度:")
    print(f"  學生 {student_ids[0]}: 保持 NOT_STARTED")
    simulate_student_progress(assignment_id, student_ids[1], "IN_PROGRESS")
    simulate_student_progress(assignment_id, student_ids[2], "SUBMITTED")
    simulate_student_progress(assignment_id, student_ids[3], "GRADED")

    # 4. 預覽取消指派
    print("\n3. 預覽取消指派影響:")
    student_ids_str = ",".join(map(str, student_ids))
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}/unassign-preview",
        headers=headers,
        params={"student_ids": student_ids_str},
    )

    if response.status_code == 200:
        preview = response.json()
        print(f"  可直接取消: {len(preview.get('can_unassign', []))} 位")
        for s in preview.get("can_unassign", []):
            print(f"    - {s['student_name']} (狀態: {s['status']})")

        print(f"  需要確認: {len(preview.get('need_confirmation', []))} 位")
        for s in preview.get("need_confirmation", []):
            print(f"    - {s['student_name']} (狀態: {s['status']})")

        print(f"  無法取消: {len(preview.get('cannot_unassign', []))} 位")
        for s in preview.get("cannot_unassign", []):
            print(f"    - {s['student_name']} (狀態: {s['status']})")
    else:
        print(f"❌ 預覽失敗: {response.text}")

    # 5. 嘗試取消指派（不強制）
    print("\n4. 嘗試取消指派（不強制）:")
    response = requests.post(
        f"{BASE_URL}/api/assignments/{assignment_id}/unassign",
        headers=headers,
        json={"student_ids": student_ids, "force": False},
    )

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ {result['message']}")
        print(f"  成功取消: {result.get('unassigned', [])}")
        if result.get("protected"):
            print("  受保護的學生:")
            for p in result["protected"]:
                print(f"    - {p['student_name']}: {p['reason']}")
    else:
        print(f"❌ 取消失敗: {response.text}")

    # 6. 強制取消指派
    print("\n5. 強制取消指派（force=True）:")
    response = requests.post(
        f"{BASE_URL}/api/assignments/{assignment_id}/unassign",
        headers=headers,
        json={"student_ids": [student_ids[1]], "force": True},  # IN_PROGRESS 的學生
    )

    if response.status_code == 200:
        result = response.json()
        print(f"  ✅ {result['message']}")
        print(f"  強制取消: {result.get('unassigned', [])}")
    else:
        print(f"❌ 強制取消失敗: {response.text}")

    # 7. 驗證最終狀態
    print("\n6. 驗證最終狀態:")
    response = requests.get(
        f"{BASE_URL}/api/assignments/{assignment_id}", headers=headers
    )

    if response.status_code == 200:
        assignment = response.json()
        final_students = assignment.get("student_ids", [])
        print(f"  最終指派學生: {final_students}")
        print(f"  剩餘學生數: {len(final_students)}")
    else:
        print("❌ 無法取得作業狀態")


def main():
    print("=" * 60)
    print("取消指派功能測試")
    print("=" * 60)

    # 登入
    print("\n登入教師...")
    token = login_teacher()
    if not token:
        print("❌ 登入失敗")
        return
    print("✅ 登入成功")

    # 創建測試作業
    print("\n創建測試作業...")
    result = create_test_assignment(token)
    if not result:
        print("❌ 創建作業失敗")
        return

    assignment_id, classroom_id = result
    print(f"✅ 創建作業成功 (ID: {assignment_id})")

    # 執行測試
    test_unassign_scenarios(token, assignment_id, classroom_id)

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
