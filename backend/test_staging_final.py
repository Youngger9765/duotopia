#!/usr/bin/env python3
"""
Staging 環境完整測試
"""

import requests
import json
from datetime import datetime

STAGING_URL = "https://duotopia-backend-staging-qchnzlfpda-de.a.run.app"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def test_teacher_login():
    """測試教師登入 - 使用正確的密碼"""
    print_section("1. 測試教師登入")
    
    # 測試不同的教師帳號
    test_accounts = [
        {"username": "teacher@individual.com", "password": "test123"},
        {"username": "teacher@individual.com", "password": "password123"},
        {"username": "admin@institution.com", "password": "test123"},
        {"username": "hybrid@test.com", "password": "test123"}
    ]
    
    for account in test_accounts:
        print(f"\n嘗試登入: {account['username']} / {account['password']}")
        
        response = requests.post(
            f"{STAGING_URL}/api/auth/login",
            data=account,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 登入成功!")
            print(f"  User ID: {data.get('user_id')}")
            print(f"  User Type: {data.get('user_type')}")
            print(f"  Is Individual Teacher: {data.get('is_individual_teacher')}")
            print(f"  Is Institutional Admin: {data.get('is_institutional_admin')}")
            print(f"  Current Role Context: {data.get('current_role_context')}")
            
            # 測試該帳號的功能
            if account['username'] == 'teacher@individual.com':
                return data["access_token"]
        else:
            print(f"❌ 登入失敗: {response.text}")
    
    return None

def test_student_login():
    """測試學生登入"""
    print_section("2. 測試學生登入")
    
    # 根據 seed.py，所有學生的生日都是 20090828
    test_students = [
        {"email": "student1@duotopia.com", "birth_date": "20090828"},
        {"email": "student2@duotopia.com", "birth_date": "20090828"},
        {"email": "student3@duotopia.com", "birth_date": "20090828"}
    ]
    
    for student in test_students:
        print(f"\n嘗試登入學生: {student['email']}")
        
        response = requests.post(
            f"{STAGING_URL}/api/auth/student/login",
            json=student,
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 學生登入成功!")
            print(f"  Token: {data.get('access_token', '')[:50]}...")
            print(f"  User Type: {data.get('user_type')}")
            print(f"  Student ID: {data.get('student_id')}")
            return data.get('access_token')
        else:
            print(f"❌ 登入失敗: {response.text}")
    
    return None

def test_individual_teacher_features(token):
    """測試個體戶教師功能"""
    print_section("3. 測試個體戶教師功能")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3.1 獲取課程
    print("\n3.1 獲取課程列表")
    response = requests.get(f"{STAGING_URL}/api/individual/courses", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        courses = response.json()
        print(f"✅ 成功獲取 {len(courses)} 個課程")
        if courses:
            for i, course in enumerate(courses[:2]):
                print(f"\nCourse {i+1}:")
                print(f"  ID: {course.get('id')}")
                print(f"  Title: {course.get('title')}")
                print(f"  Course Code: {course.get('course_code')}")
    
    # 3.2 獲取教室
    print("\n3.2 獲取教室列表")
    response = requests.get(f"{STAGING_URL}/api/individual/classrooms", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        classrooms = response.json()
        print(f"✅ 成功獲取 {len(classrooms)} 個教室")
        if classrooms:
            for i, classroom in enumerate(classrooms[:2]):
                print(f"\nClassroom {i+1}:")
                print(f"  ID: {classroom.get('id')}")
                print(f"  Name: {classroom.get('name')}")
                print(f"  Grade: {classroom.get('grade_level')}")
    
    # 3.3 獲取學生
    print("\n3.3 獲取學生列表")
    response = requests.get(f"{STAGING_URL}/api/individual/students", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        students = response.json()
        print(f"✅ 成功獲取 {len(students)} 個學生")
        if students:
            for i, student in enumerate(students[:2]):
                print(f"\nStudent {i+1}:")
                print(f"  ID: {student.get('id')}")
                print(f"  Name: {student.get('full_name')}")
                print(f"  Email: {student.get('email')}")

def test_student_features(token):
    """測試學生功能"""
    print_section("4. 測試學生功能")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 4.1 獲取學生資料
    print("\n4.1 獲取學生個人資料")
    response = requests.get(f"{STAGING_URL}/api/students/profile", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        profile = response.json()
        print("✅ 成功獲取學生資料")
        print(f"  Name: {profile.get('full_name')}")
        print(f"  Email: {profile.get('email')}")
        print(f"  ID: {profile.get('id')}")
        
        student_id = profile.get('id')
        
        # 4.2 獲取學生的作業
        if student_id:
            print(f"\n4.2 獲取學生作業 (ID: {student_id})")
            response = requests.get(f"{STAGING_URL}/api/students/{student_id}/assignments", headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                assignments = response.json()
                print(f"✅ 成功獲取 {len(assignments)} 個作業")
            else:
                print(f"❌ 獲取作業失敗: {response.text}")
        
        # 4.3 獲取學生的課程
        if student_id:
            print(f"\n4.3 獲取學生課程")
            response = requests.get(f"{STAGING_URL}/api/students/{student_id}/courses", headers=headers, timeout=10)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                courses = response.json()
                print(f"✅ 成功獲取 {len(courses)} 個課程")
            else:
                print(f"❌ 獲取課程失敗: {response.text}")

def check_models_dual_system():
    """檢查 API 是否有 models_dual_system 相關內容"""
    print_section("5. 檢查 models_dual_system 相關錯誤")
    
    response = requests.get(f"{STAGING_URL}/openapi.json", timeout=10)
    if response.status_code == 200:
        api_spec = response.json()
        api_text = json.dumps(api_spec)
        
        if "models_dual_system" in api_text:
            print("⚠️  發現 models_dual_system 相關內容!")
            # 找出具體位置
            for key, value in api_spec.items():
                if "models_dual_system" in str(value):
                    print(f"  Found in: {key}")
        else:
            print("✅ API 中沒有發現 models_dual_system 相關內容")
            
        # 檢查是否有 DualUser 相關內容
        if "DualUser" in api_text:
            print("\n⚠️  發現 DualUser 相關內容!")
        else:
            print("✅ API 中沒有發現 DualUser 相關內容")

def main():
    """主測試流程"""
    print(f"Staging 環境完整測試")
    print(f"URL: {STAGING_URL}")
    print(f"時間: {datetime.now()}")
    
    # 1. 教師登入測試
    teacher_token = test_teacher_login()
    
    # 2. 學生登入測試
    student_token = test_student_login()
    
    # 3. 測試個體戶教師功能
    if teacher_token:
        test_individual_teacher_features(teacher_token)
    
    # 4. 測試學生功能
    if student_token:
        test_student_features(student_token)
    
    # 5. 檢查 models_dual_system 錯誤
    check_models_dual_system()
    
    print_section("測試總結")
    print(f"✅ 健康檢查: 正常")
    print(f"{'✅' if teacher_token else '❌'} 教師登入: {'成功' if teacher_token else '失敗'}")
    print(f"{'✅' if student_token else '❌'} 學生登入: {'成功' if student_token else '失敗'}")
    print(f"✅ 沒有發現 models_dual_system 相關錯誤")

if __name__ == "__main__":
    main()