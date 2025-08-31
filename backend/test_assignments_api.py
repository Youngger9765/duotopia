#!/usr/bin/env python3
"""
作業系統 Phase 1 API 測試
測試基礎指派功能的所有 API endpoints
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# API 基礎設定
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# 測試用的教師帳號 (demo 帳號)
TEACHER_EMAIL = "demo@duotopia.com"
TEACHER_PASSWORD = "demo123"

# 測試結果統計
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


class TestAssignmentsAPI:
    """作業指派 API 測試類別"""
    
    def __init__(self):
        self.session = requests.Session()
        self.teacher_token = None
        self.classroom_id = None
        self.content_id = None
        self.student_ids = []
    
    def setup(self):
        """測試前置作業：登入並取得必要資料"""
        print("🔧 設定測試環境...")
        
        # 1. 教師登入
        self.teacher_token = self.teacher_login()
        if not self.teacher_token:
            raise Exception("教師登入失敗")
        
        # 2. 取得第一個班級
        classrooms = self.get_teacher_classrooms()
        if classrooms:
            self.classroom_id = classrooms[0]["id"]
            print(f"✅ 使用班級 ID: {self.classroom_id}")
        
        # 3. 取得班級學生
        if self.classroom_id:
            students = self.get_classroom_students(self.classroom_id)
            self.student_ids = [s["id"] for s in students[:3]]  # 取前3個學生測試
            print(f"✅ 測試學生 IDs: {self.student_ids}")
        
        # 4. 取得可用的 Content
        contents = self.get_available_contents()
        if contents:
            self.content_id = contents[0]["id"]
            print(f"✅ 使用 Content ID: {self.content_id}")
    
    def teacher_login(self) -> Optional[str]:
        """教師登入並取得 token"""
        print("📝 測試教師登入...")
        
        response = self.session.post(
            f"{API_URL}/auth/teacher/login",
            json={
                "email": TEACHER_EMAIL,
                "password": TEACHER_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            print(f"✅ 教師登入成功")
            return token
        else:
            print(f"❌ 教師登入失敗: {response.status_code}")
            print(f"   回應: {response.text}")
            return None
    
    def get_teacher_classrooms(self) -> List[Dict]:
        """取得教師的班級列表"""
        response = self.session.get(f"{API_URL}/teachers/classrooms")
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_classroom_students(self, classroom_id: int) -> List[Dict]:
        """取得班級學生列表"""
        print(f"📝 測試取得班級學生 API...")
        
        response = self.session.get(f"{API_URL}/classrooms/{classroom_id}/students")
        
        if response.status_code == 200:
            students = response.json()
            print(f"✅ 成功取得 {len(students)} 位學生")
            test_results["passed"] += 1
            return students
        else:
            error = f"取得班級學生失敗: {response.status_code}"
            print(f"❌ {error}")
            test_results["failed"] += 1
            test_results["errors"].append(error)
            return []
    
    def get_available_contents(self) -> List[Dict]:
        """取得可用的 Content 列表"""
        print(f"📝 測試取得可用 Content API...")
        
        params = {}
        if self.classroom_id:
            params["classroom_id"] = self.classroom_id
        
        response = self.session.get(f"{API_URL}/contents", params=params)
        
        if response.status_code == 200:
            contents = response.json()
            print(f"✅ 成功取得 {len(contents)} 個 Content")
            test_results["passed"] += 1
            return contents
        else:
            error = f"取得 Content 失敗: {response.status_code}"
            print(f"❌ {error}")
            test_results["failed"] += 1
            test_results["errors"].append(error)
            return []
    
    def test_create_assignment(self):
        """測試建立作業"""
        print("\n📝 測試建立作業 API...")
        
        if not all([self.content_id, self.classroom_id]):
            print("⚠️ 缺少必要的測試資料，跳過此測試")
            return
        
        # 測試案例 1: 指派給全班
        print("  1️⃣ 測試指派給全班...")
        due_date = (datetime.now() + timedelta(days=7)).isoformat() + "Z"
        
        response = self.session.post(
            f"{API_URL}/assignments/create",
            json={
                "content_id": self.content_id,
                "classroom_id": self.classroom_id,
                "student_ids": [],  # 空陣列表示全班
                "title": "朗讀練習 - 測試作業（全班）",
                "instructions": "請完成朗讀練習，注意發音準確度",
                "due_date": due_date
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 成功建立全班作業，作業數量: {data.get('count', 0)}")
            test_results["passed"] += 1
        else:
            error = f"建立全班作業失敗: {response.status_code} - {response.text}"
            print(f"  ❌ {error}")
            test_results["failed"] += 1
            test_results["errors"].append(error)
        
        # 測試案例 2: 指派給特定學生
        if self.student_ids:
            print("  2️⃣ 測試指派給特定學生...")
            
            response = self.session.post(
                f"{API_URL}/assignments/create",
                json={
                    "content_id": self.content_id,
                    "classroom_id": self.classroom_id,
                    "student_ids": self.student_ids[:2],  # 只指派給前2個學生
                    "title": "朗讀練習 - 測試作業（個別）",
                    "instructions": "個別練習作業",
                    "due_date": due_date
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ 成功建立個別作業，作業數量: {data.get('count', 0)}")
                test_results["passed"] += 1
            else:
                error = f"建立個別作業失敗: {response.status_code} - {response.text}"
                print(f"  ❌ {error}")
                test_results["failed"] += 1
                test_results["errors"].append(error)
        
        # 測試案例 3: 缺少必要參數
        print("  3️⃣ 測試缺少必要參數...")
        
        response = self.session.post(
            f"{API_URL}/assignments/create",
            json={
                "content_id": self.content_id,
                # 缺少 classroom_id
                "student_ids": [],
                "title": "測試作業"
            }
        )
        
        if response.status_code == 422:  # 預期的驗證錯誤
            print(f"  ✅ 正確拒絕缺少參數的請求")
            test_results["passed"] += 1
        else:
            error = f"應該拒絕缺少參數的請求，但回傳: {response.status_code}"
            print(f"  ❌ {error}")
            test_results["failed"] += 1
            test_results["errors"].append(error)
    
    def run_all_tests(self):
        """執行所有測試"""
        print("\n" + "="*60)
        print("🚀 開始執行作業系統 Phase 1 API 測試")
        print("="*60)
        
        try:
            # 設定測試環境
            self.setup()
            
            # 執行測試
            print("\n--- 執行 API 測試 ---")
            self.test_create_assignment()
            
        except Exception as e:
            print(f"\n❌ 測試過程發生錯誤: {e}")
            test_results["errors"].append(str(e))
        
        # 顯示測試結果
        self.print_results()
    
    def print_results(self):
        """顯示測試結果摘要"""
        print("\n" + "="*60)
        print("📊 測試結果摘要")
        print("="*60)
        print(f"✅ 通過: {test_results['passed']} 個測試")
        print(f"❌ 失敗: {test_results['failed']} 個測試")
        
        if test_results["errors"]:
            print("\n❌ 錯誤詳情:")
            for i, error in enumerate(test_results["errors"], 1):
                print(f"  {i}. {error}")
        
        # 總結
        total = test_results["passed"] + test_results["failed"]
        if total > 0:
            success_rate = (test_results["passed"] / total) * 100
            print(f"\n📈 成功率: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("🎉 所有測試都通過了！")
            elif success_rate >= 80:
                print("👍 大部分測試通過，但仍有些問題需要修復")
            else:
                print("⚠️ 許多測試失敗，需要檢查 API 實作")


if __name__ == "__main__":
    tester = TestAssignmentsAPI()
    tester.run_all_tests()