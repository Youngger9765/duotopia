# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 最高指導原則：修完要自己去測試過！

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

## 📚 相關文件

- **產品需求**: 詳見 [PRD.md](./PRD.md)
- **部署與 CI/CD**: 詳見 [CICD.md](./CICD.md)
- **測試指南**: 詳見 [docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)
- **部署狀態**: 詳見 [docs/DEPLOYMENT_STATUS.md](./docs/DEPLOYMENT_STATUS.md)

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
