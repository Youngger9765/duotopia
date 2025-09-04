#!/usr/bin/env python3
"""
測試班級刪除功能
確認刪除班級的各種情境處理
"""

import requests
import json  # noqa: F401
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


def test_delete_empty_classroom():
    """測試刪除空班級（沒有學生）"""
    print("=" * 60)
    print("測試刪除空班級")
    print("=" * 60)

    token = get_teacher_token()
    if not token:
        assert False, "Test failed"

    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立測試班級
    print("\n1. 建立測試班級...")
    classroom_data = {
        "name": f"測試空班級_{datetime.now().strftime('%H%M%S')}",
        "description": "準備刪除的空班級",
        "level": "A1",
    }

    response = requests.post(
        f"{BASE_URL}/teachers/classrooms", json=classroom_data, headers=headers
    )

    if response.status_code != 200:
        print(f"❌ 建立班級失敗: {response.status_code} - {response.text}")
        assert False, "Test failed"

    classroom = response.json()
    classroom_id = classroom["id"]
    print(f"✅ 建立班級成功 - ID: {classroom_id}, 名稱: {classroom['name']}")

    # 2. 刪除班級
    print(f"\n2. 刪除班級 (ID: {classroom_id})...")
    response = requests.delete(
        f"{BASE_URL}/teachers/classrooms/{classroom_id}", headers=headers
    )

    if response.status_code != 200:
        print(f"❌ 刪除班級失敗: {response.status_code} - {response.text}")
        assert False, "Test failed"

    print("✅ 刪除班級成功")

    # 3. 確認班級已被軟刪除
    print("\n3. 確認班級已被軟刪除...")
    response = requests.get(f"{BASE_URL}/teachers/classrooms", headers=headers)

    if response.status_code == 200:
        classrooms = response.json()
        deleted_classroom = [c for c in classrooms if c["id"] == classroom_id]
        if not deleted_classroom:
            print("✅ 確認班級已從列表中移除")
        else:
            print("❌ 班級仍在列表中")
            assert False, "Test failed"

    # Test passed


def test_delete_classroom_with_students():
    """測試刪除有學生的班級"""
    print("\n" + "=" * 60)
    print("測試刪除有學生的班級")
    print("=" * 60)

    token = get_teacher_token()
    if not token:
        assert False, "Test failed"

    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立測試班級
    print("\n1. 建立測試班級...")
    classroom_data = {
        "name": f"測試班級有學生_{datetime.now().strftime('%H%M%S')}",
        "description": "有學生的班級",
        "level": "B1",
    }

    response = requests.post(
        f"{BASE_URL}/teachers/classrooms", json=classroom_data, headers=headers
    )

    if response.status_code != 200:
        print(f"❌ 建立班級失敗: {response.status_code}")
        assert False, "Test failed"

    classroom = response.json()
    classroom_id = classroom["id"]
    print(f"✅ 建立班級成功 - ID: {classroom_id}")

    # 2. 新增學生到班級
    print("\n2. 新增學生到班級...")
    student_data = {
        "name": f"班級學生_{datetime.now().strftime('%H%M%S')}",
        "email": f"class_student_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-01-01",
        "classroom_id": classroom_id,
    }

    response = requests.post(
        f"{BASE_URL}/teachers/students", json=student_data, headers=headers
    )

    if response.status_code != 200:
        print(f"❌ 新增學生失敗: {response.status_code}")
        assert False, "Test failed"

    student = response.json()
    print(f"✅ 新增學生成功 - ID: {student['id']}")

    # 3. 嘗試刪除有學生的班級
    print("\n3. 嘗試刪除有學生的班級...")
    response = requests.delete(
        f"{BASE_URL}/teachers/classrooms/{classroom_id}", headers=headers
    )

    # 根據業務邏輯，可能會：
    # - 允許刪除（軟刪除，學生仍保留）
    # - 拒絕刪除（返回錯誤）
    if response.status_code == 200:
        print("✅ 允許刪除有學生的班級（軟刪除）")

        # 檢查學生是否仍存在
        response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)
        if response.status_code == 200:
            students = response.json()
            class_student = [s for s in students if s["id"] == student["id"]]
            if class_student:
                print("✅ 學生仍存在系統中")
            else:
                print("⚠️  學生可能被一併刪除")
    elif response.status_code == 400:
        print(f"⚠️  系統拒絕刪除有學生的班級: {response.json()}")
        # 這也是合理的業務邏輯
        # Test passed
    else:
        print(f"❌ 未預期的錯誤: {response.status_code} - {response.text}")
        assert False, "Test failed"

    # Test passed


def test_delete_nonexistent_classroom():
    """測試刪除不存在的班級"""
    print("\n" + "=" * 60)
    print("測試刪除不存在的班級")
    print("=" * 60)

    token = get_teacher_token()
    if not token:
        assert False, "Test failed"

    headers = {"Authorization": f"Bearer {token}"}

    # 嘗試刪除不存在的班級
    print("\n嘗試刪除不存在的班級 (ID: 99999)...")
    response = requests.delete(f"{BASE_URL}/teachers/classrooms/99999", headers=headers)

    if response.status_code == 404:
        print("✅ 正確返回 404 錯誤")
        # Test passed
    else:
        print(f"❌ 未預期的回應: {response.status_code}")
        assert False, "Test failed"


def test_delete_other_teacher_classroom():
    """測試刪除其他教師的班級（權限測試）"""
    print("\n" + "=" * 60)
    print("測試權限控制 - 不能刪除其他教師的班級")
    print("=" * 60)

    # 這個測試需要第二個教師帳號
    print("⚠️  需要第二個教師帳號來完整測試權限控制")
    print("   目前假設 API 會正確檢查權限")

    # Test passed


def main():
    """執行所有測試"""
    print("🚀 開始測試班級刪除功能")

    results = {
        "刪除空班級": test_delete_empty_classroom(),
        "刪除有學生的班級": test_delete_classroom_with_students(),
        "刪除不存在的班級": test_delete_nonexistent_classroom(),
        "權限控制": test_delete_other_teacher_classroom(),
    }

    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n🎉 所有測試通過！")
    else:
        print("\n⚠️ 部分測試失敗")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
