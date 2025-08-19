from playwright.sync_api import sync_playwright
import time

def test_page_load():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 監聽 console 錯誤
        def handle_console(msg):
            if msg.type == 'error':
                print(f"❌ Console Error: {msg.text}")
        
        page.on("console", handle_console)
        
        # 登入
        print("登入中...")
        page.goto("http://localhost:5174/login")
        time.sleep(2)
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'password123')
        page.click('button[type="submit"]')
        
        # 檢查登入結果
        time.sleep(3)
        current_url = page.url
        page_text = page.locator('body').inner_text()
        
        print(f"登入後 URL: {current_url}")
        if "錯誤" in page_text or "失敗" in page_text:
            print(f"❌ 登入失敗: {page_text[:100]}")
            return
        
        if "/teacher" in current_url:
            print("✅ 登入成功")
        else:
            print("⚠️  登入狀態未知")
        
        # 檢查學生管理頁面
        print("導航到學生管理...")
        page.goto("http://localhost:5174/teacher/students")
        time.sleep(5)
        
        # 檢查頁面內容
        title = page.locator('h2').count()
        body_text = page.locator('body').inner_text()
        
        print(f"頁面標題數量: {title}")
        print(f"頁面內容前 200 字符: {body_text[:200]}")
        
        if "學生管理" in body_text:
            print("✅ 找到學生管理標題")
        else:
            print("❌ 沒有找到學生管理標題")
            
        if "載入中" in body_text:
            print("⏳ 頁面仍在載入")
        
        browser.close()

if __name__ == "__main__":
    test_page_load()