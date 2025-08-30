#!/usr/bin/env python3
"""測試 Reading Assessment Editor API"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_teacher_login():
    """測試教師登入獲取 token"""
    # 這裡需要實際的教師 token，可從瀏覽器開發者工具取得
    print("請從瀏覽器開發者工具複製 JWT token...")
    return input("Token: ").strip()

def test_get_classrooms(token):
    """獲取教師的班級列表"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teacher/classrooms", headers=headers)
    
    if response.status_code == 200:
        classrooms = response.json()
        print(f"✅ 成功獲取 {len(classrooms)} 個班級")
        if classrooms:
            return classrooms[0]['id']
    else:
        print(f"❌ 獲取班級失敗: {response.status_code}")
        print(response.text)
    return None

def test_get_programs(token, classroom_id):
    """獲取班級的課程"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/teacher/classrooms/{classroom_id}/programs", headers=headers)
    
    if response.status_code == 200:
        programs = response.json()
        print(f"✅ 成功獲取 {len(programs)} 個課程")
        if programs and programs[0].get('lessons'):
            return programs[0]['lessons'][0]['id']
    else:
        print(f"❌ 獲取課程失敗: {response.status_code}")
    return None

def test_create_reading_content(token, lesson_id):
    """創建朗讀錄音內容"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "type": "reading_assessment",
        "title": "測試朗讀錄音",
        "items": [
            {
                "text": "Hello, how are you?",
                "translation": "你好，你好嗎？"
            },
            {
                "text": "I am fine, thank you.",
                "translation": "我很好，謝謝。"
            },
            {
                "text": "What is your name?",
                "translation": "你叫什麼名字？"
            }
        ],
        "target_wpm": 60,
        "target_accuracy": 0.8,
        "level": "A1",
        "tags": ["greeting", "basic"]
    }
    
    response = requests.post(
        f"{BASE_URL}/api/lessons/{lesson_id}/contents",
        headers=headers,
        json=data
    )
    
    if response.status_code in [200, 201]:
        print("✅ 成功創建朗讀錄音內容")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"❌ 創建內容失敗: {response.status_code}")
        print(response.text)

def main():
    print("=== Reading Assessment Editor API 測試 ===\n")
    
    # 1. 獲取 token
    token = test_teacher_login()
    if not token:
        print("需要有效的 token 才能繼續測試")
        return
    
    print("\n--- 測試 API 連接 ---")
    
    # 2. 獲取班級
    classroom_id = test_get_classrooms(token)
    if not classroom_id:
        print("無法獲取班級資訊")
        return
    
    # 3. 獲取課程和課程單元
    lesson_id = test_get_programs(token, classroom_id)
    if not lesson_id:
        print("無法獲取課程單元資訊")
        return
    
    # 4. 創建朗讀錄音內容
    print(f"\n--- 測試創建朗讀錄音內容 (Lesson ID: {lesson_id}) ---")
    test_create_reading_content(token, lesson_id)

if __name__ == "__main__":
    main()