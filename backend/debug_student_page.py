from playwright.sync_api import sync_playwright
import time

def debug_student_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 監聽所有 console 訊息
        def handle_console(msg):
            print(f"🖥️ [{msg.type}]: {msg.text}")
        
        def handle_response(response):
            if '/api/' in response.url:
                print(f"📥 API {response.status}: {response.url}")
        
        page.on("console", handle_console)
        page.on("response", handle_response)
        
        # 登入
        print("🔐 登入...")
        page.goto("http://localhost:5174/login")
        time.sleep(2)
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'password123')
        page.click('button[type="submit"]')
        time.sleep(3)
        
        print(f"✅ 登入成功，當前 URL: {page.url}")
        
        # 直接導航到學生管理頁面
        print("📋 導航到學生管理...")
        page.goto("http://localhost:5174/teacher/students")
        time.sleep(2)
        
        # 等待更長時間以觀察錯誤
        print("⏳ 等待頁面載入...")
        time.sleep(10)
        
        # 檢查頁面狀態
        current_url = page.url
        page_text = page.locator('body').inner_text()
        
        print(f"🎯 最終 URL: {current_url}")
        print(f"🎯 頁面內容: {page_text[:300]}")
        
        # 檢查是否有錯誤邊界
        error_boundary = page.locator('text=頁面載入錯誤').count()
        if error_boundary > 0:
            print("❌ 發現錯誤邊界")
        
        # 檢查是否有學生管理標題
        title_count = page.locator('h2:has-text("學生管理")').count()
        print(f"📊 學生管理標題數量: {title_count}")
        
        browser.close()

if __name__ == "__main__":
    debug_student_page()