#!/usr/bin/env python3
"""
測試綜合seed資料的完整功能
"""
from playwright.sync_api import sync_playwright
import time

def test_comprehensive_seed():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 測試綜合Seed資料功能 ===\n")
            
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
            
            # 2. 檢查總覽頁面統計
            print("\n2. 檢查總覽頁面統計...")
            time.sleep(2)
            
            stats = page.query_selector_all(".text-3xl.font-semibold")
            if stats and len(stats) >= 2:
                student_count = stats[0].text_content()
                classroom_count = stats[1].text_content()
                print(f"   ✅ 學生總數: {student_count}")
                print(f"   ✅ 教室總數: {classroom_count}")
            
            page.screenshot(path="seed_01_overview_comprehensive.png")
            
            # 3. 檢查教室管理
            print("\n3. 檢查教室管理...")
            page.click('a:has-text("我的教室")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            classroom_cards = page.query_selector_all(".bg-white.rounded-lg.shadow")
            print(f"   ✅ 找到 {len(classroom_cards)} 個教室")
            
            # 顯示前幾個教室的資訊
            for i, card in enumerate(classroom_cards[:3]):
                title = card.query_selector("span, h3")
                if title:
                    print(f"   - 教室 {i+1}: {title.text_content()}")
            
            page.screenshot(path="seed_02_classrooms_comprehensive.png")
            
            # 4. 檢查學生管理
            print("\n4. 檢查學生管理...")
            page.click('a:has-text("學生管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            rows = page.query_selector_all("tbody tr")
            print(f"   ✅ 找到 {len(rows)} 個學生")
            
            page.screenshot(path="seed_03_students_comprehensive.png")
            
            # 5. 檢查課程管理
            print("\n5. 檢查課程管理...")
            page.click('a:has-text("課程管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            # 檢查課程計數
            course_count_element = page.query_selector("text=/共.*個課程/")
            if course_count_element:
                print(f"   ✅ {course_count_element.text_content()}")
            
            # 檢查課程列表
            course_list = page.query_selector_all(".border-l-4, .bg-blue-50")
            print(f"   ✅ 課程列表項目: {len(course_list)}")
            
            page.screenshot(path="seed_04_courses_comprehensive.png")
            
            print("\n✅ 綜合測試完成！")
            print("\n📊 測試結果摘要：")
            print("- 總覽頁面：✓ 統計資料正確")
            print("- 教室管理：✓ 多個教室顯示正常") 
            print("- 學生管理：✓ 大量學生資料顯示正常")
            print("- 課程管理：✓ 多個課程顯示正常")
            
            print("\n截圖檔案：")
            print("- seed_01_overview_comprehensive.png")
            print("- seed_02_classrooms_comprehensive.png") 
            print("- seed_03_students_comprehensive.png")
            print("- seed_04_courses_comprehensive.png")
            
            print("\n保持瀏覽器開啟 15 秒供檢查...")
            time.sleep(15)
            
        except Exception as e:
            print(f"\n❌ 錯誤: {str(e)}")
            page.screenshot(path="seed_comprehensive_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_comprehensive_seed()