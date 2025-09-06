#!/bin/bash

# Prevent .env files from being committed
echo "🔒 Checking for .env files..."

# List of .env files that should never be committed
ENV_FILES=(
    ".env"
    ".env.local"
    ".env.staging"
    ".env.production"
    "backend/.env"
    "backend/.env.staging"
    "backend/.env.production"
    "frontend/.env"
    "frontend/.env.local"
    "frontend/.env.staging"
    "frontend/.env.production"
)

found_env=false

for env_file in "${ENV_FILES[@]}"; do
    if git diff --cached --name-only | grep -q "^$env_file$"; then
        echo "❌ Error: Attempting to commit $env_file"
        echo "   .env files contain secrets and should NEVER be committed!"
        found_env=true
    fi
done

# Also check for any new .env files
if git diff --cached --name-only | grep -E "\.env(\.|$)" | grep -v "\.example"; then
    echo "❌ Error: Found .env file in staged changes"
    found_env=true
fi

if [ "$found_env" = true ]; then
    echo ""
    echo "🚨 SECURITY ALERT: .env files detected in commit!"
    echo "Remove them with: git reset HEAD <file>"
    echo ""
    echo "Make sure these are in .gitignore:"
    echo "  .env"
    echo "  .env.*"
    echo "  !.env.example"
    exit 1
fi

echo "✅ No .env files in commit"
exit 0
