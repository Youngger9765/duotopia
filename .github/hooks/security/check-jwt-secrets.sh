#!/bin/bash

# Check for exposed JWT secrets
echo "🔐 Checking for exposed JWT secrets..."

# Check for hardcoded JWT secrets
if grep -r -E "JWT_SECRET\s*=\s*[\"'][^\"']+[\"']" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.json" \
    --include="Makefile" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude="*.example" \
    2>/dev/null | \
    grep -v "os.getenv" | \
    grep -v "process.env" | \
    grep -v "import.meta.env" | \
    grep -v "dummy" | \
    grep -v "your-"; then
    echo "❌ Error: Hardcoded JWT_SECRET found!"
    echo "Use environment variables instead: os.getenv('JWT_SECRET')"
    exit 1
fi

# Check for weak JWT secrets in committed files
if grep -r "secret\|password\|123456\|qwerty" \
    --include="*.env.example" \
    . 2>/dev/null | \
    grep -i "JWT"; then
    echo "⚠️  Warning: Weak JWT secret in example files"
fi

echo "✅ No exposed JWT secrets found"
exit 0
