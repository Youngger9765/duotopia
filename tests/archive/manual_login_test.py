#!/usr/bin/env python3
"""
手動登入測試
"""
from playwright.sync_api import sync_playwright
import time

def manual_test():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # 打開開發者工具
        context = browser.new_context()
        page = context.new_page()
        
        # 開啟網路請求記錄
        page.on("request", lambda request: print(f">> {request.method} {request.url}"))
        page.on("response", lambda response: print(f"<< {response.status} {response.url}"))
        
        print("1. 訪問登入頁面...")
        page.goto("http://localhost:5173/login")
        
        print("\n請手動操作：")
        print("1. 輸入 email: teacher@individual.com")
        print("2. 輸入密碼: password123")
        print("3. 點擊登入按鈕")
        print("\n觀察網路請求和頁面跳轉...")
        
        # 保持瀏覽器開啟
        input("\n按 Enter 關閉瀏覽器...")
        browser.close()

if __name__ == "__main__":
    manual_test()