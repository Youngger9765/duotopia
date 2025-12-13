#!/usr/bin/env python3
"""
檢查 Azure Speech Service 定價層
需要: pip install azure-mgmt-cognitiveservices azure-identity
"""
import os
import sys
from pathlib import Path

# 加入 backend 路徑以使用 config
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

try:
    from azure.identity import DefaultAzureCredential
    from azure.mgmt.cognitiveservices import CognitiveServicesManagementClient
    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False
    print("⚠️  Azure SDK 未安裝，無法查詢")
    print("安裝方式: pip install azure-mgmt-cognitiveservices azure-identity")
    print()

# 從環境變數讀取（或從 .env）
from core.config import settings

def check_azure_tier():
    """檢查 Azure Speech Service 定價層"""

    if not settings.AZURE_SPEECH_KEY:
        print("❌ 未設定 AZURE_SPEECH_KEY 環境變數")
        return

    if not settings.AZURE_SPEECH_REGION:
        print("❌ 未設定 AZURE_SPEECH_REGION 環境變數")
        return

    print(f"✅ Azure Speech Region: {settings.AZURE_SPEECH_REGION}")
    print(f"✅ Azure Speech Key: {settings.AZURE_SPEECH_KEY[:10]}...")
    print()

    # 檢查 TPS (從文檔中的已知限制)
    print("📋 已知的 TPS 限制：")
    print("   - F0 (免費層): 20 TPS, 5M 字符/月")
    print("   - S0 (標準層): 20 TPS (預設，可聯繫客服提升至 100-1000)")
    print()

    if not AZURE_SDK_AVAILABLE:
        print("💡 建議操作：")
        print("   1. 前往 Azure Portal 查看: https://portal.azure.com")
        print("   2. 搜尋 'Speech Services'")
        print("   3. 選擇資源 → 左側 'Pricing tier'")
        return

    # 使用 Azure Management API 查詢
    try:
        print("🔍 嘗試使用 Azure Management API 查詢...")
        credential = DefaultAzureCredential()

        # 需要 Subscription ID（從 Azure Portal 取得）
        subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
        if not subscription_id:
            print("❌ 需要設定 AZURE_SUBSCRIPTION_ID 環境變數")
            print("   可從 Azure Portal → 訂閱 → 複製訂閱 ID")
            return

        client = CognitiveServicesManagementClient(credential, subscription_id)

        # 列出所有認知服務
        print("📋 你的 Azure Cognitive Services 資源：")
        for account in client.accounts.list():
            if account.kind == "SpeechServices":
                print(f"   - 名稱: {account.name}")
                print(f"   - 資源群組: {account.id.split('/')[4]}")
                print(f"   - 定價層: {account.sku.name}")
                print(f"   - 位置: {account.location}")
                print()

    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        print()
        print("💡 請改用 Azure Portal 查詢：")
        print("   https://portal.azure.com → Speech Services")

if __name__ == "__main__":
    check_azure_tier()
