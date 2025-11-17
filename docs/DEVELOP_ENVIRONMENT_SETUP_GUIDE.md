# Develop 環境設定指南

本指南將協助您完成 develop 測試環境的設定與部署。

## 📋 前置條件

- [x] 已完成 CI/CD workflow 修改
- [ ] 安裝 GitHub CLI (`brew install gh`)
- [ ] 登入 GitHub CLI (`gh auth login`)
- [ ] 具有 Repository 管理員權限

## 🚀 設定步驟

### 步驟 1: 設定 GitHub Secrets

執行自動化設定腳本：

```bash
cd /Users/benson/GIT/duotopia
chmod +x scripts/setup_develop_secrets.sh
./scripts/setup_develop_secrets.sh
```

此腳本會自動設定以下 Secrets：

| Secret 名稱 | 說明 | 自動生成 |
|------------|------|---------|
| `DEVELOP_BACKEND_SERVICE` | Backend Cloud Run 服務名稱 | ✅ |
| `DEVELOP_FRONTEND_SERVICE` | Frontend Cloud Run 服務名稱 | ✅ |
| `DEVELOP_BACKEND_URL` | Backend URL（首次部署後更新） | ✅ |
| `DEVELOP_FRONTEND_URL` | Frontend URL（首次部署後更新） | ✅ |
| `DEVELOP_JWT_SECRET` | JWT 密鑰 | ✅ (隨機生成) |
| `DEVELOP_CRON_SECRET` | Cron job 密鑰 | ✅ (隨機生成) |
| `DEVELOP_ENABLE_PAYMENT` | 付款功能開關 | ✅ (`true`) |

**重要提示**：
- 腳本執行完成後會顯示生成的密鑰，請妥善保存！
- 其他共用的 Secrets（如資料庫、SMTP、TapPay 等）會自動使用 staging 環境的配置

### 步驟 2: 創建 develop Branch

從 staging branch 創建 develop branch：

```bash
# 1. 確保 staging 是最新的
git checkout staging
git pull origin staging

# 2. 創建並推送 develop branch
git checkout -b develop
git push -u origin develop
```

### 步驟 3: Merge feature-sentence 到 develop

```bash
# 1. 切換到 develop branch
git checkout develop

# 2. Merge feature-sentence
git merge feature-sentence

# 3. 解決任何衝突（如果有）

# 4. 推送到遠端
git push origin develop
```

### 步驟 4: 等待自動部署

推送後，GitHub Actions 會自動：

1. ✅ 執行測試（backend + frontend）
2. ✅ 執行資料庫 migrations（使用 staging DB）
3. ✅ 建置並推送 Docker images
4. ✅ 部署到 Cloud Run
5. ✅ 執行健康檢查

監控部署狀態：
```bash
# 在瀏覽器中查看
open https://github.com/Youngger9765/duotopia/actions

# 或使用 CLI
gh run list --branch develop
gh run watch
```

### 步驟 5: 更新實際 URLs

首次部署完成後，取得實際的 Cloud Run URLs：

```bash
# 取得 Backend URL
BACKEND_URL=$(gcloud run services describe duotopia-backend-develop \
  --region asia-east1 \
  --format 'value(status.url)')

# 取得 Frontend URL
FRONTEND_URL=$(gcloud run services describe duotopia-frontend-develop \
  --region asia-east1 \
  --format 'value(status.url)')

# 顯示 URLs
echo "Backend URL:  $BACKEND_URL"
echo "Frontend URL: $FRONTEND_URL"

# 更新 GitHub Secrets
gh secret set DEVELOP_BACKEND_URL --body "$BACKEND_URL" --repo Youngger9765/duotopia
gh secret set DEVELOP_FRONTEND_URL --body "$FRONTEND_URL" --repo Youngger9765/duotopia
```

### 步驟 6: 驗證部署

1. **測試 Backend 健康檢查**
```bash
curl $BACKEND_URL/api/health | jq '.'
# 應該返回: {"status": "healthy", "environment": "develop"}
```

2. **測試 Frontend**
```bash
open $FRONTEND_URL
# 應該看到 Duotopia 登入頁面
```

3. **測試資料庫連接**
- 使用 develop 環境的帳號登入
- 確認可以讀取 staging 資料庫的資料
- 測試新功能（sentence making）

## 🔄 日常開發流程

### 開發新功能

1. 從 develop 創建 feature branch
```bash
git checkout develop
git pull origin develop
git checkout -b feature-your-feature
```

2. 開發並測試
```bash
# 本地開發
npm run dev  # frontend
uvicorn main:app --reload  # backend

# 提交變更
git add .
git commit -m "feat: your feature"
git push origin feature-your-feature
```

3. Merge 到 develop 測試
```bash
git checkout develop
git merge feature-your-feature
git push origin develop
# GitHub Actions 自動部署到 develop 環境
```

4. 測試通過後 merge 到 staging
```bash
git checkout staging
git merge develop
git push origin staging
# 部署到 staging 環境供正式測試
```

5. 最終 merge 到 main
```bash
git checkout main
git merge staging
git push origin main
# 部署到 production
```

### Migration 注意事項

**重要！所有 migrations 必須遵循 Additive Migration 規則**

✅ 允許的操作：
```python
# 使用 IF NOT EXISTS
op.execute("""
    CREATE TABLE IF NOT EXISTS new_table (...)
""")

op.execute("""
    ALTER TABLE existing_table
    ADD COLUMN IF NOT EXISTS new_column VARCHAR(100) DEFAULT 'default_value'
""")

op.execute("""
    CREATE INDEX IF NOT EXISTS idx_name ON table_name (column)
""")

op.execute("""
    CREATE OR REPLACE FUNCTION function_name() ...
""")
```

❌ 禁止的操作：
```python
# 這些會破壞共用資料庫
op.drop_column('table', 'column')
op.alter_column('table', 'column', type_=NewType)
op.rename_column('table', 'old', 'new')
op.drop_table('table')
```

詳見：[CLAUDE.md - Database Migration 鐵則](../CLAUDE.md#-database-migration-鐵則全局規則)

## 🗑️ 清理 Develop 環境（可選）

如果不再需要 develop 環境：

```bash
# 1. 刪除 Cloud Run 服務
gcloud run services delete duotopia-backend-develop --region asia-east1
gcloud run services delete duotopia-frontend-develop --region asia-east1

# 2. 刪除 Docker images
gcloud artifacts docker images list \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-backend-develop \
  --format="value(version)" | \
  xargs -I {} gcloud artifacts docker images delete \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-backend-develop:{} \
  --quiet

gcloud artifacts docker images list \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-frontend-develop \
  --format="value(version)" | \
  xargs -I {} gcloud artifacts docker images delete \
  asia-east1-docker.pkg.dev/duotopia-472708/duotopia-repo/duotopia-frontend-develop:{} \
  --quiet

# 3. 刪除 GitHub Secrets（可選）
gh secret delete DEVELOP_BACKEND_SERVICE --repo Youngger9765/duotopia
gh secret delete DEVELOP_FRONTEND_SERVICE --repo Youngger9765/duotopia
gh secret delete DEVELOP_BACKEND_URL --repo Youngger9765/duotopia
gh secret delete DEVELOP_FRONTEND_URL --repo Youngger9765/duotopia
gh secret delete DEVELOP_JWT_SECRET --repo Youngger9765/duotopia
gh secret delete DEVELOP_CRON_SECRET --repo Youngger9765/duotopia
gh secret delete DEVELOP_ENABLE_PAYMENT --repo Youngger9765/duotopia

# 4. 刪除 develop branch（可選）
git branch -d develop
git push origin --delete develop
```

## 📊 環境對照表

| 項目 | Production | Staging | Develop |
|-----|-----------|---------|---------|
| Branch | `main` | `staging` | `develop` |
| 資料庫 | Production DB | Staging DB | **Staging DB** (共用) |
| Cloud Run Backend | `duotopia-backend` | `duotopia-backend-staging` | `duotopia-backend-develop` |
| Cloud Run Frontend | `duotopia-frontend` | `duotopia-frontend-staging` | `duotopia-frontend-develop` |
| Min Instances (Backend) | 1 | 1 | **0** (節省成本) |
| Min Instances (Frontend) | 0 | 0 | 0 |
| TapPay 環境 | Production | Production | Production |
| 付款功能 | 關閉 | 開啟 | 開啟 |
| 每月成本 | ~$50 | ~$50 | ~$20-25 |

## ❓ 常見問題

### Q1: Develop 和 Staging 會互相影響嗎？

**A**: 會，因為共用資料庫。這是設計的考量：
- ✅ 節省成本（不需要額外的資料庫）
- ✅ 測試真實資料環境
- ⚠️ 需要遵循 Additive Migration 規則避免衝突

### Q2: Migration 執行順序重要嗎？

**A**: 不重要，因為使用了 IF NOT EXISTS：
- 無論 develop 或 staging 先執行 migration 都安全
- 第一個執行的會創建 table/column
- 第二個執行的會跳過（已存在）

### Q3: 如何測試需要刪除欄位的情況？

**A**: 使用漸進式棄用（Gradual Deprecation）：
1. 先停止使用該欄位（程式碼不再讀寫）
2. 部署並測試
3. 確認無影響後，再創建 DROP COLUMN migration
4. 只在不共用的環境執行（如 production 單獨執行）

### Q4: Develop 環境冷啟動很慢怎麼辦？

**A**: Develop 環境設定為 min-instances=0 節省成本，冷啟動約 10-15 秒。如果需要加速：
```bash
# 臨時提高 min-instances
gcloud run services update duotopia-backend-develop \
  --region asia-east1 \
  --min-instances 1

# 測試完記得改回 0
gcloud run services update duotopia-backend-develop \
  --region asia-east1 \
  --min-instances 0
```

### Q5: 如何快速切換測試不同的 feature branches？

**A**: 使用 develop branch 作為整合點：
```bash
# 測試 feature-A
git checkout develop
git merge feature-A
git push origin develop

# 改測試 feature-B
git reset --hard origin/staging  # 重置到 staging
git merge feature-B
git push -f origin develop  # 強制推送
```

## 📚 相關文件

- [DEVELOP_ENVIRONMENT_PLAN.md](./DEVELOP_ENVIRONMENT_PLAN.md) - 詳細實作計劃
- [CLAUDE.md](../CLAUDE.md) - 開發規範與 Migration 規則
- [CICD.md](../CICD.md) - CI/CD 配置說明
- [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md) - 部署狀態追蹤
