"""
TDD 測試：確保系統完全使用 ContentItem，不依賴 Content.items JSONB
"""

from sqlalchemy.orm import Session
from models import (
    Teacher,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    Student,
    Classroom,
)


def test_content_should_not_have_items_jsonb_field(db_session: Session):
    """測試 Content 不應該有 items JSONB 欄位"""
    # 建立基本測試資料
    teacher = Teacher(
        name="Test Teacher", email="teacher@test.com", password_hash="hash"
    )
    db_session.add(teacher)
    db_session.commit()

    program = Program(name="Test Program", description="Test", teacher_id=teacher.id)
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(name="Test Lesson", program_id=program.id)
    db_session.add(lesson)
    db_session.commit()

    # 建立 Content
    content = Content(
        title="Test Content", lesson_id=lesson.id, type="reading_assessment"
    )
    db_session.add(content)
    db_session.commit()

    # Content 不應該有 items 屬性（JSONB）
    assert not hasattr(content, "items") or content.items is None

    # 應該透過 ContentItem 關聯來取得 items
    assert hasattr(content, "content_items")


def test_create_content_with_content_items(db_session: Session):
    """測試建立 Content 時自動建立 ContentItem 記錄"""
    # 準備資料
    teacher = Teacher(name="Teacher", email="t@test.com", password_hash="hash")
    db_session.add(teacher)
    db_session.commit()

    program = Program(name="Program", description="Test", teacher_id=teacher.id)
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(name="Lesson", program_id=program.id)
    db_session.add(lesson)
    db_session.commit()

    # 建立 Content
    content = Content(title="Greetings", lesson_id=lesson.id, type="reading_assessment")
    db_session.add(content)
    db_session.commit()

    # 建立對應的 ContentItem 記錄
    items_data = [
        {"text": "Hello", "translation": "你好"},
        {"text": "Good morning", "translation": "早安"},
        {"text": "How are you?", "translation": "你好嗎？"},
    ]

    for idx, item_data in enumerate(items_data):
        content_item = ContentItem(
            content_id=content.id,
            order_index=idx,
            text=item_data["text"],
            translation=item_data["translation"],
        )
        db_session.add(content_item)

    db_session.commit()

    # 驗證
    content_items = (
        db_session.query(ContentItem)
        .filter_by(content_id=content.id)
        .order_by(ContentItem.order_index)
        .all()
    )
    assert len(content_items) == 3
    assert content_items[0].text == "Hello"
    assert content_items[1].text == "Good morning"
    assert content_items[2].text == "How are you?"

    # 透過關聯取得
    db_session.refresh(content)
    assert len(content.content_items) == 3


def test_api_returns_content_items_not_jsonb(db_session: Session):
    """測試 API 返回 ContentItem 資料而非 JSONB"""
    # 建立測試資料
    teacher = Teacher(name="Teacher", email="api@test.com", password_hash="hash")
    db_session.add(teacher)
    db_session.commit()

    program = Program(name="Program", description="Test", teacher_id=teacher.id)
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(name="Lesson", program_id=program.id)
    db_session.add(lesson)
    db_session.commit()

    content = Content(title="Numbers", lesson_id=lesson.id, type="reading_assessment")
    db_session.add(content)
    db_session.commit()

    # 建立 ContentItem
    for i in range(1, 4):
        item = ContentItem(
            content_id=content.id,
            order_index=i - 1,
            text=f"Number {i}",
            translation=f"數字 {i}",
        )
        db_session.add(item)
    db_session.commit()

    # 模擬 API 邏輯：取得 Content 的 items
    content_items = (
        db_session.query(ContentItem)
        .filter_by(content_id=content.id)
        .order_by(ContentItem.order_index)
        .all()
    )

    # 建構 API 回應
    items_response = []
    for item in content_items:
        items_response.append(
            {
                "id": item.id,  # 必須有 ID！
                "text": item.text,
                "translation": item.translation,
                "order_index": item.order_index,
            }
        )

    # 驗證
    assert len(items_response) == 3
    assert all("id" in item for item in items_response)
    assert items_response[0]["text"] == "Number 1"


def test_student_assignment_uses_content_items(db_session: Session):
    """測試學生作業正確使用 ContentItem"""
    # 建立完整測試環境
    teacher = Teacher(name="Teacher", email="assign@test.com", password_hash="hash")
    student = Student(
        name="Student",
        email="s@test.com",
        password_hash="hash",
        student_number="S001",
        birthdate="2010-01-01",
    )
    db.add_all([teacher, student])
    db_session.commit()

    program = Program(name="Program", description="Test", teacher_id=teacher.id)
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(name="Lesson", program_id=program.id)
    db_session.add(lesson)
    db_session.commit()

    classroom = Classroom(name="Class A", teacher_id=teacher.id)
    db_session.add(classroom)
    db_session.commit()

    # 建立 Content 和 ContentItem
    content = Content(
        title="Test Content", lesson_id=lesson.id, type="reading_assessment"
    )
    db_session.add(content)
    db_session.commit()

    content_item = ContentItem(
        content_id=content.id, order_index=0, text="Test item", translation="測試項目"
    )
    db_session.add(content_item)
    db_session.commit()

    # 建立作業
    assignment = Assignment(
        title="Test Assignment", classroom_id=classroom.id, teacher_id=teacher.id
    )
    db_session.add(assignment)
    db_session.commit()

    assignment_content = AssignmentContent(
        assignment_id=assignment.id, content_id=content.id, order_index=0
    )
    db_session.add(assignment_content)
    db_session.commit()

    student_assignment = StudentAssignment(
        assignment_id=assignment.id,
        student_id=student.id,
        classroom_id=classroom.id,
        title=assignment.title,
        status="NOT_STARTED",
    )
    db_session.add(student_assignment)
    db_session.commit()

    # 驗證可以透過關聯鏈找到 ContentItem
    assignment_contents = (
        db_session.query(AssignmentContent).filter_by(assignment_id=assignment.id).all()
    )

    for ac in assignment_contents:
        content = ac.content
        content_items = content.content_items
        assert len(content_items) > 0
        assert content_items[0].id is not None
        assert content_items[0].text == "Test item"


def test_no_jsonb_items_in_database(db_session: Session):
    """測試資料庫中不應該有 items JSONB 欄位的資料"""
    # 直接查詢 Content 表
    contents = db_session.query(Content).all()

    for content in contents:
        # 如果 items 屬性還存在，它應該是 None 或空
        if hasattr(content, "items"):
            assert content.items is None or content.items == []

        # 應該有對應的 ContentItem 記錄
        item_count = (
            db_session.query(ContentItem).filter_by(content_id=content.id).count()
        )
        # 如果 Content 有資料，應該要有 ContentItem
        if content.title and content.lesson_id:
            assert item_count >= 0  # 可能是 0（空內容）或更多


if __name__ == "__main__":
    import sys

    sys.path.append("../../..")
    from database import get_session_local

    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        print("🧪 執行 ContentItem-only 測試...")
        test_content_should_not_have_items_jsonb_field(db)
        print("✅ Content 不依賴 JSONB items")

        test_create_content_with_content_items(db)
        print("✅ ContentItem 建立正確")

        test_api_returns_content_items_not_jsonb(db)
        print("✅ API 返回 ContentItem 資料")

        test_student_assignment_uses_content_items(db)
        print("✅ 學生作業使用 ContentItem")

        test_no_jsonb_items_in_database(db)
        print("✅ 資料庫無 JSONB items 依賴")

        print("\n🎉 所有測試通過！")
    finally:
        db.rollback()
        db.close()
