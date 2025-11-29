"""
Main orchestrator for seed data
Coordinates all seed stages in proper dependency order
"""
from sqlalchemy.orm import Session
from database import get_engine, Base
from models import Teacher, Program, Lesson, Content, ContentItem

# Import all stage functions
from seed_data.stage_01_users import seed_users_and_organizations
from seed_data.stage_02_classrooms import seed_classrooms
from seed_data.stage_03_students import seed_students
from seed_data.stage_04_programs import seed_programs
from seed_data.stage_05_assignments import seed_assignments


def create_demo_data(db: Session):
    """
    Main entry point - creates complete demo data
    Executes all stages in dependency order
    """
    print("🌱 開始建立 Demo 資料（新作業系統架構）...")
    
    # Stage 1: Users and Organizations
    print("\n=== Stage 1: Users and Organizations ===")
    users_data = seed_users_and_organizations(db)
    
    # Stage 2: Classrooms
    print("\n=== Stage 2: Classrooms ===")
    classrooms_data = seed_classrooms(db, users_data)
    
    # Stage 3: Students
    print("\n=== Stage 3: Students ===")
    students_data = seed_students(db, classrooms_data)
    
    # Stage 4: Programs
    print("\n=== Stage 4: Programs ===")
    programs_data = seed_programs(db, users_data)
    
    # Stage 5: Assignments
    print("\n=== Stage 5: Assignments ===")
    assignments_data = seed_assignments(db, users_data, classrooms_data, 
                                       students_data, programs_data)
    
    print("\n✅ 所有 Demo 資料建立完成！")


def seed_template_programs(db: Session):
    """建立公版課程模板資料"""
    print("\n🌱 建立公版課程模板...")

    # ============ 1. 取得 Demo 教師 ============
    demo_teacher = (
        db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    )

    if not demo_teacher:
        print("❌ 找不到 Demo 教師，請先執行主要 seed")
        return

    # ============ 2. 建立公版課程模板 ============

    # 模板 1: 初級英語會話 (A1)
    template_basic_conversation = Program(
        name="初級英語會話課程",
        description="適合初學者的英語會話課程，涵蓋日常生活基本對話",
        level="A1",
        is_template=True,  # 公版模板
        classroom_id=None,  # 不屬於任何班級
        teacher_id=demo_teacher.id,
        estimated_hours=20,
        tags=["speaking", "beginner", "conversation", "daily"],
        source_type=None,
        source_metadata={"created_by": "seed", "version": "1.0"},
        is_active=True,
    )

    # 模板 2: 中級英語閱讀 (B1)
    template_intermediate_reading = Program(
        name="中級英語閱讀理解",
        description="提升閱讀技巧，包含短文理解、詞彙擴充和閱讀策略",
        level="B1",
        is_template=True,
        classroom_id=None,
        teacher_id=demo_teacher.id,
        estimated_hours=30,
        tags=["reading", "intermediate", "vocabulary", "comprehension"],
        source_type=None,
        source_metadata={"created_by": "seed", "version": "1.0"},
        is_active=True,
    )

    # 模板 3: 英語發音訓練 (A2)
    template_pronunciation = Program(
        name="英語發音訓練課程",
        description="系統性學習英語發音規則，改善口說清晰度",
        level="A2",
        is_template=True,
        classroom_id=None,
        teacher_id=demo_teacher.id,
        estimated_hours=15,
        tags=["pronunciation", "speaking", "phonics", "accent"],
        source_type=None,
        source_metadata={"created_by": "seed", "version": "1.0"},
        is_active=True,
    )

    # 模板 4: 商務英語入門 (B2)
    template_business = Program(
        name="商務英語入門",
        description="職場必備英語，包含email寫作、會議英語和商務禮儀",
        level="B2",
        is_template=True,
        classroom_id=None,
        teacher_id=demo_teacher.id,
        estimated_hours=25,
        tags=["business", "professional", "email", "meeting"],
        source_type=None,
        source_metadata={"created_by": "seed", "version": "1.0"},
        is_active=True,
    )

    # 模板 5: 英語文法基礎 (A1)
    template_grammar = Program(
        name="英語文法基礎課程",
        description="從零開始學習英語文法，建立扎實的語言基礎",
        level="A1",
        is_template=True,
        classroom_id=None,
        teacher_id=demo_teacher.id,
        estimated_hours=20,
        tags=["grammar", "beginner", "structure", "basics"],
        source_type=None,
        source_metadata={"created_by": "seed", "version": "1.0"},
        is_active=True,
    )

    db.add_all(
        [
            template_basic_conversation,
            template_intermediate_reading,
            template_pronunciation,
            template_business,
            template_grammar,
        ]
    )
    db.commit()

    print("✅ 建立 5 個公版課程模板")

    # ============ 3. 為每個模板建立 Lessons ============

    # 初級英語會話課程的 Lessons
    lessons_basic_conv = [
        Lesson(
            program_id=template_basic_conversation.id,
            name="Lesson 1: Greetings and Introductions",
            description="Learn how to greet people and introduce yourself",
            order_index=1,
            estimated_minutes=45,
            is_active=True,
        ),
        Lesson(
            program_id=template_basic_conversation.id,
            name="Lesson 2: Daily Activities",
            description="Talk about your daily routine",
            order_index=2,
            estimated_minutes=45,
            is_active=True,
        ),
        Lesson(
            program_id=template_basic_conversation.id,
            name="Lesson 3: Shopping and Numbers",
            description="Learn shopping vocabulary and numbers",
            order_index=3,
            estimated_minutes=50,
            is_active=True,
        ),
        Lesson(
            program_id=template_basic_conversation.id,
            name="Lesson 4: Food and Restaurants",
            description="Order food and talk about preferences",
            order_index=4,
            estimated_minutes=50,
            is_active=True,
        ),
    ]

    db.add_all(lessons_basic_conv)
    db.commit()

    # 中級閱讀理解課程的 Lessons
    lessons_reading = [
        Lesson(
            program_id=template_intermediate_reading.id,
            name="Lesson 1: Reading Strategies",
            description="Learn effective reading strategies for comprehension",
            order_index=1,
            estimated_minutes=60,
            is_active=True,
        ),
        Lesson(
            program_id=template_intermediate_reading.id,
            name="Lesson 2: News Articles",
            description="Practice reading news articles and current events",
            order_index=2,
            estimated_minutes=60,
            is_active=True,
        ),
        Lesson(
            program_id=template_intermediate_reading.id,
            name="Lesson 3: Short Stories",
            description="Read and analyze short stories",
            order_index=3,
            estimated_minutes=75,
            is_active=True,
        ),
    ]

    db.add_all(lessons_reading)
    db.commit()

    # 發音訓練課程的 Lessons
    lessons_pronunciation = [
        Lesson(
            program_id=template_pronunciation.id,
            name="Lesson 1: Vowel Sounds",
            description="Master English vowel sounds",
            order_index=1,
            estimated_minutes=40,
            is_active=True,
        ),
        Lesson(
            program_id=template_pronunciation.id,
            name="Lesson 2: Consonant Sounds",
            description="Practice consonant pronunciation",
            order_index=2,
            estimated_minutes=40,
            is_active=True,
        ),
        Lesson(
            program_id=template_pronunciation.id,
            name="Lesson 3: Word Stress and Intonation",
            description="Learn stress patterns and intonation",
            order_index=3,
            estimated_minutes=45,
            is_active=True,
        ),
    ]

    db.add_all(lessons_pronunciation)
    db.commit()

    # 商務英語的 Lessons
    lessons_business = [
        Lesson(
            program_id=template_business.id,
            name="Lesson 1: Business Email Writing",
            description="Write professional emails",
            order_index=1,
            estimated_minutes=60,
            is_active=True,
        ),
        Lesson(
            program_id=template_business.id,
            name="Lesson 2: Meeting English",
            description="Participate effectively in business meetings",
            order_index=2,
            estimated_minutes=60,
            is_active=True,
        ),
        Lesson(
            program_id=template_business.id,
            name="Lesson 3: Presentations",
            description="Give professional presentations",
            order_index=3,
            estimated_minutes=75,
            is_active=True,
        ),
    ]

    db.add_all(lessons_business)
    db.commit()

    # 文法基礎的 Lessons
    lessons_grammar = [
        Lesson(
            program_id=template_grammar.id,
            name="Lesson 1: Be Verbs and Simple Present",
            description="Learn be verbs and simple present tense",
            order_index=1,
            estimated_minutes=45,
            is_active=True,
        ),
        Lesson(
            program_id=template_grammar.id,
            name="Lesson 2: Articles and Nouns",
            description="Master articles (a, an, the) and noun usage",
            order_index=2,
            estimated_minutes=45,
            is_active=True,
        ),
        Lesson(
            program_id=template_grammar.id,
            name="Lesson 3: Simple Past Tense",
            description="Learn to talk about past events",
            order_index=3,
            estimated_minutes=50,
            is_active=True,
        ),
    ]

    db.add_all(lessons_grammar)
    db.commit()

    print("✅ 為每個模板建立了 Lessons")

    # ============ 3.5 為模板課程建立內容 ============
    print("📝 為模板課程建立內容...")

    # 為初級英語會話課程建立內容
    template_contents = []

    # Lesson 1: Greetings - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_basic_conv[0].id,
            type=ContentType.READING_ASSESSMENT,
            title="Basic Greetings 基本問候語",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 2: Daily Activities - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_basic_conv[1].id,
            type=ContentType.READING_ASSESSMENT,
            title="My Daily Routine 我的日常作息",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 3: Shopping and Numbers - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_basic_conv[2].id,
            type=ContentType.READING_ASSESSMENT,
            title="Shopping Vocabulary 購物詞彙",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 4: Food and Restaurants - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_basic_conv[3].id,
            type=ContentType.READING_ASSESSMENT,
            title="Restaurant English 餐廳英語",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # 為中級閱讀理解課程建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_reading[0].id,
            type=ContentType.READING_ASSESSMENT,
            title="Reading Strategies 閱讀策略",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 2: News Articles - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_reading[1].id,
            type=ContentType.READING_ASSESSMENT,
            title="News Headlines 新聞標題",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 3: Short Stories - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_reading[2].id,
            type=ContentType.READING_ASSESSMENT,
            title="Story Elements 故事元素",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # 為英語發音訓練課程建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_pronunciation[0].id,
            type=ContentType.READING_ASSESSMENT,
            title="Vowel Sounds 母音發音",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 2: Consonant Sounds - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_pronunciation[1].id,
            type=ContentType.READING_ASSESSMENT,
            title="Consonant Sounds 子音發音",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 3: Word Stress and Intonation - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_pronunciation[2].id,
            type=ContentType.READING_ASSESSMENT,
            title="Word Stress 重音練習",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # 為商務英語入門建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_business[0].id,
            type=ContentType.READING_ASSESSMENT,
            title="Business Email Writing 商務郵件",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 2: Meeting English - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_business[1].id,
            type=ContentType.READING_ASSESSMENT,
            title="Meeting English 會議英語",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 3: Presentations - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_business[2].id,
            type=ContentType.READING_ASSESSMENT,
            title="Presentation Skills 簡報技巧",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # 為文法基礎課程建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_grammar[0].id,
            type=ContentType.READING_ASSESSMENT,
            title="Be Verbs and Simple Present Be動詞與現在簡單式",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 2: Articles and Nouns - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_grammar[1].id,
            type=ContentType.READING_ASSESSMENT,
            title="Articles and Nouns 冠詞與名詞",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    # Lesson 3: Simple Past Tense - 建立內容
    template_contents.append(
        Content(
            lesson_id=lessons_grammar[2].id,
            type=ContentType.READING_ASSESSMENT,
            title="Simple Past Tense 過去簡單式",
            order_index=1,
            is_active=True,
            is_public=True,
        )
    )

    db.add_all(template_contents)
    db.commit()
    print(f"✅ 為模板課程建立了 {len(template_contents)} 個內容")

    # ============ 3.5 為模板課程內容建立 ContentItem ============
    print("📝 為模板課程建立 ContentItem...")

    # ContentItem 資料定義（已在前面定義過）
    content_items_data = {
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
    template_content_items = []
    for content in template_contents:
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
                template_content_items.append(content_item)

    if template_content_items:
        db.add_all(template_content_items)
        db.commit()
        print(f"✅ 為模板課程建立了 {len(template_content_items)} 個 ContentItem")

    # ============ 4. 顯示結果摘要 ============
    template_count = (
        db.query(Program)
        .filter(Program.is_template.is_(True), Program.teacher_id == demo_teacher.id)
        .count()
    )

    print(f"✅ 總共建立了 {template_count} 個公版課程模板（含標籤）")




def reset_database():
    """重置資料庫並建立 seed data"""
    print("⚠️  正在重置資料庫...")

    engine = get_engine()

    # Drop all tables using SQLAlchemy
    Base.metadata.drop_all(bind=engine)
    print("✅ 舊資料已清除")

    # Recreate all tables using SQLAlchemy
    Base.metadata.create_all(bind=engine)
    print("✅ 資料表已重新建立")

    db = Session(engine)
    try:
        create_demo_data(db)
        seed_template_programs(db)  # 加入公版課程模板
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
