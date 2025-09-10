# CICD.md - Duotopia CI/CD 部署準則

本文件規範 Duotopia 專案的 CI/CD 流程與部署準則，避免重複犯錯。

## 🔴 最高原則：絕不手動創建昂貴資源

### Cloud SQL 創建鐵律
1. **永遠使用 Makefile 創建資源**
   ```bash
   # ✅ 正確
   make db-create

   # ❌ 錯誤 - 絕對禁止
   gcloud sql instances create ...
   ```

2. **Tier 必須檢查三次**
   - 只允許 `db-f1-micro`（$11/月）
   - 禁止 `db-g1-small`（$50/月）
   - 禁止任何更大的實例

3. **Edition 必須明確指定**
   ```bash
   --edition=ENTERPRISE  # 必須，否則 db-f1-micro 不可用
   ```

## 📋 部署前檢查清單

### 1. 配置檢查
- [ ] 確認 `gcloud config get-value project` 顯示 `duotopia-469413`
- [ ] 確認區域是 `asia-east1`
- [ ] 確認沒有硬編碼的 localhost URL
- [ ] 確認沒有舊的 import 路徑

### 2. 資源檢查
```bash
# 部署前必須執行
gcloud sql instances list --format="table(name,tier,state)"
# 確保：
# - 沒有 Small 或更大的實例
# - 沒有不必要的 RUNNABLE 實例
```

### 3. 成本預檢
- [ ] Cloud SQL 實例數量 ≤ 1
- [ ] Cloud Run min-instances = 0
- [ ] 沒有遺留的測試資源

## 🚀 標準部署流程

### 開發環境部署
```bash
# 1. 本地測試
npm run typecheck
npm run lint
npm run build
cd backend && python -m pytest

# 2. Docker 測試
docker build -t test-backend backend/
docker run -p 8080:8080 test-backend

# 3. 推送到 staging
git push origin staging

# 4. 監控部署
gh run watch
gh run list --workflow=deploy-staging.yml --limit=1

# 5. 驗證部署
curl https://duotopia-backend-staging-xxx.run.app/health
```

### 生產環境部署（謹慎）
```bash
# 1. 確認 staging 測試通過
make test-staging

# 2. 創建 PR
git checkout -b release/v1.x.x
git push origin release/v1.x.x
gh pr create --base main

# 3. Code Review 後合併

# 4. 監控生產部署
gh run watch
```

## 🔍 部署監控

### 即時監控命令
```bash
# 查看部署進度
gh run watch

# 查看部署日誌
gh run view --log

# 查看服務日誌
gcloud run logs read duotopia-backend --limit=50

# 檢查錯誤
gcloud run logs read duotopia-backend --limit=50 | grep -i error
```

### 健康檢查
```bash
# Backend
curl https://duotopia-backend-staging-xxx.run.app/health
curl https://duotopia-backend-staging-xxx.run.app/api/docs

# Frontend
curl https://duotopia-frontend-staging-xxx.run.app
```

## ⚠️ 常見錯誤與解決

### 1. PORT 配置錯誤
**錯誤**: Container failed to start
**原因**: Cloud Run 需要 PORT=8080
**解決**:
```python
# main.py
port = int(os.environ.get("PORT", 8080))
```

### 2. 資料庫連線失敗
**錯誤**: Connection refused 或 could not translate host name
**原因**:
- 啟動時立即連接資料庫
- GitHub Actions 缺少 Pooler URL (IPv4)
**解決**:
```python
# 不要在頂層連接
# 使用 Depends(get_db) 延遲連接
```
**CI/CD 解決**：設定 `STAGING_SUPABASE_POOLER_URL` (見下方 Supabase Pooler 設定)

### 3. Import 路徑錯誤
**錯誤**: Module not found
**原因**: TypeScript 路徑別名
**解決**: 使用相對路徑而非 @/

### 4. Cloud SQL 版本不相容
**錯誤**: Invalid tier for edition
**原因**: Enterprise Plus 不支援 micro
**解決**: 指定 `--edition=ENTERPRISE`

## 💰 成本控制檢查點

### 每日檢查
```bash
# 檢查 Cloud SQL
gcloud sql instances list
# 任何非 micro 或 RUNNABLE 但未使用的立即處理

# 檢查 Cloud Run
gcloud run services list
# 確認 min-instances = 0
```

### 每週檢查
```bash
# 查看帳單
gcloud billing accounts list
gcloud alpha billing budgets list

# 清理未使用資源
gcloud artifacts repositories list
gcloud storage ls
```

## 📊 部署指標

### 成功部署標準
- ✅ 健康檢查通過
- ✅ 無錯誤日誌
- ✅ API 文檔可訪問
- ✅ 前端頁面正常載入
- ✅ 資料庫連線正常

### 性能指標
- 冷啟動時間 < 10s
- 健康檢查回應 < 1s
- Docker 映像 < 500MB
- 記憶體使用 < 512MB

## 🛡️ Alembic Migration 管理

### 防呆機制（三層防護）

#### 第一層：本地 Pre-commit Hook
安裝後，每次 commit 時自動檢查：
```bash
# 安裝
pip install pre-commit
pre-commit install

# 自動執行 alembic check
# 如果 model 有變更但沒有 migration，會阻止 commit
```

#### 第二層：Makefile 快捷指令
```bash
# 檢查是否需要 migration
make db-check

# 生成 migration（有提示）
make db-migrate MSG="add new field"

# 執行 migration
make db-upgrade
```

#### 第三層：CI/CD 強制檢查
GitHub Actions 會：
1. 執行 `alembic check` 檢查是否有遺漏的 migration
2. 如果有遺漏，**部署會失敗**並顯示錯誤訊息
3. 強制開發者生成 migration 才能部署

### Migration 工作流程

1. **修改 Model**
```python
# backend/models.py
class Content(Base):
    # 新增欄位
    is_public = Column(Boolean, default=False)
```

2. **生成 Migration**
```bash
cd backend
alembic revision --autogenerate -m "add_is_public_to_content"
```

3. **檢查生成的檔案**
```bash
# 檢查 alembic/versions/xxx_add_is_public_to_content.py
# ⚠️ 重要：autogenerate 不完美，必須手動檢查
```

4. **本地測試**
```bash
alembic upgrade head
alembic downgrade -1  # 測試回滾
alembic upgrade head
```

5. **提交變更**
```bash
git add alembic/versions/
git commit -m "feat: add is_public field to content model"
git push
```

### CI/CD 自動執行 Migration

```yaml
- name: Run Alembic database migrations
  env:
    # 使用 Pooler URL 確保 IPv4 連線（GitHub Actions 需要）
    DATABASE_URL: ${{ secrets.STAGING_SUPABASE_POOLER_URL || secrets.STAGING_SUPABASE_URL }}
  working-directory: ./backend
  run: |
    alembic current        # 顯示當前版本
    alembic upgrade head   # 升級到最新
    alembic check          # 檢查是否有遺漏的變更
```

### Migration 失敗處理

如果 migration 失敗：
1. **部署會自動停止**，防止不一致的狀態
2. **查看錯誤日誌**：GitHub Actions 的 logs
3. **本地重現問題**：
   ```bash
   alembic upgrade head --sql  # 預覽 SQL
   alembic upgrade head         # 實際執行
   ```
4. **修復後重新部署**

### 常見 Migration 錯誤

- `New upgrade operations detected`：Model 變更但沒有 migration
- `Can't locate revision`：alembic_version 表不同步
- `could not translate host name`：需要設定 Pooler URL

## 🔴 Supabase Pooler 設定（CI/CD 必須）

### 問題背景
Supabase 新專案預設只提供 IPv6 地址，但 GitHub Actions 不支援 IPv6，導致 CI/CD 無法連接資料庫。

### 解決方案：使用 Supabase Pooler
使用 Supabase Pooler (Supavisor) 連線，它提供 IPv4 地址。**這是 CI/CD 正常運作的必要設定！**

### 設定步驟

1. **取得 Pooler URL**
   - 登入 [Supabase Dashboard](https://supabase.com/dashboard)
   - 選擇你的專案 → Settings → Database
   - 找到 **Connection string** 區塊
   - 選擇 **Connection pooling** 標籤
   - 複製 **Transaction** 模式的連線字串

   格式範例：
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres
   ```

2. **設定 GitHub Secret**
   - GitHub repository → Settings → Secrets and variables → Actions
   - 新增 secret：`STAGING_SUPABASE_POOLER_URL`
   - 值：貼上 Pooler URL

3. **驗證設定**
   - 推送程式碼後，CI/CD 應該能成功執行 Alembic migrations

### Pooler vs Direct Connection
| 連線類型 | URL 格式 | 使用場景 |
|---------|----------|----------|
| Direct Connection | db.xxx.supabase.co | 應用程式長連線 |
| Pooler Connection | pooler.supabase.com | CI/CD、短連線、serverless |

### Transaction vs Session Mode
- **Transaction Mode**：每個 transaction 使用新連線（適合 migrations）
- **Session Mode**：保持連線狀態（適合需要 prepared statements 的應用）

## 🔄 回滾程序

### 快速回滾
```bash
# 1. 找到上一個成功版本
gcloud run revisions list --service=duotopia-backend

# 2. 回滾到特定版本
gcloud run services update-traffic duotopia-backend \
  --to-revisions=duotopia-backend-00002-abc=100

# 3. 或使用 git revert
git revert HEAD
git push origin staging
```

## 📋 環境變數配置

### GitHub Secrets 設定
```yaml
# 資料庫
STAGING_SUPABASE_URL        # Supabase 直連字串 (IPv6)
STAGING_SUPABASE_POOLER_URL # Supabase Pooler 連線字串 (IPv4) ⚠️ CI/CD 必須
STAGING_SUPABASE_PROJECT_URL # Supabase project URL
STAGING_SUPABASE_ANON_KEY   # Supabase anon key

# JWT
STAGING_JWT_SECRET          # JWT 簽名密鑰

# GCP
GCP_SA_KEY                  # Service Account JSON
```

## 📝 部署日誌模板

每次部署後記錄：
```markdown
### 部署記錄 - [日期]
- **版本**: v1.x.x
- **環境**: staging/production
- **部署者**: [姓名]
- **變更內容**:
  - Feature: xxx
  - Fix: xxx
- **測試結果**:
  - [ ] 健康檢查通過
  - [ ] API 測試通過
  - [ ] 前端測試通過
- **問題**: 無/[描述問題]
- **Cloud SQL 狀態**: STOPPED/RUNNABLE
- **預估成本影響**: $0
```

## 🚨 緊急聯絡

發現以下情況立即處理：
1. Cloud SQL 實例 tier 不是 micro
2. 每日帳單 > $10 USD
3. 生產環境服務中斷
4. 資料庫被誤刪

處理步驟：
1. 立即停止問題資源
2. 通知團隊
3. 記錄事件
4. 事後檢討

---

**記住**：寧可多檢查一次，不要產生巨額帳單！
