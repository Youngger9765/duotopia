#!/usr/bin/env python3
import os
import sys
sys.path.append('/opt/homebrew/lib/python3.10/site-packages')

import asyncio
from playwright.async_api import async_playwright

async def test_individual_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 先清除 localStorage
        await page.goto('http://localhost:5173/')
        await page.evaluate('localStorage.clear()')
        
        # 打開登入頁面
        await page.goto('http://localhost:5173/login')
        await page.wait_for_timeout(1000)
        
        # 點擊個體戶教師按鈕
        await page.click('text=個體戶教師')
        await page.wait_for_timeout(500)
        
        # 登入
        await page.click('button[type="submit"]')
        
        # 等待導航到 /individual
        await page.wait_for_url('**/individual', timeout=5000)
        await page.wait_for_timeout(2000)
        
        # 檢查 localStorage
        storage = await page.evaluate('''() => {
            return {
                token: localStorage.getItem('token'),
                userEmail: localStorage.getItem('userEmail'),
                userFullName: localStorage.getItem('userFullName'),
                userRole: localStorage.getItem('userRole'),
                userId: localStorage.getItem('userId')
            }
        }''')
        print("LocalStorage 內容:", storage)
        
        # 檢查當前 URL
        print("當前 URL:", page.url)
        
        # 如果不在 /individual，手動導航
        if '/individual' not in page.url:
            await page.goto('http://localhost:5173/individual')
            await page.wait_for_timeout(2000)
        
        # 檢查用戶資訊是否顯示
        try:
            # 查找側邊欄的用戶資訊
            user_info = await page.query_selector('.text-sm.font-medium.text-gray-900')
            if user_info:
                text = await user_info.text_content()
                print("側邊欄顯示的名字:", text)
            else:
                print("找不到用戶名稱元素")
                
            email_info = await page.query_selector('.text-xs.text-gray-500')
            if email_info:
                text = await email_info.text_content()
                print("側邊欄顯示的 email:", text)
            else:
                print("找不到 email 元素")
        except Exception as e:
            print("錯誤:", str(e))
        
        # 檢查 React 組件狀態
        react_state = await page.evaluate('''() => {
            // 嘗試獲取 React 組件的狀態
            const elements = document.querySelectorAll('[class*="text-sm font-medium"]');
            const results = [];
            elements.forEach(el => {
                results.push({
                    text: el.textContent,
                    className: el.className
                });
            });
            return results;
        }''')
        print("所有 text-sm font-medium 元素:", react_state)
        
        # 截圖
        await page.screenshot(path='individual_dashboard.png', full_page=True)
        print("已截圖到 individual_dashboard.png")
        
        # 檢查 Console logs
        print("\n=== Console 訊息 ===")
        
        # 再次檢查 AuthContext 的 user
        auth_user = await page.evaluate('''() => {
            // 嘗試從 React DevTools 獲取資訊
            const rootElement = document.getElementById('root');
            if (rootElement && rootElement._reactRootContainer) {
                // React 17+
                return "Found React root";
            }
            return "No React root found";
        }''')
        print("React check:", auth_user)
        
        # 重新整理頁面以測試 AuthContext 重新載入
        print("\n重新整理頁面...")
        await page.reload()
        await page.wait_for_timeout(2000)
        
        # 再次檢查側邊欄
        print("\n=== 重新整理後 ===")
        user_info = await page.query_selector('.text-sm.font-medium.text-gray-900')
        if user_info:
            text = await user_info.text_content()
            print("側邊欄顯示的名字:", text)
            
        email_info = await page.query_selector('.text-xs.text-gray-500')
        if email_info:
            text = await email_info.text_content()
            print("側邊欄顯示的 email:", text)
        
        # 再次截圖
        await page.screenshot(path='individual_dashboard_after_reload.png', full_page=True)
        print("已截圖到 individual_dashboard_after_reload.png")
        
        # 保持瀏覽器開啟 5 秒讓我們看到結果
        print("\n瀏覽器將保持開啟 5 秒...")
        await page.wait_for_timeout(5000)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_individual_login())