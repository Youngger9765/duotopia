"""
批次匯入單字集 CSV 到正式環境
使用方式: python import_vocabulary_from_csv.py <csv_file_path>
"""
import csv
import sys
import requests
import getpass
from pathlib import Path

# === 配置 ===
# 選擇執行模式：
# - "vm": 在 VM 上執行，直接連接內部 backend (推薦)
# - "external": 從外部透過 HTTPS 連接 (可能因 CORS 限制失敗)
EXECUTION_MODE = "vm"  # 或 "external"

if EXECUTION_MODE == "vm":
    # 在 VM 上執行，直接連到 backend container
    API_BASE_URL = "http://localhost:8080/api"
else:
    # 從外部執行（注意：可能因 nginx CORS 限制而失敗）
    API_BASE_URL = "https://duotopia.co/api"

TEACHER_EMAIL = "contact@duotopia.co"

def login():
    """登入並取得 token"""
    print(f"\n執行模式: {EXECUTION_MODE}")
    print(f"API URL: {API_BASE_URL}")
    print(f"正在登入 {TEACHER_EMAIL}...")
    
    # 輸入密碼
    password = getpass.getpass(f"請輸入 {TEACHER_EMAIL} 的密碼: ")
    
    login_url = f"{API_BASE_URL}/auth/teacher/login"
    response = requests.post(
        login_url,
        json={
            "email": TEACHER_EMAIL,
            "password": password
        },
        headers={"Content-Type": "application/json"}
    )
    
    print(f"登入請求狀態碼: {response.status_code}")

    
    if response.status_code != 200:
        print(f"❌ 登入失敗: {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    print("✅ 登入成功")
    return token

def get_headers(token):
    """取得API請求標頭"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def get_or_create_course(token, course_name):
    """取得或建立課程"""
    headers = get_headers(token)
    
    # 取得所有課程
    response = requests.get(f"{API_BASE_URL}/teachers/programs", headers=headers)
    programs = response.json()
    
    # 尋找同名課程
    for program in programs:
        if program["title"] == course_name:
            print(f"✅ 找到現有課程: {program['title']} (ID: {program['id']})")
            return program
    
    # 沒有找到，建立新課程
    print(f"📝 建立新課程: {course_name}")
    response = requests.post(
        f"{API_BASE_URL}/teachers/programs",
        headers=headers,
        json={
            "title": course_name,
            "description": f"從 CSV 匯入",
            "is_template": False,
            "is_active": True
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 建立課程失敗: {response.text}")
        sys.exit(1)
    
    program = response.json()
    print(f"✅ 課程已建立 (ID: {program['id']})")
    return program

def get_or_create_lesson(token, program_id, lesson_name):
    """取得或建立單元"""
    headers = get_headers(token)
    
    # 取得課程詳情（包含所有單元）
    response = requests.get(
        f"{API_BASE_URL}/teachers/programs/{program_id}",
        headers=headers
    )
    program = response.json()
    
    # 尋找單元
    for lesson in program.get("lessons", []):
        if lesson["title"] == lesson_name:
            print(f"✅ 找到單元: {lesson['title']} (ID: {lesson['id']})")
            return lesson
    
    # 建立新單元
    print(f"📝 建立新單元: {lesson_name}")
    response = requests.post(
        f"{API_BASE_URL}/teachers/programs/{program_id}/lessons",
        headers=headers,
        json={
            "title": lesson_name,
            "description": f"從 CSV 匯入",
            "order_index": len(program.get("lessons", []))
        }
    )
    
    if response.status_code != 200:
        print(f"❌ 建立單元失敗: {response.text}")
        sys.exit(1)
    
    lesson = response.json()
    print(f"✅ 單元已建立 (ID: {lesson['id']})")
    return lesson

def create_vocabulary_set(token, lesson_id, content_title, level, tags, items):
    """建立單字集"""
    headers = get_headers(token)
    
    print(f"📝 建立單字集: {content_title} ({len(items)} 個單字)")
    
    # 準備資料
    content_data = {
        "type": "VOCABULARY_SET",
        "title": content_title,
        "level": level,
        "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
        "items": items,
        "target_wpm": 60,
        "target_accuracy": 0.8,
        "is_public": False
    }
    
    response = requests.post(
        f"{API_BASE_URL}/teachers/lessons/{lesson_id}/contents",
        headers=headers,
        json=content_data
    )
    
    if response.status_code != 200:
        print(f"❌ 建立單字集失敗: {response.text}")
        return None
    
    content = response.json()
    print(f"✅ 單字集已建立 (ID: {content['id']})")
    return content

def import_csv(csv_file_path):
    """匯入 CSV 檔案"""
    print(f"\n📂 讀取 CSV 檔案: {csv_file_path}")
    
    # 讀取 CSV
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✅ 共讀取 {len(rows)} 筆資料")
    
    # 登入
    token = login()
    
    # 取得課程
    program = get_or_create_course(token, rows[0]['course_name'])
    
    # 按單元和內容分組
    grouped = {}
    for row in rows:
        unit_name = row['unit_name']
        content_title = row['content_title']
        
        if unit_name not in grouped:
            grouped[unit_name] = {}
        
        if content_title not in grouped[unit_name]:
            grouped[unit_name][content_title] = {
                'level': row['level'],
                'tags': row['tags'],
                'items': []
            }
        
        # 準備單字項目
        item = {
            'text': row['text'],
            'translation': row['translation'],
        }
        
        if row.get('part_of_speech'):
            item['parts_of_speech'] = [row['part_of_speech']]
        
        if row.get('example_sentence'):
            item['example_sentence'] = row['example_sentence']
        
        if row.get('example_sentence_translation'):
            item['example_sentence_translation'] = row['example_sentence_translation']
        
        grouped[unit_name][content_title]['items'].append(item)
    
    # 建立內容
    print(f"\n📊 開始建立內容...")
    print(f"   共 {len(grouped)} 個單元")
    
    for unit_name, contents in grouped.items():
        print(f"\n{'='*60}")
        
        # 取得或建立單元
        lesson = get_or_create_lesson(token, program['id'], unit_name)
        
        # 建立單字集
        for content_title, data in contents.items():
            create_vocabulary_set(
                token,
                lesson['id'],
                content_title,
                data['level'],
                data['tags'],
                data['items']
            )
    
    print(f"\n{'='*60}")
    print(f"✅ 匯入完成！")
    print(f"   課程: {program['title']}")
    print(f"   單元數: {len(grouped)}")
    print(f"   單字集數: {sum(len(contents) for contents in grouped.values())}")
    print(f"   總單字數: {len(rows)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方式: python import_vocabulary_from_csv.py <csv_file_path>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"❌ 找不到檔案: {csv_file}")
        sys.exit(1)
    
    import_csv(csv_file)
