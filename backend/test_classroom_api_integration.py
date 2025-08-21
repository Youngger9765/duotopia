#!/usr/bin/env python3
"""
教室功能整合測試 - 快速驗證 API 是否正常運作
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def test_classroom_api_integration():
    """整合測試教室相關 API"""
    print("=== 教室功能整合測試 ===\n")
    
    try:
        # 1. 登入
        print("1. 登入...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": "teacher@individual.com", "password": "test123"}
        )
        if response.status_code != 200:
            print(f"❌ 登入失敗: {response.status_code}")
            return False
            
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登入成功")
        
        # 2. 獲取教室列表
        print("\n2. 獲取教室列表...")
        response = requests.get(f"{BASE_URL}/api/individual/classrooms", headers=headers)
        if response.status_code != 200:
            print(f"❌ 獲取教室列表失敗: {response.status_code}")
            return False
            
        classrooms = response.json()
        if not classrooms:
            print("❌ 沒有找到教室")
            return False
            
        classroom = classrooms[0]
        classroom_id = classroom["id"]
        print(f"✅ 找到 {len(classrooms)} 個教室，選擇: {classroom['name']}")
        
        # 3. 獲取教室學生
        print(f"\n3. 獲取教室學生 (ID: {classroom_id})...")
        response = requests.get(
            f"{BASE_URL}/api/individual/classrooms/{classroom_id}/students", 
            headers=headers
        )
        if response.status_code != 200:
            print(f"❌ 獲取學生失敗: {response.status_code} - {response.text}")
            return False
            
        students = response.json()
        print(f"✅ 找到 {len(students)} 個學生")
        
        # 4. 獲取教室課程
        print(f"\n4. 獲取教室課程...")
        response = requests.get(
            f"{BASE_URL}/api/individual/classrooms/{classroom_id}/courses",
            headers=headers
        )
        if response.status_code != 200:
            print(f"❌ 獲取課程失敗: {response.status_code} - {response.text}")
            return False
            
        courses = response.json()
        print(f"✅ 找到 {len(courses)} 個課程")
        
        # 5. 獲取公版課程
        print(f"\n5. 獲取公版課程...")
        response = requests.get(f"{BASE_URL}/api/individual/courses/public", headers=headers)
        if response.status_code != 200:
            print(f"❌ 獲取公版課程失敗: {response.status_code} - {response.text}")
            return False
            
        public_courses = response.json()
        print(f"✅ 找到 {len(public_courses)} 個公版課程")
        
        # 6. 測試複製課程
        if public_courses:
            print(f"\n6. 測試複製課程...")
            source_course = public_courses[0]
            response = requests.post(
                f"{BASE_URL}/api/individual/classrooms/{classroom_id}/courses/copy",
                headers=headers,
                json={"source_course_id": source_course["id"]}
            )
            
            if response.status_code == 200:
                copied_course = response.json()
                print(f"✅ 成功複製課程: {copied_course['title']}")
                print(f"   複製來源: {source_course['title']}")
                print(f"   教室ID: {copied_course['classroom_id']}")
            else:
                print(f"❌ 複製課程失敗: {response.status_code} - {response.text}")
                return False
        else:
            print("⚠️  沒有公版課程可複製")
        
        print(f"\n✅ 所有測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def test_specific_endpoints():
    """測試特定端點的詳細資訊"""
    print("\n=== 詳細端點測試 ===")
    
    # 登入
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={"username": "teacher@individual.com", "password": "test123"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 測試各個端點
    endpoints = [
        ("/api/individual/classrooms", "GET", "教室列表"),
        ("/api/individual/courses/public", "GET", "公版課程"),
    ]
    
    for endpoint, method, description in endpoints:
        print(f"\n測試 {method} {endpoint} ({description})")
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            
            print(f"  狀態碼: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"  回應長度: {len(data) if isinstance(data, list) else 1}")
                if isinstance(data, list) and data:
                    print(f"  第一筆資料鍵值: {list(data[0].keys())}")
            else:
                print(f"  錯誤: {response.text}")
                
        except Exception as e:
            print(f"  異常: {e}")

if __name__ == "__main__":
    print(f"測試時間: {datetime.now()}")
    
    success = test_classroom_api_integration()
    
    if success:
        test_specific_endpoints()
        print(f"\n🎉 整合測試完成！")
    else:
        print(f"\n💥 整合測試失敗，請檢查系統狀態")