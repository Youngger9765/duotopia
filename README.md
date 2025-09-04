# Duotopia - 英語學習平台

一個以 AI 驅動的多元智能英語學習平台，專為學生和教師設計。

## 快速開始

### 1. 安裝依賴
```bash
make dev-setup
```

### 2. 啟動開發環境
```bash
# Terminal 1 - 後端
make dev-backend

# Terminal 2 - 前端
make dev-frontend
```

### 3. 測試
```bash
make test
```

### 4. 部署到 staging
```bash
git push origin staging
```

## 專案結構

```
duotopia/
├── frontend/          # React + Vite + TypeScript
├── backend/           # Python + FastAPI
├── .github/           # GitHub Actions CI/CD
├── docker-compose.yml # 本地開發環境
└── Makefile          # 開發指令
```

## 技術架構

- **前端**: React 18 + Vite + TypeScript + Tailwind CSS
- **後端**: Python + FastAPI
- **部署**: Google Cloud Run
- **CI/CD**: GitHub Actions

## 可用指令

```bash
make help              # 查看所有可用指令
make dev-setup         # 設定開發環境
make test              # 執行測試
make build             # 建置 Docker images
make test-local        # 本地 Docker 測試
make deploy-staging    # 部署到 staging
make status            # 查看服務狀態
make logs-backend      # 查看後端日誌
make logs-frontend     # 查看前端日誌
```

## 環境

- **開發**: http://localhost:5173 (前端) + http://localhost:8000 (後端)
- **Staging**: 透過 GitHub Actions 自動部署到 Google Cloud Run

## API 文檔

- 開發環境: http://localhost:8000/docs
- Staging: [部署後自動更新]
