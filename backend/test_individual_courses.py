#!/usr/bin/env python3
"""
測試個體戶教師的課程相關功能
"""

import requests
import json

STAGING_URL = "https://duotopia-backend-staging-qchnzlfpda-de.a.run.app"

def login_teacher():
    """登入教師帳號"""
    login_data = {
        "username": "teacher@individual.com",
        "password": "password123"
    }
    
    response = requests.post(
        f"{STAGING_URL}/api/auth/login",
        data=login_data,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print("✅ 教師登入成功")
        print(f"User ID: {data.get('user_id')}")
        print(f"Is Individual Teacher: {data.get('is_individual_teacher')}")
        print(f"Current Role Context: {data.get('current_role_context')}")
        return data["access_token"]
    else:
        print(f"❌ 登入失敗: {response.text}")
        return None

def test_individual_courses(token):
    """測試個體戶課程端點"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("\n測試個體戶課程端點:")
    
    # 1. 獲取課程列表
    print("\n1. GET /api/individual/courses")
    response = requests.get(
        f"{STAGING_URL}/api/individual/courses",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        courses = response.json()
        print(f"✅ 成功獲取 {len(courses)} 個課程")
        
        for i, course in enumerate(courses[:3]):
            print(f"\nCourse {i+1}:")
            print(f"  ID: {course.get('id')}")
            print(f"  Title: {course.get('title')}")
            print(f"  Description: {course.get('description')}")
            print(f"  Created At: {course.get('created_at')}")
            
            # 獲取該課程的 lessons
            if course.get('id'):
                test_course_lessons(token, course['id'])
    else:
        print(f"❌ 獲取課程失敗: {response.text}")
    
    # 2. 獲取公開課程
    print("\n2. GET /api/individual/courses/public")
    response = requests.get(
        f"{STAGING_URL}/api/individual/courses/public",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        public_courses = response.json()
        print(f"✅ 成功獲取 {len(public_courses)} 個公開課程")
    else:
        print(f"❌ 獲取公開課程失敗: {response.text}")

def test_course_lessons(token, course_id):
    """測試課程的 lessons"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print(f"\n  獲取課程 {course_id} 的 lessons:")
    response = requests.get(
        f"{STAGING_URL}/api/individual/courses/{course_id}/lessons",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        lessons = response.json()
        print(f"  ✅ 該課程有 {len(lessons)} 個 lessons")
        for j, lesson in enumerate(lessons[:2]):
            print(f"    Lesson {j+1}: {lesson.get('title', {}).get('zh-TW', 'No title')}")
    else:
        print(f"  ❌ 獲取 lessons 失敗: {response.status_code}")

def test_individual_classrooms(token):
    """測試個體戶教室端點"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("\n\n測試個體戶教室端點:")
    
    # 獲取教室列表
    print("\nGET /api/individual/classrooms")
    response = requests.get(
        f"{STAGING_URL}/api/individual/classrooms",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        classrooms = response.json()
        print(f"✅ 成功獲取 {len(classrooms)} 個教室")
        
        for i, classroom in enumerate(classrooms[:3]):
            print(f"\nClassroom {i+1}:")
            print(f"  ID: {classroom.get('id')}")
            print(f"  Name: {classroom.get('name')}")
            print(f"  Grade: {classroom.get('grade')}")
            print(f"  Student Count: {classroom.get('student_count', 0)}")
    else:
        print(f"❌ 獲取教室失敗: {response.text}")

def test_individual_students(token):
    """測試個體戶學生端點"""
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    print("\n\n測試個體戶學生端點:")
    
    # 獲取學生列表
    print("\nGET /api/individual/students")
    response = requests.get(
        f"{STAGING_URL}/api/individual/students",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        students = response.json()
        print(f"✅ 成功獲取 {len(students)} 個學生")
        
        for i, student in enumerate(students[:3]):
            print(f"\nStudent {i+1}:")
            print(f"  ID: {student.get('id')}")
            print(f"  Name: {student.get('name')}")
            print(f"  Email: {student.get('email')}")
            print(f"  Grade: {student.get('grade')}")
    else:
        print(f"❌ 獲取學生失敗: {response.text}")

def main():
    """主測試流程"""
    print("測試 Staging 環境的個體戶教師功能")
    print("="*60)
    
    # 登入
    token = login_teacher()
    
    if token:
        # 測試各項功能
        test_individual_courses(token)
        test_individual_classrooms(token)
        test_individual_students(token)
    else:
        print("\n無法繼續測試，因為登入失敗")

if __name__ == "__main__":
    main()