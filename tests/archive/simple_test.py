#!/usr/bin/env python3
import sys
sys.path.append('/opt/homebrew/lib/python3.10/site-packages')

import asyncio
from playwright.async_api import async_playwright

async def simple_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 清除 localStorage
        await page.goto('http://localhost:5173/')
        await page.evaluate('localStorage.clear()')
        
        # 登入
        await page.goto('http://localhost:5173/login')
        await page.wait_for_timeout(1000)
        
        # 點擊個體戶教師
        await page.click('text=個體戶教師')
        await page.wait_for_timeout(500)
        
        # 點擊登入
        await page.click('button[type="submit"]')
        
        # 等待導航到 /individual
        await page.wait_for_url('**/individual', timeout=5000)
        await page.wait_for_timeout(2000)
        
        # 截圖
        await page.screenshot(path='debug_screenshot.png', full_page=True)
        
        # 檢查 DEBUG 資訊
        debug_elements = await page.query_selector_all('.text-red-500')
        for element in debug_elements:
            text = await element.text_content()
            print("DEBUG:", text)
        
        # 檢查側邊欄
        name_element = await page.query_selector('.text-sm.font-medium.text-gray-900')
        if name_element:
            name = await name_element.text_content()
            print("側邊欄名字:", name)
            
        email_element = await page.query_selector('.text-xs.text-gray-500')
        if email_element:
            email = await email_element.text_content()
            print("側邊欄 email:", email)
        
        # 保持開啟 5 秒
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(simple_test())