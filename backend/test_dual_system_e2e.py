#!/usr/bin/env python3
"""
雙體系 E2E 測試
測試機構管理和個體戶管理的所有頁面
"""
from playwright.sync_api import sync_playwright
import time

BASE_URL = "http://localhost:5173"

# 測試帳號
ACCOUNTS = {
    "institutional": {
        "email": "admin@institution.com",
        "password": "test123",
        "name": "機構管理員"
    },
    "individual": {
        "email": "teacher@individual.com", 
        "password": "test123",
        "name": "個體戶教師"
    },
    "hybrid": {
        "email": "hybrid@test.com",
        "password": "test123", 
        "name": "混合型用戶"
    }
}

def login(page, account_type):
    """登入指定帳號"""
    account = ACCOUNTS[account_type]
    print(f"\n登入 {account['name']}...")
    
    page.goto(f"{BASE_URL}/login")
    time.sleep(1)
    
    # 使用測試帳號按鈕
    if account_type == "institutional":
        page.click("text=機構管理員")
    elif account_type == "individual":
        page.click("text=個體戶教師")
    elif account_type == "hybrid":
        page.click("text=混合型使用者")
    
    time.sleep(1)
    page.click("button[type='submit']")
    
    # 等待導航完成
    page.wait_for_load_state("networkidle")
    time.sleep(3)
    
    print(f"當前URL: {page.url}")

def test_institutional_system(page):
    """測試機構管理系統"""
    print("\n=== 測試機構管理系統 ===")
    
    # 1. 登入機構管理員
    login(page, "institutional")
    
    # 檢查是否進入正確頁面
    if "/institutional" in page.url:
        print("✓ 成功進入機構管理系統")
    else:
        # 可能需要手動導航
        page.goto(f"{BASE_URL}/institutional")
        time.sleep(2)
    
    # 2. 測試學校管理
    print("\n2. 測試學校管理...")
    page.click("text=學校管理")
    time.sleep(2)
    
    # 檢查是否有學校列表
    schools = page.locator("text=台北市立大安國小").count()
    if schools > 0:
        print("✓ 學校列表顯示正常")
    else:
        print("✗ 無法看到學校列表")
    
    # 3. 測試教室管理
    print("\n3. 測試教室管理...")
    page.click("text=教室管理")
    time.sleep(2)
    
    # 檢查教室數量
    classrooms = page.locator("text=/.*班$/").count()
    print(f"✓ 找到 {classrooms} 個教室")
    
    # 4. 測試學生管理
    print("\n4. 測試學生管理...")
    page.click("text=學生管理")
    time.sleep(2)
    
    # 檢查學生列表
    students = page.locator("text=/學生\\d+/").count()
    print(f"✓ 找到 {students} 個學生")
    
    # 5. 測試課程管理
    print("\n5. 測試課程管理...")
    page.click("text=課程管理")
    time.sleep(2)
    
    # 檢查課程列表
    courses = page.locator("text=/.*課程.*/").count()
    print(f"✓ 找到 {courses} 個課程")

def test_individual_system(page):
    """測試個體戶系統"""
    print("\n=== 測試個體戶系統 ===")
    
    # 1. 登入個體戶教師
    login(page, "individual")
    
    # 檢查是否進入正確頁面
    if "/individual" in page.url:
        print("✓ 成功進入個體戶系統")
    else:
        # 可能需要手動導航
        page.goto(f"{BASE_URL}/individual")
        time.sleep(2)
    
    # 2. 測試我的教室
    print("\n2. 測試我的教室...")
    page.click("text=我的教室")
    time.sleep(2)
    
    # 檢查教室列表
    classrooms = page.locator("text=/.*班$/").count()
    print(f"✓ 找到 {classrooms} 個個人教室")
    
    # 檢查是否顯示價格
    pricing = page.locator("text=/$\\d+/").count()
    if pricing > 0:
        print("✓ 顯示收費資訊")
    
    # 3. 測試學生管理
    print("\n3. 測試學生管理...")
    page.click("text=學生管理")
    time.sleep(2)
    
    # 檢查個人學生
    students = page.locator("text=/個人學生\\d+/").count()
    print(f"✓ 找到 {students} 個個人學生")
    
    # 4. 測試課程管理
    print("\n4. 測試課程管理...")
    page.click("text=課程管理")
    time.sleep(2)
    
    # 檢查個人課程
    courses = page.locator("text=/.*英語.*|.*數學.*|.*寫作.*/").count()
    print(f"✓ 找到 {courses} 個個人課程")
    
    # 5. 測試收費管理
    print("\n5. 測試收費管理...")
    if page.locator("text=收費管理").count() > 0:
        page.click("text=收費管理")
        time.sleep(2)
        print("✓ 收費管理頁面存在")

def test_role_switching(page):
    """測試角色切換"""
    print("\n=== 測試角色切換 ===")
    
    # 1. 登入混合型用戶
    login(page, "hybrid")
    time.sleep(2)
    
    # 2. 檢查是否有角色切換器
    print("\n2. 檢查角色切換器...")
    role_switcher = page.locator("text=/機構管理|個人教師|個體戶教師/").first
    
    if role_switcher.count() > 0:
        print("✓ 找到角色切換器")
        
        # 3. 切換到機構管理
        print("\n3. 切換到機構管理...")
        role_switcher.click()
        time.sleep(1)
        
        if page.locator("text=機構管理").count() > 0:
            page.click("text=機構管理")
            time.sleep(3)
            
            # 檢查導航選單
            if page.locator("text=學校管理").count() > 0:
                print("✓ 成功切換到機構管理模式")
            else:
                print("✗ 切換失敗")
        
        # 4. 切換回個體戶
        print("\n4. 切換到個體戶...")
        role_switcher = page.locator("text=/機構管理|個人教師|個體戶教師/").first
        if role_switcher.count() > 0:
            role_switcher.click()
            time.sleep(1)
            
            if page.locator("text=/個人教師|個體戶/").count() > 0:
                page.click("text=/個人教師|個體戶/")
                time.sleep(3)
                
                # 檢查導航選單
                if page.locator("text=我的教室").count() > 0:
                    print("✓ 成功切換到個體戶模式")
                else:
                    print("✗ 切換失敗")
    else:
        print("✗ 沒有找到角色切換器")

def test_navigation_differences(page):
    """測試不同角色看到的導航差異"""
    print("\n=== 測試導航選單差異 ===")
    
    # 1. 機構管理員導航
    print("\n1. 機構管理員導航...")
    login(page, "institutional")
    
    nav_items = {
        "學校管理": False,
        "教室管理": False,
        "學生管理": False,
        "課程管理": False,
        "我的教室": False,
        "收費管理": False
    }
    
    for item in nav_items:
        if page.locator(f"text={item}").count() > 0:
            nav_items[item] = True
    
    print("機構管理員看到的選單：")
    for item, visible in nav_items.items():
        print(f"  {item}: {'✓' if visible else '✗'}")
    
    # 2. 個體戶教師導航
    print("\n2. 個體戶教師導航...")
    login(page, "individual")
    
    nav_items = {
        "學校管理": False,
        "教室管理": False,
        "學生管理": False,
        "課程管理": False,
        "我的教室": False,
        "收費管理": False
    }
    
    for item in nav_items:
        if page.locator(f"text={item}").count() > 0:
            nav_items[item] = True
    
    print("個體戶教師看到的選單：")
    for item, visible in nav_items.items():
        print(f"  {item}: {'✓' if visible else '✗'}")

def run_all_tests():
    """執行所有測試"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=300  # 稍微放慢速度以便觀察
        )
        context = browser.new_context(
            viewport={'width': 1400, 'height': 900}
        )
        page = context.new_page()
        
        # 監聽控制台消息
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        
        # 監聽網路請求
        def handle_response(response):
            if response.status >= 400:
                print(f"HTTP {response.status} {response.url}")
        
        page.on("response", handle_response)
        
        try:
            print("=== 開始雙體系 E2E 測試 ===")
            
            # 執行各項測試
            test_institutional_system(page)
            test_individual_system(page)
            test_role_switching(page)
            test_navigation_differences(page)
            
            print("\n=== 測試完成 ===")
            
        except Exception as e:
            print(f"\n錯誤：{e}")
            page.screenshot(path="error_screenshot.png")
            print("已儲存錯誤截圖")
        
        finally:
            print("\n5秒後關閉瀏覽器...")
            time.sleep(5)
            browser.close()

if __name__ == "__main__":
    run_all_tests()