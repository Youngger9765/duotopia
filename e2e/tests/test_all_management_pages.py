#!/usr/bin/env python3
"""
Complete E2E tests for all teacher management pages
Tests CRUD operations and data display for students, courses, and classrooms
"""
import time
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"
HEADLESS = True  # Set to False to see browser

class TestHelpers:
    """Helper functions for common test operations"""
    
    @staticmethod
    def login(page):
        """Login as teacher"""
        print("Logging in...")
        page.goto(f"{BASE_URL}/login")
        page.wait_for_load_state("domcontentloaded")
        
        # Fill credentials
        page.locator("input[type='email']").fill(TEACHER_EMAIL)
        page.locator("input[type='password']").fill(TEACHER_PASSWORD)
        
        # Submit
        page.locator("button[type='submit']").click()
        
        # Wait for redirect
        page.wait_for_url("**/teacher", timeout=10000)
        print("✓ Login successful")
    
    @staticmethod
    def take_screenshot_on_failure(page, test_name):
        """Take screenshot when test fails"""
        filename = f"e2e_failure_{test_name}_{int(time.time())}.png"
        page.screenshot(path=filename)
        print(f"Screenshot saved: {filename}")


def test_student_management(page):
    """Test student management page"""
    print("\n=== Testing Student Management ===")
    
    # Navigate to students page
    page.goto(f"{BASE_URL}/teacher/students")
    page.wait_for_selector("h2:has-text('學生管理')")
    
    # 1. Check data is displayed
    print("1. Checking student data display...")
    # Wait for student items to load
    page.wait_for_selector(".bg-white.rounded-lg.shadow", timeout=10000)
    student_items = page.locator(".bg-white.rounded-lg.shadow").all()
    initial_count = len(student_items)
    print(f"   Found {initial_count} students")
    assert initial_count > 0, "No students found!"
    
    # 2. Test search
    print("2. Testing search functionality...")
    search_input = page.locator("input[placeholder*='搜尋']")
    search_input.fill("陳小明")
    page.wait_for_timeout(500)  # Wait for search debounce
    
    filtered_items = page.locator(".bg-white.rounded-lg.shadow").all()
    assert len(filtered_items) >= 1, "Search should return at least one result"
    print(f"   Search returned {len(filtered_items)} results")
    
    # Clear search
    search_input.clear()
    page.wait_for_timeout(500)
    
    # 3. Test CREATE
    print("3. Testing CREATE student...")
    page.click("button:has-text('新增學生')")
    page.wait_for_selector("[role='dialog'], .modal, .fixed.inset-0")
    
    # Fill form - match actual form structure
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    
    # Student name - first input field
    modal.locator("input").nth(0).clear()
    modal.locator("input").nth(0).fill("測試學生E2E")
    
    # Email - placeholder text is "student@example.com"
    modal.locator("input[placeholder='student@example.com']").clear()
    modal.locator("input[placeholder='student@example.com']").fill("e2e.test@duotopia.com")
    
    # Birth date - placeholder is "YYYYMMDD"
    modal.locator("input[placeholder='YYYYMMDD']").clear()
    modal.locator("input[placeholder='YYYYMMDD']").fill("20090828")
    
    # Parent email
    modal.locator("input[placeholder='parent@example.com']").clear()
    modal.locator("input[placeholder='parent@example.com']").fill("parent.e2e@example.com")
    
    # Parent phone
    modal.locator("input[placeholder='0912345678']").clear()
    modal.locator("input[placeholder='0912345678']").fill("0912345678")
    
    # Submit
    modal.locator("button:has-text('新增')").click()
    
    # Wait for success
    page.wait_for_selector("text=學生已新增", timeout=5000)
    print("   ✓ Student created successfully")
    
    # 4. Test UPDATE
    print("4. Testing UPDATE student...")
    page.wait_for_timeout(1000)
    
    # Find test student
    test_student = page.locator(".bg-white.rounded-lg.shadow:has-text('測試學生E2E')").first
    test_student.locator("button[aria-label*='編輯'], button:has(svg.lucide-edit)").click()
    
    # Update name
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    name_input = modal.locator("input[placeholder*='學生姓名']")
    name_input.clear()
    name_input.fill("更新測試學生E2E")
    
    # Submit
    modal.locator("button:has-text('儲存')").click()
    page.wait_for_selector("text=學生資料已更新", timeout=5000)
    print("   ✓ Student updated successfully")
    
    # 5. Test DELETE
    print("5. Testing DELETE student...")
    page.wait_for_timeout(1000)
    
    # Find updated student
    test_student = page.locator(".bg-white.rounded-lg.shadow:has-text('更新測試學生E2E')").first
    test_student.locator("button[aria-label*='刪除'], button:has(svg.lucide-trash)").click()
    
    # Confirm
    page.click("button:has-text('確定')")
    page.wait_for_selector("text=學生已刪除", timeout=5000)
    print("   ✓ Student deleted successfully")
    
    print("✅ Student Management tests passed!")


def test_course_management(page):
    """Test course management page"""
    print("\n=== Testing Course Management ===")
    
    # Navigate to courses page
    page.goto(f"{BASE_URL}/teacher/courses")
    page.wait_for_selector("h2:has-text('課程管理')")
    
    # 1. Check data is displayed
    print("1. Checking course data display...")
    page.wait_for_selector(".bg-white.rounded-lg.shadow", timeout=10000)
    course_items = page.locator(".bg-white.rounded-lg.shadow").all()
    initial_count = len(course_items)
    print(f"   Found {initial_count} courses")
    assert initial_count > 0, "No courses found!"
    
    # Check if activities are shown
    print("2. Checking course activities...")
    # Click first course to select it
    first_course = page.locator(".bg-white.rounded-lg.shadow").first
    first_course.click()
    page.wait_for_timeout(1000)
    
    # Check for activities in right panel
    activities_section = page.locator("text=已發布").or_(page.locator("text=活動")).first
    assert activities_section.is_visible(), "Activities section should be visible"
    print("   ✓ Activities are displayed")
    
    # 3. Test CREATE course
    print("3. Testing CREATE course...")
    page.click("button:has-text('新增課程')")
    page.wait_for_selector("[role='dialog'], .modal, .fixed.inset-0")
    
    # Fill form
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    modal.locator("input[placeholder*='基礎英語會話']").fill("E2E測試課程")
    modal.locator("textarea[placeholder*='請描述']").fill("這是E2E測試課程的描述")
    modal.locator("select").select_option("A1")
    
    # Submit
    modal.locator("button:has-text('新增')").click()
    page.wait_for_selector("text=課程已新增", timeout=5000)
    print("   ✓ Course created successfully")
    
    # 4. Test UPDATE
    print("4. Testing UPDATE course...")
    page.wait_for_timeout(1000)
    
    # Find test course
    test_course = page.locator(".bg-white.rounded-lg.shadow:has-text('E2E測試課程')").first
    test_course.locator("button[aria-label*='編輯'], button:has(svg.lucide-edit)").click()
    
    # Update name
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    title_input = modal.locator("input[placeholder*='基礎英語會話']")
    title_input.clear()
    title_input.fill("更新E2E測試課程")
    
    # Submit
    modal.locator("button:has-text('儲存')").click()
    page.wait_for_selector("text=課程已更新", timeout=5000)
    print("   ✓ Course updated successfully")
    
    # 5. Test DELETE
    print("5. Testing DELETE course...")
    page.wait_for_timeout(1000)
    
    # Find updated course
    test_course = page.locator(".bg-white.rounded-lg.shadow:has-text('更新E2E測試課程')").first
    test_course.locator("button[aria-label*='刪除'], button:has(svg.lucide-trash)").click()
    
    # Confirm
    page.click("button:has-text('確定')")
    page.wait_for_selector("text=課程已刪除", timeout=5000)
    print("   ✓ Course deleted successfully")
    
    print("✅ Course Management tests passed!")


def test_classroom_management(page):
    """Test classroom management page"""
    print("\n=== Testing Classroom Management ===")
    
    # Navigate to classrooms page
    page.goto(f"{BASE_URL}/teacher/classrooms")
    page.wait_for_selector("h2:has-text('教室管理')")
    
    # 1. Check data is displayed
    print("1. Checking classroom data display...")
    page.wait_for_selector(".p-4.border-b", timeout=10000)
    classroom_items = page.locator(".p-4.border-b").all()
    initial_count = len(classroom_items) - 1  # Subtract header if any
    print(f"   Found {initial_count} classrooms")
    assert initial_count > 0, "No classrooms found!"
    
    # 2. Test classroom selection
    print("2. Testing classroom selection...")
    first_classroom = page.locator(".p-4.border-b.cursor-pointer").first
    first_classroom.click()
    page.wait_for_timeout(500)
    
    # Check if right panel shows classroom details
    selected_indicator = page.locator(".bg-blue-50.border-l-4.border-l-blue-500")
    assert selected_indicator.count() > 0, "Classroom should be selected"
    print("   ✓ Classroom selection works")
    
    # 3. Test CREATE classroom
    print("3. Testing CREATE classroom...")
    page.click("button:has-text('新增教室')")
    page.wait_for_selector("[role='dialog'], .modal, .fixed.inset-0")
    
    # Fill form
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    
    # Select school
    school_select = modal.locator("select").first()
    school_select.select_option(index=1)
    
    # Fill classroom name
    modal.locator("input[placeholder*='六年一班']").fill("E2E測試教室")
    
    # Select grade
    grade_select = modal.locator("select:has-text('請選擇年級')").or_(modal.locator("select").nth(1))
    grade_select.select_option("6")
    
    # Submit
    modal.locator("button:has-text('新增')").click()
    page.wait_for_selector("text=教室已新增", timeout=5000)
    print("   ✓ Classroom created successfully")
    
    # 4. Test UPDATE
    print("4. Testing UPDATE classroom...")
    page.wait_for_timeout(1000)
    
    # Find test classroom
    test_classroom = page.locator(".p-4.border-b:has-text('E2E測試教室')").first
    test_classroom.locator("button:has(svg.lucide-edit)").click()
    
    # Update name
    modal = page.locator("[role='dialog'], .modal, .fixed.inset-0").last
    name_input = modal.locator("input[value='E2E測試教室']")
    name_input.clear()
    name_input.fill("更新E2E測試教室")
    
    # Submit
    modal.locator("button:has-text('儲存')").click()
    page.wait_for_selector("text=教室資料已更新", timeout=5000)
    print("   ✓ Classroom updated successfully")
    
    # 5. Test DELETE
    print("5. Testing DELETE classroom...")
    page.wait_for_timeout(1000)
    
    # Find updated classroom
    test_classroom = page.locator(".p-4.border-b:has-text('更新E2E測試教室')").first
    test_classroom.locator("button:has(svg.lucide-trash)").click()
    
    # Confirm
    page.click("button:has-text('確定')")
    page.wait_for_selector("text=教室已刪除", timeout=5000)
    print("   ✓ Classroom deleted successfully")
    
    print("✅ Classroom Management tests passed!")


def main():
    """Run all E2E tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='zh-TW'
        )
        page = context.new_page()
        
        try:
            # Login
            TestHelpers.login(page)
            
            # Run all tests
            test_student_management(page)
            test_course_management(page)
            test_classroom_management(page)
            
            print("\n🎉 All E2E tests passed successfully!")
            print("✅ Student Management - PASSED")
            print("✅ Course Management - PASSED") 
            print("✅ Classroom Management - PASSED")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            TestHelpers.take_screenshot_on_failure(page, "final")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    main()