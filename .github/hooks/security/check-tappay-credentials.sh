#!/bin/bash
# 🔥 超嚴格 TapPay Credentials 檢查
# 絕對不允許任何 TapPay credentials 被 commit！

set -e

echo "🔍 檢查 TapPay credentials..."

# 顏色定義
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FOUND_ISSUES=0

# 檢查所有即將 commit 的檔案（排除 security hooks 自身）
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -v "security/check-tappay-credentials.sh" | grep -v "security/security-audit.sh")

if [ -z "$FILES" ]; then
    echo "✅ No files to check"
    exit 0
fi

# ============================================
# 1. 檢查 TapPay APP_KEY 模式
# ============================================
echo "  Checking for TapPay APP_KEY patterns..."

# APP_KEY 的模式: app_ 開頭 + 64 個字元
if echo "$FILES" | xargs git diff --cached | grep -E "app_[a-zA-Z0-9]{60,70}" | grep -v "your-" | grep -v "YOUR_" | grep -v "PLACEHOLDER" | grep -v "example" | grep -v "check-tappay-credentials.sh" | grep -v "security-audit.sh" | grep -v "BLACKLIST"; then
    echo -e "${RED}❌ TapPay APP_KEY detected!${NC}"
    echo -e "${YELLOW}Pattern: app_XXXX... (64+ chars)${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
fi

# ============================================
# 2. 檢查 TapPay PARTNER_KEY 模式
# ============================================
echo "  Checking for TapPay PARTNER_KEY patterns..."

# PARTNER_KEY 的模式: partner_ 開頭 + 64 個字元
if echo "$FILES" | xargs git diff --cached | grep -E "partner_[a-zA-Z0-9]{60,70}" | grep -v "your-" | grep -v "YOUR_" | grep -v "PLACEHOLDER" | grep -v "example" | grep -v "check-tappay-credentials.sh" | grep -v "security-audit.sh" | grep -v "BLACKLIST"; then
    echo -e "${RED}❌ TapPay PARTNER_KEY detected!${NC}"
    echo -e "${YELLOW}Pattern: partner_XXXX... (64+ chars)${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
fi

# ============================================
# 3. 檢查 TapPay MERCHANT_ID 模式
# ============================================
echo "  Checking for TapPay MERCHANT_ID patterns..."

# MERCHANT_ID 的模式: tppf_ 開頭
if echo "$FILES" | xargs git diff --cached | grep -E "tppf_[a-zA-Z0-9_]+" | grep -v "your-" | grep -v "YOUR_" | grep -v "PLACEHOLDER" | grep -v "example" | grep -v "測試" | grep -v "test" | grep -v "check-tappay-credentials.sh" | grep -v "security-audit.sh" | grep -v "BLACKLIST" | grep -v "tppf_xxx" | grep -v "tppf_duotopia_\*\*\*"; then
    echo -e "${RED}❌ TapPay MERCHANT_ID detected!${NC}"
    echo -e "${YELLOW}Pattern: tppf_XXXX...${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
fi

# ============================================
# 4. 檢查已知的洩漏 credentials（黑名單）
# ============================================
echo "  Checking against known leaked credentials blacklist..."

# 檢查已知洩漏的 pattern（不直接存 credential，用 hash 比對）
# SHA256 hash of leaked credentials
BLACKLIST_HASHES=(
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # Placeholder - 實際不用
)

# 直接檢查 pattern，不存實際值
if echo "$FILES" | xargs git diff --cached | grep -E "app_4H0U1hnw[a-zA-Z0-9]{56}" | grep -v "check-tappay-credentials.sh" > /dev/null; then
    echo -e "${RED}❌ BLOCKED! Known leaked APP_KEY pattern detected!${NC}"
    echo -e "${YELLOW}This APP_KEY was previously leaked and MUST NOT be committed!${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
fi

if echo "$FILES" | xargs git diff --cached | grep -E "partner_WiCZj1tZ[a-zA-Z0-9]{56}|partner_PHgswvYE[a-zA-Z0-9]{56}" | grep -v "check-tappay-credentials.sh" > /dev/null; then
    echo -e "${RED}❌ BLOCKED! Known leaked PARTNER_KEY pattern detected!${NC}"
    echo -e "${YELLOW}This PARTNER_KEY was previously leaked and MUST NOT be committed!${NC}"
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
fi

# ============================================
# 5. 檢查環境變數賦值（硬編碼檢查）
# ============================================
echo "  Checking for hardcoded TapPay environment variables..."

# 檢查 TAPPAY_* 環境變數的硬編碼賦值
TAPPAY_VARS=(
    "TAPPAY_APP_KEY"
    "TAPPAY_PARTNER_KEY"
    "TAPPAY_MERCHANT_ID"
    "TAPPAY_SANDBOX_APP_KEY"
    "TAPPAY_SANDBOX_PARTNER_KEY"
    "TAPPAY_SANDBOX_MERCHANT_ID"
    "TAPPAY_PRODUCTION_APP_KEY"
    "TAPPAY_PRODUCTION_PARTNER_KEY"
    "TAPPAY_PRODUCTION_MERCHANT_ID"
    "VITE_TAPPAY_APP_KEY"
    "VITE_TAPPAY_SANDBOX_APP_KEY"
    "VITE_TAPPAY_PRODUCTION_APP_KEY"
)

for var in "${TAPPAY_VARS[@]}"; do
    # 檢查是否有硬編碼的環境變數賦值
    if echo "$FILES" | xargs git diff --cached | grep -E "${var}\\s*=\\s*[\"'][a-zA-Z0-9_]{20,}[\"']" | grep -v "your-" | grep -v "YOUR_" | grep -v "getenv" | grep -v "import.meta.env" | grep -v "real_value" | grep -v "actual_value"; then
        echo -e "${RED}❌ Hardcoded ${var} detected!${NC}"
        echo -e "${YELLOW}Use os.getenv('${var}') or import.meta.env.${var} instead!${NC}"
        FOUND_ISSUES=$((FOUND_ISSUES + 1))
    fi
done

# ============================================
# 6. 檢查文檔中的 credentials（除非明確標記為 REDACTED）
# ============================================
echo "  Checking documentation files for credentials..."

for file in $FILES; do
    if [[ "$file" == *.md ]] || [[ "$file" == *.txt ]]; then
        # 檢查文檔中是否有實際的 TapPay credentials
        if git diff --cached "$file" | grep -E "(app_[a-zA-Z0-9]{60,}|partner_[a-zA-Z0-9]{60,})" | grep -v "REDACTED" | grep -v "REMOVED" | grep -v "\\*\\*\\*" | grep -v "\\.\\.\\."; then
            echo -e "${RED}❌ TapPay credentials found in documentation: $file${NC}"
            echo -e "${YELLOW}Redact credentials in docs! Use: app_XXXX... or ***REDACTED***${NC}"
            FOUND_ISSUES=$((FOUND_ISSUES + 1))
        fi
    fi
done

# ============================================
# 7. 檢查測試檔案中的硬編碼
# ============================================
echo "  Checking test files for hardcoded credentials..."

for file in $FILES; do
    if [[ "$file" == *test*.py ]] || [[ "$file" == *test*.ts ]]; then
        # 測試檔案不應該硬編碼實際的 credentials
        if git diff --cached "$file" | grep -E "(app_[a-zA-Z0-9]{60,}|partner_[a-zA-Z0-9]{60,})" | grep -v "mock" | grep -v "fake" | grep -v "test_" | grep -v "settings\\."; then
            echo -e "${RED}❌ Real credentials in test file: $file${NC}"
            echo -e "${YELLOW}Use mock values or read from settings/environment!${NC}"
            FOUND_ISSUES=$((FOUND_ISSUES + 1))
        fi
    fi
done

# ============================================
# 最終結果
# ============================================
if [ $FOUND_ISSUES -gt 0 ]; then
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  🚨 COMMIT BLOCKED - TapPay Credentials Detected!        ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Found $FOUND_ISSUES security issue(s)${NC}"
    echo ""
    echo "📋 What to do:"
    echo "  1. Remove all hardcoded TapPay credentials"
    echo "  2. Use environment variables instead:"
    echo "     - Backend: os.getenv('TAPPAY_APP_KEY')"
    echo "     - Frontend: import.meta.env.VITE_TAPPAY_APP_KEY"
    echo "  3. Add credentials to .env files (gitignored)"
    echo "  4. For docs, redact: app_XXXX... or ***REDACTED***"
    echo ""
    echo "🔒 Security Policy:"
    echo "  - ALL TapPay credentials MUST be in environment variables"
    echo "  - NO credentials in code, docs, or test files"
    echo "  - Previously leaked credentials are PERMANENTLY BLOCKED"
    echo ""
    exit 1
fi

echo "✅ TapPay credentials check passed"
exit 0
