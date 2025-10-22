# Cloud Scheduler 設定 - 快速指南

## 🎯 三步驟完成設定

### 步驟 1：設定 Cloud Run 環境變數
```bash
# 執行快速設定腳本（需要 gcloud 權限）
./.github/workflows/QUICK_SETUP.sh
```

這會自動設定：
- ✅ Staging Backend `CRON_SECRET`
- ✅ Production Backend `CRON_SECRET`

### 步驟 2：設定 GitHub Secrets

前往：https://github.com/Youngger9765/duotopia/settings/secrets/actions

新增 4 個 secrets（值會在步驟 1 腳本輸出中顯示）：

1. `STAGING_BACKEND_URL`
2. `STAGING_CRON_SECRET`
3. `PRODUCTION_BACKEND_URL`
4. `PRODUCTION_CRON_SECRET`

### 步驟 3：執行 GitHub Actions

1. 前往：https://github.com/Youngger9765/duotopia/actions/workflows/setup-cloud-scheduler.yml
2. 點擊 "Run workflow"
3. 選擇環境：`staging` 或 `production`
4. 點擊 "Run workflow" 開始執行

## ✅ 完成後驗證

```bash
# 查看創建的 Cloud Scheduler jobs
gcloud scheduler jobs list --location=asia-east1

# 測試 staging 環境（手動觸發）
gcloud scheduler jobs run monthly-renewal-staging --location=asia-east1
```

## 💰 成本
- Cloud Scheduler: USD 0.40/月（4 個 jobs）
- Cloud Run 請求: 免費（在免費額度內）

## 📅 Cron 排程
- **每月續訂**: 每月 1 號凌晨 2:00 (台北時間)
- **到期提醒**: 每天凌晨 3:00 (台北時間)

## 🔧 需要更新時
只有當 cron 規則變更時才需要重新執行步驟 3。平常不需要做任何事。

## 📚 詳細文件
完整說明請參考：[CLOUD_SCHEDULER_SETUP.md](./CLOUD_SCHEDULER_SETUP.md)
