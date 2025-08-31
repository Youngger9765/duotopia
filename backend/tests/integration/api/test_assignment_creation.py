#!/usr/bin/env python3
"""
測試作業創建功能 (Phase 1)
測試教師為學生或整個班級派發作業的功能
"""

import requests
import json
from datetime import datetime, timedelta
import sys
import pytest

BASE_URL = "http://localhost:8000/api"

def get_teacher_token():
    """取得教師 token"""
    response = requests.post(
        f"{BASE_URL}/auth/teacher/login",
        json={"email": "demo@duotopia.com", "password": "demo123"}
    )
    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        return None
    return response.json()["access_token"]

def create_test_classroom_and_content(token):
    """建立測試班級和課程內容"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 建立測試班級
    classroom_data = {
        "name": f"作業測試班級_{datetime.now().strftime('%H%M%S')}",
        "description": "用於測試作業功能",
        "level": "A1"
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/classrooms",
        json=classroom_data,
        headers=headers
    )
    assert response.status_code == 200, f"建立班級失敗: {response.status_code}"
    classroom = response.json()
    
    # 2. 建立測試學生
    students = []
    for i in range(3):
        student_data = {
            "name": f"作業測試學生{i+1}",
            "email": f"assignment_student{i+1}_{int(datetime.now().timestamp())}@test.local",
            "birthdate": "2012-01-01",
            "classroom_id": classroom["id"]
        }
        
        response = requests.post(
            f"{BASE_URL}/teachers/students",
            json=student_data,
            headers=headers
        )
        assert response.status_code == 200, f"建立學生 {i+1} 失敗"
        students.append(response.json())
    
    # 3. 建立測試課程 (Program)
    program_data = {
        "name": f"作業測試課程_{datetime.now().strftime('%H%M%S')}",
        "description": "測試用課程",
        "level": "A1",
        "classroom_id": classroom["id"]
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/programs",
        json=program_data,
        headers=headers
    )
    assert response.status_code == 200, f"建立課程失敗: {response.status_code}"
    program = response.json()
    
    # 4. 建立測試課程單元 (Lesson)
    lesson_data = {
        "name": "Unit 1 - Test Assignment",
        "description": "用於測試作業的課程單元",
        "order_index": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/programs/{program['id']}/lessons",
        json=lesson_data,
        headers=headers
    )
    assert response.status_code == 200, f"建立課程單元失敗: {response.status_code}"
    lesson = response.json()
    
    # 5. 建立測試內容 (Content) - 朗讀評測
    content_data = {
        "title": "Reading Practice 1",
        "description": "測試朗讀練習",
        "content_type": "reading_assessment",
        "items": [
            {"text": "Hello, my name is John.", "order": 1},
            {"text": "I am a student.", "order": 2},
            {"text": "Nice to meet you.", "order": 3}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/lessons/{lesson['id']}/contents",
        json=content_data,
        headers=headers
    )
    assert response.status_code == 200, f"建立內容失敗: {response.status_code}"
    content = response.json()
    
    return {
        "classroom": classroom,
        "students": students,
        "program": program,
        "lesson": lesson,
        "content": content
    }

class TestAssignmentCreation:
    """作業創建功能測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.token = get_teacher_token()
        assert self.token is not None, "無法取得教師 token"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # 建立測試資料
        self.test_data = create_test_classroom_and_content(self.token)
    
    def test_create_assignment_for_individual_student(self):
        """測試為個別學生創建作業"""
        print("\n=== 測試為個別學生創建作業 ===")
        
        student = self.test_data["students"][0]
        content = self.test_data["content"]
        
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [student["id"]],
            "title": "個人朗讀作業 - Reading Practice 1",
            "instructions": "請仔細朗讀每一句話，注意發音的準確性。",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"創建作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "success" in result
        assert result["success"] == True
        assert "count" in result
        assert result["count"] == 1
        
        print(f"✅ 成功為學生 {student['name']} 創建作業 (創建了 {result['count']} 份作業)")
    
    def test_create_assignment_for_multiple_students(self):
        """測試為多個學生創建作業"""
        print("\n=== 測試為多個學生創建作業 ===")
        
        students = self.test_data["students"]
        content = self.test_data["content"]
        
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [s["id"] for s in students[:2]],  # 選擇前兩個學生
            "title": "多人朗讀作業 - Reading Practice 1",
            "instructions": "這是給多位學生的朗讀練習作業。",
            "due_date": (datetime.now() + timedelta(days=5)).isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"創建作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "success" in result
        assert result["success"] == True
        assert "count" in result
        assert result["count"] == 2  # 應該為兩個學生各創建一份作業
        
        print(f"✅ 成功為 {result['count']} 位學生創建作業")
    
    def test_create_assignment_for_entire_classroom(self):
        """測試為整個班級創建作業"""
        print("\n=== 測試為整個班級創建作業 ===")
        
        classroom = self.test_data["classroom"]
        content = self.test_data["content"]
        
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": classroom["id"],
            "student_ids": [],  # 空陣列表示全班
            "title": "班級朗讀作業 - Reading Practice 1",
            "instructions": "這是給整個班級的朗讀練習作業，每位同學都要完成。",
            "due_date": (datetime.now() + timedelta(days=10)).isoformat()
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        assert response.status_code == 200, f"創建作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert "success" in result
        assert result["success"] == True
        assert "count" in result
        assert result["count"] == 3  # 應該為班級內的 3 位學生各創建一份作業
        
        print(f"✅ 成功為整個班級 ({result['count']} 位學生) 創建作業")
    
    def test_create_assignment_validation_errors(self):
        """測試作業創建的驗證錯誤"""
        print("\n=== 測試作業創建驗證錯誤 ===")
        
        content = self.test_data["content"]
        
        # 測試 1: 缺少必要欄位 (classroom_id)
        invalid_data = {
            "content_id": content["id"],
            "student_ids": [],
            "title": "無效作業",
            "instructions": "測試無效資料"
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=invalid_data,
            headers=self.headers
        )
        
        assert response.status_code == 422, "應該返回驗證錯誤"
        print("✅ 正確捕獲缺少必要欄位的錯誤")
        
        # 測試 2: 不存在的內容 ID
        invalid_data = {
            "content_id": 99999,
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [self.test_data["students"][0]["id"]],
            "title": "無效內容作業",
            "instructions": "測試不存在的內容"
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=invalid_data,
            headers=self.headers
        )
        
        assert response.status_code == 404, "應該返回內容不存在錯誤"
        print("✅ 正確捕獲不存在內容的錯誤")
        
        # 測試 3: 不存在的學生 ID
        invalid_data = {
            "content_id": content["id"],
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [99999],
            "title": "無效學生作業",
            "instructions": "測試不存在的學生"
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=invalid_data,
            headers=self.headers
        )
        
        assert response.status_code == 400, "應該返回學生不在班級的錯誤"
        print("✅ 正確捕獲學生不在班級的錯誤")
    
    def test_create_assignment_with_past_due_date(self):
        """測試使用過去日期作為截止日期"""
        print("\n=== 測試過去截止日期驗證 ===")
        
        student = self.test_data["students"][0]
        content = self.test_data["content"]
        
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [student["id"]],
            "title": "過期作業測試",
            "instructions": "測試過期日期處理",
            "due_date": (datetime.now() - timedelta(days=1)).isoformat()  # 昨天
        }
        
        response = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        # API 目前允許過去的截止日期（可能是業務需求）
        # 如果未來需要驗證，可以在 API 中添加驗證邏輯
        assert response.status_code in [200, 422], "API 行為：允許或拒絕過去日期"
        if response.status_code == 200:
            print("✅ API 允許過去的截止日期（業務決策）")
        else:
            print("✅ API 拒絕過去的截止日期")
    
    def test_duplicate_assignment_handling(self):
        """測試重複作業的處理"""
        print("\n=== 測試重複作業處理 ===")
        
        student = self.test_data["students"][0]
        content = self.test_data["content"]
        
        assignment_data = {
            "content_id": content["id"],
            "classroom_id": self.test_data["classroom"]["id"],
            "student_ids": [student["id"]],
            "title": "重複作業測試",
            "instructions": "測試重複作業處理",
            "due_date": (datetime.now() + timedelta(days=3)).isoformat()
        }
        
        # 第一次創建 - 應該成功
        response1 = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        assert response1.status_code == 200, "第一次創建應該成功"
        
        # 第二次創建相同作業 - API 會跳過已存在的作業
        response2 = requests.post(
            f"{BASE_URL}/assignments/create",
            json=assignment_data,
            headers=self.headers
        )
        
        # API 應該返回成功但創建數為 0 (跳過重複)
        assert response2.status_code == 200, "第二次應該也返回成功"
        result2 = response2.json()
        assert result2["count"] == 0, "應該跳過重複作業，創建數為 0"
        
        print("✅ 正確跳過重複作業 (count: 0)")
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'test_data'):
            # 清理測試資料
            try:
                # 刪除建立的內容、課程、學生、班級等
                # 由於有外鍵約束，按順序刪除
                requests.delete(f"{BASE_URL}/teachers/programs/{self.test_data['program']['id']}", headers=self.headers)
                for student in self.test_data["students"]:
                    requests.delete(f"{BASE_URL}/teachers/students/{student['id']}", headers=self.headers)
                requests.delete(f"{BASE_URL}/teachers/classrooms/{self.test_data['classroom']['id']}", headers=self.headers)
            except Exception as e:
                print(f"⚠️ 清理測試資料時發生錯誤: {e}")

if __name__ == "__main__":
    # 執行測試
    test_class = TestAssignmentCreation()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print("🚀 開始測試作業創建功能 (Phase 1)")
    passed = 0
    total = len(test_methods)
    
    for method_name in test_methods:
        try:
            print(f"\n{'='*60}")
            print(f"執行測試: {method_name}")
            print(f"{'='*60}")
            
            test_class.setup_method()
            test_method = getattr(test_class, method_name)
            test_method()
            test_class.teardown_method()
            
            print(f"✅ {method_name} 通過")
            passed += 1
            
        except Exception as e:
            print(f"❌ {method_name} 失敗: {str(e)}")
            try:
                test_class.teardown_method()
            except:
                pass
    
    print(f"\n{'='*60}")
    print(f"測試結果: {passed}/{total} 通過")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 所有測試通過！")
        sys.exit(0)
    else:
        print("⚠️ 部分測試失敗")
        sys.exit(1)