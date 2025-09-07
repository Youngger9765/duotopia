#!/usr/bin/env python3
"""
測試前端批改頁面功能
確認前端可以正確顯示和操作批改功能
"""

import requests
import json  # noqa: F401
import time

BASE_URL = "http://localhost:8000"


def test_frontend_grading():
    """測試前端批改頁面功能"""
    print("\n" + "=" * 60)
    print("測試前端批改頁面功能")
    print("=" * 60)

    # 1. 教師登入取得 token
    print("\n1. 教師登入...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    assert login_response.status_code == 200, f"登入失敗: {login_response.text}"
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登入成功")

    # 2. 測試特定的批改頁面 URL (assignment 11, student 11)
    print("\n2. 測試批改頁面 API (assignment=11, student=11)...")

    # 取得學生提交詳情
    submission_response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/11/submissions/11",
        headers=headers,
    )

    if submission_response.status_code != 200:
        print(f"❌ 無法取得提交詳情: {submission_response.text}")
        return False

    submission = submission_response.json()
    print("✅ 成功取得提交詳情")
    print(f"   學生: {submission['student_name']}")
    print(f"   狀態: {submission['status']}")
    print(f"   目前分數: {submission.get('current_score', '未批改')}")
    print(f"   目前評語: {submission.get('current_feedback', '無')}")

    # 3. 測試批改功能
    print("\n3. 測試批改功能...")

    test_score = 95
    test_feedback = f"前端測試批改 - 時間: {time.strftime('%H:%M:%S')}"

    grade_response = requests.post(
        f"{BASE_URL}/api/teachers/teachers/assignments/11/grade",
        headers=headers,
        json={"student_id": 11, "score": test_score, "feedback": test_feedback},
    )

    if grade_response.status_code != 200:
        print(f"❌ 批改失敗: {grade_response.text}")
        return False

    print("✅ 批改成功")
    print(f"   分數: {test_score}")
    print(f"   評語: {test_feedback}")

    # 4. 驗證批改結果
    print("\n4. 驗證批改結果...")
    time.sleep(1)

    verify_response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/11/submissions/11",
        headers=headers,
    )

    if verify_response.status_code == 200:
        updated = verify_response.json()
        assert updated.get("current_score") == test_score, f"分數不符: {updated.get('current_score')} != {test_score}"
        assert updated.get("current_feedback") == test_feedback, "評語不符"
        print("✅ 批改結果驗證成功")
        print(f"   更新後分數: {updated['current_score']}")
        print(f"   更新後評語: {updated['current_feedback']}")
    else:
        print(f"❌ 無法驗證: {verify_response.text}")
        return False

    # 5. 測試前端頁面是否能正確載入
    print("\n5. 檢查前端頁面...")
    print("   前端 URL: http://localhost:5173/teacher/classroom/1/assignment/11/grade/11")
    print("   ⚠️ 請手動在瀏覽器檢查頁面是否正確顯示")
    print("   應該看到:")
    print("   - 學生姓名: 蔡雅芳")
    print(f"   - 目前分數: {test_score}")
    print(f"   - 目前評語: {test_feedback}")

    print("\n" + "=" * 60)
    print("✅ 前端批改頁面功能測試完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_frontend_grading()
    exit(0 if success else 1)
