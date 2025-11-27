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
cd backend && uvicorn main:app --reload --port 8080

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

- **開發**: http://localhost:5173 (前端) + http://localhost:8080 (後端)
- **Staging**: 透過 GitHub Actions 自動部署到 Google Cloud Run

## 核心功能

### 多租戶機構階層系統 (Multi-Tenant Organization Hierarchy)

Duotopia 支援完整的機構階層架構，適合補習班、學校體系、教育機構使用：

```
Organization (機構)
  ├── School (分校)
  │   ├── Classroom (班級)
  │   │   └── Students (學生)
  │   └── Teachers (教師)
  └── Teachers (機構成員)
```

**角色與權限：**
- **org_owner (機構擁有人)**: 完整控制權 + 訂閱管理 (每個機構限 1 人)
- **org_admin (機構管理員)**: 完整控制權 (除訂閱外)
- **school_admin (分校校長)**: 分校層級管理
- **teacher (教師)**: 教學功能

**功能特點：**
- ✅ 基於 Casbin 的 RBAC 權限控制
- ✅ Domain 隔離 (org-{id}, school-{id})
- ✅ 多角色支援 (教師可同時擔任多個角色)
- ✅ 完整的 CRUD API
- ✅ 前端管理界面

詳細文檔: [API_ORGANIZATION_HIERARCHY.md](./docs/API_ORGANIZATION_HIERARCHY.md)

---

## API 文檔

- 開發環境: http://localhost:8080/docs
- Staging: [部署後自動更新]
- [Organization Hierarchy API](./docs/API_ORGANIZATION_HIERARCHY.md)
- [RBAC Permissions](./backend/docs/RBAC_PERMISSIONS.md)
