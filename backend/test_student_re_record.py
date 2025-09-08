#!/usr/bin/env python3
"""測試學生重新錄製功能（應該會刪除舊檔案）"""

import requests
import time

def test_student_re_record():
    """測試學生重新錄製功能"""
    
    # 1. 學生登入
    login_url = "http://localhost:8000/api/auth/student/login"
    login_data = {
        "email": "student1@duotopia.com",
        "password": "20120101"  # 生日作為密碼 (2012-01-01)
    }
    
    login_response = requests.post(login_url, json=login_data)
    if not login_response.ok:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Student login successful")
    
    # 2. 準備測試音檔
    test_file_path = "/tmp/test_first_recording.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"First recording for testing re-record")
    
    # 3. 第一次上傳錄音
    upload_url = "http://localhost:8000/api/students/upload-recording"
    
    print("📤 Uploading FIRST recording...")
    with open(test_file_path, "rb") as f:
        files = {"audio_file": ("first_recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": 1,
            "content_item_index": 0
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response1 = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response1.ok:
        result1 = response1.json()
        print(f"✅ First upload successful!")
        print(f"   - URL: {result1.get('audio_url')}")
        first_url = result1.get('audio_url')
    else:
        print(f"❌ First upload failed: {response1.status_code}")
        print(f"   Error: {response1.text}")
        return
    
    # 等待 2 秒
    time.sleep(2)
    
    # 4. 第二次上傳（重新錄製）
    test_file_path2 = "/tmp/test_second_recording.webm"
    with open(test_file_path2, "wb") as f:
        f.write(b"Second recording - should replace the first one")
    
    print("📤 Uploading SECOND recording (re-record)...")
    with open(test_file_path2, "rb") as f:
        files = {"audio_file": ("second_recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": 1,
            "content_item_index": 0  # 同樣的 assignment 和 index
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        response2 = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response2.ok:
        result2 = response2.json()
        print(f"✅ Second upload successful!")
        print(f"   - URL: {result2.get('audio_url')}")
        second_url = result2.get('audio_url')
        
        # 檢查 URL 是否不同
        if first_url != second_url:
            print(f"🎉 SUCCESS: Old recording should be deleted!")
            print(f"   First:  {first_url}")
            print(f"   Second: {second_url}")
        else:
            print(f"⚠️  Same URL returned - this might be unexpected")
            
    else:
        print(f"❌ Second upload failed: {response2.status_code}")
        print(f"   Error: {response2.text}")

if __name__ == "__main__":
    test_student_re_record()