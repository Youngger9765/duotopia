#!/bin/bash
set -e

echo "🔐 自動設定 GitHub Secrets..."

# 已知的值
PROJECT_ID="duotopia-469413"
PROJECT_NUMBER="206313737181"
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
WIF_SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

# 設定 WIF secrets
echo "設定 WIF_PROVIDER..."
gh secret set WIF_PROVIDER --body "$WIF_PROVIDER"

echo "設定 WIF_SERVICE_ACCOUNT..."
gh secret set WIF_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT"

echo ""
echo "✅ WIF Secrets 已設定完成！"
echo ""
echo "⚠️  您還需要手動設定以下 secrets："
echo "1. GOOGLE_CLIENT_ID - 從 Google Cloud Console 獲取"
echo "2. GOOGLE_CLIENT_SECRET - 從 Google Cloud Console 獲取"
echo ""
echo "使用以下命令設定："
echo "gh secret set GOOGLE_CLIENT_ID --body 'your-client-id'"
echo "gh secret set GOOGLE_CLIENT_SECRET --body 'your-client-secret'"
echo ""
echo "查看所有 secrets："
gh secret list