#!/bin/bash
# Cleanup git worktree after issue is resolved
# Usage: ./cleanup-worktree.sh <issue-number>

set -e

ISSUE_NUM="$1"
WORKTREE_DIR=".worktrees"
BRANCH_NAME="claude/issue-${ISSUE_NUM}"
WORKTREE_PATH="${WORKTREE_DIR}/issue-${ISSUE_NUM}"

# Validate input
if [ -z "$ISSUE_NUM" ]; then
    echo "Error: Issue number required"
    echo "Usage: $0 <issue-number>"
    exit 1
fi

# Strip # prefix if present
ISSUE_NUM="${ISSUE_NUM#\#}"

# Check if worktree exists
if [ ! -d "$WORKTREE_PATH" ]; then
    echo "Worktree not found at $WORKTREE_PATH"
    echo "Available worktrees:"
    git worktree list
    exit 1
fi

# Check for uncommitted changes
if [ -n "$(cd $WORKTREE_PATH && git status --porcelain)" ]; then
    echo "Warning: Worktree has uncommitted changes!"
    cd "$WORKTREE_PATH" && git status --short
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

# Check if branch should be deleted
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME"; then
    echo "Local branch $BRANCH_NAME exists."
    read -p "Delete local branch? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BRANCH_NAME"
        echo "Local branch deleted."
    fi
fi

echo ""
echo "Cleanup complete!"
echo ""
echo "Remaining worktrees:"
git worktree list
