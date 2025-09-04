# CI/CD Documentation

## 概述
本專案使用 GitHub Actions 進行持續整合與部署，自動化測試、建置和部署流程。

## 🛡️ 防呆機制（三層防護）

### 第一層：本地 Pre-commit Hook
安裝後，每次 commit 時自動檢查：
```bash
# 安裝
pip install pre-commit
pre-commit install

# 自動執行 alembic check
# 如果 model 有變更但沒有 migration，會阻止 commit
```

### 第二層：Makefile 快捷指令
```bash
# 檢查是否需要 migration
make db-check

# 生成 migration（有提示）
make db-migrate MSG="add new field"

# 執行 migration
make db-upgrade
```

### 第三層：CI/CD 強制檢查
GitHub Actions 會：
1. 執行 `alembic check` 檢查是否有遺漏的 migration
2. 如果有遺漏，**部署會失敗**並顯示錯誤訊息
3. 強制開發者生成 migration 才能部署

## 部署流程

### 觸發條件
- **自動觸發**: Push 到 `staging` 分支
- **手動觸發**: GitHub Actions 頁面的 workflow_dispatch

### 部署階段

#### 1. 測試階段 (Test)
- 前端型別檢查 (TypeScript)
- 前端 ESLint 檢查
- 前端建置測試
- 後端 import 測試

#### 2. 資料庫 Migration (Alembic)
**重要：所有資料庫變更都透過 Alembic 自動執行**

```yaml
- name: Run Alembic database migrations
  env:
    DATABASE_URL: ${{ secrets.STAGING_SUPABASE_URL }}
  working-directory: ./backend
  run: |
    alembic current        # 顯示當前版本
    alembic upgrade head   # 升級到最新
```

**Migration 流程**：
1. CI/CD 自動偵測 `alembic/versions/` 中的新 migration
2. 執行 `alembic upgrade head` 更新資料庫
3. 失敗時會阻止部署，確保資料一致性

#### 3. 建置與部署
- Docker 映像建置
- 推送至 Google Artifact Registry
- 部署到 Cloud Run

#### 4. 健康檢查
- 後端 `/health` endpoint 檢查
- 前端載入檢查
- API proxy 檢查

## Alembic Migration 最佳實踐

### 開發者工作流程

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

### CI/CD 自動執行

每次部署時，GitHub Actions 會：
1. 檢查當前資料庫版本
2. 執行所有 pending migrations
3. 驗證 migration 成功
4. 繼續部署應用程式

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

### 生產環境注意事項

1. **備份優先**
   ```bash
   # 執行 migration 前備份
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

2. **維護窗口**
   - 選擇低流量時段
   - 通知用戶維護時間

3. **監控**
   - 監控 migration 執行時間
   - 檢查應用程式錯誤率
   - 驗證資料完整性

## 環境變數

### Secrets 配置 (GitHub Settings > Secrets)
```yaml
# 資料庫
STAGING_SUPABASE_URL        # Supabase 連線字串
STAGING_SUPABASE_PROJECT_URL # Supabase project URL
STAGING_SUPABASE_ANON_KEY   # Supabase anon key

# JWT
STAGING_JWT_SECRET          # JWT 簽名密鑰

# GCP
GCP_SA_KEY                  # Service Account JSON
```

## 常見問題

### Q: Migration 在 CI/CD 失敗
A: 檢查以下項目：
1. DATABASE_URL 是否正確設定
2. 資料庫是否可連線
3. Migration 檔案是否有語法錯誤
4. 是否有衝突的 migration（多人同時開發）

### Q: 如何回滾 Migration
A:
```bash
# 本地回滾
cd backend
alembic downgrade -1

# 生產環境（謹慎使用）
# 1. 先備份
# 2. 執行回滾
# 3. 部署舊版程式碼
```

### Q: 多人開發 Migration 衝突
A:
1. 溝通協調 migration 順序
2. 使用 branch protection rules
3. Code review migration 檔案
4. 必要時手動合併 migration

## 監控與告警

### 關鍵指標
- Migration 執行時間
- 部署成功率
- 應用程式啟動時間
- 健康檢查通過率

### 日誌查看
```bash
# GitHub Actions logs
gh run list --workflow=deploy-staging-supabase.yml
gh run view <RUN_ID>

# Cloud Run logs
gcloud run logs read duotopia-staging-backend --limit=50
```

## 最佳實踐總結

1. ✅ **永遠使用 Alembic 管理 schema**
2. ✅ **CI/CD 自動執行 migration**
3. ✅ **本地測試每個 migration**
4. ✅ **Review autogenerate 的結果**
5. ✅ **生產環境先備份**
6. ✅ **監控 migration 執行**
7. ❌ **不要手動修改資料庫**
8. ❌ **不要跳過 migration 直接部署**
9. ❌ **不要在高峰期執行 migration**
