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

| Environment | URL | Branch |
|-------------|-----|--------|
| Production | https://duotopia.com | main |
| Staging | https://staging.duotopia.com | staging |

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
npm run test:api:all
npm run typecheck
npm run lint
npm run build

# Git workflow (via agent)
create-feature-fix <issue> <desc>
deploy-feature <issue>
```

## Project-Specific Rules

1. **組織層級管理** - 見 `ORG_IMPLEMENTATION_SPEC.md`
2. **TapPay 金流整合** - 見 `TAPPAY_INTEGRATION_GUIDE.md`
3. **Per-Issue Test Environment** - 每個 issue 有獨立測試環境
4. **Use feature branches** - 不直接 commit 到 staging

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
