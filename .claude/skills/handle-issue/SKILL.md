---
name: handle-issue
description: Handle GitHub issues using git worktrees for isolated, parallel development. Use when user says "handle issue", "fix issue", "work on issue", or provides issue numbers to work on.
argument-hint: "<issue-number> [issue-number2 ...]"
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch
---

# Handle Issue Skill

Handle one or more GitHub issues using git worktrees for parallel, isolated development.

**Announce at start:** "I'm using the handle-issue skill to set up isolated worktrees for issue(s) #$ARGUMENTS."

## Arguments

- `$ARGUMENTS` - Space-separated issue numbers (e.g., `42`, `42 43 44`, `#42 #43`)

## Current Context

- **Repository**: !`basename $(git rev-parse --show-toplevel)`
- **Current branch**: !`git branch --show-current`
- **Worktrees**: !`git worktree list 2>/dev/null | head -5`

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────┐
│  1. SETUP         Create worktree from staging              │
│                   └─ .worktrees/issue-<N>                   │
│                   └─ Branch: claude/issue-<N>               │
├─────────────────────────────────────────────────────────────┤
│  2. ANALYZE       Read GitHub issue content                 │
│                   └─ gh issue view <N>                      │
│                   └─ Identify requirements & questions      │
├─────────────────────────────────────────────────────────────┤
│  3. PLAN          Present structured plan                   │
│                   └─ Problem summary                        │
│                   └─ Proposed solution                      │
│                   └─ Files to modify                        │
│                   └─ ⏸️ STOP: Wait for user approval        │
├─────────────────────────────────────────────────────────────┤
│  4. IMPLEMENT     After approval, execute in worktree       │
│                   └─ TDD: Write tests first                 │
│                   └─ Implement solution                     │
│                   └─ Run tests                              │
│                   └─ Commit & push                          │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1: Setup Worktree

### 1.1 Verify worktree directory

```bash
# Check if .worktrees exists
if [ ! -d ".worktrees" ]; then
    mkdir -p .worktrees
    # Ensure it's in .gitignore
    if ! git check-ignore -q .worktrees 2>/dev/null; then
        echo ".worktrees/" >> .gitignore
        git add .gitignore
        git commit -m "chore: add .worktrees to gitignore"
    fi
fi
```

### 1.2 Fetch latest staging and create worktree

```bash
# For each issue number in $ARGUMENTS
ISSUE_NUM=<extracted-number>

git fetch origin staging

# Create worktree with new branch from staging
git worktree add .worktrees/issue-${ISSUE_NUM} -b claude/issue-${ISSUE_NUM} origin/staging
```

### 1.3 Install dependencies (if needed)

```bash
cd .worktrees/issue-${ISSUE_NUM}

# Backend (Python)
if [ -d backend ] && [ -f backend/requirements.txt ]; then
    cd backend && pip install -r requirements.txt && cd ..
fi

# Frontend (Node.js)
if [ -f package.json ]; then
    npm install
fi
```

## Phase 2: Analyze Issue

### 2.1 Read GitHub issue

```bash
gh issue view ${ISSUE_NUM} --json title,body,labels,comments,assignees
```

### 2.2 Analysis checklist

- [ ] Understand the problem statement
- [ ] Identify acceptance criteria
- [ ] Check for linked issues or PRs
- [ ] Note labels (bug, feature, priority)
- [ ] Review any existing comments
- [ ] List unclear requirements or questions

## Phase 3: Present Plan (CRITICAL: STOP FOR APPROVAL)

Present the plan in this format:

```markdown
## Issue #<NUM>: <Title>

### Problem Summary
[One paragraph summary of the issue]

### Proposed Solution
1. [Step 1 - specific action]
2. [Step 2 - specific action]
3. [Step 3 - specific action]

### Files to Modify
- `path/to/file1.py` - [what changes]
- `path/to/file2.tsx` - [what changes]

### Test Plan
- [ ] Test case 1: [description]
- [ ] Test case 2: [description]

### Questions (if any)
- [ ] Question 1?
- [ ] Question 2?

### Scope Assessment
- [ ] Small (1-2 files, straightforward)
- [ ] Medium (3-5 files, some complexity)
- [ ] Large (6+ files, significant changes)

---
**Worktree**: `.worktrees/issue-<NUM>`
**Branch**: `claude/issue-<NUM>`

Please review and confirm this plan, or provide feedback.
```

**IMPORTANT**: Do NOT proceed to Phase 4 until user explicitly approves.

## Phase 4: Implement (After Approval Only)

### 4.1 Work in the worktree

```bash
cd .worktrees/issue-${ISSUE_NUM}
```

### 4.2 TDD Development

1. **Red Phase**: Write failing tests first
   ```bash
   # Create test file
   # backend/tests/integration/api/test_issue_${ISSUE_NUM}.py
   ```

2. **Green Phase**: Implement the fix
   - Make minimal changes to pass tests
   - Follow existing code patterns

3. **Refactor Phase**: Clean up if needed

### 4.3 Run tests

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run typecheck && npm run build
```

### 4.4 Commit changes

```bash
git add .
git commit -m "fix: [description] (Related to #${ISSUE_NUM})

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 4.5 Push branch

```bash
git push -u origin claude/issue-${ISSUE_NUM}
```

### 4.6 Report completion

```markdown
## Issue #<NUM> Implementation Complete

**Branch**: `claude/issue-<NUM>` (pushed)
**Worktree**: `.worktrees/issue-<NUM>`

### Changes Made
- [Change 1]
- [Change 2]

### Test Results
- Backend: X tests passed
- Frontend: Build successful

### Next Steps
1. Create PR to staging: `gh pr create --base staging`
2. Wait for CI/CD checks
3. Request case owner testing
```

## Handling Multiple Issues

When `$ARGUMENTS` contains multiple issue numbers:

### Parallel Setup
```bash
# Extract all issue numbers
ISSUES="$ARGUMENTS"  # e.g., "42 43 44"

# Create all worktrees
for NUM in $ISSUES; do
    git worktree add .worktrees/issue-${NUM} -b claude/issue-${NUM} origin/staging &
done
wait
```

### Present All Plans Together

```markdown
# Plans for Issues $ARGUMENTS

## Issue #42: [Title]
[Full plan...]

---

## Issue #43: [Title]
[Full plan...]

---

## Issue #44: [Title]
[Full plan...]

---

Please review all plans. You can:
- Approve all: "proceed with all"
- Approve specific: "proceed with #42 and #43"
- Request changes: "for #42, please also consider..."
```

## Worktree Management Commands

```bash
# List all worktrees
git worktree list

# Check status of specific worktree
cd .worktrees/issue-<NUM> && git status

# Remove worktree (after PR merged)
git worktree remove .worktrees/issue-<NUM>
git branch -D claude/issue-<NUM>  # if branch exists locally
```

## Red Flags - Never Do These

- Implement without presenting plan first
- Skip user confirmation before coding
- Work in main workspace instead of worktree
- Create branches from `main` instead of `staging`
- Push without running tests
- Assume requirements without asking
- Commit directly to `staging` branch

## Integration with Other Workflows

After implementation, use the standard PDCA workflow:
1. Create PR with `gh pr create --base staging`
2. Use "Fixes #<NUM>" in PR body to auto-close issue
3. Wait for CI/CD checks
4. Wait for case owner approval
5. Merge via `gh pr merge --squash`

See `.claude/agents/git-issue-pr-flow.md` for complete workflow details.
