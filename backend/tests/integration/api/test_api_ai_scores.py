#!/usr/bin/env python
"""測試 API 是否正確回傳 ai_scores"""
import requests
import json

# 模擬學生登入
print("1. 學生登入...")
login_response = requests.post(
    "http://localhost:8000/api/auth/student/login",
    json={
        "email": "demo@duotopia.com",
        "classroom_id": 1,
        "student_id": "S001",
        "password": "20120101",
    },
)

if login_response.status_code != 200:
    print(f"登入失敗: {login_response.text}")
    exit(1)

token = login_response.json()["access_token"]
print("✅ 登入成功")

# 獲取作業活動列表
print("\n2. 取得活動列表...")
activities_response = requests.get(
    "http://localhost:8000/api/students/assignments/290/activities",
    headers={"Authorization": f"Bearer {token}"},
)

if activities_response.status_code != 200:
    print(f"獲取活動失敗: {activities_response.text}")
    exit(1)

activities = activities_response.json()["activities"]
print(f"✅ 成功取得 {len(activities)} 個活動")

# 檢查是否有 ai_scores
for i, activity in enumerate(activities):
    print(f"\n活動 {i+1} (ID: {activity['id']}):")
    print(f"  - 狀態: {activity['status']}")
    print(f"  - 完成時間: {activity.get('completed_at', 'None')}")

    if activity.get("ai_scores"):
        ai_scores = activity["ai_scores"]
        print("  - AI 評估結果: ✅ 有資料")
        print(f"    * 準確度: {ai_scores.get('accuracy_score', 'N/A')}")
        print(f"    * 流暢度: {ai_scores.get('fluency_score', 'N/A')}")
        print(f"    * 完整度: {ai_scores.get('completeness_score', 'N/A')}")
        print(f"    * 發音分數: {ai_scores.get('pronunciation_score', 'N/A')}")
        if ai_scores.get("word_details"):
            print(f"    * 單字數量: {len(ai_scores['word_details'])}")
    else:
        print("  - AI 評估結果: ❌ 無資料")

print("\n3. 測試完成！")
