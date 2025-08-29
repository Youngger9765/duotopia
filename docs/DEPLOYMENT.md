# 🚀 Duotopia 部署指南

## 📊 部署架構（2x2 矩陣）

我們支援兩種環境 × 兩種資料庫的靈活部署：

|            | Supabase (免費) | Cloud SQL ($2.28/天) |
|------------|----------------|---------------------|
| **Staging**    | ✅ 預設         | ✅ 可選              |
| **Production** | ✅ 初期使用      | ✅ 規模化後          |

## 🎯 快速開始

### 預設部署（使用 Supabase - 免費）
```bash
# 部署到 Staging（使用免費的 Supabase）
make deploy-staging

# 或明確指定
make deploy-staging-supabase
```

### 使用 Cloud SQL 部署（需要成本考量）
```bash
# 部署到 Staging with Cloud SQL（$2.28/天）
make deploy-staging-cloudsql
# 系統會提醒成本並要求確認
```

## 🔄 切換資料庫（不重新部署）

快速切換已部署服務的資料庫：

```bash
# 切換到 Supabase（省錢）
make switch-staging-supabase

# 切換到 Cloud SQL（需要時）
make switch-staging-cloudsql

# 檢查當前使用的資料庫
make check-database
```

## 📝 GitHub Actions 工作流程

### 自動觸發
- **Push to `staging` branch** → 自動部署（預設用 Supabase）
- **Pull Request to `staging`** → 只執行測試，不部署

### 手動觸發（推薦）
1. 前往 GitHub Actions 頁面
2. 選擇 "Deploy to Staging" workflow
3. 點擊 "Run workflow"
4. 選擇資料庫：
   - `supabase`（預設，免費）
   - `cloudsql`（需成本）

## 💰 成本管理

### 成本比較
| 資料庫 | 每日成本 | 每月成本 | 適用場景 |
|--------|---------|---------|----------|
| Supabase | $0 | $0 | 開發、測試、初期上線 |
| Cloud SQL | $2.28 | $68.40 | 正式生產、高流量 |

### Cloud SQL 管理指令
```bash
# 停止 Cloud SQL（省錢）
./scripts/manage-db.sh stop

# 啟動 Cloud SQL
./scripts/manage-db.sh start

# 檢查成本
./scripts/manage-db.sh cost
```

## 🔑 必要的 GitHub Secrets

在 GitHub Repository Settings > Secrets 中設定：

### 基本配置
- `GCP_SA_KEY`: GCP Service Account JSON key
- `STAGING_JWT_SECRET`: JWT 密鑰

### Supabase 配置
- `STAGING_SUPABASE_URL`: PostgreSQL 連接字串
- `STAGING_SUPABASE_PROJECT_URL`: Supabase 專案 URL
- `STAGING_SUPABASE_ANON_KEY`: Supabase 匿名金鑰

### Cloud SQL 配置
- `STAGING_CLOUDSQL_URL`: Cloud SQL 連接字串

## 🛠️ 本地開發

### 使用 Docker（推薦）
```bash
# 啟動本地資料庫
docker-compose up -d

# 設定環境變數
export DATABASE_TYPE=local
export DATABASE_URL=postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia

# 啟動服務
make dev-backend  # Terminal 1
make dev-frontend # Terminal 2
```

### 連接 Supabase（測試遠端）
```bash
export DATABASE_TYPE=supabase
export DATABASE_URL=[你的 Supabase URL]
make dev-backend
```

## 📊 監控與健康檢查

### 檢查服務狀態
```bash
# 後端健康檢查
curl https://duotopia-staging-backend-xxx.run.app/health

# 回應範例：
{
  "status": "healthy",
  "service": "duotopia-backend",
  "database": {
    "type": "supabase",
    "environment": "staging",
    "deployment": "staging-supabase",
    "is_free_tier": true,
    "daily_cost_usd": 0.0
  }
}
```

## 🚨 注意事項

1. **預設使用 Supabase**：為了節省成本，所有部署預設使用免費的 Supabase
2. **Cloud SQL 需手動確認**：使用 Cloud SQL 時會提示成本警告
3. **記得關閉 Cloud SQL**：不使用時請執行 `./scripts/manage-db.sh stop`
4. **資料遷移**：從 Supabase 遷移到 Cloud SQL 請參考 [Migration Guide](./MIGRATION.md)

## 📚 相關文件

- [Supabase 設定指南](./SUPABASE_SETUP.md)
- [Cloud SQL 設定指南](./CLOUDSQL_SETUP.md)
- [資料庫遷移指南](./MIGRATION.md)
- [成本優化指南](./COST_OPTIMIZATION.md)

## 🆘 常見問題

### Q: 如何知道目前使用哪個資料庫？
```bash
make check-database
# 或訪問 /health endpoint
```

### Q: 如何從 Supabase 遷移到 Cloud SQL？
1. 匯出 Supabase 資料：`pg_dump [supabase_url] > backup.sql`
2. 匯入 Cloud SQL：`psql [cloudsql_url] < backup.sql`
3. 切換環境：`make switch-staging-cloudsql`

### Q: 部署失敗怎麼辦？
1. 檢查 GitHub Actions 日誌
2. 確認 Secrets 設定正確
3. 檢查資料庫連線：`make check-database`

---
更新日期：2025-08-29