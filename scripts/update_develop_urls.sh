#!/bin/bash
# Update Develop Environment URLs after first deployment
# 在首次部署完成後，自動取得並更新真實的 Cloud Run URLs

set -e

REPO="Youngger9765/duotopia"
REGION="asia-east1"

echo "=========================================="
echo "🔄 Update Develop URLs"
echo "=========================================="
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) 未安裝！"
    echo "   請執行: brew install gh"
    exit 1
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Google Cloud CLI (gcloud) 未安裝！"
    echo "   請執行: brew install --cask google-cloud-sdk"
    exit 1
fi

echo "📡 取得 Cloud Run 服務 URLs..."
echo ""

# Get Backend URL
echo "1/2 取得 Backend URL..."
BACKEND_URL=$(gcloud run services describe duotopia-backend-develop \
  --region $REGION \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend service 尚未部署！"
    echo "   請先推送到 develop branch 觸發部署："
    echo "   git push origin develop"
    exit 1
fi

echo "   ✅ Backend URL: $BACKEND_URL"

# Get Frontend URL
echo "2/2 取得 Frontend URL..."
FRONTEND_URL=$(gcloud run services describe duotopia-frontend-develop \
  --region $REGION \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [ -z "$FRONTEND_URL" ]; then
    echo "❌ Frontend service 尚未部署！"
    echo "   請等待 GitHub Actions 完成部署"
    exit 1
fi

echo "   ✅ Frontend URL: $FRONTEND_URL"
echo ""

echo "=========================================="
echo "📝 更新 GitHub Secrets"
echo "=========================================="
echo ""

# Update Backend URL
echo "1/2 更新 DEVELOP_BACKEND_URL..."
echo "$BACKEND_URL" | gh secret set DEVELOP_BACKEND_URL --repo "$REPO"
echo "   ✅ 已更新"

# Update Frontend URL
echo "2/2 更新 DEVELOP_FRONTEND_URL..."
echo "$FRONTEND_URL" | gh secret set DEVELOP_FRONTEND_URL --repo "$REPO"
echo "   ✅ 已更新"

echo ""
echo "=========================================="
echo "✅ URLs 更新完成！"
echo "=========================================="
echo ""
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"
echo ""
echo "下一步："
echo "  1. 測試 Backend 健康檢查："
echo "     curl $BACKEND_URL/api/health | jq '.'"
echo ""
echo "  2. 打開 Frontend 頁面："
echo "     open $FRONTEND_URL"
echo ""
echo "  3. 如果需要觸發重新部署（使用新的 URLs）："
echo "     git commit --allow-empty -m 'chore: trigger redeploy with updated URLs'"
echo "     git push origin develop"
echo ""
