#!/bin/bash
# Setup git worktree for issue handling
# Usage: ./setup-worktree.sh <issue-number> [base-branch]

set -e

ISSUE_NUM="$1"
BASE_BRANCH="${2:-staging}"
WORKTREE_DIR=".worktrees"

# Validate input
if [ -z "$ISSUE_NUM" ]; then
    echo "Error: Issue number required"
    echo "Usage: $0 <issue-number> [base-branch]"
    exit 1
fi

# Strip # prefix if present
ISSUE_NUM="${ISSUE_NUM#\#}"

# Validate issue number is numeric only (security check)
if ! [[ "$ISSUE_NUM" =~ ^[0-9]+$ ]]; then
    echo "Error: Issue number must be numeric, got: $ISSUE_NUM"
    exit 1
fi

# Get issue title and create slug for branch name
echo "Fetching issue #${ISSUE_NUM} details..."
ISSUE_TITLE=$(gh issue view "$ISSUE_NUM" --json title -q '.title' 2>/dev/null || echo "")

if [ -z "$ISSUE_TITLE" ]; then
    echo "Error: Could not fetch issue #${ISSUE_NUM}. Make sure it exists and you have access."
    exit 1
fi

# Convert title to slug: lowercase, replace non-alphanumeric with dash, limit to 30 chars
ISSUE_SLUG=$(echo "$ISSUE_TITLE" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-30 | sed 's/-$//')

# Branch name follows project standard: fix/issue-<N>-<description>
BRANCH_NAME="fix/issue-${ISSUE_NUM}-${ISSUE_SLUG}"
WORKTREE_PATH="${WORKTREE_DIR}/issue-${ISSUE_NUM}"

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
    echo "Current branch: $(cd "$WORKTREE_PATH" && git branch --show-current)"
    exit 0
fi

# Check if branch already exists
if git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
    echo "Warning: Branch $BRANCH_NAME already exists locally"
fi

if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME" 2>/dev/null; then
    echo "Warning: Branch $BRANCH_NAME already exists on remote"
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
echo "  Issue: #${ISSUE_NUM} - ${ISSUE_TITLE}"
echo ""
echo "To work in this worktree:"
echo "  cd $WORKTREE_PATH"
