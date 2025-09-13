# Duotopia - 英語學習平台

一個以 AI 驅動的多元智能英語學習平台，專為學生和教師設計。

## 快速開始

### 1. 安裝依賴
```bash
# 前端
cd frontend && npm install

# 後端
cd backend && pip install -r requirements.txt
```

### 2. 啟動開發環境
```bash
# Terminal 1 - 後端
cd backend && uvicorn main:app --reload --port 8000

# Terminal 2 - 前端
cd frontend && npm run dev
```

### 3. 測試
```bash
# 後端測試（平行執行）
cd backend && pytest -n auto

# 前端檢查
cd frontend && npm run lint && npm run typecheck
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
└── docker-compose.yml # 本地開發環境
```

## 技術架構

- **前端**: React 18 + Vite + TypeScript + Tailwind CSS
- **後端**: Python + FastAPI
- **部署**: Google Cloud Run
- **CI/CD**: GitHub Actions

## 常用指令

### 前端
```bash
npm run dev            # 開發伺服器
npm run build          # 建置生產版本
npm run lint           # ESLint 檢查
npm run typecheck      # TypeScript 型別檢查
```

### 後端
```bash
uvicorn main:app --reload    # 開發伺服器
pytest                        # 執行所有測試
pytest -n auto               # 平行執行測試
python seed_data.py          # 填充測試資料
```

## 環境

- **開發**: http://localhost:5173 (前端) + http://localhost:8000 (後端)
- **Staging**: 透過 GitHub Actions 自動部署到 Google Cloud Run

## API 文檔

- 開發環境: http://localhost:8000/docs
- Staging: [部署後自動更新]
