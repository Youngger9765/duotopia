"""
完整的作業流程端到端測試
測試從教師建立作業到學生收到批改結果的完整流程
"""

from datetime import datetime, date, timedelta
from database import SessionLocal
from models import (
    Teacher,
    Student,
    Classroom,
    Assignment,
    AssignmentContent,
    Content,
    ContentItem,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    ClassroomStudent,
    AssignmentStatus,
    Lesson,
    Program,
)


def test_complete_assignment_lifecycle():
    """
    測試完整作業流程:
    1. 教師建立作業
    2. 派發作業給學生
    3. 學生拿到作業
    4. 學生答題（至少兩題）
    5. 檢查答案儲存位置
    6. 學生提交作業
    7. 教師批改每題
    8. 教師給總評
    9. 學生看到批改結果
    """

    db = SessionLocal()
    print("\n" + "=" * 60)
    print("🚀 開始完整作業流程測試")
    print("=" * 60)

    try:
        # ========== 1. 教師建立作業 ==========
        print("\n📚 步驟 1: 教師建立作業")
        print("-" * 40)

        # 建立教師
        teacher = Teacher(
            name="張老師",
            email=f"teacher_{datetime.now().timestamp()}@test.com",
            password_hash="hashed",
        )
        db.add(teacher)
        db.flush()
        print(f"✅ 建立教師: {teacher.name} (ID: {teacher.id})")

        # 建立班級
        classroom = Classroom(name="五年級A班", teacher_id=teacher.id)
        db.add(classroom)
        db.flush()
        print(f"✅ 建立班級: {classroom.name} (ID: {classroom.id})")

        # 建立課程結構
        program = Program(name="英語會話課程", description="基礎英語對話練習", teacher_id=teacher.id)
        db.add(program)
        db.flush()

        lesson = Lesson(name="第一課：日常問候", program_id=program.id)
        db.add(lesson)
        db.flush()

        # 建立內容和題目
        content1 = Content(
            title="基礎問候語", lesson_id=lesson.id, items=[]  # 使用 ContentItem 而非 JSON
        )
        db.add(content1)
        db.flush()

        # 建立具體題目（ContentItem）
        items = [
            ContentItem(
                content_id=content1.id,
                order_index=0,
                text="Good morning! How are you today?",
                translation="早安！你今天好嗎？",
            ),
            ContentItem(
                content_id=content1.id,
                order_index=1,
                text="Nice to meet you. My name is John.",
                translation="很高興認識你。我叫約翰。",
            ),
            ContentItem(
                content_id=content1.id,
                order_index=2,
                text="Thank you very much for your help.",
                translation="非常感謝你的幫助。",
            ),
        ]
        for item in items:
            db.add(item)
        db.flush()
        print(f"✅ 建立 {len(items)} 個題目")

        # 建立作業
        assignment = Assignment(
            title="每日英語問候練習",
            description="請朗讀以下英文句子",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            due_date=datetime.now() + timedelta(days=7),
        )
        db.add(assignment)
        db.flush()
        print(f"✅ 建立作業: {assignment.title} (ID: {assignment.id})")

        # 關聯作業與內容
        assignment_content = AssignmentContent(
            assignment_id=assignment.id, content_id=content1.id, order_index=0
        )
        db.add(assignment_content)
        db.flush()

        # ========== 2. 派發作業給學生 ==========
        print("\n👥 步驟 2: 派發作業給學生")
        print("-" * 40)

        # 建立學生
        students = []
        for i in range(3):
            student = Student(
                name=f"學生{i+1}",
                email=f"student{i+1}_{datetime.now().timestamp()}@test.com",
                password_hash="hashed",
                student_number=f"S202300{i+1}",
                birthdate=date(2012, 1, 1),
            )
            db.add(student)
            students.append(student)
        db.flush()
        print(f"✅ 建立 {len(students)} 位學生")

        # 學生加入班級
        for student in students:
            classroom_student = ClassroomStudent(
                classroom_id=classroom.id, student_id=student.id
            )
            db.add(classroom_student)
        db.flush()
        print("✅ 學生已加入班級")

        # 派發作業給學生
        student_assignments = []
        for student in students:
            sa = StudentAssignment(
                assignment_id=assignment.id,
                student_id=student.id,
                classroom_id=classroom.id,
                title=assignment.title,
                instructions=assignment.description,
                due_date=assignment.due_date,
                status=AssignmentStatus.NOT_STARTED,
            )
            db.add(sa)
            student_assignments.append(sa)
        db.flush()
        print(f"✅ 派發作業給 {len(student_assignments)} 位學生")

        # 為每個學生建立內容進度
        for sa in student_assignments:
            progress = StudentContentProgress(
                student_assignment_id=sa.id,
                content_id=content1.id,
                status=AssignmentStatus.NOT_STARTED,
                order_index=0,
            )
            db.add(progress)
        db.flush()

        # ========== 3. 驗證學生拿到作業 ==========
        print("\n📖 步驟 3: 驗證學生拿到作業")
        print("-" * 40)

        test_student = students[0]
        test_assignment = student_assignments[0]

        # 模擬學生查看作業
        student_check = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.student_id == test_student.id,
                StudentAssignment.id == test_assignment.id,
            )
            .first()
        )

        assert student_check is not None, "學生無法找到作業"
        print(f"✅ 學生 {test_student.name} 成功取得作業")

        # 檢查學生能看到題目
        content_progress = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == test_assignment.id)
            .first()
        )

        content_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == content_progress.content_id)
            .order_by(ContentItem.order_index)
            .all()
        )

        assert len(content_items) == 3, f"預期 3 題，實際 {len(content_items)} 題"
        print(f"✅ 學生看到 {len(content_items)} 個題目")
        for idx, item in enumerate(content_items):
            print(f"   題目 {idx+1}: {item.text[:30]}...")

        # ========== 4. 學生答題（至少兩題）==========
        print("\n✍️ 步驟 4: 學生答題")
        print("-" * 40)

        # 學生回答前兩題
        answered_items = content_items[:2]
        item_progresses = []

        for idx, item in enumerate(answered_items):
            # 模擬學生錄音上傳
            item_progress = StudentItemProgress(
                student_assignment_id=test_assignment.id,
                content_item_id=item.id,
                recording_url=(
                    f"https://storage.googleapis.com/recordings/"
                    f"student_{test_student.id}_item_{item.id}.webm"
                ),
                submitted_at=datetime.now(),
                status="SUBMITTED",
                attempts=1,
            )
            db.add(item_progress)
            item_progresses.append(item_progress)
            print(f"✅ 學生完成第 {idx+1} 題: {item.text[:30]}...")

        db.flush()

        # ========== 5. 檢查答案儲存位置 ==========
        print("\n🔍 步驟 5: 檢查答案儲存位置")
        print("-" * 40)

        # 驗證答案儲存在 StudentItemProgress
        saved_answers = (
            db.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == test_assignment.id)
            .all()
        )

        assert len(saved_answers) == 2, f"預期 2 個答案，實際 {len(saved_answers)} 個"
        print(f"✅ StudentItemProgress 表中找到 {len(saved_answers)} 個答案記錄")

        for answer in saved_answers:
            print(f"   - ContentItem {answer.content_item_id}: {answer.recording_url}")
            assert answer.recording_url is not None, "錄音 URL 不應為空"
            assert answer.submitted_at is not None, "提交時間不應為空"

        # ========== 6. 學生提交作業 ==========
        print("\n📤 步驟 6: 學生提交作業")
        print("-" * 40)

        # 更新作業狀態為已提交
        test_assignment.status = AssignmentStatus.SUBMITTED
        test_assignment.submitted_at = datetime.now()

        # 更新內容進度狀態
        content_progress.status = AssignmentStatus.SUBMITTED
        content_progress.completed_at = datetime.now()

        db.flush()
        print(f"✅ 作業狀態更新為: {test_assignment.status.value}")
        print(f"✅ 提交時間: {test_assignment.submitted_at}")

        # ========== 7. 教師批改每題（AI 評分）==========
        print("\n🤖 步驟 7: AI 自動評分")
        print("-" * 40)

        # 模擬 AI 評分
        for idx, item_progress in enumerate(item_progresses):
            # AI 評分
            item_progress.accuracy_score = 85.5 + idx * 5  # 85.5, 90.5
            item_progress.fluency_score = 80.0 + idx * 3
            item_progress.pronunciation_score = 82.0 + idx * 4
            item_progress.ai_feedback = f"第{idx+1}題: 發音清晰，但語調可以更自然一些。"
            item_progress.ai_assessed_at = datetime.now()

            print(f"✅ AI 評分第 {idx+1} 題:")
            print(f"   準確度: {item_progress.accuracy_score}")
            print(f"   流暢度: {item_progress.fluency_score}")
            print(f"   發音: {item_progress.pronunciation_score}")

        db.flush()

        # ========== 8. 教師給總評 ==========
        print("\n👨‍🏫 步驟 8: 教師批改和總評")
        print("-" * 40)

        # 教師對整個內容群組的評價（StudentContentProgress）
        content_progress.score = 88.0  # 內容總分
        content_progress.feedback = "整體表現不錯，第一題的語調很自然，第二題需要注意連音。繼續加油！"
        content_progress.checked = True

        # 教師對整份作業的總評（StudentAssignment）
        test_assignment.score = 88.0  # 作業總分
        test_assignment.feedback = """
        整體評語：
        1. 發音清晰度有進步
        2. 語調掌握良好
        3. 建議多練習連音部分

        繼續保持這樣的學習態度！
        """
        test_assignment.status = AssignmentStatus.GRADED
        test_assignment.graded_at = datetime.now()

        db.flush()
        print(f"✅ 內容評分: {content_progress.score} 分")
        print(f"✅ 作業總分: {test_assignment.score} 分")
        print(f"✅ 批改狀態: {test_assignment.status.value}")

        # ========== 9. 驗證學生看到批改結果 ==========
        print("\n👁️ 步驟 9: 驗證學生看到批改結果")
        print("-" * 40)

        # 學生查看作業狀態
        student_view = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.id == test_assignment.id)
            .first()
        )

        assert student_view.status == AssignmentStatus.GRADED, "作業狀態應為已批改"
        assert student_view.score is not None, "應有總分"
        assert student_view.feedback is not None, "應有總評"

        print(f"✅ 學生看到作業狀態: {student_view.status.value}")
        print(f"✅ 學生看到總分: {student_view.score} 分")
        print(f"✅ 學生看到總評: {student_view.feedback[:50]}...")

        # 學生查看每題的 AI 評分
        student_item_progress = (
            db.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == test_assignment.id)
            .all()
        )

        print("\n📊 學生看到各題評分:")
        for idx, progress in enumerate(student_item_progress):
            print(f"   第 {idx+1} 題:")
            print(f"      準確度: {progress.accuracy_score}")
            print(f"      AI 評語: {progress.ai_feedback}")

        # 學生查看內容評價
        student_content_progress = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == test_assignment.id)
            .first()
        )

        print(f"\n✅ 學生看到內容評價: {student_content_progress.feedback[:50]}...")

        # ========== 測試完成 ==========
        print("\n" + "=" * 60)
        print("🎉 完整作業流程測試通過！")
        print("=" * 60)

        print("\n📈 測試統計:")
        print("  • 建立教師: 1 位")
        print("  • 建立班級: 1 個")
        print(f"  • 建立學生: {len(students)} 位")
        print(f"  • 建立題目: {len(items)} 題")
        print(f"  • 學生答題: {len(item_progresses)} 題")
        print(f"  • AI 評分: {len(item_progresses)} 題")
        print("  • 教師總評: 1 份")

        print("\n✅ 資料流程驗證:")
        print("  1. 作業建立 ✓")
        print("  2. 作業派發 ✓")
        print("  3. 學生接收 ✓")
        print("  4. 學生答題 ✓")
        print("  5. 答案儲存位置正確 ✓")
        print("  6. 作業提交 ✓")
        print("  7. AI 評分 ✓")
        print("  8. 教師總評 ✓")
        print("  9. 學生查看結果 ✓")

        db.commit()
        print("\n✅ 資料已提交到資料庫")

    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_complete_assignment_lifecycle()
