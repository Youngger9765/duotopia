#!/usr/bin/env python3
"""
學生密碼修改功能測試
"""
import requests
import json
import pytest

API_BASE_URL = "http://localhost:8000"

class TestStudentPasswordChange:
    """學生密碼修改功能測試類"""
    
    def setup_method(self):
        """每個測試方法執行前的設定"""
        self.teacher_email = "teacher@individual.com"
        self.api_base = API_BASE_URL
    
    def test_student_password_change_flow(self):
        """測試完整的學生密碼修改流程"""
        print("=== 學生密碼修改功能測試 ===")
        
        # 1. 搜尋老師
        response = requests.get(f"{self.api_base}/api/student-login/teachers/search", 
                              params={"email": self.teacher_email})
        assert response.status_code == 200, f"搜尋老師失敗: {response.text}"
        
        teacher = response.json()
        teacher_id = teacher["id"]
        print(f"✅ 找到老師: {teacher['full_name']} ({teacher['email']})")
        
        # 2. 獲取老師的教室
        response = requests.get(f"{self.api_base}/api/student-login/teachers/{teacher_id}/classrooms")
        assert response.status_code == 200, f"獲取教室失敗: {response.text}"
        
        classrooms = response.json()
        assert len(classrooms) > 0, "沒有找到教室"
        
        classroom_id = classrooms[0]["id"]
        print(f"✅ 找到教室: {classrooms[0]['name']}")
        
        # 3. 獲取學生列表
        response = requests.get(f"{self.api_base}/api/student-login/classrooms/{classroom_id}/students")
        assert response.status_code == 200, f"獲取學生失敗: {response.text}"
        
        students = response.json()
        assert len(students) > 0, "沒有找到學生"
        
        student = students[0]
        student_id = student["id"]
        print(f"✅ 找到學生: {student['full_name']} (生日: {student['birth_date']})")
        
        # 4. 測試密碼驗證（使用預設密碼）
        default_password = student["birth_date"].replace('-', '')
        response = requests.post(f"{self.api_base}/api/student-login/verify-password", 
                               json={
                                   "student_id": student_id,
                                   "password": default_password
                               })
        assert response.status_code == 200, f"密碼驗證失敗: {response.text}"
        
        login_data = response.json()
        assert login_data['student']['is_default_password'] == True, "學生應該使用預設密碼"
        print(f"✅ 密碼驗證成功，學生使用預設密碼")
        
        # 5. 測試密碼修改
        new_password = "newpass123"
        response = requests.post(f"{self.api_base}/api/student-login/change-password", 
                               json={
                                   "student_id": student_id,
                                   "current_password": default_password,
                                   "new_password": new_password
                               })
        assert response.status_code == 200, f"密碼修改失敗: {response.text}"
        
        change_result = response.json()
        assert change_result['success'] == True, "密碼修改應該成功"
        print(f"✅ 密碼修改成功")
        
        # 6. 測試新密碼登入
        response = requests.post(f"{self.api_base}/api/student-login/verify-password", 
                               json={
                                   "student_id": student_id,
                                   "password": new_password
                               })
        assert response.status_code == 200, f"新密碼登入失敗: {response.text}"
        
        login_data = response.json()
        assert login_data['student']['is_default_password'] == False, "學生應該不再使用預設密碼"
        print(f"✅ 新密碼登入成功")
        
        # 7. 測試舊密碼不再有效
        response = requests.post(f"{self.api_base}/api/student-login/verify-password", 
                               json={
                                   "student_id": student_id,
                                   "password": default_password
                               })
        assert response.status_code == 401, "舊密碼應該不再有效"
        print(f"✅ 舊密碼已失效")
        
        print("🎉 所有測試通過！學生密碼修改功能正常運作")
    
    def test_password_validation(self):
        """測試密碼驗證規則"""
        # 獲取測試學生
        teacher_response = requests.get(f"{self.api_base}/api/student-login/teachers/search", 
                                      params={"email": self.teacher_email})
        teacher = teacher_response.json()
        
        classrooms_response = requests.get(f"{self.api_base}/api/student-login/teachers/{teacher['id']}/classrooms")
        classrooms = classrooms_response.json()
        
        students_response = requests.get(f"{self.api_base}/api/student-login/classrooms/{classrooms[0]['id']}/students")
        students = students_response.json()
        
        student = students[0]
        default_password = student["birth_date"].replace('-', '')
        
        # 測試短密碼
        response = requests.post(f"{self.api_base}/api/student-login/change-password", 
                               json={
                                   "student_id": student["id"],
                                   "current_password": default_password,
                                   "new_password": "123"  # 太短
                               })
        assert response.status_code == 400, "短密碼應該被拒絕"
        
        # 測試錯誤的當前密碼
        response = requests.post(f"{self.api_base}/api/student-login/change-password", 
                               json={
                                   "student_id": student["id"],
                                   "current_password": "wrongpass",
                                   "new_password": "newpass123"
                               })
        assert response.status_code == 401, "錯誤的當前密碼應該被拒絕"
        
        print("✅ 密碼驗證規則測試通過")

def run_manual_test():
    """手動執行測試的函數"""
    test_class = TestStudentPasswordChange()
    test_class.setup_method()
    
    try:
        test_class.test_student_password_change_flow()
        test_class.test_password_validation()
        print("\n🎉 所有測試都通過了！")
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        raise

if __name__ == "__main__":
    run_manual_test()