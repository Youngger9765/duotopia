#!/bin/bash
set -e

echo "🚀 開始部署到 Staging 環境..."

# 設定變數
PROJECT_ID="duotopia-469413"
REGION="asia-east1"
SERVICE_NAME="duotopia-backend-staging"
FRONTEND_BUCKET="duotopia-frontend-staging"

# 確認 gcloud 配置
echo "📋 檢查 GCloud 配置..."
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "⚠️  切換到 Duotopia 專案..."
    gcloud config set project $PROJECT_ID
fi

# 建置後端 Docker 映像
echo "🐳 建置後端 Docker 映像..."
cd backend
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# 部署到 Cloud Run
echo "☁️  部署後端到 Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars "ENVIRONMENT=staging" \
    --set-env-vars "DATABASE_URL=$DATABASE_URL" \
    --set-env-vars "JWT_SECRET=$JWT_SECRET" \
    --set-env-vars "GOOGLE_CLIENT_ID=$GOOGLE_CLIENT_ID" \
    --set-env-vars "GOOGLE_CLIENT_SECRET=$GOOGLE_CLIENT_SECRET" \
    --set-env-vars "OPENAI_API_KEY=$OPENAI_API_KEY"

# 取得後端 URL
BACKEND_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "✅ 後端部署完成: $BACKEND_URL"

# 建置前端
echo "🔨 建置前端..."
cd ../frontend
echo "VITE_API_URL=$BACKEND_URL" > .env.production
npm run build

# 部署前端到 Cloud Storage
echo "📦 部署前端到 Cloud Storage..."
gsutil -m rsync -r -d dist/ gs://$FRONTEND_BUCKET/

# 設定 Cloud Storage 為網站
gsutil web set -m index.html -e 404.html gs://$FRONTEND_BUCKET

# 設定公開存取
gsutil iam ch allUsers:objectViewer gs://$FRONTEND_BUCKET

echo "✅ 前端部署完成: https://storage.googleapis.com/$FRONTEND_BUCKET/index.html"

# 測試健康檢查
echo "🏥 測試健康檢查..."
curl -s "$BACKEND_URL/health" | jq

echo "
🎉 部署完成！
後端: $BACKEND_URL
前端: https://storage.googleapis.com/$FRONTEND_BUCKET/index.html
"