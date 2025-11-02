# GitHub Secrets 設定指南

## 🔐 需要設定的 GitHub Secrets

所有 secrets 都存在 GitHub，透過 CI/CD 自動注入到 Cloud Run。
**不需要手動修改 Cloud Run 環境變數！**

---

## 📋 必要 Secrets 清單

### GCP 認證
```bash
GCP_SA_KEY
# Service Account 的 JSON key
# 取得方式: GCP Console → IAM & Admin → Service Accounts → 建立 key
```

### Staging 環境資料庫
```bash
STAGING_DATABASE_URL
STAGING_DATABASE_POOLER_URL
STAGING_SUPABASE_URL
STAGING_SUPABASE_ANON_KEY
STAGING_JWT_SECRET
```

### Production 環境資料庫
```bash
PRODUCTION_DATABASE_URL
PRODUCTION_DATABASE_POOLER_URL
PRODUCTION_SUPABASE_URL
PRODUCTION_SUPABASE_ANON_KEY
PRODUCTION_JWT_SECRET
```

### TapPay Credentials (所有環境共用)
```bash
# Sandbox 參數
TAPPAY_SANDBOX_APP_ID=[從 TapPay Portal 取得]
TAPPAY_SANDBOX_APP_KEY=[從 TapPay Portal 取得]
TAPPAY_SANDBOX_PARTNER_KEY=[從 TapPay Portal 取得]
TAPPAY_SANDBOX_MERCHANT_ID=[從 TapPay Portal 取得]

# Production 參數 (3D 驗證)
TAPPAY_PRODUCTION_APP_ID=[從 TapPay Portal 取得]
TAPPAY_PRODUCTION_APP_KEY=[從 TapPay Portal 取得]
TAPPAY_PRODUCTION_PARTNER_KEY=[從 TapPay Portal 取得]
TAPPAY_PRODUCTION_MERCHANT_ID=[從 TapPay Portal 取得 - 建議選 3D 驗證]
```

### OpenAI & Email
```bash
OPENAI_API_KEY=[從 OpenAI 取得]
SMTP_USER=[Gmail 帳號]
SMTP_PASSWORD=[Gmail App Password]
```

---

## 🔧 設定方式

### 方法 1: 使用 GitHub Web UI
1. 到 GitHub repository
2. Settings → Secrets and variables → Actions
3. New repository secret
4. 逐個加入上述 secrets

### 方法 2: 使用 `gh` CLI (推薦)
```bash
# 從 .env 檔案讀取並設定
gh secret set TAPPAY_SANDBOX_APP_ID --body "[YOUR_VALUE]"
gh secret set TAPPAY_SANDBOX_APP_KEY --body "[YOUR_VALUE]"
gh secret set TAPPAY_SANDBOX_PARTNER_KEY --body "[YOUR_VALUE]"
gh secret set TAPPAY_SANDBOX_MERCHANT_ID --body "[YOUR_VALUE]"

gh secret set TAPPAY_PRODUCTION_APP_ID --body "[YOUR_VALUE]"
gh secret set TAPPAY_PRODUCTION_APP_KEY --body "[YOUR_VALUE]"
gh secret set TAPPAY_PRODUCTION_PARTNER_KEY --body "[YOUR_VALUE]"
gh secret set TAPPAY_PRODUCTION_MERCHANT_ID --body "[YOUR_VALUE]"

# 或從本地 .env 檔案讀取 (不要把 .env 推到 git!)
# 參考 backend/.env.staging 中的值
```

---

## 🎯 架構優勢

### ✅ Code 控制環境，Secrets 存資料
```
Staging branch:
  TAPPAY_ENV=production  ← 在 workflow 中設定
  → 自動使用 TAPPAY_PRODUCTION_* secrets

Production branch:
  TAPPAY_ENV=sandbox     ← 在 workflow 中設定
  → 自動使用 TAPPAY_SANDBOX_* secrets
```

### ✅ 不需要手動改 Cloud Run
- 所有環境變數由 GitHub Actions 自動注入
- Push code → 自動部署 → 環境變數正確

### ✅ 切換環境只需改 code
```yaml
# deploy-staging.yml
--set-env-vars "TAPPAY_ENV=production"  ← 改這裡

# deploy-production.yml
--set-env-vars "TAPPAY_ENV=sandbox"     ← 改這裡
```

---

## 📝 部署流程

### Staging (測試 Production 金流)
```bash
# 1. 修改 code (如果需要)
# 2. Commit & Push
git add .
git commit -m "feat: 測試功能"
git push origin staging

# 3. GitHub Actions 自動:
#    - Build image
#    - 注入環境變數 (TAPPAY_ENV=production)
#    - Deploy to Cloud Run
#    - ✅ 自動使用 Production credentials
```

### Production (免費期，關閉付款)
```bash
# Push to main
git push origin main

# GitHub Actions 自動:
#    - ENABLE_PAYMENT=false
#    - TAPPAY_ENV=sandbox
#    - ✅ 付款功能關閉
```

---

## 🚀 未來開放 Production 付款

只需改一行 code:

```yaml
# .github/workflows/deploy-production.yml
--set-env-vars "ENABLE_PAYMENT=true" \      ← false → true
--set-env-vars "TAPPAY_ENV=production" \    ← sandbox → production
```

Commit & Push → 自動部署 → 付款功能開放 ✅

---

## 🔒 安全性

- ✅ 所有 keys 在 GitHub Secrets (加密)
- ✅ 不會出現在 code 中
- ✅ 不會出現在 git history
- ✅ Cloud Run 環境變數由 CI/CD 設定
- ✅ 本地開發用 `.env.local` (gitignore)

---

## 📊 環境對照表

| 環境 | Branch | TAPPAY_ENV | ENABLE_PAYMENT | 用途 |
|------|--------|------------|----------------|------|
| **Staging** | `staging` | `production` | `true` | 測試正式金流 |
| **Production** | `main` | `sandbox` | `false` | 免費期 (暫不收費) |

**未來 Production 開放付款時:**
- 改 `deploy-production.yml` 中的兩個變數
- Push → 自動部署 → 完成 ✅

---

**最後更新**: 2025-11-02
**狀態**: ✅ 架構設計完成，待設定 GitHub Secrets
