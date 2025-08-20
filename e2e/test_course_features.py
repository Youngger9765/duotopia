#!/usr/bin/env python3
"""
Test course management features
"""
from playwright.sync_api import sync_playwright, expect

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def test_course_management():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to True for headless
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            locale='zh-TW'
        )
        page = context.new_page()
        
        try:
            # Login
            print("1. Logging in...")
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            print("   ✓ Login successful")
            
            # Navigate to course management
            print("\n2. Navigating to course management...")
            page.goto(f"{BASE_URL}/teacher/courses")
            page.wait_for_selector("h2:has-text('課程管理')")
            print("   ✓ Course management page loaded")
            
            # Check courses are displayed
            print("\n3. Checking courses display...")
            page.wait_for_selector(".bg-white.rounded-lg.shadow", timeout=5000)
            courses = page.locator(".p-3.border-b.cursor-pointer").all()
            print(f"   ✓ Found {len(courses)} courses")
            
            if len(courses) == 0:
                print("   ! No courses found, checking for errors...")
                page.screenshot(path="no_courses_found.png")
            
            # Click first course
            print("\n4. Testing course selection...")
            first_course = page.locator(".p-3.border-b").first
            first_course.click()
            page.wait_for_timeout(1000)
            
            # Check if activities are displayed
            page.wait_for_selector("h3:has-text('活動')")
            activities = page.locator("div:has-text('已發布')").all()
            print(f"   ✓ Course selected, activities panel shown")
            
            # Click an activity
            print("\n5. Testing activity selection...")
            activity_items = page.locator(".p-3.border-b.cursor-pointer").all()
            if len(activity_items) > 1:  # Skip first course item
                activity_items[1].click()
                page.wait_for_timeout(1000)
                
                # Check activity content display
                if page.locator("h4:has-text('活動說明')").is_visible():
                    print("   ✓ Activity content displayed")
                else:
                    print("   ✗ Activity content not displayed")
            
            # Test creating activity
            print("\n6. Testing create activity...")
            page.locator("button:has-text('新增活動')").click()
            page.wait_for_selector("[role='dialog']")
            
            # Fill form
            modal = page.locator("[role='dialog']").last
            modal.locator("input[placeholder*='活動名稱']").fill("E2E測試活動")
            modal.locator("select").select_option(index=1)  # Select activity type
            
            # Submit
            modal.locator("button:has-text('新增')").click()
            
            # Check for success or error
            page.wait_for_timeout(2000)
            if page.locator("text=活動已建立").is_visible():
                print("   ✓ Activity created successfully")
            elif page.locator("text=錯誤").is_visible():
                error_msg = page.locator(".destructive").text_content()
                print(f"   ✗ Failed to create activity: {error_msg}")
            else:
                print("   ? Activity creation result unclear")
            
            print("\n✅ All tests completed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="course_test_failure.png")
        finally:
            browser.close()

if __name__ == "__main__":
    test_course_management()