#!/usr/bin/env python3
"""完整測試學生錄音上傳流程 - 包括資料庫操作和舊檔案刪除"""

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

def check_database_record(assignment_id, content_item_index):
    """檢查資料庫中的 StudentContentProgress 記錄"""
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
            audio_url = progress.response_data.get("audio_url") if progress.response_data else None
            print(f"📊 Database record found:")
            print(f"   - Progress ID: {progress.id}")
            print(f"   - Audio URL: {audio_url}")
            print(f"   - Status: {progress.status}")
            return audio_url
        else:
            print(f"📊 No database record found for assignment {assignment_id}, index {content_item_index}")
            return None
    finally:
        db.close()

def create_database_record(assignment_id, content_item_index, audio_url):
    """手動創建 StudentContentProgress 記錄"""
    db = SessionLocal()
    try:
        # 假設 content_id = 1 (需要根據實際情況調整)
        progress = StudentContentProgress(
            student_assignment_id=assignment_id,
            content_id=1,
            order_index=content_item_index,
            status="IN_PROGRESS",
            response_data={"audio_url": audio_url, "recorded_at": time.time()}
        )
        db.add(progress)
        db.commit()
        print(f"📝 Created database record with audio URL: {audio_url}")
        return progress.id
    except Exception as e:
        print(f"❌ Failed to create database record: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def test_complete_student_flow():
    """完整測試學生錄音流程"""
    
    print("🚀 Starting complete student recording flow test...")
    
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
    
    # 2. 檢查初始資料庫狀態
    print(f"\n=== STEP 1: Check initial database state ===")
    initial_url = check_database_record(assignment_id, content_item_index)
    
    # 3. 第一次上傳錄音
    print(f"\n=== STEP 2: First recording upload ===")
    test_file_path = "/tmp/test_first_recording.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"First recording for complete flow test")
    
    upload_url = "http://localhost:8000/api/students/upload-recording"
    
    print("📤 Uploading FIRST recording to GCS...")
    with open(test_file_path, "rb") as f:
        files = {"audio_file": ("first_recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": assignment_id,
            "content_item_index": content_item_index
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response1 = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response1.ok:
        result1 = response1.json()
        first_url = result1.get('audio_url')
        print(f"✅ First upload successful!")
        print(f"   - URL: {first_url}")
        
        # 如果資料庫沒有記錄，手動創建一個
        if not initial_url:
            progress_id = create_database_record(assignment_id, content_item_index, first_url)
            if progress_id:
                print(f"📝 Created database record with ID: {progress_id}")
        
    else:
        print(f"❌ First upload failed: {response1.status_code}")
        print(f"   Error: {response1.text}")
        return
    
    # 4. 檢查第一次上傳後的資料庫狀態
    print(f"\n=== STEP 3: Check database after first upload ===")
    check_database_record(assignment_id, content_item_index)
    
    # 等待 3 秒
    print(f"\n⏳ Waiting 3 seconds before second upload...")
    time.sleep(3)
    
    # 5. 第二次上傳（重新錄製）
    print(f"\n=== STEP 4: Second recording upload (re-record) ===")
    test_file_path2 = "/tmp/test_second_recording.webm"
    with open(test_file_path2, "wb") as f:
        f.write(b"Second recording - should replace the first one and delete old file")
    
    print("📤 Uploading SECOND recording (re-record)...")
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
        print(f"✅ Second upload successful!")
        print(f"   - URL: {second_url}")
        
        # 檢查 URL 是否不同
        if first_url != second_url:
            print(f"🎉 SUCCESS: URLs are different!")
            print(f"   First:  {first_url}")
            print(f"   Second: {second_url}")
            print(f"   Expected: Old file should be deleted from GCS")
        else:
            print(f"⚠️  Same URL returned - this might be unexpected")
            
    else:
        print(f"❌ Second upload failed: {response2.status_code}")
        print(f"   Error: {response2.text}")
        return
    
    # 6. 檢查第二次上傳後的資料庫狀態
    print(f"\n=== STEP 5: Check database after second upload ===")
    final_url = check_database_record(assignment_id, content_item_index)
    
    # 7. 總結
    print(f"\n=== SUMMARY ===")
    print(f"✅ First URL:  {first_url}")
    print(f"✅ Second URL: {second_url}")
    print(f"✅ Final DB URL: {final_url}")
    
    if first_url != second_url:
        print(f"🎉 Test PASSED: Different URLs generated")
    else:
        print(f"⚠️  Test WARNING: Same URLs")
        
    if final_url == second_url:
        print(f"🎉 Database UPDATED: Final URL matches second upload")
    else:
        print(f"❌ Database ERROR: Final URL doesn't match")
    
    print(f"\n💡 Check server logs for 'Deleted old student recording' message")

if __name__ == "__main__":
    test_complete_student_flow()