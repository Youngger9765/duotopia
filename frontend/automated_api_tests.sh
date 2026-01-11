#!/bin/bash

# Automated API Tests for Organization Portal Separation
# Date: 2026-01-01
# Purpose: Verify backend APIs work correctly before manual UI testing

set -e

BASE_URL="http://localhost:8000"
RESULTS_FILE="api_test_results.txt"

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Organization Portal API Testing"
echo "========================================"
echo ""

# Store tokens
ORG_OWNER_TOKEN=""
ORG_ADMIN_TOKEN=""
SCHOOL_ADMIN_TOKEN=""
TEACHER_TOKEN=""

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Function to log test result
log_test() {
    local test_name=$1
    local status=$2
    local details=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    if [ "$status" == "PASS" ]; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo -e "${GREEN}✓ PASS${NC} - $test_name"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo -e "${RED}✗ FAIL${NC} - $test_name"
    fi

    if [ -n "$details" ]; then
        echo "   Details: $details"
    fi
    echo ""
}

# Function to extract JSON field
extract_json() {
    echo "$1" | python3 -c "import sys, json; print(json.load(sys.stdin)$2)" 2>/dev/null || echo ""
}

echo "========================================="
echo "Stage 1: Authentication Tests"
echo "========================================="
echo ""

# Test 1.1: Login as org_owner
echo "Test 1.1: Login as org_owner (owner@duotopia.com)"
response=$(curl -s -X POST "${BASE_URL}/api/auth/teacher/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"owner@duotopia.com","password":"owner123"}')

ORG_OWNER_TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$ORG_OWNER_TOKEN" ]; then
    user_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['name'])" 2>/dev/null || echo "")
    log_test "Login as org_owner" "PASS" "Token received, User: $user_name"
else
    log_test "Login as org_owner" "FAIL" "No token received"
fi

# Test 1.2: Login as org_admin
echo "Test 1.2: Login as org_admin (orgadmin@duotopia.com)"
response=$(curl -s -X POST "${BASE_URL}/api/auth/teacher/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"orgadmin@duotopia.com","password":"orgadmin123"}')

ORG_ADMIN_TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$ORG_ADMIN_TOKEN" ]; then
    user_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['name'])" 2>/dev/null || echo "")
    log_test "Login as org_admin" "PASS" "Token received, User: $user_name"
else
    log_test "Login as org_admin" "FAIL" "No token received"
fi

# Test 1.3: Login as school_admin
echo "Test 1.3: Login as school_admin (schooladmin@duotopia.com)"
response=$(curl -s -X POST "${BASE_URL}/api/auth/teacher/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"schooladmin@duotopia.com","password":"schooladmin123"}')

SCHOOL_ADMIN_TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$SCHOOL_ADMIN_TOKEN" ]; then
    user_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['name'])" 2>/dev/null || echo "")
    log_test "Login as school_admin" "PASS" "Token received, User: $user_name"
else
    log_test "Login as school_admin" "FAIL" "No token received"
fi

# Test 1.4: Login as teacher
echo "Test 1.4: Login as teacher (orgteacher@duotopia.com)"
response=$(curl -s -X POST "${BASE_URL}/api/auth/teacher/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"orgteacher@duotopia.com","password":"orgteacher123"}')

TEACHER_TOKEN=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ -n "$TEACHER_TOKEN" ]; then
    user_name=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['user']['name'])" 2>/dev/null || echo "")
    log_test "Login as teacher" "PASS" "Token received, User: $user_name"
else
    log_test "Login as teacher" "FAIL" "No token received"
fi

echo "========================================="
echo "Stage 2: Organization API Tests"
echo "========================================="
echo ""

# Test 2.1: org_owner can list organizations
echo "Test 2.1: org_owner list organizations"
if [ -n "$ORG_OWNER_TOKEN" ]; then
    response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/organizations" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    if [ "$http_code" == "200" ]; then
        org_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        log_test "org_owner list organizations" "PASS" "HTTP 200, Organizations: $org_count"
    else
        log_test "org_owner list organizations" "FAIL" "HTTP $http_code"
    fi
else
    log_test "org_owner list organizations" "FAIL" "No token available"
fi

# Test 2.2: org_owner can get roles
echo "Test 2.2: org_owner get roles"
if [ -n "$ORG_OWNER_TOKEN" ]; then
    response=$(curl -s -X GET "${BASE_URL}/api/v1/teachers/me/roles" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/teachers/me/roles" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    if [ "$http_code" == "200" ]; then
        roles=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print([r['role'] for r in data])" 2>/dev/null || echo "[]")
        log_test "org_owner get roles" "PASS" "HTTP 200, Roles: $roles"
    else
        log_test "org_owner get roles" "FAIL" "HTTP $http_code"
    fi
else
    log_test "org_owner get roles" "FAIL" "No token available"
fi

# Test 2.3: teacher CANNOT list organizations (should get empty or 403)
echo "Test 2.3: Pure teacher cannot list organizations"
if [ -n "$TEACHER_TOKEN" ]; then
    response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations" \
        -H "Authorization: Bearer $TEACHER_TOKEN")

    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/organizations" \
        -H "Authorization: Bearer $TEACHER_TOKEN")

    if [ "$http_code" == "200" ]; then
        org_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        if [ "$org_count" == "0" ]; then
            log_test "Teacher blocked from organizations" "PASS" "HTTP 200 with empty list"
        else
            log_test "Teacher blocked from organizations" "FAIL" "Teacher can see $org_count organizations (should be 0)"
        fi
    elif [ "$http_code" == "403" ]; then
        log_test "Teacher blocked from organizations" "PASS" "HTTP 403 Forbidden (correct)"
    else
        log_test "Teacher blocked from organizations" "FAIL" "Unexpected HTTP $http_code"
    fi
else
    log_test "Teacher blocked from organizations" "FAIL" "No token available"
fi

echo "========================================="
echo "Stage 3: Schools API Tests"
echo "========================================="
echo ""

# First, get organization ID for org_owner
ORG_ID=""
if [ -n "$ORG_OWNER_TOKEN" ]; then
    response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")
    ORG_ID=$(echo "$response" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data[0]['id'] if len(data) > 0 else '')" 2>/dev/null || echo "")
fi

# Test 3.1: org_owner can list schools
echo "Test 3.1: org_owner list schools"
if [ -n "$ORG_OWNER_TOKEN" ] && [ -n "$ORG_ID" ]; then
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/schools" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    if [ "$http_code" == "200" ]; then
        response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/schools" \
            -H "Authorization: Bearer $ORG_OWNER_TOKEN")
        school_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        log_test "org_owner list schools" "PASS" "HTTP 200, Schools: $school_count"
    else
        log_test "org_owner list schools" "FAIL" "HTTP $http_code"
    fi
else
    log_test "org_owner list schools" "FAIL" "No token or org_id available"
fi

# Test 3.2: teacher CANNOT list schools
echo "Test 3.2: Teacher cannot list schools"
if [ -n "$TEACHER_TOKEN" ] && [ -n "$ORG_ID" ]; then
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/schools" \
        -H "Authorization: Bearer $TEACHER_TOKEN")

    if [ "$http_code" == "403" ] || [ "$http_code" == "401" ]; then
        log_test "Teacher blocked from schools" "PASS" "HTTP $http_code (access denied)"
    elif [ "$http_code" == "200" ]; then
        response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/schools" \
            -H "Authorization: Bearer $TEACHER_TOKEN")
        school_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        if [ "$school_count" == "0" ]; then
            log_test "Teacher blocked from schools" "PASS" "HTTP 200 with empty list"
        else
            log_test "Teacher blocked from schools" "FAIL" "Teacher can see $school_count schools"
        fi
    else
        log_test "Teacher blocked from schools" "FAIL" "Unexpected HTTP $http_code"
    fi
else
    log_test "Teacher blocked from schools" "FAIL" "No token or org_id available"
fi

echo "========================================="
echo "Stage 4: Teachers API Tests"
echo "========================================="
echo ""

# Test 4.1: org_owner can list teachers in organization
echo "Test 4.1: org_owner list teachers"
if [ -n "$ORG_OWNER_TOKEN" ] && [ -n "$ORG_ID" ]; then
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/teachers" \
        -H "Authorization: Bearer $ORG_OWNER_TOKEN")

    if [ "$http_code" == "200" ]; then
        response=$(curl -s -X GET "${BASE_URL}/api/v1/organizations/${ORG_ID}/teachers" \
            -H "Authorization: Bearer $ORG_OWNER_TOKEN")
        teacher_count=$(echo "$response" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
        log_test "org_owner list teachers" "PASS" "HTTP 200, Teachers: $teacher_count"
    else
        log_test "org_owner list teachers" "FAIL" "HTTP $http_code"
    fi
else
    log_test "org_owner list teachers" "FAIL" "No token or org_id available"
fi

echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed! Backend is ready for UI testing.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please fix issues before UI testing.${NC}"
    exit 1
fi
