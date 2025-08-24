#!/usr/bin/env python3
"""
最終測試個體戶教師的功能
"""
from playwright.sync_api import sync_playwright
import time

def test_final_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 最終測試個體戶教師功能 ===\n")
            
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
            
            # 2. 檢查總覽頁面
            print("\n2. 檢查總覽頁面...")
            time.sleep(2)
            
            # 檢查使用者資訊
            user_name = page.query_selector(".text-sm.font-medium.text-gray-900")
            if user_name:
                print(f"   ✓ 使用者名稱: {user_name.text_content()}")
            
            # 檢查統計數據
            stats = page.query_selector_all(".text-3xl.font-semibold")
            if stats and len(stats) >= 2:
                print(f"   ✓ 學生總數: {stats[0].text_content()}")
                print(f"   ✓ 開課教室: {stats[1].text_content()}")
            
            page.screenshot(path="final_01_overview.png")
            print("   已截圖: final_01_overview.png")
            
            # 3. 檢查教室管理
            print("\n3. 訪問教室管理...")
            page.click('a:has-text("我的教室")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 檢查是否有教室
            no_classrooms = page.query_selector("text=尚未建立任何教室")
            if no_classrooms:
                print("   ⚠️  尚未建立任何教室")
            else:
                cards = page.query_selector_all(".bg-white.rounded-lg.shadow")
                print(f"   ✓ 找到 {len(cards)} 個教室")
                
                # 顯示第一個教室的資訊
                if cards:
                    first_card = cards[0]
                    title = first_card.query_selector("span")
                    if title:
                        print(f"   ✓ 第一個教室: {title.text_content()}")
                    
                    # 檢查學生人數
                    student_info = first_card.query_selector("text=/學生人數/")
                    if student_info:
                        print(f"   ✓ {student_info.text_content()}")
            
            page.screenshot(path="final_02_classrooms.png")
            print("   已截圖: final_02_classrooms.png")
            
            # 4. 檢查學生管理
            print("\n4. 訪問學生管理...")
            page.click('a:has-text("學生管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 檢查是否有學生
            no_students = page.query_selector("text=沒有找到符合條件的學生")
            if no_students:
                print("   ⚠️  沒有找到學生")
            else:
                rows = page.query_selector_all("tbody tr")
                print(f"   ✓ 找到 {len(rows)} 個學生")
            
            page.screenshot(path="final_03_students.png")
            print("   已截圖: final_03_students.png")
            
            # 5. 檢查課程管理
            print("\n5. 訪問課程管理...")
            page.click('a:has-text("課程管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            page.screenshot(path="final_04_courses.png")
            print("   已截圖: final_04_courses.png")
            
            print("\n✅ 測試完成！")
            print("\n截圖檔案：")
            print("- final_01_overview.png (總覽)")
            print("- final_02_classrooms.png (教室管理)")
            print("- final_03_students.png (學生管理)")
            print("- final_04_courses.png (課程管理)")
            
            print("\n瀏覽器將在 10 秒後關閉...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 錯誤: {str(e)}")
            page.screenshot(path="final_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_final_ui()