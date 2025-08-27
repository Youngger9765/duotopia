"""
Seed data for Duotopia
建立 Demo 教師、學生、班級、課程、作業
"""
from datetime import datetime, date, timedelta
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
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id="S001",
            target_wpm=60,
            target_accuracy=0.75
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
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id="S003",
            target_wpm=55,
            target_accuracy=0.70
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
            password_hash=common_password,
            birthdate=common_birthdate,
            student_id="S005",
            target_wpm=75,
            target_accuracy=0.88
        )
    ]
    
    all_students = students_5a + students_6b
    db.add_all(all_students)
    db.commit()
    print(f"✅ 建立 {len(all_students)} 位學生（密碼都是 20120101）")
    
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
    # Program - 課程計畫 (在五年級A班內創建)
    program = Program(
        name="國小英語基礎課程",
        description="適合國小學生的基礎英語課程",
        level=ProgramLevel.A1,
        teacher_id=demo_teacher.id,
        classroom_id=classroom_a.id,  # 在五年級A班內創建
        estimated_hours=20
    )
    db.add(program)
    db.commit()
    
    # Lesson 1 - Greetings
    lesson1 = Lesson(
        program_id=program.id,
        name="Unit 1: Greetings 打招呼",
        description="學習基本的英語問候語",
        order_index=1,
        estimated_minutes=30
    )
    
    # Lesson 2 - Numbers
    lesson2 = Lesson(
        program_id=program.id,
        name="Unit 2: Numbers 數字",
        description="學習數字 1-10",
        order_index=2,
        estimated_minutes=30
    )
    
    db.add_all([lesson1, lesson2])
    db.commit()
    
    # Content - 朗讀錄音集內容
    content1 = Content(
        lesson_id=lesson1.id,
        type=ContentType.READING_RECORDING,
        title="基礎問候語練習",
        order_index=1,
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
    
    content2 = Content(
        lesson_id=lesson2.id,
        type=ContentType.READING_RECORDING,
        title="數字 1-10 練習",
        order_index=1,
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
    
    db.add_all([content1, content2])
    db.commit()
    print("✅ 建立課程: 國小英語基礎課程 (2個單元，每個單元有朗讀錄音集)")
    
    # 注意：課程直接關聯到班級，不再需要 ClassroomProgramMapping
    print("✅ 課程已直接關聯到五年級A班")
    
    # ============ 7. Demo 作業 ============
    # 給五年級A班派發 Greetings 作業
    for student in students_5a:
        assignment1 = StudentAssignment(
            student_id=student.id,
            content_id=content1.id,
            classroom_id=classroom_a.id,
            title="Greetings 問候語練習",
            instructions="請練習錄音以下問候語，注意發音準確度",
            status=AssignmentStatus.NOT_STARTED if student.name != "王小明" else AssignmentStatus.SUBMITTED,
            due_date=datetime.now() + timedelta(days=7)
        )
        db.add(assignment1)
        
        # 王小明已完成作業 - 先 flush 以取得 assignment id
        if student.name == "王小明":
            db.flush()  # 確保 assignment1 有 id
            submission = AssignmentSubmission(
                assignment_id=assignment1.id,
                submission_data={
                    "recordings": [
                        {"text": "Hello", "audio_url": "demo_audio_1.mp3"},
                        {"text": "Good morning", "audio_url": "demo_audio_2.mp3"}
                    ]
                },
                ai_scores={
                    "wpm": 65,
                    "accuracy": 0.82,
                    "fluency": 0.78
                },
                ai_feedback="很好！發音清楚，繼續保持！"
            )
            db.add(submission)
            assignment1.submitted_at = datetime.now()
    
    # 給六年級B班派發 Numbers 作業
    for student in students_6b:
        assignment2 = StudentAssignment(
            student_id=student.id,
            content_id=content2.id,
            classroom_id=classroom_b.id,
            title="Numbers 數字練習",
            instructions="請練習錄音數字 1-10，注意語調",
            status=AssignmentStatus.NOT_STARTED,
            due_date=datetime.now() + timedelta(days=5)
        )
        db.add(assignment2)
    
    db.commit()
    print("✅ 建立作業並派發給學生")
    
    print("\n" + "="*50)
    print("🎉 Demo 資料建立完成！")
    print("="*50)
    print("\n📝 測試帳號：")
    print("教師登入: demo@duotopia.com / demo123")
    print("學生登入: 選擇教師 demo@duotopia.com → 選擇班級 → 選擇學生名字 → 密碼 20120101")
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