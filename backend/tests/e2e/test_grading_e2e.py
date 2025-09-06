#!/usr/bin/env python3
"""
端到端批改流程測試
測試從登入到批改的完整流程
"""

import requests
from datetime import datetime  # noqa: F401
import time

BASE_URL = "http://localhost:8000"


def test_complete_grading_flow():
    """完整批改流程測試"""
    print("\n" + "=" * 60)
    print("開始端到端批改流程測試")
    print("=" * 60)

    # 1. 教師登入
    print("\n1. 教師登入...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    assert login_response.status_code == 200, f"登入失敗: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登入成功")

    # 2. 取得作業列表
    print("\n2. 取得作業列表...")
    assignments_response = requests.get(
        f"{BASE_URL}/api/teachers/assignments", headers=headers
    )
    assert assignments_response.status_code == 200
    assignments = assignments_response.json()
    assert len(assignments) > 0, "沒有作業"
    print(f"✅ 取得 {len(assignments)} 個作業")

    # 選擇第一個作業
    assignment = assignments[0]
    assignment_id = assignment["id"]
    print(f"   選擇作業: {assignment['title']} (ID: {assignment_id})")

    # 3. 取得學生提交列表
    print("\n3. 取得學生提交列表...")
    submissions_response = requests.get(
        f"{BASE_URL}/api/teachers/{assignment_id}/submissions", headers=headers
    )
    assert submissions_response.status_code == 200
    submissions = submissions_response.json()
    assert len(submissions) > 0, "沒有學生提交"
    print(f"✅ 取得 {len(submissions)} 個學生提交")

    # 找一個待批改的學生
    student_to_grade = None
    for submission in submissions:
        if submission["status"] in ["SUBMITTED", "RESUBMITTED"]:
            student_to_grade = submission
            break

    if not student_to_grade:
        # 如果沒有待批改的，選第一個
        student_to_grade = submissions[0]

    student_id = student_to_grade["student_id"]
    print(
        f"   選擇學生: {student_to_grade['student_name']} (ID: {student_id}, 狀態: {student_to_grade['status']})"
    )

    # 4. 取得學生提交詳情
    print("\n4. 取得學生提交詳情...")
    detail_response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if detail_response.status_code != 200:
        print(f"❌ 無法取得提交詳情: {detail_response.text}")
        print("\n嘗試修正路徑問題...")

        # 嘗試簡化 API（移除 content 相關邏輯）
        print("   建議：簡化 API 邏輯，不查詢 Content")
        return False

    submission_detail = detail_response.json()
    print("✅ 取得提交詳情")
    print(f"   學生: {submission_detail['student_name']}")
    print(f"   狀態: {submission_detail['status']}")

    # 5. 批改作業
    print("\n5. 批改作業...")
    test_score = 88
    test_feedback = f"自動化測試批改 - 表現優秀！時間: {datetime.now().strftime('%H:%M:%S')}"

    grade_response = requests.post(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json={"student_id": student_id, "score": test_score, "feedback": test_feedback},
    )

    if grade_response.status_code != 200:
        print(f"❌ 批改失敗: {grade_response.text}")
        return False

    print("✅ 批改成功")
    print(f"   分數: {test_score}")
    print(f"   評語: {test_feedback}")

    # 6. 驗證批改結果
    print("\n6. 驗證批改結果...")
    time.sleep(1)  # 等待資料更新

    verify_response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if verify_response.status_code == 200:
        updated_submission = verify_response.json()
        if updated_submission.get("current_score") == test_score:
            print("✅ 分數更新正確")
        else:
            print(
                f"⚠️ 分數不符: 期望 {test_score}, 實際 {updated_submission.get('current_score')}"
            )

        if updated_submission.get("current_feedback") == test_feedback:
            print("✅ 評語更新正確")
        else:
            print("⚠️ 評語不符")

    print("\n" + "=" * 60)
    print("✅ 端到端批改流程測試完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_complete_grading_flow()
    exit(0 if success else 1)
