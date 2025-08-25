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

## 🚀 部署檢查清單

### 部署前檢查

#### 1. 環境變數檢查
- [ ] 確認 `PORT` 設定正確（Cloud Run 使用 8080）
- [ ] 確認所有 API URL 使用環境變數，不是硬編碼
- [ ] 確認資料庫連線字串正確（不是 localhost）
- [ ] 確認所有密鑰都在 Secret Manager

#### 2. 程式碼檢查
```bash
# 檢查硬編碼的 URL
grep -r "localhost:[0-9]" frontend/src/
grep -r "http://localhost" frontend/src/

# 檢查錯誤的 import
grep -r "models_dual_system" backend/
grep -r "DualUser" backend/
```

#### 3. Docker 測試
```bash
# 本地測試 Cloud Run 環境
docker build -f Dockerfile.backend -t test-backend .
docker run -p 8080:8080 -e PORT=8080 test-backend

# 測試健康檢查
curl http://localhost:8080/health
```

### 部署中監控

#### 1. 即時監控部署
```bash
# 監控 GitHub Actions
gh run watch

# 查看部署日誌
gh run view --log
```

#### 2. Cloud Run 日誌
```bash
# 查看最新日誌
gcloud run logs read duotopia-backend-staging --limit=50

# 持續監控
gcloud run logs tail duotopia-backend-staging
```

### 部署後驗證

#### 1. API 健康檢查
```bash
# 後端健康檢查
curl https://[backend-url]/health

# API 端點測試
curl https://[backend-url]/api/auth/validate
```

#### 2. 前端功能測試
```python
# 使用 test_staging_api_call.py
python test_staging_api_call.py
```

#### 3. 完整流程測試
- [ ] 教師登入流程
- [ ] 學生登入流程
- [ ] 課程管理功能
- [ ] 作業派發功能

### 🔥 常見問題排查

#### 1. Container 無法啟動
- 檢查 PORT 環境變數
- 檢查 import 錯誤
- 檢查 requirements.txt

#### 2. API 呼叫失敗
- 檢查 CORS 設定
- 檢查環境變數是否正確傳遞
- 檢查 API URL 是否正確

#### 3. 資料庫連線失敗
- 檢查 DATABASE_URL 格式
- 檢查 Cloud SQL 權限
- 檢查網路連線

### 🛡️ 預防措施

#### 1. Git Hooks（已設定）
- pre-commit: TypeScript 檢查 + 建置測試
- pre-push: 完整測試套件

#### 2. CI/CD 改進（已實施）
- Docker 構建測試
- 健康檢查驗證
- 自動回滾機制

#### 3. 監控告警
- 設定 Cloud Monitoring
- 設定錯誤追蹤
- 設定 Email 通知（如需要）

### 📝 部署命令速查

```bash
# 手動部署
./scripts/deploy.sh

# 查看部署狀態
gh run list --workflow=deploy-staging.yml

# 回滾到上一版
gcloud run services update-traffic duotopia-backend-staging \
  --to-revisions=REVISION_NAME=100

# 查看所有版本
gcloud run revisions list --service=duotopia-backend-staging
```

### 🎯 部署黃金法則

1. **永遠不要跳過測試**
2. **每次部署後立即驗證**
3. **發現問題立即回滾**
4. **記錄所有變更**
5. **保持環境一致性**

## 🔥 部署錯誤反思與預防

### 常見部署錯誤模式

#### 1. 硬編碼 URL 錯誤
- **錯誤案例**：frontend auth.ts 中寫死 `http://localhost:8000`
- **症狀**：staging 環境前端無法連接後端
- **解決**：使用環境變數 `import.meta.env.VITE_API_URL`
- **預防**：git hooks 檢查硬編碼 URL

#### 2. PORT 配置錯誤  
- **錯誤案例**：Dockerfile 設定 `ENV PORT=8000`
- **症狀**：Cloud Run 容器無法啟動
- **解決**：改為 `ENV PORT=8080`
- **預防**：CI/CD 中加入 Docker 本地測試

#### 3. Import 路徑錯誤
- **錯誤案例**：`from models_dual_system import DualUser`
- **症狀**：後端容器啟動失敗
- **解決**：改為 `from models import User`
- **預防**：重構後全專案搜尋舊程式碼

### 系統性改進措施

#### 1. Git Hooks 自動檢查
```bash
# .githooks/pre-push
grep -r "localhost:[0-9]" frontend/src/ && exit 1
grep -r "models_dual_system" backend/ && exit 1
```

#### 2. CI/CD 流程強化
- **Docker 本地測試**：部署前測試容器是否能正常啟動
- **健康檢查重試**：5次重試機制，避免誤判
- **自動日誌輸出**：失敗時自動顯示最近 50 行日誌

#### 3. 監控 SOP
```bash
# 推送後立即執行
gh run watch                        # 即時監控
gh run view --log | grep ERROR      # 查看錯誤
gcloud run logs tail [service]     # 追蹤日誌
```

### 診斷決策樹

```
容器無法啟動？
├─ 檢查 PORT 環境變數
├─ 檢查 import 錯誤
├─ 檢查啟動時是否有資料庫連線
│  └─ main.py 頂層不能有 DB 操作
│  └─ lifespan 不能立即連資料庫
└─ 檢查 requirements.txt

API 呼叫失敗？
├─ 檢查環境變數是否正確
├─ 檢查 CORS 設定
└─ 檢查 API URL 格式

資料庫連線失敗？
├─ 檢查 DATABASE_URL（不能是 localhost）
├─ 檢查 Cloud SQL 權限
└─ 檢查網路設定
```

### 啟動時資料庫連線陷阱

#### 問題描述
Cloud Run 容器在啟動時如果立即嘗試連接資料庫，很可能會失敗，因為：
1. 環境變數可能還沒完全載入
2. 網路連線可能還沒建立
3. Cloud SQL proxy 可能還沒準備好

#### 常見錯誤
```python
# ❌ main.py 頂層
Base.metadata.create_all(bind=engine)

# ❌ 在 __init__ 就連接資料庫
class DatabaseInitializer:
    def __init__(self):
        self.db = SessionLocal()  # 立即連接！
```

#### 解決方案
1. 資料表建立交給 alembic migrations
2. 資料庫連線使用 FastAPI 的 Depends 機制（lazy loading）
3. 健康檢查端點可以測試連線，但要處理失敗情況

### 部署前必做清單
- [ ] 本地 Docker 測試：`docker run -p 8080:8080`
- [ ] 搜尋硬編碼：`grep -r "localhost"`
- [ ] 環境變數確認：檢查 .env.production
- [ ] 建置測試：`npm run build`

### 部署後必做清單
- [ ] 監控部署：`gh run watch`
- [ ] 健康檢查：`curl /health`
- [ ] API 測試：測試關鍵端點
- [ ] 日誌檢查：查看是否有錯誤