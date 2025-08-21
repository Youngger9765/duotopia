#!/usr/bin/env python3
"""
實際視覺檢查頁面載入狀況
"""
import subprocess
import time
import requests

def check_frontend():
    print("=== 實際檢查前端頁面 ===\n")
    
    # 1. 檢查前端服務是否運行
    try:
        response = requests.get("http://localhost:5173")
        print(f"✓ 前端服務運行中 (狀態碼: {response.status_code})")
    except:
        print("✗ 前端服務未運行")
        return
    
    # 2. 截圖當前頁面狀態
    print("\n正在截圖當前頁面...")
    try:
        # 使用 screencapture 截圖
        subprocess.run([
            "screencapture", 
            "-x",  # 無聲
            "-T", "3",  # 延遲3秒
            "frontend_check.png"
        ])
        print("✓ 截圖已保存為 frontend_check.png")
        
        # 打開截圖
        subprocess.run(["open", "frontend_check.png"])
        print("✓ 已打開截圖供檢查")
    except Exception as e:
        print(f"✗ 截圖失敗: {e}")
    
    # 3. 檢查瀏覽器控制台錯誤
    print("\n請檢查瀏覽器控制台是否有錯誤訊息...")
    print("1. 打開 Chrome 開發者工具 (F12)")
    print("2. 查看 Console 標籤")
    print("3. 檢查是否有紅色錯誤訊息")
    
    # 4. 測試 API 連接
    print("\n檢查 API 連接...")
    try:
        # 登入測試
        login_response = requests.post("http://localhost:8000/api/auth/login", data={
            "username": "teacher@individual.com",
            "password": "test123"
        })
        
        if login_response.status_code == 200:
            print("✓ API 連接正常")
            token = login_response.json()["access_token"]
            
            # 檢查課程 API
            headers = {"Authorization": f"Bearer {token}"}
            courses_response = requests.get("http://localhost:8000/api/individual/courses", headers=headers)
            
            if courses_response.status_code == 200:
                courses = courses_response.json()
                print(f"✓ 課程 API 正常 (找到 {len(courses)} 個課程)")
            else:
                print(f"✗ 課程 API 錯誤: {courses_response.status_code}")
        else:
            print(f"✗ 登入失敗: {login_response.status_code}")
    except Exception as e:
        print(f"✗ API 連接失敗: {e}")
    
    print("\n=== 檢查完成 ===")
    print("請查看：")
    print("1. frontend_check.png - 頁面截圖")
    print("2. 瀏覽器控制台 - 錯誤訊息")
    print("3. 網路標籤 - API 請求狀況")

if __name__ == "__main__":
    check_frontend()