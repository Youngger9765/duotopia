# CICD.md - Duotopia CI/CD 部署準則

本文件規範 Duotopia 專案的 CI/CD 流程與部署準則，避免重複犯錯。

---

## 🔗 Related Documentation

- **Git Workflow**: See [.claude/agents/git-issue-pr-flow.md](./.claude/agents/git-issue-pr-flow.md)
- **Agent System**: See [CLAUDE.md](./CLAUDE.md)
- **TapPay Integration**: See [docs/integrations/TAPPAY_INTEGRATION_GUIDE.md](./docs/integrations/TAPPAY_INTEGRATION_GUIDE.md)
- **Organization Hierarchy**: See [ORG_IMPLEMENTATION_SPEC.md](./ORG_IMPLEMENTATION_SPEC.md)

---

## 🔴 最高原則：使用 Supabase 免費方案

### 資料庫策略
- **Staging**: Supabase（免費）
- **Production**: Supabase（免費）
- **本地開發**: Docker PostgreSQL
- **成本**: $0/月（完全免費）

## 📋 部署前檢查清單

### 1. 配置檢查
- [ ] 確認 `gcloud config get-value project` 顯示 `duotopia-472708`
- [ ] 確認區域是 `asia-east1`
- [ ] 確認沒有硬編碼的 localhost URL
- [ ] 確認沒有舊的 import 路徑

### 2. 程式碼品質檢查
- [ ] **Frontend**: Prettier 格式化 (`npx prettier --check frontend/src`)
- [ ] **Frontend**: TypeScript 編譯 (`npm run typecheck`)
- [ ] **Frontend**: ESLint 檢查 (`npm run lint:ci`)
- [ ] **Backend**: Black 格式化 (`black --check backend/`)
- [ ] **Backend**: Flake8 檢查 (`flake8 backend/`)
- [ ] **Backend**: pytest 測試 (`pytest`)

### 3. 環境變數檢查
- [ ] Supabase URL 和 Key 已設定
- [ ] JWT Secret 已設定
- [ ] OpenAI API Key 已設定（如需要）

## 🎨 程式碼格式化策略（AI 輔助開發）

### 設計哲學
**只擋會影響 Production 的錯誤，其他都是摩擦**

### Pre-commit Hooks（Commit 階段）
執行時間 < 10 秒，只檢查會導致 runtime 錯誤的項目：

**✅ 必須通過**：
- TypeScript 編譯檢查 (5-8s)
- Python Import patterns (<1s) - 防止 UnboundLocalError
- 安全檢查 (3s) - 防止密碼洩漏
- 基本檔案檢查 (1s) - 防止 .db/.env 被 commit

**❌ 移除項目**（移到手動執行）：
- Black/Flake8/Autoflake - 純格式化
- ESLint - 純格式化
- Prettier - 純格式化
- Frontend tests - 太慢
- Alembic check - 改 models 才需要

### CI/CD 檢查（Push 後執行）
GitHub Actions 會執行完整的格式化與測試檢查：

**Frontend (`deploy-frontend.yml`)**：
1. Prettier 格式化檢查
2. TypeScript 型別檢查
3. ESLint 程式碼檢查
4. Vite 建置測試
5. API 測試框架

**Backend (`deploy-backend.yml`)**：
1. Black 格式化檢查
2. Flake8 程式碼檢查
3. pytest 單元測試
4. Alembic migration 檢查

### 手動格式化（需要時執行）
```bash
# Frontend 格式化
npx prettier --write frontend/src

# Backend 格式化
cd backend && black . && autoflake --in-place --recursive .

# 檢查格式（不修改）
npx prettier --check frontend/src
cd backend && black --check .
```

### 為什麼這樣設計？
1. **本地 commit 快速** - AI 輔助開發需要快速迭代
2. **CI/CD 嚴格把關** - 確保 push 到遠端的程式碼品質
3. **手動格式化可選** - 只在需要時整理程式碼
4. **避免格式化阻擋開發** - 格式問題不應該阻止進度

### 格式化執行時機
| 階段 | 檢查項目 | 執行時間 | 失敗是否阻擋 |
|------|---------|---------|-------------|
| **Commit** | TypeScript, Import, 安全 | < 10s | 🔴 是 |
| **Push (CI/CD)** | 格式化 + 測試 + 建置 | ~2-3min | 🔴 是 |
| **手動** | 格式化整理 | 依需求 | ⚠️ 否 |

## 🚀 標準部署流程

### 開發環境部署
```bash
# 1. 本地測試
npm run typecheck
npm run lint
npm run build
cd backend && python -m pytest

# 2. 推送到 staging
git push origin staging

# 3. 監控部署
gh run watch

# 4. 驗證部署
curl https://duotopia-backend-staging-xxx.run.app/health
```

### 生產環境部署
```bash
# 1. 確認 staging 測試通過
# 2. 創建 PR 到 main branch
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

# 健康檢查
curl https://duotopia-backend-staging-xxx.run.app/health
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
**原因**: GitHub Actions 缺少 Pooler URL (IPv4)
**解決**: 設定 `STAGING_SUPABASE_POOLER_URL` (見下方 Supabase Pooler 設定)

### 3. Import 路徑錯誤
**錯誤**: Module not found
**原因**: TypeScript 路徑別名
**解決**: 使用相對路徑而非 @/

## 💰 成本控制檢查點

### 每日檢查
```bash
# 檢查 Cloud Run
gcloud run services list
# 確認 min-instances = 0

# 檢查 Supabase 使用量
# 登入 Supabase Dashboard 查看使用量
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
- ✅ Supabase 連線正常

### 性能指標
- 冷啟動時間 < 10s
- 健康檢查回應 < 1s
- Docker 映像 < 500MB
- 記憶體使用 < 512MB

## 🔍 自動化部署驗證

### CI/CD 內建驗證流程
每次部署完成後，GitHub Actions 會自動執行以下驗證：

#### Backend 部署驗證
```bash
🔍 Deployment Verification
├── 1️⃣ Cloud Run 部署確認
│   ├── ✅ Latest revision: duotopia-staging-backend-00040-q46
│   └── ✅ Created at: 2025-09-29T00:49:59.255381Z
├── 2️⃣ 服務健康檢查
│   ├── 🩺 GET /health
│   ├── ✅ Health check passed
│   └── 📊 Health response: {"status":"healthy","environment":"staging"}
└── 3️⃣ 環境變數驗證
    └── ✅ Environment correctly set to: staging
```

#### Frontend 部署驗證
```bash
🔍 Deployment Verification
├── 1️⃣ Cloud Run 部署確認
│   ├── ✅ Latest revision: duotopia-staging-frontend-00032-m2m
│   └── ✅ Created at: 2025-09-29T00:46:58.826089Z
├── 2️⃣ 前端頁面檢查
│   ├── 🌐 GET / (首頁)
│   ├── ✅ Frontend page loads correctly
│   └── ✅ Found Duotopia title
├── 3️⃣ 資產編譯驗證
│   ├── ✅ Frontend assets compiled correctly
│   └── 🔧 Backend URL configured: https://duotopia-staging-backend-xxx.run.app
└── 4️⃣ API 連接設定確認
    └── 📝 確認前端正確設定後端 API URL
```

### 驗證失敗處理
如果任何驗證步驟失敗，部署會**自動標記為失敗**：
- ❌ 健康檢查失敗 → exit 1
- ❌ 前端頁面無法載入 → exit 1
- ❌ 環境設定錯誤 → 警告但繼續

### 手動驗證指令
```bash
# 檢查最新部署版本
gcloud run revisions list --service duotopia-staging-backend --limit 1

# 健康檢查
curl -s https://duotopia-staging-backend-xxx.run.app/health | jq

# 前端檢查
curl -s https://duotopia-staging-frontend-xxx.run.app/ | grep -o "<title>.*</title>"
```

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

#### 第二層：Alembic 指令
```bash
# 檢查是否需要 migration
cd backend && alembic check

# 生成 migration
cd backend && alembic revision --autogenerate -m "add new field"

# 執行 migration
cd backend && alembic upgrade head
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

## 🔒 Supabase Row Level Security (RLS) 管理

### ⚠️ 重要：建立新資料表時必須啟用 RLS！

所有儲存在 Supabase 的業務資料表**必須啟用 Row Level Security (RLS)**，否則會造成嚴重的資料安全漏洞。

### RLS 是什麼？

**Row Level Security = 行級安全控制**

功能：控制誰可以存取資料庫的哪些資料

範例：
```sql
-- ❌ 沒有 RLS：任何人都能看到所有老師資料
SELECT * FROM teachers;  -- 可看到所有老師的 email、付款記錄

-- ✅ 有 RLS：只能看到自己的資料
SELECT * FROM teachers WHERE id = 當前登入的老師ID;
```

### 為什麼 Alembic Migration 不會自動啟用 RLS？

- **Supabase Dashboard** 建立的表 → ✅ 自動啟用 RLS
- **Alembic Migration** 建立的表 → ❌ **不會自動啟用 RLS**

因此，使用 Alembic 建表時，**必須手動在 migration 中加入 RLS 配置**。

### RLS Migration 標準流程

#### 1. 使用 RLS Template

專案已提供完整的 RLS Template：`backend/alembic/rls_template.py`

#### 2. Migration 範例（建立教師專屬資料表）

```python
"""add courses table

Revision ID: xxx
"""
from alembic import op
import sqlalchemy as sa

# 🔒 匯入 RLS 函數
from alembic.rls_template import (
    enable_rls,
    disable_rls,
    create_teacher_only_policies,
    drop_all_policies,
)

def upgrade() -> None:
    # 1️⃣ 建立資料表
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
    )

    # 2️⃣ 啟用 RLS（必須！）
    enable_rls('courses')

    # 3️⃣ 建立 Policies（必須！）
    # 教師只能存取自己的課程
    create_teacher_only_policies(
        'courses',
        owner_column='teacher_id',
        allow_insert=True,
        allow_update=True,
        allow_delete=True,
    )

def downgrade() -> None:
    # 1️⃣ 刪除 Policies
    drop_all_policies('courses')

    # 2️⃣ 關閉 RLS
    disable_rls('courses')

    # 3️⃣ 刪除資料表
    op.drop_table('courses')
```

#### 3. 不同類型資料表的 Policy 選擇

| 資料表類型 | 使用的 Policy 函數 | 說明 |
|-----------|------------------|------|
| 教師專屬資料 | `create_teacher_only_policies()` | 班級、課程、作業範本 |
| 學生專屬資料 | `create_student_only_policies()` | 學生進度、學生答案 |
| 師生共享資料 | `create_teacher_student_shared_policies()` | 作業派發（教師派，學生做） |
| JOIN 關聯資料 | `create_join_based_policies()` | 沒有直接 student_id 的表 |

範例參考：`backend/alembic/rls_template.py` 有完整說明

### RLS 自動檢查機制（四層防護）

#### 第一層：Pre-commit Hook 提醒
```bash
# commit 時如果修改了 alembic/versions/*.py，會顯示提醒：
⚠️ 重要提醒：新增 migration 時記得啟用 RLS！
參考：backend/alembic/rls_template.py
檢查：enable_rls(表名) + create_*_policies(表名)
```

#### 第二層：本地手動檢查
```bash
# 隨時可以執行 RLS 檢查腳本
export DATABASE_URL=$STAGING_SUPABASE_POOLER_URL
./scripts/check_rls.sh

# 輸出範例：
🔍 檢查 Supabase RLS 配置...
1️⃣ 檢查未啟用 RLS 的資料表...
✅ 所有業務資料表都已啟用 RLS

2️⃣ 檢查已啟用 RLS 但缺少 Policy 的資料表...
✅ 所有啟用 RLS 的表都有 Policy

3️⃣ RLS 配置摘要...
 tablename | rls_enabled | policies
-----------+-------------+----------
 teachers  |     ✅      |    2
 students  |     ✅      |    3
 ...
```

#### 第三層：CI/CD 自動驗證
GitHub Actions 會在部署前自動檢查：

```yaml
- name: 🔒 Verify RLS Configuration
  run: |
    # 檢查是否有表未啟用 RLS
    # 如果有 → 部署失敗 ❌
    # 如果沒有 → 繼續部署 ✅
```

#### 第四層：Supabase Security Advisor
Supabase Dashboard 會定期掃描並發送警告郵件

### RLS 快速檢查指令

```bash
# 檢查 Staging 環境
export DATABASE_URL=$(grep STAGING_SUPABASE_POOLER_URL .env.staging | cut -d '=' -f2)
./scripts/check_rls.sh

# 檢查 Production 環境
export DATABASE_URL=$(grep PRODUCTION_SUPABASE_POOLER_URL .env.production | cut -d '=' -f2)
./scripts/check_rls.sh
```

### 如果忘記啟用 RLS 怎麼辦？

#### 方法一：修改 Migration（推薦）
```bash
# 1. 編輯 migration 檔案，加入 RLS 配置
# 2. 重新執行 migration
cd backend
alembic downgrade -1
alembic upgrade head
```

#### 方法二：手動執行修復腳本
```bash
# 使用專案提供的 RLS 修復腳本
export PGPASSWORD=你的密碼
psql "你的資料庫URL" -f backend/migrations/enable_rls_all_tables.sql
```

### RLS 最佳實踐總結

✅ **DO（必須做）**：
- 每次建立新表時**必須**啟用 RLS
- 使用 `rls_template.py` 提供的標準函數
- 本地測試時驗證 RLS Policy 是否正確
- Commit 前執行 `./scripts/check_rls.sh` 檢查

❌ **DON'T（絕對不要）**：
- 建表後忘記啟用 RLS
- 啟用 RLS 但沒有建立 Policy（表會無法存取）
- 跳過 CI/CD 的 RLS 檢查
- 忽略 Supabase Security Advisor 警告

### 參考資源

- **RLS Template**：`backend/alembic/rls_template.py`
- **修復腳本**：`backend/migrations/enable_rls_all_tables.sql`
- **檢查腳本**：`scripts/check_rls.sh`
- **Supabase 官方文件**：https://supabase.com/docs/guides/database/postgres/row-level-security

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

# TapPay Payment（⚠️ 重要：區分 Sandbox 和 Production）
TAPPAY_SANDBOX_APP_ID       # Sandbox APP ID (測試用)
TAPPAY_SANDBOX_APP_KEY      # Sandbox APP KEY (測試用)
TAPPAY_SANDBOX_PARTNER_KEY  # Sandbox PARTNER KEY (測試用)
TAPPAY_SANDBOX_MERCHANT_ID  # Sandbox MERCHANT ID (測試用)

TAPPAY_PRODUCTION_APP_ID    # Production APP ID (正式環境)
TAPPAY_PRODUCTION_APP_KEY   # Production APP KEY (正式環境)
TAPPAY_PRODUCTION_PARTNER_KEY # Production PARTNER KEY (正式環境)
TAPPAY_PRODUCTION_MERCHANT_ID # Production MERCHANT ID (正式環境)

# GCP
GCP_SA_KEY                  # Service Account JSON
```

### ⚠️ TapPay 配置重要注意事項

#### Frontend 環境變數命名規則
Frontend 使用 Vite build-time 注入，必須使用 `VITE_TAPPAY_PRODUCTION_*` 前綴：

```yaml
# ❌ 錯誤：這樣會導致 appKey = undefined
--build-arg VITE_TAPPAY_APP_ID=xxx
--build-arg VITE_TAPPAY_APP_KEY=xxx

# ✅ 正確：必須使用 PRODUCTION 前綴
--build-arg VITE_TAPPAY_PRODUCTION_APP_ID=xxx
--build-arg VITE_TAPPAY_PRODUCTION_APP_KEY=xxx
--build-arg VITE_TAPPAY_SERVER_TYPE=production
```

#### Backend 環境變數
Backend 使用 runtime 環境變數，支援雙環境切換：

```yaml
# Backend Cloud Run 環境變數
TAPPAY_ENV=production  # 或 sandbox

# 兩套完整 credentials
TAPPAY_SANDBOX_APP_ID=xxx
TAPPAY_SANDBOX_APP_KEY=xxx
TAPPAY_SANDBOX_PARTNER_KEY=xxx
TAPPAY_SANDBOX_MERCHANT_ID=xxx

TAPPAY_PRODUCTION_APP_ID=xxx
TAPPAY_PRODUCTION_APP_KEY=xxx
TAPPAY_PRODUCTION_PARTNER_KEY=xxx
TAPPAY_PRODUCTION_MERCHANT_ID=xxx
```

#### Staging vs Production 環境配置

**Staging 環境（測試真實刷卡）**：
- Frontend: `VITE_TAPPAY_PRODUCTION_*` + `VITE_TAPPAY_SERVER_TYPE=production`
- Backend: `TAPPAY_ENV=production` + 所有 production credentials

**Production 環境（正式刷卡）**：
- Frontend: `VITE_TAPPAY_PRODUCTION_*` + `VITE_TAPPAY_SERVER_TYPE=production`
- Backend: `TAPPAY_ENV=production` + 所有 production credentials

**本地開發（測試模擬刷卡）**：
- Frontend: `VITE_TAPPAY_SANDBOX_*` + `VITE_TAPPAY_SERVER_TYPE=sandbox`
- Backend: `TAPPAY_ENV=sandbox` + 所有 sandbox credentials

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

## 🔧 GCloud 配置設定

### 確保使用正確的 Duotopia 專案
```bash
# 切換到 Duotopia 配置
gcloud config configurations activate duotopia

# 驗證當前配置
gcloud config list
# 應該顯示：
# account = myduotopia@gmail.com
# project = duotopia-472708

# 或直接設定專案
gcloud config set project duotopia-472708
```

### 重要提醒
- **部署前必須確認專案**: `gcloud config get-value project`
- **應該顯示**: `duotopia-472708`
- **區域**: `asia-east1`

### 🛡️ 隔離環境部署（避免專案互相干擾）
```bash
# 使用 Duotopia 專屬的 gcloud 環境
export CLOUDSDK_CONFIG=$HOME/.gcloud-duotopia
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.11

# 驗證環境
gcloud config list
# 應該顯示：
# account = myduotopia@gmail.com
# project = duotopia-472708
```

## 🚨 部署後測試規則

### 部署完成 ≠ 工作完成
**部署只是第一步，測試通過才算完成！**

### 每次部署後必須：
1. **監控部署進度**：`gh run watch`
2. **健康檢查**：`curl https://your-service-url/health`
3. **檢查錯誤日誌**：`gcloud run logs read duotopia-backend --limit=50 | grep -i error`
4. **測試失敗時立即修復**

**⚠️ 絕對不要推完代碼就不管！每次部署都要監控到成功並測試通過！**

## 🔥 部署錯誤反思與預防

### 常見部署錯誤模式
1. **硬編碼 URL 錯誤**
   - ❌ 錯誤：`fetch('http://localhost:8080/api/...')`
   - ✅ 正確：使用環境變數 `import.meta.env.VITE_API_URL`
   - **教訓**：所有 API URL 必須使用環境變數

2. **PORT 配置錯誤**
   - ❌ 錯誤：Dockerfile 設定 `ENV PORT=8000`
   - ✅ 正確：Cloud Run 預設使用 `PORT=8080`
   - **教訓**：了解部署平台的默認配置

3. **Import 路徑錯誤**
   - ❌ 錯誤：`from models_dual_system import DualUser`
   - ✅ 正確：`from models import User`
   - **教訓**：重構後徹底搜尋舊程式碼

### 系統性預防措施
1. **部署前檢查腳本**（已加入 git hooks）
   ```bash
   # 檢查硬編碼 URL
   grep -r "localhost:[0-9]" frontend/src/ && exit 1
   # 檢查舊的 import
   grep -r "models_dual_system" backend/ && exit 1
   ```

2. **CI/CD 強化**（已實施）
   - Docker 本地測試步驟
   - 健康檢查重試機制（5次）
   - 部署失敗自動顯示日誌

3. **監控流程標準化**
   ```bash
   # 每次推送後立即執行
   gh run watch
   gh run view --log | grep -i error
   ```

4. **診斷優先順序**
   - Container 無法啟動 → 先查 PORT 和 import
   - API 呼叫失敗 → 先查環境變數
   - 資料庫連線失敗 → 先查 DATABASE_URL

### 部署黃金法則
1. **推送前本地測試**：`docker run -p 8080:8080`
2. **推送後立即監控**：`gh run watch`
3. **部署後立即驗證**：`curl /health`
4. **發現問題立即修復**：不要累積技術債

### 啟動時資料庫連線問題
**重要教訓**：絕對不要在應用頂層或啟動時立即連接資料庫！

#### ❌ 錯誤模式（會導致 Cloud Run 失敗）
```python
# main.py 頂層
Base.metadata.create_all(bind=engine)  # 立即連接資料庫！

# lifespan 啟動時
with DatabaseInitializer() as db_init:  # __init__ 就連接資料庫！
    db_init.initialize()
```

#### ✅ 正確模式
```python
# 資料表建立交給 alembic migrations
# 資料庫連線只在處理請求時才建立（透過 Depends(get_db)）
```

**為什麼會失敗**：
- Cloud Run 啟動容器時，環境變數可能還沒完全準備好
- 資料庫可能還在初始化或網路還沒連通
- 任何啟動時的連線失敗都會導致容器無法啟動

### Cloud Scheduler 權限問題
**問題**：GitHub Actions 執行 `gcloud scheduler jobs create` 時出現 `PERMISSION_DENIED`

**原因**：Service Account 缺少 `cloudscheduler.admin` 角色

**解決方案**：
```bash
# 1. 為 GitHub Actions Service Account 添加權限
gcloud projects add-iam-policy-binding duotopia-472708 \
  --member="serviceAccount:github-actions@duotopia-472708.iam.gserviceaccount.com" \
  --role="roles/cloudscheduler.admin"

# 2. 等待 5-10 分鐘讓 IAM 變更傳播

# 3. 重新觸發 Cloud Scheduler workflow
gh workflow run setup-cloud-scheduler.yml -f environment=production
```

**所需的 Service Account 權限**：
- `roles/run.admin` - 部署 Cloud Run
- `roles/iam.serviceAccountUser` - 使用 Service Account
- `roles/cloudscheduler.admin` - 管理 Cloud Scheduler ⚠️ **新增**
- `roles/artifactregistry.writer` - 推送 Docker 映像
- `roles/cloudbuild.builds.editor` - 執行 Cloud Build
- `roles/storage.admin` - 管理 Cloud Storage

**重要提醒**：
- IAM 權限變更需要 5-10 分鐘才會生效
- 如果立即重試會繼續失敗，需要等待傳播完成
- 可以用 `gcloud projects get-iam-policy duotopia-472708` 驗證權限已加入

### 本地測試的重要性
**絕對不要用假資料測試**：
- ❌ `DATABASE_URL="postgresql://dummy:dummy@localhost:5432/dummy"`
- ✅ 使用真實的本地資料庫：`docker-compose up -d`
- ✅ 測試真實的連線：`DATABASE_URL="postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia"`

**每次修改後必須本地測試**：
```bash
# 1. 測試模組載入
python -c "import sys; sys.path.append('backend'); import main"

# 2. 測試服務啟動（如果有依賴）
cd backend && uvicorn main:app --host 0.0.0.0 --port 8080
```

## 💰 成本控制（Supabase 免費方案）

### 當前成本結構
- **資料庫**: $0/月（Supabase 免費方案）
- **Cloud Run**: ~$5-10/月（根據流量）
- **總計**: ~$5-10/月（完全可控）

### 成本監控建議
1. 設定 GCP 預算警報：$20 USD/月
2. 定期檢查 Supabase 使用量
3. 監控 Cloud Run 實例數量

### 最佳實踐
- 使用 Supabase 免費方案（500MB 資料庫 + 2GB 頻寬）
- Cloud Run min-instances = 0（無流量時不收費）
- 定期清理未使用的 Docker 映像

---

**記住**：使用 Supabase 免費方案，成本完全可控！
