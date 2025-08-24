#!/usr/bin/env python3
"""
完整測試個體戶教師登入和資料顯示
"""
from playwright.sync_api import sync_playwright
import time
import sys

def test_individual_teacher_complete():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("=== 開始測試個體戶教師功能 ===\n")
            
            # 1. 訪問登入頁面
            print("1. 訪問登入頁面...")
            page.goto("http://localhost:5173/login")
            page.wait_for_load_state("networkidle")
            time.sleep(1)
            
            # 2. 清除任何現有的登入狀態
            print("2. 清除現有登入狀態...")
            page.evaluate("""() => {
                localStorage.clear();
                sessionStorage.clear();
            }""")
            page.reload()
            page.wait_for_load_state("networkidle")
            
            # 3. 填寫登入表單
            print("3. 填寫個體戶教師登入資訊...")
            page.fill('input[type="email"]', "teacher@individual.com")
            page.fill('input[type="password"]', "password123")
            
            # 截圖登入頁面
            page.screenshot(path="01_login_form_filled.png")
            print("   ✓ 已截圖: 01_login_form_filled.png")
            
            # 4. 監聽控制台錯誤
            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
            
            # 5. 點擊登入按鈕
            print("4. 點擊登入按鈕...")
            page.click('button[type="submit"]')
            
            # 6. 等待登入完成
            print("5. 等待登入處理...")
            time.sleep(3)  # 給登入一些時間
            
            # 檢查控制台日誌
            if console_logs:
                print("\n控制台日誌:")
                for log in console_logs:
                    print(f"  {log}")
            
            # 檢查當前 URL
            current_url = page.url
            print(f"   當前 URL: {current_url}")
            
            # 6. 檢查是否成功導航
            if "/individual" in current_url:
                print("   ✓ 成功導航到個體戶儀表板")
                
                # 等待頁面完全載入
                page.wait_for_load_state("networkidle")
                time.sleep(2)
                
                # 7. 截圖儀表板
                page.screenshot(path="02_individual_dashboard.png")
                print("\n6. 已截圖個體戶儀表板: 02_individual_dashboard.png")
                
                # 8. 檢查使用者資料顯示
                print("\n7. 檢查使用者資料顯示...")
                
                # 尋找並打印所有包含使用者資訊的元素
                user_info_selectors = [
                    ".text-sm.font-medium.text-gray-900",
                    ".text-xs.text-gray-500",
                    ".text-xs.text-gray-400"
                ]
                
                for selector in user_info_selectors:
                    elements = page.query_selector_all(selector)
                    for element in elements:
                        text = element.text_content()
                        if text and text.strip():
                            print(f"   找到文字: {text.strip()}")
                
                # 9. 檢查 localStorage
                print("\n8. 檢查 localStorage 資料...")
                storage_data = page.evaluate("""() => {
                    return {
                        token: localStorage.getItem('token') ? '已設置' : '未設置',
                        userEmail: localStorage.getItem('userEmail'),
                        userFullName: localStorage.getItem('userFullName'),
                        userId: localStorage.getItem('userId'),
                        userRole: localStorage.getItem('userRole')
                    };
                }""")
                
                for key, value in storage_data.items():
                    print(f"   - {key}: {value}")
                
                # 10. 點擊側邊欄展開/收合按鈕
                print("\n9. 測試側邊欄功能...")
                chevron_button = page.query_selector('button svg.w-5.h-5')
                if chevron_button:
                    chevron_button.click()
                    time.sleep(1)
                    page.screenshot(path="03_sidebar_collapsed.png")
                    print("   ✓ 已截圖收合的側邊欄: 03_sidebar_collapsed.png")
                    
                    # 再次點擊展開
                    chevron_button.click()
                    time.sleep(1)
                
                print("\n✅ 測試完成！")
                print("\n請檢查截圖檔案：")
                print("1. 01_login_form_filled.png - 登入表單")
                print("2. 02_individual_dashboard.png - 個體戶儀表板")
                print("3. 03_sidebar_collapsed.png - 收合的側邊欄")
                
            elif "/teacher" in current_url:
                print("   ⚠️  被導航到一般教師儀表板")
                page.screenshot(path="wrong_dashboard.png")
                print("   已截圖: wrong_dashboard.png")
                
            elif "/login" in current_url:
                print("   ❌ 仍在登入頁面，登入可能失敗")
                # 檢查是否有錯誤訊息
                error_msg = page.query_selector('.text-red-500')
                if error_msg:
                    print(f"   錯誤訊息: {error_msg.text_content()}")
                page.screenshot(path="login_failed.png")
                print("   已截圖: login_failed.png")
            
            else:
                print(f"   ❓ 未預期的頁面: {current_url}")
                page.screenshot(path="unexpected_page.png")
                
            # 保持瀏覽器開啟供檢查
            print("\n瀏覽器將在 10 秒後關閉...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
            page.screenshot(path="error_screenshot.png")
            print("   已保存錯誤截圖: error_screenshot.png")
            raise
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_individual_teacher_complete()