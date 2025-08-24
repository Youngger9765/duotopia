#!/usr/bin/env python3
"""
最終測試課程管理頁面
"""
from playwright.sync_api import sync_playwright
import time

def test_courses_final():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 測試課程管理功能修復 ===\n")
            
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
            
            # 2. 直接跳到課程管理
            print("\n2. 訪問課程管理...")
            page.click('a:has-text("課程管理")')
            page.wait_for_load_state("networkidle")
            time.sleep(3)  # 給 API 更多時間
            
            # 檢查課程計數
            course_count_element = page.query_selector("text=/共.*個課程/")
            if course_count_element:
                course_count_text = course_count_element.text_content()
                print(f"   ✅ 課程計數: {course_count_text}")
                
                if "共 0 個課程" in course_count_text:
                    print("   ❌ 仍然顯示 0 個課程")
                else:
                    print("   ✅ 課程數量正常")
            else:
                print("   ⚠️  找不到課程計數元素")
            
            # 檢查課程列表
            course_items = page.query_selector_all(".border-l-4")  # 課程項目通常有左邊框
            if course_items:
                print(f"   ✅ 找到 {len(course_items)} 個課程項目")
                
                # 顯示課程資訊
                for i, item in enumerate(course_items[:3]):  # 只顯示前3個
                    title = item.query_selector(".font-semibold, .font-bold, h3")
                    description = item.query_selector(".text-gray-600, .text-sm")
                    if title:
                        print(f"   - 課程 {i+1}: {title.text_content()}")
                        if description:
                            print(f"     描述: {description.text_content()}")
            else:
                # 檢查是否有其他課程顯示方式
                course_titles = page.query_selector_all("h3, .font-semibold")
                course_titles = [t for t in course_titles if "課程" in t.text_content() or "英語" in t.text_content()]
                if course_titles:
                    print(f"   ✅ 找到 {len(course_titles)} 個課程標題")
                else:
                    print("   ❌ 沒有找到課程項目")
            
            page.screenshot(path="courses_test_final.png")
            print("   已截圖: courses_test_final.png")
            
            print("\n✅ 測試完成！")
            
            print("\n保持瀏覽器開啟 10 秒供檢查...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 錯誤: {str(e)}")
            page.screenshot(path="courses_test_error.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_courses_final()