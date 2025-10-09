"""BigQuery 日誌記錄服務"""
import os
from datetime import datetime
from google.cloud import bigquery
from typing import Dict, Any


class BigQueryLogger:
    def __init__(self):
        self.client = None
        self._initialized = False

        # 從環境變數讀取專案 ID，預設使用 duotopia-472708
        project_id = os.getenv("GCP_PROJECT_ID", "duotopia-472708")
        self.table_id = f"{project_id}.duotopia_logs.audio_playback_errors"

    def _ensure_client(self):
        """延遲初始化 BigQuery client（只在第一次使用時初始化）"""
        if self._initialized:
            return

        try:
            # 使用跟 audio_upload.py 一樣的認證方式
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            key_path = os.path.join(backend_dir, "service-account-key.json")

            if os.path.exists(key_path):
                self.client = bigquery.Client.from_service_account_json(key_path)
                print(
                    f"✅ BigQuery client initialized with service account from {key_path}"
                )
            else:
                # Cloud Run 環境使用 Application Default Credentials
                self.client = bigquery.Client()
                print("✅ BigQuery client initialized with default credentials")

            print(f"📊 BigQuery table: {self.table_id}")
            self._initialized = True
        except Exception as e:
            print(f"⚠️ BigQuery client initialization failed: {e}")
            print("⚠️ Audio error logging will be disabled, but app will continue")
            self._initialized = True  # 標記為已嘗試初始化，避免重複嘗試

    async def log_audio_error(self, error_data: Dict[str, Any]) -> bool:
        """
        記錄音檔錯誤到 BigQuery

        Args:
            error_data: 錯誤資料字典

        Returns:
            bool: 是否成功記錄
        """
        try:
            # 延遲初始化 client
            self._ensure_client()

            # 如果 client 初始化失敗，靜默返回 False
            if self.client is None:
                print("⚠️ BigQuery client not available, skipping log")
                return False

            # 確保有 timestamp（使用 ISO 格式字串）
            if "timestamp" not in error_data:
                error_data["timestamp"] = datetime.utcnow().isoformat()

            print(f"📝 Logging to BigQuery: {error_data.get('error_type')}")

            # 插入資料（Streaming Insert）
            errors = self.client.insert_rows_json(self.table_id, [error_data])

            if errors:
                print(f"❌ BigQuery insert failed: {errors}")
                return False

            print(f"✅ BigQuery logged: {error_data.get('error_type')}")
            return True

        except Exception as e:
            print(f"❌ BigQuery error: {e}")
            return False


# 單例模式
_bigquery_logger = None


def get_bigquery_logger() -> BigQueryLogger:
    global _bigquery_logger
    if _bigquery_logger is None:
        _bigquery_logger = BigQueryLogger()
    return _bigquery_logger
