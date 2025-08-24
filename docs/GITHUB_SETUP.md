# 🚀 GitHub Actions 設置指南

本文件說明如何在 GitHub 上設置 CI/CD pipeline 所需的 Secrets 和環境變數。

## 📋 必需的 GitHub Secrets

請在 GitHub 儲存庫的 Settings → Secrets and variables → Actions 中添加以下 secrets：

### 1. Google Cloud Platform 相關
```yaml
WIF_PROVIDER: projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
WIF_SERVICE_ACCOUNT: duotopia-github-actions@duotopia-469413.iam.gserviceaccount.com
```

### 2. 資料庫相關
```yaml
DB_PASSWORD: your-secure-database-password
DATABASE_URL: postgresql://user:password@host:5432/dbname
```

### 3. 應用程式密鑰
```yaml
JWT_SECRET: your-super-secret-jwt-key-minimum-32-characters
SECRET_KEY: your-secret-key-for-encryption
```

### 4. 第三方服務 API Keys
```yaml
GOOGLE_CLIENT_ID: your-google-oauth-client-id
GOOGLE_CLIENT_SECRET: your-google-oauth-client-secret
OPENAI_API_KEY: sk-your-openai-api-key
SENDGRID_API_KEY: SG.your-sendgrid-api-key
```

### 5. 通知相關（選用）
```yaml
SLACK_WEBHOOK: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🔧 設置步驟

### Step 1: 建立 Workload Identity Federation

```bash
# 建立 Workload Identity Pool
gcloud iam workload-identity-pools create github-pool \
    --location="global" \
    --display-name="GitHub Actions Pool"

# 建立 Provider
gcloud iam workload-identity-pools providers create-oidc github-provider \
    --location="global" \
    --workload-identity-pool="github-pool" \
    --display-name="GitHub Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.aud=assertion.aud,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# 授予權限
gcloud projects add-iam-policy-binding duotopia-469413 \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_GITHUB_ORG/duotopia" \
    --role="roles/cloudrun.developer"
```

### Step 2: 建立 Service Account

```bash
# 建立 Service Account
gcloud iam service-accounts create duotopia-github-actions \
    --display-name="GitHub Actions Service Account"

# 授予必要權限
gcloud projects add-iam-policy-binding duotopia-469413 \
    --member="serviceAccount:duotopia-github-actions@duotopia-469413.iam.gserviceaccount.com" \
    --role="roles/cloudrun.admin"

gcloud projects add-iam-policy-binding duotopia-469413 \
    --member="serviceAccount:duotopia-github-actions@duotopia-469413.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"
```

### Step 3: 在 GitHub 設置 Secrets

1. 前往你的 GitHub 儲存庫
2. 點擊 **Settings** → **Secrets and variables** → **Actions**
3. 點擊 **New repository secret**
4. 逐一添加上述所有 secrets

## 📊 驗證設置

### 測試 CI Pipeline

1. 建立一個新的分支：
```bash
git checkout -b test-ci
```

2. 做一個小改動：
```bash
echo "# Test CI" >> README.md
git add README.md
git commit -m "Test CI pipeline"
git push origin test-ci
```

3. 建立 Pull Request 並檢查 Actions 是否成功執行

### 檢查 Badge 狀態

在 README.md 中添加狀態徽章：

```markdown
![Test CI](https://github.com/YOUR_ORG/duotopia/workflows/Test%20CI/badge.svg)
![Deploy](https://github.com/YOUR_ORG/duotopia/workflows/Deploy%20to%20GCP/badge.svg)
```

## 🔐 安全注意事項

1. **定期輪換密鑰**：建議每 3-6 個月更新一次 secrets
2. **最小權限原則**：Service Account 只授予必要的權限
3. **環境分離**：生產環境和測試環境使用不同的 secrets
4. **審計日誌**：定期檢查 GitHub Actions 和 GCP 的審計日誌

## 🆘 疑難排解

### 常見錯誤

1. **Workload Identity 認證失敗**
   - 檢查 WIF_PROVIDER 格式是否正確
   - 確認 repository 名稱與設置相符

2. **Docker push 失敗**
   - 確認 Artifact Registry API 已啟用
   - 檢查 Service Account 權限

3. **Cloud Run 部署失敗**
   - 確認所有必需的環境變數都已設置
   - 檢查 Cloud SQL 連線設定

### 除錯指令

```bash
# 檢查 Service Account 權限
gcloud projects get-iam-policy duotopia-469413 \
    --flatten="bindings[].members" \
    --format="table(bindings.role)" \
    --filter="bindings.members:duotopia-github-actions"

# 檢查 Workload Identity 設定
gcloud iam workload-identity-pools providers describe github-provider \
    --workload-identity-pool="github-pool" \
    --location="global"
```

## 📚 參考資源

- [GitHub Actions 文檔](https://docs.github.com/en/actions)
- [Google Cloud Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)
- [Cloud Run 部署指南](https://cloud.google.com/run/docs/deploying)

---

完成以上設置後，你的 CI/CD pipeline 就可以正常運作了！🎉