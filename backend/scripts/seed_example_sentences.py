"""
Seed script: 創建例句集課程資料 (EXAMPLE_SENTENCES / READING_ASSESSMENT)
- 1 個課程 (Program)
- 2 個單元 (Lessons)
- 每個單元 2 個例句集 (Contents)
- 每個例句集 10-15 個句子 (ContentItems)

句子規格：
- 每個句子 2-25 個英文單字
- 包含中文翻譯

使用方式：
- python3 scripts/seed_example_sentences.py          # 新增資料
- python3 scripts/seed_example_sentences.py --reset  # 重置（刪除舊資料後重新建立）
"""

import sys
import os
import argparse
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from database import Base  # noqa: F401, E402
from models import (  # noqa: E402
    Program,
    Lesson,
    Content,
    ContentItem,
    ContentType,
    ProgramLevel,
)
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def count_words(text: str) -> int:
    """計算英文單字數量"""
    words = text.split()
    return len(words)


def create_example_sentences_course():
    """創建例句集課程"""
    db = SessionLocal()

    try:
        # 五年級A班 ID (根據 seed_data.py)
        classroom_id = 1
        teacher_id = 1

        print("🚀 開始創建例句集課程...")

        # 1. 創建課程 (Program)
        program = Program(
            name="日常生活英語例句集",
            description="涵蓋日常生活、學校、家庭等主題的基礎英語例句練習",
            level=ProgramLevel.A1,
            is_template=False,
            classroom_id=classroom_id,
            teacher_id=teacher_id,
            source_type="custom",
            source_metadata={"created_by": "seed_example_sentences"},
            estimated_hours=8,
            order_index=2,
            is_active=True,
        )
        db.add(program)
        db.flush()
        print(f"✅ 創建課程: {program.name} (ID: {program.id})")

        # 2. 創建第一個單元
        lesson1 = Lesson(
            program_id=program.id,
            name="Unit 1: 學校生活",
            description="學校相關的日常英語例句練習",
            order_index=1,
            estimated_minutes=90,
            is_active=True,
        )
        db.add(lesson1)
        db.flush()
        print(f"✅ 創建單元: {lesson1.name} (ID: {lesson1.id})")

        # 2.1 第一個單元的第一個例句集
        content1_1 = Content(
            lesson_id=lesson1.id,
            type=ContentType.EXAMPLE_SENTENCES,
            title="上學日常對話",
            order_index=1,
            level="A1",
            target_wpm=60,
            target_accuracy=0.8,
            time_limit_seconds=180,
            is_active=True,
        )
        db.add(content1_1)
        db.flush()
        print(f"  ✅ 創建例句集: {content1_1.title} (ID: {content1_1.id})")

        # 第一個例句集的句子 (12句, 每句 2-25 字)
        # 格式: (sentence, translation)
        sentences_set1_1 = [
            ("Good morning, teacher!", "老師早安！"),
            ("I am ready for class.", "我準備好上課了。"),
            ("May I go to the restroom?", "我可以去洗手間嗎？"),
            ("Please open your textbook to page ten.", "請把課本翻到第十頁。"),
            ("I don't understand this question.", "我不懂這個問題。"),
            ("Can you explain it again?", "你可以再解釋一次嗎？"),
            ("The homework is due tomorrow.", "作業明天要交。"),
            ("Let's work together on this project.", "我們一起做這個專題吧。"),
            ("I forgot my pencil case at home.", "我把鉛筆盒忘在家裡了。"),
            ("The bell is ringing.", "鐘聲響了。"),
            ("See you tomorrow!", "明天見！"),
            ("Have a nice day!", "祝你有美好的一天！"),
        ]

        # 驗證句子長度
        for sentence, _ in sentences_set1_1:
            word_count = count_words(sentence)
            if word_count < 2 or word_count > 25:
                print(f"  ⚠️ 警告: '{sentence}' 有 {word_count} 個單字（需 2-25）")

        for idx, (sentence, translation) in enumerate(sentences_set1_1, 1):
            word_count = count_words(sentence)
            item = ContentItem(
                content_id=content1_1.id,
                order_index=idx,
                text=sentence,
                translation=translation,
                audio_url=None,
                word_count=word_count,
                max_errors=max(1, word_count // 5),  # 每 5 個字允許 1 個錯誤
            )
            db.add(item)
        print(f"    ✅ 添加 {len(sentences_set1_1)} 個句子")

        # 2.2 第一個單元的第二個例句集
        content1_2 = Content(
            lesson_id=lesson1.id,
            type=ContentType.EXAMPLE_SENTENCES,
            title="課堂互動用語",
            order_index=2,
            level="A1",
            target_wpm=60,
            target_accuracy=0.8,
            time_limit_seconds=180,
            is_active=True,
        )
        db.add(content1_2)
        db.flush()
        print(f"  ✅ 創建例句集: {content1_2.title} (ID: {content1_2.id})")

        sentences_set1_2 = [
            ("Raise your hand if you know the answer.", "如果你知道答案請舉手。"),
            ("Please speak louder.", "請說大聲一點。"),
            ("Could you repeat that?", "你可以重複一遍嗎？"),
            ("I have a question.", "我有一個問題。"),
            ("Let me think about it.", "讓我想一想。"),
            ("That's a great idea!", "這是個好主意！"),
            ("I agree with you.", "我同意你的看法。"),
            ("Can I borrow your eraser?", "我可以借你的橡皮擦嗎？"),
            ("Thanks for your help!", "謝謝你的幫忙！"),
            ("You're welcome.", "不客氣。"),
            ("Good job, everyone!", "大家做得很好！"),
            ("Keep up the good work.", "繼續保持。"),
        ]

        for idx, (sentence, translation) in enumerate(sentences_set1_2, 1):
            word_count = count_words(sentence)
            item = ContentItem(
                content_id=content1_2.id,
                order_index=idx,
                text=sentence,
                translation=translation,
                audio_url=None,
                word_count=word_count,
                max_errors=max(1, word_count // 5),
            )
            db.add(item)
        print(f"    ✅ 添加 {len(sentences_set1_2)} 個句子")

        # 3. 創建第二個單元
        lesson2 = Lesson(
            program_id=program.id,
            name="Unit 2: 家庭生活",
            description="家庭與日常生活相關的英語例句練習",
            order_index=2,
            estimated_minutes=90,
            is_active=True,
        )
        db.add(lesson2)
        db.flush()
        print(f"✅ 創建單元: {lesson2.name} (ID: {lesson2.id})")

        # 3.1 第二個單元的第一個例句集
        content2_1 = Content(
            lesson_id=lesson2.id,
            type=ContentType.EXAMPLE_SENTENCES,
            title="家人相處",
            order_index=1,
            level="A1",
            target_wpm=60,
            target_accuracy=0.8,
            time_limit_seconds=180,
            is_active=True,
        )
        db.add(content2_1)
        db.flush()
        print(f"  ✅ 創建例句集: {content2_1.title} (ID: {content2_1.id})")

        sentences_set2_1 = [
            ("I love my family.", "我愛我的家人。"),
            ("Mom is cooking dinner.", "媽媽正在煮晚餐。"),
            ("Dad is reading the newspaper.", "爸爸正在看報紙。"),
            ("My sister is doing her homework.", "我的姊姊正在做作業。"),
            ("Can you help me with this?", "你可以幫我這個嗎？"),
            ("Let's watch TV together.", "我們一起看電視吧。"),
            ("It's time for bed.", "該睡覺了。"),
            ("Good night, sleep tight!", "晚安，睡個好覺！"),
            ("I'll clean my room today.", "我今天會打掃房間。"),
            ("We eat breakfast at seven.", "我們七點吃早餐。"),
            ("Please set the table.", "請擺好餐具。"),
            ("The dinner is delicious.", "晚餐很好吃。"),
        ]

        for idx, (sentence, translation) in enumerate(sentences_set2_1, 1):
            word_count = count_words(sentence)
            item = ContentItem(
                content_id=content2_1.id,
                order_index=idx,
                text=sentence,
                translation=translation,
                audio_url=None,
                word_count=word_count,
                max_errors=max(1, word_count // 5),
            )
            db.add(item)
        print(f"    ✅ 添加 {len(sentences_set2_1)} 個句子")

        # 3.2 第二個單元的第二個例句集
        content2_2 = Content(
            lesson_id=lesson2.id,
            type=ContentType.EXAMPLE_SENTENCES,
            title="週末活動",
            order_index=2,
            level="A1",
            target_wpm=60,
            target_accuracy=0.8,
            time_limit_seconds=180,
            is_active=True,
        )
        db.add(content2_2)
        db.flush()
        print(f"  ✅ 創建例句集: {content2_2.title} (ID: {content2_2.id})")

        sentences_set2_2 = [
            ("What are you doing this weekend?", "你這個週末要做什麼？"),
            ("I'm going to the park.", "我要去公園。"),
            ("Let's go shopping together.", "我們一起去購物吧。"),
            ("I want to play basketball.", "我想打籃球。"),
            ("My family will visit grandma.", "我的家人要去看奶奶。"),
            ("I like riding my bike.", "我喜歡騎腳踏車。"),
            ("We're having a barbecue.", "我們要烤肉。"),
            ("Can I invite my friends over?", "我可以邀請朋友來嗎？"),
            ("I need to finish my homework first.", "我需要先完成作業。"),
            ("Let's play video games.", "我們來打電動吧。"),
            ("I want to sleep in tomorrow.", "我明天想睡晚一點。"),
            ("The weekend is too short!", "週末太短了！"),
            ("I had a great weekend.", "我有一個很棒的週末。"),
            ("Monday is coming soon.", "星期一快到了。"),
        ]

        for idx, (sentence, translation) in enumerate(sentences_set2_2, 1):
            word_count = count_words(sentence)
            item = ContentItem(
                content_id=content2_2.id,
                order_index=idx,
                text=sentence,
                translation=translation,
                audio_url=None,
                word_count=word_count,
                max_errors=max(1, word_count // 5),
            )
            db.add(item)
        print(f"    ✅ 添加 {len(sentences_set2_2)} 個句子")

        # Commit all changes
        db.commit()
        total_sentences = (
            len(sentences_set1_1)
            + len(sentences_set1_2)
            + len(sentences_set2_1)
            + len(sentences_set2_2)
        )
        print("\n🎉 完成！例句集課程已成功創建！")
        print("\n📊 總結：")
        print("  - 課程數量: 1")
        print("  - 單元數量: 2")
        print("  - 例句集: 4")
        print(f"  - 句子總數: {total_sentences}")

        return program

    except Exception as e:
        db.rollback()
        print(f"❌ 錯誤: {e}")
        raise
    finally:
        db.close()


def delete_example_sentences_course():
    """刪除既有的例句集課程資料"""
    from sqlalchemy import text

    db = SessionLocal()

    try:
        print("🗑️  正在刪除既有的例句集課程...")

        # 找到 seed 創建的 programs
        result = db.execute(
            text(
                """
                SELECT id, name FROM programs
                WHERE name = '日常生活英語例句集'
                OR source_metadata->>'created_by' = 'seed_example_sentences'
            """
            )
        )

        programs = result.fetchall()

        if not programs:
            print("  ⚠️ 沒有找到需要刪除的課程")
            return

        for program in programs:
            program_id, program_name = program
            print(f"  🗑️  刪除課程: {program_name} (ID: {program_id})")

            # 刪除相關的進度資料
            db.execute(
                text(
                    """
                DELETE FROM student_item_progress
                WHERE student_assignment_id IN (
                    SELECT sa.id FROM student_assignments sa
                    JOIN assignment_contents ac ON sa.assignment_id = ac.assignment_id
                    JOIN contents c ON ac.content_id = c.id
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            db.execute(
                text(
                    """
                DELETE FROM student_content_progress
                WHERE student_assignment_id IN (
                    SELECT sa.id FROM student_assignments sa
                    JOIN assignment_contents ac ON sa.assignment_id = ac.assignment_id
                    JOIN contents c ON ac.content_id = c.id
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            db.execute(
                text(
                    """
                DELETE FROM student_assignments
                WHERE assignment_id IN (
                    SELECT a.id FROM assignments a
                    JOIN assignment_contents ac ON a.id = ac.assignment_id
                    JOIN contents c ON ac.content_id = c.id
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            db.execute(
                text(
                    """
                DELETE FROM assignment_contents
                WHERE content_id IN (
                    SELECT c.id FROM contents c
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            db.execute(
                text(
                    """
                DELETE FROM assignments
                WHERE id IN (
                    SELECT DISTINCT a.id FROM assignments a
                    JOIN assignment_contents ac ON a.id = ac.assignment_id
                    JOIN contents c ON ac.content_id = c.id
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            # 刪除 content_items
            db.execute(
                text(
                    """
                DELETE FROM content_items
                WHERE content_id IN (
                    SELECT c.id FROM contents c
                    JOIN lessons l ON c.lesson_id = l.id
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            # 刪除 contents
            db.execute(
                text(
                    """
                DELETE FROM contents
                WHERE lesson_id IN (
                    SELECT l.id FROM lessons l
                    WHERE l.program_id = :program_id
                )
            """
                ),
                {"program_id": program_id},
            )

            # 刪除 lessons
            db.execute(
                text("DELETE FROM lessons WHERE program_id = :program_id"),
                {"program_id": program_id},
            )

            # 最後刪除 program
            db.execute(
                text("DELETE FROM programs WHERE id = :program_id"),
                {"program_id": program_id},
            )

        db.commit()
        print("✅ 舊資料已刪除")

    except Exception as e:
        db.rollback()
        print(f"❌ 刪除失敗: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed example sentences data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset: delete existing data before creating new data",
    )
    args = parser.parse_args()

    if args.reset:
        print("=" * 60)
        print("🔄 重置模式：將刪除既有資料後重新建立")
        print("=" * 60)
        delete_example_sentences_course()

    create_example_sentences_course()
