# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 最高指導原則：修完要自己去測試過！

## ⚠️ 必須遵守的操作順序 (STOP! READ FIRST!)

### 在執行任何重要操作前，必須按順序檢查：
1. **先查 Makefile** - `make help` 或 `cat Makefile | grep "^[a-z-]*:"`
2. **先查 README** - 了解專案標準流程  
3. **先查 CLAUDE.md** - 了解專案特定規則
4. **先查 package.json/requirements.txt** - 了解已有的腳本命令
5. **絕對不要自作主張創建資源** - 永遠使用專案既有的配置

### 🔴 紅線規則 (絕對禁止)：
- ❌ **不要手動 gcloud 命令創建資源** - 必須用 Makefile
- ❌ **不要猜測版本號** - POSTGRES_15 vs POSTGRES_17 等必須查證
- ❌ **不要忽略專案既有工具** - Makefile, npm scripts 優先
- ❌ **不要在未讀取配置前就執行命令** - 先讀後做

### ✅ 正確操作範例：
```bash
# 錯誤：直接創建 Cloud SQL
gcloud sql instances create duotopia-db-staging --database-version=POSTGRES_15

# 正確：使用 Makefile
make help  # 先看有什麼命令
make db-create  # 使用專案配置創建
```

### ⚡ 每次修改後必須執行的測試流程：

1. **立即編譯測試**
   ```bash
   npm run build  # 確保沒有編譯錯誤
   ```

2. **實際打開瀏覽器檢查**
   ```bash
   open http://localhost:5173/[修改的頁面]
   ```

3. **檢查瀏覽器控制台**
   - 打開 F12 開發者工具
   - 查看 Console 是否有錯誤
   - 檢查 Network 標籤 API 請求

4. **API 功能測試**
   ```bash
   # 寫測試腳本驗證 API
   python test_[功能]_api.py
   ```

5. **截圖存證**
   ```bash
   screencapture -x frontend_[功能]_fixed.png
   ```

**⚠️ 絕對不要讓用戶一直幫你抓錯！每個修復都要自己先測試過！**

## 🔧 GCloud 配置設定

### 確保使用正確的 Duotopia 專案
```bash
# 切換到 Duotopia 配置
gcloud config configurations activate duotopia

# 驗證當前配置
gcloud config list
# 應該顯示：
# account = purpleice9765@msn.com
# project = duotopia-469413

# 或直接設定專案
gcloud config set project duotopia-469413
```

### 重要提醒
- **部署前必須確認專案**: `gcloud config get-value project`
- **應該顯示**: `duotopia-469413`
- **區域**: `asia-east1`

### 🛡️ 隔離環境部署（避免專案互相干擾）
```bash
# 使用 Duotopia 專屬的 gcloud 環境
export CLOUDSDK_CONFIG=$HOME/.gcloud-duotopia
export CLOUDSDK_PYTHON=/opt/homebrew/bin/python3.11

# 驗證環境
gcloud config list
# 應該顯示：
# account = terraform-deploy@duotopia-469413.iam.gserviceaccount.com
# project = duotopia-469413
```

## 🏗️ 平台開發核心原則 - 不要繞遠路

### 🎯 核心教訓：直接用生產級方案，避免技術債

> **"There is nothing more permanent than a temporary solution"**
> 臨時解決方案會變成永久的技術債

### 📊 平台開發鐵則

#### 1. **基礎設施優先 (Infrastructure First)**
```yaml
正確做法 (Day 1)：
✅ Cloud SQL + Cloud Run 從第一天開始
✅ Terraform 管理所有基礎設施
✅ CI/CD pipeline 第一週建立
✅ Secret Manager 管理所有密碼
✅ 監控告警從第一天開始

錯誤做法（避免）：
❌ 用檔案系統當資料庫（如 Base44 BaaS）
❌ 手寫部署腳本（deploy.sh）
❌ 手動管理環境變數
❌ "先簡單後複雜" 的漸進式架構
```

#### 2. **資料架構不妥協 (Data Architecture Non-negotiable)**
```yaml
正確做法：
✅ PostgreSQL 作為 Single Source of Truth
✅ 正確的關聯式設計（外鍵、CASCADE DELETE）
✅ JSONB 處理彈性資料
✅ Redis 作為快取層
✅ 使用成熟的 ORM（如 SQLAlchemy）

錯誤做法：
❌ Base44 entities 當資料庫
❌ 混用多種儲存方式
❌ 沒有外鍵約束
❌ Schema 多次重構
```

#### 3. **DevOps 文化 (Everything as Code)**
```yaml
正確做法：
✅ Infrastructure as Code (Terraform)
✅ Configuration as Code (環境變數)
✅ Deployment as Code (CI/CD)
✅ Immutable Infrastructure
✅ Blue-Green Deployment

錯誤做法：
❌ 手動配置伺服器
❌ SSH 進去修改設定
❌ 部署後手動測試
❌ 沒有回滾機制
```

### 🚀 新專案 Day 1 Checklist

```bash
# Day 1 必須完成（8小時內）：
□ Terraform 專案初始化
□ PostgreSQL + Redis 設定
□ GitHub Actions CI/CD Pipeline
□ 環境分離 (dev/staging/prod)
□ Secret Manager 設定
□ 基本健康檢查 API (/api/health)
□ 監控告警設定
□ 第一個 E2E 測試

# 絕對不要做的事：
✗ 用 BaaS 平台儲存業務資料
✗ 手寫 shell scripts 部署
✗ "暫時" 的解決方案
✗ "之後再加" 的安全措施
✗ 沒有測試就上線
```

## 🚨 測試驅動開發 (TDD)

### 每次修復都必須：
1. **寫測試** - 先寫測試確認問題存在
2. **自己測試** - 實際執行代碼驗證修復
3. **驗證結果** - 確認看到正確的結果

### ⚠️ 重要提醒 - 不要混淆前後端工具！
**前端 (JavaScript/TypeScript)**：
- `package.json` - Node.js 套件管理
- `npm` / `yarn` - 套件安裝工具
- `tsconfig.json` - TypeScript 設定
- `vite.config.ts` - Vite 建置設定

**後端 (Python)**：
- `requirements.txt` - Python 套件管理
- `pip` - Python 套件安裝工具
- `pytest.ini` - pytest 測試設定
- `setup.py` / `pyproject.toml` - Python 專案設定
- **不要把 Python 設定寫在 package.json！**

**通用工具**：
- `Makefile` - 跨語言的快捷指令
- `docker-compose.yml` - 容器編排
- `.env` - 環境變數

### 測試流程：
```bash
# 1. 型別檢查（最重要）
npm run typecheck

# 2. ESLint 檢查
npm run lint

# 3. 單元測試（如果有）
npm test --if-present

# 4. 建置測試
npm run build

# 5. E2E 測試（如果有）
npx playwright test --if-present
```

**絕對不要讓用戶一直幫你抓錯！每個修復都要自己先測試過！**

## 🧪 測試檔案組織原則 (Test Organization Rules)

### ⚠️ 重要：測試檔案必須放在正確位置！

**絕對不要亂放測試檔案！** 每個測試都有固定的位置規則：

### 📁 測試目錄結構
```
duotopia/
├── backend/tests/           # ✅ 正確：所有 Python 測試
│   ├── unit/               # 單元測試
│   │   └── test_*.py
│   ├── integration/        # 整合測試
│   │   ├── api/           # API 整合測試
│   │   │   └── test_*.py
│   │   └── auth/          # 認證整合測試
│   │       └── test_*.py
│   └── e2e/               # E2E 測試
│       └── test_*.py
├── frontend/tests/          # ✅ 正確：前端測試（如果需要）
└── tests/                   # ❌ 錯誤：不要用這個資料夾！
```

### 🎯 測試分類原則

#### 1. **單元測試** (`backend/tests/unit/`)
- 測試單一函數或類別
- 不依賴外部資源（資料庫、API）
- 檔名：`test_模組名稱.py`
- 例：`test_schemas.py`, `test_utils.py`

#### 2. **整合測試** (`backend/tests/integration/`)
- **API 測試** (`api/`): 測試 API 端點功能
  - `test_student_classroom_assignment.py` ✅
  - `test_student_deletion_soft_delete.py` ✅
  - `test_classroom_deletion.py` ✅
- **認證測試** (`auth/`): 測試登入、權限功能
  - `test_auth_comprehensive.py` ✅
  - `test_student_login.py` ✅

#### 3. **E2E 測試** (`backend/tests/e2e/`)
- 測試完整用戶流程
- 從登入到完成任務的完整測試
- 例：`test_assignment_flow.py`

### 🚨 禁止事項
1. **絕對不要放在根目錄 `tests/`** - 這會造成混亂！
2. **不要放在 `backend/scripts/`** - 腳本不是測試！
3. **不要用奇怪檔名** - 如 `test_phase2_api.py`
4. **不要混合不同測試類型** - 單元測試不要呼叫 API

### 📝 測試檔名規範
- ✅ **正確**: `test_student_classroom_assignment.py`
- ✅ **正確**: `test_auth_comprehensive.py`
- ❌ **錯誤**: `test_phase2_api.py`（語意不清）
- ❌ **錯誤**: `student_test.py`（不符合 pytest 慣例）

### 🔧 測試執行指令
```bash
# 執行所有測試
cd backend && python -m pytest tests/

# 執行特定類型測試
cd backend && python -m pytest tests/unit/           # 單元測試
cd backend && python -m pytest tests/integration/    # 整合測試
cd backend && python -m pytest tests/e2e/           # E2E 測試

# 執行特定測試檔案
cd backend && python -m pytest tests/integration/api/test_student_classroom_assignment.py
```

### 📋 檢查清單
創建新測試前必須確認：
- [ ] 檔案放在正確目錄
- [ ] 檔名符合 `test_*.py` 格式
- [ ] 檔名清楚描述測試內容
- [ ] 測試類型分類正確（unit/integration/e2e）

**記住：亂放測試檔案 = 技術債務 = 維護噩夢！**

## 🚨 部署後強制測試規則

### 部署完成 ≠ 工作完成
**部署只是第一步，測試通過才算完成！**

### 每次 git push 後必須：
1. **立即監控部署進度**
   ```bash
   # 查看最新部署
   gh run list --workflow=deploy-staging.yml --limit=1
   
   # 持續監控直到完成
   gh run watch <RUN_ID>
   ```

2. **部署完成後立即測試**
   ```bash
   # 健康檢查
   curl https://your-service-url/health
   
   # API 測試
   curl https://your-service-url/api/auth/validate
   
   # 功能測試（例如個人教師登入）
   python test_individual_api.py
   ```

3. **錯誤日誌檢查**
   ```bash
   gcloud run logs read duotopia-backend --limit=50 | grep -i error
   ```

4. **測試失敗時立即修復**
   - 不要等用戶發現問題
   - 立即查看錯誤日誌
   - 修復後重新部署並測試

**⚠️ 絕對不要推完代碼就不管！每次部署都要監控到成功並測試通過！**

## 🔥 部署錯誤反思與預防

### 常見部署錯誤模式
1. **硬編碼 URL 錯誤**
   - ❌ 錯誤：`fetch('http://localhost:8000/api/...')`
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

## 專案資訊

### Duotopia 概述
Duotopia 是一個以 AI 驅動的多元智能英語學習平台，專為國小到國中學生（6-15歲）設計。透過語音辨識、即時回饋和遊戲化學習，幫助學生提升英語口說能力。

### 技術架構
- **前端**: React 18 + Vite + TypeScript + Tailwind CSS + Radix UI
- **後端**: Python + FastAPI + SQLAlchemy
- **資料庫**: PostgreSQL on Google Cloud SQL
- **儲存**: Google Cloud Storage
- **AI 服務**: OpenAI API for speech analysis
- **部署**: Google Cloud Run + Terraform
- **CI/CD**: GitHub Actions

### 專案結構
```
duotopia/
├── frontend/          # Vite + React + TypeScript
├── backend/           # Python + FastAPI
├── shared/           # 共用類型定義
├── terraform/        # 基礎設施即代碼
├── legacy/           # 原始程式碼（Base44 版本）
├── .github/          # CI/CD workflows
├── docker-compose.yml # 本地開發環境
└── Makefile          # 快捷指令
```

### 核心功能模組

#### 認證系統
- Google OAuth 2.0 (教師/機構管理者)
- 自訂認證 (學生使用 email + 生日)
- JWT token 管理

#### 教師功能
- 班級管理
- 學生管理（批量匯入）
- 課程建立與管理
- 作業派發與批改
- 統計分析

#### 學生功能
- 多步驟登入流程
- 作業列表與管理
- 六種活動類型練習
- 即時 AI 回饋
- 學習進度追蹤

#### 活動類型
1. **朗讀評測** (reading_assessment)
2. **口說練習** (speaking_practice)
3. **情境對話** (speaking_scenario)
4. **聽力填空** (listening_cloze)
5. **造句練習** (sentence_making)
6. **口說測驗** (speaking_quiz)

### 資料模型

#### 使用者系統
- User (教師/管理者)
- Student (學生)
- School (學校)
- Classroom (班級) - ⚠️ 使用 Classroom 而非 Class（避免與 Python 保留字衝突）

#### 課程系統
- Program (課程計畫)
- Lesson (課程單元)
- Content (課程內容)
- ClassroomProgramMapping (班級與課程關聯)

#### 作業系統
- StudentAssignment (學生作業)
- ActivityResult (活動結果)

## 🔧 資料庫 Migration (Alembic)

### 重要原則
**絕對不要手動修改資料庫！所有 schema 變更都必須透過 Alembic migration**

### Alembic 標準工作流程

#### 1. 修改 Model 後生成 Migration
```bash
# 修改 models.py 後
cd backend

# 自動生成 migration
alembic revision --autogenerate -m "add_field_to_model"

# ⚠️ 重要：檢查生成的檔案
# 檢查 alembic/versions/xxx_add_field_to_model.py
# Alembic autogenerate 不是完美的，必須手動檢查
```

#### 2. 執行 Migration
```bash
# 升級到最新版本
alembic upgrade head

# 查看當前版本
alembic current

# 查看歷史
alembic history

# 降級（緊急回滾用）
alembic downgrade -1
```

#### 3. CI/CD 自動執行
- GitHub Actions 在部署前自動執行 `alembic upgrade head`
- 確保 DATABASE_URL 環境變數設定正確
- Migration 失敗會阻止部署

### 常見情境

#### 新增欄位
```python
# models.py
class Content(Base):
    # ... existing fields ...
    is_public = Column(Boolean, default=False)  # 新增欄位

# 然後執行
alembic revision --autogenerate -m "add_is_public_to_content"
alembic upgrade head
```

#### 本地開發同步
```bash
# 拉取最新程式碼後
git pull
cd backend
alembic upgrade head  # 同步資料庫到最新 schema
```

#### 檢查是否需要 Migration
```bash
# 使用 --sql 參數預覽會執行的 SQL
alembic upgrade head --sql

# 如果輸出為空，表示已經是最新
```

### ⚠️ 注意事項
1. **永遠先在本地測試 migration**
2. **生產環境 migration 前必須備份**
3. **autogenerate 限制**：
   - 不會偵測表名或欄位名變更
   - 不會偵測匿名約束
   - 某些索引變更可能遺漏
4. **團隊協作**：
   - Migration 檔案必須 commit 到 git
   - 多人同時建立 migration 可能衝突，需要手動解決

### 開發指令

#### 本地開發
```bash
# 安裝依賴
npm install
cd backend && pip install -r requirements.txt

# 啟動資料庫
docker-compose up -d

# 執行開發伺服器（兩個終端）
# Terminal 1 - 後端
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 - 前端
cd frontend && npm run dev
```

#### 部署
```bash
# 部署到 GCP
./scripts/deploy.sh

# Terraform 管理
cd terraform
terraform init
terraform plan
terraform apply
```

### 環境變數配置

#### 前端 (frontend/.env)
```
VITE_API_URL=http://localhost:8000
```

#### 後端 (backend/.env)
```
DATABASE_URL=postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia
JWT_SECRET=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OPENAI_API_KEY=your-openai-api-key
GCP_PROJECT_ID=duotopia-469413
```

### 測試策略

#### 單元測試
- 前端: Jest + React Testing Library
- 後端: pytest

#### E2E 測試
- Playwright for browser automation
- 測試關鍵用戶流程

#### 測試指令
```bash
# 前端測試
npm run typecheck   # 型別檢查
npm run lint        # 程式碼品質
npm test            # 單元測試（如果有）

# 後端測試
cd backend
python -m pytest    # 單元測試（如果有）
```

### 安全最佳實踐
- 所有密碼存在 Secret Manager
- Service Account 最小權限原則
- HTTPS everywhere
- 輸入驗證與消毒
- SQL injection 防護

### 監控與日誌
- Cloud Logging for application logs
- Cloud Monitoring for metrics
- Error tracking with structured logging
- Performance monitoring

### 已知問題與注意事項
1. **學生登入**: 使用 email + 生日(YYYYMMDD) 格式作為密碼
2. **多語言支援**: 所有標題和描述使用 `Record<string, string>` 格式
3. **Cloud SQL 連線**: 確保 Cloud Run 與 Cloud SQL 在同一區域 (asia-east1)
4. **Base44 遷移**: 完全不要使用 legacy/ 資料夾中的舊代碼
5. **API 路由**: 前端使用 /api 前綴，Vite 會代理到後端的 8000 port
6. **Python 虛擬環境**: 後端開發時記得啟動 venv

### 聯絡資訊
- Project ID: duotopia-469413
- Region: asia-east1
- Support: 透過 GitHub Issues 回報問題

## 💰 成本控制與優化措施 (2025-08-27 更新)

### 🔴 重大教訓：Cloud SQL Tier 錯誤導致巨額帳單
**事件**: 2025-08-21 創建了 **db-g1-small** 實例（應為 db-f1-micro）
- 錯誤實例: duotopia-db-production (db-g1-small)
- 運行時間: 112 小時
- 產生費用: **$233.24 USD**（單日 $67）
- 正確配置: db-f1-micro 只需 ~$11/月

### ⚠️ Cloud SQL 創建紅線規則
1. **絕對禁止手動創建 Cloud SQL**
   ```bash
   # ❌ 錯誤 - 絕對不要這樣做
   gcloud sql instances create duotopia-xxx --tier=db-g1-small
   
   # ✅ 正確 - 永遠使用 Makefile
   make db-create  # 已設定 db-f1-micro
   ```

2. **Tier 必須是 db-f1-micro**
   - db-f1-micro: ~$11/月
   - db-g1-small: ~$50/月（5倍價格！）
   - 任何其他 tier 都太貴

3. **Edition 必須指定 ENTERPRISE**
   ```bash
   --edition=ENTERPRISE  # 必須！不然 db-f1-micro 不能用
   ```

### 問題診斷
初始問題：開發階段每月成本高達 $300+ USD（~$10,000 TWD）
- Cloud SQL: $272 USD (78%) - 主要問題（含錯誤的 Small 實例）
- Cloud Run: $73 USD (21%)
- Artifact Registry: $1.10 USD (<1%)

### 已實施的成本優化
| 優化項目 | 執行指令 | 每月節省 |
|---------|---------|----------|
| 刪除錯誤 Small 實例 | `gcloud sql instances delete duotopia-db-production` | $200+ USD |
| 停止 Production DB | `gcloud sql instances patch duotopia-db-production --activation-policy=NEVER` | $50 USD |
| 停止 Staging DB | `gcloud sql instances patch duotopia-db-staging --activation-policy=NEVER` | $10 USD |
| 降低 Cloud Run 實例 | 後端/前端 max-instances 降至 2，min-instances 設為 0 | $20 USD |
| **總節省** | | **$280 USD/月** |

### 開發階段最佳實踐

#### 1. 資料庫管理（嚴格遵守）
```bash
# 創建資料庫 - 只用 Makefile！
make db-create  # 自動使用正確的 db-f1-micro 配置

# 開發前啟動
make db-start

# 開發完立即停止（省錢）
make db-stop

# 刪除不需要的實例
make db-delete

# 使用本地 Docker（完全免費）
docker-compose up -d
```

#### 2. 成本檢查 SOP
```bash
# 每天檢查一次
gcloud sql instances list --format="table(name,tier,state)"

# 看到任何非 db-f1-micro 立即刪除！
# 看到任何 RUNNABLE 狀態但沒在用的立即停止！
```

#### 3. Cloud Run 設定
- min-instances: 0（無流量時不收費）
- max-instances: 2（開發階段足夠）
- 容器大小目標: <500MB（目前 11GB 太大）

### 成本監控建議
1. 設定 GCP 預算警報：$30 USD/月
2. 每日檢查：`gcloud sql instances list`
3. 發現異常立即處理：任何 > $10/天 都是異常

### 費用預估（正確配置下）
- 開發階段（資料庫停用）：~$20 USD/月
- 測試階段（資料庫啟用）：~$30 USD/月
- 生產環境：根據實際流量計費