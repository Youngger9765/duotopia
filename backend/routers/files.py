"""
檔案服務 API 路由
用於提供學生錄音檔案和其他靜態資源
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter(prefix="/api/files", tags=["files"])

# 設定檔案儲存路徑
UPLOAD_DIR = Path("uploads")
RECORDINGS_DIR = UPLOAD_DIR / "recordings"

# 確保目錄存在
RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/recordings/{filename}")
async def get_recording(filename: str):
    """獲取錄音檔案"""
    file_path = RECORDINGS_DIR / filename

    # 檢查檔案是否存在
    if not file_path.exists():
        # 如果檔案不存在，返回範例音檔（用於開發測試）
        # 在生產環境中應該返回 404
        raise HTTPException(
            status_code=404, detail=f"Recording file not found: {filename}"
        )

    # 返回檔案
    return FileResponse(
        path=str(file_path),
        media_type="audio/webm",  # 根據實際檔案格式調整
        headers={
            "Cache-Control": "public, max-age=3600",  # 快取 1 小時
        },
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
    # 創建一個簡單的測試音檔路徑
    test_file = RECORDINGS_DIR / "test.mp3"

    if not test_file.exists():
        # 如果沒有測試檔案，返回說明
        return {
            "message": "No test audio file available",
            "instruction": "Please place a test.mp3 file in the uploads/recordings directory",
            "alternative": "Using online sample audio files for testing",
        }

    return FileResponse(path=str(test_file), media_type="audio/mpeg")
