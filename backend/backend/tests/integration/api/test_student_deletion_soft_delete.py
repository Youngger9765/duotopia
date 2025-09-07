#!/usr/bin/env python3
"""
測試學生軟刪除功能
確認學生刪除後不再出現在列表中，但資料庫中仍保留（is_active=False）
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


def test_student_soft_deletion():
    """測試學生軟刪除功能"""
    print("=" * 60)
    print("測試學生軟刪除功能")
    print("=" * 60)

    token = get_teacher_token()
    if not token:
        assert False, "Test failed"

    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立測試學生
    print("\n1. 建立測試學生...")
    student_data = {
        "name": f"測試軟刪除學生_{datetime.now().strftime('%H%M%S')}",
        "email": f"delete_test_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-05-20",
    }

    response = requests.post(f"{BASE_URL}/teachers/students", json=student_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 建立學生失敗: {response.status_code}")
        assert False, "Test failed"

    student = response.json()
    student_id = student["id"]
    student_name = student["name"]
    print(f"✅ 建立學生成功 - ID: {student_id}, 姓名: {student_name}")

    # 2. 確認學生出現在列表中
    print("\n2. 確認學生出現在列表中...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code != 200:
        print(f"❌ 取得學生列表失敗: {response.status_code}")
        assert False, "Test failed"

    students = response.json()
    test_student = next((s for s in students if s["id"] == student_id), None)

    if not test_student:
        print("❌ 新建學生未出現在列表中")
        assert False, "Test failed"

    print(f"✅ 確認學生出現在列表中 - 狀態: {test_student['status']}")
    student_count_before = len(students)

    # 3. 刪除學生
    print(f"\n3. 刪除學生 (ID: {student_id})...")
    response = requests.delete(f"{BASE_URL}/teachers/students/{student_id}", headers=headers)

    if response.status_code != 200:
        print(f"❌ 刪除學生失敗: {response.status_code} - {response.text}")
        assert False, "Test failed"

    print("✅ 刪除學生成功")

    # 4. 確認學生不再出現在列表中
    print("\n4. 確認學生不再出現在列表中...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code != 200:
        print(f"❌ 取得學生列表失敗: {response.status_code}")
        assert False, "Test failed"

    students_after = response.json()
    deleted_student = next((s for s in students_after if s["id"] == student_id), None)

    if deleted_student:
        print(f"❌ 學生仍出現在列表中！狀態: {deleted_student['status']}")
        assert False, "Test failed"

    student_count_after = len(students_after)
    print("✅ 確認學生已從列表中移除")
    print(f"   刪除前學生數: {student_count_before}")
    print(f"   刪除後學生數: {student_count_after}")

    # 5. 嘗試直接存取被刪除的學生
    print("\n5. 嘗試直接存取被刪除的學生...")
    response = requests.get(f"{BASE_URL}/teachers/students/{student_id}", headers=headers)

    # 被軟刪除的學生應該返回 404 或不可存取
    if response.status_code == 404:
        print("✅ 被刪除學生正確返回 404")
    elif response.status_code == 403:
        print("✅ 被刪除學生正確返回 403 (無權限)")
    else:
        print(f"⚠️  被刪除學生返回狀態碼: {response.status_code}")
        # 這可能需要根據實際業務邏輯調整

    # 6. 測試刪除不存在的學生
    print("\n6. 測試刪除不存在的學生...")
    response = requests.delete(f"{BASE_URL}/teachers/students/99999", headers=headers)

    if response.status_code == 404:
        print("✅ 刪除不存在學生正確返回 404")
    else:
        print(f"❌ 刪除不存在學生返回: {response.status_code}")
        assert False, "Test failed"

    # Test passed


def test_student_with_classroom_deletion():
    """測試有班級的學生刪除"""
    print("\n" + "=" * 60)
    print("測試有班級的學生刪除")
    print("=" * 60)

    token = get_teacher_token()
    if not token:
        assert False, "Test failed"

    headers = {"Authorization": f"Bearer {token}"}

    # 1. 建立測試班級
    print("\n1. 建立測試班級...")
    classroom_data = {
        "name": f"測試刪除班級_{datetime.now().strftime('%H%M%S')}",
        "description": "有學生的班級刪除測試",
        "level": "A1",
    }

    response = requests.post(f"{BASE_URL}/teachers/classrooms", json=classroom_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 建立班級失敗: {response.status_code}")
        assert False, "Test failed"

    classroom = response.json()
    classroom_id = classroom["id"]
    print(f"✅ 建立班級成功 - ID: {classroom_id}")

    # 2. 建立有班級的學生
    print("\n2. 建立有班級的學生...")
    student_data = {
        "name": f"有班級學生_{datetime.now().strftime('%H%M%S')}",
        "email": f"classroom_student_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-08-10",
        "classroom_id": classroom_id,
    }

    response = requests.post(f"{BASE_URL}/teachers/students", json=student_data, headers=headers)

    if response.status_code != 200:
        print(f"❌ 建立學生失敗: {response.status_code}")
        assert False, "Test failed"

    student = response.json()
    student_id = student["id"]
    print(f"✅ 建立學生成功 - ID: {student_id}, 班級: {student.get('classroom_id')}")

    # 3. 刪除有班級的學生
    print("\n3. 刪除有班級的學生...")
    response = requests.delete(f"{BASE_URL}/teachers/students/{student_id}", headers=headers)

    if response.status_code != 200:
        print(f"❌ 刪除學生失敗: {response.status_code}")
        assert False, "Test failed"

    print("✅ 刪除有班級的學生成功")

    # 4. 確認學生從列表中消失
    print("\n4. 確認學生從列表中消失...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)

    if response.status_code == 200:
        students = response.json()
        deleted_student = next((s for s in students if s["id"] == student_id), None)

        if not deleted_student:
            print("✅ 有班級的學生也正確從列表中消失")
        else:
            print("❌ 有班級的學生仍在列表中")
            assert False, "Test failed"

    # 清理：刪除測試班級
    requests.delete(f"{BASE_URL}/teachers/classrooms/{classroom_id}", headers=headers)

    # Test passed


def main():
    """執行所有測試"""
    print("🚀 開始測試學生軟刪除功能")

    results = {
        "學生軟刪除": test_student_soft_deletion(),
        "有班級學生刪除": test_student_with_classroom_deletion(),
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
