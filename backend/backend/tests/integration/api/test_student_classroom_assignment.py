#!/usr/bin/env python3
"""
測試學生班級分配功能
確認學生可以在創建後分配到班級，並且可以重新分配
"""

import requests
from datetime import datetime  # noqa: F401
import sys

BASE_URL = "http://localhost:8000/api"


def get_teacher_token():
    """取得教師 token"""
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"},
    )
    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        return None
    return response.json()["access_token"]


def test_student_classroom_assignment():
    """測試學生班級分配功能"""
    print("=" * 60)
    print("測試學生班級分配功能")
    print("=" * 60)

    token = get_teacher_token()
    assert token is not None, "教師登入失敗"

    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立測試班級
    print("\n1. 建立測試班級...")
    classroom_data = {
        "name": f"測試班級_{datetime.now().strftime('%H%M%S')}",
        "description": "用於測試班級分配",
        "level": "A2",
    }

    response = requests.post(f"{BASE_URL}/teachers/classrooms", json=classroom_data, headers=headers)

    assert response.status_code == 200, f"建立班級失敗: {response.status_code}"

    classroom = response.json()
    classroom_id = classroom["id"]
    print(f"✅ 建立班級成功 - ID: {classroom_id}")

    # 2. 建立無班級學生
    print("\n2. 建立無班級學生...")
    student_data = {
        "name": f"測試學生_{datetime.now().strftime('%H%M%S')}",
        "email": f"assign_test_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-03-15",
        # 注意：沒有 classroom_id
    }

    response = requests.post(f"{BASE_URL}/teachers/students", json=student_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 建立學生失敗: {response.status_code}")
        assert False, "Test failed"

    student = response.json()
    student_id = student["id"]
    print(f"✅ 建立學生成功 - ID: {student_id}, 班級: {student.get('classroom_id', '無')}")

    # 3. 確認學生顯示為未分配
    print("\n3. 確認學生顯示為未分配...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code != 200:
        print(f"❌ 取得學生列表失敗: {response.status_code}")
        assert False, "Test failed"

    students = response.json()
    test_student = next((s for s in students if s["id"] == student_id), None)

    if not test_student:
        print("❌ 找不到測試學生")
        assert False, "Test failed"

    if test_student["classroom_name"] != "未分配":
        print(f"❌ 學生應該顯示為未分配，實際: {test_student['classroom_name']}")
        assert False, "Test failed"

    print("✅ 確認學生顯示為未分配")

    # 4. 分配學生到班級
    print(f"\n4. 分配學生到班級 (班級ID: {classroom_id})...")
    update_data = {"classroom_id": classroom_id}

    response = requests.put(f"{BASE_URL}/teachers/students/{student_id}", json=update_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 分配學生到班級失敗: {response.status_code} - {response.text}")
        assert False, "Test failed"

    print("✅ 分配學生到班級成功")

    # 5. 確認學生已分配到班級
    print("\n5. 確認學生已分配到班級...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code == 200:
        students = response.json()
        test_student = next((s for s in students if s["id"] == student_id), None)

        if test_student and test_student["classroom_id"] == classroom_id:
            print(f"✅ 確認學生已分配到班級: {test_student['classroom_name']}")
        else:
            print(f"❌ 學生分配失敗 - classroom_id: {test_student['classroom_id'] if test_student else 'None'}")
            assert False, "Test failed"

    # 6. 建立第二個班級測試重新分配
    print("\n6. 建立第二個班級...")
    classroom2_data = {
        "name": f"測試班級2_{datetime.now().strftime('%H%M%S')}",
        "description": "用於測試重新分配",
        "level": "B1",
    }

    response = requests.post(f"{BASE_URL}/teachers/classrooms", json=classroom2_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 建立第二個班級失敗: {response.status_code}")
        assert False, "Test failed"

    classroom2 = response.json()
    classroom2_id = classroom2["id"]
    print(f"✅ 建立第二個班級成功 - ID: {classroom2_id}")

    # 7. 重新分配學生到第二個班級
    print("\n7. 重新分配學生到第二個班級...")
    update_data = {"classroom_id": classroom2_id}

    response = requests.put(f"{BASE_URL}/teachers/students/{student_id}", json=update_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 重新分配學生失敗: {response.status_code}")
        assert False, "Test failed"

    print("✅ 重新分配學生成功")

    # 8. 確認學生已重新分配
    print("\n8. 確認學生已重新分配...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code == 200:
        students = response.json()
        test_student = next((s for s in students if s["id"] == student_id), None)

        if test_student and test_student["classroom_id"] == classroom2_id:
            print(f"✅ 確認學生已重新分配到班級: {test_student['classroom_name']}")
        else:
            print("❌ 學生重新分配失敗")
            assert False, "Test failed"

    # 9. 取消班級分配（設為未分配）
    print("\n9. 取消班級分配...")
    update_data = {"classroom_id": 0}  # 0 表示取消分配

    response = requests.put(f"{BASE_URL}/teachers/students/{student_id}", json=update_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 取消班級分配失敗: {response.status_code}")
        assert False, "Test failed"

    print("✅ 取消班級分配成功")

    # 10. 確認學生回到未分配狀態
    print("\n10. 確認學生回到未分配狀態...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code == 200:
        students = response.json()
        test_student = next((s for s in students if s["id"] == student_id), None)

        if test_student and test_student["classroom_name"] == "未分配":
            print("✅ 確認學生回到未分配狀態")
        else:
            print(f"❌ 學生未回到未分配狀態: {test_student['classroom_name'] if test_student else 'None'}")
            assert False, "Test failed"

    # 清理：刪除測試資料
    requests.delete(f"{BASE_URL}/teachers/students/{student_id}", headers=headers)
    requests.delete(f"{BASE_URL}/teachers/classrooms/{classroom_id}", headers=headers)
    requests.delete(f"{BASE_URL}/teachers/classrooms/{classroom2_id}", headers=headers)

    # Test passed


def main():
    """執行測試"""
    print("🚀 開始測試學生班級分配功能")

    result = test_student_classroom_assignment()

    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)

    if result:
        print("✅ 學生班級分配功能")
        print("\n🎉 測試通過！")
        return 0
    else:
        print("❌ 學生班級分配功能")
        print("\n⚠️ 測試失敗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
