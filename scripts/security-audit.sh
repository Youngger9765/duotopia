#!/bin/bash

# Comprehensive security audit
echo "="
echo "🔒 SECURITY AUDIT STARTING..."
echo "="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Function to report issues
report_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
    ((errors++))
}

report_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
    ((warnings++))
}

report_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 1. Check for Supabase credentials
echo -e "${BLUE}[1/8] Checking for Supabase credentials...${NC}"
if grep -r "Duotopia2025\|oenkjognodqhvujaooax" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="Makefile" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v ".env"; then
    report_error "Supabase credentials found in code!"
else
    report_success "No Supabase credentials in code"
fi

# 2. Check for OpenAI API keys
echo -e "${BLUE}[2/8] Checking for OpenAI API keys...${NC}"
if grep -r "sk-proj-[a-zA-Z0-9_-]{48,}" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v ".env" | \
    grep -v "example"; then
    report_error "OpenAI API key found in code!"
else
    report_success "No OpenAI API keys in code"
fi

# 3. Check for private keys
echo -e "${BLUE}[3/8] Checking for private keys...${NC}"
if grep -r "BEGIN RSA PRIVATE KEY\|BEGIN PRIVATE KEY\|BEGIN EC PRIVATE KEY" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=scripts \
    --exclude="*.sh" \
    2>/dev/null; then
    report_error "Private key file found!"
else
    report_success "No private keys in repository"
fi

# 4. Check for AWS credentials
echo -e "${BLUE}[4/8] Checking for AWS credentials...${NC}"
if grep -r "AKIA[0-9A-Z]{16}\|aws_secret_access_key" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.json" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v "example"; then
    report_error "AWS credentials found!"
else
    report_success "No AWS credentials in code"
fi

# 5. Check for localhost URLs in production code
echo -e "${BLUE}[5/8] Checking for localhost URLs...${NC}"
localhost_count=$(grep -r "localhost:[0-9]\|127.0.0.1:[0-9]" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    frontend/src backend/routers \
    2>/dev/null | \
    grep -v "test" | \
    grep -v ".env" | \
    wc -l)

if [ "$localhost_count" -gt 0 ]; then
    report_warning "Found $localhost_count localhost references (use environment variables)"
else
    report_success "No hardcoded localhost URLs"
fi

# 6. Check for console.log with sensitive data
echo -e "${BLUE}[6/8] Checking for console.log with passwords...${NC}"
if grep -r "console.log.*password\|console.log.*secret\|console.log.*token" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    frontend/src \
    2>/dev/null | \
    grep -v "test"; then
    report_warning "console.log with potentially sensitive data"
else
    report_success "No console.log with sensitive data"
fi

# 7. Check Python logging
echo -e "${BLUE}[7/8] Checking Python logging...${NC}"
if grep -r "print.*password\|logger.*password\|print.*secret" \
    --include="*.py" \
    backend \
    2>/dev/null | \
    grep -v "test" | \
    grep -v "#"; then
    report_warning "Python logging with potentially sensitive data"
else
    report_success "No Python logging with sensitive data"
fi

# 8. Check for TODO security items
echo -e "${BLUE}[8/8] Checking for security TODOs...${NC}"
security_todos=$(grep -r "TODO.*security\|FIXME.*security\|XXX.*security\|HACK" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | wc -l)

if [ "$security_todos" -gt 0 ]; then
    report_warning "Found $security_todos security-related TODOs"
else
    report_success "No security TODOs"
fi

# Summary
echo ""
echo "="
echo "📊 SECURITY AUDIT SUMMARY"
echo "="

if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    echo -e "${GREEN}🎉 Perfect! No security issues found.${NC}"
    exit 0
elif [ "$errors" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Found $warnings warning(s) - review recommended${NC}"
    exit 0
else
    echo -e "${RED}🚨 Found $errors error(s) and $warnings warning(s)${NC}"
    echo -e "${RED}Fix these security issues before committing!${NC}"
    exit 1
fi
