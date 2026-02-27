---
name: fix-workflow
description: |
  Auto-fix CI test workflow errors (backend/frontend) on a PR.
  Parses failed GitHub Actions logs, identifies error type, applies fixes, and re-pushes.
  Handles: Black, Flake8, Prettier, TypeScript, ESLint, build errors, and pytest failures.
argument-hint: "<PR-number>"
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, TodoWrite, AskUserQuestion
---

# Fix Workflow Skill

Automatically analyze and fix CI test workflow failures on a PR, iterating until all checks pass.

**Announce at start:** "I'm using the fix-workflow skill to automatically resolve CI test failures."

## Arguments

- `$ARGUMENTS` - PR number (e.g., `322`, `#322`)

## Current Context

- **Repository**: !`basename $(git rev-parse --show-toplevel)`
- **Current branch**: !`git branch --show-current`
- **Working directory**: !`pwd`

---

# Phase 1: Initialize

### 1.1 Parse PR number

```bash
PR_NUM="${ARGUMENTS#\#}"

# Validate PR number is numeric
if ! [[ "$PR_NUM" =~ ^[0-9]+$ ]]; then
    echo "Error: PR number must be numeric, got: $PR_NUM"
    exit 1
fi
```

### 1.2 Get PR metadata

```bash
gh pr view "$PR_NUM" --json title,headRefName,baseRefName,state,body
```

Verify:
- PR is OPEN
- Identify the head branch

### 1.3 Ensure we're on the correct branch

Check if we are currently on the PR's head branch. If not:
1. Check if a worktree exists for this branch
2. If yes, work in that worktree
3. If no, switch to the branch or inform the user

```bash
PR_BRANCH=$(gh pr view "$PR_NUM" --json headRefName -q '.headRefName')
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "$PR_BRANCH" ]; then
    WORKTREE_PATH=$(git worktree list | grep -F "$PR_BRANCH" | awk '{print $1}')
    if [ -n "$WORKTREE_PATH" ]; then
        echo "Found worktree at: $WORKTREE_PATH"
    else
        echo "Warning: Not on PR branch. Current: $CURRENT_BRANCH, PR: $PR_BRANCH"
        # Ask user how to proceed
    fi
fi
```

### 1.4 Pull latest changes

```bash
git pull --rebase origin "$PR_BRANCH"
```

---

# Phase 2: Identify Failed Workflow Checks

### 2.1 Get all PR check statuses

```bash
gh pr checks "$PR_NUM" --json name,conclusion,status
```

### 2.2 Classify each check

Focus on **test workflow jobs** only (not review or deploy):

| Check Name Pattern | Workflow | Type |
|--------------------|----------|------|
| Contains "Test Backend" | deploy-backend.yml | `BACKEND_TEST` |
| Contains "Test Frontend" | deploy-frontend.yml | `FRONTEND_TEST` |
| Contains "claude-review" | automation-claude-review.yml | `REVIEW` (skip - handled by /fix-review) |
| Contains "Deploy" | deploy-*.yml | `DEPLOY` (skip - depends on tests) |

### 2.3 Determine action

| Test Status | Classification | Action |
|-------------|---------------|--------|
| All test checks passed | `CLEAN` | Report success, exit |
| queued / in_progress | `WAITING` | Poll every 30s until complete |
| Backend test failed | `BACKEND_FAILED` | Fetch logs and fix |
| Frontend test failed | `FRONTEND_FAILED` | Fetch logs and fix |
| Both failed | `BOTH_FAILED` | Fix backend first, then frontend |
| No test checks found | `NO_TESTS` | Inform user (PR may not trigger test workflows) |

### 2.4 Handle WAITING status

```bash
echo "Test workflows are running... polling every 30 seconds"
POLL_COUNT=0

while true; do
    CHECKS=$(gh pr checks "$PR_NUM" --json name,status,conclusion)
    PENDING=$(echo "$CHECKS" | jq '[.[] | select(.name | test("Test Backend|Test Frontend"; "i")) | select(.status != "completed")] | length')
    if [ "$PENDING" = "0" ]; then
        break
    fi
    POLL_COUNT=$((POLL_COUNT + 1))
    if [ "$POLL_COUNT" -ge 60 ]; then
        echo "ERROR: Timed out after 30 minutes waiting for CI checks to complete."
        break
    fi
    echo "Still waiting for $PENDING check(s)... (poll $POLL_COUNT/60)"
    sleep 30
done
```

---

# Phase 3: Fetch and Parse Failed Logs

### 3.1 Get the failed run ID

```bash
# For backend
BACKEND_RUN_ID=$(gh run list --workflow="Deploy Backend (Cloud Run)" --branch="$PR_BRANCH" --limit=1 --json databaseId,conclusion -q '.[0].databaseId // empty')
if [ -z "$BACKEND_RUN_ID" ]; then
    echo "No backend workflow run found for branch $PR_BRANCH"
fi

# For frontend
FRONTEND_RUN_ID=$(gh run list --workflow="Deploy Frontend (Cloud Run)" --branch="$PR_BRANCH" --limit=1 --json databaseId,conclusion -q '.[0].databaseId // empty')
if [ -z "$FRONTEND_RUN_ID" ]; then
    echo "No frontend workflow run found for branch $PR_BRANCH"
fi
```

### 3.2 Fetch failed step logs

```bash
# Get failed logs (only failed steps are shown)
gh run view "$RUN_ID" --log-failed
```

### 3.3 Parse errors by step name

Identify which step failed by looking at the log output prefix. Each log line starts with the job and step name.

**Backend test steps (in order, first failure stops):**

| Step | Error Pattern | Fix Strategy |
|------|--------------|--------------|
| `Run Black formatting check` | Shows file paths with reformatting needed | `AUTO_FIX` - Run `black backend/` |
| `Run Flake8 linting` | `file.py:line:col: E/W/F code message` | `PARSE_AND_FIX` - Read each error, fix code |
| `Apply migrations to fresh DB` | Alembic error messages | `NEEDS_HUMAN` - Migration errors are complex |
| `Test backend import` | `ImportError` / `ModuleNotFoundError` | `PARSE_AND_FIX` - Fix import statements |

**Note:** Steps with `continue-on-error: true` (model-migration sync, unit tests, integration tests) do NOT cause the workflow to fail. Skip these.

**Frontend test steps (in order, first failure stops):**

| Step | Error Pattern | Fix Strategy |
|------|--------------|--------------|
| `Run Prettier formatting check` | Shows file paths needing formatting | `AUTO_FIX` - Run `npx prettier --write frontend/src` |
| `Run frontend type check` | `file.ts(line,col): error TSxxxx: message` | `PARSE_AND_FIX` - Read each error, fix types |
| `Run ESLint check` | `file.ts line:col error/warning rule-name` | `PARSE_AND_FIX` - Try `--fix` first, then manual |
| `Run API Testing Framework` | Test failure output | `PARSE_AND_FIX` - Read test and source, fix |
| `Build frontend (test build)` | Vite/Rollup build errors | `PARSE_AND_FIX` - Usually import/type issues |

### 3.4 Create structured error list

For each error found, create an entry:

```
{
  "step": "Run Black formatting check",
  "type": "AUTO_FIX" | "PARSE_AND_FIX" | "NEEDS_HUMAN",
  "file": "backend/services/auth.py",
  "line": 42,
  "error_code": "E501",
  "message": "line too long (120 > 79 characters)",
  "raw_log": "..."
}
```

Use TodoWrite to track each error group.

---

# Phase 4: Apply Fixes

### 4.1 AUTO_FIX: Formatting errors (Black / Prettier)

These are the easiest - just run the formatter locally:

**Black (backend):**
```bash
cd backend && black .
```

**Prettier (frontend):**
```bash
cd frontend && npx prettier --write src
```

> **Note:** These commands format all files in the directory, not just PR-changed files. This ensures consistency but may produce slightly larger diffs. The CI checks run the same way, so this matches the expected behavior.

After running, verify the formatter made changes:
```bash
git diff --stat
```

Mark as completed immediately.

### 4.2 PARSE_AND_FIX: Linting errors (Flake8 / ESLint)

**ESLint - try auto-fix first:**
```bash
cd frontend && npx eslint --fix src/
```

Check if all errors were resolved by re-running lint:
```bash
cd frontend && npm run lint:ci 2>&1
```

If errors remain, parse each one and fix manually:
1. Read the file at the error location
2. Understand the surrounding context
3. Apply the fix using Edit tool
4. Move to next error

**Flake8 - manual fix required:**

Flake8 has no auto-fix. For each error:
1. Parse the error: `file.py:line:col: CODE message`
2. Read the file at that location
3. Apply the appropriate fix based on error code:
   - `E501` (line too long): Break the line
   - `E302` (expected 2 blank lines): Add blank lines
   - `F401` (imported but unused): Remove the import
   - `F841` (local variable assigned but never used): Remove or use the variable
   - `W291/W292/W293` (whitespace): Remove trailing whitespace
   - Other codes: Read context and fix appropriately
4. Mark as completed

### 4.3 PARSE_AND_FIX: TypeScript type errors

Parse `tsc` output format: `src/file.ts(line,col): error TS2xxx: message`

For each error:
1. Read the file at the error location (include surrounding context, ~20 lines)
2. Understand the type relationship
3. Common fixes:
   - `TS2322` (Type not assignable): Fix type annotation or value
   - `TS2339` (Property does not exist): Add property to interface or fix property name
   - `TS2345` (Argument type mismatch): Fix argument type
   - `TS2307` (Cannot find module): Fix import path
   - `TS7006` (Parameter implicitly has 'any'): Add type annotation
   - `TS18047/TS18048` (Possibly null/undefined): Add null check
4. Apply fix with Edit tool
5. After fixing all errors, verify locally:
   ```bash
   cd frontend && npx tsc --noEmit 2>&1 | head -50
   ```

### 4.4 PARSE_AND_FIX: Build errors

Build errors from `npm run build` (Vite/Rollup) are often caused by:
- The same TypeScript errors (fix those first)
- Missing imports/exports
- Circular dependencies

If build fails after TypeScript errors are fixed:
1. Parse the build output
2. Identify the root cause
3. Fix and verify: `cd frontend && npm run build 2>&1 | tail -30`

### 4.5 PARSE_AND_FIX: Import errors (backend)

For `python -c "import main"` failures:
1. Parse the ImportError/ModuleNotFoundError
2. Trace the import chain
3. Fix the broken import (typo, missing file, circular import)

### 4.6 PARSE_AND_FIX: Test failures (pytest / API tests)

For test failures:
1. Parse the test output to identify failing test(s)
2. Read the test file AND the source file being tested
3. Determine if the fix should be in the source or the test:
   - If the test is correct and source is wrong → fix source
   - If the source is correct and test is outdated → fix test
   - If unclear → escalate to NEEDS_HUMAN
4. Apply fix and verify locally if possible

### 4.7 NEEDS_HUMAN: Complex errors

For errors that require human judgment:
- Migration failures
- Architectural issues
- Ambiguous test failures
- Errors in files not part of the PR

Present to user with analysis:
```markdown
## Workflow Error Requiring Your Input

### Error in: [step name]
**File**: path/to/file
**Error**: [error message]
**My analysis**: [what I found]
**Options**:
  A) [Proposed fix A]
  B) [Proposed fix B]
  C) Skip this error
```

Use `AskUserQuestion` for each decision.

---

# Phase 5: Commit, Push, and Re-check

### 5.1 Verify fixes locally (when possible)

Before committing, run local checks where feasible:

```bash
# Backend formatting
cd backend && black --check . 2>&1 | tail -5

# Frontend formatting
cd frontend && npx prettier --check src 2>&1 | tail -5

# Frontend types
cd frontend && npx tsc --noEmit 2>&1 | tail -20

# Frontend lint
cd frontend && npm run lint:ci 2>&1 | tail -20
```

Only verify checks that were actually failing - don't run unnecessary checks.

### 5.2 Commit and push

```bash
# Stage specific files only
git add [specific files that were modified]

# Commit with descriptive message
git commit -m "fix: resolve CI test failures for PR #$PR_NUM

- [list of fixes applied]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Push
git push origin "$PR_BRANCH"
```

**IMPORTANT**: Always ask the user before committing. Show them what will be committed.

### 5.3 Wait for CI re-run

```bash
echo "Changes pushed. Waiting for test workflows to re-run..."
sleep 10
POLL_COUNT=0

while true; do
    CHECKS=$(gh pr checks "$PR_NUM" --json name,status,conclusion)
    PENDING=$(echo "$CHECKS" | jq '[.[] | select(.name | test("Test Backend|Test Frontend"; "i")) | select(.status != "completed")] | length')
    if [ "$PENDING" = "0" ]; then
        break
    fi
    POLL_COUNT=$((POLL_COUNT + 1))
    if [ "$POLL_COUNT" -ge 60 ]; then
        echo "ERROR: Timed out after 30 minutes waiting for CI checks to complete."
        break
    fi
    echo "Tests still running... ($PENDING pending, poll $POLL_COUNT/60)"
    sleep 30
done
```

### 5.4 Re-evaluate

Go back to **Phase 2** and check results:
- If all tests pass → Phase 6
- If new/different errors → repeat Phase 3-5
- Same errors persisting → escalate to user

### 5.5 Loop limit

Maximum **3 iterations**. After 3 rounds:

```
I've completed 3 rounds of workflow fixes. There are still failing checks:
- [check 1]: [error summary]
- [check 2]: [error summary]

Would you like me to:
A) Continue with another round
B) Show detailed error logs for manual debugging
C) Proceed anyway (tests may be non-blocking)
```

---

# Phase 6: Report

When all test workflows pass:

```markdown
## CI Test Workflows - All Passing

**PR**: #$PR_NUM - [PR title]
**Branch**: $PR_BRANCH

### Fix Summary
- **Rounds**: [N]
- **Errors fixed**: [N]
- **Errors skipped**: [N] (by your decision)

### Changes Made
- [file1]: [what was fixed]
- [file2]: [what was fixed]

### Current CI Status
- Test Backend: Passed
- Test Frontend: Passed
- Claude Code Review: [status]
- Deploy: [status - only runs on push to protected branches]
```

---

# Error Type Quick Reference

## Auto-fixable (no human input needed)

| Error | Command | Confidence |
|-------|---------|------------|
| Black formatting | `cd backend && black .` | 100% |
| Prettier formatting | `cd frontend && npx prettier --write src` | 100% |
| ESLint auto-fixable rules | `cd frontend && npx eslint --fix src/` | ~80% |

## Parseable (auto-fix with code understanding)

| Error | Parse Format | Approach |
|-------|-------------|----------|
| Flake8 | `file:line:col: CODE msg` | Fix by error code |
| TypeScript | `file(line,col): error TSxxxx: msg` | Fix type/import |
| Build errors | Various | Usually import/type related |
| Import errors | `ImportError: ...` | Fix import chain |

## Requires human judgment

| Error | Reason |
|-------|--------|
| Migration failures | Database schema decisions |
| Pytest failures (ambiguous) | Source vs test correctness |
| Architectural issues | Design decisions |

---

# Edge Cases

### PR doesn't trigger test workflows

If no test checks appear for the PR (e.g., changes only affect non-triggering paths):
```
No test workflow checks found for this PR. The changed files may not trigger
the test workflows. Check the workflow path filters in deploy-backend.yml
and deploy-frontend.yml.
```

### continue-on-error steps

Steps with `continue-on-error: true` in the workflow (currently: model-migration sync, unit tests, integration tests) do NOT cause overall workflow failure. Do NOT attempt to fix these unless the user specifically asks.

### Only one workflow is failing

If only backend OR frontend tests fail, only fix the failing one. Do not touch the other.

### Errors in files outside the PR diff

If the test failure is caused by a file not changed in the PR (pre-existing issue):
```
The test failure in [file] appears to be a pre-existing issue, not caused
by changes in this PR. Would you like me to fix it anyway, or skip it?
```

Use `AskUserQuestion` to decide.

### Network/infrastructure failures

If the workflow log shows infrastructure issues (e.g., npm registry timeout, Docker pull failure) rather than code errors:
```
The workflow failed due to an infrastructure issue, not a code problem.

**Error**: [extracted message]
**Suggestion**: Re-run the workflow via GitHub Actions UI, or wait and push again.
```

---

# Red Flags - Never Do These

- Apply formatting fixes to files outside the repository (node_modules, etc.)
- Auto-fix errors in migration files without user approval
- Push changes without asking the user first
- Ignore security-related lint errors (treat as NEEDS_HUMAN)
- Run `black` or `prettier` with overly broad paths that format vendored/generated code
- Loop more than 3 times without user intervention
- Attempt to fix `continue-on-error` steps unless explicitly asked
- Modify test expectations to make tests pass without understanding why they fail
- Make changes to the base branch instead of the PR branch
