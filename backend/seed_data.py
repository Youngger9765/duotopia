"""
Seed data for Duotopia
建立 Demo 教師、學生、班級、課程、作業
"""
from datetime import datetime, date, timedelta
import random
from sqlalchemy.orm import Session
from database import engine, Base
from models import (
    Teacher, Student, Classroom, ClassroomStudent,
    Program, Lesson, Content,
    StudentAssignment, AssignmentSubmission,
    ProgramLevel, ContentType, AssignmentStatus
)
from auth import get_password_hash

def create_demo_data(db: Session):
    """建立完整的 demo 資料"""
    
    print("🌱 開始建立 Demo 資料...")
    
    # ============ 1. Demo 教師 ============
    demo_teacher = Teacher(
        email="demo@duotopia.com",
        password_hash=get_password_hash("demo123"),
        name="Demo 老師",
        is_demo=True,
        is_active=True
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
        is_active=True
    )
    
    classroom_b = Classroom(
        name="六年級B班",
        description="國小六年級英語進階班",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        is_active=True
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
            password_changed=True  # 標記密碼已更改
        ),
        Student(
            name="李小美",
            email="student2@duotopia.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id="S002",
            target_wpm=65,
            target_accuracy=0.80
        ),
        Student(
            name="陳大雄",
            email="student3@duotopia.com",
            password_hash=get_password_hash("student456"),  # 改過密碼
            birthdate=common_birthdate,
            student_id="S003",
            target_wpm=55,
            target_accuracy=0.70,
            password_changed=True  # 標記密碼已更改
        )
    ]
    
    # 六年級B班學生
    students_6b = [
        Student(
            name="張志豪",
            email="student4@duotopia.com",
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id="S004",
            target_wpm=70,
            target_accuracy=0.85
        ),
        Student(
            name="林靜香",
            email="student5@duotopia.com",
            password_hash=get_password_hash("password789"),  # 改過密碼
            birthdate=common_birthdate,
            student_id="S005",
            target_wpm=75,
            target_accuracy=0.88,
            password_changed=True  # 標記密碼已更改
        )
    ]
    
    all_students = students_5a + students_6b
    db.add_all(all_students)
    db.commit()
    print(f"✅ 建立 {len(all_students)} 位學生（2位使用預設密碼，3位已更改密碼）")
    
    # ============ 4. 學生加入班級 ============
    # 五年級A班
    for student in students_5a:
        enrollment = ClassroomStudent(
            classroom_id=classroom_a.id,
            student_id=student.id
        )
        db.add(enrollment)
    
    # 六年級B班
    for student in students_6b:
        enrollment = ClassroomStudent(
            classroom_id=classroom_b.id,
            student_id=student.id
        )
        db.add(enrollment)
    
    db.commit()
    print("✅ 學生已加入班級")
    
    # ============ 5. Demo 課程（三層結構）============
    # 五年級A班課程 - Program 1
    program_5a_basic = Program(
        name="五年級英語基礎課程",
        description="適合五年級學生的基礎英語課程",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_a.id,
        estimated_hours=20,
        order_index=1
    )
    
    # 五年級A班課程 - Program 2
    program_5a_conversation = Program(
        name="五年級口語會話課程",
        description="培養五年級學生的英語口語能力",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_a.id,
        estimated_hours=15,
        order_index=2
    )
    
    # 六年級B班課程 - Program 1
    program_6b_advanced = Program(
        name="六年級英語進階課程",
        description="適合六年級學生的進階英語課程",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_b.id,
        estimated_hours=25,
        order_index=1
    )
    
    # 六年級B班課程 - Program 2
    program_6b_reading = Program(
        name="六年級閱讀理解課程",
        description="提升六年級學生的英語閱讀能力",
        level=ProgramLevel.A2,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_b.id,
        estimated_hours=20,
        order_index=2
    )
    
    db.add_all([program_5a_basic, program_5a_conversation, program_6b_advanced, program_6b_reading])
    db.commit()
    
    # 五年級基礎課程的 Lessons (3個單元)
    lessons_5a_basic = [
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 1: Greetings 打招呼",
            description="學習基本的英語問候語",
            order_index=1,
            estimated_minutes=30
        ),
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 2: Numbers 數字",
            description="學習數字 1-20",
            order_index=2,
            estimated_minutes=30
        ),
        Lesson(
            program_id=program_5a_basic.id,
            name="Unit 3: Colors 顏色",
            description="學習各種顏色的英文",
            order_index=3,
            estimated_minutes=25
        )
    ]
    
    # 五年級會話課程的 Lessons (3個單元)
    lessons_5a_conversation = [
        Lesson(
            program_id=program_5a_conversation.id,
            name="Unit 1: Self Introduction 自我介紹",
            description="學習如何用英語自我介紹",
            order_index=1,
            estimated_minutes=35
        ),
        Lesson(
            program_id=program_5a_conversation.id,
            name="Unit 2: Asking Questions 提問技巧",
            description="學習如何用英語提問",
            order_index=2,
            estimated_minutes=35
        ),
        Lesson(
            program_id=program_5a_conversation.id,
            name="Unit 3: Daily Routines 日常作息",
            description="談論每日的活動安排",
            order_index=3,
            estimated_minutes=30
        )
    ]
    
    # 六年級進階課程的 Lessons (3個單元)
    lessons_6b_advanced = [
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 1: Daily Conversation 日常對話",
            description="學習日常英語對話",
            order_index=1,
            estimated_minutes=40
        ),
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 2: My Family 我的家庭",
            description="學習家庭成員相關詞彙",
            order_index=2,
            estimated_minutes=40
        ),
        Lesson(
            program_id=program_6b_advanced.id,
            name="Unit 3: Hobbies 興趣愛好",
            description="談論個人興趣與嗜好",
            order_index=3,
            estimated_minutes=35
        )
    ]
    
    # 六年級閱讀課程的 Lessons (3個單元)
    lessons_6b_reading = [
        Lesson(
            program_id=program_6b_reading.id,
            name="Unit 1: Short Stories 短篇故事",
            description="閱讀簡單的英文故事",
            order_index=1,
            estimated_minutes=45
        ),
        Lesson(
            program_id=program_6b_reading.id,
            name="Unit 2: News Articles 新聞文章",
            description="閱讀適齡的新聞內容",
            order_index=2,
            estimated_minutes=45
        ),
        Lesson(
            program_id=program_6b_reading.id,
            name="Unit 3: Poems 詩歌欣賞",
            description="欣賞簡單的英文詩歌",
            order_index=3,
            estimated_minutes=40
        )
    ]
    
    db.add_all(lessons_5a_basic + lessons_5a_conversation + lessons_6b_advanced + lessons_6b_reading)
    db.commit()
    
    # Content - 選擇第一個 lesson 來創建內容
    first_lesson_5a = lessons_5a_basic[0]
    first_lesson_6b = lessons_6b_advanced[0]
    
    # Content - 五年級A班朗讀錄音集內容
    content1_5a = Content(
        lesson_id=first_lesson_5a.id,
        type=ContentType.READING_ASSESSMENT,
        title="基礎問候語練習",
        order_index=1,
        is_public=True,  # 公開內容，其他教師可以使用
        items=[
            {"text": "Hello", "translation": "你好"},
            {"text": "Good morning", "translation": "早安"},
            {"text": "Good afternoon", "translation": "午安"},
            {"text": "Good evening", "translation": "晚安"},
            {"text": "How are you?", "translation": "你好嗎？"},
            {"text": "I'm fine, thank you", "translation": "我很好，謝謝"},
            {"text": "Nice to meet you", "translation": "很高興認識你"},
            {"text": "See you later", "translation": "待會見"},
            {"text": "Goodbye", "translation": "再見"}
        ],
        target_wpm=50,
        target_accuracy=0.75,
        time_limit_seconds=180
    )
    
    content2_5a = Content(
        lesson_id=lessons_5a_basic[1].id,
        type=ContentType.READING_ASSESSMENT,
        title="數字 1-10 練習",
        order_index=1,
        is_public=True,  # 公開內容
        items=[
            {"text": "One", "translation": "一"},
            {"text": "Two", "translation": "二"},
            {"text": "Three", "translation": "三"},
            {"text": "Four", "translation": "四"},
            {"text": "Five", "translation": "五"},
            {"text": "Six", "translation": "六"},
            {"text": "Seven", "translation": "七"},
            {"text": "Eight", "translation": "八"},
            {"text": "Nine", "translation": "九"},
            {"text": "Ten", "translation": "十"}
        ],
        target_wpm=60,
        target_accuracy=0.80,
        time_limit_seconds=120
    )
    
    # Content - 六年級B班朗讀錄音集內容
    content1_6b = Content(
        lesson_id=first_lesson_6b.id,
        type=ContentType.READING_ASSESSMENT,
        title="日常對話練習",
        order_index=1,
        is_public=False,  # 私人內容
        items=[
            {"text": "What's your name?", "translation": "你叫什麼名字？"},
            {"text": "My name is David", "translation": "我叫大衛"},
            {"text": "Where are you from?", "translation": "你來自哪裡？"},
            {"text": "I'm from Taiwan", "translation": "我來自台灣"},
            {"text": "How old are you?", "translation": "你幾歲？"},
            {"text": "I'm twelve years old", "translation": "我十二歲"},
            {"text": "Nice to meet you", "translation": "很高興認識你"}
        ],
        target_wpm=70,
        target_accuracy=0.85,
        time_limit_seconds=180
    )
    
    content2_6b = Content(
        lesson_id=lessons_6b_advanced[1].id,
        type=ContentType.READING_ASSESSMENT,
        title="家庭成員練習",
        order_index=1,
        is_public=False,  # 私人內容
        items=[
            {"text": "Father", "translation": "爸爸"},
            {"text": "Mother", "translation": "媽媽"},
            {"text": "Brother", "translation": "哥哥/弟弟"},
            {"text": "Sister", "translation": "姐姐/妹妹"},
            {"text": "Grandfather", "translation": "爺爺"},
            {"text": "Grandmother", "translation": "奶奶"},
            {"text": "This is my family", "translation": "這是我的家人"}
        ],
        target_wpm=75,
        target_accuracy=0.85,
        time_limit_seconds=150
    )
    
    db.add_all([content1_5a, content2_5a, content1_6b, content2_6b])
    db.commit()
    
    # ============ 6.5 為所有沒有內容的 Lessons 建立內容 ============
    print("📚 為所有 Lessons 建立完整內容...")
    
    # 取得所有 lessons
    all_lessons = db.query(Lesson).all()
    content_created = 0
    
    for lesson in all_lessons:
        # 檢查是否已有內容
        existing_content = db.query(Content).filter(Content.lesson_id == lesson.id).first()
        
        if not existing_content:
            # 根據 lesson 名稱生成相關的內容
            if "Introduction" in lesson.name or "自我介紹" in lesson.name:
                items = [
                    {"text": "Hello, my name is Alice.", "translation": "你好，我的名字是 Alice。"},
                    {"text": "I am ten years old.", "translation": "我十歲了。"},
                    {"text": "I like to play basketball.", "translation": "我喜歡打籃球。"},
                    {"text": "Nice to meet you!", "translation": "很高興認識你！"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Question" in lesson.name or "提問" in lesson.name:
                items = [
                    {"text": "What is your name?", "translation": "你叫什麼名字？"},
                    {"text": "Where are you from?", "translation": "你來自哪裡？"},
                    {"text": "How old are you?", "translation": "你幾歲？"},
                    {"text": "What do you like to do?", "translation": "你喜歡做什麼？"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Daily" in lesson.name or "日常" in lesson.name:
                items = [
                    {"text": "I wake up at seven o'clock.", "translation": "我七點起床。"},
                    {"text": "I eat breakfast at home.", "translation": "我在家吃早餐。"},
                    {"text": "I go to school by bus.", "translation": "我搭公車去學校。"},
                    {"text": "I do my homework after dinner.", "translation": "我晚餐後做作業。"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Family" in lesson.name or "家庭" in lesson.name:
                items = [
                    {"text": "This is my father.", "translation": "這是我的爸爸。"},
                    {"text": "My mother is a teacher.", "translation": "我媽媽是老師。"},
                    {"text": "I have one brother and one sister.", "translation": "我有一個哥哥和一個妹妹。"},
                    {"text": "We live together.", "translation": "我們住在一起。"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Color" in lesson.name or "顏色" in lesson.name:
                items = [
                    {"text": "Red", "translation": "紅色"},
                    {"text": "Blue", "translation": "藍色"},
                    {"text": "Green", "translation": "綠色"},
                    {"text": "Yellow", "translation": "黃色"},
                    {"text": "The sky is blue.", "translation": "天空是藍色的。"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Hobbies" in lesson.name or "興趣" in lesson.name:
                items = [
                    {"text": "I like reading books.", "translation": "我喜歡讀書。"},
                    {"text": "She enjoys playing piano.", "translation": "她喜歡彈鋼琴。"},
                    {"text": "We love watching movies.", "translation": "我們喜歡看電影。"},
                    {"text": "Do you like sports?", "translation": "你喜歡運動嗎？"}
                ]
                title = f"{lesson.name} - 練習"
            elif "Stories" in lesson.name or "故事" in lesson.name:
                items = [
                    {"text": "Once upon a time, there was a little girl.", "translation": "從前有一個小女孩。"},
                    {"text": "She lived in a small house.", "translation": "她住在一個小房子裡。"},
                    {"text": "Every day she went to the forest.", "translation": "她每天都去森林。"},
                    {"text": "The end.", "translation": "結束。"}
                ]
                title = f"{lesson.name} - 練習"
            else:
                # 通用內容
                items = [
                    {"text": f"This is lesson {lesson.order_index}.", "translation": f"這是第 {lesson.order_index} 課。"},
                    {"text": "Let's practice together.", "translation": "讓我們一起練習。"},
                    {"text": "Good job!", "translation": "做得好！"},
                    {"text": "Keep going!", "translation": "繼續加油！"}
                ]
                title = f"{lesson.name} - 練習"
            
            # 建立內容
            new_content = Content(
                lesson_id=lesson.id,
                type=ContentType.READING_ASSESSMENT,
                title=title,
                items=items,
                target_wpm=60,
                target_accuracy=80,
                time_limit_seconds=180,
                order_index=1,
                is_active=True
            )
            db.add(new_content)
            content_created += 1
    
    db.commit()
    print(f"✅ 建立 {content_created} 個新內容，所有 Lessons 現在都有內容了")
    print("✅ 建立課程: 每個班級有2個課程，每個課程有3個單元")
    
    # 注意：課程直接關聯到班級，不再需要 ClassroomProgramMapping
    print("✅ 課程已直接關聯到對應班級")
    
    # ============ 7. Demo 作業 (更豐富的測試資料) ============
    print("📝 建立作業測試資料...")
    
    # 清除舊的作業資料
    db.query(AssignmentSubmission).delete()
    db.query(StudentAssignment).delete()
    db.commit()
    
    assignment_count = 0
    
    # 五年級A班的作業
    contents_5a = [content1_5a, content2_5a]
    for i, content in enumerate(contents_5a):
        # 決定作業的時間和狀態
        if i == 0:
            # 已過期的作業
            due_date = datetime.now() - timedelta(days=2)
            title = f"[已過期] {content.title}"
            instructions = "這是一個已過期的作業測試"
        else:
            # 即將到期的作業（24小時內）
            due_date = datetime.now() + timedelta(hours=20)
            title = f"[即將到期] {content.title}"
            instructions = "請盡快完成此作業，即將到期！"
        
        # 為每個學生建立作業
        for j, student in enumerate(students_5a):
            # 設定不同的狀態
            if i == 0:  # 過期作業
                if j == 0:  # 王小明
                    status = AssignmentStatus.GRADED
                    score = random.randint(80, 95)
                    feedback = "做得很好！繼續加油！"
                elif j == 1:  # 李小美
                    status = AssignmentStatus.SUBMITTED
                    score = None
                    feedback = None
                else:
                    status = AssignmentStatus.NOT_STARTED
                    score = None
                    feedback = None
            else:  # 即將到期
                if j == 0:  # 王小明
                    status = AssignmentStatus.SUBMITTED
                    score = None
                    feedback = None
                elif j == 1:  # 李小美
                    status = AssignmentStatus.IN_PROGRESS
                    score = None
                    feedback = None
                else:
                    status = AssignmentStatus.NOT_STARTED
                    score = None
                    feedback = None
            
            # 建立作業
            assignment = StudentAssignment(
                student_id=student.id,
                content_id=content.id,
                classroom_id=classroom_a.id,
                title=title,
                instructions=instructions,
                status=status,
                due_date=due_date,
                score=score,
                feedback=feedback
            )
            
            # 如果是已提交或已批改的，設定提交時間
            if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED]:
                assignment.submitted_at = datetime.now() - timedelta(days=1)
            
            # 如果是已批改的，設定批改時間
            if status == AssignmentStatus.GRADED:
                assignment.graded_at = datetime.now() - timedelta(hours=12)
            
            db.add(assignment)
            assignment_count += 1
            
            # 如果作業已提交，建立提交記錄
            if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED]:
                db.flush()  # 確保 assignment 有 id
                
                submission = AssignmentSubmission(
                    assignment_id=assignment.id,
                    submission_data={
                        "audio_urls": [
                            f"gs://duotopia-audio/demo/{student.id}/recording_{k}.mp3"
                            for k in range(3)
                        ]
                    },
                    ai_scores={
                        "wpm": random.randint(60, 120),
                        "accuracy": round(random.uniform(0.7, 0.95), 2),
                        "fluency": round(random.uniform(0.6, 0.9), 2),
                        "pronunciation": round(random.uniform(0.65, 0.95), 2)
                    } if status == AssignmentStatus.GRADED else None,
                    ai_feedback="AI 評分：發音清晰，語調自然。建議加強連音練習。" if status == AssignmentStatus.GRADED else None
                )
                db.add(submission)
    
    # 六年級B班的作業
    contents_6b = [content1_6b, content2_6b]
    for content in contents_6b[:1]:  # 只用第一個 Content
        # 正常的作業（7天後到期）
        due_date = datetime.now() + timedelta(days=7)
        title = f"{content.title} - 練習作業"
        instructions = "請認真完成練習，注意發音準確度"
        
        for j, student in enumerate(students_6b):
            if j == 0:
                status = AssignmentStatus.RETURNED  # 需修正
                score = 65
                feedback = "請重新錄音第2和第3題，注意發音"
            elif j == 1:
                status = AssignmentStatus.IN_PROGRESS
                score = None
                feedback = None
            else:
                status = AssignmentStatus.NOT_STARTED
                score = None
                feedback = None
            
            assignment = StudentAssignment(
                student_id=student.id,
                content_id=content.id,
                classroom_id=classroom_b.id,
                title=title,
                instructions=instructions,
                status=status,
                due_date=due_date,
                score=score,
                feedback=feedback
            )
            
            if status == AssignmentStatus.RETURNED:
                assignment.submitted_at = datetime.now() - timedelta(days=2)
                assignment.graded_at = datetime.now() - timedelta(days=1)
            
            db.add(assignment)
            assignment_count += 1
    
    db.commit()
    print(f"✅ 建立 {assignment_count} 個作業記錄")
    
    # 顯示統計
    print("\n📊 作業統計：")
    for status in AssignmentStatus:
        count = db.query(StudentAssignment).filter(
            StudentAssignment.status == status
        ).count()
        if count > 0:
            print(f"  - {status.value}: {count} 個")
    
    print("\n" + "="*50)
    print("🎉 Demo 資料建立完成！")
    print("="*50)
    print("\n📝 測試帳號：")
    print("教師登入: demo@duotopia.com / demo123")
    print("學生登入: 選擇教師 demo@duotopia.com → 選擇班級 → 選擇學生名字")
    print("  - 預設密碼: 20120101 (李小美、張志豪)")
    print("  - 已更改密碼的學生:")
    print("    * 王小明: mynewpassword123")
    print("    * 陳大雄: student456")
    print("    * 林靜香: password789")
    print("="*50)

def reset_database():
    """重置資料庫並建立 seed data"""
    print("⚠️  正在重置資料庫...")
    Base.metadata.drop_all(bind=engine)
    print("✅ 舊資料已清除")
    
    Base.metadata.create_all(bind=engine)
    print("✅ 資料表已建立")
    
    db = Session(engine)
    try:
        create_demo_data(db)
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()