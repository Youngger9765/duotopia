#!/usr/bin/env python3
"""
Test adding activity to course
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"

def test_add_activity():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # Go directly to courses page (assuming already logged in)
            print("1. Going to courses page...")
            page.goto(f"{BASE_URL}/teacher/courses")
            time.sleep(2)
            
            # Click first course
            print("2. Clicking first course...")
            first_course = page.locator(".p-3.border-b.cursor-pointer").first
            first_course.click()
            time.sleep(1)
            
            # Click Add Activity button
            print("3. Clicking Add Activity button...")
            add_button = page.locator("button:has-text('新增活動')")
            add_button.click()
            time.sleep(1)
            
            # Fill form
            print("4. Filling form...")
            modal = page.locator(".fixed.inset-0").last
            
            # Enter title
            title_input = modal.locator("input[placeholder='請輸入活動標題']")
            title_input.fill("測試活動123")
            
            # Select type
            type_select = modal.locator("select").first
            type_select.select_option("聽力克漏字")
            
            # Click save
            print("5. Clicking save...")
            save_button = modal.locator("button:has-text('建立活動')")
            save_button.click()
            
            # Wait for result
            time.sleep(3)
            
            print("✅ Test completed")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            page.screenshot(path="add_activity_error.png")
        finally:
            input("Press Enter to close browser...")
            browser.close()

if __name__ == "__main__":
    test_add_activity()