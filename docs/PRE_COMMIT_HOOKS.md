# Pre-commit Hooks 程式碼品質保證

## 概述
Duotopia 使用 pre-commit hooks 在每次 commit 前自動執行程式碼品質檢查，確保所有程式碼符合專案標準。

## 為什麼 Flake8 之前沒有阻止提交？

Pre-commit hooks 需要正確安裝才能生效。之前的問題：
1. 開發者可能沒有執行 `pre-commit install`
2. 可以使用 `--no-verify` 跳過檢查
3. Flake8 錯誤累積到 40+ 個才被發現

## 現在的解決方案

### 1. 強制安裝 Hooks
```bash
# 開發環境設定時自動安裝
make dev-setup

# 或單獨安裝
make setup-hooks
```

### 2. 禁止跳過檢查
**絕對禁止使用 `--no-verify`！** 這在 CLAUDE.md 中明確規定。

### 3. 自動執行的檢查

每次 commit 前會自動執行：

| 檢查項目 | 工具 | 說明 |
|---------|------|------|
| Python 格式化 | Black | 自動格式化 Python 程式碼 |
| Python Linting | Flake8 | 檢查程式碼品質（120 字元限制） |
| TypeScript Linting | ESLint | 檢查 TypeScript 程式碼品質 |
| TypeScript 編譯 | tsc | 確保沒有型別錯誤 |
| 資料庫 Migration | Alembic | 檢查 Model 變更是否有對應 Migration |
| 硬編碼 URL | grep | 防止 localhost URL 進入程式碼 |
| 安全檢查 | 自訂腳本 | 檢查密碼、API keys、JWT secrets |
| 大檔案檢查 | pre-commit | 防止超過 1MB 的檔案 |
| JSON/YAML 格式 | pre-commit | 確保設定檔格式正確 |

## 使用指南

### 手動執行所有檢查
```bash
pre-commit run --all-files
```

### 只檢查特定檔案
```bash
pre-commit run --files backend/main.py
```

### 只執行特定檢查
```bash
pre-commit run flake8 --all-files
pre-commit run black --all-files
```

## 常見問題修復

### Flake8 錯誤
```bash
# 自動修復未使用的 import
pip install autoflake
autoflake --in-place --remove-unused-variables --remove-all-unused-imports backend/**/*.py

# 手動修復其他問題
# F841: 移除未使用的變數
# E501: 縮短過長的行（>120 字元）
# E302: 函數間需要兩個空行
```

### Black 格式化
```bash
# 自動格式化所有 Python 檔案
black backend/
```

### ESLint 錯誤
```bash
# 自動修復
cd frontend && npm run lint:fix
```

### TypeScript 錯誤
```bash
# 檢查錯誤
cd frontend && npm run typecheck
```

## 設定檔

- `.pre-commit-config.yaml`: Pre-commit hooks 設定
- `.flake8`: Flake8 規則設定（如果需要）
- `pyproject.toml`: Black 設定
- `frontend/.eslintrc`: ESLint 規則

## 重要原則

1. **Never Skip**: 絕對不要使用 `--no-verify`
2. **Fix Immediately**: 發現錯誤立即修復
3. **Clean Commits**: 每個 commit 都應該通過所有檢查
4. **Team Discipline**: 整個團隊都要遵守

## 成本效益

- 預防 Bug 進入主分支
- 減少 Code Review 時間
- 維持程式碼品質一致性
- 避免技術債累積

---

記住：**好的程式碼品質從每個 commit 開始！**
