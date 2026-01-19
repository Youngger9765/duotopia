"""
Stage 4: Program/Lesson/Content Setup
Creates programs, lessons, contents, and content items
"""
from seed_data.utils import *


def seed_programs(db: Session, users_data: dict):
    """
    Stage 4: Create programs, lessons, contents, and content items

    Args:
        users_data: Dictionary from Stage 1 containing teachers

    Returns:
        dict: Dictionary containing created programs, lessons, contents
    """
    demo_teacher = users_data["demo_teacher"]

    # ============ 5. Demo 課程（三層結構）============
    # 五年級A班課程
    program_5a_basic = Program(
        name="五年級英語基礎課程",
        description="適合五年級學生的基礎英語課程",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_a.id,
        estimated_hours=20,
        order_index=1,
        is_active=True,
    )

    program_5a_conversation = Program(
        name="五年級口語會話課程",
        description="培養五年級學生的英語口語能力",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_a.id,
        estimated_hours=15,
        order_index=2,
        is_active=True,
    )

    # 六年級B班課程
    program_6b_advanced = Program(
        name="六年級英語進階課程",
        description="適合六年級學生的進階英語課程",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_b.id,
        estimated_hours=25,
        order_index=1,
        is_active=True,
    )

    db.add_all([program_5a_basic, program_5a_conversation, program_6b_advanced])
    db.commit()
    print("✅ 建立 3 個課程計畫")

    # 5.1 為每個學校班級創建課程
    school_programs = []
    for idx, (classroom, school) in enumerate(school_classrooms):
        school_prefix, _ = school_names_prefixes[idx]
        program = Program(
            name=f"{school_prefix}-基礎課程",
            description=f"{classroom.name}的英語課程",
            level=classroom.level,
            teacher_id=classroom.teacher_id,
            classroom_id=classroom.id,
            estimated_hours=20,
            order_index=1,
            is_active=True,
        )
        school_programs.append(program)
        db.add(program)

    db.commit()
    for p in school_programs:
        db.refresh(p)
    print(f"✅ 建立 {len(school_programs)} 個學校課程（每個班級一個課程）")

    # ============ 6. Lessons 和 Contents ============
    # 五年級基礎課程的 Lessons
    lessons_5a_basic = [
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 1: Greetings 打招呼",
            description="學習基本的英語問候語",
            order_index=1,
            estimated_minutes=30,
            is_active=True,
        ),
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 2: Numbers 數字",
            description="學習數字 1-20",
            order_index=2,
            estimated_minutes=30,
            is_active=True,
        ),
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 3: Colors 顏色",
            description="學習各種顏色的英文",
            order_index=3,
            estimated_minutes=25,
            is_active=True,
        ),
    ]

    # 五年級會話課程的 Lessons
    lessons_5a_conversation = [
        Lesson(
            program_id=program_5a_conversation.id,
            name="Unit 1: Self Introduction 自我介紹",
            description="學習如何用英語自我介紹",
            order_index=1,
            estimated_minutes=35,
            is_active=True,
        ),
        Lesson(
            program_id=program_5a_conversation.id,
            name="Unit 2: Daily Routines 日常作息",
            description="談論每日的活動安排",
            order_index=2,
            estimated_minutes=30,
            is_active=True,
        ),
    ]

    # 六年級進階課程的 Lessons
    lessons_6b_advanced = [
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 1: Daily Conversation 日常對話",
            description="學習日常英語對話",
            order_index=1,
            estimated_minutes=40,
            is_active=True,
        ),
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 2: My Family 我的家庭",
            description="學習家庭成員相關詞彙",
            order_index=2,
            estimated_minutes=40,
            is_active=True,
        ),
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 3: Hobbies 興趣愛好",
            description="談論個人興趣與嗜好",
            order_index=3,
            estimated_minutes=35,
            is_active=True,
        ),
    ]

    db.add_all(lessons_5a_basic + lessons_5a_conversation + lessons_6b_advanced)
    db.commit()
    print("✅ 建立 8 個課程單元")

    # 為每個 Lesson 建立 Contents
    contents = []

    # 五年級基礎課程內容
    content1_5a = Content(
        lesson_id=lessons_5a_basic[0].id,
        type=ContentType.READING_ASSESSMENT,
        title="基礎問候語練習",
        order_index=1,
        is_public=True,
        target_wpm=50,
        target_accuracy=0.75,
        time_limit_seconds=180,
        level="A1",
        tags=["greeting", "basic"],
        is_active=True,
    )
    contents.append(content1_5a)

    content2_5a = Content(
        lesson_id=lessons_5a_basic[0].id,
        type=ContentType.READING_ASSESSMENT,
        title="進階問候語練習",
        order_index=2,
        is_public=True,
        target_wpm=55,
        target_accuracy=0.75,
        time_limit_seconds=180,
        level="A1",
        tags=["greeting", "basic"],
        is_active=True,
    )
    contents.append(content2_5a)

    content3_5a = Content(
        lesson_id=lessons_5a_basic[1].id,
        type=ContentType.READING_ASSESSMENT,
        title="數字 1-10 練習",
        order_index=1,
        is_public=True,
        target_wpm=60,
        target_accuracy=0.80,
        time_limit_seconds=120,
        level="A1",
        tags=["numbers", "basic"],
        is_active=True,
    )
    contents.append(content3_5a)

    content4_5a = Content(
        lesson_id=lessons_5a_basic[2].id,
        type=ContentType.READING_ASSESSMENT,
        title="顏色練習",
        order_index=1,
        is_public=True,
        target_wpm=55,
        target_accuracy=0.75,
        time_limit_seconds=150,
        level="A1",
        tags=["colors", "basic"],
        is_active=True,
    )
    contents.append(content4_5a)

    # 五年級會話課程內容
    content5_5a = Content(
        lesson_id=lessons_5a_conversation[0].id,
        type=ContentType.READING_ASSESSMENT,
        title="自我介紹練習",
        order_index=1,
        is_public=False,
        target_wpm=65,
        target_accuracy=0.80,
        time_limit_seconds=180,
        level="A1",
        tags=["introduction", "conversation"],
        is_active=True,
    )
    contents.append(content5_5a)

    # 六年級進階課程內容
    content1_6b = Content(
        lesson_id=lessons_6b_advanced[0].id,
        type=ContentType.READING_ASSESSMENT,
        title="日常對話練習 Part 1",
        order_index=1,
        is_public=False,
        target_wpm=70,
        target_accuracy=0.85,
        time_limit_seconds=180,
        level="A2",
        tags=["conversation", "daily"],
        is_active=True,
    )
    contents.append(content1_6b)

    content2_6b = Content(
        lesson_id=lessons_6b_advanced[0].id,
        type=ContentType.READING_ASSESSMENT,
        title="日常對話練習 Part 2",
        order_index=2,
        is_public=False,
        target_wpm=75,
        target_accuracy=0.85,
        time_limit_seconds=180,
        level="A2",
        tags=["conversation", "hobbies"],
        is_active=True,
    )
    contents.append(content2_6b)

    content3_6b = Content(
        lesson_id=lessons_6b_advanced[1].id,
        type=ContentType.READING_ASSESSMENT,
        title="家庭成員練習",
        order_index=1,
        is_public=False,
        target_wpm=75,
        target_accuracy=0.85,
        time_limit_seconds=150,
        level="A2",
        tags=["family", "vocabulary"],
        is_active=True,
    )
    contents.append(content3_6b)

    db.add_all(contents)
    db.commit()
    print(f"✅ 建立 {len(contents)} 個課程內容")

    # ============ 6.5 建立 ContentItem ============
    print("\n📝 建立 ContentItem 資料...")

    # 定義所有 Content 的 items（因為 Content.items 欄位已移除）
    # 這裡先定義幾個主要的，其他的會從資料庫遷移
    content_items_data = {
        "基礎問候語練習": [
            {"text": "Hello", "translation": "你好"},
            {"text": "Good morning", "translation": "早安"},
            {"text": "Good afternoon", "translation": "午安"},
            {"text": "How are you?", "translation": "你好嗎？"},
            {"text": "I'm fine, thank you", "translation": "我很好，謝謝"},
        ],
        "進階問候語練習": [
            {"text": "Nice to meet you", "translation": "很高興認識你"},
            {"text": "See you later", "translation": "待會見"},
            {"text": "Have a nice day", "translation": "祝你有美好的一天"},
            {"text": "Take care", "translation": "保重"},
            {"text": "Goodbye", "translation": "再見"},
        ],
        "數字 1-10 練習": [
            {"text": "One, Two, Three", "translation": "一、二、三"},
            {"text": "Four, Five, Six", "translation": "四、五、六"},
            {"text": "Seven, Eight", "translation": "七、八"},
            {"text": "Nine, Ten", "translation": "九、十"},
            {"text": "I have five apples", "translation": "我有五個蘋果"},
        ],
        "顏色練習": [
            {"text": "Red and Blue", "translation": "紅色和藍色"},
            {"text": "Green and Yellow", "translation": "綠色和黃色"},
            {"text": "Black and White", "translation": "黑色和白色"},
            {"text": "The sky is blue", "translation": "天空是藍色的"},
            {"text": "I like green", "translation": "我喜歡綠色"},
        ],
        "自我介紹練習": [
            {"text": "My name is John", "translation": "我的名字是約翰"},
            {"text": "I am ten years old", "translation": "我十歲"},
            {"text": "I live in Taipei", "translation": "我住在台北"},
            {"text": "I like playing games", "translation": "我喜歡玩遊戲"},
            {"text": "Nice to meet you all", "translation": "很高興認識大家"},
        ],
        "日常對話練習 Part 1": [
            {"text": "What time is it?", "translation": "現在幾點？"},
            {"text": "It's three o'clock", "translation": "現在三點"},
            {"text": "Where are you going?", "translation": "你要去哪裡？"},
            {"text": "I'm going to school", "translation": "我要去學校"},
            {"text": "See you tomorrow", "translation": "明天見"},
        ],
        # Program ID 4: 初級英語會話課程
        "Basic Greetings 基本問候語": [
            {"text": "Hello, how are you?", "translation": "你好，你好嗎？"},
            {"text": "I'm fine, thank you", "translation": "我很好，謝謝"},
            {"text": "Good morning", "translation": "早安"},
            {"text": "Good afternoon", "translation": "午安"},
            {"text": "Good evening", "translation": "晚安"},
        ],
        "My Daily Routine 我的日常作息": [
            {"text": "I wake up at seven", "translation": "我七點起床"},
            {"text": "I brush my teeth", "translation": "我刷牙"},
            {"text": "I eat breakfast", "translation": "我吃早餐"},
            {"text": "I go to school", "translation": "我去上學"},
            {"text": "I do my homework", "translation": "我做功課"},
        ],
        "Shopping Vocabulary 購物詞彙": [
            {"text": "How much is this?", "translation": "這個多少錢？"},
            {"text": "It's ten dollars", "translation": "十塊錢"},
            {"text": "Can I try it on?", "translation": "我可以試穿嗎？"},
            {"text": "Do you have a smaller size?", "translation": "有小一點的尺寸嗎？"},
            {"text": "I'll take it", "translation": "我要買這個"},
        ],
        "Restaurant English 餐廳英語": [
            {"text": "May I see the menu?", "translation": "我可以看菜單嗎？"},
            {"text": "I'd like to order", "translation": "我想要點餐"},
            {"text": "What do you recommend?", "translation": "你推薦什麼？"},
            {"text": "Can I have the bill?", "translation": "可以結帳嗎？"},
            {"text": "The food was delicious", "translation": "食物很美味"},
        ],
        # Program ID 5: 中級英語閱讀理解
        "Reading Strategies 閱讀策略": [
            {"text": "Find the main idea", "translation": "找出主要概念"},
            {"text": "Look for key words", "translation": "尋找關鍵字"},
            {"text": "Understand context clues", "translation": "理解上下文線索"},
            {"text": "Make predictions", "translation": "進行預測"},
            {"text": "Summarize the text", "translation": "總結文章"},
        ],
        "News Headlines 新聞標題": [
            {"text": "Breaking news today", "translation": "今日突發新聞"},
            {"text": "Weather forecast shows rain", "translation": "天氣預報顯示有雨"},
            {"text": "Sports team wins championship", "translation": "運動隊贏得冠軍"},
            {"text": "New technology announced", "translation": "新科技發布"},
            {"text": "Market prices increase", "translation": "市場價格上漲"},
        ],
        "Story Elements 故事元素": [
            {"text": "The main character", "translation": "主角"},
            {"text": "Setting of the story", "translation": "故事背景"},
            {"text": "Plot development", "translation": "情節發展"},
            {"text": "Climax of the story", "translation": "故事高潮"},
            {"text": "Story resolution", "translation": "故事結局"},
        ],
        # Program ID 6: 英語發音訓練課程
        "Vowel Sounds 母音發音": [
            {"text": "Cat, bat, sat", "translation": "貓、蝙蝠、坐"},
            {"text": "See, bee, tree", "translation": "看、蜜蜂、樹"},
            {"text": "Go, no, so", "translation": "去、不、所以"},
            {"text": "Book, cook, look", "translation": "書、煮、看"},
            {"text": "Blue, true, new", "translation": "藍色、真的、新的"},
        ],
        "Consonant Sounds 子音發音": [
            {"text": "Pet, put, pot", "translation": "寵物、放、鍋子"},
            {"text": "Big, bag, bug", "translation": "大、包、蟲"},
            {"text": "Think, thing, thank", "translation": "想、東西、謝謝"},
            {"text": "Fish, wish, dish", "translation": "魚、希望、盤子"},
            {"text": "Red, run, rain", "translation": "紅色、跑、雨"},
        ],
        "Word Stress 重音練習": [
            {"text": "TEAcher, STUdent", "translation": "老師、學生"},
            {"text": "comPUter, umBRElla", "translation": "電腦、雨傘"},
            {"text": "HOSpital, LIbrary", "translation": "醫院、圖書館"},
            {"text": "imPORtant, inTEresting", "translation": "重要的、有趣的"},
            {"text": "phoTOgraphy, geOgraphy", "translation": "攝影、地理"},
        ],
        # Program ID 7: 商務英語入門
        "Business Email Writing 商務郵件": [
            {"text": "Dear Mr. Smith", "translation": "親愛的史密斯先生"},
            {"text": "I hope this email finds you well", "translation": "希望您一切安好"},
            {"text": "Please find attached", "translation": "請查收附件"},
            {"text": "Looking forward to your reply", "translation": "期待您的回覆"},
            {"text": "Best regards", "translation": "最誠摯的問候"},
        ],
        "Meeting English 會議英語": [
            {"text": "Let's begin the meeting", "translation": "讓我們開始會議"},
            {"text": "Could you elaborate on that?", "translation": "您能詳細說明嗎？"},
            {"text": "I'd like to add something", "translation": "我想補充一點"},
            {"text": "Let's move on to the next topic", "translation": "讓我們進入下一個議題"},
            {"text": "Meeting adjourned", "translation": "會議結束"},
        ],
        "Presentation Skills 簡報技巧": [
            {"text": "Good morning everyone", "translation": "大家早安"},
            {"text": "Today I'll be talking about", "translation": "今天我要談論的是"},
            {"text": "Let me show you this chart", "translation": "讓我展示這個圖表"},
            {"text": "Are there any questions?", "translation": "有任何問題嗎？"},
            {"text": "Thank you for your attention", "translation": "感謝您的關注"},
        ],
        # Program ID 8: 英語文法基礎課程
        "Be Verbs and Simple Present Be動詞與現在簡單式": [
            {"text": "I am a student", "translation": "我是學生"},
            {"text": "She is happy", "translation": "她很開心"},
            {"text": "They are friends", "translation": "他們是朋友"},
            {"text": "He plays tennis", "translation": "他打網球"},
            {"text": "We study English", "translation": "我們學習英文"},
        ],
        "Articles and Nouns 冠詞與名詞": [
            {"text": "A cat, an apple", "translation": "一隻貓、一個蘋果"},
            {"text": "The sun is bright", "translation": "太陽很亮"},
            {"text": "Books are interesting", "translation": "書很有趣"},
            {"text": "The children play", "translation": "孩子們在玩"},
            {"text": "An hour ago", "translation": "一小時前"},
        ],
        "Simple Past Tense 過去簡單式": [
            {"text": "I went to school", "translation": "我去了學校"},
            {"text": "She ate breakfast", "translation": "她吃了早餐"},
            {"text": "They played games", "translation": "他們玩了遊戲"},
            {"text": "We watched a movie", "translation": "我們看了電影"},
            {"text": "He studied hard", "translation": "他努力學習"},
        ],
    }

    # 建立 ContentItem 記錄
    content_items = []
    for content in contents:
        # 根據 title 找對應的 items
        items_data = content_items_data.get(content.title, [])

        if items_data:
            for idx, item_data in enumerate(items_data):
                content_item = ContentItem(
                    content_id=content.id,
                    order_index=idx,
                    text=item_data.get("text", ""),
                    translation=item_data.get("translation", ""),
                    audio_url=item_data.get("audio_url"),
                )
                content_items.append(content_item)
        # Content 不再有 items 屬性，所有項目都通過 ContentItem 表管理

    if content_items:
        db.add_all(content_items)
        db.commit()
        print(f"✅ 建立 {len(content_items)} 個 ContentItem 記錄")

    # Return created programs
    return {
        "beginner_program": beginner_program,
        "intermediate_program": intermediate_program,
        "advanced_program": advanced_program,
        "lessons": {
            "beginner": beginner_lessons,
            "intermediate": intermediate_lessons,
            "advanced": advanced_lessons,
        },
        "contents": {
            "beginner": beginner_contents,
            "intermediate": intermediate_contents,
            "advanced": advanced_contents,
        },
    }
