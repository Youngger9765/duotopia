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

# 1. Check for Supabase credentials (including .github/)
echo -e "${BLUE}[1/8] Checking for Supabase credentials...${NC}"
if grep -r "Duotopia2025\|oenkjognodqhvujaooax" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.yml" \
    --include="*.yaml" \
    --include="Makefile" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v ".env" | \
    grep -v "security-audit.sh"; then
    report_error "Supabase credentials found in code!"
else
    report_success "No Supabase credentials in code"
fi

# 2. Check for OpenAI API keys (including .github/)
echo -e "${BLUE}[2/8] Checking for OpenAI API keys...${NC}"
if grep -r "sk-proj-[a-zA-Z0-9_-]{48,}" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.yml" \
    --include="*.yaml" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v ".env" | \
    grep -v "example" | \
    grep -v "security-audit.sh"; then
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
    --exclude="service-account-key.json" \
    --exclude="*-key.json" \
    --exclude="*-sa.json" \
    --exclude="*-credentials.json" \
    2>/dev/null; then
    report_error "Private key file found!"
else
    report_success "No private keys in repository"
fi

# 4. Check for AWS credentials (including .github/)
echo -e "${BLUE}[4/8] Checking for AWS credentials...${NC}"
if grep -r "AKIA[0-9A-Z]{16}\|aws_secret_access_key" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.yml" \
    --include="*.yaml" \
    --include="*.json" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v "example" | \
    grep -v "security-audit.sh"; then
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

# 8. Check for TapPay credentials (CRITICAL!)
echo -e "${BLUE}[8/11] Checking for TapPay credentials...${NC}"
tappay_issues=0

# Check for TapPay APP_KEY pattern (app_ + 60-70 chars)
if grep -r "app_[a-zA-Z0-9]{60,70}" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.md" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v "your-" | \
    grep -v "YOUR_" | \
    grep -v "PLACEHOLDER" | \
    grep -v "example" | \
    grep -v "REDACTED" | \
    grep -v "\\.\\.\\."; then
    report_error "TapPay APP_KEY pattern detected!"
    ((tappay_issues++))
fi

# Check for TapPay PARTNER_KEY pattern (partner_ + 60-70 chars)
if grep -r "partner_[a-zA-Z0-9]{60,70}" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.sh" \
    --include="*.md" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    2>/dev/null | \
    grep -v "your-" | \
    grep -v "YOUR_" | \
    grep -v "PLACEHOLDER" | \
    grep -v "example" | \
    grep -v "REDACTED" | \
    grep -v "\\.\\.\\."; then
    report_error "TapPay PARTNER_KEY pattern detected!"
    ((tappay_issues++))
fi

# Check for known leaked TapPay credentials (use pattern, not full value)
if grep -rE "app_4H0U1hnw[a-zA-Z0-9]{56}|partner_WiCZj1tZ[a-zA-Z0-9]{56}|partner_PHgswvYE[a-zA-Z0-9]{56}" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    --include="*.md" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=__pycache__ \
    --exclude="check-tappay-credentials.sh" \
    --exclude="security-audit.sh" \
    2>/dev/null | \
    grep -v "pattern" | \
    grep -v "REDACTED" | \
    grep -v "\\.\\.\\."; then
    report_error "BLOCKED! Previously leaked TapPay credentials pattern detected!"
    ((tappay_issues++))
fi

if [ "$tappay_issues" -eq 0 ]; then
    report_success "No TapPay credentials detected"
fi

# 9. Check for hardcoded MERCHANT_ID
echo -e "${BLUE}[9/11] Checking for TapPay MERCHANT_ID...${NC}"
if grep -r "tppf_duotopia_[a-zA-Z0-9_]\\+" \
    --include="*.py" \
    --include="*.ts" \
    --include="*.tsx" \
    --include="*.js" \
    . \
    --exclude-dir=node_modules \
    --exclude-dir=.git \
    --exclude-dir=tests \
    --exclude-dir=__tests__ \
    --exclude="*.md" \
    2>/dev/null | \
    grep -v "getenv" | \
    grep -v "import.meta.env" | \
    grep -v "example" | \
    grep -v "測試" | \
    grep -v "assert.*tappay_merchant_id"; then
    report_error "Hardcoded TapPay MERCHANT_ID found!"
else
    report_success "No hardcoded MERCHANT_ID"
fi

# 10. Check for service account keys
echo -e "${BLUE}[10/11] Checking for service account key files...${NC}"
if find . -type f \( -name "*-key.json" -o -name "*-sa.json" -o -name "*credentials.json" -o -name "service-account-key.json" \) \
    ! -path "*/node_modules/*" \
    ! -path "*/.git/*" \
    2>/dev/null | grep -v ".gitignore"; then
    report_error "Service account key files found in repository!"
else
    report_success "No service account key files"
fi

# 11. Check for TODO security items
echo -e "${BLUE}[11/11] Checking for security TODOs...${NC}"
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
