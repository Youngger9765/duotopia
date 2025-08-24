#!/bin/bash
set -e

echo "🔐 設定 Google Cloud Workload Identity Federation..."

# 預設值
PROJECT_ID="${PROJECT_ID:-duotopia-469413}"
POOL_NAME="github-actions"
PROVIDER_NAME="github"
SERVICE_ACCOUNT_NAME="github-actions"
REPO_NAME="Youngger9765/duotopia"

# 顏色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}使用以下設定：${NC}"
echo "Project ID: $PROJECT_ID"
echo "Repository: $REPO_NAME"
echo ""

# 確認 gcloud 設定
echo "檢查 gcloud 設定..."
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
    echo "切換到專案 $PROJECT_ID..."
    gcloud config set project $PROJECT_ID
fi

# 獲取 Project Number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "Project Number: $PROJECT_NUMBER"

# 1. 建立 Workload Identity Pool
echo -e "\n${GREEN}1. 建立 Workload Identity Pool...${NC}"
gcloud iam workload-identity-pools create $POOL_NAME \
    --location="global" \
    --display-name="GitHub Actions Pool" \
    --description="Pool for GitHub Actions authentication" \
    || echo "Pool 可能已存在，繼續..."

# 2. 建立 OIDC Provider
echo -e "\n${GREEN}2. 建立 OIDC Provider...${NC}"
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_NAME \
    --location="global" \
    --workload-identity-pool="$POOL_NAME" \
    --display-name="GitHub provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
    --attribute-condition="assertion.repository=='$REPO_NAME'" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    || echo "Provider 可能已存在，繼續..."

# 3. 建立 Service Account
echo -e "\n${GREEN}3. 建立 Service Account...${NC}"
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
    --display-name="GitHub Actions Service Account" \
    --description="Service account for GitHub Actions CI/CD" \
    || echo "Service Account 可能已存在，繼續..."

# 4. 授予必要權限
echo -e "\n${GREEN}4. 授予 Service Account 權限...${NC}"

# Cloud Run Admin
echo "授予 Cloud Run Admin 權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/run.admin"

# Storage Admin (for Container Registry and Cloud Storage)
echo "授予 Storage Admin 權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Service Account User
echo "授予 Service Account User 權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Cloud Build Editor (for building containers)
echo "授予 Cloud Build Editor 權限..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudbuild.builds.editor"

# 5. 設定 Workload Identity 綁定
echo -e "\n${GREEN}5. 設定 Workload Identity 綁定...${NC}"
gcloud iam service-accounts add-iam-policy-binding \
    "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/attribute.repository/${REPO_NAME}"

# 輸出資訊
echo -e "\n${GREEN}✅ Workload Identity Federation 設定完成！${NC}"
echo ""
echo -e "${YELLOW}重要資訊（已自動設定到 GitHub Secrets）：${NC}"
echo "WIF_PROVIDER: projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_NAME}/providers/${PROVIDER_NAME}"
echo "WIF_SERVICE_ACCOUNT: ${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo -e "\n${YELLOW}測試部署：${NC}"
echo "1. 確認所有 GitHub Secrets 已設定："
echo "   gh secret list"
echo ""
echo "2. 推送到 staging 分支："
echo "   git push origin staging"
echo ""
echo "3. 查看 GitHub Actions 執行狀況："
echo "   gh run list"
echo "   gh run watch"