#!/usr/bin/env python3
"""
測試新增學生（不指定班級）
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def test_add_student_without_classroom():
    """測試新增學生不指定班級"""
    session = requests.Session()
    
    # 1. 教師登入
    print("1. 教師登入...")
    response = session.post(
        f"{BASE_URL}/auth/teacher/login",
        json={
            "email": "demo@duotopia.com",
            "password": "demo123"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        print(response.text)
        return False
    
    teacher_data = response.json()
    token = teacher_data["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"✅ 教師登入成功: {teacher_data['user']['name']}")
    
    # 2. 新增學生（不指定班級）
    print("\n2. 新增學生（不指定班級）...")
    student_data = {
        "name": "無班級測試學生",
        "email": f"no_class_{int(datetime.now().timestamp())}@duotopia.local",
        "birthdate": "2012-01-01",
        "student_id": f"NOCLASS{int(datetime.now().timestamp())}"
        # 注意：沒有 classroom_id
    }
    
    print(f"   發送資料: {json.dumps(student_data, indent=2, ensure_ascii=False)}")
    
    response = session.post(
        f"{BASE_URL}/teachers/students",
        json=student_data
    )
    
    print(f"   狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ 新增學生成功（無班級）！")
        print(f"   學生ID: {result['id']}")
        print(f"   姓名: {result['name']}")
        print(f"   Email: {result['email']}")
        print(f"   班級ID: {result.get('classroom_id', '無')}")
        print(f"   預設密碼: {result.get('default_password', 'N/A')}")
        return True
    else:
        print(f"❌ 新增學生失敗: {response.status_code}")
        print(f"   錯誤訊息: {response.text}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 測試新增學生（不指定班級）")
    print("=" * 60)
    success = test_add_student_without_classroom()
    
    if success:
        print("\n✅ 測試通過！學生可以在不指定班級的情況下建立")
    else:
        print("\n❌ 測試失敗！")