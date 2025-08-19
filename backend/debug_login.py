from playwright.sync_api import sync_playwright
import time

def debug_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 監聽網路請求
        def handle_request(request):
            if 'login' in request.url:
                print(f"📤 Login Request: {request.method} {request.url}")
                if request.post_data:
                    print(f"📤 Post Data: {request.post_data}")
        
        def handle_response(response):
            if 'login' in response.url:
                print(f"📥 Login Response: {response.status} {response.url}")
                print(f"📥 Response text: {response.text()}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        # 監聽 console 錯誤
        def handle_console(msg):
            print(f"🖥️  Console {msg.type}: {msg.text}")
        
        page.on("console", handle_console)
        
        # 登入
        print("🔐 開始登入流程...")
        page.goto("http://localhost:5174/login")
        time.sleep(2)
        
        # 檢查頁面內容
        print("📄 登入頁面內容:")
        print(page.locator('body').inner_text()[:200])
        
        # 填寫登入表單
        print("✏️ 填寫登入表單...")
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'password123')
        
        # 點擊登入按鈕
        print("🔽 點擊登入按鈕...")
        page.click('button[type="submit"]')
        
        # 等待回應
        time.sleep(5)
        
        # 檢查登入結果
        current_url = page.url
        page_text = page.locator('body').inner_text()
        
        print(f"🎯 登入後 URL: {current_url}")
        print(f"🎯 登入後頁面內容前 200 字符: {page_text[:200]}")
        
        # 檢查 localStorage
        token = page.evaluate("localStorage.getItem('token')")
        print(f"🎫 Token in localStorage: {token[:50] if token else 'None'}...")
        
        browser.close()

if __name__ == "__main__":
    debug_login()