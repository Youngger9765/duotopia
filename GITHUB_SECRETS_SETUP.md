# GitHub Secrets 設定指南

## ✅ 已完成的設定

以下 secrets 已經設定完成：
- `DATABASE_URL` - PostgreSQL 連接字串
- `JWT_SECRET` - JWT 簽名密鑰
- `WIF_PROVIDER` - Workload Identity Federation Provider
- `WIF_SERVICE_ACCOUNT` - GitHub Actions Service Account

## ⚠️ 需要手動設定的 Secrets

### 1. Google OAuth 認證
您需要從 [Google Cloud Console](https://console.cloud.google.com/apis/credentials) 獲取：

```bash
# 設定 Client ID
gh secret set GOOGLE_CLIENT_ID --body "your-actual-client-id.apps.googleusercontent.com"

# 設定 Client Secret
gh secret set GOOGLE_CLIENT_SECRET --body "your-actual-client-secret"
```

**獲取步驟：**
1. 前往 [Google Cloud Console](https://console.cloud.google.com/apis/credentials?project=duotopia-469413)
2. 點擊「建立憑證」→「OAuth 用戶端 ID」
3. 應用程式類型選擇「網頁應用程式」
4. 授權的重新導向 URI 加入：
   - `http://localhost:5173/auth/callback`
   - `https://duotopia-backend-staging-731209836128.asia-east1.run.app/api/auth/google/callback`
   - `https://duotopia-backend-731209836128.asia-east1.run.app/api/auth/google/callback`


## 🔍 驗證設定

查看所有已設定的 secrets：
```bash
gh secret list
```

應該要看到以下所有 secrets：
- DATABASE_URL
- JWT_SECRET
- WIF_PROVIDER
- WIF_SERVICE_ACCOUNT
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

## 🚀 測試部署

1. **確認所有 secrets 都已設定**
   ```bash
   gh secret list | wc -l
   # 應該要有 6 個或以上
   ```

2. **執行 Workload Identity 設定**
   ```bash
   ./setup-workload-identity.sh
   ```

3. **推送到 staging 測試**
   ```bash
   git push origin staging
   ```

4. **監控部署狀態**
   ```bash
   gh run list
   gh run watch
   ```

## 🆘 疑難排解

### 如果部署失敗
1. 檢查 Actions 日誌：
   ```bash
   gh run view
   ```

2. 檢查 secret 是否正確：
   - DATABASE_URL 格式：`postgresql://user:password@host:port/database`
   - GOOGLE_CLIENT_ID 結尾應該是 `.apps.googleusercontent.com`

3. 確認 Workload Identity 設定：
   ```bash
   gcloud iam service-accounts list | grep github-actions
   ```

## 📝 備註
- GCP_SA_KEY 是舊的認證方式，新的 CI/CD 使用 Workload Identity Federation
- SECRET_KEY 可能是舊的設定，目前使用 JWT_SECRET