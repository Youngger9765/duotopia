#!/usr/bin/env python3
"""
快速測試教室頁面並檢查控制台
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def quick_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 監聽控制台消息
        page.on("console", lambda msg: print(f"Console: {msg.text}"))
        
        try:
            # 登入
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            
            # 進入教室管理
            page.goto(f"{BASE_URL}/teacher/classrooms")
            time.sleep(5)  # 等待數據載入和調試信息
            
            print("\n頁面載入完成，檢查控制台輸出...")
            
        except Exception as e:
            print(f"錯誤：{e}")
        finally:
            input("按 Enter 關閉...")
            browser.close()

if __name__ == "__main__":
    quick_test()