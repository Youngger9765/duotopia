"""
Seed data for Duotopia - 新作業系統架構
建立完整的 Demo 資料：教師、學生、班級、課程、作業
覆蓋所有作業系統情境（教師端和學生端）
"""
from datetime import datetime, date, timedelta
import random
from sqlalchemy.orm import Session
from database import engine, Base
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

    # 五年級A班學生
    students_5a = [
        Student(
            name="王小明",
            email="student1@duotopia.com",
            password_hash=get_password_hash("mynewpassword123"),  # 改過密碼
            birthdate=common_birthdate,
            student_id="S001",
            target_wpm=60,
            target_accuracy=0.75,
            password_changed=True,
            is_active=True,
        ),
        Student(
            name="李小美",
            email="student2@duotopia.com",
            password_hash=common_password,  # 使用預設密碼
            birthdate=common_birthdate,
            student_id="S002",
            target_wpm=65,
            target_accuracy=0.80,
            is_active=True,
        ),
        Student(
            name="陳大雄",
            email="student3@duotopia.com",
            password_hash=get_password_hash("student456"),  # 改過密碼
            birthdate=common_birthdate,
            student_id="S003",
            target_wpm=55,
            target_accuracy=0.70,
            password_changed=True,
            is_active=True,
        ),
    ]

    # 六年級B班學生
    students_6b = [
        Student(
            name="張志豪",
            email="student4@duotopia.com",
            password_hash=common_password,  # 使用預設密碼
            birthdate=common_birthdate,
            student_id="S004",
            target_wpm=70,
            target_accuracy=0.85,
            is_active=True,
        ),
        Student(
            name="林靜香",
            email="student5@duotopia.com",
            password_hash=get_password_hash("password789"),  # 改過密碼
            birthdate=common_birthdate,
            student_id="S005",
            target_wpm=75,
            target_accuracy=0.88,
            password_changed=True,
            is_active=True,
        ),
    ]

    all_students = students_5a + students_6b
    db.add_all(all_students)
    db.commit()
    print(f"✅ 建立 {len(all_students)} 位學生（2位使用預設密碼，3位已更改密碼）")

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

    # === 作業情境 1: 單一內容作業（已完成批改）===
    assignment1 = Assignment(
        title="第一週基礎問候語練習",
        description="請完成基礎問候語的朗讀練習，注意發音準確度",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() - timedelta(days=2),  # 已過期
        is_active=True,
    )
    db.add(assignment1)
    db.flush()

    # 關聯內容
    assignment1_content = AssignmentContent(
        assignment_id=assignment1.id, content_id=content1_5a.id, order_index=1
    )
    db.add(assignment1_content)

    # 指派給五年級A班所有學生
    for student in students_5a:
        if student.name == "王小明":
            status = AssignmentStatus.GRADED
            score = 92.5
            feedback = "發音清晰，語調自然！繼續保持！"
        elif student.name == "李小美":
            status = AssignmentStatus.SUBMITTED
            score = None
            feedback = None
        else:
            status = AssignmentStatus.NOT_STARTED
            score = None
            feedback = None

        student_assignment1 = StudentAssignment(
            assignment_id=assignment1.id,
            student_id=student.id,
            classroom_id=classroom_a.id,
            title=assignment1.title,  # 暫時保留以兼容
            instructions=assignment1.description,
            due_date=assignment1.due_date,
            status=status,
            score=score,
            feedback=feedback,
            is_active=True,
        )

        if status == AssignmentStatus.GRADED:
            student_assignment1.submitted_at = datetime.now() - timedelta(days=3)
            student_assignment1.graded_at = datetime.now() - timedelta(days=2, hours=12)
        elif status == AssignmentStatus.SUBMITTED:
            student_assignment1.submitted_at = datetime.now() - timedelta(
                days=2, hours=6
            )

        db.add(student_assignment1)
        db.flush()

        # 建立內容進度
        progress = StudentContentProgress(
            student_assignment_id=student_assignment1.id,
            content_id=content1_5a.id,
            status=status,
            score=score if status == AssignmentStatus.GRADED else None,
            order_index=1,
            is_locked=False,
            checked=True if status == AssignmentStatus.GRADED else None,
            feedback=feedback if status == AssignmentStatus.GRADED else None,
        )

        if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED]:
            progress.started_at = datetime.now() - timedelta(days=3, hours=2)
            progress.completed_at = datetime.now() - timedelta(days=3)
            progress.response_data = {
                "recordings": [f"recording_{i}.webm" for i in range(5)],
                "duration": 156,
            }

            if status == AssignmentStatus.GRADED:
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

    # === 作業情境 2: 多內容作業（進行中）===
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
    for idx, content in enumerate([content1_5a, content2_5a, content3_5a], 1):
        assignment_content = AssignmentContent(
            assignment_id=assignment2.id, content_id=content.id, order_index=idx
        )
        db.add(assignment_content)

    # 指派給五年級A班所有學生
    for student in students_5a:
        if student.name == "王小明":
            status = AssignmentStatus.IN_PROGRESS
        elif student.name == "李小美":
            status = AssignmentStatus.IN_PROGRESS
        else:
            status = AssignmentStatus.NOT_STARTED

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

        if status == AssignmentStatus.IN_PROGRESS:
            student_assignment2.started_at = datetime.now() - timedelta(hours=2)

        db.add(student_assignment2)
        db.flush()

        # 建立多個內容的進度
        for idx, content in enumerate([content1_5a, content2_5a, content3_5a], 1):
            if student.name == "王小明":
                # 王小明完成了前兩個內容
                if idx <= 2:
                    content_status = AssignmentStatus.SUBMITTED
                    is_locked = False
                else:
                    content_status = AssignmentStatus.NOT_STARTED
                    is_locked = False  # 第三個已解鎖但未開始
            elif student.name == "李小美":
                # 李小美只完成第一個
                if idx == 1:
                    content_status = AssignmentStatus.SUBMITTED
                    is_locked = False
                elif idx == 2:
                    content_status = AssignmentStatus.IN_PROGRESS
                    is_locked = False
                else:
                    content_status = AssignmentStatus.NOT_STARTED
                    is_locked = True  # 第三個還鎖著
            else:
                # 其他學生都還沒開始
                content_status = AssignmentStatus.NOT_STARTED
                is_locked = idx > 1  # 只有第一個解鎖

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

    # === 作業情境 4: 六年級的多內容進階作業 ===
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
            status = AssignmentStatus.SUBMITTED
        else:
            status = AssignmentStatus.IN_PROGRESS

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

        if status == AssignmentStatus.SUBMITTED:
            student_assignment4.submitted_at = datetime.now() - timedelta(hours=6)
        else:
            student_assignment4.started_at = datetime.now() - timedelta(days=1)

        db.add(student_assignment4)
        db.flush()

        # 建立內容進度
        for idx, content in enumerate([content1_6b, content2_6b], 1):
            if student.name == "張志豪":
                # 張志豪完成了所有內容
                content_status = AssignmentStatus.SUBMITTED
                is_locked = False
            else:
                # 林靜香完成第一個，正在做第二個
                if idx == 1:
                    content_status = AssignmentStatus.SUBMITTED
                else:
                    content_status = AssignmentStatus.IN_PROGRESS
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

    # === 作業情境 5: 即將到期的緊急作業 ===
    assignment5 = Assignment(
        title="【緊急】顏色單字測驗",
        description="明天要進行顏色單字測驗，請務必完成練習",
        classroom_id=classroom_a.id,
        teacher_id=demo_teacher.id,
        due_date=datetime.now() + timedelta(hours=20),  # 20小時後到期
        is_active=True,
    )
    db.add(assignment5)
    db.flush()

    assignment5_content = AssignmentContent(
        assignment_id=assignment5.id, content_id=content4_5a.id, order_index=1
    )
    db.add(assignment5_content)

    # 指派給五年級A班部分學生（模擬選擇性指派）
    for student in students_5a[:2]:  # 只指派給前兩個學生
        student_assignment5 = StudentAssignment(
            assignment_id=assignment5.id,
            student_id=student.id,
            classroom_id=classroom_a.id,
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
            content_id=content4_5a.id,
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
    student_assignment6.submitted_at = datetime.now() - timedelta(days=2)
    student_assignment6.graded_at = datetime.now() - timedelta(days=1)

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

    db.commit()

    # ============ 8. 統計顯示 ============
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
    print("    - 王小明: mynewpassword123 (已改密碼)")
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
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
