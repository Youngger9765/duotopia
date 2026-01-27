#!/bin/bash
# Setup git worktree for issue handling
# Usage: ./setup-worktree.sh <issue-number> [base-branch]

set -e

ISSUE_NUM="$1"
BASE_BRANCH="${2:-staging}"
WORKTREE_DIR=".worktrees"
BRANCH_NAME="claude/issue-${ISSUE_NUM}"
WORKTREE_PATH="${WORKTREE_DIR}/issue-${ISSUE_NUM}"

# Validate input
if [ -z "$ISSUE_NUM" ]; then
    echo "Error: Issue number required"
    echo "Usage: $0 <issue-number> [base-branch]"
    exit 1
fi

# Strip # prefix if present
ISSUE_NUM="${ISSUE_NUM#\#}"

# Ensure worktree directory exists
if [ ! -d "$WORKTREE_DIR" ]; then
    echo "Creating worktree directory: $WORKTREE_DIR"
    mkdir -p "$WORKTREE_DIR"
fi

# Ensure directory is git-ignored
if ! git check-ignore -q "$WORKTREE_DIR" 2>/dev/null; then
    echo "Adding $WORKTREE_DIR to .gitignore"
    echo "$WORKTREE_DIR/" >> .gitignore
fi

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
    echo "Worktree already exists at $WORKTREE_PATH"
    echo "Current branch: $(cd $WORKTREE_PATH && git branch --show-current)"
    exit 0
fi

# Fetch latest from remote
echo "Fetching latest $BASE_BRANCH..."
git fetch origin "$BASE_BRANCH"

# Create worktree with new branch
echo "Creating worktree at $WORKTREE_PATH with branch $BRANCH_NAME"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "origin/$BASE_BRANCH"

# Report success
echo ""
echo "Worktree created successfully!"
echo "  Path: $WORKTREE_PATH"
echo "  Branch: $BRANCH_NAME"
echo "  Base: origin/$BASE_BRANCH"
echo ""
echo "To work in this worktree:"
echo "  cd $WORKTREE_PATH"
