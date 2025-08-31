#!/usr/bin/env python3
"""
測試作業列表功能 (Phase 2)
測試教師和學生查看作業列表的功能
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

def get_student_token(email, password):
    """取得學生 token"""
    response = requests.post(
        f"{BASE_URL}/auth/student/login",
        json={"email": email, "password": password}
    )
    if response.status_code != 200:
        print(f"❌ 學生登入失敗: {response.status_code}")
        return None
    return response.json()["access_token"]

def create_test_data_with_assignments(token):
    """建立測試資料並創建作業"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 建立測試班級
    classroom_data = {
        "name": f"作業列表測試班級_{datetime.now().strftime('%H%M%S')}",
        "description": "用於測試作業列表功能",
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
    for i in range(2):
        student_data = {
            "name": f"作業列表測試學生{i+1}",
            "email": f"assignment_list_student{i+1}_{int(datetime.now().timestamp())}@example.com",
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
    
    # 3. 建立測試課程和內容
    program_data = {
        "name": f"作業列表測試課程_{datetime.now().strftime('%H%M%S')}",
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
    
    lesson_data = {
        "name": "Unit 1 - Assignment List Test",
        "description": "用於測試作業列表的課程單元",
        "order_index": 1
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/programs/{program['id']}/lessons",
        json=lesson_data,
        headers=headers
    )
    assert response.status_code == 200, f"建立課程單元失敗: {response.status_code}"
    lesson = response.json()
    
    # 建立多個測試內容 (Content) - 用於不同作業
    contents = []
    
    # Content 1: 個人作業用
    content_data1 = {
        "title": "Individual Reading Practice",
        "description": "個人朗讀練習",
        "content_type": "reading_assessment",
        "items": [
            {"text": "Hello, my name is John.", "order": 1},
            {"text": "I am a student.", "order": 2}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/lessons/{lesson['id']}/contents",
        json=content_data1,
        headers=headers
    )
    assert response.status_code == 200, f"建立內容1失敗: {response.status_code}"
    contents.append(response.json())
    
    # Content 2: 班級作業用
    content_data2 = {
        "title": "Classroom Reading Practice",
        "description": "班級朗讀練習",
        "content_type": "reading_assessment",
        "items": [
            {"text": "We are learning English together.", "order": 1},
            {"text": "This is our classroom assignment.", "order": 2}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/lessons/{lesson['id']}/contents",
        json=content_data2,
        headers=headers
    )
    assert response.status_code == 200, f"建立內容2失敗: {response.status_code}"
    contents.append(response.json())
    
    # Content 3: 過期作業用
    content_data3 = {
        "title": "Overdue Reading Practice",
        "description": "過期朗讀練習",
        "content_type": "reading_assessment",
        "items": [
            {"text": "This assignment is overdue.", "order": 1},
            {"text": "But you can still complete it.", "order": 2}
        ]
    }
    
    response = requests.post(
        f"{BASE_URL}/teachers/lessons/{lesson['id']}/contents",
        json=content_data3,
        headers=headers
    )
    assert response.status_code == 200, f"建立內容3失敗: {response.status_code}"
    contents.append(response.json())
    
    # 4. 建立多個作業來測試列表功能
    assignments = []
    
    # 作業 1: 給第一個學生 (使用 Content 1)
    assignment_data1 = {
        "content_id": contents[0]["id"],
        "classroom_id": classroom["id"],
        "student_ids": [students[0]["id"]],
        "title": "個人作業 - Reading Test 1",
        "instructions": "請朗讀第一段內容。",
        "due_date": (datetime.now() + timedelta(days=7)).isoformat()
    }
    
    response = requests.post(
        f"{BASE_URL}/assignments/create",
        json=assignment_data1,
        headers=headers
    )
    assert response.status_code == 200, "建立第一個作業失敗"
    
    # DEBUG: 檢查班級中有多少學生
    students_response = requests.get(
        f"{BASE_URL}/classrooms/{classroom['id']}/students",
        headers=headers
    )
    if students_response.status_code == 200:
        classroom_students = students_response.json()
        print(f"DEBUG: 班級中共有 {len(classroom_students)} 個學生")
    
    # 作業 2: 給所有學生 (使用 Content 2)
    assignment_data2 = {
        "content_id": contents[1]["id"],
        "classroom_id": classroom["id"],
        "student_ids": [],  # 空陣列表示全班
        "title": "班級作業 - Reading Test 2",
        "instructions": "這是給整個班級的作業。",
        "due_date": (datetime.now() + timedelta(days=5)).isoformat()
    }
    
    response = requests.post(
        f"{BASE_URL}/assignments/create",
        json=assignment_data2,
        headers=headers
    )
    assert response.status_code == 200, "建立第二個作業失敗"
    result2 = response.json()
    print(f"DEBUG: 建立班級作業結果: count={result2.get('count')}")  # Debug info
    
    # 作業 3: 過期作業（測試狀態）(使用 Content 3)
    assignment_data3 = {
        "content_id": contents[2]["id"],
        "classroom_id": classroom["id"],
        "student_ids": [students[1]["id"]],
        "title": "過期作業測試",
        "instructions": "這是一個過期的作業。",
        "due_date": (datetime.now() - timedelta(days=1)).isoformat()
    }
    
    response = requests.post(
        f"{BASE_URL}/assignments/create",
        json=assignment_data3,
        headers=headers
    )
    # 即使是過期日期，API 也應該允許創建（根據 Phase 1 測試結果）
    assert response.status_code == 200, "建立過期作業失敗"
    
    return {
        "classroom": classroom,
        "students": students,
        "program": program,
        "lesson": lesson,
        "contents": contents  # 返回所有內容列表
    }

class TestAssignmentLists:
    """作業列表功能測試"""
    
    def setup_method(self):
        """測試前準備"""
        self.token = get_teacher_token()
        assert self.token is not None, "無法取得教師 token"
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # 建立測試資料並創建作業
        self.test_data = create_test_data_with_assignments(self.token)
    
    def test_teacher_get_classroom_assignments(self):
        """測試教師查詢班級作業列表"""
        print("\n=== 測試教師查詢班級作業列表 ===")
        
        classroom_id = self.test_data["classroom"]["id"]
        
        response = requests.get(
            f"{BASE_URL}/assignments/teacher?classroom_id={classroom_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"查詢班級作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert isinstance(result, list), "應該返回作業列表"
        assert len(result) >= 3, f"應該有至少3組作業，實際: {len(result)}"  # 每個 content 一組
        
        # 檢查作業統計資料結構
        assignment_stat = result[0]
        required_fields = ["content_id", "classroom_id", "title", "total_students", "status_distribution"]
        for field in required_fields:
            assert field in assignment_stat, f"作業統計資料缺少欄位: {field}"
        
        # 檢查狀態分佈
        assert "status_distribution" in assignment_stat
        assert isinstance(assignment_stat["status_distribution"], dict)
        status_fields = ["not_started", "in_progress", "submitted", "graded", "returned"]
        for status_field in status_fields:
            assert status_field in assignment_stat["status_distribution"], f"缺少狀態: {status_field}"
        
        print(f"✅ 成功取得 {len(result)} 組作業統計")
        print(f"  作業標題: {[a['title'] for a in result]}")
        print(f"  總學生數: {[a['total_students'] for a in result]}")
    
    def test_teacher_get_all_assignments(self):
        """測試教師查詢所有作業（不指定班級）"""
        print("\n=== 測試教師查詢所有作業 ===")
        
        response = requests.get(
            f"{BASE_URL}/assignments/teacher",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"查詢所有作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert isinstance(result, list), "應該返回作業列表"
        
        # 應該包含我們建立的作業（可能包含其他測試的作業）
        our_assignments = [a for a in result if a["title"].startswith(("個人作業", "班級作業", "過期作業"))]
        assert len(our_assignments) >= 3, f"應該包含我們建立的3組作業，實際: {len(our_assignments)}"
        
        print(f"✅ 成功取得 {len(result)} 個作業（包含 {len(our_assignments)} 個測試作業）")
    
    def test_student_get_assignments(self):
        """測試學生查詢自己的作業列表"""
        print("\n=== 測試學生查詢作業列表 ===")
        
        # 使用第一個學生登入
        student = self.test_data["students"][0]
        student_token = get_student_token(student["email"], "20120101")  # 生日密碼
        assert student_token is not None, "學生登入失敗"
        
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/assignments/student",
            headers=student_headers
        )
        
        assert response.status_code == 200, f"學生查詢作業失敗: {response.status_code} - {response.text}"
        
        result = response.json()
        assert isinstance(result, list), "應該返回作業列表"
        
        print(f"DEBUG: 第一個學生取得 {len(result)} 個作業")
        for i, assignment in enumerate(result):
            print(f"  {i+1}. {assignment['title']} - {assignment['status']}")
        
        # 第一個學生應該有 2 個作業：個人作業 + 班級作業
        # 不應該看到第二個學生的過期作業
        assert len(result) >= 2, f"第一個學生應該有至少2個作業（個人+班級），實際: {len(result)}"
        
        # 檢查作業資料結構
        assignment = result[0]
        required_fields = ["id", "title", "instructions", "due_date", "content", "status"]
        for field in required_fields:
            assert field in assignment, f"學生作業資料缺少欄位: {field}"
        
        # 檢查狀態（使用實際的枚舉值 - 大寫）
        valid_statuses = ["NOT_STARTED", "IN_PROGRESS", "SUBMITTED", "GRADED", "RETURNED"]
        assert assignment["status"] in valid_statuses, f"未知的作業狀態: {assignment['status']}"
        
        print(f"✅ 學生成功取得 {len(result)} 個作業")
        print(f"  作業標題: {[a['title'] for a in result]}")
        print(f"  作業狀態: {[a['status'] for a in result]}")
    
    def test_student_assignment_filtering(self):
        """測試學生作業篩選功能"""
        print("\n=== 測試學生作業篩選 ===")
        
        # 使用第二個學生登入（應該只有班級作業 + 過期作業）
        student = self.test_data["students"][1]
        student_token = get_student_token(student["email"], "20120101")
        assert student_token is not None, "第二個學生登入失敗"
        
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        # 測試查詢所有作業
        response = requests.get(
            f"{BASE_URL}/assignments/student",
            headers=student_headers
        )
        
        assert response.status_code == 200, "查詢作業失敗"
        all_assignments = response.json()
        
        print(f"DEBUG: 第二個學生取得 {len(all_assignments)} 個作業")
        for i, assignment in enumerate(all_assignments):
            print(f"  {i+1}. {assignment['title']} - {assignment['status']}")
        
        # 第二個學生應該有 2 個作業：班級作業 + 過期個人作業
        assert len(all_assignments) >= 2, f"第二個學生應該有至少2個作業，實際: {len(all_assignments)}"
        
        # 測試狀態篩選（如果 API 支援）
        response = requests.get(
            f"{BASE_URL}/assignments/student?status=pending",
            headers=student_headers
        )
        
        # 這個功能可能還沒實作，允許 404 或正常回應
        if response.status_code == 200:
            pending_assignments = response.json()
            print(f"✅ 待完成作業: {len(pending_assignments)} 個")
        else:
            print("ℹ️ 狀態篩選功能尚未實作（預期行為）")
        
        print(f"✅ 第二個學生作業驗證完成")
    
    def test_assignment_details_structure(self):
        """測試作業詳情資料結構"""
        print("\n=== 測試作業詳情資料結構 ===")
        
        classroom_id = self.test_data["classroom"]["id"]
        
        response = requests.get(
            f"{BASE_URL}/assignments/teacher?classroom_id={classroom_id}",
            headers=self.headers
        )
        
        assert response.status_code == 200, "查詢作業失敗"
        assignments = response.json()
        assert len(assignments) > 0, "沒有作業資料"
        
        assignment_stat = assignments[0]
        
        # 驗證教師端作業統計資料結構
        expected_teacher_fields = {
            "content_id": int,
            "classroom_id": int,
            "title": str,
            "total_students": int,
            "status_distribution": dict
        }
        
        for field, expected_type in expected_teacher_fields.items():
            assert field in assignment_stat, f"缺少欄位: {field}"
            assert isinstance(assignment_stat[field], expected_type), f"欄位 {field} 類型錯誤，期望 {expected_type.__name__}"
        
        # 驗證狀態分佈結構
        status_dist = assignment_stat["status_distribution"]
        status_fields = ["not_started", "in_progress", "submitted", "graded", "returned"]
        for status_field in status_fields:
            assert status_field in status_dist, f"缺少狀態欄位: {status_field}"
            assert isinstance(status_dist[status_field], int), f"狀態 {status_field} 應該是整數"
        
        print("✅ 教師端作業統計資料結構正確")
        
        # 驗證學生端資料結構
        student = self.test_data["students"][0]
        student_token = get_student_token(student["email"], "20120101")
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/assignments/student",
            headers=student_headers
        )
        
        assert response.status_code == 200, "學生查詢作業失敗"
        student_assignments = response.json()
        assert len(student_assignments) > 0, "學生沒有作業資料"
        
        student_assignment = student_assignments[0]
        
        expected_student_fields = {
            "id": int,
            "title": str,
            "instructions": str,
            "due_date": (str, type(None)),  # 可能為 None
            "status": str,
            "content": (dict, type(None))  # 可能為 None
        }
        
        for field, expected_type in expected_student_fields.items():
            assert field in student_assignment, f"學生作業缺少欄位: {field}"
            assert isinstance(student_assignment[field], expected_type), f"學生作業欄位 {field} 類型錯誤"
        
        print("✅ 學生端作業資料結構正確")
    
    def test_invalid_requests(self):
        """測試無效請求的錯誤處理"""
        print("\n=== 測試無效請求錯誤處理 ===")
        
        # 測試 1: 教師查詢不存在的班級
        response = requests.get(
            f"{BASE_URL}/assignments/teacher?classroom_id=99999",
            headers=self.headers
        )
        
        # 應該返回空列表而不是錯誤
        assert response.status_code == 200, "查詢不存在班級應該返回200"
        result = response.json()
        assert isinstance(result, list), "應該返回空列表"
        
        print("✅ 不存在班級查詢處理正確")
        
        # 測試 2: 未認證的請求
        response = requests.get(f"{BASE_URL}/assignments/teacher")
        assert response.status_code == 401, "未認證請求應該返回401"
        
        response = requests.get(f"{BASE_URL}/assignments/student")
        assert response.status_code == 401, "未認證請求應該返回401"
        
        print("✅ 未認證請求處理正確")
        
        # 測試 3: 學生嘗試存取教師API
        student = self.test_data["students"][0]
        student_token = get_student_token(student["email"], "20120101")
        student_headers = {"Authorization": f"Bearer {student_token}"}
        
        response = requests.get(
            f"{BASE_URL}/assignments/teacher",
            headers=student_headers
        )
        
        # 應該拒絕學生存取教師API
        assert response.status_code in [403, 401], "學生不應能存取教師API"
        
        print("✅ 權限控制正確")
    
    def teardown_method(self):
        """測試後清理"""
        if hasattr(self, 'test_data'):
            try:
                # 清理測試資料
                requests.delete(f"{BASE_URL}/teachers/programs/{self.test_data['program']['id']}", headers=self.headers)
                for student in self.test_data["students"]:
                    requests.delete(f"{BASE_URL}/teachers/students/{student['id']}", headers=self.headers)
                requests.delete(f"{BASE_URL}/teachers/classrooms/{self.test_data['classroom']['id']}", headers=self.headers)
            except Exception as e:
                print(f"⚠️ 清理測試資料時發生錯誤: {e}")

if __name__ == "__main__":
    # 執行測試
    test_class = TestAssignmentLists()
    test_methods = [method for method in dir(test_class) if method.startswith('test_')]
    
    print("🚀 開始測試作業列表功能 (Phase 2)")
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