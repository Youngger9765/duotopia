#!/usr/bin/env python3
"""
音檔功能完整測試
包含 TTS 生成、錄音上傳、持久化、刪除等所有功能
"""
import requests
import time
import sys

API_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZW1haWwiOiJkZW1vQGR1b3RvcGlhLmNvbSIsInR5cGUiOiJ0ZWFjaGVyIiwibmFtZSI6IkRlbW8gXHU4MDAxXHU1ZTJiIiwiZXhwIjoxNzU2NjI0OTczfQ.bRVgA3LWVItxpjyOJoaIQTmjvO22mK52kq27uyFZXj8"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_tts():
    """測試 TTS 生成"""
    print("\n測試 TTS 生成...")
    response = requests.post(
        f"{API_URL}/api/teachers/tts",
        json={"text": "Testing TTS functionality", "voice": "en-US-JennyNeural"},
        headers=headers
    )
    
    if response.status_code == 200:
        audio_url = response.json()["audio_url"]
        print(f"✅ TTS 生成成功: {audio_url}")
        
        # 檢查音檔是否存在
        check = requests.head(audio_url)
        if check.status_code == 200:
            print(f"✅ 音檔可訪問 ({check.headers.get('content-length')} bytes)")
            return audio_url
        else:
            print(f"❌ 音檔無法訪問: HTTP {check.status_code}")
            return None
    else:
        print(f"❌ TTS 生成失敗: {response.status_code}")
        return None

def test_recording_upload():
    """測試錄音上傳"""
    print("\n測試錄音上傳...")
    
    # 創建測試音檔
    fake_webm = b'\x1a\x45\xdf\xa3' + b'\x00' * 1000
    files = {'file': ('recording.webm', fake_webm, 'audio/webm')}
    data = {'duration': '5'}
    upload_headers = {"Authorization": f"Bearer {TOKEN}"}
    
    response = requests.post(
        f"{API_URL}/api/teachers/upload/audio",
        files=files,
        data=data,
        headers=upload_headers
    )
    
    if response.status_code == 200:
        audio_url = response.json()["audio_url"]
        print(f"✅ 錄音上傳成功: {audio_url}")
        return audio_url
    else:
        print(f"❌ 錄音上傳失敗: {response.status_code}")
        return None

def test_persistence(audio_url):
    """測試音檔持久化"""
    print("\n測試音檔持久化...")
    
    # 獲取內容
    response = requests.get(f"{API_URL}/api/teachers/contents/1", headers=headers)
    if response.status_code != 200:
        print(f"❌ 無法獲取內容: {response.status_code}")
        return False
    
    content = response.json()
    
    # 更新音檔
    if content["items"]:
        content["items"][0]["audio_url"] = audio_url
        
        # 保存
        response = requests.put(
            f"{API_URL}/api/teachers/contents/1",
            json={
                "title": content["title"],
                "items": content["items"],
                "level": content.get("level", "A1"),
                "tags": content.get("tags", [])
            },
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ 音檔已保存到資料庫")
            
            # 重新獲取驗證
            time.sleep(1)
            verify_response = requests.get(f"{API_URL}/api/teachers/contents/1", headers=headers)
            if verify_response.status_code == 200:
                verified_content = verify_response.json()
                saved_url = verified_content["items"][0].get("audio_url")
                if saved_url == audio_url:
                    print("✅ 音檔持久化成功")
                    return True
    
    print("❌ 音檔持久化失敗")
    return False

def test_audio_replacement():
    """測試音檔替換與舊檔刪除"""
    print("\n測試音檔替換...")
    
    # 生成兩個音檔
    response1 = requests.post(
        f"{API_URL}/api/teachers/tts",
        json={"text": "First audio file", "voice": "en-US-JennyNeural"},
        headers=headers
    )
    
    response2 = requests.post(
        f"{API_URL}/api/teachers/tts",
        json={"text": "Second audio file", "voice": "en-US-AriaNeural"},
        headers=headers
    )
    
    if response1.status_code == 200 and response2.status_code == 200:
        old_url = response1.json()["audio_url"]
        new_url = response2.json()["audio_url"]
        
        print(f"舊音檔: {old_url}")
        print(f"新音檔: {new_url}")
        
        # 先設定舊音檔
        test_persistence(old_url)
        
        # 替換為新音檔
        test_persistence(new_url)
        
        # 檢查舊音檔是否被刪除
        time.sleep(2)
        check = requests.head(old_url)
        if check.status_code == 404:
            print("✅ 舊音檔已刪除")
            return True
        elif check.status_code == 200:
            print("⚠️ 舊音檔仍存在（可能需要檢查刪除邏輯）")
            return False
    
    print("❌ 音檔替換測試失敗")
    return False

def main():
    print("=" * 60)
    print("音檔功能完整測試")
    print("=" * 60)
    
    # 測試 API 連線
    try:
        response = requests.get(f"{API_URL}/api/health")
        print("✅ API 連線正常")
    except:
        print("❌ API 連線失敗，請確認後端服務是否運行")
        sys.exit(1)
    
    # 執行測試
    results = {
        "TTS 生成": False,
        "錄音上傳": False,
        "音檔持久化": False,
        "音檔替換": False
    }
    
    # TTS 測試
    tts_url = test_tts()
    if tts_url:
        results["TTS 生成"] = True
        
        # 持久化測試
        if test_persistence(tts_url):
            results["音檔持久化"] = True
    
    # 錄音測試
    recording_url = test_recording_upload()
    if recording_url:
        results["錄音上傳"] = True
    
    # 替換測試
    if test_audio_replacement():
        results["音檔替換"] = True
    
    # 總結
    print("\n" + "=" * 60)
    print("測試結果總結")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有測試通過！")
    else:
        print("\n⚠️ 部分測試失敗，請檢查相關功能")
    
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()