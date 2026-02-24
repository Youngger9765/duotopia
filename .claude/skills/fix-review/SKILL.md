---
name: fix-review
description: |
  Auto-fix PR review feedback iteratively until the PR is ready to merge.
  Monitors Claude Code Review CI, analyzes comments, applies fixes, and repeats.
  Only asks the user when human judgment is needed.
argument-hint: "<PR-number>"
disable-model-invocation: false
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebFetch, TodoWrite, AskUserQuestion
---

# Fix Review Skill

Automatically analyze and fix Claude Code Review feedback on a PR, iterating until the PR is merge-ready.

**Announce at start:** "I'm using the fix-review skill to automatically resolve PR review feedback."

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
- Identify the head branch (this is where we'll make fixes)

### 1.3 Ensure we're on the correct branch

Check if we are currently on the PR's head branch. If not:
1. Check if a worktree exists for this branch
2. If yes, work in that worktree
3. If no, switch to the branch or inform the user

```bash
PR_BRANCH=$(gh pr view "$PR_NUM" --json headRefName -q '.headRefName')
CURRENT_BRANCH=$(git branch --show-current)

if [ "$CURRENT_BRANCH" != "$PR_BRANCH" ]; then
    # Check worktrees
    WORKTREE_PATH=$(git worktree list | grep "$PR_BRANCH" | awk '{print $1}')
    if [ -n "$WORKTREE_PATH" ]; then
        echo "Found worktree at: $WORKTREE_PATH"
        # Work in this worktree
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

# Phase 2: Check Review Status

### 2.1 Check Claude Code Review CI status

```bash
gh pr checks "$PR_NUM" --json name,conclusion,status
```

Classify the result:

| CI Status | Review Comments | Classification | Action |
|-----------|----------------|---------------|--------|
| queued / in_progress | - | `WAITING` | Poll every 30s until complete |
| failure | Has comments | `REVIEW_FAILED` | Analyze comments and fix |
| failure | No comments | `CI_INFRA_ERROR` | Check logs, notify user |
| success | Has comments | `REVIEW_PASSED_WITH_SUGGESTIONS` | Ask user if they want to address |
| success | No comments | `CLEAN` | PR is merge-ready |

### 2.2 Handle WAITING status

```bash
echo "Claude Code Review is running... polling every 30 seconds"

while true; do
    STATUS=$(gh pr checks "$PR_NUM" --json name,status | jq -r '.[] | select(.name == "claude-review") | .status')
    if [ "$STATUS" != "IN_PROGRESS" ] && [ "$STATUS" != "QUEUED" ]; then
        break
    fi
    sleep 30
done
```

### 2.3 Handle CI_INFRA_ERROR

If the review CI failed but there are no review comments, this is an infrastructure issue (e.g., workflow validation, token error).

```bash
# Get the failed run ID
RUN_ID=$(gh run list --workflow="Claude Code Review" --branch="$PR_BRANCH" --limit=1 --json databaseId -q '.[0].databaseId')

# Get the failure reason
gh run view "$RUN_ID" --log-failed | tail -30
```

Report to user:
```
The Claude Code Review CI failed due to an infrastructure issue, not a code problem.

**Error**: [extracted error message]
**Suggested fix**: [based on error type]

Would you like me to attempt to fix this, or would you prefer to handle it manually?
```

Use `AskUserQuestion` to let the user decide.

---

# Phase 3: Fetch and Analyze Review Comments

### 3.1 Fetch review comments

Claude Code Review posts comments via `gh pr comment`, so fetch PR comments:

```bash
# Get all comments on the PR
gh api repos/{owner}/{repo}/issues/$PR_NUM/comments --jq '.[] | select(.user.login == "github-actions[bot]" or .user.login == "claude[bot]") | {id: .id, body: .body, created_at: .created_at}' | jq -s 'sort_by(.created_at) | last'
```

Also check for PR review comments (inline):

```bash
gh api repos/{owner}/{repo}/pulls/$PR_NUM/comments --jq '.[] | select(.user.login == "github-actions[bot]" or .user.login == "claude[bot]") | {id: .id, path: .path, line: .line, body: .body}'
```

### 3.2 Parse review into actionable items

For each review comment/item, classify as:

1. **AUTO_FIX** - Clear, specific code change that can be applied automatically
   - Examples: "rename variable X to Y", "add error handling for null case", "fix typo in string"

2. **NEEDS_CONTEXT** - Requires reading more code to understand the right fix
   - Examples: "this function could have a race condition", "consider edge case X"

3. **NEEDS_HUMAN** - Requires human judgment or architectural decision
   - Examples: "consider using a different approach", "this design pattern may not scale"

4. **INFORMATIONAL** - No action needed, just feedback
   - Examples: "nice approach here", "good use of X pattern"

### 3.3 Create todo list

Use TodoWrite to track each review item:

```
- [ ] [AUTO_FIX] Fix typo in UserService.ts:42
- [ ] [AUTO_FIX] Add null check in handleSubmit
- [ ] [NEEDS_CONTEXT] Review race condition in fetchData
- [ ] [NEEDS_HUMAN] Consider refactoring auth middleware
- [x] [INFORMATIONAL] Positive feedback on test coverage (no action)
```

---

# Phase 4: Apply Fixes

### 4.1 Handle AUTO_FIX items

For each AUTO_FIX item:
1. Read the relevant file
2. Understand the context around the issue
3. Apply the fix using Edit tool
4. Mark the todo item as completed

### 4.2 Handle NEEDS_CONTEXT items

For each NEEDS_CONTEXT item:
1. Read the relevant files and surrounding code
2. Analyze the issue
3. If the fix becomes clear → apply it (treat as AUTO_FIX)
4. If still ambiguous → escalate to NEEDS_HUMAN

### 4.3 Handle NEEDS_HUMAN items

Batch all NEEDS_HUMAN items and present to user:

```markdown
## Review Items Requiring Your Input

### 1. [File: path/to/file.ts, Line 42]
**Review comment**: "Consider using a different approach for state management"
**My analysis**: [what I found after reading the code]
**Options**:
  A) [Proposed fix A]
  B) [Proposed fix B]
  C) Skip this item

### 2. [File: path/to/other.ts, Line 15]
...
```

Use `AskUserQuestion` for each decision needed.

### 4.4 Commit and push

After all fixes are applied:

```bash
# Stage changed files (specific files only, not git add -A)
git add [specific files]

# Commit with descriptive message
git commit -m "fix: address Claude Code Review feedback for PR #$PR_NUM

- [list of changes made]

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Push
git push origin "$PR_BRANCH"
```

**IMPORTANT**: Always ask the user before committing. Show them what will be committed.

---

# Phase 5: Wait and Re-evaluate

### 5.1 Wait for new review

After pushing, the Claude Code Review CI will re-trigger automatically.

```bash
echo "Changes pushed. Waiting for Claude Code Review to re-run..."

# Wait for the new run to appear (may take a few seconds)
sleep 10

# Poll for completion
while true; do
    LATEST_RUN=$(gh run list --workflow="Claude Code Review" --branch="$PR_BRANCH" --limit=1 --json databaseId,status,conclusion)
    STATUS=$(echo "$LATEST_RUN" | jq -r '.[0].status')

    if [ "$STATUS" = "completed" ]; then
        CONCLUSION=$(echo "$LATEST_RUN" | jq -r '.[0].conclusion')
        break
    fi

    echo "Review still running... (status: $STATUS)"
    sleep 30
done
```

### 5.2 Check new results

Go back to **Phase 2** and repeat the cycle:
1. Check if there are new review comments
2. If yes → analyze and fix (Phase 3-4)
3. If no new comments and CI passed → move to Phase 6

### 5.3 Loop limit

Maximum **3 iterations** of the fix cycle. If after 3 rounds there are still unresolved issues:

```
I've completed 3 rounds of review fixes. There are still [N] unresolved items:
- [item 1]
- [item 2]

These may require a different approach. Would you like me to:
A) Continue with another round
B) Show you the remaining items for manual review
C) Proceed to merge as-is
```

---

# Phase 6: Report Merge Readiness

When the review cycle is complete (no more actionable comments):

```markdown
## PR #$PR_NUM is ready to merge

**Title**: [PR title]
**Branch**: $PR_BRANCH → $BASE_BRANCH

### Review Summary
- **Rounds of fixes**: [N]
- **Total items resolved**: [N]
- **Items skipped (by your decision)**: [N]

### Changes made during review fixes
- [commit 1 summary]
- [commit 2 summary]

### CI Status
- Claude Code Review: Passed
- [Other checks]: [status]

You can merge this PR now.
```

---

# Edge Cases

### No review bot comment found but CI passed

The review may have run successfully but the bot couldn't post (permissions issue). Check the run log:

```bash
RUN_ID=$(gh run list --workflow="Claude Code Review" --branch="$PR_BRANCH" --limit=1 --json databaseId -q '.[0].databaseId')
gh run view "$RUN_ID" --log | grep -i "comment\|review\|error" | tail -20
```

If the log shows the review completed with no issues → PR is clean.
If the log shows a posting error → notify user about the permissions issue.

### PR branch has conflicts

If during `git pull --rebase` there are conflicts:

```
The PR branch has conflicts with the base branch. This needs to be resolved before I can apply review fixes.

Would you like me to attempt to resolve the conflicts, or would you prefer to handle this manually?
```

### Review comments reference files not in the PR diff

Skip these items and note:
```
Skipping review item about [file] - this file is not part of the PR diff.
The reviewer may have gone out of scope.
```

### Multiple review comment sources

Comments may come from:
- `github-actions[bot]` - Claude Code Action
- `claude[bot]` - Direct Claude bot
- Human reviewers

This skill only auto-fixes bot review comments. For human reviewer comments, present them to the user without auto-fixing.

---

# Red Flags - Never Do These

- Apply fixes without understanding the full context of the code
- Auto-fix items classified as NEEDS_HUMAN without user approval
- Push changes without asking the user first
- Modify files not mentioned in the review
- Ignore review comments about security issues
- Loop more than 3 times without user intervention
- Make changes to the base branch instead of the PR branch
- Skip running existing tests after making changes
- Auto-resolve merge conflicts without user awareness
