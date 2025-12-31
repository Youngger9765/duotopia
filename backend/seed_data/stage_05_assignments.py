"""
Stage 5: Assignment and Activity Setup
Creates assignments, student assignments, and activity submissions
"""
from seed_data.utils import *


def seed_assignments(
    db: Session,
    users_data: dict,
    classrooms_data: dict,
    students_data: dict,
    programs_data: dict,
):
    """
    Stage 5: Create assignments and activities

    Args:
        users_data: Dictionary from Stage 1
        classrooms_data: Dictionary from Stage 2
        students_data: Dictionary from Stage 3
        programs_data: Dictionary from Stage 4

    Returns:
        dict: Dictionary containing created assignments
    """
    demo_teacher = users_data["demo_teacher"]
    demo_class = classrooms_data["demo_class"]
    xiaoming = students_data["xiaoming"]
    xiaohong = students_data["xiaohong"]
    xiaohua = students_data["xiaohua"]
    xiaogang = students_data["xiaogang"]
    xiaomei = students_data["xiaomei"]
    xiaoqiang = students_data["xiaoqiang"]
    beginner_program = programs_data["beginner_program"]
    intermediate_program = programs_data["intermediate_program"]
    advanced_program = programs_data["advanced_program"]

    # Get organization data for organization assignments
    org_owner_teacher = users_data.get("org_owner_teacher")
    miaoli_class1 = classrooms_data.get("miaoli_class1")
    miaoli_students = students_data.get("miaoli_students", [])

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
    xiaoming_assignments = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.student_id == xiaoming.id)
        .all()
    )
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
                due_date=datetime.now() + timedelta(days=7),
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
            if status in [
                AssignmentStatus.SUBMITTED,
                AssignmentStatus.GRADED,
                AssignmentStatus.RETURNED,
                AssignmentStatus.RESUBMITTED,
            ]:
                student_assignment.submitted_at = datetime.now() - timedelta(days=2)
            if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                student_assignment.graded_at = datetime.now() - timedelta(days=1)
            if status == AssignmentStatus.RETURNED:
                student_assignment.returned_at = student_assignment.graded_at

            db.add(student_assignment)
            db.flush()  # 取得 student_assignment.id

            # 建立進度記錄（NOT_STARTED 不需要）
            if status != AssignmentStatus.NOT_STARTED:
                progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=content1_5a.id,
                    status=status,
                    score=score if score else None,
                )
                db.add(progress)

        db.commit()
        print(f"✅ 為王小明添加了 {len(missing_statuses)} 個缺失狀態的作業")
    else:
        print("王小明已有完整的作業狀態分布")

    # ============ 8.5 建立 StudentItemProgress 測試資料（含 AI 評估）============
    print("\n📝 建立 StudentItemProgress 測試資料（含 AI 評估）...")

    # 為第一個作業建立一些測試的錄音和 AI 評估資料
    # 先查詢第一個作業的 StudentAssignment
    test_student_assignments = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.status.in_(
                [
                    AssignmentStatus.IN_PROGRESS,
                    AssignmentStatus.SUBMITTED,
                    AssignmentStatus.GRADED,
                ]
            )
        )
        .limit(3)
        .all()
    )

    # 查詢 ContentItem 記錄
    test_content_items = db.query(ContentItem).order_by(ContentItem.id).limit(5).all()

    student_item_progress_records = []

    if test_student_assignments and test_content_items:
        from decimal import Decimal
        import json

        for student_assignment in test_student_assignments[:2]:  # 只為前兩個學生作業建立
            for idx, content_item in enumerate(
                test_content_items[:3]
            ):  # 每個作業建立 3 個題目的進度
                progress = StudentItemProgress(
                    student_assignment_id=student_assignment.id,
                    content_item_id=content_item.id,
                    recording_url=(
                        f"https://storage.googleapis.com/duotopia-audio/recordings/"
                        f"test_{student_assignment.id}_{content_item.id}.webm"
                    ),
                    submitted_at=datetime.now()
                    - timedelta(hours=random.randint(1, 24)),
                    accuracy_score=Decimal(str(round(random.uniform(75, 95), 2))),
                    fluency_score=Decimal(str(round(random.uniform(70, 90), 2))),
                    pronunciation_score=Decimal(str(round(random.uniform(65, 95), 2))),
                    ai_feedback=json.dumps(
                        {
                            "completeness_score": round(random.uniform(80, 100), 2),
                            "word_details": [
                                {
                                    "word": content_item.text.split()[0]
                                    if content_item.text
                                    else "Hello",
                                    "accuracy_score": round(random.uniform(70, 95), 2),
                                    "error_type": None
                                    if random.random() > 0.3
                                    else "mispronunciation",
                                }
                            ],
                            "suggestions": "Good pronunciation overall. Keep practicing!"
                            if idx == 0
                            else None,
                        }
                    ),
                    ai_assessed_at=datetime.now()
                    - timedelta(hours=random.randint(1, 20)),
                    status="COMPLETED" if idx < 2 else "SUBMITTED",
                    attempts=random.randint(1, 3),
                )
                student_item_progress_records.append(progress)

        if student_item_progress_records:
            db.add_all(student_item_progress_records)
            db.commit()
            print(
                f"✅ 建立 {len(student_item_progress_records)} 個 StudentItemProgress 記錄（含 AI 評估）"
            )

    # ============ 8.6 為組織班級建立作業 ============
    print("\n📝 為組織班級建立作業資料...")

    # 為每個學校班級建立一個簡單作業
    org_assignments_created = 0
    for classroom, school in school_classrooms[:10]:  # 只為前10個班級建立作業
        # 建立作業
        assignment = Assignment(
            title=f"{school.display_name}-{classroom.name[:10]}作業",
            description=f"請完成{classroom.name}的練習作業",
            classroom_id=classroom.id,
            teacher_id=classroom.teacher_id,
            due_date=datetime.now() + timedelta(days=7),
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        # 為該班級的學生建立 StudentAssignment
        students_in_class = (
            db.query(ClassroomStudent)
            .filter(ClassroomStudent.classroom_id == classroom.id)
            .limit(5)  # 每班只為前5個學生建立
            .all()
        )

        for cs in students_in_class:
            student_assignment = StudentAssignment(
                assignment_id=assignment.id,
                student_id=cs.student_id,
                classroom_id=classroom.id,
                title=assignment.title,
                status=random.choice(
                    [
                        AssignmentStatus.NOT_STARTED,
                        AssignmentStatus.IN_PROGRESS,
                        AssignmentStatus.SUBMITTED,
                    ]
                ),
                instructions=assignment.description,
                due_date=assignment.due_date,
                is_active=True,
            )
            db.add(student_assignment)

        org_assignments_created += 1

    # 為 org_classroom_a 和 org_classroom_b 建立作業
    for org_classroom, classroom_name in [
        (org_classroom_a, "機構初級A班"),
        (org_classroom_b, "機構進階B班"),
    ]:
        assignment = Assignment(
            title=f"{classroom_name}期末測驗",
            description=f"{classroom_name}期末綜合練習",
            classroom_id=org_classroom.id,
            teacher_id=org_classroom.teacher_id,
            due_date=datetime.now() + timedelta(days=14),
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        # 為該班學生建立 StudentAssignment
        students_in_class = (
            db.query(ClassroomStudent)
            .filter(ClassroomStudent.classroom_id == org_classroom.id)
            .all()
        )

        for cs in students_in_class:
            student_assignment = StudentAssignment(
                assignment_id=assignment.id,
                student_id=cs.student_id,
                classroom_id=org_classroom.id,
                title=assignment.title,
                status=random.choice(
                    [
                        AssignmentStatus.NOT_STARTED,
                        AssignmentStatus.IN_PROGRESS,
                        AssignmentStatus.SUBMITTED,
                    ]
                ),
                instructions=assignment.description,
                due_date=assignment.due_date,
                is_active=True,
            )
            db.add(student_assignment)

        org_assignments_created += 1

    db.commit()
    print(f"✅ 為組織班級建立 {org_assignments_created} 個作業")

    # Return created assignments
    return {
        "assignments_created": True,
    }
