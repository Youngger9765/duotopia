#!/usr/bin/env python3
"""
測試個體戶教師的各個管理頁面
"""
from playwright.sync_api import sync_playwright
import time

def test_individual_pages():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 測試個體戶教師管理頁面 ===\n")
            
            # 1. 登入
            print("1. 登入個體戶教師...")
            page.goto("http://localhost:5173/login")
            page.click('button:has-text("個體戶教師")')
            time.sleep(0.5)
            page.click('button[type="submit"]:has-text("登入")')
            page.wait_for_url("**/individual", timeout=5000)
            page.wait_for_load_state("networkidle")
            print("   ✓ 登入成功")
            
            # 2. 檢查總覽頁面的統計數據
            print("\n2. 檢查總覽頁面統計...")
            stats = page.query_selector_all(".text-3xl.font-semibold")
            if stats:
                print(f"   學生總數: {stats[0].text_content()}")
                print(f"   開課教室: {stats[1].text_content()}")
                if len(stats) > 2:
                    print(f"   本月收入: {stats[2].text_content()}")
            
            # 3. 訪問我的教室頁面
            print("\n3. 訪問「我的教室」頁面...")
            page.click('a:has-text("我的教室")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 截圖教室頁面
            page.screenshot(path="individual_01_classrooms.png")
            print("   已截圖: individual_01_classrooms.png")
            
            # 檢查是否有教室資料
            classroom_cards = page.query_selector_all(".bg-white.rounded-lg.shadow")
            print(f"   找到 {len(classroom_cards)} 個教室")
            
            # 4. 訪問學生管理頁面
            print("\n4. 訪問「學生管理」頁面...")
            page.click('a:has-text("學生管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 截圖學生頁面
            page.screenshot(path="individual_02_students.png")
            print("   已截圖: individual_02_students.png")
            
            # 檢查是否有學生資料
            student_rows = page.query_selector_all("tbody tr")
            print(f"   找到 {len(student_rows)} 位學生")
            
            # 5. 訪問課程管理頁面
            print("\n5. 訪問「課程管理」頁面...")
            page.click('a:has-text("課程管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 截圖課程頁面
            page.screenshot(path="individual_03_courses.png")
            print("   已截圖: individual_03_courses.png")
            
            # 檢查是否有課程資料
            course_cards = page.query_selector_all(".bg-white.rounded-lg")
            print(f"   找到 {len(course_cards)} 個課程")
            
            # 6. 檢查側邊欄的用戶信息
            print("\n6. 檢查側邊欄用戶信息...")
            user_name = page.query_selector(".text-sm.font-medium.text-gray-900").text_content()
            user_email = page.query_selector(".text-xs.text-gray-500").text_content()
            print(f"   用戶名: {user_name}")
            print(f"   Email: {user_email}")
            
            print("\n=== 測試完成 ===")
            print("\n請檢查截圖檔案：")
            print("- individual_01_classrooms.png (教室頁面)")
            print("- individual_02_students.png (學生頁面)")
            print("- individual_03_courses.png (課程頁面)")
            
            print("\n瀏覽器將在 10 秒後關閉...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            page.screenshot(path="individual_error.png")
            print("已保存錯誤截圖: individual_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_individual_pages()