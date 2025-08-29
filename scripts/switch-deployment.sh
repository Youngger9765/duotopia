#!/bin/bash

# 部署配置切換工具
# Usage: ./scripts/switch-deployment.sh [staging|production] [supabase|cloudsql]

ENV=$1
DB=$2
WORKFLOW_DIR=".github/workflows"

if [ -z "$ENV" ] || [ -z "$DB" ]; then
    echo "Usage: $0 [staging|production] [supabase|cloudsql]"
    echo ""
    echo "Current active workflows:"
    ls -la $WORKFLOW_DIR/*.yml 2>/dev/null | awk '{print "  - "$NF}'
    echo ""
    echo "Available backup workflows:"
    ls -la $WORKFLOW_DIR/*.backup 2>/dev/null | awk '{print "  - "$NF}'
    exit 1
fi

echo "🔄 Switching to $ENV with $DB..."

# Backup current
if [ -f "$WORKFLOW_DIR/deploy-$ENV.yml" ]; then
    echo "📦 Backing up current deploy-$ENV.yml"
    mv "$WORKFLOW_DIR/deploy-$ENV.yml" "$WORKFLOW_DIR/deploy-$ENV.yml.temp"
fi

# Restore target
TARGET="$WORKFLOW_DIR/deploy-$ENV-$DB.yml.backup"
if [ -f "$TARGET" ]; then
    echo "✅ Activating $ENV-$DB configuration"
    cp "$TARGET" "$WORKFLOW_DIR/deploy-$ENV.yml"
    echo "✅ Switched to $ENV with $DB"
    
    if [ "$DB" = "cloudsql" ]; then
        echo "💰 WARNING: Cloud SQL costs $2.28/day ($68.40/month)"
    else
        echo "🆓 Using Supabase (free tier)"
    fi
else
    echo "❌ Configuration not found: $TARGET"
    # Restore original if exists
    if [ -f "$WORKFLOW_DIR/deploy-$ENV.yml.temp" ]; then
        mv "$WORKFLOW_DIR/deploy-$ENV.yml.temp" "$WORKFLOW_DIR/deploy-$ENV.yml"
    fi
    exit 1
fi

# Clean temp
rm -f "$WORKFLOW_DIR/deploy-$ENV.yml.temp"

echo ""
echo "📝 Next steps:"
echo "1. Review the changes: git diff"
echo "2. Commit: git add -A && git commit -m 'Switch $ENV to $DB'"
echo "3. Push: git push origin $ENV"