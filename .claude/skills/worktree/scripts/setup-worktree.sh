#!/bin/bash
# Setup git worktree for isolated development
# Supports two modes:
#   Issue mode: ./setup-worktree.sh --issue <issue-number> [base-branch]
#   Task mode:  ./setup-worktree.sh --task <slug> [base-branch]
#
# Examples:
#   ./setup-worktree.sh --issue 42
#   ./setup-worktree.sh --issue 42 main
#   ./setup-worktree.sh --task optimize-homepage-loading
#   ./setup-worktree.sh --task fix-navbar-mobile staging

set -e

WORKTREE_DIR=".worktrees"
BASE_BRANCH="staging"
MODE=""
IDENTIFIER=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --issue|-i)
            MODE="issue"
            IDENTIFIER="$2"
            shift 2
            ;;
        --task|-t)
            MODE="task"
            IDENTIFIER="$2"
            shift 2
            ;;
        *)
            # Remaining argument is base branch
            if [ -n "$1" ]; then
                BASE_BRANCH="$1"
            fi
            shift
            ;;
    esac
done

# Validate mode
if [ -z "$MODE" ]; then
    echo "Error: Mode required (--issue or --task)"
    echo ""
    echo "Usage:"
    echo "  $0 --issue <issue-number> [base-branch]"
    echo "  $0 --task <slug> [base-branch]"
    echo ""
    echo "Examples:"
    echo "  $0 --issue 42"
    echo "  $0 --task optimize-homepage"
    exit 1
fi

# Validate identifier
if [ -z "$IDENTIFIER" ]; then
    echo "Error: Identifier required"
    if [ "$MODE" = "issue" ]; then
        echo "Usage: $0 --issue <issue-number>"
    else
        echo "Usage: $0 --task <slug>"
    fi
    exit 1
fi

# Ensure worktree directory exists
ensure_worktree_dir() {
    if [ ! -d "$WORKTREE_DIR" ]; then
        echo "Creating worktree directory: $WORKTREE_DIR"
        mkdir -p "$WORKTREE_DIR"
    fi

    # Ensure directory is git-ignored
    if ! git check-ignore -q "$WORKTREE_DIR" 2>/dev/null; then
        echo "Adding $WORKTREE_DIR to .gitignore"
        echo "$WORKTREE_DIR/" >> .gitignore
    fi
}

# Setup for issue mode
setup_issue_worktree() {
    local ISSUE_NUM="$1"

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

    # Create worktree
    create_worktree "$WORKTREE_PATH" "$BRANCH_NAME"

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
}

# Setup for task mode
setup_task_worktree() {
    local TASK_SLUG="$1"

    # Sanitize slug: lowercase, replace non-alphanumeric with dash, limit to 30 chars
    TASK_SLUG=$(echo "$TASK_SLUG" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | cut -c1-30 | sed 's/-$//')

    # Fallback: generate random 16-char string if slug is empty (e.g., Chinese-only input)
    if [ -z "$TASK_SLUG" ]; then
        TASK_SLUG="task-$(date +%s%N | shasum | cut -c1-16)"
        echo "Warning: Empty slug after sanitization, using fallback: $TASK_SLUG"
    fi

    # Generate Task ID: YYYYMMDD-NNN
    TODAY=$(date +%Y%m%d)

    # Find existing task worktrees for today and get next number
    EXISTING=$(ls -1 "$WORKTREE_DIR" 2>/dev/null | grep "^task-${TODAY}-" | sort -r | head -1 || true)
    if [ -n "$EXISTING" ]; then
        LAST_NUM=$(echo "$EXISTING" | sed "s/task-${TODAY}-//" | sed 's/^0*//')
        NEXT_NUM=$((LAST_NUM + 1))
    else
        NEXT_NUM=1
    fi

    TASK_ID=$(printf "%s-%03d" "$TODAY" "$NEXT_NUM")

    # Branch name format: fix/YYYYMMDD-NNN-<slug>
    BRANCH_NAME="fix/${TASK_ID}-${TASK_SLUG}"
    WORKTREE_PATH="${WORKTREE_DIR}/task-${TASK_ID}"

    # Check if worktree already exists (unlikely with timestamp)
    if [ -d "$WORKTREE_PATH" ]; then
        echo "Worktree already exists at $WORKTREE_PATH"
        echo "Current branch: $(cd "$WORKTREE_PATH" && git branch --show-current)"
        exit 0
    fi

    # Create worktree
    create_worktree "$WORKTREE_PATH" "$BRANCH_NAME"

    # Report success
    echo ""
    echo "Worktree created successfully!"
    echo "  Path: $WORKTREE_PATH"
    echo "  Branch: $BRANCH_NAME"
    echo "  Base: origin/$BASE_BRANCH"
    echo "  Task ID: ${TASK_ID}"
    echo "  Description: ${TASK_SLUG}"
    echo ""
    echo "To work in this worktree:"
    echo "  cd $WORKTREE_PATH"
}

# Common function to create worktree
create_worktree() {
    local WORKTREE_PATH="$1"
    local BRANCH_NAME="$2"

    # Fetch latest from remote
    echo "Fetching latest $BASE_BRANCH..."
    git fetch origin "$BASE_BRANCH"

    # Create worktree with new branch
    echo "Creating worktree at $WORKTREE_PATH with branch $BRANCH_NAME"
    git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "origin/$BASE_BRANCH"
}

# Main execution
ensure_worktree_dir

case $MODE in
    issue)
        setup_issue_worktree "$IDENTIFIER"
        ;;
    task)
        setup_task_worktree "$IDENTIFIER"
        ;;
esac
