# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 最高指導原則：修完要自己去測試過！

## 🔐 資安鐵則：絕對禁止 Hardcode Secrets！

**絕對不要在任何會被 commit 的檔案中硬編碼 secrets！**

### Secret 管理規則：
- ❌ 不要在 `.sh`, `.py`, `.ts`, `.yml` 中硬編碼 secrets
- ✅ 本機開發：使用 `.env` 檔案（gitignore）
- ✅ CI/CD：使用 GitHub Secrets (`gh secret set`)
- ✅ 生產環境：使用 Cloud Run 環境變數或 Secret Manager
- ✅ 程式碼：從環境變數讀取 (`os.getenv()`, `import.meta.env`)
- ⚠️ 洩漏後：立即重新生成並清除 git 歷史

---

## 🔴 絕對禁止使用 --no-verify！
**永遠不要偷懶！** 所有 pre-commit hooks 的錯誤都必須修復，不能跳過：
- ❌ **絕對禁止** `git commit --no-verify`
- ✅ **必須修復** 所有 flake8、ESLint、black 錯誤
- ✅ **必須通過** 所有 pre-commit 檢查才能 commit

## ⚠️ 必須遵守的操作順序 (STOP! READ FIRST!)

### 在執行任何重要操作前，必須按順序檢查：
1. **先查 README** - 了解專案標準流程
2. **先查 CLAUDE.md** - 了解專案特定規則
3. **先查 package.json/requirements.txt** - 了解已有的腳本命令
4. **絕對不要自作主張創建資源** - 永遠使用專案既有的配置

### 🔴 紅線規則 (絕對禁止)：
- ❌ **不要手動 gcloud 命令創建資源** - 必須使用專案配置
- ❌ **不要猜測版本號** - POSTGRES_15 vs POSTGRES_17 等必須查證
- ❌ **不要忽略專案既有工具** - npm scripts, pytest 優先
- ❌ **不要在未讀取配置前就執行命令** - 先讀後做

### ✅ 正確操作範例：
```bash
# 錯誤：直接創建 Cloud SQL
gcloud sql instances create duotopia-db-staging --database-version=POSTGRES_15

# 正確：使用專案配置
gcloud sql instances create duotopia-staging-0827 \
  --database-version=POSTGRES_17 \
  --tier=db-f1-micro \
  --region=asia-east1
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

### 🔴 Git Commit/Push 流程（絕對遵守）

**標準工作流程：**
1. **修改代碼**
2. **自己測試** - 執行上述所有測試步驟
3. **報告測試結果** - 告訴用戶測試通過與否
4. **等待命令** - ⚠️ **絕對不要主動 commit 或 push**

**禁止事項：**
- ❌ **絕對禁止** 自己決定何時 commit
- ❌ **絕對禁止** 自己決定何時 push
- ❌ **絕對禁止** 測試不完整就想 commit
- ❌ **絕對禁止** 沒有用戶明確命令就 commit/push

**正確做法：**
```
✅ 我：修改完成，已測試通過（附測試結果）
✅ 用戶：commit push
✅ 我：執行 git commit && git push
```

**錯誤做法：**
```
❌ 我：修改完成，現在 commit...（自作主張）
❌ 我：測試通過，推送到 staging...（沒等命令）
```

### 🔴 絕對禁止草率判斷「修復完成」！

**血淋淋的教訓（2025-09-07）：**
```
錯誤行為：
1. 看到 API 返回 200 OK 就以為修好了 ❌
2. 沒有檢查 API 返回的實際資料內容 ❌
3. 沒有在前端瀏覽器實際測試功能 ❌
4. 截圖抓錯（抓到桌面背景）還說功能正常 ❌
5. 急著要 commit push 而沒有驗證 ❌

正確做法：
1. API 返回 200 不代表功能正常 ✅
2. 必須檢查返回的 JSON 資料結構和內容 ✅
3. 必須在瀏覽器中實際操作功能 ✅
4. 截圖必須確認是正確的頁面 ✅
5. 測試通過後才能 commit ✅
```

**判斷修復完成的標準：**
- [ ] API 返回正確的狀態碼
- [ ] API 返回正確的資料結構
- [ ] 前端頁面正常顯示
- [ ] 功能可以正常操作
- [ ] 沒有 console 錯誤
- [ ] 截圖證明功能正常

**記住：用戶說「操你媽的」時，代表你沒有做好測試！**

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

## 🔍 完成工作前的強制檢查清單 (Pre-Completion Checklist)

### ⚠️ 每次回報「完成」前必須執行：

```bash
# 1. 檢查檔案位置
git status --short
# 確認：
# - 所有測試檔案在正確目錄 (unit/integration/e2e)
# - 沒有重複的測試檔案
# - 沒有開發過程中的臨時檔案

# 2. 清理不必要的檔案
# 刪除所有 *_temp.py, *_old.py, *_backup.py, *_test*.py (開發過程檔案)
# 只保留最終版本的測試檔案

# 3. 執行完整測試
npm run test:api:all  # 所有後端測試
npm run build        # 前端建置

# 4. 檢查 code formatting
black --check backend/  # Python
npm run lint           # TypeScript/JavaScript

# 5. 檢查 git diff
git diff --stat        # 確認改動合理
git diff              # 檢視實際變更內容
```

### 📋 回報格式標準

完成工作時必須包含：

```markdown
## ✅ 完成項目
- [具體完成的功能/修復]

## 📊 測試結果
- Unit tests: X/X PASSED
- Integration tests: X/X PASSED
- E2E tests: X/X PASSED

## 📝 修改的檔案
1. `路徑/檔案名` - 做了什麼修改
2. `路徑/檔案名` - 做了什麼修改

## 🗑️ 已刪除的臨時檔案
- `舊檔案名` - 為何刪除

## ⏳ 待用戶確認
- 等待 commit 指示（遵守 "不要主動 commit" 規則）
```

### 🚨 絕對不要：
- ❌ 回報「完成」時還有臨時測試檔案沒清理
- ❌ 回報「完成」時測試檔案位置不對
- ❌ 回報「完成」時沒有執行完整測試
- ❌ 回報「完成」時 git status 一團亂
- ❌ 讓用戶問「檔案位置對嗎？」「臨時檔案刪了嗎？」

**記住：用戶問這些問題 = 你沒做好基本檢查！**

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

### 🔧 業界標準測試執行指令

#### NPM Scripts (推薦使用)
```bash
# API 測試
npm run test:api                 # 所有 API 整合測試
npm run test:api:unit            # 單元測試
npm run test:api:integration     # 整合測試
npm run test:api:e2e             # E2E 測試
npm run test:api:all             # 所有 Python 測試
npm run test:api:coverage        # 測試覆蓋率報告

# 前端測試
npm run test:e2e                 # Playwright E2E 測試
npm run test:e2e:ui              # Playwright UI 模式

# 完整測試
npm run test:all                 # 所有測試（Python + Playwright）
```

#### 直接使用 pytest（進階用法）
```bash
cd backend

# 基本測試執行
pytest                                    # 所有測試（289個）
pytest -v                                # 詳細輸出
pytest tests/unit/                       # 只執行單元測試
pytest tests/integration/api/            # 只執行 API 測試

# 特定測試
pytest tests/integration/api/test_student_classroom_assignment.py -v

# 測試分類執行
pytest -m "unit"                         # 執行標記為 unit 的測試
pytest -m "api and not slow"             # 執行 API 測試但排除慢測試

# 測試覆蓋率
pytest --cov=. --cov-report=html        # 生成 HTML 覆蓋率報告

# 平行執行（需安裝 pytest-xdist）
pytest -n auto                          # 自動偵測 CPU 核心數平行執行
```

#### CI/CD 使用
```bash
# GitHub Actions 使用
pytest --junitxml=test-results.xml
```

### 📋 檢查清單
創建新測試前必須確認：
- [ ] 檔案放在正確目錄
- [ ] 檔名符合 `test_*.py` 格式
- [ ] 檔名清楚描述測試內容
- [ ] 測試類型分類正確（unit/integration/e2e）

**記住：亂放測試檔案 = 技術債務 = 維護噩夢！**

## 🤖 Git Issue PR Flow 自動化 Agent

專案已配置 Git Issue PR Flow 自動化工具，遵循以下標準流程：

```
Feature Branch → Staging (auto-deploy) → Main (PR with issue tracking)
```

### 安裝使用

```bash
# 載入 Git Issue PR Flow Agent（加到 ~/.zshrc 或 ~/.bashrc）
source /Users/young/project/duotopia/.claude/agents/git-issue-pr-flow.sh

# 查看可用命令
git-flow-help

# 查看當前狀態
git-flow-status
```

### 標準工作流程

#### 1. 修復 Issue
```bash
# 創建 feature branch
create-feature-fix 7 student-login-loading

# 修改代碼並測試
npm run build
# ... 測試 ...

# Commit 修改
git add .
git commit -m "fix: 修復學生登入 Step 1 的錯誤訊息閃現和 loading 狀態問題"

# 部署到 staging（自動 merge + push + 更新 issue）
deploy-feature 7
```

#### 2. 準備 Release
```bash
# 累積多個 fixes 後，創建/更新 Release PR
update-release-pr

# 測試 staging 環境
# Frontend: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
# Backend: https://duotopia-staging-backend-316409492201.asia-east1.run.app
```

#### 3. 發布到 Production
```bash
# 標記 PR 為 ready
gh pr ready <PR_NUMBER>

# Merge PR（自動關閉所有 issues）
gh pr merge <PR_NUMBER> --merge
```

### 固定的 Staging URLs

- **Frontend**: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
- **Backend**: https://duotopia-staging-backend-316409492201.asia-east1.run.app

### 可用命令

| 命令 | 說明 |
|------|------|
| `create-feature-fix <issue> <desc>` | 創建修復 issue 的 feature branch |
| `create-feature <desc>` | 創建新功能的 feature branch |
| `deploy-feature <issue>` | 部署到 staging 並更新 issue |
| `deploy-feature-no-issue` | 部署到 staging（不關聯 issue）|
| `update-release-pr` | 創建/更新 staging → main 的 Release PR |
| `patrol-issues` | **🔍 巡邏 GitHub Issues，顯示統計和列表** |
| `git-flow-status` | 查看當前工作流程狀態 |
| `git-flow-help` | 顯示所有可用命令 |

### Claude Code 自動化指南

**⚠️ 重要：當用戶說以下關鍵字時，自動使用 Git Issue PR Flow Agent**

#### 觸發關鍵字
- 「修復 issue」、「fix issue」
- 「部署到 staging」、「deploy to staging」
- 「發 PR」、「create PR」、「準備 release」
- 「merge to staging」
- 「有什麼 issue」、「檢查 issues」、「巡邏 issues」、「patrol issues」
- 「檢查 approval」、「查看批准狀態」、「check approvals」
- 任何提到 GitHub Issue 編號（如「處理 #7」）

#### 自動化流程

**場景 1: 用戶說「修復 issue #7 學生登入問題」**
```bash
# 1. 自動執行 create-feature-fix
create-feature-fix 7 student-login-loading

# 2. 修改代碼並測試
npm run build
npm run typecheck
# ... 實際測試功能 ...

# 3. Commit（⚠️ 必須包含 #issue_number）
git add .
git commit -m "fix: 修復學生登入 Step 1 的錯誤訊息閃現和 loading 狀態問題

Fixes #7"

# 4. 自動執行 deploy-feature
deploy-feature 7
```

**場景 2: 用戶說「部署到 staging」**
```bash
# 檢查當前 branch
current_branch=$(git branch --show-current)

# 如果在 feature branch，執行 deploy-feature
deploy-feature <issue_number>
# 或 deploy-feature-no-issue（如果沒有關聯 issue）
```

**場景 3: 用戶說「準備 release」或「發 PR」**
```bash
# 自動執行 update-release-pr
update-release-pr
```

**場景 4: 用戶說「有什麼 issue」或「檢查 issues」**
```bash
# 自動執行 patrol-issues
patrol-issues

# 顯示摘要：
# - 總共幾個 open issues
# - 幾個 bugs、enhancements
# - 幾個未分配的 issues
# - 列出所有 issues 的標題、標籤、建立時間
```

**場景 5: 用戶說「查看狀態」**
```bash
# 自動執行 git-flow-status
git-flow-status
```

**場景 6: 用戶說「檢查 approval」或「查看批准狀態」**
```bash
# 自動執行 check-approvals
check-approvals

# 顯示：
# - Release PR 資訊
# - 每個 issue 的批准狀態
# - 進度統計（幾個已批准/總共幾個）
# - 下一步建議（是否可以 deploy to production）
```

#### Approval 自動化流程

**當 case owner（如 Kaddy）在 issue 留言「測試通過」或「approved」時**：

1. **GitHub Actions 自動觸發**
   - 檢測關鍵字：「測試通過」、「approved」、「✅」、「LGTM」
   - 驗證留言者是否為 case owner（kaddy-eunice 或 Youngger9765）

2. **自動加上標籤**
   - 加上 `✅ tested-in-staging` label 到該 issue

3. **檢查 Release PR**
   - 找到包含此 issue 的 Release PR
   - 檢查 PR 中所有 issues 是否都有 `✅ tested-in-staging` label

4. **全部批准後自動動作**
   - 標記 PR 為 Ready for review（移除 Draft 狀態）
   - 在 PR 加上評論通知可以 merge

5. **使用 `check-approvals` 手動檢查**
   - 任何時候想知道批准進度，執行 `check-approvals`
   - 顯示清楚的進度統計和下一步建議

#### 重要規則
- ❌ 不要手動創建 feature → staging 的 PR
- ✅ 只為 staging → main 創建 PR
- ✅ PR 會自動追蹤所有相關 issues（`Fixes #N`）
- ✅ Merge PR 時會自動關閉所有 issues
- ✅ **所有 Git 操作都使用 agent 命令，不要手動執行 git 指令**
- ⚠️ **Commit message 必須包含 `#issue_number` 或 `Fixes #N`**，否則 PR 無法自動追蹤 issue

#### 固定的 Staging URLs（不需要查詢）
- **Frontend**: https://duotopia-staging-frontend-316409492201.asia-east1.run.app
- **Backend**: https://duotopia-staging-backend-316409492201.asia-east1.run.app

---

## 📚 相關文件

- **產品需求**: 詳見 [PRD.md](./PRD.md)
- **部署與 CI/CD**: 詳見 [CICD.md](./CICD.md)
- **測試指南**: 詳見 [docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)
- **部署狀態**: 詳見 [docs/DEPLOYMENT_STATUS.md](./docs/DEPLOYMENT_STATUS.md)
- **Git Issue PR Flow Agent**: 詳見 [.claude/agents/git-issue-pr-flow-agent.md](./.claude/agents/git-issue-pr-flow-agent.md)

## 🎯 錄音播放架構重構 TDD (2024-12-27)

### 測試需求規格

#### 1. **GroupedQuestionsTemplate 播放測試**
```typescript
// 測試案例：切換題目時應正確播放對應錄音
describe('GroupedQuestionsTemplate', () => {
  it('應該直接從當前 item 播放錄音', () => {
    // Given: 有 3 個題目，每個都有 recording_url
    const items = [
      { id: 1, text: '題目1', recording_url: 'audio1.webm' },
      { id: 2, text: '題目2', recording_url: 'audio2.webm' },
      { id: 3, text: '題目3', recording_url: 'audio3.webm' }
    ];

    // When: 切換到第 2 題
    currentQuestionIndex = 1;

    // Then: 應該播放 items[1].recording_url
    expect(播放的URL).toBe('audio2.webm');
    // 不應該使用 recordings[1]
    expect(不使用recordings陣列).toBe(true);
  });
});
```

#### 2. **ReadingAssessmentTemplate 播放測試**
```typescript
describe('ReadingAssessmentTemplate', () => {
  it('應該直接從 item 播放錄音', () => {
    // Given: reading_assessment 只有一個 item
    const item = { id: 1, text: '朗讀內容', recording_url: 'reading.webm' };

    // Then: 直接播放 item.recording_url
    expect(audioUrl).toBe('reading.webm');
    // 不需要陣列處理
    expect(不使用recordings陣列).toBe(true);
  });
});
```

#### 3. **重新錄音測試**
```typescript
it('重新錄音應更新對應 item 的 recording_url', () => {
  // When: 第 2 題重新錄音
  重新錄音(題目索引: 1, 新錄音: 'new_audio2.webm');

  // Then: 只更新 items[1].recording_url
  expect(items[1].recording_url).toBe('new_audio2.webm');
  // 其他題目不受影響
  expect(items[0].recording_url).toBe('audio1.webm');
  expect(items[2].recording_url).toBe('audio3.webm');
});
```

#### 4. **頁面重刷測試**
```typescript
it('重刷頁面後應能播放所有錄音', () => {
  // Given: 從 API 載入資料
  const apiData = {
    items: [
      { recording_url: 'saved1.webm' },
      { recording_url: 'saved2.webm' }
    ]
  };

  // When: 切換題目
  // Then: 每個題目都能正常播放其 recording_url
  題目.forEach((item, index) => {
    切換到題目(index);
    expect(可以播放).toBe(true);
    expect(播放URL).toBe(item.recording_url);
  });
});
```

### 重構原則
1. **移除 recordings 陣列** - 不需要額外維護錄音陣列
2. **直接使用 item.recording_url** - 資料在哪，就從哪取用
3. **簡化狀態管理** - 只需要 currentQuestionIndex
4. **保持向後相容** - 確保現有功能不受影響

### 驗收標準
- [ ] 所有題型都能正常錄音
- [ ] 切換題目時播放正確的錄音
- [ ] 重新錄音只影響當前題目
- [ ] 頁面重刷後所有錄音可播放
- [ ] 程式碼更簡潔直觀
- [ ] 移除不必要的陣列操作

---

**記住**：每次修改都要自己測試過，不要讓用戶一直幫你抓錯！
