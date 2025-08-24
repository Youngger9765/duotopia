#!/bin/bash
set -e

echo "🔐 設定缺少的 GitHub Secrets..."

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 檢查現有 secrets
echo "現有的 Secrets："
gh secret list

echo -e "\n${YELLOW}需要設定以下 Secrets：${NC}"
echo "- WIF_PROVIDER"
echo "- WIF_SERVICE_ACCOUNT"
echo "- GOOGLE_CLIENT_ID"
echo "- GOOGLE_CLIENT_SECRET"
echo "- OPENAI_API_KEY"

# 快速設定 WIF（使用預設值）
echo -e "\n${GREEN}設定 Workload Identity Federation...${NC}"
PROJECT_ID="duotopia-469413"
read -p "請輸入 GCP Project Number: " PROJECT_NUMBER

WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
WIF_SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "設定 WIF_PROVIDER..."
gh secret set WIF_PROVIDER --body "$WIF_PROVIDER"

echo "設定 WIF_SERVICE_ACCOUNT..."
gh secret set WIF_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT"

# Google OAuth
echo -e "\n${GREEN}設定 Google OAuth...${NC}"
read -p "請輸入 GOOGLE_CLIENT_ID: " GOOGLE_CLIENT_ID
gh secret set GOOGLE_CLIENT_ID --body "$GOOGLE_CLIENT_ID"

read -p "請輸入 GOOGLE_CLIENT_SECRET: " GOOGLE_CLIENT_SECRET
gh secret set GOOGLE_CLIENT_SECRET --body "$GOOGLE_CLIENT_SECRET"

# OpenAI API Key
echo -e "\n${GREEN}設定 OpenAI API Key...${NC}"
read -p "請輸入 OPENAI_API_KEY: " OPENAI_API_KEY
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"

echo -e "\n${GREEN}✅ 完成！${NC}"
echo "更新後的 Secrets："
gh secret list