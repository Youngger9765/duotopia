"""
檔案服務 API 路由
用於提供學生錄音檔案和其他靜態資源
"""

from fastapi import APIRouter, HTTPException, Response

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/recordings/{filename}")
async def get_recording(filename: str):
    """獲取錄音檔案 - 從 GCS 重定向"""
    # 錄音檔案應該已經儲存在 GCS，這個 endpoint 只是為了相容性
    # 實際的錄音 URL 應該直接指向 GCS
    raise HTTPException(
        status_code=404,
        detail=f"Recording file not found: {filename}. Files should be accessed directly from GCS.",
    )


@router.get("/audio/{content_id}/{item_index}")
async def get_content_audio(content_id: int, item_index: int):
    """獲取內容音檔（題目參考音檔）"""
    # 這裡應該從資料庫或儲存系統中獲取實際的音檔路徑
    # 現在返回範例音檔用於測試

    # 範例：返回不同的測試音檔
    sample_urls = [
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
    ]

    # 使用 item_index 選擇不同的範例音檔
    sample_url = sample_urls[item_index % len(sample_urls)]

    # 在實際應用中，這裡應該返回實際的音檔檔案
    # return FileResponse(path=audio_file_path)

    # 暫時返回重定向到範例音檔
    return Response(status_code=307, headers={"Location": sample_url})


@router.get("/test-audio")
async def get_test_audio():
    """提供測試用音檔"""
    # 返回線上範例音檔
    return {
        "message": "Test audio endpoint",
        "alternative": "Using online sample audio files for testing",
        "sample_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
    }
