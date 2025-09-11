# Duotopia Pre-Check 機制完整分析

## 概述
Duotopia 專案使用多層次的檢查機制來確保程式碼品質，主要以 `.pre-commit-config.yaml` 為核心，但還有其他補充機制。

## 1. 主要檢查機制：Pre-commit Hooks

### 核心配置檔案
- **`.pre-commit-config.yaml`** - 所有 pre-commit 檢查的主要配置
- **執行時機**: 每次 `git commit` 前自動執行
- **安裝方式**: `pre-commit install` 或 `make dev-setup`

### 檢查項目（按執行順序）

#### Python 檢查
1. **Black** (格式化)
   - 自動格式化 Python 程式碼
   - 版本: 23.12.1
   - 範圍: `backend/**/*.py`

2. **Flake8** (Linting)
   - 程式碼品質檢查
   - 版本: 7.0.0
   - 設定: `--max-line-length=120 --ignore=E203,W503`
   - 範圍: `backend/**/*.py`

#### TypeScript/JavaScript 檢查
3. **ESLint**
   - TypeScript/React 程式碼品質
   - 執行: `cd frontend && npx eslint --ext ts,tsx src --max-warnings 0`
   - 範圍: `frontend/src/**/*.(ts|tsx)`

4. **TypeScript Check**
   - 型別檢查
   - 執行: `cd frontend && npx tsc --noEmit`
   - 範圍: `frontend/src/**/*.(ts|tsx)`

#### 資料庫檢查
5. **Alembic Check**
   - 檢查 models.py 變更是否有對應的 migration
   - 執行條件: models.py 有變更時
   - 失敗時提示執行 migration 指令

6. **Migration Format Check**
   - 檢查 migration 檔案格式
   - 範圍: `backend/alembic/versions/*.py`

#### 安全檢查
7. **Prevent Hardcoded URLs**
   - 防止 localhost URL 進入程式碼
   - 檢查: `grep -r "localhost:[0-9]" frontend/src/`

8. **Check Credentials**
   - 檢查硬編碼的密碼
   - 腳本: `.github/hooks/security/check-credentials.sh`

9. **Check Database URLs**
   - 檢查暴露的資料庫連線字串
   - 腳本: `.github/hooks/security/check-database-urls.sh`

10. **Check API Keys**
    - 檢查暴露的 API 金鑰
    - 腳本: `.github/hooks/security/check-api-keys.sh`

11. **Check JWT Secrets**
    - 檢查暴露的 JWT 密鑰
    - 腳本: `.github/hooks/security/check-jwt-secrets.sh`

12. **Check Env Files**
    - 防止 .env 檔案被提交
    - 腳本: `.github/hooks/security/check-env-files.sh`

13. **Security Audit**
    - 綜合安全審計
    - 腳本: `.github/hooks/security/security-audit.sh`

#### 通用檢查
14. **Check Large Files**
    - 防止大檔案（>1MB）
    - 來源: pre-commit-hooks v4.5.0

15. **Check JSON/YAML**
    - 驗證 JSON 和 YAML 格式
    - 排除: `tsconfig.*.json`

16. **Fix End of Files**
    - 確保檔案結尾有換行

17. **Trim Trailing Whitespace**
    - 移除行尾空格

18. **Check Merge Conflicts**
    - 檢查未解決的合併衝突標記

## 2. 次要檢查機制：Pre-push Hook

### 配置檔案
- **`.git/hooks/pre-push`** - 自訂 pre-push 腳本
- **執行時機**: `git push` 前

### 檢查項目
1. **Models.py 變更警告**
   - 提醒是否需要執行 Alembic migration
   - 需要手動確認

2. **防止提交 .db 檔案**
   - 阻止資料庫檔案被推送

3. **測試檔案位置警告**
   - 提醒測試應放在 `backend/tests/` 而非 `backend/scripts/`

## 3. CI/CD 檢查：GitHub Actions

### 配置檔案
- **`.github/workflows/deploy-staging-supabase.yml`**
- **執行時機**: Push 到 staging 分支或 PR

### 檢查項目
1. **Frontend 檢查**
   - ~~TypeScript 編譯~~ (目前跳過 - CI 路徑解析問題)
   - ESLint (`npm run lint:ci`)
   - Build 測試 (`npm run build`)

2. **Backend 檢查**
   - Import 測試（確保 main.py 可以載入）
   - ❌ 沒有執行 Flake8
   - ❌ 沒有執行 Black
   - ❌ 沒有執行 pytest

3. **安全掃描**
   - Trufflehog 密鑰掃描
   - 設為 continue-on-error（不阻擋部署）

## 4. 本地開發輔助工具

### Makefile 指令
- `make dev-setup` - 完整開發環境設定（含 pre-commit）
- `make setup-hooks` - 單獨設定 pre-commit hooks

### NPM Scripts (package.json)
- `npm run test:api:all` - 執行所有 Python 測試
- 沒有 `npm run lint:fix` 或 `npm run format` 指令

### Git 配置
- `git config hooks.failFast true` - 第一個錯誤就停止

## 5. 檢查機制強度分析

### ✅ 強項
1. **Pre-commit 層面很完整**
   - Python 和 TypeScript 都有覆蓋
   - 安全檢查齊全
   - 格式化自動執行

2. **多層防護**
   - Commit 時檢查（pre-commit）
   - Push 時檢查（pre-push）
   - CI/CD 時檢查（GitHub Actions）

### ⚠️ 弱點
1. **CI/CD 檢查不足**
   - 沒有執行 Python linting (Flake8/Black)
   - 沒有執行 pytest
   - TypeScript 檢查被跳過

2. **可以被繞過**
   - 使用 `--no-verify` 可跳過檢查
   - CI/CD 的安全掃描是 continue-on-error

3. **缺少自動修復工具**
   - 沒有 `npm run format` 指令
   - 沒有 `npm run lint:fix` 指令

## 6. 執行優先順序

```
1. Pre-commit (每次 commit)
   └── .pre-commit-config.yaml 定義的所有檢查

2. Pre-push (每次 push)
   └── .git/hooks/pre-push 的額外檢查

3. GitHub Actions (push 到 staging)
   └── 部分前端檢查 + 安全掃描
```

## 7. 建議改進

### 高優先級
1. **加強 CI/CD 檢查**
   ```yaml
   - name: Run Flake8
     run: cd backend && flake8 .

   - name: Run Black Check
     run: cd backend && black --check .

   - name: Run pytest
     run: cd backend && pytest
   ```

2. **加入自動修復指令**
   ```json
   "scripts": {
     "format": "cd backend && black . && cd ../frontend && prettier --write .",
     "lint:fix": "cd frontend && eslint . --fix"
   }
   ```

### 中優先級
3. **統一檢查標準**
   - CI/CD 應該執行與 pre-commit 相同的檢查
   - 避免本地通過但 CI 失敗的情況

4. **加入 pytest 到 pre-commit**
   - 至少執行快速的單元測試

### 低優先級
5. **效能優化**
   - 使用 `--hook-stage` 分階段執行
   - 大型檢查移到 pre-push

## 總結

**主要依賴**: `.pre-commit-config.yaml` 是核心
**覆蓋率**: Commit 層面 90%，CI/CD 層面 40%
**建議**: 加強 CI/CD 檢查，確保與本地檢查一致

---
*最後更新: 2025-09-11*
