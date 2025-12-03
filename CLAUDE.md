# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 最高指导原则

### 1. 修完要自己去测试过！

### 2. GitHub Issue 处理必须使用 @agent-git-issue-pr-flow

⚠️ **当用户提到以下关键字时，自动使用 agent**：
- 「修复 issue」、「处理 issue #N」
- 「有什么 issue」、「巡逻 issues」
- 「部署到 staging」、「准备 release」
- 「检查 approval」、「查看批准状态」
- 任何提到 GitHub Issue 编号（#15, #7 等）

**Agent 功能**：
- 🔍 完整 PDCA 流程（Plan → Do → Check → Act）
- 🧪 TDD 测试驱动开发
- 🌐 Per-Issue Test Environment 管理
- ✅ AI 智能批准侦测
- 🛡️ Schema 变更保护

**详细说明**: `.claude/agents/git-issue-pr-flow.md`

---

## 🎯 Issue vs PR 职责分工

| 维度 | **Issue（业务层）** | **PR（技术层）** |
|------|-------------------|-----------------|
| **受众** | 👔 案主（非技术） | 💻 工程师（技术） |
| **目的** | 追踪业务价值 | 追踪技术品质 |
| **内容** | 问题、测试链接、批准 | 完整工程报告 |
| **通过标准** | ✅ 案主 OK | ✅ CI/CD OK |

---

## 🗄️ Database Migration 鐵則（全局規則）

**背景**：Develop 和 Staging 環境共用同一個資料庫，所有 migration 必須向前相容。

### ⚠️ Additive Migration 原則

**所有 migration 都必須是 Additive（新增型）**，無論是在哪個分支開發：

#### ✅ 允許的 Migration（必須使用 IF NOT EXISTS）

```python
# ✅ 新增表
op.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id SERIAL PRIMARY KEY,
        ...
    )
""")

# ✅ 新增欄位（必須 nullable 或有 DEFAULT）
op.execute("""
    ALTER TABLE users
    ADD COLUMN IF NOT EXISTS new_field VARCHAR(50) DEFAULT 'default_value'
""")

# ✅ 新增 Index
op.execute("""
    CREATE INDEX IF NOT EXISTS idx_name ON table_name (column)
""")

# ✅ 新增 Function（使用 CREATE OR REPLACE）
op.execute("""
    CREATE OR REPLACE FUNCTION function_name(...) RETURNS ... AS $$
    ...
    $$ LANGUAGE plpgsql;
""")
```

#### ❌ 禁止的 Migration（破壞性變更）

```python
# ❌ 刪除欄位（會破壞其他環境）
op.drop_column('users', 'old_field')
op.execute("ALTER TABLE users DROP COLUMN old_field")

# ❌ 重新命名（舊環境會找不到）
op.alter_column('users', 'name', new_column_name='full_name')
op.execute("ALTER TABLE users RENAME COLUMN name TO full_name")

# ❌ 修改欄位型別（可能導致資料損失）
op.alter_column('users', 'age', type_=sa.String())
op.execute("ALTER TABLE users ALTER COLUMN age TYPE VARCHAR")

# ❌ 刪除表（會破壞其他環境）
op.drop_table('old_table')
op.execute("DROP TABLE old_table")

# ❌ 不使用 IF NOT EXISTS（會在共用 DB 環境失敗）
op.create_table('new_table', ...)  # ❌ 第二次執行會失敗
```

### 🔍 為什麼需要 IF NOT EXISTS？

**場景說明**：
```
Day 1: feature-sentence merge 到 develop
  → develop CI/CD 執行 migration v12 (CREATE TABLE user_word_progress)
  → 資料庫：表已建立 ✅

Week 2: develop merge 到 staging
  → staging CI/CD 執行 migration v12
  → 如果沒有 IF NOT EXISTS，會報錯：table already exists ❌
  → 有 IF NOT EXISTS：跳過建立，繼續執行 ✅
```

**另一個場景**：
```
Day 1: feature-A merge 到 staging
  → staging 執行 migration v13 (ADD COLUMN)
  → 資料庫：欄位已加入

Day 2: staging merge 回 develop
  → develop 執行 migration v13
  → 如果沒有 IF NOT EXISTS，會報錯：column already exists ❌
```

### 📋 Migration Checklist（每次創建 migration 必須檢查）

創建 migration 前必須確認：
- [ ] 使用 `CREATE TABLE IF NOT EXISTS` 而非 `op.create_table()`
- [ ] 使用 `ADD COLUMN IF NOT EXISTS` 而非 `op.add_column()`
- [ ] 使用 `CREATE INDEX IF NOT EXISTS` 而非 `op.create_index()`
- [ ] 新增欄位有 `DEFAULT` 或 `nullable=True`
- [ ] 沒有 DROP, RENAME, ALTER TYPE 等破壞性操作
- [ ] Functions 使用 `CREATE OR REPLACE`

### 🔧 Migration 範例

**正確範例**（Phase 1 Sentence Making）：
```python
def upgrade() -> None:
    # ✅ 使用 IF NOT EXISTS
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_word_progress (
            id SERIAL PRIMARY KEY,
            ...
        )
    """)

    # ✅ Index 也用 IF NOT EXISTS
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_name ON table (column)
    """)

    # ✅ Function 用 CREATE OR REPLACE
    op.execute("""
        CREATE OR REPLACE FUNCTION update_memory_strength(...)
        RETURNS ... AS $$ ... $$ LANGUAGE plpgsql;
    """)
```

**錯誤範例**（會導致 staging/develop 衝突）：
```python
def upgrade() -> None:
    # ❌ 沒有 IF NOT EXISTS
    op.create_table('user_word_progress', ...)

    # ❌ 破壞性變更
    op.drop_column('users', 'old_field')
    op.alter_column('users', 'name', new_column_name='full_name')
```

### 🚨 違反規則的後果

1. **共用資料庫環境失敗**
   - Staging 執行 migration 失敗（表已存在）
   - Develop 無法測試功能

2. **資料損失風險**
   - 破壞性變更可能刪除正在測試的資料
   - 影響其他團隊成員的工作

3. **部署中斷**
   - CI/CD pipeline 失敗
   - 需要手動修復資料庫

### 📚 延伸閱讀

- [DEVELOP_ENVIRONMENT_PLAN.md](./docs/DEVELOP_ENVIRONMENT_PLAN.md) - Develop 環境架構說明
- [Migration 相容性策略](./docs/DEVELOP_ENVIRONMENT_PLAN.md#3-migration-相容性策略)

---

## 📝 Content Type 命名規範

### 標準命名（必須使用大寫）

| Content Type | 中文名稱 | 說明 |
|--------------|----------|------|
| `EXAMPLE_SENTENCES` | 例句集 | 聽音檔重組句子練習 |
| `VOCABULARY_SET` | 單字集 | 看單字造句練習 |
| `MULTIPLE_CHOICE` | 選擇題 | 單選題庫（未來） |
| `SCENARIO_DIALOGUE` | 情境對話 | 情境對話練習（未來） |

### ⚠️ 命名規則

1. **一律使用全大寫**：`EXAMPLE_SENTENCES` ✅，`example_sentences` ❌
2. **不要使用舊名稱**：
   - ❌ `READING_ASSESSMENT` → ✅ `EXAMPLE_SENTENCES`
   - ❌ `SENTENCE_MAKING` → ✅ `VOCABULARY_SET`
3. **資料庫已統一為新名稱**，程式碼中不應再使用舊名稱建立新資料

### 範例

```python
# ✅ 正確
content = Content(type=ContentType.EXAMPLE_SENTENCES, ...)

# ❌ 錯誤 - 不要使用舊名稱
content = Content(type=ContentType.READING_ASSESSMENT, ...)
```

```typescript
// ✅ 正確
const contentType = "EXAMPLE_SENTENCES";

// ❌ 錯誤 - 不要使用小寫或舊名稱
const contentType = "reading_assessment";
```

### 向後相容

後端的 `normalize_content_type()` 函數會自動將舊名稱轉換為新名稱：
- `READING_ASSESSMENT` → `EXAMPLE_SENTENCES`
- `SENTENCE_MAKING` → `VOCABULARY_SET`

但**新程式碼**應該直接使用新名稱。

---

## ⚠️ 必須遵守的操作順序 (STOP! READ FIRST!)

### Issue 的内容（给案主看）
- ✅ 问题描述（业务语言）
- ✅ 测试环境链接
- ✅ 案主测试结果和批准
- ❌ 不要放技术细节

### PR 的内容（给工程师看）
- ✅ 完整工程报告（根因分析、技术决策、测试覆盖率）
- ✅ CI/CD 状态检查
- ✅ 影响范围评估
- ❌ 不要放案主批准（在 Issue 中）

---

## 🔐 资安铁则

**绝对不要在任何会被 commit 的档案中硬编码 secrets！**

- ❌ 不要在 `.sh`, `.py`, `.ts`, `.yml` 中硬编码 secrets
- ✅ 本机：`.env` 档案（gitignore）
- ✅ CI/CD：GitHub Secrets (`gh secret set`)
- ✅ 生产：Cloud Run 环境变数或 Secret Manager
- ✅ 程式码：从环境变数读取 (`os.getenv()`, `import.meta.env`)

---

## 🔴 绝对禁止

1. **`git commit --no-verify`** - 必须修复所有 pre-commit 错误
2. **主动 commit/push** - 必须等待用户明确命令
3. **草率判断「修复完成」** - 必须完整测试

---

## ⚠️ 操作顺序 (STOP! READ FIRST!)

### 执行任何重要操作前：
1. **先查 README** - 了解专案标准流程
2. **先查 CLAUDE.md** - 了解专案特定规则
3. **先查 package.json/requirements.txt** - 了解已有的脚本命令
4. **绝对不要自作主张创建资源** - 永远使用专案既有的配置

### 🔴 红线规则（绝对禁止）
- ❌ 手动 gcloud 命令创建资源 → 必须使用专案配置
- ❌ 猜测版本号 → 必须查证
- ❌ 忽略专案既有工具 → npm scripts, pytest 优先
- ❌ 未读取配置前就执行命令 → 先读后做

---

## 🚨 测试驱动开发 (TDD)

### 每次修改后的测试流程

```bash
# 1. 型别检查
npm run typecheck

# 2. 代码检查
npm run lint

# 3. 建置测试
npm run build

# 4. 执行测试
npm run test:api:all     # 后端测试
npm run test:e2e         # E2E 测试

# 5. 实际浏览器测试
open http://localhost:5173/[修改的页面]
# 检查 Console 是否有错误
# 检查 Network API 请求
```

### ⚠️ 不要混淆前后端工具

**前端**：`package.json`, `npm`, `tsconfig.json`, `vite.config.ts`
**后端**：`requirements.txt`, `pip`, `pytest.ini`, `pyproject.toml`
**通用**：`Makefile`, `docker-compose.yml`, `.env`

### 判断修复完成的标准
- [ ] API 返回正确的状态码和资料结构
- [ ] 前端页面正常显示
- [ ] 功能可以正常操作
- [ ] 没有 console 错误
- [ ] 截图证明功能正常

**记住：用户一直帮你抓错 = 你没做好测试！**

---

## 🔴 Git Commit/Push 流程

**标准流程**：
1. 修改代码
2. **自己测试** - 执行上述所有测试步骤
3. **报告测试结果** - 告诉用户测试通过与否
4. **等待命令** - ⚠️ 绝对不要主动 commit 或 push

**正确示范**：
```
✅ 我：修改完成，已测试通过（附测试结果）
✅ 用户：commit push
✅ 我：执行 git commit && git push
```

**错误示范**：
```
❌ 我：修改完成，现在 commit...（自作主张）
❌ 我：测试通过，推送到 staging...（没等命令）
```

---

## 🧪 测试档案组织原则

### 📁 测试目录结构
```
duotopia/
├── backend/tests/           # ✅ 所有 Python 测试
│   ├── unit/               # 单元测试
│   ├── integration/        # 整合测试
│   │   ├── api/           # API 测试
│   │   └── auth/          # 认证测试
│   └── e2e/               # E2E 测试
└── frontend/tests/          # ✅ 前端测试
```

### 🎯 测试分类原则

**单元测试** (`backend/tests/unit/`):
- 测试单一函数或类别
- 不依赖外部资源（资料库、API）
- 档名：`test_模组名称.py`

**整合测试** (`backend/tests/integration/`):
- API 测试、认证测试
- 档名：`test_功能描述.py`

**E2E 测试** (`backend/tests/e2e/`):
- 测试完整用户流程
- 从登入到完成任务

### 🚨 禁止事项
- ❌ 放在根目录 `tests/` - 会造成混乱
- ❌ 放在 `backend/scripts/` - 脚本不是测试
- ❌ 用奇怪档名 - 如 `test_phase2_api.py`
- ❌ 混合不同测试类型

### 🔧 测试执行指令

```bash
# NPM Scripts（推荐）
npm run test:api                 # 所有 API 测试
npm run test:api:unit            # 单元测试
npm run test:api:integration     # 整合测试
npm run test:api:e2e             # E2E 测试
npm run test:all                 # 所有测试

# 直接使用 pytest（进阶）
cd backend
pytest                           # 所有测试
pytest -v                        # 详细输出
pytest tests/unit/               # 只执行单元测试
pytest --cov=. --cov-report=html # 测试覆盖率
```

---

## 🔍 完成工作前的检查清单

### 回报「完成」前必须执行：

```bash
# 1. 检查档案位置
git status --short

# 2. 清理不必要的档案
# 删除所有 *_temp.py, *_old.py, *_backup.py

# 3. 执行完整测试
npm run test:api:all
npm run build

# 4. 检查 code formatting
black --check backend/
npm run lint

# 5. 检查 git diff
git diff --stat
```

### 📋 回报格式标准

```markdown
## ✅ 完成项目
- [具体完成的功能/修复]

## 📊 测试结果
- Unit tests: X/X PASSED
- Integration tests: X/X PASSED
- Build: ✅ SUCCESS

## 📝 修改的档案
1. `路径/档案名` - 做了什么修改

## ⏳ 待用户确认
- 等待 commit 指示
```

---

## 🏗️ 平台开发核心原则

> **"There is nothing more permanent than a temporary solution"**

### 基础设施优先 (Infrastructure First)
- ✅ Cloud SQL + Cloud Run 从第一天开始
- ✅ Terraform 管理所有基础设施
- ✅ CI/CD pipeline 第一周建立
- ✅ Secret Manager 管理所有密码
- ❌ 避免：档案系统当资料库、手写部署脚本、"暂时"的解决方案

### 资料架构不妥协 (Data Architecture)
- ✅ PostgreSQL 作为 Single Source of Truth
- ✅ 正确的关联式设计（外键、CASCADE DELETE）
- ✅ 使用成熟的 ORM（SQLAlchemy）
- ❌ 避免：混用多种储存方式、没有外键约束

### DevOps 文化 (Everything as Code)
- ✅ Infrastructure as Code (Terraform)
- ✅ Configuration as Code (环境变数)
- ✅ Deployment as Code (CI/CD)
- ❌ 避免：手动配置伺服器、SSH 修改设定、没有回滚机制

---

## 📚 相关文件

- **产品需求**: [PRD.md](./PRD.md)
- **部署与 CI/CD**: [CICD.md](./CICD.md)
- **测试指南**: [docs/TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)
- **部署状态**: [docs/DEPLOYMENT_STATUS.md](./docs/DEPLOYMENT_STATUS.md)
- **Git Issue PR Flow Agent**: [.claude/agents/git-issue-pr-flow.md](./.claude/agents/git-issue-pr-flow.md)
