#!/usr/bin/env python3
"""測試個體戶教室詳細功能"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 登入獲取token
def get_token():
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data={
            "username": "teacher@individual.com",
            "password": "test123"
        }
    )
    return response.json()["access_token"]

def test_classroom_detail():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 獲取教室列表
    print("=== 1. 獲取教室列表 ===")
    response = requests.get(f"{BASE_URL}/api/individual/classrooms", headers=headers)
    classrooms = response.json()
    print(f"找到 {len(classrooms)} 個教室")
    
    if not classrooms:
        print("沒有教室")
        return
    
    # 使用第一個教室
    classroom = classrooms[0]
    classroom_id = classroom["id"]
    print(f"\n選擇教室: {classroom['name']} (ID: {classroom_id})")
    
    # 2. 獲取教室詳情
    print("\n=== 2. 獲取教室詳情 ===")
    response = requests.get(f"{BASE_URL}/api/individual/classrooms/{classroom_id}", headers=headers)
    if response.status_code == 200:
        details = response.json()
        print(f"教室名稱: {details['name']}")
        print(f"學生數: {details['student_count']}/{details['max_students']}")
        print(f"學生列表: {len(details['students'])} 人")
    else:
        print(f"錯誤: {response.status_code} - {response.text}")
    
    # 3. 獲取教室學生
    print("\n=== 3. 獲取教室學生 ===")
    response = requests.get(f"{BASE_URL}/api/individual/classrooms/{classroom_id}/students", headers=headers)
    if response.status_code == 200:
        students = response.json()
        print(f"找到 {len(students)} 個學生")
        for student in students[:3]:
            print(f"  - {student['full_name']} ({student['payment_status']})")
    else:
        print(f"錯誤: {response.status_code} - {response.text}")
    
    # 4. 獲取教室課程
    print("\n=== 4. 獲取教室課程 ===")
    response = requests.get(f"{BASE_URL}/api/individual/classrooms/{classroom_id}/courses", headers=headers)
    if response.status_code == 200:
        courses = response.json()
        print(f"找到 {len(courses)} 個課程")
        for course in courses:
            print(f"  - {course['title']}")
            if course.get('copied_from_title'):
                print(f"    (複製自: {course['copied_from_title']})")
    else:
        print(f"錯誤: {response.status_code} - {response.text}")
    
    # 5. 獲取公版課程
    print("\n=== 5. 獲取公版課程 ===")
    response = requests.get(f"{BASE_URL}/api/individual/courses/public", headers=headers)
    if response.status_code == 200:
        public_courses = response.json()
        print(f"找到 {len(public_courses)} 個公版課程")
        for course in public_courses[:3]:
            print(f"  - {course['title']} (${course['pricing_per_lesson']}/堂)")
    else:
        print(f"錯誤: {response.status_code} - {response.text}")
    
    # 6. 測試複製課程
    print("\n=== 6. 測試複製課程 ===")
    if public_courses:
        source_course = public_courses[0]
        print(f"複製課程: {source_course['title']}")
        
        response = requests.post(
            f"{BASE_URL}/api/individual/classrooms/{classroom_id}/courses/copy",
            headers=headers,
            json={"source_course_id": source_course['id']}
        )
        
        if response.status_code == 200:
            new_course = response.json()
            print(f"成功複製! 新課程: {new_course['title']}")
        else:
            print(f"錯誤: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_classroom_detail()