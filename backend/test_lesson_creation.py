#!/usr/bin/env python3
"""測試單元建立功能"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_lesson_creation():
    # 1. 登入個體戶教師
    login_data = {
        "username": "teacher@example.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", data=login_data)
    if response.status_code != 200:
        print(f"登入失敗: {response.status_code} - {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. 獲取教室列表
    response = requests.get(f"{BASE_URL}/api/individual/classrooms", headers=headers)
    if response.status_code != 200:
        print(f"獲取教室失敗: {response.status_code}")
        return
        
    classrooms = response.json()
    if not classrooms:
        print("沒有找到教室")
        return
        
    classroom_id = classrooms[0]["id"]
    print(f"使用教室: {classrooms[0]['name']} (ID: {classroom_id})")
    
    # 3. 獲取該教室的課程
    response = requests.get(f"{BASE_URL}/api/individual/classrooms/{classroom_id}/courses", headers=headers)
    if response.status_code != 200:
        print(f"獲取課程失敗: {response.status_code}")
        return
        
    courses = response.json()
    if not courses:
        print("該教室沒有課程")
        return
        
    course_id = courses[0]["id"]
    print(f"使用課程: {courses[0]['title']} (ID: {course_id})")
    
    # 4. 獲取現有課時數量
    response = requests.get(f"{BASE_URL}/api/individual/courses/{course_id}/lessons", headers=headers)
    if response.status_code != 200:
        print(f"獲取課時失敗: {response.status_code}")
        return
        
    lessons = response.json()
    next_lesson_number = len(lessons) + 1
    print(f"現有課時數: {len(lessons)}")
    
    # 5. 建立新課時
    lesson_data = {
        "lesson_number": next_lesson_number,
        "title": f"測試單元 {next_lesson_number}",
        "activity_type": "reading_assessment",
        "time_limit_minutes": 30,
        "content": {
            "instructions": "請完成以下練習",
            "materials": [],
            "objectives": []
        },
        "is_active": True
    }
    
    print(f"\n建立課時資料: {json.dumps(lesson_data, ensure_ascii=False, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/individual/courses/{course_id}/lessons",
        headers=headers,
        json=lesson_data
    )
    
    if response.status_code == 200:
        print(f"\n✅ 課時建立成功！")
        print(f"回應: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    else:
        print(f"\n❌ 課時建立失敗!")
        print(f"狀態碼: {response.status_code}")
        print(f"錯誤訊息: {response.text}")

if __name__ == "__main__":
    test_lesson_creation()