#!/usr/bin/env python3
"""測試 GCS 上傳功能是否正常"""

import os
import sys
from pathlib import Path
from google.cloud import storage

# 確保環境變數正確設定
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"


def test_gcs_connection():
    """測試 GCS 連線是否正常"""
    try:
        # 初始化 GCS client
        key_path = Path("service-account-key.json")
        if not key_path.exists():
            print(f"❌ Service account key 檔案不存在: {key_path}")
            return False

        print(f"✅ Service account key 檔案存在: {key_path}")

        # 創建 client
        client = storage.Client.from_service_account_json(str(key_path))
        print("✅ GCS client 初始化成功")

        # 測試存取 bucket
        bucket_name = "duotopia-audio"
        bucket = client.bucket(bucket_name)

        # 檢查 bucket 是否存在
        if bucket.exists():
            print(f"✅ Bucket '{bucket_name}' 存在且可存取")
        else:
            print(f"❌ Bucket '{bucket_name}' 不存在或無法存取")
            return False

        # 測試上傳一個小檔案
        test_blob_name = "test/connection_test.txt"
        blob = bucket.blob(test_blob_name)
        test_content = "GCS connection test successful"
        blob.upload_from_string(test_content)
        print(f"✅ 測試檔案上傳成功: gs://{bucket_name}/{test_blob_name}")

        # 刪除測試檔案
        blob.delete()
        print("✅ 測試檔案刪除成功")

        return True

    except Exception as e:
        print(f"❌ GCS 連線失敗: {e}")
        return False


if __name__ == "__main__":
    print("開始測試 GCS 連線...")
    print("-" * 50)

    success = test_gcs_connection()

    print("-" * 50)
    if success:
        print("✅ GCS 連線測試完全成功！錄音上傳功能應該可以正常運作。")
        sys.exit(0)
    else:
        print("❌ GCS 連線測試失敗，請檢查設定。")
        sys.exit(1)
