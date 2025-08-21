#!/usr/bin/env python3
"""
學生密碼修改功能測試腳本
"""
import requests
import json

API_BASE_URL = "http://localhost:8000"

def test_student_password_change():
    print("=== 學生密碼修改功能測試 ===")
    
    # 1. 搜尋老師
    print("1. 搜尋老師...")
    response = requests.get(f"{API_BASE_URL}/api/student-login/teachers/search", 
                          params={"email": "teacher@individual.com"})
    if response.status_code != 200:
        print(f"❌ 搜尋老師失敗: {response.text}")
        return False
        
    teacher = response.json()
    teacher_id = teacher["id"]
    print(f"✅ 找到老師: {teacher['full_name']} ({teacher['email']})")
    
    # 2. 獲取老師的教室
    print("2. 獲取教室列表...")
    response = requests.get(f"{API_BASE_URL}/api/student-login/teachers/{teacher_id}/classrooms")
    if response.status_code != 200:
        print(f"❌ 獲取教室失敗: {response.text}")
        return False
        
    classrooms = response.json()
    if not classrooms:
        print("❌ 沒有找到教室")
        return False
        
    classroom_id = classrooms[0]["id"]
    print(f"✅ 找到教室: {classrooms[0]['name']}")
    
    # 3. 獲取學生列表
    print("3. 獲取學生列表...")
    response = requests.get(f"{API_BASE_URL}/api/student-login/classrooms/{classroom_id}/students")
    if response.status_code != 200:
        print(f"❌ 獲取學生失敗: {response.text}")
        return False
        
    students = response.json()
    if not students:
        print("❌ 沒有找到學生")
        return False
        
    student = students[0]
    student_id = student["id"]
    print(f"✅ 找到學生: {student['full_name']} (生日: {student['birth_date']})")
    
    # 4. 測試密碼驗證（使用預設密碼）
    print("4. 測試密碼驗證...")
    default_password = student["birth_date"].replace('-', '')
    response = requests.post(f"{API_BASE_URL}/api/student-login/verify-password", 
                           json={
                               "student_id": student_id,
                               "password": default_password
                           })
    if response.status_code != 200:
        print(f"❌ 密碼驗證失敗: {response.text}")
        return False
        
    login_data = response.json()
    print(f"✅ 密碼驗證成功，學生使用預設密碼: {login_data['student']['is_default_password']}")
    
    # 5. 測試密碼修改
    print("5. 測試密碼修改...")
    new_password = "newpass123"
    response = requests.post(f"{API_BASE_URL}/api/student-login/change-password", 
                           json={
                               "student_id": student_id,
                               "current_password": default_password,
                               "new_password": new_password
                           })
    if response.status_code != 200:
        print(f"❌ 密碼修改失敗: {response.text}")
        return False
        
    print(f"✅ 密碼修改成功: {response.json()['message']}")
    
    # 6. 測試新密碼登入
    print("6. 測試新密碼登入...")
    response = requests.post(f"{API_BASE_URL}/api/student-login/verify-password", 
                           json={
                               "student_id": student_id,
                               "password": new_password
                           })
    if response.status_code != 200:
        print(f"❌ 新密碼登入失敗: {response.text}")
        return False
        
    login_data = response.json()
    print(f"✅ 新密碼登入成功，不再使用預設密碼: {not login_data['student']['is_default_password']}")
    
    print("\n🎉 所有測試通過！學生密碼修改功能正常運作")
    return True

if __name__ == "__main__":
    try:
        test_student_password_change()
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")