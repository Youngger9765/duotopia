#!/bin/bash

# Check for exposed database URLs with passwords
if grep -E "postgresql://[^:]+:[^@]+@" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="Makefile" \
    -r . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v ".env.example" | \
    grep -v "dummy" | \
    grep -v "localhost"; then
    echo "Error: Exposed database URL with password found!"
    exit 1
fi

exit 0
