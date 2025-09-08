#!/usr/bin/env python3
"""測試學生錄音上傳到 GCS"""

import requests

def test_student_upload():
    """測試學生錄音上傳到 GCS"""
    
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
    test_file_path = "/tmp/test_student_recording.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"Test student recording for GCS upload")
    
    # 3. 上傳錄音到 GCS
    upload_url = "http://localhost:8000/api/students/upload-recording"
    
    with open(test_file_path, "rb") as f:
        files = {"audio_file": ("recording.webm", f, "audio/webm")}
        data = {
            "assignment_id": 1,
            "content_item_index": 0
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        print("📤 Uploading student recording to GCS...")
        response = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response.ok:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   - URL: {result.get('audio_url')}")
        print(f"   - Storage: {result.get('storage_type')}")
        print(f"   - Message: {result.get('message')}")
        
        # 判斷是 GCS 還是本地
        audio_url = result.get('audio_url', '')
        if audio_url.startswith('https://storage.googleapis.com/'):
            print("🎉 Successfully uploaded to Google Cloud Storage!")
        elif audio_url.startswith('/static/'):
            print("⚠️  Using local storage (GCS not available)")
        else:
            print(f"❓ Unknown storage type: {audio_url}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_student_upload()