# Duotopia

> 通用規則見 `~/.claude/CLAUDE.md`（Agent 路由、Git、Security、TDD）

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / FastAPI |
| Database | PostgreSQL (Supabase) |
| Frontend | Node.js (shared) |
| Deploy | Vercel / GCP Cloud Run |

## Environments

| Environment | URL | Branch | Database |
|-------------|-----|--------|----------|
| Production | https://duotopia.com | main | Supabase (prod) |
| Staging | https://staging.duotopia.com | staging | Supabase (staging) |
| Develop | https://develop.duotopia.com | develop | Supabase (develop) |

> **Note**: 每個環境使用獨立的 Supabase project，資料庫不共用。

## Key Docs

| Doc | Purpose |
|-----|---------|
| [PRD.md](./PRD.md) | 產品需求 |
| [ORG_IMPLEMENTATION_SPEC.md](./ORG_IMPLEMENTATION_SPEC.md) | 組織層級規格 |
| [TESTING_GUIDE.md](./docs/TESTING_GUIDE.md) | 測試指南 |
| [TAPPAY_INTEGRATION_GUIDE.md](./docs/integrations/TAPPAY_INTEGRATION_GUIDE.md) | 金流整合 |
| [CICD.md](./CICD.md) | 部署與 CI/CD |

## Project-Specific Agents

### @agent-git-issue-pr-flow
**Trigger**: issue, fix, bug, #N, 部署, staging
- PDCA workflow + TDD enforcement
- Per-Issue Test Environment
- AI-powered approval detection

### @agent-error-reflection
**Trigger**: errors, test failures, user corrections
- 錯誤模式學習
- `/reflect [error]` - 手動反思
- `/weekly-review` - 週報

**Learning Files**: `.claude/learning/*.json`

## Project Hooks

| Hook | Script | Purpose |
|------|--------|---------|
| UserPromptSubmit | `check-agent-rules.py` | Agent 路由檢查 |
| PreToolUse(Write\|Edit) | `check-file-size.py` | 檔案大小檢查 |
| PostToolUse(Write\|Edit) | Auto-format | 程式碼格式化 |
| Stop | `error-reflection.py` | 錯誤學習 |

## Commands

```bash
# Testing
npm run test:api:all          # Backend API tests
npm run typecheck             # TypeScript type checking
npm run lint                  # ESLint
npm run build                 # Production build

# Chrome Testing (MANDATORY for UI changes)
# Use Playwright to test in Chrome - NO manual testing
npx playwright test           # Run all browser tests
npx playwright test --headed  # Run with visible browser
npx playwright codegen <url>  # Record new test

# Git workflow (via agent)
create-feature-fix <issue> <desc>
deploy-feature <issue>
```

## Testing Rules (CRITICAL)

### ❌ 禁止說「手動測試」
- **絕對不能**叫用戶手動在 Chrome 測試
- **必須**使用 Playwright 自動化測試
- **必須**提供截圖證明

### ✅ 正確測試流程
1. Backend API: `pytest tests/test_*.py -v`
2. Frontend UI: Playwright 測試 + 截圖
3. 提供測試證明（terminal output + screenshots）

### 🔑 測試登入

**登入頁面有快速登入按鈕 - 直接點擊即可！**

打開 `http://localhost:5173/teacher/login`，頁面底部有：
- 「Demo Teacher (300 days prepaid)」← 點這個
- 「Trial Teacher (30-day trial)」
- 其他測試帳號...

**Playwright 登入**:
```typescript
// 直接點快速登入按鈕，不需要輸入帳密
await page.goto('http://localhost:5173/teacher/login');
await page.locator('text=Demo Teacher (300 days prepaid)').first().click();
await page.waitForURL('**/teacher/dashboard');
```

**環境**:
- Backend: `localhost:8080` ⚠️ (不是 8000!)
- Frontend: `localhost:5173`
- `.env.local`: `VITE_API_URL=http://localhost:8080`

## Project-Specific Rules

1. **組織層級管理** - 見 `ORG_IMPLEMENTATION_SPEC.md`
2. **TapPay 金流整合** - 見 `TAPPAY_INTEGRATION_GUIDE.md`
3. **Per-Issue Test Environment** - 每個 issue 有獨立測試環境
4. **Use feature branches** - 不直接 commit 到 staging

<<<<<<< HEAD
### 🚨 Database Migration 規則 (CRITICAL)

**絕對禁止未經許可創建 Migrations：**

- ❌ **禁止** 未經明確許可創建任何 `backend/alembic/versions/*.py` files
- ❌ **禁止** 執行 `alembic revision` without asking first
- ✅ **必須** 在創建 migration 前明確詢問：「需要創建 DB migration，是否允許？」

**原因：**
- Alembic migration chain 在 merge 時會衝突
- 多個 feature branches 同時有 migrations → 難以 merge
- Production database schema 變更需要謹慎規劃

**替代方案（Preview/Dev 環境）：**
```python
# 使用 seed scripts with IF NOT EXISTS：
op.execute("""
    CREATE TABLE IF NOT EXISTS teacher_schools (
        ...
    )
""")
```
=======
## Database Migration 鐵則

> **核心原則**：所有 migration 必須是 **Idempotent（冪等）**，可安全重複執行。

### ✅ 必須使用的寫法

```python
# 新增表 - 使用 IF NOT EXISTS
op.execute("""
    CREATE TABLE IF NOT EXISTS new_table (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100)
    )
""")

# 新增欄位 - 使用 IF NOT EXISTS + nullable 或 DEFAULT
op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'users' AND column_name = 'new_field') THEN
            ALTER TABLE users ADD COLUMN new_field VARCHAR(50) DEFAULT 'default_value';
        END IF;
    END $$;
""")

# 新增 Index - 使用 IF NOT EXISTS
op.execute("CREATE INDEX IF NOT EXISTS idx_name ON table_name (column)")

# 新增 Constraint - 檢查後再建立
op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_table_column') THEN
            ALTER TABLE table_name ADD CONSTRAINT uq_table_column UNIQUE (column);
        END IF;
    END $$;
""")

# Function - 使用 CREATE OR REPLACE
op.execute("CREATE OR REPLACE FUNCTION func_name() RETURNS ... AS $$ ... $$ LANGUAGE plpgsql;")
```

### ❌ 禁止的寫法

```python
# ❌ 直接使用 Alembic op（重複執行會失敗）
op.create_table('new_table', ...)
op.add_column('users', sa.Column('field', ...))
op.create_index('idx_name', 'table', ['column'])

# ❌ 破壞性變更（會破壞其他環境）
op.drop_column('users', 'old_field')
op.alter_column('users', 'name', new_column_name='full_name')
op.drop_table('old_table')
```

### 為什麼需要 Idempotent？

1. **多環境部署**：同一個 migration 可能在 develop、staging、production 各執行一次
2. **時序問題**：不同分支的 migration 可能以不同順序執行
3. **重試安全**：部署失敗重試時不會報錯
4. **Feature branch**：Per-Issue 環境可能先於 staging 執行 migration

### Migration Checklist

建立 migration 前必須確認：
- [ ] 使用 `CREATE TABLE IF NOT EXISTS`
- [ ] 使用 `ADD COLUMN IF NOT EXISTS` 或 DO $$ 檢查
- [ ] 使用 `CREATE INDEX IF NOT EXISTS`
- [ ] Constraint 使用 pg_constraint 檢查後再建立
- [ ] 新增欄位有 `DEFAULT` 或 `nullable=True`
- [ ] 沒有 DROP, RENAME, ALTER TYPE 等破壞性操作
- [ ] Functions 使用 `CREATE OR REPLACE`
>>>>>>> origin/staging
