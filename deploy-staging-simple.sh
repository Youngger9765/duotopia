#!/bin/bash
set -e

echo "🚀 開始部署後端到 Staging 環境..."

# 設定變數
PROJECT_ID="duotopia-469413"
REGION="asia-east1"
SERVICE_NAME="duotopia-backend-staging"

# 確認在專案根目錄
if [ ! -f "Dockerfile.backend" ]; then
    echo "❌ 錯誤：請在專案根目錄執行此腳本"
    exit 1
fi

# 確認 gcloud 配置
echo "📋 檢查 GCloud 配置..."
gcloud config set project $PROJECT_ID

# 建置 Docker 映像
echo "🐳 建置 Docker 映像..."
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/$SERVICE_NAME \
    -f Dockerfile.backend \
    .

# 部署到 Cloud Run
echo "☁️  部署到 Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 60 \
    --max-instances 10

# 取得服務 URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "
✅ 部署完成！
服務 URL: $SERVICE_URL
健康檢查: $SERVICE_URL/health
"

# 測試健康檢查
echo "🏥 測試健康檢查..."
sleep 5
curl -s "$SERVICE_URL/health" || echo "⚠️  健康檢查失敗，請稍後再試"