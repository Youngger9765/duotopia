#!/usr/bin/env python3
"""
Test for login page functionality
"""
from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5174"

def test_login_page():
    """Test that login page works correctly"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("1. Testing login page loads...")
            page.goto(f"{BASE_URL}/login")
            page.wait_for_load_state("domcontentloaded")
            
            # Check page title
            assert "教師登入" in page.text_content("h2"), "Login page should show teacher login title"
            print("✓ Login page loads correctly")
            
            print("\n2. Testing demo button exists...")
            demo_button = page.locator("button:has-text('使用 Demo 教師帳號')")
            assert demo_button.count() > 0, "Demo button should exist"
            print("✓ Demo button exists")
            
            print("\n3. Testing demo button fills credentials...")
            demo_button.click()
            page.wait_for_timeout(500)
            
            # Check if email is filled
            email_input = page.locator("input[type='email']")
            email_value = email_input.input_value()
            assert email_value == "teacher1@duotopia.com", f"Email should be filled, got: {email_value}"
            print("✓ Email filled correctly")
            
            # Check if password is filled
            password_input = page.locator("input[type='password']")
            password_value = password_input.input_value()
            assert password_value == "password123", f"Password should be filled, got: {password_value}"
            print("✓ Password filled correctly")
            
            print("\n4. Testing login submission...")
            # Submit the form
            submit_button = page.locator("button[type='submit']")
            submit_button.click()
            
            # Wait for navigation
            page.wait_for_url("**/teacher", timeout=10000)
            print("✓ Successfully logged in and redirected to teacher dashboard")
            
            print("\n✅ All login tests passed!")
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="login_test_failure.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    test_login_page()