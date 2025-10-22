#!/bin/bash
# Cloud Scheduler 快速設定腳本
# 用途：設定 Cloud Run 環境變數（CRON_SECRET）

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Cloud Scheduler 快速設定"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 檢查 gcloud 權限
echo "檢查 GCP 配置..."
PROJECT_ID=$(gcloud config get-value project)
ACCOUNT=$(gcloud config get-value account)

echo "✅ Project: $PROJECT_ID"
echo "✅ Account: $ACCOUNT"
echo ""

# CRON_SECRET 值（從上面生成的）
STAGING_CRON_SECRET="NICb1+SnYez3tJm00b70dRzas0E/VwMJQfeh1wqtlYM="
PRODUCTION_CRON_SECRET="7gwU8zuaSzDQbEgZrOK9tNbkQj1+ByVNts9H32SPz5s="

# Backend URLs
STAGING_BACKEND_URL="https://duotopia-staging-backend-b2ovkkgl6a-de.a.run.app"
PRODUCTION_BACKEND_URL="https://duotopia-production-backend-b2ovkkgl6a-de.a.run.app"

echo "📝 準備設定以下環境變數："
echo ""
echo "Staging:"
echo "  Service: duotopia-staging-backend"
echo "  CRON_SECRET: ${STAGING_CRON_SECRET:0:20}..."
echo ""
echo "Production:"
echo "  Service: duotopia-production-backend"
echo "  CRON_SECRET: ${PRODUCTION_CRON_SECRET:0:20}..."
echo ""

read -p "確認要繼續嗎？(y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 取消設定"
    exit 1
fi

echo ""
echo "🚀 設定 Staging 環境變數..."
gcloud run services update duotopia-staging-backend \
  --update-env-vars CRON_SECRET="$STAGING_CRON_SECRET" \
  --region asia-east1

echo ""
echo "🚀 設定 Production 環境變數..."
gcloud run services update duotopia-production-backend \
  --update-env-vars CRON_SECRET="$PRODUCTION_CRON_SECRET" \
  --region asia-east1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Cloud Run 環境變數設定完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 接下來請設定 GitHub Secrets："
echo ""
echo "前往: https://github.com/Youngger9765/duotopia/settings/secrets/actions"
echo ""
echo "新增以下 4 個 secrets："
echo ""
echo "1. STAGING_BACKEND_URL"
echo "   值: $STAGING_BACKEND_URL"
echo ""
echo "2. STAGING_CRON_SECRET"
echo "   值: $STAGING_CRON_SECRET"
echo ""
echo "3. PRODUCTION_BACKEND_URL"
echo "   值: $PRODUCTION_BACKEND_URL"
echo ""
echo "4. PRODUCTION_CRON_SECRET"
echo "   值: $PRODUCTION_CRON_SECRET"
echo ""
echo "💡 設定完成後，前往 GitHub Actions 手動觸發 'Setup Cloud Scheduler' workflow"
echo ""
