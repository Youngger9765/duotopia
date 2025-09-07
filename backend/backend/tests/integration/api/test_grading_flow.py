#!/usr/bin/env python3
"""
批改流程完整測試
測試整個批改流程的 API 端點
"""

import requests
import json  # noqa: F401
from datetime import datetime  # noqa: F401

BASE_URL = "http://localhost:8000"


def login_teacher():
    """教師登入"""
    print("\n1. 教師登入...")
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 登入成功: {data['user']['name']}")
        return data["access_token"]
    else:
        print(f"❌ 登入失敗: {response.text}")
        return None


def get_teacher_assignments(token):
    """取得教師的作業列表"""
    print("\n2. 取得教師作業列表...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/teachers/assignments", headers=headers)

    if response.status_code == 200:
        assignments = response.json()
        print(f"✅ 取得 {len(assignments)} 個作業")

        # 顯示前3個作業
        for i, assignment in enumerate(assignments[:3]):
            print(f"   作業 {i+1}: {assignment['title']} (ID: {assignment['id']})")
            print(f"      - 學生數: {assignment['student_count']}")
            print(f"      - 完成率: {assignment['completion_rate']}%")

        return assignments
    else:
        print(f"❌ 取得作業失敗: {response.text}")
        return []


def get_assignment_submissions(token, assignment_id):
    """取得作業的學生提交列表"""
    print(f"\n3. 取得作業 {assignment_id} 的學生提交...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(f"{BASE_URL}/api/teachers/{assignment_id}/submissions", headers=headers)

    if response.status_code == 200:
        submissions = response.json()
        print(f"✅ 取得 {len(submissions)} 個學生提交")

        # 找出待批改的學生
        submitted_students = [s for s in submissions if s["status"] == "SUBMITTED"]
        if submitted_students:
            print(f"   找到 {len(submitted_students)} 個待批改的學生")
            for student in submitted_students[:3]:
                print(f"   - {student['student_name']} (ID: {student['student_id']})")

        return submissions
    else:
        print(f"❌ 取得提交列表失敗: {response.text}")
        return []


def get_student_submission_detail(token, assignment_id, student_id):
    """取得單個學生的提交詳情"""
    print(f"\n4. 取得學生 {student_id} 在作業 {assignment_id} 的提交詳情...")
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if response.status_code == 200:
        submission = response.json()
        print("✅ 取得學生提交詳情")
        print(f"   學生: {submission['student_name']} ({submission['student_email']})")
        print(f"   狀態: {submission['status']}")
        print(f"   內容類型: {submission['content_type']}")
        print(f"   提交數量: {len(submission['submissions'])}")

        if submission["current_score"]:
            print(f"   目前分數: {submission['current_score']}")
        if submission["current_feedback"]:
            print(f"   目前評語: {submission['current_feedback']}")

        return submission
    else:
        print(f"❌ 取得提交詳情失敗: {response.text}")
        return None


def grade_student_submission(token, assignment_id, student_id, score, feedback):
    """批改學生作業"""
    print("\n5. 批改學生作業...")
    headers = {"Authorization": f"Bearer {token}"}

    grade_data = {"student_id": student_id, "score": score, "feedback": feedback}

    response = requests.post(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json=grade_data,
    )

    if response.status_code == 200:
        result = response.json()
        print("✅ 批改成功")
        print(f"   分數: {score}")
        print(f"   評語: {feedback}")
        print(f"   狀態: {result.get('status', 'GRADED')}")
        return result
    else:
        print(f"❌ 批改失敗: {response.text}")
        return None


def main():
    """主測試流程"""
    print("=" * 60)
    print("批改流程完整測試")
    print("=" * 60)

    # 1. 教師登入
    token = login_teacher()
    if not token:
        print("❌ 測試失敗：無法登入")
        return

    # 2. 取得作業列表
    assignments = get_teacher_assignments(token)
    if not assignments:
        print("❌ 測試失敗：無法取得作業")
        return

    # 3. 選擇第一個有學生的作業
    target_assignment = None
    for assignment in assignments:
        if assignment["student_count"] > 0:
            target_assignment = assignment
            break

    if not target_assignment:
        print("❌ 測試失敗：沒有找到有學生的作業")
        return

    print(f"\n選擇作業: {target_assignment['title']} (ID: {target_assignment['id']})")

    # 4. 取得學生提交列表
    submissions = get_assignment_submissions(token, target_assignment["id"])
    if not submissions:
        print("❌ 測試失敗：無法取得學生提交")
        return

    # 5. 找一個待批改的學生
    target_student = None
    for submission in submissions:
        if submission["status"] in ["SUBMITTED", "RESUBMITTED"]:
            target_student = submission
            break

    if not target_student:
        # 如果沒有待批改的，選第一個學生
        target_student = submissions[0]
        print(f"⚠️ 沒有待批改的學生，選擇 {target_student['student_name']} 進行測試")
    else:
        print(f"選擇待批改學生: {target_student['student_name']}")

    # 6. 取得學生提交詳情
    submission_detail = get_student_submission_detail(token, target_assignment["id"], target_student["student_id"])

    if not submission_detail:
        print("❌ 測試失敗：無法取得學生提交詳情")
        return

    # 7. 批改作業
    test_score = 85
    test_feedback = f"測試批改 - 表現良好！時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    grade_result = grade_student_submission(
        token,
        target_assignment["id"],
        target_student["student_id"],
        test_score,
        test_feedback,
    )

    if grade_result:
        print("\n" + "=" * 60)
        print("✅ 批改流程測試完成！")
        print("=" * 60)

        # 8. 驗證批改結果
        print("\n6. 驗證批改結果...")
        updated_submission = get_student_submission_detail(token, target_assignment["id"], target_student["student_id"])

        if updated_submission:
            if updated_submission["current_score"] == test_score:
                print("✅ 分數更新正確")
            else:
                print(f"⚠️ 分數不符: 期望 {test_score}, 實際 {updated_submission['current_score']}")

            if updated_submission["current_feedback"] == test_feedback:
                print("✅ 評語更新正確")
            else:
                print("⚠️ 評語不符")
    else:
        print("\n❌ 批改流程測試失敗")


if __name__ == "__main__":
    main()
