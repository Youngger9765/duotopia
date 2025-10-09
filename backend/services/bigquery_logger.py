"""BigQuery 日誌記錄服務"""
import os
from datetime import datetime
from google.cloud import bigquery
from typing import Dict, Any


class BigQueryLogger:
    def __init__(self):
        # 使用跟 audio_upload.py 一樣的認證方式
        backend_dir = os.path.dirname(os.path.dirname(__file__))
        key_path = os.path.join(backend_dir, "service-account-key.json")

        if os.path.exists(key_path):
            self.client = bigquery.Client.from_service_account_json(key_path)
            print(f"✅ BigQuery client initialized with service account from {key_path}")
        else:
            self.client = bigquery.Client()
            print("✅ BigQuery client initialized with default credentials")

        # 從環境變數讀取專案 ID，預設使用 duotopia-472708
        project_id = os.getenv("GCP_PROJECT_ID", "duotopia-472708")
        self.table_id = f"{project_id}.duotopia_logs.audio_playback_errors"
        print(f"📊 BigQuery table: {self.table_id}")

    async def log_audio_error(self, error_data: Dict[str, Any]) -> bool:
        """
        記錄音檔錯誤到 BigQuery

        Args:
            error_data: 錯誤資料字典

        Returns:
            bool: 是否成功記錄
        """
        try:
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
