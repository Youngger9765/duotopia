"""
Seed data for Duotopia - 新作業系統架構
建立完整的 Demo 資料：教師、學生、班級、課程、作業
覆蓋所有作業系統情境（教師端和學生端）
"""

from datetime import datetime, date, timedelta  # noqa: F401
import random
from sqlalchemy.orm import Session
from database import engine
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    StudentContentProgress,
    ProgramLevel,
    ContentType,
    AssignmentStatus,
)
from auth import get_password_hash


def create_demo_data(db: Session):
    """建立完整的 demo 資料 - 新作業系統架構"""

    print("🌱 開始建立 Demo 資料（新作業系統架構）...")

    # ============ 1. Demo 教師 ============
    demo_teacher = Teacher(
        email="demo@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="Demo 老師",
        is_demo=True,
        is_active=True,
    )
    db.add(demo_teacher)
    db.commit()
    print("✅ 建立 Demo 教師: demo@duotopia.com / demo123")

    # ============ 2. Demo 班級 ============
    classroom_a = Classroom(
        name="五年級A班",
        description="國小五年級英語基礎班",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        is_active=True,
    )

    classroom_b = Classroom(
        name="六年級B班",
        description="國小六年級英語進階班",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        is_active=True,
    )

    db.add_all([classroom_a, classroom_b])
    db.commit()
    print("✅ 建立 2 個班級: 五年級A班、六年級B班")

    # ============ 3. Demo 學生（統一密碼：20120101）============
    common_birthdate = date(2012, 1, 1)
    common_password = get_password_hash("20120101")

    # 五年級A班學生（增加到12位）
    students_5a_names = [
        "王小明",
        "李小美",
        "陳大雄",
        "黃小華",
        "劉心怡",
        "吳志明",
        "許雅婷",
        "鄭建國",
        "林佳慧",
        "張偉強",
        "蔡雅芳",
        "謝志偉",
    ]

    students_5a = []
    for i, name in enumerate(students_5a_names):
        # 所有五年級學生都使用預設密碼
        student = Student(
            name=name,
            email=f"student{i+1}@duotopia.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id=f"S{i+1:03d}",
            target_wpm=random.randint(50, 70),
            target_accuracy=round(random.uniform(0.70, 0.85), 2),
            password_changed=False,
            email_verified=False,  # 所有學生預設都未驗證 email
            email_verified_at=None,
            is_active=True,
        )
        students_5a.append(student)

    # 六年級B班學生（增加到15位）
    students_6b_names = [
        "張志豪",
        "林靜香",
        "測試學生",
        "蔡文傑",
        "謝佩琪",
        "楊智凱",
        "周美玲",
        "高俊宇",
        "羅曉晴",
        "洪志峰",
        "鍾雅筑",
        "施建成",
        "賴文芳",
        "簡志明",
        "余佳蓉",
    ]

    students_6b = []
    for i, name in enumerate(students_6b_names):
        # 只有最後一個學生（余佳蓉）有特殊密碼
        if name == "余佳蓉":
            password_hash = get_password_hash("custom123")
            password_changed = True
        else:
            password_hash = common_password
            password_changed = False

        student = Student(
            name=name,
            email=f"student{i+13}@duotopia.com",
            password_hash=password_hash,
            birthdate=common_birthdate,
            student_id=f"S{i+13:03d}",
            target_wpm=random.randint(65, 85),
            target_accuracy=round(random.uniform(0.80, 0.95), 2),
            password_changed=password_changed,
            email_verified=False,  # 所有學生預設都未驗證 email
            email_verified_at=None,
            is_active=True,
        )
        students_6b.append(student)

    all_students = students_5a + students_6b
    db.add_all(all_students)
    db.commit()
    print(
        f"✅ 建立 {len(all_students)} 位學生（五年級A班{len(students_5a)}位，六年級B班{len(students_6b)}位）"
    )

    # ============ 4. 學生加入班級 ============
    # 五年級A班
    for student in students_5a:
        enrollment = ClassroomStudent(
            classroom_id=classroom_a.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    # 六年級B班
    for student in students_6b:
        enrollment = ClassroomStudent(
            classroom_id=classroom_b.id, student_id=student.id, is_active=True
        )
        db.add(enrollment)

    db.commit()
    print("✅ 學生已加入班級")

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
        items=[
            {"text": "Hello", "translation": "你好"},
            {"text": "Good morning", "translation": "早安"},
            {"text": "Good afternoon", "translation": "午安"},
            {"text": "How are you?", "translation": "你好嗎？"},
            {"text": "I'm fine, thank you", "translation": "我很好，謝謝"},
        ],
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
        items=[
            {"text": "Nice to meet you", "translation": "很高興認識你"},
            {"text": "See you later", "translation": "待會見"},
            {"text": "Have a nice day", "translation": "祝你有美好的一天"},
            {"text": "Take care", "translation": "保重"},
            {"text": "Goodbye", "translation": "再見"},
        ],
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
        items=[
            {"text": "One, Two, Three", "translation": "一、二、三"},
            {"text": "Four, Five, Six", "translation": "四、五、六"},
            {"text": "Seven, Eight", "translation": "七、八"},
            {"text": "Nine, Ten", "translation": "九、十"},
            {"text": "I have five apples", "translation": "我有五個蘋果"},
        ],
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
        items=[
            {"text": "Red and Blue", "translation": "紅色和藍色"},
            {"text": "Green and Yellow", "translation": "綠色和黃色"},
            {"text": "Black and White", "translation": "黑色和白色"},
            {"text": "The sky is blue", "translation": "天空是藍色的"},
            {"text": "I like green", "translation": "我喜歡綠色"},
        ],
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
        items=[
            {"text": "My name is Alice", "translation": "我的名字是 Alice"},
            {"text": "I am ten years old", "translation": "我十歲"},
            {"text": "I live in Taipei", "translation": "我住在台北"},
            {"text": "I like to read books", "translation": "我喜歡讀書"},
            {"text": "Nice to meet you all", "translation": "很高興認識大家"},
        ],
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
        items=[
            {"text": "What's your name?", "translation": "你叫什麼名字？"},
            {"text": "Where are you from?", "translation": "你來自哪裡？"},
            {"text": "I'm from Taiwan", "translation": "我來自台灣"},
            {"text": "How old are you?", "translation": "你幾歲？"},
            {"text": "I'm twelve years old", "translation": "我十二歲"},
        ],
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
        items=[
            {"text": "What do you like to do?", "translation": "你喜歡做什麼？"},
            {"text": "I enjoy playing basketball", "translation": "我喜歡打籃球"},
            {"text": "Do you have any hobbies?", "translation": "你有什麼嗜好嗎？"},
            {"text": "Yes, I love reading", "translation": "有，我喜歡閱讀"},
            {"text": "That sounds interesting", "translation": "聽起來很有趣"},
        ],
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
        items=[
            {"text": "This is my family", "translation": "這是我的家人"},
            {"text": "My father is a doctor", "translation": "我爸爸是醫生"},
            {"text": "My mother is a teacher", "translation": "我媽媽是老師"},
            {"text": "I have one brother", "translation": "我有一個哥哥"},
            {"text": "We live together happily", "translation": "我們快樂地住在一起"},
        ],
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

    # ============ 7. 新作業系統（Assignment + StudentAssignment + StudentContentProgress）============
    print("\n📝 建立新作業系統測試資料...")

    # === 作業情境 1: 五年級A班 - 展示所有狀態 ===
    assignment1 = Assignment(
        title="第一週基礎問候語練習",
        description="請完成基礎問候語的朗讀練習，注意發音準確度",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=7),  # 7天後到期
        is_active=True,
    )
    db.add(assignment1)
    db.flush()

    # 關聯內容
    assignment1_content = AssignmentContent(
        assignment_id=assignment1.id, content_id=content1_5a.id, order_index=1
    )
    db.add(assignment1_content)

    # 指派給五年級A班所有學生 - 展示所有狀態
    assignment1_statuses = {
        "王小明": {
            "status": AssignmentStatus.NOT_STARTED,
            "score": None,
            "feedback": None,
        },
        "李小美": {
            "status": AssignmentStatus.IN_PROGRESS,
            "score": None,
            "feedback": None,
            "started_at": datetime.now() - timedelta(hours=2),
        },
        "陳大雄": {
            "status": AssignmentStatus.SUBMITTED,
            "score": None,
            "feedback": None,
            "started_at": datetime.now() - timedelta(days=1),
            "submitted_at": datetime.now() - timedelta(hours=3),
        },
        "黃小華": {
            "status": AssignmentStatus.SUBMITTED,
            "score": None,
            "feedback": None,
            "started_at": datetime.now() - timedelta(days=2),
            "submitted_at": datetime.now() - timedelta(hours=6),
        },
        "劉心怡": {
            "status": AssignmentStatus.GRADED,
            "score": 85,
            "feedback": "表現良好，發音清晰！",
            "started_at": datetime.now() - timedelta(days=3),
            "submitted_at": datetime.now() - timedelta(days=2),
            "graded_at": datetime.now() - timedelta(days=1),
        },
        "吳志明": {
            "status": AssignmentStatus.GRADED,
            "score": 92,
            "feedback": "優秀！語調自然流暢！",
            "started_at": datetime.now() - timedelta(days=3),
            "submitted_at": datetime.now() - timedelta(days=2, hours=12),
            "graded_at": datetime.now() - timedelta(days=1, hours=6),
        },
        "許雅婷": {
            "status": AssignmentStatus.RETURNED,
            "score": 65,
            "feedback": "第2和第3句需要重新錄製，注意發音",
            "started_at": datetime.now() - timedelta(days=3),
            "submitted_at": datetime.now() - timedelta(days=2),
            "graded_at": datetime.now() - timedelta(days=1),
            "returned_at": datetime.now() - timedelta(days=1),  # 退回時間
        },
        "鄭建國": {
            "status": AssignmentStatus.RETURNED,
            "score": 70,
            "feedback": "語速太快，請放慢速度重新錄製",
            "started_at": datetime.now() - timedelta(days=4),
            "submitted_at": datetime.now() - timedelta(days=3),
            "graded_at": datetime.now() - timedelta(hours=12),
            "returned_at": datetime.now() - timedelta(hours=12),  # 退回時間
        },
        "林佳慧": {
            "status": AssignmentStatus.RESUBMITTED,
            "score": None,
            "feedback": None,
            "started_at": datetime.now() - timedelta(days=4),
            "submitted_at": datetime.now() - timedelta(days=3),  # 第一次提交
            "graded_at": datetime.now() - timedelta(days=2),
            "returned_at": datetime.now() - timedelta(days=2),  # 被退回
            "resubmitted_at": datetime.now() - timedelta(hours=4),  # 重新提交
        },
        "張偉強": {
            "status": AssignmentStatus.RESUBMITTED,
            "score": None,
            "feedback": None,
            "started_at": datetime.now() - timedelta(days=5),
            "submitted_at": datetime.now() - timedelta(days=4),  # 第一次提交
            "graded_at": datetime.now() - timedelta(days=3),
            "returned_at": datetime.now() - timedelta(days=3),  # 被退回
            "resubmitted_at": datetime.now() - timedelta(hours=8),  # 重新提交
        },
        "蔡雅芳": {
            "status": AssignmentStatus.GRADED,
            "score": 88,
            "feedback": "訂正後表現很好！進步明顯！",
            "started_at": datetime.now() - timedelta(days=5),
            "submitted_at": datetime.now() - timedelta(days=4),  # 第一次提交
            "returned_at": datetime.now() - timedelta(days=3),  # 被退回
            "resubmitted_at": datetime.now() - timedelta(days=2),  # 重新提交
            "graded_at": datetime.now() - timedelta(days=1),  # 批改完成
        },
        "謝志偉": {
            "status": AssignmentStatus.GRADED,
            "score": 90,
            "feedback": "重新錄製後效果很好！",
            "started_at": datetime.now() - timedelta(days=6),
            "submitted_at": datetime.now() - timedelta(days=5),  # 第一次提交
            "returned_at": datetime.now() - timedelta(days=4),  # 被退回
            "resubmitted_at": datetime.now() - timedelta(days=3),  # 重新提交
            "graded_at": datetime.now() - timedelta(days=2),  # 批改完成
        },
    }

    for student in students_5a:
        student_data = assignment1_statuses.get(
            student.name,
            {"status": AssignmentStatus.NOT_STARTED, "score": None, "feedback": None},
        )

        student_assignment1 = StudentAssignment(
            assignment_id=assignment1.id,
            student_id=student.id,
            classroom_id=classroom_a.id,
            title=assignment1.title,  # 暫時保留以兼容
            instructions=assignment1.description,
            due_date=assignment1.due_date,
            status=student_data["status"],
            score=student_data.get("score"),
            feedback=student_data.get("feedback"),
            is_active=True,
        )

        # 設定時間戳記
        if "started_at" in student_data:
            student_assignment1.started_at = student_data["started_at"]
        if "submitted_at" in student_data:
            student_assignment1.submitted_at = student_data["submitted_at"]
        if "graded_at" in student_data:
            student_assignment1.graded_at = student_data["graded_at"]
        if "returned_at" in student_data:
            student_assignment1.returned_at = student_data["returned_at"]
        if "resubmitted_at" in student_data:
            student_assignment1.resubmitted_at = student_data["resubmitted_at"]

        db.add(student_assignment1)
        db.flush()

        # 建立內容進度
        progress = StudentContentProgress(
            student_assignment_id=student_assignment1.id,
            content_id=content1_5a.id,
            status=student_data["status"],
            score=(
                student_data.get("score")
                if student_data["status"] == AssignmentStatus.GRADED
                else None
            ),
            order_index=1,
            is_locked=False,
            checked=True if student_data["status"] == AssignmentStatus.GRADED else None,
            feedback=(
                student_data.get("feedback")
                if student_data["status"] == AssignmentStatus.GRADED
                else None
            ),
        )

        if student_data["status"] in [
            AssignmentStatus.SUBMITTED,
            AssignmentStatus.GRADED,
            AssignmentStatus.RETURNED,
            AssignmentStatus.RESUBMITTED,
        ]:
            progress.started_at = student_data.get(
                "started_at", datetime.now() - timedelta(days=3)
            )
            progress.completed_at = student_data.get("submitted_at")
            progress.response_data = {
                "recordings": [f"recording_{i}.webm" for i in range(5)],
                "duration": 156,
            }

            if student_data["status"] == AssignmentStatus.GRADED:
                progress.ai_scores = {
                    "wpm": 68,
                    "accuracy": 0.92,
                    "fluency": 0.88,
                    "pronunciation": 0.90,
                }
                progress.ai_feedback = (
                    "Great pronunciation! Keep practicing the 'th' sound."
                )

        db.add(progress)

    # === 作業情境 2: 五年級A班 - 待批改和待訂正 ===
    assignment2 = Assignment(
        title="期中綜合練習",
        description="請完成所有指定的朗讀練習，這是期中考核的一部分",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=3),  # 3天後到期
        is_active=True,
    )
    db.add(assignment2)
    db.flush()

    # 關聯多個內容
    for idx, content in enumerate([content2_5a, content3_5a], 1):
        assignment_content = AssignmentContent(
            assignment_id=assignment2.id, content_id=content.id, order_index=idx
        )
        db.add(assignment_content)

    # 指派給五年級A班所有學生 - 展示更多狀態
    for student in students_5a:
        if student.name == "王小明":
            status = AssignmentStatus.SUBMITTED  # 待批改
        elif student.name == "李小美":
            status = AssignmentStatus.RETURNED  # 待訂正
        else:
            status = AssignmentStatus.RESUBMITTED  # 重新提交（待批改訂正）

        student_assignment2 = StudentAssignment(
            assignment_id=assignment2.id,
            student_id=student.id,
            classroom_id=classroom_a.id,
            title=assignment2.title,
            instructions=assignment2.description,
            due_date=assignment2.due_date,
            status=status,
            is_active=True,
        )

        if status == AssignmentStatus.SUBMITTED:
            student_assignment2.submitted_at = datetime.now() - timedelta(hours=6)
        elif status == AssignmentStatus.RETURNED:
            student_assignment2.submitted_at = datetime.now() - timedelta(days=1)
            student_assignment2.graded_at = datetime.now() - timedelta(hours=12)
            student_assignment2.returned_at = datetime.now() - timedelta(
                hours=12
            )  # 🔥 設置 returned_at
        elif status == AssignmentStatus.RESUBMITTED:
            student_assignment2.submitted_at = datetime.now() - timedelta(
                days=2
            )  # 第一次提交
            student_assignment2.returned_at = datetime.now() - timedelta(
                days=1
            )  # 🔥 被退回
            student_assignment2.resubmitted_at = datetime.now() - timedelta(
                hours=3
            )  # 🔥 重新提交
            student_assignment2.graded_at = datetime.now() - timedelta(hours=1)  # 批改完成

        db.add(student_assignment2)
        db.flush()

        # 建立多個內容的進度
        for idx, content in enumerate([content2_5a, content3_5a], 1):
            if student.name == "王小明":
                # 王小明已提交所有內容
                content_status = AssignmentStatus.SUBMITTED
                is_locked = False
            elif student.name == "李小美":
                # 李小美被退回需要訂正
                content_status = AssignmentStatus.RETURNED
                is_locked = False
            else:
                # 陳大雄重新提交了
                content_status = AssignmentStatus.RESUBMITTED
                is_locked = False

            progress = StudentContentProgress(
                student_assignment_id=student_assignment2.id,
                content_id=content.id,
                status=content_status,
                order_index=idx,
                is_locked=is_locked,
            )

            if content_status == AssignmentStatus.SUBMITTED:
                progress.started_at = datetime.now() - timedelta(hours=3)
                progress.completed_at = datetime.now() - timedelta(hours=1)
                progress.response_data = {
                    "recordings": [f"recording_{i}.webm" for i in range(5)],
                    "duration": 120 + idx * 10,
                }
            elif content_status == AssignmentStatus.IN_PROGRESS:
                progress.started_at = datetime.now() - timedelta(minutes=30)

            db.add(progress)

    # === 作業情境 3: 退回訂正的作業 ===
    assignment3 = Assignment(
        title="口語會話練習 - 自我介紹",
        description="請錄製自我介紹，注意語調和流暢度",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=7),
        is_active=True,
    )
    db.add(assignment3)
    db.flush()

    assignment3_content = AssignmentContent(
        assignment_id=assignment3.id, content_id=content5_5a.id, order_index=1
    )
    db.add(assignment3_content)

    # 只指派給王小明（測試退回訂正流程）
    student_assignment3 = StudentAssignment(
        assignment_id=assignment3.id,
        student_id=students_5a[0].id,  # 王小明
        classroom_id=classroom_a.id,
        title=assignment3.title,
        instructions=assignment3.description,
        due_date=assignment3.due_date,
        status=AssignmentStatus.RETURNED,
        score=65,
        feedback="發音不錯，但第3和第4句需要重新錄製，注意語調起伏",
        is_active=True,
    )
    student_assignment3.submitted_at = datetime.now() - timedelta(days=1)
    student_assignment3.graded_at = datetime.now() - timedelta(hours=12)
    student_assignment3.returned_at = datetime.now() - timedelta(
        hours=12
    )  # 🔥 設置 returned_at

    db.add(student_assignment3)
    db.flush()

    progress3 = StudentContentProgress(
        student_assignment_id=student_assignment3.id,
        content_id=content5_5a.id,
        status=AssignmentStatus.RETURNED,
        score=65,
        order_index=1,
        is_locked=False,
        checked=False,  # False = 未通過
        feedback="第3句的語調需要更自然，第4句的 'books' 發音需要加強",
    )
    progress3.started_at = datetime.now() - timedelta(days=2)
    progress3.completed_at = datetime.now() - timedelta(days=1)
    progress3.response_data = {
        "recordings": [f"recording_{i}.webm" for i in range(5)],
        "duration": 142,
    }
    progress3.ai_scores = {
        "wpm": 55,
        "accuracy": 0.65,
        "fluency": 0.70,
        "pronunciation": 0.68,
    }
    db.add(progress3)

    # === 作業情境 4: 六年級B班 - 進行中與待批改 ===
    assignment4 = Assignment(
        title="日常對話綜合練習",
        description="完成所有日常對話練習，準備口語測驗",
        classroom_id=classroom_b.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=5),
        is_active=True,
    )
    db.add(assignment4)
    db.flush()

    # 關聯兩個內容
    for idx, content in enumerate([content1_6b, content2_6b], 1):
        assignment_content = AssignmentContent(
            assignment_id=assignment4.id, content_id=content.id, order_index=idx
        )
        db.add(assignment_content)

    # 指派給六年級B班所有學生
    for student in students_6b:
        if student.name == "張志豪":
            status = AssignmentStatus.IN_PROGRESS  # 進行中
        elif student.name == "林靜香":
            status = AssignmentStatus.SUBMITTED  # 待批改
        else:  # 測試學生
            status = AssignmentStatus.GRADED  # 已完成

        student_assignment4 = StudentAssignment(
            assignment_id=assignment4.id,
            student_id=student.id,
            classroom_id=classroom_b.id,
            title=assignment4.title,
            instructions=assignment4.description,
            due_date=assignment4.due_date,
            status=status,
            is_active=True,
        )

        if status == AssignmentStatus.IN_PROGRESS:
            student_assignment4.started_at = datetime.now() - timedelta(days=1)
        elif status == AssignmentStatus.SUBMITTED:
            student_assignment4.submitted_at = datetime.now() - timedelta(hours=6)
        else:  # GRADED
            student_assignment4.submitted_at = datetime.now() - timedelta(days=2)
            student_assignment4.graded_at = datetime.now() - timedelta(days=1)
            student_assignment4.score = 88
            student_assignment4.feedback = "做得很好！繼續保持！"

        db.add(student_assignment4)
        db.flush()

        # 建立內容進度
        for idx, content in enumerate([content1_6b, content2_6b], 1):
            if student.name == "張志豪":
                # 張志豪進行中
                if idx == 1:
                    content_status = AssignmentStatus.SUBMITTED
                else:
                    content_status = AssignmentStatus.IN_PROGRESS
                is_locked = False
            elif student.name == "林靜香":
                # 林靜香完成所有內容
                content_status = AssignmentStatus.SUBMITTED
                is_locked = False
            else:  # 測試學生
                # 已批改完成
                content_status = AssignmentStatus.GRADED
                is_locked = False

            progress = StudentContentProgress(
                student_assignment_id=student_assignment4.id,
                content_id=content.id,
                status=content_status,
                order_index=idx,
                is_locked=is_locked,
            )

            if content_status == AssignmentStatus.SUBMITTED:
                progress.started_at = datetime.now() - timedelta(days=1)
                progress.completed_at = datetime.now() - timedelta(hours=7)
                progress.response_data = {
                    "recordings": [f"recording_{i}.webm" for i in range(5)],
                    "duration": 165,
                }
                progress.ai_scores = {
                    "wpm": 78,
                    "accuracy": 0.88,
                    "fluency": 0.85,
                    "pronunciation": 0.87,
                }
            elif content_status == AssignmentStatus.IN_PROGRESS:
                progress.started_at = datetime.now() - timedelta(hours=2)
                progress.response_data = {
                    "recordings": [f"recording_{i}.webm" for i in range(2)],  # 部分完成
                    "duration": 68,
                }

            db.add(progress)

    # === 作業情境 5: 六年級B班 - 部分未指派 ===
    assignment5 = Assignment(
        title="家庭成員練習作業",
        description="學習家庭成員相關詞彙，錄製介紹家人的句子",
        classroom_id=classroom_b.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=4),
        is_active=True,
    )
    db.add(assignment5)
    db.flush()

    assignment5_content = AssignmentContent(
        assignment_id=assignment5.id, content_id=content3_6b.id, order_index=1
    )
    db.add(assignment5_content)

    # 只指派給張志豪（林靜香未被指派）
    student_assignment5 = StudentAssignment(
        assignment_id=assignment5.id,
        student_id=students_6b[0].id,  # 張志豪
        classroom_id=classroom_b.id,
        title=assignment5.title,
        instructions=assignment5.description,
        due_date=assignment5.due_date,
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    db.add(student_assignment5)
    db.flush()

    progress5 = StudentContentProgress(
        student_assignment_id=student_assignment5.id,
        content_id=content3_6b.id,
        status=AssignmentStatus.NOT_STARTED,
        order_index=1,
        is_locked=False,
    )
    db.add(progress5)

    # === 作業情境 6: 重新提交的作業（RESUBMITTED）===
    assignment6 = Assignment(
        title="數字練習 - 訂正版",
        description="請根據老師的回饋重新錄製",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=2),
        is_active=True,
    )
    db.add(assignment6)
    db.flush()

    assignment6_content = AssignmentContent(
        assignment_id=assignment6.id, content_id=content3_5a.id, order_index=1
    )
    db.add(assignment6_content)

    # 指派給李小美（測試重新提交流程）
    student_assignment6 = StudentAssignment(
        assignment_id=assignment6.id,
        student_id=students_5a[1].id,  # 李小美
        classroom_id=classroom_a.id,
        title=assignment6.title,
        instructions=assignment6.description,
        due_date=assignment6.due_date,
        status=AssignmentStatus.RESUBMITTED,
        is_active=True,
    )
    student_assignment6.submitted_at = datetime.now() - timedelta(days=3)  # 第一次提交
    student_assignment6.returned_at = datetime.now() - timedelta(days=2)  # 🔥 被退回
    student_assignment6.resubmitted_at = datetime.now() - timedelta(hours=6)  # 🔥 重新提交
    student_assignment6.graded_at = datetime.now() - timedelta(hours=2)  # 批改完成

    db.add(student_assignment6)
    db.flush()

    progress6 = StudentContentProgress(
        student_assignment_id=student_assignment6.id,
        content_id=content3_5a.id,
        status=AssignmentStatus.RESUBMITTED,
        order_index=1,
        is_locked=False,
    )
    progress6.started_at = datetime.now() - timedelta(days=3)
    progress6.completed_at = datetime.now() - timedelta(hours=3)  # 今天重新提交
    progress6.response_data = {
        "recordings": [f"recording_v2_{i}.webm" for i in range(5)],  # 第二版錄音
        "duration": 115,
    }
    db.add(progress6)

    # === 作業情境 7: 六年級B班 - 待訂正狀態 ===
    assignment7 = Assignment(
        title="興趣愛好對話練習",
        description="練習談論個人興趣與嗜好的對話",
        classroom_id=classroom_b.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(days=2),
        is_active=True,
    )
    db.add(assignment7)
    db.flush()

    # 使用 Lesson 3 的內容
    lesson_6b_3 = lessons_6b_advanced[2]  # Unit 3: Hobbies

    # 為這個 lesson 創建新的 content
    content_hobby = Content(
        lesson_id=lesson_6b_3.id,
        type=ContentType.READING_ASSESSMENT,
        title="興趣愛好對話",
        order_index=1,
        is_public=False,
        items=[
            {"text": "What are your hobbies?", "translation": "你的興趣是什麼？"},
            {"text": "I enjoy playing sports", "translation": "我喜歡運動"},
            {"text": "Reading is my favorite", "translation": "閱讀是我的最愛"},
            {"text": "I like listening to music", "translation": "我喜歡聽音樂"},
            {"text": "Let's play together", "translation": "我們一起玩吧"},
        ],
        target_wpm=70,
        target_accuracy=0.85,
        time_limit_seconds=180,
        level="A2",
        tags=["hobbies", "conversation"],
        is_active=True,
    )
    db.add(content_hobby)
    db.flush()

    assignment7_content = AssignmentContent(
        assignment_id=assignment7.id, content_id=content_hobby.id, order_index=1
    )
    db.add(assignment7_content)

    # 指派給測試學生（展示 RETURNED 狀態）
    student_assignment7 = StudentAssignment(
        assignment_id=assignment7.id,
        student_id=students_6b[2].id,  # 測試學生
        classroom_id=classroom_b.id,
        title=assignment7.title,
        instructions=assignment7.description,
        due_date=assignment7.due_date,
        status=AssignmentStatus.RETURNED,  # 待訂正
        score=70,
        feedback="第2句和第4句的發音需要加強，請重新錄製",
        is_active=True,
    )
    student_assignment7.submitted_at = datetime.now() - timedelta(days=1)
    student_assignment7.graded_at = datetime.now() - timedelta(hours=8)
    student_assignment7.returned_at = datetime.now() - timedelta(
        hours=8
    )  # 🔥 設置 returned_at

    db.add(student_assignment7)
    db.flush()

    progress7 = StudentContentProgress(
        student_assignment_id=student_assignment7.id,
        content_id=content_hobby.id,
        status=AssignmentStatus.RETURNED,
        score=70,
        order_index=1,
        is_locked=False,
        checked=False,  # 未通過
        feedback="請注意 'sports' 和 'music' 的發音",
    )
    progress7.started_at = datetime.now() - timedelta(days=2)
    progress7.completed_at = datetime.now() - timedelta(days=1)
    db.add(progress7)

    # ============ 8. 增強作業資料：全面展示所有狀態組合 ============
    print("\n📝 建立增強作業資料：全面狀態展示...")

    # 所有可能的狀態
    all_statuses = [
        AssignmentStatus.NOT_STARTED,
        AssignmentStatus.IN_PROGRESS,
        AssignmentStatus.SUBMITTED,
        AssignmentStatus.GRADED,
        AssignmentStatus.RETURNED,
        AssignmentStatus.RESUBMITTED,
    ]

    # 為五年級A班創建更多作業（8個作業，展示所有狀態）
    additional_assignments_5a = []
    for i in range(8):
        assignment = Assignment(
            title=f"五年級作業{i+8} - 狀態測試",
            description=f"測試作業 {i+8}：展示 {all_statuses[i % len(all_statuses)].value} 狀態",
            classroom_id=classroom_a.id,
            teacher_id=demo_teacher.id,
            due_date=datetime.now() + timedelta(days=random.randint(1, 7)),
            is_active=True,
        )
        additional_assignments_5a.append(assignment)

    db.add_all(additional_assignments_5a)
    db.flush()

    # 關聯基本內容
    for assignment in additional_assignments_5a:
        assignment_content = AssignmentContent(
            assignment_id=assignment.id,
            content_id=content1_5a.id,  # 使用基礎問候語練習
            order_index=1,
        )
        db.add(assignment_content)

    # 為五年級A班學生指派作業（展示所有狀態）
    for i, assignment in enumerate(additional_assignments_5a):
        for j, student in enumerate(students_5a):
            # 前6個作業確保每種狀態都有代表
            if i < 6:
                if j == i:
                    status = all_statuses[i]
                elif j == (i + 6) % len(students_5a):  # 每個作業再加一個已完成學生
                    status = AssignmentStatus.GRADED
                else:
                    # 增加 GRADED 狀態的機率
                    status_pool = all_statuses + [
                        AssignmentStatus.GRADED,
                        AssignmentStatus.GRADED,
                    ]
                    status = random.choice(status_pool)
            else:
                # 後面的作業也增加已完成的機率
                status_pool = all_statuses + [
                    AssignmentStatus.GRADED,
                    AssignmentStatus.GRADED,
                ]
                status = random.choice(status_pool)

            # 根據狀態設定分數和回饋
            score = None
            feedback = None
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                # 30% 機率已完成但沒有分數（不需要評分的作業）
                if random.random() < 0.3:
                    score = None
                    feedback = (
                        "作業已完成，表現良好！"
                        if status == AssignmentStatus.GRADED
                        else "需要訂正部分內容"
                    )
                else:
                    score = random.randint(65, 95)
                    if status == AssignmentStatus.GRADED:
                        feedback = (
                            f"做得很好！分數：{score}" if score >= 80 else f"有進步空間，分數：{score}"
                        )
                    else:
                        feedback = f"分數：{score}，請根據回饋訂正後重新提交"

            student_assignment = StudentAssignment(
                assignment_id=assignment.id,
                student_id=student.id,
                classroom_id=classroom_a.id,
                title=assignment.title,
                instructions=assignment.description,
                due_date=assignment.due_date,
                status=status,
                score=score,
                feedback=feedback,
                is_active=True,
            )

            # 設定時間戳記 - 這是關鍵！
            if status != AssignmentStatus.NOT_STARTED:
                student_assignment.started_at = datetime.now() - timedelta(
                    days=random.randint(1, 5)
                )
            if status in [
                AssignmentStatus.SUBMITTED,
                AssignmentStatus.GRADED,
                AssignmentStatus.RETURNED,
                AssignmentStatus.RESUBMITTED,
            ]:
                student_assignment.submitted_at = datetime.now() - timedelta(
                    days=random.randint(0, 3)
                )
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                student_assignment.graded_at = datetime.now() - timedelta(
                    days=random.randint(0, 2)
                )
            if status == AssignmentStatus.RETURNED:
                student_assignment.returned_at = (
                    student_assignment.graded_at
                )  # 關鍵：returned_at 時間戳
            if status == AssignmentStatus.RESUBMITTED:
                # RESUBMITTED 表示經過 RETURNED 狀態，所以也要有 returned_at
                student_assignment.submitted_at = datetime.now() - timedelta(
                    days=random.randint(2, 4)
                )  # 第一次提交
                student_assignment.returned_at = datetime.now() - timedelta(
                    days=random.randint(1, 2)
                )  # 被退回
                student_assignment.resubmitted_at = datetime.now() - timedelta(
                    hours=random.randint(1, 24)
                )  # 🔥 重新提交

            db.add(student_assignment)

    # 為六年級B班創建更多作業（10個作業）
    additional_assignments_6b = []
    for i in range(10):
        assignment = Assignment(
            title=f"六年級作業{i+8} - 進階測試",
            description=f"進階測試作業 {i+8}",
            classroom_id=classroom_b.id,
            teacher_id=demo_teacher.id,
            due_date=datetime.now() + timedelta(days=random.randint(2, 10)),
            is_active=True,
        )
        additional_assignments_6b.append(assignment)

    db.add_all(additional_assignments_6b)
    db.flush()

    # 關聯內容
    for assignment in additional_assignments_6b:
        assignment_content = AssignmentContent(
            assignment_id=assignment.id,
            content_id=content1_6b.id,  # 使用日常對話練習
            order_index=1,
        )
        db.add(assignment_content)

    # 為六年級B班學生指派作業
    for i, assignment in enumerate(additional_assignments_6b):
        for j, student in enumerate(students_6b):
            # 前6個作業確保每種狀態都有代表
            if i < 6:
                if j == i:
                    status = all_statuses[i]
                elif j == (i + 1) % len(students_6b):
                    status = all_statuses[(i + 1) % len(all_statuses)]
                elif j == (i + 8) % len(students_6b):  # 增加已完成學生
                    status = AssignmentStatus.GRADED
                else:
                    # 增加 GRADED 狀態的機率
                    status_pool = all_statuses + [
                        AssignmentStatus.GRADED,
                        AssignmentStatus.GRADED,
                        AssignmentStatus.GRADED,
                    ]
                    status = random.choice(status_pool)
            else:
                # 後面的作業也增加已完成的機率
                status_pool = all_statuses + [
                    AssignmentStatus.GRADED,
                    AssignmentStatus.GRADED,
                    AssignmentStatus.GRADED,
                ]
                status = random.choice(status_pool)

            # 設定分數和回饋
            score = None
            feedback = None
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                # 25% 機率已完成但沒有分數
                if random.random() < 0.25:
                    score = None
                    feedback = (
                        "作業完成度良好" if status == AssignmentStatus.GRADED else "請根據建議進行修改"
                    )
                else:
                    score = random.randint(70, 98)
                    if status == AssignmentStatus.GRADED:
                        feedback = (
                            f"優秀表現！繼續保持！分數：{score}"
                            if score >= 85
                            else f"不錯的表現，分數：{score}"
                        )
                    else:
                        feedback = f"分數：{score}，有些地方需要加強，請重新練習"

            student_assignment = StudentAssignment(
                assignment_id=assignment.id,
                student_id=student.id,
                classroom_id=classroom_b.id,
                title=assignment.title,
                instructions=assignment.description,
                due_date=assignment.due_date,
                status=status,
                score=score,
                feedback=feedback,
                is_active=True,
            )

            # 設定時間戳記 - 重點是 returned_at 和 submitted_at 的邏輯
            if status != AssignmentStatus.NOT_STARTED:
                student_assignment.started_at = datetime.now() - timedelta(
                    days=random.randint(1, 6)
                )
            if status in [
                AssignmentStatus.SUBMITTED,
                AssignmentStatus.GRADED,
                AssignmentStatus.RETURNED,
                AssignmentStatus.RESUBMITTED,
            ]:
                student_assignment.submitted_at = datetime.now() - timedelta(
                    days=random.randint(0, 4)
                )
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                student_assignment.graded_at = datetime.now() - timedelta(
                    days=random.randint(0, 3)
                )
            if status == AssignmentStatus.RETURNED:
                student_assignment.returned_at = student_assignment.graded_at
            if status == AssignmentStatus.RESUBMITTED:
                # RESUBMITTED 必須先經過 RETURNED，所以要有 returned_at
                student_assignment.submitted_at = datetime.now() - timedelta(
                    days=random.randint(3, 5)
                )  # 第一次提交
                student_assignment.returned_at = datetime.now() - timedelta(
                    days=random.randint(1, 2)
                )  # 被退回
                student_assignment.resubmitted_at = datetime.now() - timedelta(
                    hours=random.randint(1, 48)
                )  # 🔥 重新提交

            db.add(student_assignment)

    db.commit()
    print(
        f"✅ 增強作業資料建立完成：五年級A班額外 {len(additional_assignments_5a)} 個作業，六年級B班額外 {len(additional_assignments_6b)} 個作業"
    )

    # ============ 確保王小明有所有狀態的作業 ============
    print("\n確保王小明有完整的作業狀態分布...")
    
    xiaoming = students_5a[0]  # 王小明
    
    # 檢查王小明目前的作業狀態
    existing_statuses = set()
    xiaoming_assignments = db.query(StudentAssignment).filter(StudentAssignment.student_id == xiaoming.id).all()
    for assignment in xiaoming_assignments:
        existing_statuses.add(assignment.status)
    
    print(f"王小明現有狀態: {[status.value for status in existing_statuses]}")
    
    # 為王小明添加缺失的狀態作業
    missing_statuses = set(AssignmentStatus) - existing_statuses
    if missing_statuses:
        print(f"為王小明添加缺失狀態: {[status.value for status in missing_statuses]}")
        
        for status in missing_statuses:
            # 建立新作業
            new_assignment = Assignment(
                title=f"王小明專用作業 - {status.value}",
                description=f"測試 {status.value} 狀態的作業",
                content_type="reading_assessment",
                due_date=datetime.now() + timedelta(days=7),
                estimated_minutes=15,
                teacher_id=demo_teacher.id,
                classroom_id=classroom_a.id,
                is_active=True,
            )
            db.add(new_assignment)
            db.flush()  # 取得 ID
            
            # 關聯內容
            assignment_content = AssignmentContent(
                assignment_id=new_assignment.id,
                content_id=content1_5a.id,
                order_index=1,
            )
            db.add(assignment_content)
            
            # 建立學生作業
            score = None
            feedback = None
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                score = random.randint(70, 95)
                feedback = f"測試 {status.value} 狀態的回饋"
            
            student_assignment = StudentAssignment(
                assignment_id=new_assignment.id,
                student_id=xiaoming.id,
                classroom_id=classroom_a.id,
                title=new_assignment.title,
                instructions=new_assignment.description,
                due_date=new_assignment.due_date,
                status=status,
                score=score,
                feedback=feedback,
                is_active=True,
            )
            
            # 設置時間戳
            if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED, AssignmentStatus.RETURNED, AssignmentStatus.RESUBMITTED]:
                student_assignment.submitted_at = datetime.now() - timedelta(days=2)
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                student_assignment.graded_at = datetime.now() - timedelta(days=1)
            if status == AssignmentStatus.RETURNED:
                student_assignment.returned_at = student_assignment.graded_at
            
            db.add(student_assignment)
            
            # 建立進度記錄（NOT_STARTED 不需要）
            if status != AssignmentStatus.NOT_STARTED:
                progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=content1_5a.id,
                    status="completed" if status == AssignmentStatus.GRADED else "in_progress",
                    attempts=1,
                    best_score=score if score else 0,
                )
                db.add(progress)
        
        db.commit()
        print(f"✅ 為王小明添加了 {len(missing_statuses)} 個缺失狀態的作業")
    else:
        print("王小明已有完整的作業狀態分布")

    # ============ 9. 統計顯示 ============
    print("\n📊 作業系統統計：")

    # 統計 Assignments
    total_assignments = db.query(Assignment).count()
    print(f"\n作業主表 (Assignments): {total_assignments} 個")

    # 統計 StudentAssignments 各狀態
    print("\n學生作業狀態分布 (StudentAssignments):")
    for status in AssignmentStatus:
        count = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.status == status)
            .count()
        )
        if count > 0:
            print(f"  - {status.value}: {count} 個")

    # 統計內容進度
    total_progress = db.query(StudentContentProgress).count()
    completed_progress = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.status == AssignmentStatus.SUBMITTED)
        .count()
    )
    print(f"\n內容進度記錄 (StudentContentProgress): {total_progress} 個")
    print(f"  - 已完成: {completed_progress} 個")
    print(f"  - 進行中/未開始: {total_progress - completed_progress} 個")

    print("\n" + "=" * 60)
    print("🎉 Demo 資料建立完成！")
    print("=" * 60)
    print("\n📝 測試帳號：")
    print("\n【教師登入】")
    print("  Email: demo@duotopia.com")
    print("  密碼: demo123")
    print("\n【學生登入】")
    print("  方式: 選擇教師 demo@duotopia.com → 選擇班級 → 選擇學生")
    print("\n  五年級A班:")
    print("    - 王小明: 20120101 (預設密碼)")
    print("    - 李小美: 20120101 (預設密碼)")
    print("    - 陳大雄: student456 (已改密碼)")
    print("\n  六年級B班:")
    print("    - 張志豪: 20120101 (預設密碼)")
    print("    - 林靜香: password789 (已改密碼)")
    print("\n【作業測試情境】")
    print("  1. 已批改作業：第一週基礎問候語練習")
    print("  2. 多內容進行中：期中綜合練習（3個內容）")
    print("  3. 退回訂正：口語會話練習（王小明）")
    print("  4. 六年級作業：日常對話綜合練習")
    print("  5. 緊急作業：顏色單字測驗（20小時後到期）")
    print("  6. 重新提交：數字練習（李小美 RESUBMITTED）")
    print("=" * 60)


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

    # 注意：我們不能用 Base.metadata.drop_all() 因為有 alembic
    # 應該用 SQL 直接 drop
    from sqlalchemy import text

    with engine.connect() as conn:
        with conn.begin():
            # Drop all tables in reverse order
            conn.execute(text("DROP TABLE IF EXISTS student_content_progress CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS assignment_contents CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS student_assignments CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS assignments CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS contents CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS lessons CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS programs CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS classroom_students CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS classrooms CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS students CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS teachers CASCADE"))
            conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE"))

            # Drop enum types
            conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS programlevel CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS assignmentstatus CASCADE"))
            conn.execute(text("DROP TYPE IF EXISTS contenttype CASCADE"))

    print("✅ 舊資料已清除")

    # 重新執行 migration
    import subprocess

    subprocess.run(["alembic", "upgrade", "head"], check=True)
    print("✅ 資料表已重新建立")

    db = Session(engine)
    try:
        create_demo_data(db)
        seed_template_programs(db)  # 加入公版課程模板
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
