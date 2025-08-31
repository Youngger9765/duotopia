#!/usr/bin/env python3
"""
本地測試學生管理功能
測試班級分配和刪除功能是否正常工作
"""

import requests
import json
from datetime import datetime
import sys

BASE_URL = "http://localhost:8000/api"

def test_local_functionality():
    """測試本地學生管理功能"""
    print("🧪 測試本地學生管理功能")
    print("=" * 50)
    
    # 1. 教師登入
    print("\n1. 教師登入...")
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"}
    )
    
    if response.status_code != 200:
        print(f"❌ 登入失敗: {response.status_code}")
        return False
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登入成功")
    
    # 2. 取得現有班級
    print("\n2. 取得班級列表...")
    response = requests.get(f"{BASE_URL}/teachers/classrooms", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 取得班級失敗: {response.status_code}")
        return False
    
    classrooms = response.json()
    print(f"✅ 找到 {len(classrooms)} 個班級")
    
    if not classrooms:
        print("⚠️  沒有班級，先建立一個...")
        classroom_data = {
            "name": "測試班級",
            "description": "本地測試用班級",
            "level": "A1"
        }
        response = requests.post(
            f"{BASE_URL}/teachers/classrooms",
            json=classroom_data,
            headers=headers
        )
        if response.status_code == 200:
            classrooms = [response.json()]
            print("✅ 建立測試班級成功")
        else:
            print("❌ 建立班級失敗")
            return False
    
    classroom_id = classrooms[0]["id"]
    classroom_name = classrooms[0]["name"]
    print(f"   使用班級: {classroom_name} (ID: {classroom_id})")
    
    # 3. 建立測試學生（無班級）
    print("\n3. 建立無班級學生...")
    timestamp = int(datetime.now().timestamp())
    student_data = {
        "name": f"本地測試學生_{timestamp}",
        "email": f"local_test_{timestamp}@duotopia.local",
        "birthdate": "2012-01-15"
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/students",
        json=student_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 建立學生失敗: {response.status_code} - {response.text}")
        return False
    
    student = response.json()
    student_id = student["id"]
    print(f"✅ 建立學生成功 - ID: {student_id}")
    
    # 4. 確認學生列表
    print("\n4. 確認學生出現在列表中...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 取得學生列表失敗: {response.status_code}")
        return False
    
    students = response.json()
    test_student = next((s for s in students if s['id'] == student_id), None)
    
    if not test_student:
        print("❌ 學生未出現在列表中")
        return False
    
    print(f"✅ 學生在列表中 - 班級: {test_student['classroom_name']}")
    
    # 5. 測試班級分配
    print(f"\n5. 分配學生到班級 (ID: {classroom_id})...")
    update_data = {"classroom_id": classroom_id}
    
    response = requests.put(
        f"{BASE_URL}/teachers/students/{student_id}",
        json=update_data,
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 分配班級失敗: {response.status_code} - {response.text}")
        return False
    
    print("✅ 分配班級成功")
    
    # 6. 確認班級分配
    print("\n6. 確認班級分配...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)
    
    if response.status_code == 200:
        students = response.json()
        test_student = next((s for s in students if s['id'] == student_id), None)
        
        if test_student and test_student['classroom_id'] == classroom_id:
            print(f"✅ 班級分配成功 - 班級: {test_student['classroom_name']}")
        else:
            print(f"❌ 班級分配失敗 - 實際班級ID: {test_student['classroom_id'] if test_student else 'None'}")
            return False
    
    # 7. 測試學生刪除
    print(f"\n7. 刪除學生 (ID: {student_id})...")
    response = requests.delete(
        f"{BASE_URL}/teachers/students/{student_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ 刪除學生失敗: {response.status_code} - {response.text}")
        return False
    
    print("✅ 刪除學生成功")
    
    # 8. 確認學生已被刪除
    print("\n8. 確認學生已從列表移除...")
    response = requests.get(f"{BASE_URL}/teachers/students", headers=headers)
    
    if response.status_code == 200:
        students = response.json()
        test_student = next((s for s in students if s['id'] == student_id), None)
        
        if not test_student:
            print("✅ 學生已從列表中移除")
        else:
            print(f"❌ 學生仍在列表中 - 狀態: {test_student['status']}")
            return False
    
    # 9. 確認刪除的學生無法直接存取
    print("\n9. 確認刪除的學生無法存取...")
    response = requests.get(
        f"{BASE_URL}/teachers/students/{student_id}",
        headers=headers
    )
    
    if response.status_code == 404:
        print("✅ 刪除的學生正確返回 404")
    else:
        print(f"❌ 刪除的學生仍可存取 - 狀態碼: {response.status_code}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 本地測試全部通過！")
    print("   - 學生建立 ✅")
    print("   - 班級分配 ✅") 
    print("   - 學生刪除 ✅")
    print("   - 軟刪除隱藏 ✅")
    
    return True

if __name__ == "__main__":
    try:
        success = test_local_functionality()
        if success:
            print("\n✨ 功能正常，可以在前端測試了！")
        else:
            print("\n❌ 發現問題，需要修復")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 測試過程出錯: {e}")
        sys.exit(1)