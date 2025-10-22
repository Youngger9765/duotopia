# Cloud Scheduler 設定指南

## 🎯 目的
設定 Google Cloud Scheduler 來自動執行每月續訂和到期提醒。

## 📋 前置需求

### 1. 生成 CRON_SECRET
```bash
# 生成隨機的 secret (32 bytes)
openssl rand -base64 32

# 範例輸出：
# aB3dEf9hIjKlMnOpQrStUvWxYz01234567890ABC=
```

### 2. 設定 GitHub Secrets

前往 GitHub Repository Settings > Secrets and variables > Actions，新增以下 secrets：

#### Staging 環境：
- `STAGING_BACKEND_URL`
  - 值：`https://duotopia-backend-staging-XXXXX.run.app`
  - 說明：從 Cloud Run 取得實際的 URL

- `STAGING_CRON_SECRET`
  - 值：上面生成的隨機字串
  - 說明：用來驗證 cron job 請求的密碼

#### Production 環境：
- `PRODUCTION_BACKEND_URL`
  - 值：`https://duotopia-backend-XXXXX.run.app`

- `PRODUCTION_CRON_SECRET`
  - 值：另一個隨機生成的字串（與 staging 不同）

### 3. 設定 Backend 環境變數

同樣的 `CRON_SECRET` 也要設定在 Cloud Run 的環境變數中：

#### 方法 A：透過 Cloud Console
1. 前往 Cloud Run > 選擇 service > Edit & Deploy new revision
2. Variables & Secrets > Add Variable
3. Name: `CRON_SECRET`
4. Value: (填入與 GitHub Secret 相同的值)

#### 方法 B：透過 gcloud CLI
```bash
# Staging
gcloud run services update duotopia-backend-staging \
  --update-env-vars CRON_SECRET="你的_STAGING_CRON_SECRET" \
  --region asia-east1

# Production
gcloud run services update duotopia-backend \
  --update-env-vars CRON_SECRET="你的_PRODUCTION_CRON_SECRET" \
  --region asia-east1
```

## 🚀 執行步驟

### 首次部署 Cloud Scheduler

1. **確認已設定好所有 Secrets** (上面 4 個)

2. **前往 GitHub Actions**
   - Repository > Actions > Setup Cloud Scheduler

3. **點擊 "Run workflow"**
   - 選擇 branch: `staging` 或 `main`
   - 選擇 environment: `staging` 或 `production`
   - 點擊 "Run workflow"

4. **等待執行完成**
   - 查看 logs 確認兩個 jobs 都創建成功

5. **驗證**
   ```bash
   # 列出所有 scheduler jobs
   gcloud scheduler jobs list --location=asia-east1

   # 查看特定 job 詳情
   gcloud scheduler jobs describe monthly-renewal-staging --location=asia-east1
   ```

### 測試 Cloud Scheduler (Staging Only)

```bash
# 手動觸發 staging 的 monthly renewal job
gcloud scheduler jobs run monthly-renewal-staging --location=asia-east1

# 手動觸發 staging 的 renewal reminder job
gcloud scheduler jobs run renewal-reminder-staging --location=asia-east1

# 查看執行歷史
gcloud scheduler jobs describe monthly-renewal-staging \
  --location=asia-east1 \
  --format="value(state,schedule)"
```

## 🔧 更新 Cloud Scheduler

當需要更新 cron 規則（時間、URL）時：

1. 修改 `.github/workflows/setup-cloud-scheduler.yml` 中的 schedule 或其他設定
2. Commit 並 push
3. 前往 GitHub Actions 手動觸發 workflow
4. Scheduler 會自動刪除舊的並創建新的

## 💰 成本

- **Cloud Scheduler**: USD 0.10/月 per job
  - 2 個 jobs = USD 0.20/月
  - Staging + Production = USD 0.40/月

- **Cloud Run 請求**: 免費
  - 每月約 31-32 次請求
  - 在免費額度內 (每月 200 萬次請求)

**總計**: 約 USD 0.40/月

## ⚠️ 注意事項

1. **不要在 production 測試**
   - 只在 staging 環境手動觸發測試
   - Production 等正式上線後才設定

2. **CRON_SECRET 安全性**
   - 使用強隨機密碼
   - Staging 和 Production 使用不同的 secret
   - 不要 commit 到程式碼中
   - 定期更換（建議每季）

3. **時區設定**
   - 使用 `Asia/Taipei` 確保是台北時間
   - 每月 1 號凌晨 2:00 = 02:00 台北時間

4. **監控**
   - 定期檢查 Cloud Scheduler 執行歷史
   - 查看 Cloud Run logs 確認 cron jobs 正常執行
   - 設定 alert 當 job 失敗時通知

## 🔍 檢查清單

部署前確認：
- [ ] 已生成兩組 CRON_SECRET (staging, production)
- [ ] GitHub Secrets 已設定 (4 個)
- [ ] Cloud Run 環境變數已設定 CRON_SECRET
- [ ] 已取得正確的 Backend URL
- [ ] 已測試 Backend `/health` 端點可訪問

部署後驗證：
- [ ] `gcloud scheduler jobs list` 顯示 2 個 jobs
- [ ] 在 staging 手動觸發測試成功
- [ ] Cloud Run logs 顯示 cron job 執行記錄
- [ ] 沒有錯誤訊息

## 📞 故障排除

### Cloud Scheduler 請求失敗 (401 Unauthorized)
**原因**: CRON_SECRET 不匹配
**解決**: 確認 GitHub Secret 和 Cloud Run 環境變數的 CRON_SECRET 相同

### Cloud Scheduler 請求失敗 (404 Not Found)
**原因**: Backend URL 錯誤或 API 路由不存在
**解決**: 確認 BACKEND_URL 正確，檢查 `/api/cron/monthly-renewal` 路由存在

### Cloud Scheduler 請求超時
**原因**: Backend 處理時間過長 (>300s)
**解決**: 檢查資料庫查詢效能，考慮增加 `--attempt-deadline`

### 查看詳細 logs
```bash
# Cloud Scheduler logs
gcloud logging read "resource.type=cloud_scheduler_job" --limit 50

# Cloud Run logs (cron 相關)
gcloud run logs read duotopia-backend-staging \
  --filter="httpRequest.requestUrl=~'cron'" \
  --limit=50
```

## 🔗 相關連結

- [Cloud Scheduler 文件](https://cloud.google.com/scheduler/docs)
- [Cloud Scheduler 定價](https://cloud.google.com/scheduler/pricing)
- [Cron 格式說明](https://cloud.google.com/scheduler/docs/configuring/cron-job-schedules)
