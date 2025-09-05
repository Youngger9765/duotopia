#!/bin/bash

# 🔐 Secure Secret Management Script for Duotopia
# Purpose: Safely manage environment variables without exposing them
# Usage: ./scripts/manage-secrets.sh [command]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENV_FILES=(
    ".env.staging"
    "backend/.env.staging"
    ".env.production"
    "backend/.env.production"
)

# Function to check if file contains exposed secrets
check_file_for_secrets() {
    local file=$1
    echo -e "${BLUE}Checking $file for exposed secrets...${NC}"

    # Check for hardcoded passwords in non-env files
    if [[ ! "$file" =~ \.env ]]; then
        if grep -E "password\s*=\s*[\"'][^\"']+[\"']" "$file" 2>/dev/null | grep -v "your-" | grep -v "dummy"; then
            echo -e "${RED}❌ WARNING: Possible hardcoded password found in $file${NC}"
            return 1
        fi
    fi

    # Check for database URLs with passwords
    if grep -E "postgresql://[^:]+:[^@]+@[^/]+" "$file" 2>/dev/null | grep -v "localhost" | grep -v "dummy"; then
        echo -e "${RED}❌ WARNING: Database URL with password found in $file${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ $file appears clean${NC}"
    return 0
}

# Function to validate environment file
validate_env_file() {
    local file=$1

    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}⚠️  File $file does not exist${NC}"
        return 0
    fi

    echo -e "${BLUE}Validating $file...${NC}"

    # Check required variables
    local required_vars=(
        "DATABASE_URL"
        "JWT_SECRET"
    )

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$file"; then
            echo -e "${RED}❌ Missing required variable: $var${NC}"
            return 1
        fi
    done

    echo -e "${GREEN}✅ $file validated${NC}"
    return 0
}

# Function to rotate a specific secret
rotate_secret() {
    local secret_name=$1
    local env_file=$2

    echo -e "${YELLOW}Rotating $secret_name in $env_file${NC}"

    # Generate new secret
    local new_secret=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

    # Update in file
    if grep -q "^${secret_name}=" "$env_file"; then
        # macOS compatible sed
        sed -i '' "s/^${secret_name}=.*/${secret_name}=${new_secret}/" "$env_file"
        echo -e "${GREEN}✅ Rotated $secret_name${NC}"
    else
        echo -e "${RED}❌ $secret_name not found in $env_file${NC}"
    fi
}

# Function to check git history for exposed secrets
check_git_history() {
    echo -e "${BLUE}Checking git history for exposed secrets...${NC}"

    # Check recent commits for database URLs with passwords
    if git log -p -10 | grep -E "postgresql://[^:]+:[^@]+@" | grep -v "dummy" | grep -v "localhost"; then
        echo -e "${RED}❌ CRITICAL: Database credentials found in git history!${NC}"
        echo -e "${RED}   You must rotate these credentials immediately!${NC}"
        return 1
    fi

    echo -e "${GREEN}✅ No obvious secrets in recent git history${NC}"
    return 0
}

# Function to update GitHub secrets
update_github_secrets() {
    echo -e "${BLUE}Instructions to update GitHub secrets:${NC}"
    echo "1. Go to: https://github.com/Youngger9765/duotopia/settings/secrets/actions"
    echo "2. Update the following secrets:"
    echo "   - STAGING_DATABASE_URL"
    echo "   - STAGING_JWT_SECRET"
    echo "   - PRODUCTION_DATABASE_URL (if exists)"
    echo "   - PRODUCTION_JWT_SECRET (if exists)"
    echo ""
    echo -e "${YELLOW}⚠️  Never commit .env files to git!${NC}"
}

# Main command handler
case "${1:-help}" in
    check)
        echo -e "${BLUE}🔍 Running security check...${NC}"

        # Check all env files
        for file in "${ENV_FILES[@]}"; do
            if [ -f "$file" ]; then
                validate_env_file "$file"
            fi
        done

        # Check for exposed secrets in code
        echo -e "${BLUE}Checking codebase for exposed secrets...${NC}"
        check_file_for_secrets "Makefile"
        check_file_for_secrets "docker-compose.yml"

        # Check git history
        check_git_history
        ;;

    rotate-jwt)
        echo -e "${YELLOW}🔄 Rotating JWT secrets...${NC}"
        for file in "${ENV_FILES[@]}"; do
            if [ -f "$file" ]; then
                rotate_secret "JWT_SECRET" "$file"
            fi
        done
        echo -e "${GREEN}✅ JWT secrets rotated. Don't forget to update GitHub secrets!${NC}"
        update_github_secrets
        ;;

    validate)
        echo -e "${BLUE}✔️  Validating environment files...${NC}"
        for file in "${ENV_FILES[@]}"; do
            validate_env_file "$file"
        done
        ;;

    github-update)
        update_github_secrets
        ;;

    help|*)
        echo "🔐 Duotopia Secret Management Tool"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  check         - Check for exposed secrets in code and git"
        echo "  validate      - Validate environment files have required variables"
        echo "  rotate-jwt    - Rotate JWT secrets in all env files"
        echo "  github-update - Show instructions to update GitHub secrets"
        echo "  help          - Show this help message"
        echo ""
        echo "Security Best Practices:"
        echo "  ✅ Never commit .env files"
        echo "  ✅ Use environment variables for all secrets"
        echo "  ✅ Rotate credentials regularly"
        echo "  ✅ Use GitHub secrets for CI/CD"
        echo "  ✅ Run 'make test' before committing"
        ;;
esac
