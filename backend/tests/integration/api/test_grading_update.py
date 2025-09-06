#!/usr/bin/env python3
"""
測試批改更新功能
確認可以多次批改並更新分數
"""

import requests
import json  # noqa: F401
from datetime import datetime  # noqa: F401
import time

BASE_URL = "http://localhost:8000"


def test_grading_update():
    """測試批改更新功能"""
    print("\n" + "=" * 60)
    print("測試批改更新功能")
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

    # 使用固定的作業和學生ID
    assignment_id = 1
    student_id = 3

    # 2. 第一次批改
    print("\n2. 第一次批改...")
    first_score = 75
    first_feedback = f"第一次批改 - 時間: {datetime.now().strftime('%H:%M:%S')}"

    grade_response = requests.post(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json={
            "student_id": student_id,
            "score": first_score,
            "feedback": first_feedback,
        },
    )

    if grade_response.status_code != 200:
        print(f"❌ 第一次批改失敗: {grade_response.text}")
        return False

    print(f"✅ 第一次批改成功: 分數={first_score}")

    # 3. 驗證第一次批改
    print("\n3. 驗證第一次批改...")
    time.sleep(1)

    verify_response = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if verify_response.status_code == 200:
        data = verify_response.json()
        assert (
            data.get("current_score") == first_score
        ), f"分數不符: {data.get('current_score')} != {first_score}"
        assert data.get("current_feedback") == first_feedback, "評語不符"
        print("✅ 第一次批改驗證成功")
    else:
        print(f"⚠️ 無法驗證: {verify_response.text}")

    # 4. 第二次批改（更新）
    print("\n4. 第二次批改（更新）...")
    second_score = 92
    second_feedback = f"第二次批改 - 進步很多！時間: {datetime.now().strftime('%H:%M:%S')}"

    update_response = requests.post(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/grade",
        headers=headers,
        json={
            "student_id": student_id,
            "score": second_score,
            "feedback": second_feedback,
        },
    )

    if update_response.status_code != 200:
        print(f"❌ 第二次批改失敗: {update_response.text}")
        return False

    print(f"✅ 第二次批改成功: 分數={second_score}")

    # 5. 驗證第二次批改
    print("\n5. 驗證第二次批改...")
    time.sleep(1)

    final_verify = requests.get(
        f"{BASE_URL}/api/teachers/teachers/assignments/{assignment_id}/submissions/{student_id}",
        headers=headers,
    )

    if final_verify.status_code == 200:
        data = final_verify.json()
        assert (
            data.get("current_score") == second_score
        ), f"分數未更新: {data.get('current_score')} != {second_score}"
        assert data.get("current_feedback") == second_feedback, "評語未更新"
        print("✅ 第二次批改驗證成功")
        print(f"   最終分數: {second_score}")
        print(f"   最終評語: {second_feedback}")
    else:
        print(f"⚠️ 無法驗證: {final_verify.text}")
        return False

    print("\n" + "=" * 60)
    print("✅ 批改更新功能測試完成！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_grading_update()
    exit(0 if success else 1)
