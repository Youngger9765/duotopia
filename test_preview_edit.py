#!/usr/bin/env python3
"""
測試預覽和編輯功能
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def test_preview_edit():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("測試預覽和編輯功能...")
            
            # 登入
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            
            # 進入課程管理
            page.goto(f"{BASE_URL}/teacher/courses")
            page.wait_for_selector("h2:has-text('課程管理')")
            time.sleep(2)
            
            # 選擇課程
            courses = page.locator(".p-3.border-b.cursor-pointer").all()
            courses[0].click()
            time.sleep(1)
            
            # 選擇活動
            activities = page.locator(".p-3.border-b.cursor-pointer").all()
            if len(activities) > 1:
                activities[1].click()  # Skip first course item
                time.sleep(1)
                
                # 測試預覽按鈕
                print("測試預覽按鈕...")
                preview_btn = page.locator("button:has-text('預覽')")
                if preview_btn.is_visible():
                    preview_btn.click()
                    time.sleep(2)
                    
                    if page.locator("h3:has-text('活動預覽')").is_visible():
                        print("✅ 預覽功能正常")
                        page.locator("button").filter(has_text="×").click()  # Close modal
                    else:
                        print("❌ 預覽功能失效")
                
                # 測試編輯按鈕  
                print("測試編輯按鈕...")
                edit_btn = page.locator("button:has-text('編輯內容')")
                if edit_btn.is_visible():
                    edit_btn.click()
                    time.sleep(2)
                    
                    if page.locator("h3:has-text('編輯活動內容')").is_visible():
                        print("✅ 編輯功能正常")
                        page.locator("button:has-text('取消')").click()  # Close modal
                    else:
                        print("❌ 編輯功能失效")
            
            print("\n✅ 測試完成")
            
        except Exception as e:
            print(f"❌ 測試失敗：{e}")
            page.screenshot(path="preview_edit_test_error.png")
        finally:
            input("按 Enter 關閉...")
            browser.close()

if __name__ == "__main__":
    test_preview_edit()