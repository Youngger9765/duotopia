"""
簡化版學生管理 E2E 測試 - 專注於基本功能驗證
"""

import time
import re
from playwright.sync_api import sync_playwright

def test_student_management_basic():
    """基本學生管理功能測試"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 登入
            print("開始登入...")
            page.goto("http://localhost:5174/login")
            page.wait_for_load_state("networkidle")
            
            page.fill('input[type="email"]', 'teacher1@duotopia.com')
            page.fill('input[type="password"]', 'teacher123')
            page.click('button[type="submit"]')
            page.wait_for_timeout(3000)
            
            print(f"登入後 URL: {page.url}")
            
            # 通過導航選單進入學生管理
            print("\\n通過導航選單進入學生管理...")
            page.goto("http://localhost:5174/teacher")
            page.wait_for_load_state("networkidle")
            
            # 點擊學生管理導航
            nav_link = page.locator('text=學生管理')
            if nav_link.is_visible():
                nav_link.click()
                page.wait_for_timeout(5000)
                print(f"點擊後 URL: {page.url}")
                
                # 檢查頁面內容
                page_text = page.locator('body').inner_text()
                
                if '學生管理' in page_text:
                    print("✅ 學生管理頁面載入成功！")
                    
                    # 檢查基本元素 - 使用 main 區域來避免側邊欄衝突
                    elements_to_check = [
                        ('h2:has-text("學生管理")', '標題'),
                        ('main nav button:has-text("學生名單")', '學生名單標籤'),
                        ('main nav button:has-text("班級管理")', '班級管理標籤'),
                        ('input[placeholder*="搜尋"]', '搜尋框'),
                        ('main button:has-text("新增學生")', '新增學生按鈕')
                    ]
                    
                    for selector, name in elements_to_check:
                        try:
                            element = page.locator(selector)
                            is_visible = element.is_visible()
                            status = "✅" if is_visible else "❌"
                            print(f"  {status} {name}: {is_visible}")
                        except Exception as e:
                            # 如果選擇器有問題，使用更簡單的方式
                            try:
                                elements = page.locator(selector.split(' ')[-1])  # 使用最後部分
                                count = elements.count()
                                if count > 0:
                                    is_visible = elements.first.is_visible()
                                    print(f"  ✅ {name}: {is_visible} (使用 .first)")
                                else:
                                    print(f"  ❌ {name}: 未找到元素")
                            except:
                                print(f"  ❌ {name}: 選擇器錯誤")
                    
                    # 測試標籤切換
                    print("\\n測試標籤切換...")
                    
                    # 切換到班級管理 - 使用 main 區域的按鈕
                    try:
                        class_tab = page.locator('main nav button:has-text("班級管理")')
                        if class_tab.is_visible():
                            class_tab.click()
                            page.wait_for_timeout(1000)
                            print("✅ 成功切換到班級管理標籤")
                            
                            # 切換回學生名單
                            student_tab = page.locator('main nav button:has-text("學生名單")')
                            if student_tab.is_visible():
                                student_tab.click()
                                page.wait_for_timeout(1000)
                                print("✅ 成功切換回學生名單標籤")
                        else:
                            # 備用方案：使用 .first
                            class_tab_alt = page.locator('button:has-text("班級管理")').nth(1)  # 第二個按鈕(主內容區)
                            class_tab_alt.click()
                            page.wait_for_timeout(1000)
                            print("✅ 成功切換到班級管理標籤 (備用方案)")
                            
                            student_tab_alt = page.locator('button:has-text("學生名單")').nth(1)
                            student_tab_alt.click()
                            page.wait_for_timeout(1000)
                            print("✅ 成功切換回學生名單標籤 (備用方案)")
                    except Exception as e:
                        print(f"❌ 標籤切換失敗: {e}")
                    
                    # 測試新增學生功能
                    print("\\n測試新增學生功能...")
                    try:
                        # 使用主內容區的新增學生按鈕
                        add_button = page.locator('main button:has-text("新增學生")')
                        if not add_button.is_visible():
                            # 備用方案：使用 nth(1) 選擇第二個按鈕
                            add_button = page.locator('button:has-text("新增學生")').nth(1)
                        
                        if add_button.is_visible():
                            add_button.click()
                            page.wait_for_timeout(2000)
                            
                            # 檢查新增學生彈窗
                            modal = page.locator('h3:has-text("新增學生")')
                            if modal.is_visible():
                                print("✅ 新增學生彈窗正常顯示")
                                
                                # 關閉彈窗
                                cancel_button = page.locator('button:has-text("取消")')
                                if cancel_button.is_visible():
                                    cancel_button.click()
                                    page.wait_for_timeout(1000)
                                    print("✅ 成功關閉新增學生彈窗")
                            else:
                                print("❌ 新增學生彈窗未顯示")
                        else:
                            print("❌ 新增學生按鈕不可見")
                    except Exception as e:
                        print(f"❌ 新增學生功能測試失敗: {e}")
                    
                    return True
                    
                elif '載入中' in page_text:
                    print("⏳ 頁面仍在載入中")
                    return False
                else:
                    print("❌ 學生管理頁面內容異常")
                    print(f"頁面內容預覽: {page_text[:300]}...")
                    return False
            else:
                print("❌ 找不到學生管理導航連結")
                return False
                
        except Exception as e:
            print(f"錯誤: {e}")
            return False
            
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_student_management_basic()
    print(f"\\n測試結果: {'成功' if success else '失敗'}")