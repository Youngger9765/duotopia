#!/usr/bin/env python3
"""
Enhanced seed data for individual teacher
- Courses with recording lessons
- Students with mixed password states (default vs custom)
"""
import sys
import os
import uuid
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal
from models import (
    User, Classroom, Student, ClassroomStudent, Course, Lesson,
    ClassroomCourseMapping, DifficultyLevel, ActivityType
)
from auth import get_password_hash

def seed_enhanced_individual_data():
    db = SessionLocal()
    try:
        print("=== 建立增強版個體戶教師測試資料 ===\n")
        
        # 1. 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name}")
        
        # 2. 建立課程（錄音集類型）
        print("\n📚 建立錄音集課程...")
        
        courses_data = [
            {
                "title": "基礎英語發音練習",
                "description": "適合初學者的英語發音基礎訓練",
                "difficulty_level": DifficultyLevel.A1,
                "lessons": [
                    {
                        "title": "字母發音 A-M",
                        "content": {
                            "texts": [
                                {"text": "Apple", "translation": "蘋果", "level": "A1"},
                                {"text": "Ball", "translation": "球", "level": "A1"},
                                {"text": "Cat", "translation": "貓", "level": "A1"},
                                {"text": "Dog", "translation": "狗", "level": "A1"},
                                {"text": "Elephant", "translation": "大象", "level": "A1"},
                                {"text": "Fish", "translation": "魚", "level": "A1"},
                                {"text": "Girl", "translation": "女孩", "level": "A1"},
                                {"text": "House", "translation": "房子", "level": "A1"},
                                {"text": "Ice cream", "translation": "冰淇淋", "level": "A1"},
                                {"text": "Jump", "translation": "跳", "level": "A1"},
                                {"text": "Kite", "translation": "風箏", "level": "A1"},
                                {"text": "Lion", "translation": "獅子", "level": "A1"},
                                {"text": "Moon", "translation": "月亮", "level": "A1"}
                            ],
                            "target_wpm": 60,
                            "target_accuracy": 80
                        }
                    },
                    {
                        "title": "字母發音 N-Z",
                        "content": {
                            "texts": [
                                {"text": "Night", "translation": "夜晚", "level": "A1"},
                                {"text": "Orange", "translation": "橘子", "level": "A1"},
                                {"text": "Pencil", "translation": "鉛筆", "level": "A1"},
                                {"text": "Queen", "translation": "女王", "level": "A1"},
                                {"text": "Rainbow", "translation": "彩虹", "level": "A1"},
                                {"text": "Sun", "translation": "太陽", "level": "A1"},
                                {"text": "Tree", "translation": "樹", "level": "A1"},
                                {"text": "Umbrella", "translation": "雨傘", "level": "A1"},
                                {"text": "Violin", "translation": "小提琴", "level": "A1"},
                                {"text": "Water", "translation": "水", "level": "A1"},
                                {"text": "X-ray", "translation": "X光", "level": "A1"},
                                {"text": "Yellow", "translation": "黃色", "level": "A1"},
                                {"text": "Zebra", "translation": "斑馬", "level": "A1"}
                            ],
                            "target_wpm": 60,
                            "target_accuracy": 80
                        }
                    },
                    {
                        "title": "數字練習 1-20",
                        "content": {
                            "texts": [
                                {"text": "One", "translation": "一", "level": "A1"},
                                {"text": "Two", "translation": "二", "level": "A1"},
                                {"text": "Three", "translation": "三", "level": "A1"},
                                {"text": "Four", "translation": "四", "level": "A1"},
                                {"text": "Five", "translation": "五", "level": "A1"},
                                {"text": "Six", "translation": "六", "level": "A1"},
                                {"text": "Seven", "translation": "七", "level": "A1"},
                                {"text": "Eight", "translation": "八", "level": "A1"},
                                {"text": "Nine", "translation": "九", "level": "A1"},
                                {"text": "Ten", "translation": "十", "level": "A1"}
                            ],
                            "target_wpm": 70,
                            "target_accuracy": 85
                        }
                    }
                ]
            },
            {
                "title": "日常生活短句",
                "description": "常用的日常英語短句練習",
                "difficulty_level": DifficultyLevel.A2,
                "lessons": [
                    {
                        "title": "問候語",
                        "content": {
                            "texts": [
                                {"text": "Good morning!", "translation": "早安！", "level": "A2"},
                                {"text": "How are you?", "translation": "你好嗎？", "level": "A2"},
                                {"text": "Nice to meet you.", "translation": "很高興認識你。", "level": "A2"},
                                {"text": "What's your name?", "translation": "你叫什麼名字？", "level": "A2"},
                                {"text": "My name is John.", "translation": "我叫約翰。", "level": "A2"},
                                {"text": "Thank you very much.", "translation": "非常感謝你。", "level": "A2"},
                                {"text": "You're welcome.", "translation": "不客氣。", "level": "A2"},
                                {"text": "See you later.", "translation": "待會見。", "level": "A2"},
                                {"text": "Have a nice day!", "translation": "祝你有美好的一天！", "level": "A2"},
                                {"text": "Good night!", "translation": "晚安！", "level": "A2"}
                            ],
                            "target_wpm": 80,
                            "target_accuracy": 85
                        }
                    },
                    {
                        "title": "課堂用語",
                        "content": {
                            "texts": [
                                {"text": "May I come in?", "translation": "我可以進來嗎？", "level": "A2"},
                                {"text": "Can you repeat that?", "translation": "你可以再說一次嗎？", "level": "A2"},
                                {"text": "I don't understand.", "translation": "我不懂。", "level": "A2"},
                                {"text": "How do you spell it?", "translation": "怎麼拼？", "level": "A2"},
                                {"text": "What does it mean?", "translation": "這是什麼意思？", "level": "A2"},
                                {"text": "Can I go to the bathroom?", "translation": "我可以去洗手間嗎？", "level": "A2"},
                                {"text": "I have a question.", "translation": "我有問題。", "level": "A2"},
                                {"text": "Is this correct?", "translation": "這樣對嗎？", "level": "A2"}
                            ],
                            "target_wpm": 75,
                            "target_accuracy": 80
                        }
                    }
                ]
            },
            {
                "title": "故事朗讀練習",
                "description": "簡短故事的朗讀訓練",
                "difficulty_level": DifficultyLevel.B1,
                "lessons": [
                    {
                        "title": "The Hungry Cat",
                        "content": {
                            "texts": [
                                {"text": "Once upon a time, there was a hungry cat.", "translation": "從前，有一隻飢餓的貓。", "level": "B1"},
                                {"text": "The cat walked around the house looking for food.", "translation": "貓在房子裡走來走去尋找食物。", "level": "B1"},
                                {"text": "It found a mouse in the kitchen.", "translation": "牠在廚房發現了一隻老鼠。", "level": "B1"},
                                {"text": "The mouse was eating cheese.", "translation": "老鼠正在吃起司。", "level": "B1"},
                                {"text": "The cat tried to catch the mouse.", "translation": "貓試圖抓住老鼠。", "level": "B1"},
                                {"text": "But the mouse was too fast.", "translation": "但是老鼠太快了。", "level": "B1"},
                                {"text": "The mouse ran into a small hole.", "translation": "老鼠跑進一個小洞裡。", "level": "B1"},
                                {"text": "The cat waited outside the hole.", "translation": "貓在洞外等待。", "level": "B1"},
                                {"text": "Finally, the cat gave up and went away.", "translation": "最後，貓放棄了並離開。", "level": "B1"},
                                {"text": "The mouse was safe and happy.", "translation": "老鼠安全又開心。", "level": "B1"}
                            ],
                            "target_wpm": 90,
                            "target_accuracy": 85
                        }
                    }
                ]
            }
        ]
        
        created_courses = []
        for course_data in courses_data:
            # 檢查課程是否已存在
            existing_course = db.query(Course).filter(
                Course.title == course_data["title"],
                Course.created_by == teacher.id
            ).first()
            
            if not existing_course:
                course = Course(
                    id=str(uuid.uuid4()),
                    title=course_data["title"],
                    description=course_data["description"],
                    difficulty_level=course_data["difficulty_level"],
                    created_by=teacher.id
                )
                db.add(course)
                db.flush()
                
                # 建立課程的單元（錄音集）
                for i, lesson_data in enumerate(course_data["lessons"]):
                    lesson = Lesson(
                        id=str(uuid.uuid4()),
                        course_id=course.id,
                        lesson_number=i + 1,
                        title=lesson_data["title"],
                        activity_type=ActivityType.READING_ASSESSMENT,  # 錄音集
                        content=lesson_data["content"],
                        time_limit_minutes=15,
                        target_wpm=lesson_data["content"].get("target_wpm", 70),
                        target_accuracy=lesson_data["content"].get("target_accuracy", 80),
                        is_active=True
                    )
                    db.add(lesson)
                
                created_courses.append(course)
                print(f"  ✓ 建立課程: {course.title} (包含 {len(course_data['lessons'])} 個錄音集單元)")
            else:
                created_courses.append(existing_course)
                print(f"  - 課程已存在: {existing_course.title}")
        
        # 3. 註：學生密碼狀態由認證系統管理，這裡只記錄說明
        print("\n👥 學生密碼狀態說明...")
        
        # 獲取所有屬於這個教師的學生
        students = db.query(Student).join(
            ClassroomStudent
        ).join(
            Classroom
        ).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).distinct().all()
        
        if students:
            # 說明學生密碼狀態（實際狀態由認證系統管理）
            print(f"  共有 {len(students)} 位學生")
            print("  密碼規則：")
            print("  - 預設密碼為生日 (YYYYMMDD 格式)")
            print("  - 學生可在首次登入後修改密碼")
            print("  - 教師可重置學生密碼為預設值")
        
        # 4. 將課程關聯到教室
        print("\n🔗 關聯課程到教室...")
        
        classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).all()
        
        # 為每個教室分配適合的課程
        for classroom in classrooms:
            # 根據教室年級分配課程
            if "基礎" in classroom.name or "三年級" in classroom.grade_level:
                course_to_assign = next((c for c in created_courses if "基礎英語發音" in c.title), None)
            elif "進階" in classroom.name or "五年級" in classroom.grade_level:
                course_to_assign = next((c for c in created_courses if "日常生活短句" in c.title), None)
            else:
                course_to_assign = next((c for c in created_courses if "故事朗讀" in c.title), None)
            
            if course_to_assign:
                # 檢查是否已關聯
                existing_mapping = db.query(ClassroomCourseMapping).filter(
                    ClassroomCourseMapping.classroom_id == classroom.id,
                    ClassroomCourseMapping.course_id == course_to_assign.id
                ).first()
                
                if not existing_mapping:
                    mapping = ClassroomCourseMapping(
                        id=str(uuid.uuid4()),
                        classroom_id=classroom.id,
                        course_id=course_to_assign.id
                    )
                    db.add(mapping)
                    print(f"  ✓ {classroom.name} → {course_to_assign.title}")
        
        db.commit()
        
        print("\n✅ 增強版種子資料建立完成！")
        print(f"   - 建立了 {len(created_courses)} 個錄音集課程")
        print(f"   - 確認了 {len(students)} 個學生")
        print(f"   - 關聯了課程到 {len(classrooms)} 個教室")
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_enhanced_individual_data()