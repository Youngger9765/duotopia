#!/usr/bin/env python3
"""測試教師上傳音檔到 GCS"""

import requests
import json

def test_teacher_upload():
    """測試教師上傳音檔到 GCS"""
    
    # 1. 教師登入
    login_url = "http://localhost:8000/api/auth/teacher/login"
    login_data = {
        "email": "demo@duotopia.com",
        "password": "demo123"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if not login_response.ok:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Teacher login successful")
    
    # 2. 準備測試檔案
    test_file_path = "/tmp/test_teacher_audio.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"Test teacher audio content for GCS upload")
    
    # 3. 上傳到 GCS (模擬教師上傳音檔)
    upload_url = "http://localhost:8000/api/teachers/upload/audio"
    
    with open(test_file_path, "rb") as f:
        files = {"file": ("test.webm", f, "audio/webm")}
        data = {
            "duration": 30,
            "content_id": 1,
            "item_index": 0
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        print("📤 Uploading to GCS via teacher endpoint...")
        response = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response.ok:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   - URL: {result.get('audio_url')}")
        
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
    test_teacher_upload()