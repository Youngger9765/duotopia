#!/usr/bin/env python3
"""
Seed 公版課程模板資料
建立可重複使用的課程模板，教師可以複製到任何班級
"""

from database import SessionLocal
from models import Teacher, Program, Lesson, Content, ContentType
from auth import get_password_hash


def seed_template_programs():
    """建立公版課程模板資料"""
    db = SessionLocal()

    try:
        # ============ 1. 取得或建立 Demo 教師 ============
        demo_teacher = (
            db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
        )

        if not demo_teacher:
            print("建立 Demo 教師...")
            demo_teacher = Teacher(
                email="demo@duotopia.com",
                password_hash=get_password_hash("demo123"),
                name="Demo 老師",
                is_demo=True,
                is_active=True,
            )
            db.add(demo_teacher)
            db.commit()
            db.refresh(demo_teacher)
            print(f"✅ 建立 Demo 教師: {demo_teacher.email}")
        else:
            print(f"✅ 使用現有 Demo 教師: {demo_teacher.email}")

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

        # ============ 3. 為每個模板建立 Lessons 和 Contents ============

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

        # 為初級會話課程建立內容
        contents_basic_conv = [
            Content(
                lesson_id=lessons_basic_conv[0].id,
                title="Self Introduction Practice",
                type=ContentType.READING_ASSESSMENT,
                items=[
                    {"text": "Hello! My name is Alice.", "translation": "你好！我的名字是愛麗絲。"},
                    {"text": "I am ten years old.", "translation": "我十歲了。"},
                    {"text": "I live in Taipei.", "translation": "我住在台北。"},
                    {"text": "Nice to meet you!", "translation": "很高興認識你！"},
                ],
                target_wpm=80,
                target_accuracy=0.85,
                time_limit_seconds=180,
                order_index=1,
                is_active=True,
            ),
            Content(
                lesson_id=lessons_basic_conv[1].id,
                title="Daily Routine Practice",
                type=ContentType.READING_ASSESSMENT,
                items=[
                    {"text": "I wake up at seven o'clock.", "translation": "我七點起床。"},
                    {
                        "text": "I brush my teeth and wash my face.",
                        "translation": "我刷牙洗臉。",
                    },
                    {
                        "text": "I have breakfast with my family.",
                        "translation": "我和家人一起吃早餐。",
                    },
                    {"text": "I go to school by bus.", "translation": "我搭公車上學。"},
                    {"text": "I come home at four o'clock.", "translation": "我四點回家。"},
                ],
                target_wpm=85,
                target_accuracy=0.85,
                time_limit_seconds=180,
                order_index=1,
                is_active=True,
            ),
            Content(
                lesson_id=lessons_basic_conv[2].id,
                title="Shopping Conversation",
                type=ContentType.READING_ASSESSMENT,
                items=[
                    {"text": "How much is this shirt?", "translation": "這件襯衫多少錢？"},
                    {
                        "text": "It costs twenty-five dollars.",
                        "translation": "它要二十五美元。",
                    },
                    {"text": "Can I try it on?", "translation": "我可以試穿嗎？"},
                    {
                        "text": "The fitting room is over there.",
                        "translation": "試衣間在那邊。",
                    },
                    {"text": "Do you have a bigger size?", "translation": "你們有更大的尺寸嗎？"},
                ],
                target_wpm=90,
                target_accuracy=0.85,
                time_limit_seconds=180,
                order_index=1,
                is_active=True,
            ),
        ]

        db.add_all(contents_basic_conv)
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

        # ============ 4. 顯示結果摘要 ============
        template_count = (
            db.query(Program)
            .filter(
                Program.is_template.is_(True), Program.teacher_id == demo_teacher.id
            )
            .count()
        )

        print("\n========== 公版課程模板建立完成 ==========\n")
        print(f"✅ 總共建立了 {template_count} 個公版課程模板")
        print("✅ 每個模板都包含完整的 Lessons 結構")
        print("\n這些模板可以被複製到任何班級使用：")

        templates = (
            db.query(Program)
            .filter(
                Program.is_template.is_(True), Program.teacher_id == demo_teacher.id
            )
            .all()
        )

        for template in templates:
            lesson_count = (
                db.query(Lesson).filter(Lesson.program_id == template.id).count()
            )
            print(f"  - {template.name} ({template.level}) - {lesson_count} lessons")

        print("\n教師可以透過以下方式使用這些模板：")
        print("1. 直接複製模板到班級")
        print("2. 複製後根據班級需求調整內容")
        print("3. 作為建立自訂課程的參考")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("開始建立公版課程模板...")
    seed_template_programs()
