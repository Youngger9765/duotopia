from playwright.sync_api import sync_playwright
import time

def check_error_boundary():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 登入
        page.goto("http://localhost:5174/login")
        time.sleep(2)
        page.fill('input[type="email"]', 'teacher1@duotopia.com')
        page.fill('input[type="password"]', 'password123')
        page.click('button[type="submit"]')
        time.sleep(3)
        
        # 導航到學生管理
        page.goto("http://localhost:5174/teacher/students")
        time.sleep(5)
        
        # 檢查錯誤邊界
        error_message = page.locator('text=頁面載入錯誤').count()
        error_retry = page.locator('text=請重試').count()
        error_details = page.locator('text=錯誤詳情').count()
        
        print(f"❌ 錯誤訊息: {error_message}")
        print(f"❌ 重試按鈕: {error_retry}")  
        print(f"❌ 錯誤詳情: {error_details}")
        
        # 檢查完整頁面 HTML
        html_content = page.locator('body').inner_html()
        if '頁面載入錯誤' in html_content:
            print("✅ 錯誤邊界正常工作")
            # 提取錯誤詳情
            error_text = page.locator('[class*="text-red"]').inner_text()
            print(f"📄 錯誤詳情: {error_text}")
        else:
            print("❌ 錯誤邊界沒有激活")
            print("📄 實際頁面內容前 500 字符:")
            print(page.locator('body').inner_text()[:500])
        
        browser.close()

if __name__ == "__main__":
    check_error_boundary()