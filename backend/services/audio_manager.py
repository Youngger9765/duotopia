"""
Audio manager service for handling audio files with GCS
"""
import os
from typing import Optional
from google.cloud import storage
from urllib.parse import urlparse


class AudioManager:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        self.storage_client = None

    def _get_storage_client(self):
        """延遲初始化 GCS client"""
        if not self.storage_client:
            try:
                # 使用環境變數中的認證
                self.storage_client = storage.Client()
            except Exception as e:
                print(f"GCS client initialization failed: {e}")
                return None
        return self.storage_client

    def delete_old_audio(self, audio_url: str) -> bool:
        """
        刪除舊的音檔

        Args:
            audio_url: 音檔 URL

        Returns:
            是否刪除成功
        """
        if not audio_url:
            return True

        try:
            # 判斷是 GCS URL 還是本地 URL
            if audio_url.startswith("https://storage.googleapis.com/"):
                # GCS URL: https://storage.googleapis.com/bucket/path/file.mp3
                parsed = urlparse(audio_url)
                path_parts = parsed.path.strip("/").split("/", 1)
                if len(path_parts) == 2:
                    bucket_name = path_parts[0]
                    blob_name = path_parts[1]

                    client = self._get_storage_client()
                    if client:
                        bucket = client.bucket(bucket_name)
                        blob = bucket.blob(blob_name)
                        blob.delete()
                        print(f"Deleted GCS file: {blob_name}")
                        return True

            elif audio_url.startswith("/static/audio/"):
                # 本地檔案
                file_path = audio_url.replace("/static/", "static/")
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Deleted local file: {file_path}")
                    return True

        except Exception as e:
            print(f"Failed to delete audio file: {e}")

        return False

    def update_audio(self, old_url: Optional[str], new_url: str) -> str:
        """
        更新音檔（刪除舊的，保留新的）

        Args:
            old_url: 舊音檔 URL
            new_url: 新音檔 URL

        Returns:
            新音檔 URL
        """
        # 如果有舊檔案且不同於新檔案，刪除舊檔案
        if old_url and old_url != new_url:
            self.delete_old_audio(old_url)

        return new_url

    def get_gcs_url(self, blob_name: str) -> str:
        """
        取得 GCS 公開 URL

        Args:
            blob_name: Blob 名稱

        Returns:
            公開 URL
        """
        return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"


# 單例模式
_audio_manager = None


def get_audio_manager() -> AudioManager:
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManager()
    return _audio_manager
