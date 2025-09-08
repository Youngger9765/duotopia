#!/usr/bin/env python
"""測試 Azure Speech API 並診斷錯誤"""
import os
import requests
import json
import base64
from pathlib import Path

# 設定環境變數
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env.local")

# 取得認證 token（模擬學生登入）
print("1. 模擬學生登入...")
login_response = requests.post(
    "http://localhost:8000/api/auth/student/login",
    json={
        "email": "demo@duotopia.com",  # 教師 email
        "classroom_id": 1,  # 五年級A班
        "student_id": "S001",  # 王小明的學生編號
        "password": "20120101",
    },
)

if login_response.status_code != 200:
    print(f"登入失敗: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print("✓ 登入成功，取得 token")

# 創建測試音檔（使用簡單的 WAV 格式）
print("\n2. 創建測試音檔...")
# 這是一個最小的 WAV 檔案（靜音）
wav_header = bytes(
    [
        0x52,
        0x49,
        0x46,
        0x46,  # "RIFF"
        0x24,
        0x00,
        0x00,
        0x00,  # ChunkSize
        0x57,
        0x41,
        0x56,
        0x45,  # "WAVE"
        0x66,
        0x6D,
        0x74,
        0x20,  # "fmt "
        0x10,
        0x00,
        0x00,
        0x00,  # Subchunk1Size
        0x01,
        0x00,  # AudioFormat (PCM)
        0x01,
        0x00,  # NumChannels (Mono)
        0x44,
        0xAC,
        0x00,
        0x00,  # SampleRate (44100)
        0x88,
        0x58,
        0x01,
        0x00,  # ByteRate
        0x02,
        0x00,  # BlockAlign
        0x10,
        0x00,  # BitsPerSample
        0x64,
        0x61,
        0x74,
        0x61,  # "data"
        0x00,
        0x00,
        0x00,
        0x00,  # Subchunk2Size (0 bytes of audio)
    ]
)

# 測試 API
print("\n3. 測試 Speech Assessment API...")
with open("/tmp/test_audio.wav", "wb") as f:
    f.write(wav_header)

with open("/tmp/test_audio.wav", "rb") as f:
    files = {"audio_file": ("test.wav", f, "audio/wav")}
    data = {"reference_text": "Hello world", "progress_id": "1"}
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.post(
        "http://localhost:8000/api/speech/assess",
        files=files,
        data=data,
        headers=headers,
    )

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 503:
    print("\n⚠️  503 錯誤 - 檢查後端日誌以獲得詳細錯誤訊息")
elif response.status_code == 200:
    print("\n✅ API 正常運作！")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
