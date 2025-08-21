# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 最高指導原則：修完要自己去測試過！

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

## 🚨 部署後強制測試規則

### 部署完成 ≠ 工作完成
**部署只是第一步，測試通過才算完成！**

### 每次部署後必須執行：
1. **健康檢查**
   ```bash
   curl https://your-service-url/health
   ```

2. **API 端點測試**
   ```bash
   # 健康檢查
   curl https://your-service-url/health
   
   # API 測試
   curl https://your-service-url/api/auth/validate
   curl -X POST https://your-service-url/api/auth/student/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "birth_date": "20100101"}'
   ```

3. **錯誤日誌檢查**
   ```bash
   gcloud run logs read duotopia-backend --limit=50 | grep -i error
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
- Class (班級)

#### 課程系統
- Course (課程)
- Lesson (課文/活動)
- ClassCourseMapping (班級課程關聯)

#### 作業系統
- StudentAssignment (學生作業)
- ActivityResult (活動結果)

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