#!/bin/bash

echo "🔐 設置 GitHub Secrets for Duotopia"
echo "=================================="

# 檢查是否在正確的目錄
if [ ! -f "package.json" ] || [ ! -d ".github" ]; then
    echo "❌ 請在 Duotopia 專案根目錄執行此腳本"
    exit 1
fi

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 檢查 gh 是否已安裝
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) 未安裝${NC}"
    echo "請先安裝: brew install gh"
    exit 1
fi

# 檢查是否已登入
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ 請先登入 GitHub${NC}"
    echo "執行: gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI 已就緒${NC}"
echo ""

# 顯示現有的 secrets
echo "📋 現有的 Secrets:"
gh secret list
echo ""

# 詢問是否要設置 GCP 相關 secrets
echo -e "${YELLOW}是否要設置 Google Cloud Platform 相關 secrets? (y/n)${NC}"
read -p "> " setup_gcp

if [ "$setup_gcp" = "y" ]; then
    echo "請提供以下資訊（如果沒有可以按 Enter 跳過）："
    
    read -p "WIF_PROVIDER (Workload Identity Federation Provider): " wif_provider
    if [ ! -z "$wif_provider" ]; then
        gh secret set WIF_PROVIDER --body "$wif_provider"
        echo -e "${GREEN}✅ WIF_PROVIDER 已設置${NC}"
    fi
    
    read -p "WIF_SERVICE_ACCOUNT (Service Account Email): " wif_sa
    if [ ! -z "$wif_sa" ]; then
        gh secret set WIF_SERVICE_ACCOUNT --body "$wif_sa"
        echo -e "${GREEN}✅ WIF_SERVICE_ACCOUNT 已設置${NC}"
    fi
    
    read -p "DB_PASSWORD (資料庫密碼): " db_password
    if [ ! -z "$db_password" ]; then
        gh secret set DB_PASSWORD --body "$db_password"
        echo -e "${GREEN}✅ DB_PASSWORD 已設置${NC}"
    fi
fi

# 詢問是否要設置 OAuth 相關 secrets
echo ""
echo -e "${YELLOW}是否要設置 Google OAuth 相關 secrets? (y/n)${NC}"
read -p "> " setup_oauth

if [ "$setup_oauth" = "y" ]; then
    read -p "GOOGLE_CLIENT_ID: " google_client_id
    if [ ! -z "$google_client_id" ]; then
        gh secret set GOOGLE_CLIENT_ID --body "$google_client_id"
        echo -e "${GREEN}✅ GOOGLE_CLIENT_ID 已設置${NC}"
    fi
    
    read -p "GOOGLE_CLIENT_SECRET: " google_client_secret
    if [ ! -z "$google_client_secret" ]; then
        gh secret set GOOGLE_CLIENT_SECRET --body "$google_client_secret"
        echo -e "${GREEN}✅ GOOGLE_CLIENT_SECRET 已設置${NC}"
    fi
fi

# 詢問是否要設置 API Keys
echo ""
echo -e "${YELLOW}是否要設置 API Keys? (y/n)${NC}"
read -p "> " setup_apis

if [ "$setup_apis" = "y" ]; then
    read -p "OPENAI_API_KEY (sk-...): " openai_key
    if [ ! -z "$openai_key" ]; then
        gh secret set OPENAI_API_KEY --body "$openai_key"
        echo -e "${GREEN}✅ OPENAI_API_KEY 已設置${NC}"
    fi
    
    read -p "SENDGRID_API_KEY (SG...): " sendgrid_key
    if [ ! -z "$sendgrid_key" ]; then
        gh secret set SENDGRID_API_KEY --body "$sendgrid_key"
        echo -e "${GREEN}✅ SENDGRID_API_KEY 已設置${NC}"
    fi
fi

# 顯示最終的 secrets 列表
echo ""
echo -e "${GREEN}📋 最終的 Secrets 列表:${NC}"
gh secret list

echo ""
echo -e "${GREEN}✅ GitHub Secrets 設置完成！${NC}"
echo ""
echo "下一步："
echo "1. 查看 GitHub Actions 運行狀態: gh run list"
echo "2. 查看特定運行的詳情: gh run view [run-id]"
echo "3. 在瀏覽器中查看: gh run view --web"
echo ""
echo "如果測試失敗，可能需要設置更多 secrets。"