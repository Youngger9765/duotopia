#!/usr/bin/env python3
"""測試重新錄音時清除 AI 分數的功能"""

import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import StudentContentProgress
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 資料庫連線
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_ai_scores(assignment_id, content_item_index):
    """檢查 StudentContentProgress 中的 AI 分數"""
    db = SessionLocal()
    try:
        progress = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id == assignment_id,
                StudentContentProgress.order_index == content_item_index,
            )
            .first()
        )
        
        if progress and progress.response_data:
            ai_fields = ['ai_scores', 'pronunciation_score', 'fluency_score', 'accuracy_score', 'word_scores']
            ai_data = {field: progress.response_data.get(field) for field in ai_fields if field in progress.response_data}
            
            print(f"📊 AI Scores in database:")
            if ai_data:
                for field, value in ai_data.items():
                    print(f"   - {field}: {value}")
                return True
            else:
                print(f"   - No AI scores found")
                return False
        else:
            print(f"📊 No progress record found")
            return False
    finally:
        db.close()

def add_fake_ai_scores(assignment_id, content_item_index):
    """添加假的 AI 分數來測試清除功能"""
    db = SessionLocal()
    try:
        progress = (
            db.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id == assignment_id,
                StudentContentProgress.order_index == content_item_index,
            )
            .first()
        )
        
        if progress:
            if not progress.response_data:
                progress.response_data = {}
            
            # 添加假的 AI 分數
            progress.response_data.update({
                "ai_scores": {"overall": 85},
                "pronunciation_score": 88,
                "fluency_score": 82,
                "accuracy_score": 87,
                "word_scores": [{"word": "hello", "score": 90}, {"word": "world", "score": 85}]
            })
            
            db.commit()
            print(f"✅ Added fake AI scores to test cleanup")
            return True
        else:
            print(f"❌ No progress record found to add AI scores")
            return False
    finally:
        db.close()

def test_ai_score_cleanup():
    """測試 AI 分數清除功能"""
    
    print("🧪 Testing AI Score Cleanup on Re-recording...")
    
    # 1. 學生登入
    login_url = "http://localhost:8000/api/auth/student/login"
    login_data = {
        "email": "student1@duotopia.com",
        "password": "20120101"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if not login_response.ok:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Student login successful")
    
    assignment_id = 1
    content_item_index = 0
    
    # 2. 第一次上傳錄音
    print(f"\n=== STEP 1: First recording upload ===")
    test_file_path = "/tmp/test_ai_cleanup_first.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"First recording for AI cleanup test")
    
    upload_url = "http://localhost:8000/api/students/upload-recording"
    
    with open(test_file_path, "rb") as f:
        files = {"audio_file": ("first_recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": assignment_id,
            "content_item_index": content_item_index
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response1 = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if not response1.ok:
        print(f"❌ First upload failed: {response1.status_code} - {response1.text}")
        return
    
    result1 = response1.json()
    first_url = result1.get('audio_url')
    print(f"✅ First upload successful: {first_url}")
    
    # 3. 添加假的 AI 分數
    print(f"\n=== STEP 2: Add fake AI scores ===")
    if add_fake_ai_scores(assignment_id, content_item_index):
        check_ai_scores(assignment_id, content_item_index)
    
    # 4. 等待 2 秒
    print(f"\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # 5. 第二次上傳（重新錄製）- 應該清除 AI 分數
    print(f"\n=== STEP 3: Re-record (should clear AI scores) ===")
    test_file_path2 = "/tmp/test_ai_cleanup_second.webm"
    with open(test_file_path2, "wb") as f:
        f.write(b"Second recording - should clear AI scores")
    
    print("📤 Re-recording (should trigger AI score cleanup)...")
    with open(test_file_path2, "rb") as f:
        files = {"audio_file": ("second_recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": assignment_id,
            "content_item_index": content_item_index
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response2 = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response2.ok:
        result2 = response2.json()
        second_url = result2.get('audio_url')
        print(f"✅ Re-record successful: {second_url}")
    else:
        print(f"❌ Re-record failed: {response2.status_code} - {response2.text}")
        return
    
    # 6. 檢查 AI 分數是否被清除
    print(f"\n=== STEP 4: Check if AI scores were cleared ===")
    ai_scores_exist = check_ai_scores(assignment_id, content_item_index)
    
    # 7. 總結
    print(f"\n=== SUMMARY ===")
    print(f"✅ First URL:  {first_url}")
    print(f"✅ Second URL: {second_url}")
    
    if first_url != second_url:
        print(f"✅ URLs are different (re-recording worked)")
    else:
        print(f"⚠️  URLs are same (unexpected)")
    
    if not ai_scores_exist:
        print(f"🎉 AI SCORES CLEARED: Success! AI scores were properly cleaned up")
    else:
        print(f"❌ AI SCORES NOT CLEARED: AI scores still exist in database")
    
    print(f"\n💡 Check server logs for 'Cleared AI scores for re-recording' message")

if __name__ == "__main__":
    test_ai_score_cleanup()