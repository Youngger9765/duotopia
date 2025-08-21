#!/usr/bin/env python3
"""
個體戶教室功能 E2E 測試
"""
from playwright.sync_api import sync_playwright
import time
import json

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"

def test_classroom_detail_e2e():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500  # 慢一點以便觀察
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = context.new_page()
        
        # 監聽控制台和網路錯誤
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        def handle_response(response):
            if response.status >= 400:
                print(f"HTTP {response.status} {response.url}")
        page.on("response", handle_response)
        
        try:
            print("=== 個體戶教室功能 E2E 測試 ===\n")
            
            # 1. 登入
            print("1. 登入個體戶教師...")
            page.goto(f"{BASE_URL}/login")
            time.sleep(1)
            
            # 使用測試帳號按鈕
            page.click("text=個體戶教師")
            time.sleep(1)
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            print(f"當前URL: {page.url}")
            assert "/individual" in page.url, "應該導向個體戶系統"
            
            # 2. 進入教室管理
            print("\n2. 進入教室管理...")
            page.click("text=我的教室")
            time.sleep(2)
            
            # 檢查教室列表
            classrooms = page.locator(".hover\\:shadow-lg").count()
            print(f"找到 {classrooms} 個教室")
            assert classrooms > 0, "應該有教室"
            
            # 3. 進入第一個教室
            print("\n3. 進入第一個教室...")
            page.locator("button:has-text('進入教室')").first.click()
            time.sleep(2)
            
            # 檢查是否進入教室詳細頁面
            assert page.locator("text=返回").count() > 0, "應該有返回按鈕"
            classroom_name = page.locator("h1").nth(1).text_content()
            print(f"進入教室: {classroom_name}")
            
            # 4. 測試學生管理標籤
            print("\n4. 測試學生管理...")
            student_tab = page.locator("button:has-text('學生管理')")
            if student_tab.count() > 0:
                student_count_text = student_tab.text_content()
                print(f"學生管理標籤: {student_count_text}")
                
                # 檢查學生列表
                students = page.locator("table tbody tr").count()
                print(f"學生列表顯示 {students} 個學生")
            
            # 5. 切換到課程管理
            print("\n5. 切換到課程管理...")
            page.click("button:has-text('課程管理')")
            time.sleep(2)
            
            # 檢查課程功能按鈕
            assert page.locator("text=從公版複製").count() > 0, "應該有複製按鈕"
            assert page.locator("text=建立新課程").count() > 0, "應該有新建按鈕"
            
            # 6. 測試公版課程複製
            print("\n6. 測試公版課程複製...")
            page.click("text=從公版複製")
            time.sleep(2)
            
            # 檢查公版課程列表
            public_courses = page.locator(".cursor-pointer.hover\\:shadow-md").count()
            print(f"找到 {public_courses} 個公版課程")
            
            if public_courses > 0:
                # 複製第一個課程
                print("複製第一個公版課程...")
                # 等待 modal 內容完全載入
                page.wait_for_selector("button:has-text('複製')", state="visible")
                time.sleep(1)
                # 使用更精確的選擇器
                copy_button = page.locator(".modal button:has-text('複製')").first
                copy_button.click()
                time.sleep(2)
                
                # 檢查是否複製成功（應該關閉 modal 並刷新課程列表）
                assert page.locator("text=從公版複製").count() > 0, "Modal 應該已關閉"
            else:
                print("沒有公版課程可複製")
                page.click("text=關閉")
            
            # 7. 返回教室列表
            print("\n7. 返回教室列表...")
            page.click("button:has-text('返回')")
            time.sleep(2)
            
            assert page.locator("text=我的教室").count() > 0, "應該返回教室列表"
            
            print("\n✅ E2E 測試完成！所有功能正常運作")
            
        except Exception as e:
            print(f"\n❌ 測試失敗：{e}")
            page.screenshot(path="classroom_test_error.png")
            print("已儲存錯誤截圖")
            raise
        
        finally:
            print("\n5秒後關閉瀏覽器...")
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    test_classroom_detail_e2e()