#!/usr/bin/env python3
"""
調試學生密碼修改問題
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def debug_password_change():
    print("=== 調試學生密碼修改 ===\n")
    
    # 1. 學生登入流程
    print("1. 搜尋老師...")
    response = requests.get(f"{API_BASE_URL}/api/student-login/teachers/search", 
                          params={"email": "teacher@individual.com"})
    teacher = response.json()
    print(f"找到老師: {teacher}")
    
    # 2. 獲取教室
    print("\n2. 獲取教室...")
    response = requests.get(f"{API_BASE_URL}/api/student-login/teachers/{teacher['id']}/classrooms")
    classrooms = response.json()
    print(f"找到 {len(classrooms)} 個教室")
    
    # 3. 獲取學生
    print("\n3. 獲取學生...")
    classroom_id = classrooms[0]["id"]
    response = requests.get(f"{API_BASE_URL}/api/student-login/classrooms/{classroom_id}/students")
    students = response.json()
    student = students[0]
    print(f"找到學生: {student}")
    
    # 4. 學生登入
    print("\n4. 學生登入...")
    default_password = student["birth_date"].replace('-', '')
    response = requests.post(f"{API_BASE_URL}/api/student-login/verify-password", 
                           json={
                               "student_id": student["id"],
                               "password": default_password
                           })
    print(f"登入狀態碼: {response.status_code}")
    if response.status_code == 200:
        login_data = response.json()
        token = login_data["access_token"]
        print(f"登入成功，獲得 token")
        print(f"學生資訊: {login_data['student']}")
    else:
        print(f"登入失敗: {response.text}")
        return
    
    # 5. 嘗試修改密碼（帶 token）
    print("\n5. 嘗試修改密碼（帶 token）...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE_URL}/api/student-login/change-password",
                           headers=headers,
                           json={
                               "student_id": student["id"],
                               "current_password": default_password,
                               "new_password": "test1234"
                           })
    print(f"修改密碼狀態碼: {response.status_code}")
    print(f"回應: {response.text}")
    
    # 6. 嘗試修改密碼（不帶 token）
    print("\n6. 嘗試修改密碼（不帶 token）...")
    response = requests.post(f"{API_BASE_URL}/api/student-login/change-password",
                           json={
                               "student_id": student["id"],
                               "current_password": default_password,
                               "new_password": "test1234"
                           })
    print(f"修改密碼狀態碼: {response.status_code}")
    print(f"回應: {response.text}")

if __name__ == "__main__":
    debug_password_change()