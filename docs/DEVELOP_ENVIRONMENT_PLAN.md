# Develop 測試環境實作計劃

> **目標**：新增一個 `develop` 測試環境，用於長期功能開發測試，與 staging 環境共用資料庫但獨立部署。

---

## 📋 目錄

- [1. 需求分析](#1-需求分析)
- [2. 架構設計](#2-架構設計)
- [3. Migration 相容性策略](#3-migration-相容性策略)
- [4. 實作步驟](#4-實作步驟)
- [5. 風險評估與緩解](#5-風險評估與緩解)
- [6. 測試計劃](#6-測試計劃)
- [7. 維護指南](#7-維護指南)

---

## 1. 需求分析

### 1.1 業務需求

**問題**：
- Sentence Making 功能需要長期測試（數週）
- 直接進 staging 會阻塞其他快速上線的功能
- 其他團隊成員需要快速 staging → production 流程

**解決方案**：
- 新增 `develop` 環境作為長期功能測試環境
- `staging` 保持為快速發布環境
- `develop` 與 `staging` 共用資料庫（降低成本）

### 1.2 技術需求

| 項目 | 需求 |
|-----|------|
| **Cloud Run 服務** | 新增 `duotopia-backend-develop` 和 `duotopia-frontend-develop` |
| **資料庫** | 共用 `staging` 的 Supabase 資料庫 |
| **分支策略** | `staging` → `develop` → `feature-sentence` merge |
| **部署觸發** | Push 到 `develop` 分支自動部署 |
| **Migration** | 必須向前相容（forward-compatible） |

---

## 2. 架構設計

### 2.1 環境架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      Duotopia 環境架構                        │
└─────────────────────────────────────────────────────────────┘

Production 環境 (main 分支)
  ├─ Cloud Run: duotopia-backend-production
  ├─ Cloud Run: duotopia-frontend-production
  └─ Database: Production Supabase (獨立)

Staging 環境 (staging 分支) ⚡ 快速發布
  ├─ Cloud Run: duotopia-backend-staging
  ├─ Cloud Run: duotopia-frontend-staging
  └─ Database: Staging Supabase ◄─┐
                                   │
Develop 環境 (develop 分支) 🧪 長期測試  │ 共用
  ├─ Cloud Run: duotopia-backend-develop  │
  ├─ Cloud Run: duotopia-frontend-develop │
  └─ Database: Staging Supabase ◄─────────┘
```

### 2.2 分支策略

```
main (production)
  ↑
staging (快速發布) ←─ 其他功能分支快速 merge
  ↑
develop (長期測試) ←─ feature-sentence merge
  ↑
feature-sentence (造句功能開發)
```

**Workflow**：
1. `feature-sentence` 開發完成 → merge 到 `develop`
2. `develop` 測試通過（數週）→ merge 到 `staging`
3. `staging` 測試通過（數天）→ merge 到 `main`
4. 其他快速功能：直接 merge 到 `staging` → `main`

---

## 3. Migration 相容性策略

### 3.1 核心挑戰

**問題**：develop 和 staging 共用同一個資料庫，但可能有不同的 migration 版本。

**場景分析**：

| 場景 | Develop Migration | Staging Migration | 資料庫 Schema | 結果 |
|-----|-------------------|-------------------|---------------|------|
| ✅ 正常 | v10 | v10 | v10 | 兩邊都正常 |
| ⚠️ Develop 領先 | v12 (新增 table) | v10 | v12 | Staging 可能出錯 |
| ⚠️ Staging 領先 | v10 | v12 (新增 column) | v12 | Develop 缺少欄位 |
| ❌ 衝突 | v12a (rename) | v12b (drop) | ??? | 資料庫損壞 |

### 3.2 解決方案：Forward-Compatible Migration 策略

#### 規則 1：只允許 Additive Changes（新增型變更）

**✅ 允許的 Migration（向前相容）**：
```python
# ✅ 新增表
op.create_table('new_feature_table', ...)

# ✅ 新增欄位（必須有 DEFAULT 或 nullable=True）
op.add_column('users',
    sa.Column('new_field', sa.String(), nullable=True))

# ✅ 新增 Index
op.create_index('idx_new', 'users', ['email'])

# ✅ 新增 Function
op.execute("CREATE FUNCTION ...")
```

**❌ 禁止的 Migration（破壞性變更）**：
```python
# ❌ 刪除欄位
op.drop_column('users', 'old_field')

# ❌ 重新命名
op.alter_column('users', 'name', new_column_name='full_name')

# ❌ 修改欄位型別
op.alter_column('users', 'age', type_=sa.String())

# ❌ 刪除表
op.drop_table('old_table')
```

#### 規則 2：Develop Migration 執行時機

**選項 A：Stamp Only（推薦用於 develop）**
```yaml
# develop 環境不執行 migration，只更新版本記錄
- name: Stamp Migration Version (Develop)
  run: |
    alembic stamp head  # 只更新記錄，不執行 SQL
```

**選項 B：Conditional Upgrade（允許新增型變更）**
```yaml
# develop 可以執行新 migration，但需要檢查相容性
- name: Run Migration with Compatibility Check
  run: |
    # 檢查是否為 additive migration
    alembic upgrade head --sql > migration.sql

    # 檢查是否包含破壞性變更
    if grep -E "(DROP|ALTER.*DROP|RENAME)" migration.sql; then
      echo "❌ 破壞性變更不允許在 develop 環境執行"
      exit 1
    fi

    alembic upgrade head
```

#### 規則 3：Migration 版本管理

**Develop 環境 Migration 流程**：

```bash
# 1. 在 develop 分支創建新 migration
cd backend
alembic revision --autogenerate -m "add_sentence_making_tables"

# 2. 檢查 migration 是否為 additive
git diff backend/alembic/versions/*.py
# 確認只有 CREATE TABLE, ADD COLUMN 等新增型變更

# 3. Merge 到 develop，觸發部署
git checkout develop
git merge feature-sentence
git push origin develop

# 4. CI/CD 執行 migration（或 stamp）
# develop 環境啟動，使用新 schema

# 5. Staging 更新時
git checkout staging
git merge develop
git push origin staging
# staging CI/CD 執行相同的 migration
```

### 3.3 Migration 相容性檢查腳本

```python
# backend/scripts/check_migration_compatibility.py
"""
檢查 migration 是否為 forward-compatible
"""
import re
import sys
from pathlib import Path

def check_migration_file(filepath: Path) -> bool:
    """檢查單個 migration 檔案"""
    content = filepath.read_text()

    # 破壞性關鍵字
    destructive_patterns = [
        r'op\.drop_table',
        r'op\.drop_column',
        r'op\.alter_column.*new_column_name',
        r'DROP\s+TABLE',
        r'DROP\s+COLUMN',
        r'ALTER\s+TABLE.*DROP',
        r'RENAME\s+COLUMN',
    ]

    for pattern in destructive_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            print(f"❌ 發現破壞性變更: {pattern}")
            print(f"   檔案: {filepath}")
            return False

    print(f"✅ {filepath.name} 是 forward-compatible")
    return True

if __name__ == "__main__":
    # 檢查最新的 migration
    versions_dir = Path("backend/alembic/versions")
    latest_files = sorted(versions_dir.glob("*.py"),
                         key=lambda p: p.stat().st_mtime)[-3:]

    all_compatible = all(check_migration_file(f) for f in latest_files)
    sys.exit(0 if all_compatible else 1)
```

---

## 4. 實作步驟

### 4.1 階段一：準備工作（30 分鐘）

#### Step 1: 創建 Develop 分支
```bash
# 從 staging 創建 develop 分支
git checkout staging
git pull origin staging
git checkout -b develop
git push -u origin develop
```

#### Step 2: 設定 GitHub Secrets

在 GitHub Repository Settings → Secrets and variables → Actions 新增：

```bash
# Develop 環境 Secrets
DEVELOP_BACKEND_SERVICE=duotopia-backend-develop
DEVELOP_FRONTEND_SERVICE=duotopia-frontend-develop
DEVELOP_BACKEND_URL=https://duotopia-backend-develop-[hash].run.app
DEVELOP_FRONTEND_URL=https://duotopia-frontend-develop-[hash].run.app

# 資料庫設定（與 staging 相同）
DEVELOP_DATABASE_URL=${{ secrets.STAGING_DATABASE_URL }}
DEVELOP_DATABASE_POOLER_URL=${{ secrets.STAGING_DATABASE_POOLER_URL }}
DEVELOP_SUPABASE_URL=${{ secrets.STAGING_SUPABASE_URL }}
DEVELOP_SUPABASE_ANON_KEY=${{ secrets.STAGING_SUPABASE_ANON_KEY }}
DEVELOP_JWT_SECRET=${{ secrets.STAGING_JWT_SECRET }}

# Cron Job Secret
DEVELOP_CRON_SECRET=[generate new random string]

# Payment (使用 staging 設定)
DEVELOP_ENABLE_PAYMENT=${{ secrets.STAGING_ENABLE_PAYMENT }}
```

### 4.2 階段二：修改 CI/CD Workflows（1 小時）

#### Step 3: 修改 `deploy-backend.yml`

```yaml
# .github/workflows/deploy-backend.yml
on:
  workflow_dispatch:
  push:
    branches: [ main, staging, develop ]  # ← 新增 develop
    paths:
      - 'backend/**'
      # ... 其他路徑

jobs:
  deploy-backend:
    # ... 前面的步驟相同

    - name: Set Environment Variables
      id: env_vars
      run: |
        if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          echo "ENV_NAME=production" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.PRODUCTION_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🚀 Deploying to PRODUCTION"
        elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
          echo "ENV_NAME=develop" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.DEVELOP_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🧪 Deploying to DEVELOP"
        else
          echo "ENV_NAME=staging" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.STAGING_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🧪 Deploying to STAGING"
        fi

    - name: Set Database Environment Variables
      id: db_env
      run: |
        if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          # Production 設定
          echo "DATABASE_URL=${{ secrets.PRODUCTION_DATABASE_URL }}" >> $GITHUB_OUTPUT
          # ... 其他 production 變數
        elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
          # Develop 使用 Staging 資料庫
          echo "DATABASE_URL=${{ secrets.DEVELOP_DATABASE_URL }}" >> $GITHUB_OUTPUT
          echo "ALEMBIC_DATABASE_URL=${{ secrets.DEVELOP_DATABASE_POOLER_URL }}" >> $GITHUB_OUTPUT
          echo "SUPABASE_URL=${{ secrets.DEVELOP_SUPABASE_URL }}" >> $GITHUB_OUTPUT
          echo "SUPABASE_KEY=${{ secrets.DEVELOP_SUPABASE_ANON_KEY }}" >> $GITHUB_OUTPUT
          echo "JWT_SECRET=${{ secrets.DEVELOP_JWT_SECRET }}" >> $GITHUB_OUTPUT
          echo "FRONTEND_URL=${{ secrets.DEVELOP_FRONTEND_URL }}" >> $GITHUB_OUTPUT
          echo "🧪 Using Staging Database (Shared with Develop)"
        else
          # Staging 設定
          echo "DATABASE_URL=${{ secrets.STAGING_DATABASE_URL }}" >> $GITHUB_OUTPUT
          # ... 其他 staging 變數
        fi

    # ⚠️ 關鍵：Develop 環境的 Migration 策略
    - name: Run Alembic database migrations
      env:
        DATABASE_URL: ${{ steps.db_env.outputs.ALEMBIC_DATABASE_URL }}
      run: |
        echo "🔍 Installing dependencies for migrations..."
        pip install -r backend/requirements.txt

        cd backend

        if [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
          # Develop 環境：檢查 migration 相容性
          echo "🔍 Checking migration compatibility for develop..."

          # 檢查是否有破壞性變更
          python ../scripts/check_migration_compatibility.py

          # 選項 A：只 stamp 版本（推薦）
          echo "📌 Stamping migration version (no SQL execution)..."
          alembic current
          alembic stamp head
          echo "✅ Migration version updated (stamped)"

          # 選項 B：執行 migration（如果確認為 additive）
          # echo "🔄 Running additive migrations only..."
          # alembic upgrade head
        else
          # Production & Staging：正常執行 migration
          echo "🔄 Running Alembic database migrations..."
          alembic current
          alembic upgrade head
          echo "✅ Migrations completed"
        fi

    # ... 其餘步驟相同
```

#### Step 4: 修改 `deploy-frontend.yml`

```yaml
# .github/workflows/deploy-frontend.yml
on:
  workflow_dispatch:
  push:
    branches: [ main, staging, develop ]  # ← 新增 develop
    paths:
      - 'frontend/**'
      # ... 其他路徑

jobs:
  deploy-frontend:
    # ... 前面的步驟相同

    - name: Set Environment Variables
      id: env_vars
      run: |
        if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
          echo "ENV_NAME=production" >> $GITHUB_OUTPUT
          echo "FRONTEND_SERVICE=${{ secrets.PRODUCTION_FRONTEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.PRODUCTION_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🚀 Deploying to PRODUCTION"
        elif [[ "${{ github.ref }}" == "refs/heads/develop" ]]; then
          echo "ENV_NAME=develop" >> $GITHUB_OUTPUT
          echo "FRONTEND_SERVICE=${{ secrets.DEVELOP_FRONTEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.DEVELOP_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🧪 Deploying to DEVELOP"
        else
          echo "ENV_NAME=staging" >> $GITHUB_OUTPUT
          echo "FRONTEND_SERVICE=${{ secrets.STAGING_FRONTEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "BACKEND_SERVICE=${{ secrets.STAGING_BACKEND_SERVICE }}" >> $GITHUB_OUTPUT
          echo "🧪 Deploying to STAGING"
        fi

    # ... 其餘步驟相同
```

### 4.3 階段三：Migration 相容性檢查腳本（30 分鐘）

#### Step 5: 新增 Migration 檢查腳本

創建 `backend/scripts/check_migration_compatibility.py`（內容見 3.3 節）

#### Step 6: 測試腳本

```bash
cd backend
python scripts/check_migration_compatibility.py
```

### 4.4 階段四：首次部署測試（1 小時）

#### Step 7: Merge feature-sentence 到 develop

```bash
# 確保 feature-sentence 是最新的
git checkout feature-sentence
git pull origin feature-sentence

# Merge 到 develop
git checkout develop
git merge feature-sentence

# 解決衝突（如果有）
git status

# 推送觸發部署
git push origin develop
```

#### Step 8: 監控部署過程

在 GitHub Actions 查看部署進度：
1. 前往 `https://github.com/[your-org]/duotopia/actions`
2. 查看 "Deploy Backend" 和 "Deploy Frontend" workflows
3. 確認 develop 環境成功部署

#### Step 9: 驗證 Develop 環境

```bash
# 1. 檢查 Cloud Run 服務
gcloud run services list --region=asia-east1 | grep develop

# 2. 檢查 Backend Health
DEVELOP_BACKEND_URL=$(gcloud run services describe duotopia-backend-develop \
  --region=asia-east1 --format='value(status.url)')
curl $DEVELOP_BACKEND_URL/api/health

# 3. 檢查 Frontend
DEVELOP_FRONTEND_URL=$(gcloud run services describe duotopia-frontend-develop \
  --region=asia-east1 --format='value(status.url)')
curl $DEVELOP_FRONTEND_URL

# 4. 檢查資料庫 Migration 版本
psql $STAGING_DATABASE_URL -c "SELECT * FROM alembic_version;"
```

---

## 5. 風險評估與緩解

### 5.1 Migration 衝突風險

| 風險 | 機率 | 影響 | 緩解措施 |
|-----|------|------|---------|
| Develop 執行破壞性 migration 導致 staging 出錯 | 中 | 高 | 1. Migration 相容性檢查腳本<br>2. Code review 強制檢查<br>3. 使用 stamp 而非 upgrade |
| Staging 更新 migration，develop 落後 | 高 | 低 | 定期將 staging merge 回 develop |
| 兩個環境同時修改資料庫 | 低 | 高 | 明確的 merge 順序：develop → staging → main |

### 5.2 資料汙染風險

| 風險 | 機率 | 影響 | 緩解措施 |
|-----|------|------|---------|
| Develop 測試資料汙染 staging | 中 | 中 | 1. 使用特定前綴標記測試資料<br>2. 定期清理測試帳號<br>3. 考慮使用 feature flags 隔離功能 |
| Staging 生產資料被 develop 修改 | 低 | 高 | 1. 測試帳號權限限制<br>2. RLS 策略隔離 |

### 5.3 成本控制

| 項目 | 預估成本 | 優化建議 |
|-----|---------|---------|
| Cloud Run (develop) | $10-20/月 | min-instances=0, 閒置時自動停止 |
| Artifact Registry | $5/月 | 定期清理舊 images |
| **總計** | **$15-25/月** | 遠低於獨立資料庫方案（+$25/月） |

---

## 6. 測試計劃

### 6.1 部署測試清單

**初次部署測試**：
- [ ] Develop 分支成功創建
- [ ] GitHub Secrets 正確設定
- [ ] Backend 服務成功部署
- [ ] Frontend 服務成功部署
- [ ] Health check 通過
- [ ] Migration 版本正確（與 staging 相同或領先一版）

**功能測試**：
- [ ] Develop 環境可以正常登入
- [ ] Sentence Making 功能正常運作
- [ ] Staging 環境未受影響
- [ ] 兩環境資料庫連接正常

### 6.2 Migration 相容性測試

**測試場景 1：Develop 領先**
```bash
# 1. Develop 執行新 migration
git checkout develop
# 創建新 migration（只新增欄位）
alembic revision --autogenerate -m "add_test_field"
git push origin develop

# 2. 等待 deploy 完成

# 3. 檢查 Staging 是否正常
curl $STAGING_BACKEND_URL/api/health
# 應該仍然正常，因為新欄位為 nullable

# 4. Merge 到 Staging
git checkout staging
git merge develop
git push origin staging

# 5. 確認 Staging migration 升級
```

**測試場景 2：破壞性變更阻擋**
```bash
# 1. 嘗試創建破壞性 migration
alembic revision --autogenerate -m "drop_old_column"
# 手動編輯：op.drop_column('users', 'old_field')

# 2. Push 到 develop
git push origin develop

# 3. CI/CD 應該失敗
# 檢查 Actions 日誌應顯示：
# "❌ 破壞性變更不允許在 develop 環境執行"
```

---

## 7. 維護指南

### 7.1 日常維護流程

**每週檢查**：
```bash
# 1. 檢查 develop 和 staging migration 版本差異
cd backend
alembic current  # 在 develop 環境
alembic current  # 在 staging 環境

# 2. 如果差異超過 3 個版本，考慮同步
git checkout develop
git merge staging
git push origin develop
```

**每月檢查**：
- 清理 Artifact Registry 舊 images
- 檢查 Cloud Run 成本
- 清理測試資料

### 7.2 升級流程

**Develop → Staging**：
```bash
# 1. 確認 develop 測試完成
# 2. Merge 到 staging
git checkout staging
git pull origin staging
git merge develop
git push origin staging

# 3. 監控 staging 部署
# 4. 執行 staging 測試
```

**Staging → Production**：
```bash
# 1. 確認 staging 測試完成
# 2. Merge 到 main
git checkout main
git pull origin main
git merge staging
git push origin main

# 3. 監控 production 部署
```

### 7.3 緊急回滾

如果 develop 環境出現嚴重問題：

```bash
# 方案 A：回滾代碼
git checkout develop
git reset --hard HEAD~1  # 回到上一個 commit
git push -f origin develop

# 方案 B：暫停 develop 服務
gcloud run services update duotopia-backend-develop \
  --region=asia-east1 \
  --min-instances=0 \
  --max-instances=0

# 方案 C：刪除 develop 服務（極端情況）
gcloud run services delete duotopia-backend-develop --region=asia-east1
gcloud run services delete duotopia-frontend-develop --region=asia-east1
```

---

## 8. 實作檢查清單

### 8.1 準備階段
- [ ] 創建 `develop` 分支
- [ ] 設定 GitHub Secrets（12 個 secrets）
- [ ] 創建 migration 檢查腳本

### 8.2 CI/CD 設定
- [ ] 修改 `deploy-backend.yml`
- [ ] 修改 `deploy-frontend.yml`
- [ ] 測試 workflows 語法

### 8.3 部署測試
- [ ] Push 到 develop 觸發首次部署
- [ ] 驗證 Backend 服務
- [ ] 驗證 Frontend 服務
- [ ] 檢查 Migration 版本
- [ ] 功能測試

### 8.4 文檔更新
- [ ] 更新 README.md（新增 develop 環境說明）
- [ ] 更新 CICD.md（新增 develop workflow）
- [ ] 創建 DEVELOP_ENVIRONMENT.md（本文件）

---

## 9. 常見問題 (FAQ)

### Q1: Develop 和 Staging 可以同時修改資料庫嗎？

**A**: 可以，但需要遵守以下規則：
- Develop 只能執行 **additive migrations**（新增型變更）
- Staging 可以執行任何 migration
- 當 staging migration 領先時，定期 merge 回 develop

### Q2: 如果 Develop 需要測試破壞性變更怎麼辦？

**A**: 有兩個選擇：
1. **推薦**：直接 merge 到 staging 測試（快速功能）
2. **替代方案**：臨時創建獨立的 Supabase 專案（需額外成本）

### Q3: Migration 檢查腳本會影響部署速度嗎？

**A**: 不會。檢查腳本只是讀取檔案內容做正則匹配，耗時 < 1 秒。

### Q4: Develop 環境的成本是多少？

**A**:
- Cloud Run: ~$15-20/月（min-instances=0 時）
- Artifact Registry: ~$5/月
- **總計**: ~$20-25/月（無需額外資料庫）

### Q5: 測試資料會影響 Staging 嗎？

**A**: 可能會。建議：
- 使用 `dev_` 前綴標記測試帳號
- 定期清理測試資料
- 考慮使用 RLS 策略隔離

---

## 10. 下一步行動

### 立即執行（今天）
1. ✅ 創建 `develop` 分支
2. ✅ 設定 GitHub Secrets
3. ✅ 修改 CI/CD workflows

### 本週執行
4. ✅ 測試首次部署
5. ✅ 驗證 Migration 相容性
6. ✅ 文檔更新

### 持續優化
7. 監控成本
8. 優化 Migration 流程
9. 收集團隊反饋

---

## 附錄

### A. GitHub Secrets 完整清單

```bash
# Backend Services
DEVELOP_BACKEND_SERVICE=duotopia-backend-develop

# Frontend Services
DEVELOP_FRONTEND_SERVICE=duotopia-frontend-develop

# URLs
DEVELOP_BACKEND_URL=https://duotopia-backend-develop-[hash].run.app
DEVELOP_FRONTEND_URL=https://duotopia-frontend-develop-[hash].run.app

# Database (與 Staging 相同)
DEVELOP_DATABASE_URL=[same as STAGING_DATABASE_URL]
DEVELOP_DATABASE_POOLER_URL=[same as STAGING_DATABASE_POOLER_URL]
DEVELOP_SUPABASE_URL=[same as STAGING_SUPABASE_URL]
DEVELOP_SUPABASE_ANON_KEY=[same as STAGING_SUPABASE_ANON_KEY]

# Auth
DEVELOP_JWT_SECRET=[same as STAGING_JWT_SECRET]

# Cron
DEVELOP_CRON_SECRET=[generate new]

# Payment
DEVELOP_ENABLE_PAYMENT=[same as STAGING_ENABLE_PAYMENT]
```

### B. 相關文件連結

- [CI/CD 文檔](./CICD.md)
- [Migration 指南](./backend/alembic/README.md)
- [Deployment Status](./DEPLOYMENT_STATUS.md)

---

**文件版本**: v1.0
**最後更新**: 2025-11-16
**作者**: Claude Code
**審核狀態**: ⏳ 待審核
