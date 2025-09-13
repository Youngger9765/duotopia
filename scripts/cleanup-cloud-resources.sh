#!/bin/bash

# 🧹 Cloud Resources Cleanup Script
# 用於清理 Cloud Run revisions 和 Container Registry images

set -e

# 設定顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 設定變數
PROJECT_ID="duotopia-469413"
REGION="asia-east1"
REPOSITORY="cloud-run-source-deploy"

# 預設值 (單人開發優化)
KEEP_REVISIONS=1
KEEP_IMAGES=2

# 解析參數
while [[ $# -gt 0 ]]; do
  case $1 in
    --keep-revisions)
      KEEP_REVISIONS="$2"
      shift 2
      ;;
    --keep-images)
      KEEP_IMAGES="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --keep-revisions N  Keep N most recent revisions (default: 3)"
      echo "  --keep-images N     Keep N most recent images (default: 5)"
      echo "  --dry-run          Show what would be deleted without actually deleting"
      echo "  --help             Show this help message"
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      exit 1
      ;;
  esac
done

echo -e "${BLUE}🧹 Cloud Resources Cleanup Script${NC}"
echo -e "${BLUE}=================================${NC}"
echo ""

# 檢查 gcloud 登入狀態
echo -e "${YELLOW}🔐 Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
  echo -e "${RED}❌ Not authenticated. Please run: gcloud auth login${NC}"
  exit 1
fi

# 確認專案
CURRENT_PROJECT=$(gcloud config get-value project)
if [ "$CURRENT_PROJECT" != "$PROJECT_ID" ]; then
  echo -e "${YELLOW}⚠️  Current project: $CURRENT_PROJECT${NC}"
  echo -e "${YELLOW}   Switching to: $PROJECT_ID${NC}"
  gcloud config set project $PROJECT_ID
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"
echo ""

# 函數：清理 Cloud Run revisions
cleanup_revisions() {
  local SERVICE=$1
  local SERVICE_NAME=$2

  echo -e "${BLUE}🔍 Checking $SERVICE_NAME revisions...${NC}"

  # 獲取所有 revisions
  REVISIONS=$(gcloud run revisions list \
    --service=$SERVICE \
    --region=$REGION \
    --format="value(name)" \
    --sort-by="~creationTimestamp" 2>/dev/null || echo "")

  if [ -z "$REVISIONS" ]; then
    echo -e "${YELLOW}⚠️  No revisions found for $SERVICE_NAME${NC}"
    return
  fi

  TOTAL=$(echo "$REVISIONS" | wc -l)
  echo -e "📊 Total revisions: ${YELLOW}$TOTAL${NC}"

  if [ $TOTAL -gt $KEEP_REVISIONS ]; then
    TO_DELETE=$(echo "$REVISIONS" | tail -n +$((KEEP_REVISIONS + 1)))
    DELETE_COUNT=$(echo "$TO_DELETE" | wc -l)

    echo -e "${YELLOW}🗑️  Will delete $DELETE_COUNT old revisions${NC}"

    if [ "$DRY_RUN" = true ]; then
      echo -e "${BLUE}[DRY RUN] Would delete:${NC}"
      echo "$TO_DELETE" | head -10
      if [ $DELETE_COUNT -gt 10 ]; then
        echo "... and $((DELETE_COUNT - 10)) more"
      fi
    else
      for REVISION in $TO_DELETE; do
        echo -n "  Deleting: $REVISION... "
        if gcloud run revisions delete $REVISION --region=$REGION --quiet 2>/dev/null; then
          echo -e "${GREEN}✓${NC}"
        else
          echo -e "${RED}✗${NC}"
        fi
      done
      echo -e "${GREEN}✅ $SERVICE_NAME cleanup complete! Deleted $DELETE_COUNT revisions${NC}"
    fi
  else
    echo -e "${GREEN}✅ No cleanup needed. Only $TOTAL revisions exist.${NC}"
  fi
  echo ""
}

# 函數：清理 Container Registry images
cleanup_images() {
  local IMAGE_NAME=$1
  local SERVICE_NAME=$2

  echo -e "${BLUE}🐳 Checking $SERVICE_NAME container images...${NC}"

  # 檢查 repository 是否存在
  if ! gcloud artifacts repositories describe $REPOSITORY --location=$REGION > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Repository $REPOSITORY not found${NC}"
    return
  fi

  # 列出所有 images
  IMAGES=$(gcloud artifacts docker images list \
    $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME \
    --format="value(version)" \
    --sort-by="~createTime" 2>/dev/null || echo "")

  if [ -z "$IMAGES" ]; then
    echo -e "${YELLOW}⚠️  No images found for $SERVICE_NAME${NC}"
    return
  fi

  TOTAL=$(echo "$IMAGES" | wc -l)
  echo -e "📊 Total images: ${YELLOW}$TOTAL${NC}"

  if [ $TOTAL -gt $KEEP_IMAGES ]; then
    TO_DELETE=$(echo "$IMAGES" | tail -n +$((KEEP_IMAGES + 1)))
    DELETE_COUNT=$(echo "$TO_DELETE" | wc -l)

    echo -e "${YELLOW}🗑️  Will delete $DELETE_COUNT old images${NC}"

    if [ "$DRY_RUN" = true ]; then
      echo -e "${BLUE}[DRY RUN] Would delete:${NC}"
      echo "$TO_DELETE" | head -10
      if [ $DELETE_COUNT -gt 10 ]; then
        echo "... and $((DELETE_COUNT - 10)) more"
      fi
    else
      for VERSION in $TO_DELETE; do
        echo -n "  Deleting: $VERSION... "
        if gcloud artifacts docker images delete \
          $REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME:$VERSION \
          --quiet 2>/dev/null; then
          echo -e "${GREEN}✓${NC}"
        else
          echo -e "${RED}✗${NC}"
        fi
      done
      echo -e "${GREEN}✅ $SERVICE_NAME images cleanup complete!${NC}"
    fi
  else
    echo -e "${GREEN}✅ No cleanup needed. Only $TOTAL images exist.${NC}"
  fi
  echo ""
}

# 顯示設定
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Keep Revisions: ${YELLOW}$KEEP_REVISIONS${NC}"
echo -e "  Keep Images: ${YELLOW}$KEEP_IMAGES${NC}"
if [ "$DRY_RUN" = true ]; then
  echo -e "  Mode: ${YELLOW}DRY RUN (no actual deletion)${NC}"
fi
echo ""

# 清理 Cloud Run revisions
echo -e "${BLUE}═══ Cloud Run Revisions Cleanup ═══${NC}"
echo ""
cleanup_revisions "duotopia-staging-backend" "Backend"
cleanup_revisions "duotopia-staging-frontend" "Frontend"

# 清理 Container Registry images
echo -e "${BLUE}═══ Container Registry Cleanup ═══${NC}"
echo ""
cleanup_images "duotopia-staging-backend" "Backend"
cleanup_images "duotopia-staging-frontend" "Frontend"

# 總結
echo -e "${BLUE}═══ Cleanup Summary ═══${NC}"
echo -e "${GREEN}✅ All cleanup tasks completed!${NC}"
echo ""
echo -e "${BLUE}💡 Tips:${NC}"
echo -e "  • Run with --dry-run to preview changes"
echo -e "  • Adjust --keep-revisions and --keep-images as needed"
echo -e "  • This script runs automatically every day at 2 AM via GitHub Actions"
echo ""
echo -e "${YELLOW}💰 Cost Savings:${NC}"
echo -e "  • Reduced Cloud Run idle instances"
echo -e "  • Freed up container registry storage"
echo -e "  • Lower monthly bills!"
