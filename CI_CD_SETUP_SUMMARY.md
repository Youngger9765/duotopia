# CI/CD 設定總結

## ✅ 已完成的工作

### 1. 重構檔案命名
- 移除所有帶版本號的檔案名稱（v1, v2）
- `individual_v2.py` → `individual.py`
- 歸檔舊版本檔案到 `archive/` 目錄
- 更新所有 import 路徑

### 2. GitHub Actions CI/CD 管線
- **Staging 部署** (`.github/workflows/deploy-staging.yml`)
  - 自動觸發：推送到 `staging` 分支
  - 包含測試、建置、部署流程
  
- **Production 部署** (`.github/workflows/deploy-production.yml`)
  - 自動觸發：推送到 `main` 分支
  - 需要手動審核（environment protection）

### 3. GitHub Secrets 設定
已設定的 Secrets：
- ✅ `DATABASE_URL`
- ✅ `JWT_SECRET`
- ✅ `WIF_PROVIDER`
- ✅ `WIF_SERVICE_ACCOUNT`
- ⚠️ `GOOGLE_CLIENT_ID` (需手動設定)
- ⚠️ `GOOGLE_CLIENT_SECRET` (需手動設定)
- ⚠️ `OPENAI_API_KEY` (需手動設定)

### 4. Workload Identity Federation
- 已建立 Service Account: `github-actions@duotopia-469413.iam.gserviceaccount.com`
- 已設定必要權限：
  - Cloud Run Admin
  - Storage Admin
  - Service Account User
  - Cloud Build Editor
- 已綁定到 GitHub Repository

### 5. Git Hooks
建立了自動檢查機制：
- **pre-commit**: TypeScript 檢查 + 建置測試
- **pre-push**: 完整測試套件

## 🚀 部署流程

1. **本地開發**
   ```bash
   # 開發時會自動執行 pre-commit 檢查
   git commit -m "feat: new feature"
   
   # 推送時會執行 pre-push 檢查
   git push origin staging
   ```

2. **Staging 部署**
   - 推送到 `staging` 分支自動觸發
   - 約 5 分鐘完成部署

3. **Production 部署**
   - 推送到 `main` 分支
   - 需要在 GitHub 上手動批准

## 📝 待辦事項

1. **設定剩餘的 Secrets**
   ```bash
   gh secret set GOOGLE_CLIENT_ID --body "your-client-id"
   gh secret set GOOGLE_CLIENT_SECRET --body "your-client-secret"
   gh secret set OPENAI_API_KEY --body "sk-..."
   ```

2. **設定 Environment Protection Rules**
   - 在 GitHub Settings → Environments → production
   - 啟用 "Required reviewers"

3. **監控和告警**
   - 設定 Cloud Monitoring
   - 設定部署失敗通知

## 🔗 相關連結

- [GitHub Actions 執行記錄](https://github.com/Youngger9765/duotopia/actions)
- [Cloud Run 服務](https://console.cloud.google.com/run?project=duotopia-469413)
- [部署文件](.github/workflows/README.md)