#!/bin/bash
# Cleanup git worktree after work is complete
# Supports two modes:
#   Issue mode: ./cleanup-worktree.sh --issue <issue-number>
#   Task mode:  ./cleanup-worktree.sh --task <task-id>
#   Auto mode:  ./cleanup-worktree.sh <identifier> (auto-detects type)
#
# Examples:
#   ./cleanup-worktree.sh --issue 42
#   ./cleanup-worktree.sh --task 20260127-001
#   ./cleanup-worktree.sh 42           # Auto-detects as issue
#   ./cleanup-worktree.sh 20260127-001 # Auto-detects as task

set -e

WORKTREE_DIR=".worktrees"
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
            # Auto-detect mode from identifier format
            IDENTIFIER="$1"
            shift
            ;;
    esac
done

# Validate identifier
if [ -z "$IDENTIFIER" ]; then
    echo "Error: Identifier required"
    echo ""
    echo "Usage:"
    echo "  $0 --issue <issue-number>"
    echo "  $0 --task <task-id>"
    echo "  $0 <identifier>  (auto-detects type)"
    echo ""
    echo "Examples:"
    echo "  $0 --issue 42"
    echo "  $0 --task 20260127-001"
    echo "  $0 42"
    exit 1
fi

# Auto-detect mode if not specified
if [ -z "$MODE" ]; then
    # Strip # prefix if present
    IDENTIFIER="${IDENTIFIER#\#}"

    # Check if it's a task ID (YYYYMMDD-NNN format)
    if [[ "$IDENTIFIER" =~ ^[0-9]{8}-[0-9]{3}$ ]]; then
        MODE="task"
    # Check if it's a numeric issue number
    elif [[ "$IDENTIFIER" =~ ^[0-9]+$ ]]; then
        MODE="issue"
    else
        echo "Error: Could not auto-detect type from identifier: $IDENTIFIER"
        echo "Use --issue or --task flag to specify explicitly"
        exit 1
    fi
fi

# Determine worktree path based on mode
case $MODE in
    issue)
        IDENTIFIER="${IDENTIFIER#\#}"  # Strip # prefix
        if ! [[ "$IDENTIFIER" =~ ^[0-9]+$ ]]; then
            echo "Error: Issue number must be numeric, got: $IDENTIFIER"
            exit 1
        fi
        WORKTREE_PATH="${WORKTREE_DIR}/issue-${IDENTIFIER}"
        ;;
    task)
        if ! [[ "$IDENTIFIER" =~ ^[0-9]{8}-[0-9]{3}$ ]]; then
            echo "Error: Task ID must be in YYYYMMDD-NNN format, got: $IDENTIFIER"
            exit 1
        fi
        WORKTREE_PATH="${WORKTREE_DIR}/task-${IDENTIFIER}"
        ;;
esac

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

# Check if branch should be deleted
if [ -n "$BRANCH_NAME" ] && git show-ref --verify --quiet "refs/heads/$BRANCH_NAME" 2>/dev/null; then
    echo "Local branch $BRANCH_NAME exists."
    read -p "Delete local branch? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BRANCH_NAME"
        echo "Local branch deleted."
    fi
fi

# Check for related branches
echo ""
echo "Checking for related branches..."

case $MODE in
    issue)
        PATTERN="issue-${IDENTIFIER}([^0-9]|$)"
        ;;
    task)
        PATTERN="${IDENTIFIER}"
        ;;
esac

RELATED_BRANCHES=$(git branch -a 2>/dev/null | grep -E "$PATTERN" | sed 's/^[* ]*//' || true)

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
