# GitHub Actions CI/CD 設定

## 概述

此專案使用 GitHub Actions 進行自動化測試和部署：
- **Staging 環境**：推送到 `staging` 分支時自動部署
- **Production 環境**：推送到 `main` 分支時自動部署

## 必要的 GitHub Secrets

在 GitHub Repository Settings > Secrets and variables > Actions 中設定以下 secrets：

### Google Cloud 認證
- `WIF_PROVIDER`: Workload Identity Federation provider (格式: `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_NAME/providers/PROVIDER_NAME`)
- `WIF_SERVICE_ACCOUNT`: Service account email (例如: `github-actions@PROJECT_ID.iam.gserviceaccount.com`)

### 應用程式環境變數
- `DATABASE_URL`: PostgreSQL 連接字串
- `JWT_SECRET`: JWT 簽名密鑰
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `OPENAI_API_KEY`: OpenAI API 金鑰

## 設定 Workload Identity Federation

1. 建立 Workload Identity Pool：
```bash
gcloud iam workload-identity-pools create github-actions \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

2. 建立 Provider：
```bash
gcloud iam workload-identity-pools providers create-oidc github \
  --location="global" \
  --workload-identity-pool="github-actions" \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

3. 建立 Service Account：
```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"
```

4. 授予必要權限：
```bash
# Cloud Run 部署權限
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Container Registry 權限
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Service Account 使用權限
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

5. 設定 Workload Identity 綁定：
```bash
gcloud iam service-accounts add-iam-policy-binding \
  github-actions@PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions/attribute.repository/YOUR_GITHUB_USERNAME/REPOSITORY_NAME"
```

## 工作流程說明

### deploy-staging.yml
- 觸發條件：推送到 `staging` 分支
- 執行步驟：
  1. 執行測試（後端 + 前端）
  2. 建置並部署後端到 Cloud Run
  3. 建置並部署前端到 Cloud Storage
  4. 健康檢查驗證

### deploy-production.yml
- 觸發條件：推送到 `main` 分支
- 需要手動審核（environment protection）
- 額外功能：
  - 更高的記憶體配置 (1Gi)
  - 最小實例數設定 (min-instances: 1)
  - CDN 快取清除

## 手動觸發部署

兩個工作流程都支援手動觸發：
1. 前往 Actions 頁面
2. 選擇對應的工作流程
3. 點擊 "Run workflow"
4. 選擇分支並執行

## 疑難排解

### 常見問題

1. **認證失敗**
   - 檢查 WIF_PROVIDER 和 WIF_SERVICE_ACCOUNT 是否正確設定
   - 確認 Service Account 有正確的權限

2. **Docker 建置失敗**
   - 檢查 Dockerfile.backend 是否正確
   - 確認所有必要檔案都已提交

3. **部署失敗**
   - 檢查 Cloud Run 服務配額
   - 確認環境變數都已正確設定

### 查看日誌

```bash
# Cloud Run 日誌
gcloud run logs read SERVICE_NAME --region=asia-east1

# GitHub Actions 日誌
# 前往 GitHub Actions 頁面查看詳細執行記錄
```