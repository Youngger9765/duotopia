# Duotopia 部署說明

## 🚀 部署總結

### 環境資訊

#### Production 環境
- **前端 URL**: https://duotopia-frontend-qchnzlfpda-de.a.run.app
- **後端 API**: https://duotopia-backend-qchnzlfpda-de.a.run.app
- **資料庫**: Cloud SQL PostgreSQL (35.201.201.210)

#### Staging 環境
- **前端 URL**: https://duotopia-frontend-staging-206313737181.asia-east1.run.app
- **後端 API**: https://duotopia-backend-staging-206313737181.asia-east1.run.app
- **資料庫**: Cloud SQL PostgreSQL (35.221.172.134)

### 基礎設施

1. **Google Cloud Platform 資源**
   - Project ID: `duotopia-469413`
   - Region: `asia-east1`
   - Cloud SQL: 
     - Production: `duotopia-db-production`
     - Staging: `duotopia-db-staging`
   - Storage Buckets:
     - `duotopia-469413-uploads` - 檔案上傳
     - `duotopia-469413-static` - 靜態資源
     - `duotopia-469413-terraform-state` - Terraform 狀態

2. **Artifact Registry**
   - Repository: `asia-east1-docker.pkg.dev/duotopia-469413/duotopia`
   - Images:
     - `backend:latest`
     - `frontend:latest`

## 🔧 GCloud 配置

### 確保使用正確的專案
部署前請務必確認 gcloud 配置：

```bash
# 切換到 Duotopia 配置
gcloud config configurations activate duotopia

# 驗證當前配置
gcloud config list
# 應該顯示：
# account = purpleice9765@msn.com  
# project = duotopia-469413

# 或直接設定專案
gcloud config set project duotopia-469413
```

### 🛡️ 使用隔離環境避免專案干擾
如果你同時開發多個 GCP 專案，使用隔離環境：

```bash
# 設定 Duotopia 專屬環境
export CLOUDSDK_CONFIG=$HOME/.gcloud-duotopia
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.11

# 之後所有 gcloud 指令都會使用這個隔離環境
gcloud run deploy ...  # 會使用 duotopia 的設定
```

## 🔧 CI/CD 設定

### GitHub Actions

已設定自動部署 workflows：
- `.github/workflows/deploy-production.yml` - 主分支自動部署到 production
- `.github/workflows/deploy-staging.yml` - staging/develop 分支自動部署到 staging

### 環境變數管理方式

1. **Terraform** 負責建立和管理 Secret Manager 中的 secrets
2. **Cloud Run** 從 Secret Manager 引用這些 secrets（使用 secret references）
3. **GitHub Actions** 不應該直接設定環境變數，而是讓 Cloud Run 從 Secret Manager 讀取

#### Secret Manager 中的 Secrets
- `jwt-secret` - JWT 簽署密鑰
- `google-client-id` - Google OAuth Client ID
- `google-client-secret` - Google OAuth Client Secret
- `openai-api-key` - OpenAI API Key（如需要）
- `sendgrid-api-key` - SendGrid API Key（如需要）

### GitHub Secrets 設定

請在 GitHub repository 設定以下 secret：

```bash
# 將服務帳號金鑰內容複製到 GitHub Secrets
cat ~/github-actions-key.json
```

在 GitHub 上：
1. 進入 Settings > Secrets and variables > Actions
2. 新增 secret: `GCP_SA_KEY`
3. 貼上服務帳號金鑰的完整 JSON 內容

## 📝 手動部署指令

### 部署後端
```bash
# 建立映像檔
docker build -t asia-east1-docker.pkg.dev/duotopia-469413/duotopia/backend:latest -f backend/Dockerfile backend/

# 推送映像檔
docker push asia-east1-docker.pkg.dev/duotopia-469413/duotopia/backend:latest

# 部署到 Cloud Run
gcloud run deploy duotopia-backend \
  --image asia-east1-docker.pkg.dev/duotopia-469413/duotopia/backend:latest \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated
```

### 部署前端
```bash
# 建立映像檔
docker build -t asia-east1-docker.pkg.dev/duotopia-469413/duotopia/frontend:latest -f frontend/Dockerfile frontend/

# 推送映像檔
docker push asia-east1-docker.pkg.dev/duotopia-469413/duotopia/frontend:latest

# 部署到 Cloud Run
gcloud run deploy duotopia-frontend \
  --image asia-east1-docker.pkg.dev/duotopia-469413/duotopia/frontend:latest \
  --region asia-east1 \
  --platform managed \
  --allow-unauthenticated
```

## 🔐 資料庫連線

### 連線資訊
- Host: `35.201.201.210`
- Port: `5432`
- Database: `duotopia`
- Username: 查看 terraform.tfvars
- Password: 查看 terraform.tfvars

### 連線字串
```
postgresql://[username]:[password]@35.201.201.210:5432/duotopia
```

## 🛠️ Terraform 管理

### 更新基礎設施
```bash
cd terraform
terraform plan
terraform apply
```

### 重要檔案
- `terraform/terraform.tfvars` - 環境變數設定（包含 secrets 的實際值）
- `terraform/secrets.tf` - Secret Manager 資源定義
- `~/terraform-key.json` - Terraform 服務帳號金鑰
- `~/github-actions-key.json` - GitHub Actions 服務帳號金鑰

### 更新 Secrets
當需要更新密鑰時：
1. 修改 `terraform/terraform.tfvars` 中的值
2. 執行 `terraform apply` 更新 Secret Manager
3. Cloud Run 會自動使用新的 secret 版本

## ⚠️ 注意事項

1. **服務帳號金鑰安全**
   - 不要將金鑰檔案提交到版本控制
   - 定期輪換金鑰
   - 使用最小權限原則

2. **成本控制**
   - Cloud SQL: 約 $10-15/月
   - Cloud Run: 按使用量計費
   - Storage: 按使用量計費

3. **監控與日誌**
   - Cloud Logging: 查看應用程式日誌
   - Cloud Monitoring: 監控服務健康狀態

## 🚨 故障排除

### Cloud Run 部署失敗
```bash
# 檢查日誌
gcloud run logs read duotopia-backend --limit=50

# 檢查服務狀態
gcloud run services describe duotopia-backend --region=asia-east1
```

### 資料庫連線問題
```bash
# 測試連線
psql postgresql://[username]:[password]@35.201.201.210:5432/duotopia

# 檢查 Cloud SQL 狀態
gcloud sql instances describe duotopia-db-production
```

## 📞 支援

如有問題，請檢查：
1. GitHub Actions 執行日誌
2. Cloud Logging 錯誤訊息
3. Cloud SQL 連線狀態