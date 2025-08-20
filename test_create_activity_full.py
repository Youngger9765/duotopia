#!/usr/bin/env python3
"""
Full test for creating activity including login
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def test_create_activity():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # 1. Login
            print("1. Logging in...")
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            print("   ✓ Login successful")
            
            # 2. Go to courses page
            print("2. Going to courses page...")
            page.goto(f"{BASE_URL}/teacher/courses")
            page.wait_for_selector("h2:has-text('課程管理')")
            time.sleep(1)
            
            # 3. Click first course
            print("3. Selecting first course...")
            courses = page.locator(".p-3.border-b.cursor-pointer").all()
            if len(courses) > 0:
                courses[0].click()
                time.sleep(1)
                print(f"   ✓ Selected course")
            else:
                print("   ✗ No courses found!")
                return
            
            # 4. Click Add Activity button
            print("4. Opening add activity modal...")
            add_button = page.locator("button:has-text('新增活動')")
            add_button.click()
            time.sleep(1)
            
            # 5. Fill form
            print("5. Filling activity form...")
            modal = page.locator(".fixed.inset-0").last
            
            # Enter title
            title_input = modal.locator("input[placeholder='請輸入活動標題']")
            title_input.fill("測試活動 - E2E Test")
            
            # Select type - use the dropdown
            type_select = modal.locator("select").first
            type_select.select_option("聽力克漏字")
            
            # Add due date (optional)
            date_input = modal.locator("input[type='date']")
            date_input.fill("2025-08-25")
            
            # Take screenshot before saving
            page.screenshot(path="before_save_activity.png")
            
            # 6. Click save
            print("6. Saving activity...")
            save_button = modal.locator("button:has-text('建立活動')")
            save_button.click()
            
            # 7. Wait for result
            time.sleep(3)
            
            # Check for success or error message
            if page.locator("text=活動已建立").is_visible():
                print("   ✓ Activity created successfully!")
            elif page.locator("text=錯誤").is_visible():
                error_text = page.locator(".destructive").text_content()
                print(f"   ✗ Error creating activity: {error_text}")
                page.screenshot(path="create_activity_error.png")
            else:
                print("   ? Result unclear")
                page.screenshot(path="create_activity_result.png")
            
            print("\n✅ Test completed")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            page.screenshot(path="test_failure.png")
        finally:
            time.sleep(5)  # Keep browser open for 5 seconds
            browser.close()

if __name__ == "__main__":
    test_create_activity()