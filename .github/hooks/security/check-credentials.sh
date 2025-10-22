#!/bin/bash

# Check for hardcoded credentials (case-insensitive)
if grep -iE "(password|secret|key|token|pwd|api_key)\\s*=\\s*[\"'][^\"']{8,}[\"']" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.yml" \
    --include="*.yaml" \
    --include="Makefile" \
    -r . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=tests \
    --exclude-dir=__tests__ \
    2>/dev/null | \
    grep -v ".env" | \
    grep -v "example" | \
    grep -v "your-" | \
    grep -v "dummy" | \
    grep -v "TODO" | \
    grep -v "test-token" | \
    grep -v "xxx"; then
    echo "❌ Error: Hardcoded credentials found!"
    exit 1
fi

exit 0
