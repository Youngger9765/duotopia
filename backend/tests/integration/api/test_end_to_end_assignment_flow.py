"""
完整的端到端測試：教師建立作業 → 學生錄音 → AI 批改
驗證新的 ContentItem 架構正確運作
"""

from sqlalchemy.orm import Session

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
    AssignmentStatus,
    Lesson,
    Program,
)


def test_complete_assignment_workflow(db_session: Session):
    """
    測試完整的作業流程：
    1. 教師建立作業
    2. 學生開啟作業
    3. 學生錄音上傳
    4. 檢查所有資料正確建立
    """

    # ===== 1. 準備測試資料 =====
    print("\n🏗️  設置測試資料...")

    # 建立教師
    teacher = Teacher(
        name="Test Teacher", email="teacher@test.com", password_hash="hashed"
    )
    db_session.add(teacher)
    db_session.flush()

    # 建立課程架構
    program = Program(name="Test Program", description="Test", teacher_id=teacher.id)
    db_session.add(program)
    db_session.flush()

    lesson = Lesson(name="Test Lesson", program_id=program.id)
    db_session.add(lesson)
    db_session.flush()

    # 建立班級
    classroom = Classroom(name="Test Class", teacher_id=teacher.id)
    db_session.add(classroom)
    db_session.flush()

    # 建立學生
    from datetime import date

    student = Student(
        name="Test Student",
        email="student@test.com",
        password_hash="hashed",
        student_number="20230001",
        birthdate=date(2012, 1, 1),
    )
    db_session.add(student)
    db_session.flush()

    # 建立內容
    content1 = Content(
        title="Content 1 - Greetings",
        lesson_id=lesson.id,
        items=[
            {"text": "Hello", "translation": "你好"},
            {"text": "Good morning", "translation": "早安"},
        ],
    )
    content2 = Content(
        title="Content 2 - Numbers",
        lesson_id=lesson.id,
        items=[
            {"text": "One", "translation": "一"},
            {"text": "Two", "translation": "二"},
        ],
    )
    db.add_all([content1, content2])
    db_session.flush()

    # 建立 ContentItem
    content_items = []
    for content in [content1, content2]:
        for i, item_data in enumerate(content.items):
            content_item = ContentItem(
                content_id=content.id,
                order_index=i,
                text=item_data["text"],
                translation=item_data.get("translation", ""),
            )
            content_items.append(content_item)
            db_session.add(content_item)

    db_session.flush()

    print(f"✅ 建立了 {len(content_items)} 個 ContentItem")

    # ===== 2. 教師建立作業 =====
    print("\n📝 教師建立作業...")

    # 模擬 create_assignment API
    assignment = Assignment(
        title="Test Assignment",
        description="Test assignment description",
        classroom_id=classroom.id,
        teacher_id=teacher.id,
    )
    db_session.add(assignment)
    db_session.flush()

    # 建立 AssignmentContent 關聯
    assignment_contents = [
        AssignmentContent(
            assignment_id=assignment.id, content_id=content1.id, order_index=0
        ),
        AssignmentContent(
            assignment_id=assignment.id, content_id=content2.id, order_index=1
        ),
    ]
    db.add_all(assignment_contents)
    db_session.flush()

    # 為學生建立 StudentAssignment（不含 content_id！）
    student_assignment = StudentAssignment(
        assignment_id=assignment.id,
        student_id=student.id,
        classroom_id=classroom.id,
        title=assignment.title,
        instructions=assignment.description,
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    db_session.add(student_assignment)
    db_session.flush()

    # 為每個內容建立進度記錄
    for idx, ac in enumerate(assignment_contents, 1):
        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=ac.content_id,
            status=AssignmentStatus.NOT_STARTED,
            order_index=idx,
        )
        db_session.add(progress)

    db_session.commit()

    print(f"✅ 建立作業：{assignment.title}")
    print("✅ 建立 StudentAssignment（無 content_id）")
    print(f"✅ 建立 {len(assignment_contents)} 個 StudentContentProgress")

    # ===== 3. 驗證資料結構 =====
    print("\n🔍 驗證資料結構...")

    # 檢查關係鏈路
    assert student_assignment.assignment_id == assignment.id
    assert len(assignment.contents) == 2  # AssignmentContent 關聯

    # 檢查 StudentAssignment 沒有 content_id
    assert (
        not hasattr(student_assignment, "content_id")
        or student_assignment.content_id is None
    )

    # 檢查可以透過 Assignment → AssignmentContent → Content → ContentItem 找到所有題目
    all_items_via_assignment = []
    for ac in assignment.contents:
        content = ac.content
        items = content.content_items
        all_items_via_assignment.extend(items)

    print(f"✅ 透過 Assignment 找到 {len(all_items_via_assignment)} 個 ContentItem")
    assert len(all_items_via_assignment) == 4  # 2個內容 × 2個題目

    # ===== 4. 模擬學生開啟作業 =====
    print("\n🎯 模擬學生開啟作業...")

    # 模擬 get_assignment_activities API 邏輯
    progress_records = (
        db_session.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id == student_assignment.id)
        .all()
    )

    activities = []
    for progress in progress_records:
        content = db_session.query(Content).filter_by(id=progress.content_id).first()
        content_items_for_content = (
            db_session.query(ContentItem)
            .filter_by(content_id=content.id)
            .order_by(ContentItem.order_index)
            .all()
        )

        # 構建前端需要的 activity 資料結構
        activity = {
            "id": progress.id,
            "content_id": content.id,
            "title": content.title,
            "items": [
                {
                    "id": item.id,  # 關鍵：ContentItem 的 ID
                    "text": item.text,
                    "translation": item.translation,
                    "order_index": item.order_index,
                    "status": "NOT_STARTED",
                }
                for item in content_items_for_content
            ],
        }
        activities.append(activity)

    print(f"✅ 學生看到 {len(activities)} 個 activity")
    print(f"✅ 第一個 activity 有 {len(activities[0]['items'])} 個 items")

    # ===== 5. 模擬學生錄音上傳 =====
    print("\n🎤 模擬學生錄音上傳...")

    # 選擇第一個 activity 的第一個 item 進行錄音
    first_activity = activities[0]
    first_item = first_activity["items"][0]
    content_item_id = first_item["id"]

    print(f"📍 對 ContentItem {content_item_id} 錄音: '{first_item['text']}'")

    # 模擬錄音上傳 API
    content_item = db_session.query(ContentItem).filter_by(id=content_item_id).first()
    assert content_item is not None

    # 建立或更新 StudentItemProgress
    item_progress = StudentItemProgress(
        student_assignment_id=student_assignment.id,
        content_item_id=content_item_id,
        recording_url="https://storage.googleapis.com/test/recording.webm",
        status=AssignmentStatus.SUBMITTED,
    )
    db_session.add(item_progress)
    db_session.commit()

    print(f"✅ 建立 StudentItemProgress for ContentItem {content_item_id}")

    # ===== 6. 驗證完整性 =====
    print("\n✅ 驗證完整性...")

    # 檢查資料一致性
    item_progress_check = (
        db_session.query(StudentItemProgress)
        .filter_by(
            student_assignment_id=student_assignment.id, content_item_id=content_item_id
        )
        .first()
    )

    assert item_progress_check is not None
    assert item_progress_check.recording_url is not None
    assert item_progress_check.status == AssignmentStatus.SUBMITTED

    # 檢查可以反向查詢
    content_item_check = (
        db_session.query(ContentItem).filter_by(id=content_item_id).first()
    )
    content_check = content_item_check.content
    assignment_content_check = (
        db_session.query(AssignmentContent)
        .filter_by(content_id=content_check.id)
        .first()
    )
    assignment_check = assignment_content_check.assignment

    assert assignment_check.id == assignment.id

    print("🎉 端到端測試通過！")
    print("\n📊 測試結果摘要：")
    print("  • Assignment: 1 個")
    print("  • AssignmentContent: 2 個")
    print("  • Content: 2 個")
    print("  • ContentItem: 4 個")
    print("  • StudentAssignment: 1 個（無 content_id）")
    print("  • StudentContentProgress: 2 個")
    print("  • StudentItemProgress: 1 個")
    print("  • 資料關係鏈路完整 ✅")
    print("  • 錄音上傳正常 ✅")

    # 清理
    db.rollback()


if __name__ == "__main__":
    # 可以直接執行此測試
    import sys

    sys.path.append("../../..")

    print("🚀 執行端到端測試...")
    db = SessionLocal()
    try:
        test_complete_assignment_workflow(db)
    finally:
        db.close()
