#!/usr/bin/env python3
"""測試 GCS 上傳功能"""

import asyncio
import requests
from pathlib import Path

def test_gcs_upload():
    """測試錄音上傳到 GCS"""
    
    # 1. 先登入取得 token
    login_url = "http://localhost:8000/api/auth/student/login"
    login_data = {
        "email": "student1@duotopia.com",  # 使用實際存在的學生
        "password": "20100101"
    }
    
    login_response = requests.post(login_url, json=login_data)
    if not login_response.ok:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print(f"✅ Login successful, token: {token[:20]}...")
    
    # 2. 準備測試檔案
    test_file_path = "/tmp/test_audio.webm"
    with open(test_file_path, "wb") as f:
        f.write(b"Test audio content for GCS upload")
    
    # 3. 上傳到 GCS
    upload_url = "http://localhost:8000/api/students/upload-recording"
    
    with open(test_file_path, "rb") as f:
        files = {"audio_file": ("test.webm", f, "audio/webm")}
        data = {
            "assignment_id": 1,
            "content_item_index": 0
        }
        headers = {"Authorization": f"Bearer {token}"}
        
        print("📤 Uploading to GCS...")
        response = requests.post(upload_url, files=files, data=data, headers=headers)
    
    if response.ok:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   - URL: {result.get('audio_url')}")
        print(f"   - Storage: {result.get('storage_type')}")
        print(f"   - Message: {result.get('message')}")
        
        if result.get('storage_type') == 'gcs':
            print("🎉 Successfully uploaded to Google Cloud Storage!")
        else:
            print("⚠️  Using local storage (GCS not available)")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(f"   Error: {response.text}")

if __name__ == "__main__":
    test_gcs_upload()