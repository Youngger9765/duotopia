# 環境變數管理指南

## 🎯 管理原則

### 1. 環境分離
- **Staging** 和 **Production** 使用完全不同的資源
- 每個環境有獨立的：
  - 資料庫
  - Secret Manager secrets
  - Service URLs

### 2. Secret 管理層級

```
Terraform (terraform.tfvars)
    ↓ 建立
Secret Manager (google-client-secret, jwt-secret, etc.)
    ↓ 引用
Cloud Run (使用 --update-secrets)
```

## 📋 環境變數清單

### 資料庫連線
| 環境 | Host | Secret Name |
|------|------|-------------|
| Staging | 35.221.172.134 | database-url-staging |
| Production | 35.201.201.210 | database-url-production |

### JWT Secret
| 環境 | Secret Name |
|------|-------------|
| Staging | jwt-secret-staging |
| Production | jwt-secret-production |

### Google OAuth
| 環境 | Secret Name |
|------|-------------|
| Staging | google-client-id-staging, google-client-secret-staging |
| Production | google-client-id-production, google-client-secret-production |

## 🔧 設定步驟

### 1. 建立 Secret Manager Secrets (透過 Terraform)

```hcl
# terraform/secrets.tf
resource "google_secret_manager_secret" "database_url_staging" {
  secret_id = "database-url-staging"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "database_url_staging" {
  secret      = google_secret_manager_secret.database_url_staging.id
  secret_data = "postgresql://${var.db_user}:${var.db_password_staging}@35.221.172.134:5432/duotopia"
}
```

### 2. GitHub Actions 設定

```yaml
# .github/workflows/deploy-staging.yml
- name: Deploy to Cloud Run
  run: |
    gcloud run deploy $SERVICE_NAME \
      --update-secrets "DATABASE_URL=database-url-staging:latest" \
      --update-secrets "JWT_SECRET=jwt-secret-staging:latest" \
      --update-secrets "GOOGLE_CLIENT_ID=google-client-id-staging:latest" \
      --update-secrets "GOOGLE_CLIENT_SECRET=google-client-secret-staging:latest"
```

### 3. 本地開發設定

```bash
# 複製範例檔案
cp .env.example .env.staging
cp .env.example .env.production

# 編輯並填入實際值
vim .env.staging

# 使用特定環境
export $(cat .env.staging | xargs)
```

## 🚨 重要提醒

1. **絕對不要**把 production 資料庫連線字串用在 staging
2. **絕對不要**把 .env 檔案提交到 Git
3. **定期輪換** JWT Secret 和其他密鑰
4. **使用 Terraform** 管理所有 secrets，不要手動建立

## 📝 檢查清單

部署前確認：
- [ ] 正確的資料庫 IP（staging vs production）
- [ ] 正確的 secret 名稱（-staging vs -production）
- [ ] GitHub Actions 使用 --update-secrets 而非 --set-env-vars
- [ ] .env 檔案已加入 .gitignore