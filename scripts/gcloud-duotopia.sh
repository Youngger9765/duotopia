#!/bin/bash
# Duotopia 專屬 gcloud 環境腳本

# 設定隔離環境變數
export CLOUDSDK_CONFIG=$HOME/.gcloud-duotopia
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.11

# 顯示當前配置
echo "🌟 使用 Duotopia 隔離環境"
echo "📁 CLOUDSDK_CONFIG=$CLOUDSDK_CONFIG"
echo "🐍 CLOUDSDK_PYTHON=$CLOUDSDK_PYTHON"
echo ""

# 驗證專案設定
PROJECT_ID=$(gcloud config get-value project)
ACCOUNT=$(gcloud config get-value account)

echo "🏗️  專案: $PROJECT_ID"
echo "👤 帳號: $ACCOUNT"
echo "🌏 區域: asia-east1"
echo ""

# 執行傳入的 gcloud 指令
if [ $# -eq 0 ]; then
    echo "使用方式: ./scripts/gcloud-duotopia.sh [gcloud command]"
    echo "範例: ./scripts/gcloud-duotopia.sh run deploy duotopia-backend ..."
else
    echo "執行: gcloud $@"
    echo "---"
    gcloud "$@"
fi