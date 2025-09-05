#!/bin/bash

# Check for hardcoded credentials in code (excluding test files)
if grep -E "(password|secret|key|token|pwd)\\s*=\\s*[\"'][^\"']+[\"']" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="Makefile" \
    -r . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=tests \
    --exclude-dir=__tests__ \
    2>/dev/null | \
    grep -v ".env.example" | \
    grep -v "your-" | \
    grep -v "dummy" | \
    grep -v "TODO" | \
    grep -v "test-token"; then
    echo "Error: Hardcoded credentials found!"
    exit 1
fi

exit 0
