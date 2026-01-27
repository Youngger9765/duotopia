#!/bin/bash
# Cleanup git worktree after issue is resolved
# Usage: ./cleanup-worktree.sh <issue-number>

set -e

ISSUE_NUM="$1"
WORKTREE_DIR=".worktrees"

# Validate input
if [ -z "$ISSUE_NUM" ]; then
    echo "Error: Issue number required"
    echo "Usage: $0 <issue-number>"
    exit 1
fi

# Strip # prefix if present
ISSUE_NUM="${ISSUE_NUM#\#}"

# Validate issue number is numeric only (security check)
if ! [[ "$ISSUE_NUM" =~ ^[0-9]+$ ]]; then
    echo "Error: Issue number must be numeric, got: $ISSUE_NUM"
    exit 1
fi

WORKTREE_PATH="${WORKTREE_DIR}/issue-${ISSUE_NUM}"

# Check if worktree exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo "Error: Worktree not found at $WORKTREE_PATH"
    echo ""
    echo "Available worktrees:"
    git worktree list
    exit 1
fi

# Get the branch name from the worktree
BRANCH_NAME=$(cd "$WORKTREE_PATH" && git branch --show-current)

# Check for uncommitted changes
if [ -n "$(cd "$WORKTREE_PATH" && git status --porcelain)" ]; then
    echo "Warning: Worktree has uncommitted changes!"
    (cd "$WORKTREE_PATH" && git status --short)
    echo ""
    read -p "Discard changes and remove? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Remove worktree
echo "Removing worktree at $WORKTREE_PATH..."
git worktree remove "$WORKTREE_PATH" --force

# Check if branch should be deleted (handles both fix/issue-* and claude/issue-* formats)
if [ -n "$BRANCH_NAME" ] && git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
    echo "Local branch $BRANCH_NAME exists."
    read -p "Delete local branch? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BRANCH_NAME"
        echo "Local branch deleted."
    fi
fi

# Also check for any other branches related to this issue
echo ""
echo "Checking for other branches related to issue #${ISSUE_NUM}..."
RELATED_BRANCHES=$(git branch -a 2>/dev/null | grep -E "issue-${ISSUE_NUM}([^0-9]|$)" | sed 's/^[* ]*//' || true)

if [ -n "$RELATED_BRANCHES" ]; then
    echo "Found related branches:"
    echo "$RELATED_BRANCHES"
    echo ""
    echo "Note: Use 'git branch -D <branch>' to delete local branches"
    echo "      Use 'git push origin --delete <branch>' to delete remote branches"
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "Remaining worktrees:"
git worktree list
