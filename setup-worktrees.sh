#!/bin/bash
# Git Worktrees Setup for Duotopia
# Based on three-environment deployment: Production (main) / Staging (staging) / Preview (feature/*)

set -e

PROJECT_NAME="duotopia"
PROJECT_ROOT="$HOME/project/$PROJECT_NAME"
WORKTREE_ROOT="$HOME/worktrees/$PROJECT_NAME"

echo "🌳 Setting up Git Worktrees for $PROJECT_NAME"
echo ""

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Show existing worktrees
echo "📋 Existing worktrees:"
git worktree list
echo ""

# Create worktree directory
mkdir -p "$WORKTREE_ROOT"

# Create standard worktrees
echo "🔧 Creating standard worktrees..."

# Main worktree (for PR review and production merges)
if [ ! -d "$WORKTREE_ROOT/main" ]; then
    echo "  Creating main worktree..."
    git worktree add "$WORKTREE_ROOT/main" main
    echo "  ✅ Created: $WORKTREE_ROOT/main"
else
    echo "  ⏭️  Skipped: main worktree already exists"
fi

# Staging worktree (for daily development)
if [ ! -d "$WORKTREE_ROOT/staging" ]; then
    echo "  Creating staging worktree..."
    git worktree add "$WORKTREE_ROOT/staging" staging
    echo "  ✅ Created: $WORKTREE_ROOT/staging"
else
    echo "  ⏭️  Skipped: staging worktree already exists"
fi

echo ""
echo "✅ Worktree setup complete!"
echo ""
echo "📂 Worktree locations:"
echo "  Main:    $WORKTREE_ROOT/main"
echo "  Staging: $WORKTREE_ROOT/staging"
echo "  Current: $PROJECT_ROOT"
echo ""
echo "💡 Usage:"
echo "  cd $WORKTREE_ROOT/main      # Switch to main for PR review"
echo "  cd $WORKTREE_ROOT/staging   # Switch to staging for daily work"
echo "  cd $PROJECT_ROOT            # Return to feature branch"
echo ""
echo "🧹 Cleanup:"
echo "  git worktree remove main"
echo "  git worktree remove staging"
