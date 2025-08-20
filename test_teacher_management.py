#!/usr/bin/env python3
"""
E2E tests for teacher management pages - student, course, and classroom CRUD operations
Uses proper selectors following industry best practices
"""
import os
import sys
import time
from playwright.sync_api import sync_playwright, expect

# Test configuration
BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"
HEADLESS = True  # Set to False to see the browser

def test_student_management_crud(page):
    """Test student management page CRUD operations"""
    print("\n=== Testing Student Management ===")
    
    # Navigate to student management
    page.goto(f"{BASE_URL}/teacher/students")
    
    # Verify page loaded
    page.wait_for_selector("h2:text-is('學生管理')")
    
    # Wait for table to load with student data
    page.wait_for_selector("table tbody tr", timeout=10000)
    
    # Count initial students
    initial_count = page.locator("table tbody tr").count()
    print(f"Initial student count: {initial_count}")
    assert initial_count > 0, "No students found in the list"
    
    # Test search functionality
    print("Testing search...")
    search_input = page.locator("input[type='search']").or_(page.locator("input[placeholder*='搜尋']"))
    search_input.fill("陳小明")
    page.wait_for_timeout(500)  # Debounce delay
    
    # Verify search results
    search_count = page.locator("table tbody tr").count()
    assert search_count >= 1, "Search did not return expected results"
    
    # Clear search
    search_input.clear()
    page.wait_for_timeout(500)
    
    # Test CREATE - Add new student
    print("Testing CREATE...")
    # Click add button - typically has plus icon or "新增" text
    page.locator("button:has-text('新增學生')").or_(page.locator("button:has(svg[class*='Plus'])")).click()
    
    # Fill in form using proper form semantics
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    
    modal.locator("input[type='text']").first.fill("測試學生")  # Name field is usually first
    modal.locator("input[type='email']").fill("test.student@duotopia.com")
    
    # Parent info - look for labels
    modal.locator("input").locator("visible=true").filter(has_text="家長").first.fill("test.parent@example.com")
    modal.locator("input[type='tel']").or_(modal.locator("input[inputmode='tel']")).fill("0912345678")
    
    # Birth date - use proper date inputs or selects
    if modal.locator("input[type='date']").count() > 0:
        modal.locator("input[type='date']").fill("2009-08-28")
    else:
        # Fallback to selects
        modal.locator("select").nth(0).select_option("2009")  # Year
        modal.locator("select").nth(1).select_option("8")     # Month
        modal.locator("select").nth(2).select_option("28")    # Day
    
    # Submit form
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('新增')")).click()
    
    # Wait for success indication
    page.wait_for_selector(".toast-success, [role='alert'], .notification", timeout=5000)
    
    # Verify student was added
    page.wait_for_timeout(1000)
    new_count = page.locator("table tbody tr").count()
    assert new_count == initial_count + 1, f"Student count should be {initial_count + 1}, but got {new_count}"
    
    # Test UPDATE - Edit student
    print("Testing UPDATE...")
    # Find the test student row and click edit button
    student_row = page.locator("tr:has-text('測試學生')").first
    student_row.locator("button[aria-label*='編輯'], button:has(svg[class*='Edit'])").click()
    
    # Update student name in modal
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    name_input = modal.locator("input[type='text']").first
    name_input.clear()
    name_input.fill("更新測試學生")
    
    # Save changes
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('儲存')")).click()
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify update
    page.wait_for_selector("tr:has-text('更新測試學生')")
    
    # Test DELETE
    print("Testing DELETE...")
    student_row = page.locator("tr:has-text('更新測試學生')").first
    student_row.locator("button[aria-label*='刪除'], button:has(svg[class*='Trash'])").click()
    
    # Confirm deletion in confirmation dialog
    confirm_dialog = page.locator("[role='alertdialog']").or_(page.locator(".confirm-dialog"))
    confirm_dialog.locator("button:has-text('確定'), button:has-text('刪除')").click()
    
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify deletion
    page.wait_for_timeout(1000)
    final_count = page.locator("table tbody tr").count()
    assert final_count == initial_count, f"Student count should be back to {initial_count}, but got {final_count}"
    
    print("✅ Student Management CRUD tests passed!")


def test_course_management_crud(page):
    """Test course management page CRUD operations"""
    print("\n=== Testing Course Management ===")
    
    # Navigate to course management
    page.goto(f"{BASE_URL}/teacher/courses")
    
    # Verify page loaded
    page.wait_for_selector("h2:text-is('課程管理')")
    
    # Wait for course cards/list to load
    page.wait_for_selector("article, .card, [role='article']", timeout=10000)
    
    # Count initial courses
    course_selector = "article, .card, [role='article']"
    initial_count = page.locator(course_selector).count()
    print(f"Initial course count: {initial_count}")
    assert initial_count > 0, "No courses found"
    
    # Test CREATE - Add new course
    print("Testing CREATE...")
    page.locator("button:has-text('新增課程')").or_(page.locator("button:has(svg[class*='Plus'])")).click()
    
    # Fill in form
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    
    # Course title - usually first input
    modal.locator("input[type='text']").first.fill("測試課程")
    
    # Description - textarea
    modal.locator("textarea").fill("這是一個測試課程描述")
    
    # Difficulty level - select or radio group
    if modal.locator("select").count() > 0:
        modal.locator("select").first.select_option("A1")
    else:
        modal.locator("input[type='radio'][value='A1']").click()
    
    # Submit form
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('新增')")).click()
    
    # Wait for success
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify course was added
    page.wait_for_timeout(1000)
    new_count = page.locator(course_selector).count()
    assert new_count == initial_count + 1, f"Course count should be {initial_count + 1}, but got {new_count}"
    
    # Test UPDATE - Edit course
    print("Testing UPDATE...")
    # Find test course and click edit
    test_course = page.locator(f"{course_selector}:has-text('測試課程')").first
    test_course.locator("button[aria-label*='編輯'], button:has(svg[class*='Edit'])").click()
    
    # Update course name
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    title_input = modal.locator("input[type='text']").first
    title_input.clear()
    title_input.fill("更新測試課程")
    
    # Save changes
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('儲存')")).click()
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify update
    page.wait_for_selector(f"{course_selector}:has-text('更新測試課程')")
    
    # Test DELETE
    print("Testing DELETE...")
    test_course = page.locator(f"{course_selector}:has-text('更新測試課程')").first
    test_course.locator("button[aria-label*='刪除'], button:has(svg[class*='Trash'])").click()
    
    # Confirm deletion
    confirm_dialog = page.locator("[role='alertdialog']").or_(page.locator(".confirm-dialog"))
    confirm_dialog.locator("button:has-text('確定'), button:has-text('刪除')").click()
    
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify deletion
    page.wait_for_timeout(1000)
    final_count = page.locator(course_selector).count()
    assert final_count == initial_count, f"Course count should be back to {initial_count}, but got {final_count}"
    
    print("✅ Course Management CRUD tests passed!")


def test_classroom_management_crud(page):
    """Test classroom management page CRUD operations"""
    print("\n=== Testing Classroom Management ===")
    
    # Navigate to classroom management
    page.goto(f"{BASE_URL}/teacher/classrooms")
    
    # Verify page loaded
    page.wait_for_selector("h2:text-is('教室管理')")
    
    # Wait for classroom list to load
    # Classrooms are typically in a list or grid layout
    classroom_selector = "[role='listitem'], article, .classroom-item"
    page.wait_for_selector(classroom_selector, timeout=10000)
    
    # Count initial classrooms
    initial_count = page.locator(classroom_selector).count()
    print(f"Initial classroom count: {initial_count}")
    assert initial_count > 0, "No classrooms found"
    
    # Test CREATE - Add new classroom
    print("Testing CREATE...")
    page.locator("button:has-text('新增教室')").or_(page.locator("button:has(svg[class*='Plus'])")).click()
    
    # Fill in form
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    
    # Select school - first select is usually school
    school_select = modal.locator("select").first
    school_select.select_option(index=1)  # Select first available school
    
    # Classroom name
    modal.locator("input[type='text']").nth(0).fill("測試教室")
    
    # Grade level - usually second select
    grade_select = modal.locator("select").nth(1)
    grade_select.select_option("6")
    
    # Submit form
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('新增')")).click()
    
    # Wait for success
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify classroom was added
    page.wait_for_timeout(1000)
    new_count = page.locator(classroom_selector).count()
    assert new_count == initial_count + 1, f"Classroom count should be {initial_count + 1}, but got {new_count}"
    
    # Test UPDATE - Edit classroom
    print("Testing UPDATE...")
    # Find test classroom and click edit
    test_classroom = page.locator(f"{classroom_selector}:has-text('測試教室')").first
    test_classroom.locator("button[aria-label*='編輯'], button:has(svg[class*='Edit'])").click()
    
    # Update classroom name
    modal = page.locator("div[role='dialog']").or_(page.locator(".modal, .dialog"))
    name_input = modal.locator("input[type='text']").first
    name_input.clear()
    name_input.fill("更新測試教室")
    
    # Save changes
    modal.locator("button[type='submit']").or_(modal.locator("button:has-text('儲存')")).click()
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify update
    page.wait_for_selector(f"{classroom_selector}:has-text('更新測試教室')")
    
    # Test DELETE
    print("Testing DELETE...")
    test_classroom = page.locator(f"{classroom_selector}:has-text('更新測試教室')").first
    test_classroom.locator("button[aria-label*='刪除'], button:has(svg[class*='Trash'])").click()
    
    # Confirm deletion
    confirm_dialog = page.locator("[role='alertdialog']").or_(page.locator(".confirm-dialog"))
    confirm_dialog.locator("button:has-text('確定'), button:has-text('刪除')").click()
    
    page.wait_for_selector(".toast-success, [role='alert']", timeout=5000)
    
    # Verify deletion
    page.wait_for_timeout(1000)
    final_count = page.locator(classroom_selector).count()
    assert final_count == initial_count, f"Classroom count should be back to {initial_count}, but got {final_count}"
    
    print("✅ Classroom Management CRUD tests passed!")


def main():
    """Run all E2E tests"""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            # Set viewport for consistent testing
            viewport={'width': 1280, 'height': 720},
            # Set locale for consistent date/time formats
            locale='zh-TW'
        )
        page = context.new_page()
        
        try:
            # Login first
            print("Logging in...")
            page.goto(BASE_URL)
            
            # Use proper form submission for login
            # Fill demo credentials
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            
            # Submit login form
            page.locator("form").locator("button[type='submit']").click()
            
            # Wait for redirect to dashboard
            page.wait_for_url("**/teacher", timeout=10000)
            print("Login successful!")
            
            # Run all tests
            test_student_management_crud(page)
            test_course_management_crud(page)
            test_classroom_management_crud(page)
            
            print("\n🎉 All E2E tests passed successfully!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            # Take screenshot on failure
            page.screenshot(path="test_failure.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()