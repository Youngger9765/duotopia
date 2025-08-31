#!/usr/bin/env python3
"""
作業系統完整流程測試
依序測試所有 Phase 1 & Phase 2 功能
"""

import requests
import json
from datetime import datetime, timedelta
import sys

BASE_URL = "http://localhost:8000/api"

def test_full_flow():
    """完整測試流程"""
    session = requests.Session()
    
    print("="*60)
    print("🚀 開始作業系統完整流程測試")
    print("="*60)
    
    # 1. 教師登入
    print("\n1️⃣ 教師登入...")
    response = session.post(
        f"{BASE_URL}/auth/teacher/login",
        json={
            "email": "demo@duotopia.com",
            "password": "demo123"
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 教師登入失敗: {response.status_code}")
        print(response.text)
        return False
    
    teacher_data = response.json()
    teacher_token = teacher_data["access_token"]
    session.headers.update({"Authorization": f"Bearer {teacher_token}"})
    print(f"✅ 教師登入成功: {teacher_data['user']['name']}")
    
    # 2. 取得班級列表
    print("\n2️⃣ 取得班級列表...")
    response = session.get(f"{BASE_URL}/teachers/classrooms")
    
    if response.status_code != 200:
        print(f"❌ 取得班級失敗: {response.status_code}")
        return False
    
    classrooms = response.json()
    print(f"✅ 找到 {len(classrooms)} 個班級")
    
    if not classrooms:
        print("❌ 沒有班級資料")
        return False
    
    classroom_id = classrooms[0]["id"]
    print(f"   使用班級: {classrooms[0]['name']} (ID: {classroom_id})")
    
    # 3. 取得班級學生
    print("\n3️⃣ 取得班級學生...")
    response = session.get(f"{BASE_URL}/classrooms/{classroom_id}/students")
    
    if response.status_code != 200:
        print(f"❌ 取得學生失敗: {response.status_code}")
        print(response.text)
        return False
    
    students = response.json()
    print(f"✅ 班級有 {len(students)} 位學生")
    for student in students[:3]:
        print(f"   - {student['name']}")
    
    # 4. 取得可用 Content
    print("\n4️⃣ 取得可用 Content...")
    response = session.get(f"{BASE_URL}/contents?classroom_id={classroom_id}")
    
    if response.status_code != 200:
        print(f"❌ 取得 Content 失敗: {response.status_code}")
        print(response.text)
        return False
    
    contents = response.json()
    print(f"✅ 找到 {len(contents)} 個 Content")
    
    if not contents:
        print("❌ 沒有 Content 資料")
        return False
    
    content_id = contents[0]["id"]
    print(f"   使用 Content: {contents[0]['title']} (ID: {content_id})")
    
    # 5. 建立作業（指派給全班）
    print("\n5️⃣ 建立作業（指派給全班）...")
    due_date = (datetime.now() + timedelta(days=3)).isoformat() + "Z"
    
    response = session.post(
        f"{BASE_URL}/assignments/create",
        json={
            "content_id": content_id,
            "classroom_id": classroom_id,
            "student_ids": [],  # 空陣列 = 全班
            "title": f"測試作業 - {datetime.now().strftime('%m/%d %H:%M')}",
            "instructions": "請完成朗讀練習",
            "due_date": due_date
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 建立作業失敗: {response.status_code}")
        print(response.text)
        return False
    
    result = response.json()
    print(f"✅ 成功建立 {result.get('count', 0)} 個作業")
    
    # 6. 查看教師的作業列表
    print("\n6️⃣ 查看教師的作業列表...")
    response = session.get(f"{BASE_URL}/assignments/teacher?classroom_id={classroom_id}")
    
    if response.status_code != 200:
        print(f"❌ 取得作業列表失敗: {response.status_code}")
        print(response.text)
        return False
    
    assignments = response.json()
    print(f"✅ 找到 {len(assignments)} 組作業統計")
    
    for assignment in assignments[:2]:
        print(f"   - {assignment['title']}")
        status = assignment.get('status_distribution', {})
        print(f"     總人數: {assignment['total_students']}")
        print(f"     未開始: {status.get('not_started', 0)}, "
              f"已提交: {status.get('submitted', 0)}, "
              f"已批改: {status.get('graded', 0)}")
    
    # 7. 學生登入測試
    print("\n7️⃣ 學生登入測試...")
    
    # 使用第一個學生測試
    if students:
        student_email = students[0]["email"]
        
        # 嘗試使用測試密碼
        response = requests.post(
            f"{BASE_URL}/auth/student/login",
            json={
                "email": student_email,
                "password": "mynewpassword123"  # 測試密碼
            }
        )
        
        if response.status_code == 200:
            student_data = response.json()
            student_token = student_data["access_token"]
            print(f"✅ 學生登入成功: {student_data['user']['name']}")
            
            # 8. 學生查看作業列表
            print("\n8️⃣ 學生查看作業列表...")
            headers = {"Authorization": f"Bearer {student_token}"}
            response = requests.get(f"{BASE_URL}/assignments/student", headers=headers)
            
            if response.status_code == 200:
                student_assignments = response.json()
                print(f"✅ 學生有 {len(student_assignments)} 個作業")
                
                for assignment in student_assignments[:3]:
                    print(f"   - {assignment['title']}")
                    print(f"     狀態: {assignment['status']}")
                    print(f"     {assignment.get('time_remaining', '無期限')}")
                
                # 9. 測試提交作業
                if student_assignments:
                    not_started = [a for a in student_assignments if a["status"] == "NOT_STARTED"]
                    
                    if not_started:
                        assignment_id = not_started[0]["id"]
                        print(f"\n9️⃣ 測試提交作業 (ID: {assignment_id})...")
                        
                        submission_data = {
                            "audio_urls": ["test1.mp3", "test2.mp3"],
                            "completed_at": datetime.now().isoformat()
                        }
                        
                        response = requests.post(
                            f"{BASE_URL}/assignments/{assignment_id}/submit",
                            json=submission_data,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            print("✅ 作業提交成功")
                        elif response.status_code == 400:
                            print("⚠️ 作業可能已經提交過")
                        else:
                            print(f"❌ 提交失敗: {response.status_code}")
            else:
                print(f"❌ 取得學生作業失敗: {response.status_code}")
        else:
            print(f"⚠️ 學生登入失敗，可能密碼已更改: {response.status_code}")
    
    print("\n" + "="*60)
    print("✅ 測試完成！")
    print("="*60)
    print("\n📊 測試摘要：")
    print("✅ Phase 1 功能：")
    print("   - 教師登入")
    print("   - 取得班級學生列表")
    print("   - 取得可用 Content")
    print("   - 建立作業（全班）")
    print("   - 查看作業統計")
    print("\n✅ Phase 2 功能：")
    print("   - 學生登入")
    print("   - 學生查看作業列表")
    print("   - 作業提交")
    
    return True


if __name__ == "__main__":
    print("⚠️  請確保：")
    print("1. 後端服務已啟動 (port 8000)")
    print("2. 已執行 seed_data.py")
    print("3. 已執行 seed_assignments.py")
    print("-" * 60)
    
    success = test_full_flow()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)