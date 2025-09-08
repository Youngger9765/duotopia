#!/usr/bin/env python
"""直接測試 Azure Speech API 問題"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env.local")

# 匯入並測試函數
sys.path.insert(0, str(Path(__file__).parent))
from routers.speech_assessment import assess_pronunciation  # noqa: E402

# 創建測試音檔（最小的 WAV）
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

print("測試 Azure Speech API...")
print(f"AZURE_SPEECH_KEY exists: {bool(os.getenv('AZURE_SPEECH_KEY'))}")
print(f"AZURE_SPEECH_REGION: {os.getenv('AZURE_SPEECH_REGION')}")

try:
    result = assess_pronunciation(wav_header, "Hello world")
    print("✅ API 正常運作！")
    print(f"Result: {result}")
except Exception as e:
    print(f"❌ 錯誤: {e}")
    import traceback

    traceback.print_exc()
