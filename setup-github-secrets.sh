#!/bin/bash
set -e

echo "🔐 設定 GitHub Secrets..."

# 檢查是否在正確的 repository
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📍 Repository: $REPO"

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "\n${YELLOW}請準備以下資訊：${NC}"
echo "1. Google Cloud Project Number (可從 GCP Console 查看)"
echo "2. Database URL (PostgreSQL 連接字串)"
echo "3. JWT Secret (隨機字串)"
echo "4. Google OAuth Client ID & Secret"
echo "5. OpenAI API Key"
echo ""

# 設定 Workload Identity Federation 相關
echo -e "\n${GREEN}設定 Workload Identity Federation...${NC}"
read -p "請輸入 GCP Project ID [duotopia-469413]: " PROJECT_ID
PROJECT_ID=${PROJECT_ID:-duotopia-469413}

read -p "請輸入 GCP Project Number: " PROJECT_NUMBER

# 建構 WIF Provider 和 Service Account
WIF_PROVIDER="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-actions/providers/github"
WIF_SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "設定 WIF_PROVIDER..."
gh secret set WIF_PROVIDER --body "$WIF_PROVIDER"

echo "設定 WIF_SERVICE_ACCOUNT..."
gh secret set WIF_SERVICE_ACCOUNT --body "$WIF_SERVICE_ACCOUNT"

# 設定應用程式 secrets
echo -e "\n${GREEN}設定應用程式 Secrets...${NC}"

# Database URL
echo -e "\n${YELLOW}Database URL 格式範例：${NC}"
echo "postgresql://username:password@host:port/database"
read -p "請輸入 DATABASE_URL: " DATABASE_URL
gh secret set DATABASE_URL --body "$DATABASE_URL"

# JWT Secret
echo -e "\n${YELLOW}JWT Secret (建議使用隨機字串)${NC}"
read -p "請輸入 JWT_SECRET (按 Enter 自動生成): " JWT_SECRET
if [ -z "$JWT_SECRET" ]; then
    JWT_SECRET=$(openssl rand -base64 32)
    echo "已生成 JWT_SECRET: $JWT_SECRET"
fi
gh secret set JWT_SECRET --body "$JWT_SECRET"

# Google OAuth
echo -e "\n${YELLOW}Google OAuth 設定${NC}"
read -p "請輸入 GOOGLE_CLIENT_ID: " GOOGLE_CLIENT_ID
gh secret set GOOGLE_CLIENT_ID --body "$GOOGLE_CLIENT_ID"

read -p "請輸入 GOOGLE_CLIENT_SECRET: " GOOGLE_CLIENT_SECRET
gh secret set GOOGLE_CLIENT_SECRET --body "$GOOGLE_CLIENT_SECRET"

# OpenAI API Key
echo -e "\n${YELLOW}OpenAI API Key${NC}"
read -p "請輸入 OPENAI_API_KEY: " OPENAI_API_KEY
gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY"

echo -e "\n${GREEN}✅ Secrets 設定完成！${NC}"
echo ""
echo "已設定的 Secrets："
gh secret list

echo -e "\n${YELLOW}下一步：${NC}"
echo "1. 執行 setup-workload-identity.sh 設定 GCP Workload Identity"
echo "2. 推送程式碼到 staging 分支測試部署"