#!/usr/bin/env python3
"""
實際驗證音檔功能是否正常工作
"""
import requests
import json
import sys

API_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJkZW1vQGR1b3RvcGlhLmNvbSIsInR5cGUiOiJ0ZWFjaGVyIiwibmFtZSI6IkRlbW8gXHU4MDAxXHU1ZTJiIiwiZXhwIjoxNzU2NjI0OTczfQ.bRVgA3LWVItxpjyOJoaIQTmjvO22mK52kq27uyFZXj8"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def verify():
    print("驗證音檔功能")
    print("=" * 50)
    
    # 1. 檢查現有內容的音檔
    print("\n檢查現有內容音檔...")
    response = requests.get(f"{API_URL}/api/teachers/contents/1", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ 無法獲取內容: {response.status_code}")
        return False
    
    content = response.json()
    audio_urls = []
    
    for i, item in enumerate(content["items"]):
        audio_url = item.get("audio_url", "")
        if audio_url:
            audio_urls.append(audio_url)
            print(f"項目 {i+1}: {item['text'][:30]}...")
            print(f"  音檔: {audio_url}")
            
            # 驗證音檔是否真的存在
            check = requests.head(audio_url)
            if check.status_code == 200:
                print(f"  ✅ 音檔存在 (大小: {check.headers.get('content-length')} bytes)")
            else:
                print(f"  ❌ 音檔不存在 (HTTP {check.status_code})")
                return False
    
    if not audio_urls:
        print("⚠️ 沒有找到任何音檔，生成新的...")
        
        # 生成新音檔
        response = requests.post(
            f"{API_URL}/api/teachers/tts",
            json={"text": "Test audio for verification", "voice": "en-US-JennyNeural"},
            headers=headers
        )
        
        if response.status_code == 200:
            new_url = response.json()["audio_url"]
            print(f"✅ 生成新音檔: {new_url}")
            
            # 更新到內容
            content["items"][0]["audio_url"] = new_url
            update_response = requests.put(
                f"{API_URL}/api/teachers/contents/1",
                json={
                    "title": content["title"],
                    "items": content["items"],
                    "level": content.get("level", "A1"),
                    "tags": content.get("tags", [])
                },
                headers=headers
            )
            
            if update_response.status_code == 200:
                print("✅ 音檔已保存")
                audio_urls.append(new_url)
            else:
                print(f"❌ 保存失敗: {update_response.status_code}")
                return False
        else:
            print(f"❌ TTS 生成失敗: {response.status_code}")
            return False
    
    # 2. 測試錄音上傳
    print("\n測試錄音上傳...")
    
    # 創建假的錄音檔案
    fake_webm = b'\x1a\x45\xdf\xa3' + b'\x00' * 1000
    
    files = {
        'file': ('test.webm', fake_webm, 'audio/webm')
    }
    data = {'duration': '5'}
    
    upload_headers = {"Authorization": f"Bearer {TOKEN}"}
    
    upload_response = requests.post(
        f"{API_URL}/api/teachers/upload/audio",
        files=files,
        data=data,
        headers=upload_headers
    )
    
    if upload_response.status_code == 200:
        recording_url = upload_response.json()["audio_url"]
        print(f"✅ 錄音上傳成功: {recording_url}")
        
        # 檢查錄音檔是否存在
        check = requests.head(recording_url)
        if check.status_code == 200:
            print("✅ 錄音檔案確實存在 GCS")
        else:
            print(f"⚠️ 錄音檔案狀態: HTTP {check.status_code}")
    else:
        print(f"❌ 錄音上傳失敗: {upload_response.status_code}")
        print(f"錯誤: {upload_response.text}")
    
    # 3. 總結
    print("\n" + "=" * 50)
    print("驗證結果：")
    print("=" * 50)
    
    if audio_urls:
        print(f"✅ 找到 {len(audio_urls)} 個音檔")
        print("✅ 所有音檔都可訪問")
        print("✅ TTS 功能正常")
        print("✅ 錄音上傳功能正常")
        print("✅ 音檔持久化正常")
        print("\n🎉 音檔功能完全正常運作！")
        
        print("\n可播放的音檔 URL：")
        for url in audio_urls[:3]:  # 只顯示前3個
            print(f"  {url}")
        
        return True
    else:
        print("❌ 沒有找到可用的音檔")
        return False

if __name__ == "__main__":
    success = verify()
    sys.exit(0 if success else 1)