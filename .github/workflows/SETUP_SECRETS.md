# GitHub Secrets 設定指南

## 🔑 需要新增的 Secrets

在 GitHub Repository Settings → Secrets and variables → Actions 中新增：

### 新增的 Secrets（Frontend Workflow 需要）
```
STAGING_BACKEND_URL = https://duotopia-staging-backend-316409492201.asia-east1.run.app
PRODUCTION_BACKEND_URL = https://duotopia-backend-316409492201.asia-east1.run.app
```

這兩個是作為 fallback，當 frontend workflow 無法自動偵測到後端 URL 時使用。

## ✅ 已存在的 Secrets（確認清單）

### GCP 相關
- [x] `GCP_SA_KEY` - Google Cloud Service Account Key
- [x] `GCS_SERVICE_ACCOUNT_KEY` - GCS Service Account Key

### Supabase Production
- [x] `PRODUCTION_SUPABASE_URL`
- [x] `PRODUCTION_SUPABASE_POOLER_URL`
- [x] `PRODUCTION_SUPABASE_PROJECT_URL`
- [x] `PRODUCTION_SUPABASE_ANON_KEY`
- [x] `PRODUCTION_JWT_SECRET`
- [x] `PRODUCTION_FRONTEND_URL`

### Supabase Staging
- [x] `STAGING_SUPABASE_URL`
- [x] `STAGING_SUPABASE_POOLER_URL`
- [x] `STAGING_SUPABASE_PROJECT_URL`
- [x] `STAGING_SUPABASE_ANON_KEY`
- [x] `STAGING_JWT_SECRET`
- [x] `STAGING_FRONTEND_URL`

### API Keys
- [x] `OPENAI_API_KEY`
- [x] `AZURE_SPEECH_KEY`
- [x] `AZURE_SPEECH_REGION`
- [x] `AZURE_SPEECH_ENDPOINT`

### Email 設定
- [x] `SMTP_HOST`
- [x] `SMTP_PORT`
- [x] `SMTP_USER`
- [x] `SMTP_PASSWORD`
- [x] `FROM_EMAIL`
- [x] `FROM_NAME`

## 📝 設定步驟

1. 進入 GitHub Repository 頁面
2. 點擊 Settings
3. 左側選單選擇 Secrets and variables → Actions
4. 點擊 "New repository secret"
5. 輸入 Name 和 Value
6. 點擊 "Add secret"

## 🔧 取得後端 URL 的方法

```bash
# Staging
gcloud run services describe duotopia-staging-backend \
  --platform managed \
  --region asia-east1 \
  --format 'value(status.url)'

# Production
gcloud run services describe duotopia-backend \
  --platform managed \
  --region asia-east1 \
  --format 'value(status.url)'
```
