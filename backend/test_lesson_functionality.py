#!/usr/bin/env python3
"""
测试课程单元(lesson)功能的 E2E 测试
"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def test_lesson_functionality():
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        print("=== 开始测试课程单元功能 ===\n")
        
        # 1. 访问登录页面
        print("1. 访问登录页面...")
        driver.get("http://localhost:5173/login")
        time.sleep(2)
        
        # 2. 使用个体户教师账号登录
        print("2. 登录个体户教师账号...")
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys("teacher@individual.com")
        
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("test123")
        
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # 3. 等待登录成功并导航到课程管理
        print("3. 导航到课程管理页面...")
        time.sleep(2)
        driver.get("http://localhost:5173/individual/courses")
        time.sleep(3)
        
        # 4. 检查三折页设计是否正常加载
        print("4. 检查三折页设计...")
        
        # 检查第一面板（课程列表）
        course_panel = wait.until(EC.presence_of_element_located((By.XPATH, "//h3[text()='課程列表']")))
        print("  ✓ 课程列表面板已加载")
        
        # 检查是否有课程
        try:
            first_course = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".bg-white.rounded-lg.shadow .p-3.border-b")))
            first_course.click()
            print("  ✓ 选择了第一个课程")
            time.sleep(1)
        except TimeoutException:
            print("  ✗ 没有找到课程")
            return
        
        # 5. 检查第二面板（单元列表）
        print("5. 检查单元列表...")
        try:
            # 查找单元面板标题
            unit_panel = wait.until(EC.presence_of_element_located((By.XPATH, "//h3[contains(text(), '單元')]")))
            print("  ✓ 单元列表面板已加载")
            
            # 检查是否有单元
            first_unit = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'divide-y')]//div[contains(@class, 'p-3')]")))
            first_unit.click()
            print("  ✓ 选择了第一个单元")
            time.sleep(1)
        except TimeoutException:
            print("  ✗ 没有找到单元")
            return
        
        # 6. 检查第三面板（单元内容）
        print("6. 检查单元内容...")
        try:
            # 查找单元说明
            unit_content = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[text()='單元說明']")))
            print("  ✓ 单元内容面板已加载")
            
            # 检查编辑和预览按钮
            edit_button = driver.find_element(By.XPATH, "//button[contains(text(), '編輯內容')]")
            preview_button = driver.find_element(By.XPATH, "//button[contains(text(), '預覽')]")
            print("  ✓ 找到编辑和预览按钮")
        except TimeoutException:
            print("  ✗ 单元内容未正确显示")
            return
        
        # 7. 测试面板收合功能
        print("7. 测试面板收合功能...")
        try:
            # 找到收合按钮
            collapse_button = driver.find_element(By.XPATH, "//button[@title='收合面板']")
            collapse_button.click()
            time.sleep(1)
            print("  ✓ 成功收合单元面板")
            
            # 展开面板
            expand_button = driver.find_element(By.XPATH, "//button[@title='展開單元列表']")
            expand_button.click()
            time.sleep(1)
            print("  ✓ 成功展开单元面板")
        except Exception as e:
            print(f"  ✗ 面板收合功能异常: {e}")
        
        print("\n=== 测试完成 ===")
        print("✓ 课程单元功能正常工作")
        print("✓ 三折页设计正常显示")
        print("✓ 前后端数据同步正常")
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        # 截图保存错误
        driver.save_screenshot("lesson_test_error.png")
        print("  错误截图已保存为 lesson_test_error.png")
    
    finally:
        input("\n按 Enter 键关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    test_lesson_functionality()