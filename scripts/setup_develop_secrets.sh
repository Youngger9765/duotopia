#!/bin/bash
# Setup GitHub Secrets for Develop Environment
# 使用此腳本設定 develop 環境所需的 GitHub Secrets

set -e  # Exit on error

REPO="myduotopia/duotopia"

echo "=========================================="
echo "🔧 Develop Environment Secrets Setup"
echo "=========================================="
echo ""
echo "此腳本將設定 develop 環境所需的 GitHub Secrets。"
echo "Repository: $REPO"
echo ""
echo "需要設定的 Secrets："
echo "  1. DEVELOP_BACKEND_SERVICE   - Cloud Run backend service 名稱"
echo "  2. DEVELOP_FRONTEND_SERVICE  - Cloud Run frontend service 名稱"
echo "  3. DEVELOP_BACKEND_URL       - Backend URL"
echo "  4. DEVELOP_FRONTEND_URL      - Frontend URL"
echo "  5. DEVELOP_JWT_SECRET        - JWT 密鑰"
echo "  6. DEVELOP_CRON_SECRET       - Cron job 密鑰"
echo "  7. DEVELOP_ENABLE_PAYMENT    - 是否啟用付款功能"
echo ""
echo "⚠️  請確保已安裝 GitHub CLI (gh)"
echo "    安裝方式: brew install gh"
echo "    登入方式: gh auth login"
echo ""

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) 未安裝！"
    echo "   請執行: brew install gh"
    exit 1
fi

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "❌ 未登入 GitHub CLI！"
    echo "   請執行: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI 已就緒"
echo ""

# Generate random secrets
JWT_SECRET=$(openssl rand -hex 32)
CRON_SECRET=$(openssl rand -hex 32)

echo "=========================================="
echo "📝 設定 Secrets"
echo "=========================================="
echo ""

# Function to set secret
set_secret() {
    local name=$1
    local value=$2
    echo "Setting $name..."
    echo "$value" | gh secret set "$name" --repo "$REPO"
}

# 1. Backend Service Name
echo "1/7 設定 DEVELOP_BACKEND_SERVICE"
set_secret "DEVELOP_BACKEND_SERVICE" "duotopia-backend-develop"

# 2. Frontend Service Name
echo "2/7 設定 DEVELOP_FRONTEND_SERVICE"
set_secret "DEVELOP_FRONTEND_SERVICE" "duotopia-frontend-develop"

# 3. Backend URL (will be set after first deployment)
echo "3/7 設定 DEVELOP_BACKEND_URL (初始為空，首次部署後會自動更新)"
set_secret "DEVELOP_BACKEND_URL" "https://duotopia-backend-develop-placeholder.a.run.app"

# 4. Frontend URL (will be set after first deployment)
echo "4/7 設定 DEVELOP_FRONTEND_URL (初始為空，首次部署後會自動更新)"
set_secret "DEVELOP_FRONTEND_URL" "https://duotopia-frontend-develop-placeholder.a.run.app"

# 5. JWT Secret (auto-generated)
echo "5/7 設定 DEVELOP_JWT_SECRET (自動生成)"
set_secret "DEVELOP_JWT_SECRET" "$JWT_SECRET"

# 6. Cron Secret (auto-generated)
echo "6/7 設定 DEVELOP_CRON_SECRET (自動生成)"
set_secret "DEVELOP_CRON_SECRET" "$CRON_SECRET"

# 7. Enable Payment (default to true for testing)
echo "7/7 設定 DEVELOP_ENABLE_PAYMENT"
set_secret "DEVELOP_ENABLE_PAYMENT" "true"

echo ""
echo "=========================================="
echo "✅ 所有 Secrets 設定完成！"
echo "=========================================="
echo ""
echo "生成的密鑰："
echo "  JWT_SECRET:  $JWT_SECRET"
echo "  CRON_SECRET: $CRON_SECRET"
echo ""
echo "⚠️  請妥善保存這些密鑰！"
echo ""
echo "下一步："
echo "  1. 從 staging 創建 develop branch:"
echo "     git checkout staging"
echo "     git pull"
echo "     git checkout -b develop"
echo "     git push -u origin develop"
echo ""
echo "  2. 將 feature-sentence merge 到 develop:"
echo "     git checkout develop"
echo "     git merge feature-sentence"
echo "     git push origin develop"
echo ""
echo "  3. 等待 GitHub Actions 自動部署 develop 環境"
echo ""
echo "  4. 首次部署完成後，更新實際的 URL:"
echo "     gh secret set DEVELOP_BACKEND_URL --body 'https://[actual-backend-url]' --repo $REPO"
echo "     gh secret set DEVELOP_FRONTEND_URL --body 'https://[actual-frontend-url]' --repo $REPO"
echo ""
