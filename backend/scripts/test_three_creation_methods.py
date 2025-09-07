#!/usr/bin/env python3
"""
Test all three methods of creating programs in a classroom:
1. Copy from template
2. Copy from another classroom
3. Create custom
"""

import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


BASE_URL = "http://localhost:8000"


def get_teacher_token(email: str = "demo@duotopia.com", password: str = "demo123"):
    """Get authentication token for teacher"""
    response = requests.post(
        f"{BASE_URL}/api/auth/teacher/login",
        json={"email": email, "password": password},
    )

    if response.status_code != 200:
        print(f"❌ Failed to login: {response.status_code}")
        print(response.text)
        return None

    return response.json()["access_token"]


def test_copy_from_template(token: str, classroom_id: int):
    """Test copying from public template"""
    headers = {"Authorization": f"Bearer {token}"}

    # Get available templates
    templates_response = requests.get(f"{BASE_URL}/api/programs/templates", headers=headers)

    if templates_response.status_code != 200:
        print(f"❌ Failed to get templates: {templates_response.status_code}")
        return False

    templates = templates_response.json()
    if not templates:
        print("❌ No templates available")
        return False

    template = templates[0]
    print(f"\n📋 Copying template: {template['name']}")

    # Copy template to classroom
    response = requests.post(
        f"{BASE_URL}/api/programs/copy-from-template",
        headers=headers,
        json={
            "template_id": template["id"],
            "classroom_id": classroom_id,
            "name": f"[從模板] {template['name']}",
        },
    )

    if response.status_code == 200:
        new_program = response.json()
        print(f"✅ Successfully created program from template: {new_program['name']}")
        print(f"   - ID: {new_program['id']}")
        print(f"   - Source: {new_program.get('source_type', 'unknown')}")
        return True
    else:
        print(f"❌ Failed to copy from template: {response.status_code}")
        print(response.text)
        return False


def test_copy_from_classroom(token: str, source_classroom_id: int, target_classroom_id: int):
    """Test copying from another classroom"""
    headers = {"Authorization": f"Bearer {token}"}

    # Get programs from source classroom
    programs_response = requests.get(f"{BASE_URL}/api/programs/classroom/{source_classroom_id}", headers=headers)

    if programs_response.status_code != 200:
        print(f"❌ Failed to get classroom programs: {programs_response.status_code}")
        return False

    programs = programs_response.json()
    if not programs:
        print("❌ No programs in source classroom")
        return False

    program = programs[0]
    print(f"\n📁 Copying from classroom: {program['name']}")

    # Copy to target classroom
    response = requests.post(
        f"{BASE_URL}/api/programs/copy-from-classroom",
        headers=headers,
        json={
            "source_program_id": program["id"],
            "target_classroom_id": target_classroom_id,
            "name": f"[從班級] {program['name']}",
        },
    )

    if response.status_code == 200:
        new_program = response.json()
        print(f"✅ Successfully copied from classroom: {new_program['name']}")
        print(f"   - ID: {new_program['id']}")
        print(f"   - Source: {new_program.get('source_type', 'unknown')}")
        return True
    else:
        print(f"❌ Failed to copy from classroom: {response.status_code}")
        print(response.text)
        return False


def test_create_custom(token: str, classroom_id: int):
    """Test creating custom program"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n➕ Creating custom program")

    response = requests.post(
        f"{BASE_URL}/api/programs/create-custom?classroom_id={classroom_id}",
        headers=headers,
        json={
            "name": "[自建] 測試自訂課程",
            "description": "這是一個測試用的自訂課程",
            "level": "B2",
            "estimated_hours": 15,
            "tags": ["custom", "test", "demo"],
        },
    )

    if response.status_code == 200:
        new_program = response.json()
        print(f"✅ Successfully created custom program: {new_program['name']}")
        print(f"   - ID: {new_program['id']}")
        print(f"   - Source: {new_program.get('source_type', 'unknown')}")
        print(f"   - Level: {new_program.get('level', 'N/A')}")
        print(f"   - Hours: {new_program.get('estimated_hours', 0)}")
        return True
    else:
        print(f"❌ Failed to create custom program: {response.status_code}")
        print(response.text)
        return False


def get_or_create_test_classrooms(token: str):
    """Get or create test classrooms"""
    headers = {"Authorization": f"Bearer {token}"}

    # Get existing classrooms
    response = requests.get(f"{BASE_URL}/api/teachers/classrooms", headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to get classrooms: {response.status_code}")
        return None, None

    classrooms = response.json()

    # Find or create source classroom
    source_classroom = next((c for c in classrooms if c["name"] == "測試源班級"), None)
    if not source_classroom:
        # Create source classroom
        create_response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms",
            headers=headers,
            json={
                "name": "測試源班級",
                "description": "用於測試複製功能的源班級",
                "level": "A1",
            },
        )
        if create_response.status_code == 200:
            source_classroom = create_response.json()
            print(f"Created source classroom: {source_classroom['name']}")
        else:
            print(f"❌ Failed to create source classroom: {create_response.status_code}")
            return None, None

    # Find or create target classroom
    target_classroom = next((c for c in classrooms if c["name"] == "測試目標班級"), None)
    if not target_classroom:
        # Create target classroom
        create_response = requests.post(
            f"{BASE_URL}/api/teachers/classrooms",
            headers=headers,
            json={
                "name": "測試目標班級",
                "description": "用於測試三種建立方式的目標班級",
                "level": "A1",
            },
        )
        if create_response.status_code == 200:
            target_classroom = create_response.json()
            print(f"Created target classroom: {target_classroom['name']}")
        else:
            print(f"❌ Failed to create target classroom: {create_response.status_code}")
            return None, None

    return source_classroom, target_classroom


def main():
    print("=" * 60)
    print("測試三種課程建立方式")
    print("=" * 60)

    # Get authentication token
    token = get_teacher_token()
    if not token:
        print("❌ Failed to authenticate")
        return

    print("✅ Authentication successful")

    # Get or create test classrooms
    source_classroom, target_classroom = get_or_create_test_classrooms(token)
    if not source_classroom or not target_classroom:
        print("❌ Failed to get/create test classrooms")
        return

    print("\n📚 Using classrooms:")
    print(f"   - Source: {source_classroom['name']} (ID: {source_classroom['id']})")
    print(f"   - Target: {target_classroom['name']} (ID: {target_classroom['id']})")

    # Test 1: Copy from template
    print("\n" + "=" * 40)
    print("測試 1: 從公版模板複製")
    print("=" * 40)
    success1 = test_copy_from_template(token, target_classroom["id"])

    # First, ensure source classroom has a program
    print("\n準備源班級...")
    test_copy_from_template(token, source_classroom["id"])

    # Test 2: Copy from another classroom
    print("\n" + "=" * 40)
    print("測試 2: 從其他班級複製")
    print("=" * 40)
    success2 = test_copy_from_classroom(token, source_classroom["id"], target_classroom["id"])

    # Test 3: Create custom
    print("\n" + "=" * 40)
    print("測試 3: 自建課程")
    print("=" * 40)
    success3 = test_create_custom(token, target_classroom["id"])

    # Summary
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    print(f"1. 從公版模板複製: {'✅ 成功' if success1 else '❌ 失敗'}")
    print(f"2. 從其他班級複製: {'✅ 成功' if success2 else '❌ 失敗'}")
    print(f"3. 自建課程:       {'✅ 成功' if success3 else '❌ 失敗'}")

    # Show final programs in target classroom
    headers = {"Authorization": f"Bearer {token}"}
    final_programs = requests.get(f"{BASE_URL}/api/programs/classroom/{target_classroom['id']}", headers=headers).json()

    print(f"\n目標班級最終課程數量: {len(final_programs)}")
    for prog in final_programs:
        print(f"  - {prog['name']} (來源: {prog.get('source_type', 'unknown')})")

    if all([success1, success2, success3]):
        print("\n🎉 所有測試通過！三種建立方式都正常運作。")
    else:
        print("\n⚠️ 部分測試失敗，請檢查上面的錯誤訊息。")


if __name__ == "__main__":
    main()
