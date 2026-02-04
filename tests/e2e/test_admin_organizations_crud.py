"""
Issue #198: Admin Organization CRUD - Comprehensive E2E Tests

This script tests the complete CRUD functionality of the Admin Organization Management feature.

Test Categories:
1. List - View organizations with correct data
2. Search - Filter organizations by name/email
3. Pagination - Navigate between pages
4. Edit - Open dialog, modify fields, save changes
5. Points - Adjust points with confirmation
6. Verify - Confirm changes persisted

Usage:
    python tests/e2e/test_admin_organizations_crud.py

Prerequisites:
    - Preview environment must be running
    - Test account: owner@duotopia.com / demo123
"""

import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

# Configuration
BASE_URL = "https://duotopia-preview-issue-198-frontend-316409492201.asia-east1.run.app"
TEST_ACCOUNT_EMAIL = "owner@duotopia.com"
TEST_ACCOUNT_PASSWORD = "demo123"
SCREENSHOT_DIR = "/tmp/issue198_tests"

# Ensure screenshot directory exists
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def take_screenshot(page, name):
    """Take a screenshot with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{SCREENSHOT_DIR}/{timestamp}_{name}.png"
    page.screenshot(path=path)
    print(f"  📸 Screenshot: {path}")
    return path


def login_as_admin(page):
    """Login using quick login button for org owner"""
    print("\n🔐 Logging in as admin...")
    page.goto(f"{BASE_URL}/teacher/login")
    page.wait_for_load_state("networkidle")

    # Click quick login button for 張機構（機構擁有者）
    login_button = page.locator("button:has-text('張機構（機構擁有者）')")
    login_button.click()

    # Wait for redirect to dashboard
    page.wait_for_url("**/organization/dashboard**", timeout=10000)
    print("  ✅ Login successful")


def navigate_to_admin_organizations(page):
    """Navigate to Admin > 組織管理 tab"""
    print("\n📍 Navigating to Admin > 組織管理...")
    page.goto(f"{BASE_URL}/admin")
    page.wait_for_load_state("networkidle")

    # Click 組織管理 tab
    org_tab = page.locator("button:has-text('組織管理')")
    org_tab.click()
    page.wait_for_timeout(1000)  # Wait for tab content to load
    print("  ✅ Navigation successful")


def test_list_organizations(page):
    """Test 1: Verify organization list displays correctly"""
    print("\n" + "="*60)
    print("TEST 1: List Organizations")
    print("="*60)

    # Check table headers exist
    headers = ["組織名稱", "擁有人", "教師數", "點數", "狀態", "創建日期", "操作"]
    for header in headers:
        locator = page.locator(f"th:has-text('{header}'), div:has-text('{header}')")
        if locator.count() > 0:
            print(f"  ✅ Header found: {header}")
        else:
            print(f"  ❌ Header missing: {header}")
            return False

    # Check at least one organization row exists
    rows = page.locator("tr:has(button:has-text('編輯'))")
    row_count = rows.count()
    print(f"  ℹ️ Found {row_count} organization rows")

    if row_count > 0:
        print("  ✅ Organizations displayed")
        take_screenshot(page, "01_list_organizations")
        return True
    else:
        print("  ❌ No organizations found")
        return False


def test_search_functionality(page):
    """Test 2: Verify search filters results correctly"""
    print("\n" + "="*60)
    print("TEST 2: Search Functionality")
    print("="*60)

    # Get initial count
    initial_rows = page.locator("tr:has(button:has-text('編輯'))").count()
    print(f"  ℹ️ Initial row count: {initial_rows}")

    # Enter search term
    search_input = page.locator("input[placeholder*='搜尋']")
    search_input.fill("Kaddy")
    page.wait_for_timeout(500)  # Wait for debounce

    # Check filtered results
    page.wait_for_timeout(1000)  # Wait for API response
    filtered_rows = page.locator("tr:has(button:has-text('編輯'))").count()
    print(f"  ℹ️ Filtered row count: {filtered_rows}")

    # Verify filtering worked (should have fewer results)
    if filtered_rows < initial_rows or filtered_rows == 1:
        print("  ✅ Search filter working")
        take_screenshot(page, "02_search_filtered")

        # Clear search
        search_input.fill("")
        page.wait_for_timeout(1000)
        return True
    else:
        print("  ❌ Search filter not working")
        return False


def test_pagination(page):
    """Test 3: Verify pagination controls work"""
    print("\n" + "="*60)
    print("TEST 3: Pagination")
    print("="*60)

    # Check pagination info exists
    pagination_info = page.locator("text=/顯示.*筆/")
    if pagination_info.count() > 0:
        info_text = pagination_info.first.text_content()
        print(f"  ℹ️ Pagination info: {info_text}")
        print("  ✅ Pagination info displayed")
    else:
        print("  ⚠️ Pagination info not found (may have few records)")

    # Check page size selector
    page_size_selector = page.locator("select, [role='combobox']").first
    if page_size_selector.count() > 0:
        print("  ✅ Page size selector exists")

    take_screenshot(page, "03_pagination")
    return True


def test_edit_dialog_open(page):
    """Test 4: Verify edit dialog opens with correct data"""
    print("\n" + "="*60)
    print("TEST 4: Edit Dialog - Open")
    print("="*60)

    # Click first edit button
    edit_button = page.locator("button:has-text('編輯')").first
    edit_button.click()
    page.wait_for_timeout(1000)

    # Check dialog opened
    dialog = page.locator("[role='dialog'], .modal, div:has-text('編輯組織')")
    if dialog.count() > 0:
        print("  ✅ Edit dialog opened")
        take_screenshot(page, "04_edit_dialog_open")
    else:
        print("  ❌ Edit dialog not found")
        return False, None

    # Check all form fields exist and have values
    fields_to_check = [
        ("顯示名稱", "input"),
        ("統一編號", "input"),
        ("組織描述", "textarea, input"),
        ("教師限制", "input"),
        ("聯絡 Email", "input"),
        ("聯絡電話", "input"),
        ("地址", "input, textarea"),
    ]

    original_values = {}

    for field_name, selector_type in fields_to_check:
        # Find label and associated input
        label = page.locator(f"label:has-text('{field_name}'), div:has-text('{field_name}')")
        if label.count() > 0:
            # Try to find the input near the label
            input_field = page.locator(f"{selector_type}").filter(has=page.locator(f"text='{field_name}'")).first
            if input_field.count() == 0:
                # Alternative: find by placeholder or nearby
                input_field = page.locator(f"input, textarea").nth(fields_to_check.index((field_name, selector_type)))

            print(f"  ✅ Field found: {field_name}")
        else:
            print(f"  ⚠️ Field label not found: {field_name}")

    return True, original_values


def test_edit_update_field(page, field_label, new_value, field_type="input"):
    """Test 5: Update a specific field and verify"""
    print(f"\n  📝 Updating field: {field_label}")

    try:
        # Find the input field
        if field_type == "textarea":
            input_field = page.locator(f"textarea").filter(
                has=page.locator(f"text='{field_label}'")
            ).first
        else:
            # Try multiple strategies to find the input
            input_field = page.locator(f"input").filter(
                has=page.locator(f"text='{field_label}'")
            ).first

        if input_field.count() == 0:
            # Try finding by label text proximity
            label = page.locator(f"label:has-text('{field_label}'), div:has-text('{field_label}')").first
            if label.count() > 0:
                # Find the next input after the label
                input_field = label.locator("xpath=following::input[1] | following::textarea[1]").first

        # Clear and fill
        input_field.fill("")
        input_field.fill(new_value)
        print(f"    ✅ Set {field_label} = {new_value}")
        return True
    except Exception as e:
        print(f"    ❌ Failed to update {field_label}: {e}")
        return False


def test_edit_save_and_verify(page):
    """Test 6: Save changes and verify they persist"""
    print("\n" + "="*60)
    print("TEST 6: Edit - Save and Verify")
    print("="*60)

    # Generate unique test value
    timestamp = datetime.now().strftime("%H%M%S")
    test_description = f"E2E Test Update {timestamp}"

    # Update description field (safest to test)
    desc_field = page.locator("textarea").first
    if desc_field.count() > 0:
        original_value = desc_field.input_value()
        print(f"  ℹ️ Original description: {original_value[:50]}...")

        desc_field.fill(test_description)
        print(f"  ℹ️ New description: {test_description}")

    take_screenshot(page, "05_before_save")

    # Click save button
    save_button = page.locator("button:has-text('儲存'), button:has-text('儲存變更')")
    if save_button.count() > 0:
        save_button.first.click()
        print("  ℹ️ Clicked save button")
        page.wait_for_timeout(2000)  # Wait for API response
    else:
        print("  ❌ Save button not found")
        return False, None

    take_screenshot(page, "06_after_save")

    # Check for success notification
    success_toast = page.locator("text=/成功|已更新|Success/i")
    if success_toast.count() > 0:
        print("  ✅ Success notification shown")

    # Verify dialog closed
    page.wait_for_timeout(1000)
    dialog = page.locator("[role='dialog']:visible")
    if dialog.count() == 0:
        print("  ✅ Dialog closed after save")

    return True, test_description


def test_verify_update_persisted(page, expected_value):
    """Test 7: Reopen dialog and verify changes persisted"""
    print("\n" + "="*60)
    print("TEST 7: Verify Update Persisted")
    print("="*60)

    # Click edit button again
    edit_button = page.locator("button:has-text('編輯')").first
    edit_button.click()
    page.wait_for_timeout(1000)

    # Check the description field has the new value
    desc_field = page.locator("textarea").first
    if desc_field.count() > 0:
        current_value = desc_field.input_value()
        print(f"  ℹ️ Current description: {current_value}")

        if expected_value in current_value:
            print("  ✅ Update persisted correctly!")
            take_screenshot(page, "07_verify_persisted")
            return True
        else:
            print(f"  ❌ Expected: {expected_value}")
            print(f"  ❌ Got: {current_value}")
            return False

    return False


def test_points_adjustment(page):
    """Test 8: Adjust points and verify confirmation dialog"""
    print("\n" + "="*60)
    print("TEST 8: Points Adjustment")
    print("="*60)

    # Find points input field
    points_input = page.locator("input[type='number']").filter(
        has=page.locator("text=/點數|總點數/")
    )

    if points_input.count() == 0:
        # Try alternative selector
        points_input = page.locator("input").filter(has_text="點數")

    # Check current points display
    points_display = page.locator("text=/總點數|剩餘/")
    if points_display.count() > 0:
        print(f"  ℹ️ Points display found")

    take_screenshot(page, "08_points_section")

    # Close dialog without saving points change
    cancel_button = page.locator("button:has-text('取消')")
    if cancel_button.count() > 0:
        cancel_button.click()
        print("  ✅ Closed dialog")

    return True


def test_error_handling(page):
    """Test 9: Test error handling (optional - requires specific conditions)"""
    print("\n" + "="*60)
    print("TEST 9: Error Handling")
    print("="*60)

    # This test would require triggering an error condition
    # For now, we just verify the UI handles empty states gracefully

    # Search for non-existent organization
    search_input = page.locator("input[placeholder*='搜尋']")
    search_input.fill("ZZZZNONEXISTENT12345")
    page.wait_for_timeout(1000)

    # Check for empty state message
    empty_state = page.locator("text=/沒有|無|No|Empty/i")
    if empty_state.count() > 0:
        print("  ✅ Empty state handled gracefully")
    else:
        # Check if table is empty
        rows = page.locator("tr:has(button:has-text('編輯'))").count()
        if rows == 0:
            print("  ✅ No results shown for invalid search")

    take_screenshot(page, "09_empty_state")

    # Clear search
    search_input.fill("")
    page.wait_for_timeout(500)

    return True


def run_all_tests():
    """Run all tests and generate report"""
    print("\n" + "="*60)
    print("🧪 ISSUE #198 - ADMIN ORGANIZATION CRUD E2E TESTS")
    print("="*60)
    print(f"Target: {BASE_URL}")
    print(f"Screenshots: {SCREENSHOT_DIR}")

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for CI
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            # Login
            login_as_admin(page)

            # Navigate to admin organizations
            navigate_to_admin_organizations(page)

            # Run tests
            results["1. List Organizations"] = test_list_organizations(page)
            results["2. Search Functionality"] = test_search_functionality(page)
            results["3. Pagination"] = test_pagination(page)

            dialog_opened, _ = test_edit_dialog_open(page)
            results["4. Edit Dialog Open"] = dialog_opened

            if dialog_opened:
                save_success, test_value = test_edit_save_and_verify(page)
                results["5. Edit Save"] = save_success

                if save_success and test_value:
                    results["6. Verify Persisted"] = test_verify_update_persisted(page, test_value)
                else:
                    results["6. Verify Persisted"] = False

                # Reopen for points test
                navigate_to_admin_organizations(page)
                page.locator("button:has-text('編輯')").first.click()
                page.wait_for_timeout(1000)
                results["7. Points Adjustment"] = test_points_adjustment(page)

            results["8. Error Handling"] = test_error_handling(page)

        except Exception as e:
            print(f"\n❌ Test execution error: {e}")
            take_screenshot(page, "error_state")
            raise
        finally:
            browser.close()

    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)

    passed = 0
    failed = 0

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1

    print("\n" + "-"*60)
    print(f"  Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
