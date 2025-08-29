#!/usr/bin/env python3

import requests
import json

# 登入取得 token
login_response = requests.post(
    'http://localhost:8000/api/auth/teacher/login',
    json={'email': 'demo@duotopia.com', 'password': 'demo123'}
)

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    
    # 獲取所有 programs
    programs_response = requests.get(
        'http://localhost:8000/api/teachers/programs',
        headers=headers
    )
    
    print("=== Programs 列表 ===")
    programs = programs_response.json()
    for program in programs:  # 顯示所有
        print(f"Program {program['id']}: {program['name']}")
        
        # 獲取 program 詳細資料（包含 lessons）
        detail_response = requests.get(
            f'http://localhost:8000/api/teachers/programs/{program["id"]}',
            headers=headers
        )
        
        if detail_response.status_code == 200:
            detail = detail_response.json()
            print(f"  Lessons:")
            for lesson in detail.get('lessons', []):
                print(f"    - Lesson {lesson['id']}: {lesson['name']}")
                print(f"      描述: {lesson.get('description', 'N/A')}")
                print(f"      順序: {lesson.get('order_index', 'N/A')}")
                print(f"      時間: {lesson.get('estimated_minutes', 'N/A')} 分鐘")
        else:
            print(f"  無法獲取詳細資料: {detail_response.status_code}")
        print()
else:
    print(f"登入失敗: {login_response.status_code}")
    print(login_response.json())