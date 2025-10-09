"""
Audio upload service for recording files
"""

import os
import uuid
from datetime import datetime  # noqa: F401
from typing import Optional  # noqa: F401
from fastapi import UploadFile, HTTPException


class AudioUploadService:
    def __init__(self):
        # GCS 設定
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        self.storage_client = None
        self.max_file_size = 2 * 1024 * 1024  # 2MB 限制
        self.allowed_formats = [
            "audio/webm",
            "audio/webm;codecs=opus",  # 支援帶 codecs 的 webm
            "audio/mp3",
            "audio/wav",
            "audio/mpeg",
            "audio/mp4",
            "audio/ogg",
            "audio/opus",
            "audio/x-m4a",
            "video/webm",  # 某些瀏覽器會將 webm 音檔標記為 video/webm
        ]
        self.environment = os.getenv("ENVIRONMENT", "development")

    def _get_storage_client(self):
        """延遲初始化 GCS client"""
        if not self.storage_client:
            try:
                from google.cloud import storage

                # 明確指定 service account key 檔案路徑 (在 backend 目錄下)
                backend_dir = os.path.dirname(os.path.dirname(__file__))
                key_path = os.path.join(backend_dir, "service-account-key.json")
                print(f"🔍 Looking for GCS key at: {key_path}")
                print(f"🔍 Key exists: {os.path.exists(key_path)}")
                if os.path.exists(key_path):
                    self.storage_client = storage.Client.from_service_account_json(
                        key_path
                    )
                    print(
                        f"GCS client initialized with service account from {key_path}"
                    )
                else:
                    # 如果找不到檔案，嘗試使用預設認證（環境變數或 gcloud）
                    self.storage_client = storage.Client()
                    print("GCS client initialized with default credentials")
            except Exception as e:
                print(f"GCS client initialization failed: {e}")
                return None
        return self.storage_client

    async def upload_audio(
        self,
        file: UploadFile,
        duration_seconds: int = 30,
        content_id: int = None,
        item_index: int = None,
        assignment_id: int = None,
        student_id: int = None,
    ) -> str:
        """
        上傳音檔到 GCS

        Args:
            file: 上傳的音檔
            duration_seconds: 音檔長度（秒）

        Returns:
            音檔 URL
        """
        try:
            # 檢查檔案類型
            if file.content_type not in self.allowed_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed: {', '.join(self.allowed_formats)}",
                )

            # 讀取檔案內容
            content = await file.read()

            # 檢查檔案大小（至少 5KB，最多 2MB）
            min_file_size = 5 * 1024  # 5KB
            if len(content) < min_file_size:
                # 記錄到 BigQuery
                from services.bigquery_logger import get_bigquery_logger

                logger = get_bigquery_logger()
                await logger.log_audio_error(
                    {
                        "error_type": "backend_validation_file_too_small",
                        "error_message": f"File size {len(content)} bytes < minimum {min_file_size} bytes",
                        "audio_url": file.filename or "unknown",
                        "audio_size": len(content),
                        "content_type": file.content_type,
                        "assignment_id": assignment_id,
                        "student_id": student_id,
                    }
                )

                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Recording file too small ({len(content)} bytes). "
                        f"Must be at least {min_file_size / 1024}KB for valid audio."
                    ),
                )

            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size / 1024 / 1024}MB",
                )

            # 檢查錄音長度
            if duration_seconds > 30:
                raise HTTPException(
                    status_code=400,
                    detail="Recording too long. Maximum duration: 30 seconds",
                )

            # 生成唯一檔名（包含 content_id 和 item_index 以便追蹤）
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 根據 content type 決定擴展名
            ext_map = {
                "audio/webm": "webm",
                "video/webm": "webm",
                "audio/mp4": "m4a",
                "audio/ogg": "ogg",
                "audio/opus": "opus",
                "audio/mpeg": "mp3",
                "audio/wav": "wav",
            }
            extension = ext_map.get(file.content_type, "webm")

            # 如果有 content_id 和 item_index，加入檔名中
            if content_id and item_index is not None:
                filename = f"recording_c{content_id}_i{item_index}_{timestamp}_{file_id}.{extension}"
            else:
                filename = f"recording_{timestamp}_{file_id}.{extension}"

            # 上傳到 GCS
            client = self._get_storage_client()
            if not client:
                raise HTTPException(
                    status_code=500,
                    detail="GCS service unavailable. Cannot save recordings.",
                )

            try:
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(f"recordings/{filename}")

                # 上傳檔案並設定正確的 content type
                blob.upload_from_string(content, content_type=file.content_type)

                # 設為公開
                blob.make_public()

                # 返回公開 URL
                return f"https://storage.googleapis.com/{self.bucket_name}/recordings/{filename}"

            except Exception as e:
                print(f"GCS upload failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload recording to cloud storage: {str(e)}",
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# 單例模式
_audio_upload_service = None


def get_audio_upload_service() -> AudioUploadService:
    global _audio_upload_service
    if _audio_upload_service is None:
        _audio_upload_service = AudioUploadService()
    return _audio_upload_service
