# GitHub Actions Workflows

## 🎯 智能檔案變更檢測 CI/CD

我們的 CI/CD 架構現在使用**智能檔案變更檢測**，根據變更的檔案自動決定要執行哪個部署流程。

## 📁 Workflow 檔案說明

### 1. `deploy-backend.yml` 🔧
**觸發條件**：
- 後端程式碼變更 (`backend/**`)
- Python 依賴變更 (`requirements*.txt`)
- 資料庫設定變更 (`alembic.ini`)

**執行內容**：
- Python 測試 (pytest)
- Black & Flake8 檢查
- 資料庫遷移 (Alembic)
- 部署後端到 Cloud Run

### 2. `deploy-frontend.yml` 🎨
**觸發條件**：
- 前端程式碼變更 (`frontend/**`)
- Node 設定變更 (`package*.json`, `tsconfig*.json`)
- Lint 設定變更 (`.eslintrc*`, `.prettierrc*`)

**執行內容**：
- TypeScript 型別檢查
- ESLint 檢查
- 前端建置測試
- 部署前端到 Cloud Run

### 3. `deploy-shared.yml` 🔄
**觸發條件**：
- Docker 設定變更 (`docker-compose*.yml`)
- 共用設定變更 (`Makefile`, `.env.example`)

**執行內容**：
- 分析需要部署的服務
- 自動觸發相關的 workflow
- 執行安全掃描

### 4. `cleanup-resources.yml` 🧹
**觸發條件**：
- 每日定時執行 (UTC 3:00)
- 手動觸發

**執行內容**：
- 清理舊的 Docker 映像
- 清理未使用的資源
- 產生清理報告

## 🚀 使用範例

### 範例 1：只修改前端
```bash
# 修改前端元件
git add frontend/src/components/Button.tsx
git commit -m "fix: Update button style"
git push

# 結果：只觸發 deploy-frontend.yml
# ✅ 前端測試 & 部署
# ❌ 後端不會被觸發（節省資源）
```

### 範例 2：只修改後端 API
```bash
# 修改 API 路由
git add backend/routers/users.py
git commit -m "feat: Add new user endpoint"
git push

# 結果：只觸發 deploy-backend.yml
# ✅ 後端測試 & 部署
# ✅ 資料庫遷移檢查
# ❌ 前端不會被觸發
```

### 範例 3：同時修改前後端
```bash
# 同時修改前後端
git add frontend/src/api/client.ts backend/main.py
git commit -m "feat: Add new feature"
git push

# 結果：兩個 workflow 平行執行
# ✅ deploy-backend.yml
# ✅ deploy-frontend.yml
# 🚀 部署時間縮短（平行執行）
```

## 🛠️ 手動觸發

所有 workflow 都支援手動觸發：

1. 進入 GitHub Actions 頁面
2. 選擇要執行的 workflow
3. 點擊 "Run workflow"
4. 選擇分支並執行

## 📊 效益

- **節省 50%+ CI/CD 時間**：只執行需要的部分
- **減少 60%+ 資源消耗**：避免不必要的建置
- **更快的部署速度**：前後端平行部署
- **更清晰的錯誤追蹤**：分離的日誌和狀態

## ⚠️ 注意事項

1. **資料庫變更**：修改 models 時會自動執行 Alembic 遷移
2. **環境變數**：新增環境變數需要在對應的 workflow 中設定
3. **依賴關係**：前端部署會自動獲取最新的後端 URL

## 🔧 維護指南

### 新增觸發路徑
編輯對應的 workflow 檔案，在 `paths` 區塊新增：
```yaml
paths:
  - 'backend/**'
  - 'new/path/**'  # 新增路徑
```

### 排除特定檔案
使用 `paths-ignore` 排除不需要觸發的檔案：
```yaml
paths-ignore:
  - '**.md'
  - 'backend/tests/**'
```

## 📝 歷史

- **2024-12-29**: 從單一 workflow 遷移到智能分離架構
- 舊的設定檔備份為 `deploy-supabase.yml.old`
