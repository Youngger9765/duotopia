#!/usr/bin/env python3
"""
測試教室管理頁面
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5174"
TEACHER_EMAIL = "teacher1@duotopia.com"
TEACHER_PASSWORD = "password123"

def test_classrooms():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("測試教室管理頁面...")
            
            # 登入
            page.goto(f"{BASE_URL}/login")
            page.locator("input[type='email']").fill(TEACHER_EMAIL)
            page.locator("input[type='password']").fill(TEACHER_PASSWORD)
            page.locator("button[type='submit']").click()
            page.wait_for_url("**/teacher", timeout=10000)
            print("✅ 登入成功")
            
            # 進入教室管理頁面
            page.goto(f"{BASE_URL}/teacher/classrooms")
            time.sleep(3)
            
            # 檢查頁面載入
            if page.locator("h2:has-text('教室管理')").is_visible():
                print("✅ 教室管理頁面載入成功")
            else:
                print("❌ 教室管理頁面載入失敗")
                page.screenshot(path="classroom_page_error.png")
                return
            
            # 檢查教室列表
            classroom_items = page.locator(".p-4.border-b").all()
            print(f"找到 {len(classroom_items)} 個教室項目")
            
            # 檢查是否有教室數據
            if len(classroom_items) > 1:  # 排除可能的標題行
                print("✅ 教室列表顯示正常")
                
                # 點擊第一個教室
                first_classroom = page.locator(".p-4.border-b.cursor-pointer").first
                if first_classroom.is_visible():
                    first_classroom.click()
                    time.sleep(1)
                    print("✅ 教室選擇功能正常")
                    
                    # 檢查右側面板
                    if page.locator(".bg-blue-50.border-l-4").is_visible():
                        print("✅ 教室詳情顯示正常")
                    else:
                        print("❌ 教室詳情沒有顯示")
                else:
                    print("❌ 沒有可點擊的教室")
            else:
                print("❌ 沒有找到教室數據")
                page.screenshot(path="no_classrooms.png")
            
            # 測試新增教室功能
            add_button = page.locator("button:has-text('新增教室')")
            if add_button.is_visible():
                print("✅ 新增教室按鈕存在")
                add_button.click()
                time.sleep(1)
                
                if page.locator("h3:has-text('新增教室')").is_visible():
                    print("✅ 新增教室對話框顯示正常")
                    page.locator("button:has-text('取消')").click()
                else:
                    print("❌ 新增教室對話框沒有顯示")
            else:
                print("❌ 新增教室按鈕不存在")
            
            print("\n測試完成")
            
        except Exception as e:
            print(f"❌ 測試失敗：{e}")
            page.screenshot(path="classroom_test_error.png")
        finally:
            input("按 Enter 關閉瀏覽器...")
            browser.close()

if __name__ == "__main__":
    test_classrooms()