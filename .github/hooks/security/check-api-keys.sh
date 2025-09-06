#!/bin/bash

# Check for exposed API keys
echo "🔍 Checking for exposed API keys..."

# Common API key patterns
API_KEY_PATTERNS=(
    "sk-[a-zA-Z0-9]{32,}"                    # OpenAI
    "AIza[0-9A-Za-z_-]{35}"                  # Google API
    "AKIA[0-9A-Z]{16}"                       # AWS Access Key
    "ghp_[a-zA-Z0-9]{36}"                    # GitHub Personal Token
    "ghs_[a-zA-Z0-9]{36}"                    # GitHub Secret
    "stripe_[a-zA-Z0-9]{32,}"                # Stripe
    "pk_[a-zA-Z0-9]{32,}"                    # Various public keys
    "sk_[a-zA-Z0-9]{32,}"                    # Various secret keys
)

found_keys=false

for pattern in "${API_KEY_PATTERNS[@]}"; do
    if grep -r -E "$pattern" \
        --include="*.py" \
        --include="*.ts" \
        --include="*.tsx" \
        --include="*.js" \
        --include="*.json" \
        --include="Makefile" \
        --include="*.yml" \
        --include="*.yaml" \
        . \
        --exclude-dir=node_modules \
        --exclude-dir=.git \
        --exclude-dir=.venv \
        --exclude="*.example" \
        2>/dev/null | \
        grep -v "# Example" | \
        grep -v "// Example" | \
        grep -v "dummy" | \
        grep -v "test"; then
        echo "❌ Error: Exposed API key pattern found: $pattern"
        found_keys=true
    fi
done

if [ "$found_keys" = true ]; then
    echo "🚨 API keys detected! Remove them before committing."
    exit 1
fi

echo "✅ No API keys found"
exit 0
