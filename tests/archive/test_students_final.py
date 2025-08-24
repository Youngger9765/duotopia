#!/usr/bin/env python3
"""
最終測試學生管理頁面
"""
from playwright.sync_api import sync_playwright
import time

def test_students_final():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 測試學生管理功能修復 ===\n")
            
            # 1. 登入
            print("1. 登入個體戶教師...")
            page.goto("http://localhost:5173/login")
            page.click('button:has-text("個體戶教師")')
            time.sleep(0.5)
            page.click('button[type="submit"]:has-text("登入")')
            
            # 等待導航
            page.wait_for_url("**/individual", timeout=5000)
            page.wait_for_load_state("networkidle")
            print("   ✓ 登入成功")
            
            # 2. 直接跳到學生管理
            print("\n2. 訪問學生管理...")
            page.click('a:has-text("學生管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # 給 API 更多時間
            
            # 檢查是否有學生
            no_students_msg = page.query_selector("text=沒有找到符合條件的學生")
            if no_students_msg:
                print("   ❌ 仍然顯示「沒有找到符合條件的學生」")
            else:
                # 檢查是否有學生行
                rows = page.query_selector_all("tbody tr")
                if rows:
                    print(f"   ✅ 找到 {len(rows)} 個學生！")
                    
                    # 顯示學生資訊
                    for i, row in enumerate(rows[:3]):  # 只顯示前3個
                        name_cell = row.query_selector(".text-sm.font-medium.text-gray-900")
                        email_cell = row.query_selector(".text-sm.text-gray-500")
                        if name_cell and email_cell:
                            print(f"   - 學生 {i+1}: {name_cell.text_content()}")
                            print(f"     Email: {email_cell.text_content()}")
                else:
                    print("   ⚠️  沒有找到學生行，但也沒有「沒有找到符合條件的學生」訊息")
            
            page.screenshot(path="students_test_final.png")
            print("   已截圖: students_test_final.png")
            
            print("\n✅ 測試完成！")
            
            print("\n保持瀏覽器開啟 10 秒供檢查...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 錯誤: {str(e)}")
            page.screenshot(path="students_test_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_students_final()