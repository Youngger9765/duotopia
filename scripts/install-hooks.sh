#!/bin/bash
#================================================================
# Install Git Hooks for Duotopia Project
# This script installs custom Git hooks for the team
#================================================================

echo "📦 Installing Duotopia Git Hooks..."

# Create hooks directory if not exists
mkdir -p .git/hooks

# Install post-push hook
cat > .git/hooks/post-push << 'EOF'
#!/bin/bash
# Auto-monitor deployment after push

BRANCH=$(git rev-parse --abbrev-ref HEAD)

if [[ "$BRANCH" == "staging" ]] || [[ "$BRANCH" == "main" ]]; then
    echo "🚀 Deployment triggered for $BRANCH"
    echo "📊 Monitor with: npm run monitor:$BRANCH"
    echo "🔗 View at: https://github.com/myduotopia/duotopia/actions"

    # Optional: Auto-start monitor (uncomment if desired)
    # (sleep 5 && npm run monitor:$BRANCH 2>/dev/null) &
fi
EOF

chmod +x .git/hooks/post-push

echo "✅ Post-push hook installed"
echo ""
echo "📝 Installed hooks:"
echo "   - post-push: Auto-monitor deployment"
echo ""
echo "💡 Tips:"
echo "   - Run 'npm run monitor' after push to monitor deployment"
echo "   - Run 'npm run cleanup:images' to manually clean images"
echo "   - Run 'npm run deploy:status' to check deployment status"
