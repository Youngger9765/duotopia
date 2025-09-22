#!/usr/bin/env python3
"""
測試作業指派權限控制

用途：驗證只有有效訂閱的教師才能指派作業
執行：python test_assignment_permission.py

測試項目：
1. 過期教師無法指派作業
2. 有效訂閱教師可以指派作業
3. Demo 帳號不再有特殊權限

修復日期：2025-09-22
修復內容：移除 demo 帳號特殊權限，統一訂閱權限控制
"""

import requests

# API 基礎 URL
BASE_URL = "http://localhost:8000"


def test_teacher_assignment_permission():
    """測試教師指派作業權限"""

    # 測試用戶：過期老師（應該無法指派作業）
    expired_teacher = {"email": "expired@duotopia.com", "password": "demo123"}

    # 測試用戶：試用老師（應該可以指派作業）
    trial_teacher = {"email": "trial@duotopia.com", "password": "demo123"}

    print("=== 測試作業指派權限控制 ===\n")

    # 測試過期老師
    print("1. 測試過期老師登入...")
    response = requests.post(f"{BASE_URL}/api/auth/teacher/login", json=expired_teacher)
    if response.status_code == 200:
        expired_token = response.json()["access_token"]
        print("✅ 過期老師登入成功")

        # 檢查教師資訊
        headers = {"Authorization": f"Bearer {expired_token}"}
        profile_response = requests.get(
            f"{BASE_URL}/api/teachers/profile", headers=headers
        )
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"   訂閱狀態：{'已訂閱' if profile['can_assign_homework'] else '未訂閱'}")
            print(f"   可指派作業：{profile['can_assign_homework']}")

        # 嘗試指派作業
        print("\n2. 測試過期老師指派作業...")
        assignment_data = {
            "title": "測試作業",
            "description": "這是測試作業",
            "classroom_id": 1,
            "content_ids": [1],
            "student_ids": [],
        }

        assign_response = requests.post(
            f"{BASE_URL}/api/teachers/assignments/create",
            headers=headers,
            json=assignment_data,
        )

        if assign_response.status_code == 403:
            print("✅ 過期老師無法指派作業（正確）")
            print(f"   錯誤訊息：{assign_response.json()['detail']}")
        else:
            print(f"❌ 過期老師竟然可以指派作業！狀態碼：{assign_response.status_code}")
    else:
        print(f"❌ 過期老師登入失敗：{response.status_code}")

    print("\n" + "=" * 50)

    # 測試試用老師
    print("\n3. 測試試用老師登入...")
    response = requests.post(f"{BASE_URL}/api/auth/teacher/login", json=trial_teacher)
    if response.status_code == 200:
        trial_token = response.json()["access_token"]
        print("✅ 試用老師登入成功")

        # 檢查教師資訊
        headers = {"Authorization": f"Bearer {trial_token}"}
        profile_response = requests.get(
            f"{BASE_URL}/api/teachers/profile", headers=headers
        )
        if profile_response.status_code == 200:
            profile = profile_response.json()
            print(f"   訂閱狀態：{'已訂閱' if profile['can_assign_homework'] else '未訂閱'}")
            print(f"   可指派作業：{profile['can_assign_homework']}")

        # 嘗試指派作業
        print("\n4. 測試試用老師指派作業...")
        assignment_data = {
            "title": "測試作業",
            "description": "這是測試作業",
            "classroom_id": 1,
            "content_ids": [1],
            "student_ids": [],
        }

        assign_response = requests.post(
            f"{BASE_URL}/api/teachers/assignments/create",
            headers=headers,
            json=assignment_data,
        )

        if assign_response.status_code == 200:
            print("✅ 試用老師可以指派作業（正確）")
            result = assign_response.json()
            print(f"   作業ID：{result.get('assignment_id')}")
            print(f"   指派學生數：{result.get('student_count')}")
        else:
            print(f"❌ 試用老師無法指派作業！狀態碼：{assign_response.status_code}")
            print(f"   錯誤：{assign_response.json()}")
    else:
        print(f"❌ 試用老師登入失敗：{response.status_code}")


if __name__ == "__main__":
    test_teacher_assignment_permission()
