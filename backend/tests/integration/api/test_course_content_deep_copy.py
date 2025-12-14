"""
測試 Issue #81: 課程複製Bug - 原始公版課程內容會被刪除
驗證課程複製時會深度複製 Content 和 ContentItem,確保原始課程不受影響

Related to Issue #81
"""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app
from database import Base, get_db
from models import (
    Teacher,
    Classroom,
    Program,
    Lesson,
    Content,
    ContentItem,
    ContentType,
)
from auth import get_password_hash

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_course_content_deep_copy.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """啟用 SQLite 外鍵約束"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """每個測試前重新創建資料庫"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_data(setup_database):
    """準備測試資料"""
    db = TestingSessionLocal()

    # 創建教師
    teacher = Teacher(
        id=1,
        name="測試教師",
        email="teacher@test.com",
        password_hash=get_password_hash("password123"),
        email_verified=True,
        is_active=True,
    )
    db.add(teacher)
    db.commit()

    # 創建兩個教室
    classroom1 = Classroom(id=1, name="測試教室1", teacher_id=1, is_active=True)
    classroom2 = Classroom(id=2, name="測試教室2", teacher_id=1, is_active=True)
    db.add(classroom1)
    db.add(classroom2)
    db.commit()

    # 創建公版課程 (is_template=True, no classroom_id)
    template_program = Program(
        id=1,
        name="公版課程",
        teacher_id=1,
        classroom_id=None,  # 公版課程沒有 classroom_id
        is_template=True,
        is_active=True,
        description="公版課程描述",
    )
    db.add(template_program)
    db.commit()

    # 創建公版課程的單元
    template_lesson = Lesson(
        id=1,
        program_id=1,
        name="公版單元1",
        order_index=1,
        is_active=True,
        description="公版單元描述",
    )
    db.add(template_lesson)
    db.commit()

    # 創建公版課程的內容
    template_content = Content(
        id=1,
        lesson_id=1,
        title="公版內容1",
        type=ContentType.EXAMPLE_SENTENCES,
        order_index=1,
        is_active=True,
    )
    db.add(template_content)
    db.commit()

    # 創建公版內容的 ContentItem (3個例句)
    content_item1 = ContentItem(
        id=1,
        content_id=1,
        order_index=1,
        text="Good morning",
        translation="早安",
        audio_url="https://example.com/audio1.mp3",
    )
    content_item2 = ContentItem(
        id=2,
        content_id=1,
        order_index=2,
        text="Good afternoon",
        translation="午安",
        audio_url="https://example.com/audio2.mp3",
    )
    content_item3 = ContentItem(
        id=3,
        content_id=1,
        order_index=3,
        text="Good evening",
        translation="晚安",
        audio_url="https://example.com/audio3.mp3",
    )
    db.add(content_item1)
    db.add(content_item2)
    db.add(content_item3)
    db.commit()

    # 創建班級課程 (is_template=False, has classroom_id)
    classroom_program = Program(
        id=2,
        name="班級課程",
        teacher_id=1,
        classroom_id=1,
        is_template=False,
        is_active=True,
        description="班級課程描述",
    )
    db.add(classroom_program)
    db.commit()

    # 創建班級課程的單元
    classroom_lesson = Lesson(
        id=2,
        program_id=2,
        name="班級單元1",
        order_index=1,
        is_active=True,
    )
    db.add(classroom_lesson)
    db.commit()

    # 創建班級課程的內容
    classroom_content = Content(
        id=2,
        lesson_id=2,
        title="班級內容1",
        type=ContentType.EXAMPLE_SENTENCES,
        order_index=1,
        is_active=True,
    )
    db.add(classroom_content)
    db.commit()

    # 創建班級內容的 ContentItem
    classroom_item1 = ContentItem(
        id=4,
        content_id=2,
        order_index=1,
        text="Hello world",
        translation="你好世界",
        audio_url="https://example.com/audio4.mp3",
    )
    classroom_item2 = ContentItem(
        id=5,
        content_id=2,
        order_index=2,
        text="How are you",
        translation="你好嗎",
        audio_url="https://example.com/audio5.mp3",
    )
    db.add(classroom_item1)
    db.add(classroom_item2)
    db.commit()

    db.close()

    return {
        "teacher_id": 1,
        "classroom1_id": 1,
        "classroom2_id": 2,
        "template_program_id": 1,
        "classroom_program_id": 2,
    }


def get_auth_token():
    """取得教師認證 token"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": "teacher@test.com", "password": "password123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestProgramCopyMechanism:
    """測試課程複製機制 (Issue #81)"""

    def test_copy_from_template_preserves_original_content(self, test_data):
        """
        測試：從公版課程複製到班級時,公版課程內容不會消失

        這是 Issue #81 的核心問題 - Bug Reproduction Test
        """
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        db = TestingSessionLocal()

        # 驗證公版課程初始狀態 (有 3 個 ContentItem)
        original_items_before = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == 1)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(original_items_before) == 3
        assert original_items_before[0].text == "Good morning"
        assert original_items_before[1].text == "Good afternoon"
        assert original_items_before[2].text == "Good evening"

        db.close()

        # 從公版課程複製到班級
        response = client.post(
            "/api/programs/copy-from-template",
            headers=headers,
            json={
                "template_id": 1,
                "classroom_id": 1,
                "name": "複製的課程",
            },
        )

        assert response.status_code == 200
        result = response.json()
        copied_program_id = result["id"]

        db = TestingSessionLocal()

        # 驗證：公版課程的 ContentItem 必須完整保留 (Issue #81 的測試重點)
        original_items_after = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == 1)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(original_items_after) == 3, "公版課程的 ContentItem 不應該消失!"
        assert original_items_after[0].text == "Good morning"
        assert original_items_after[1].text == "Good afternoon"
        assert original_items_after[2].text == "Good evening"

        # 驗證：複製的課程也有完整的 ContentItem
        copied_program = (
            db.query(Program).filter(Program.id == copied_program_id).first()
        )
        assert copied_program is not None
        assert copied_program.is_template is False
        assert copied_program.classroom_id == 1

        copied_lessons = (
            db.query(Lesson).filter(Lesson.program_id == copied_program_id).all()
        )
        assert len(copied_lessons) == 1

        copied_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[0].id).all()
        )
        assert len(copied_contents) == 1

        copied_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copied_contents[0].id)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(copied_items) == 3, "複製的課程應該有完整的 ContentItem"
        assert copied_items[0].text == "Good morning"
        assert copied_items[1].text == "Good afternoon"
        assert copied_items[2].text == "Good evening"

        # 驗證：兩者的 ContentItem ID 不同 (證明是深度複製,不是移動)
        original_ids = {item.id for item in original_items_after}
        copied_ids = {item.id for item in copied_items}
        assert original_ids.isdisjoint(copied_ids), "應該是深度複製,不是移動!"

        db.close()

    def test_copy_from_classroom_preserves_original_content(self, test_data):
        """
        測試：從班級課程複製到另一個班級時,原班級課程內容不會消失

        這是 Issue #81 的延伸問題 - copy_from_classroom 也有類似 bug
        """
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        db = TestingSessionLocal()

        # 驗證原班級課程初始狀態 (有 2 個 ContentItem)
        original_items_before = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == 2)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(original_items_before) == 2
        assert original_items_before[0].text == "Hello world"
        assert original_items_before[1].text == "How are you"

        db.close()

        # 從班級1的課程複製到班級2
        response = client.post(
            "/api/programs/copy-from-classroom",
            headers=headers,
            json={
                "source_program_id": 2,
                "target_classroom_id": 2,
                "name": "複製的班級課程",
            },
        )

        assert response.status_code == 200
        result = response.json()
        copied_program_id = result["id"]

        db = TestingSessionLocal()

        # 驗證：原班級課程的 ContentItem 必須完整保留
        original_items_after = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == 2)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(original_items_after) == 2, "原班級課程的 ContentItem 不應該消失!"
        assert original_items_after[0].text == "Hello world"
        assert original_items_after[1].text == "How are you"

        # 驗證：複製的課程也有完整的 ContentItem
        copied_program = (
            db.query(Program).filter(Program.id == copied_program_id).first()
        )
        assert copied_program is not None
        assert copied_program.classroom_id == 2

        copied_lessons = (
            db.query(Lesson).filter(Lesson.program_id == copied_program_id).all()
        )
        assert len(copied_lessons) == 1

        copied_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[0].id).all()
        )
        assert len(copied_contents) == 1, "複製的課程應該有 Content"

        copied_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copied_contents[0].id)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(copied_items) == 2, "複製的課程應該有完整的 ContentItem"
        assert copied_items[0].text == "Hello world"
        assert copied_items[1].text == "How are you"

        # 驗證：兩者的 ContentItem ID 不同 (證明是深度複製)
        original_ids = {item.id for item in original_items_after}
        copied_ids = {item.id for item in copied_items}
        assert original_ids.isdisjoint(copied_ids), "應該是深度複製,不是移動!"

        db.close()

    def test_modifying_copied_program_does_not_affect_template(self, test_data):
        """測試：修改複製後的課程不會影響公版課程"""
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 從公版課程複製
        response = client.post(
            "/api/programs/copy-from-template",
            headers=headers,
            json={
                "template_id": 1,
                "classroom_id": 1,
                "name": "複製的課程",
            },
        )
        assert response.status_code == 200
        copied_program_id = response.json()["id"]

        db = TestingSessionLocal()

        # 取得複製課程的 content
        copied_lessons = (
            db.query(Lesson).filter(Lesson.program_id == copied_program_id).all()
        )
        copied_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[0].id).all()
        )
        copied_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copied_contents[0].id)
            .order_by(ContentItem.order_index)
            .all()
        )

        # 修改複製課程的第一個 ContentItem
        copied_items[0].text = "Modified text"
        db.commit()
        db.close()

        # 驗證：公版課程沒有被影響
        db = TestingSessionLocal()
        original_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == 1)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(original_items) == 3
        assert original_items[0].text == "Good morning", "公版課程不應該被修改!"

        db.close()

    def test_copy_program_with_multiple_lessons_and_contents(self, test_data):
        """測試：複製包含多個 lessons 和 contents 的課程"""
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        db = TestingSessionLocal()

        # 為公版課程添加第二個 lesson 和 content
        lesson2 = Lesson(
            id=3,
            program_id=1,
            name="公版單元2",
            order_index=2,
            is_active=True,
        )
        db.add(lesson2)
        db.commit()

        content2 = Content(
            id=3,
            lesson_id=3,
            title="公版內容2",
            type=ContentType.EXAMPLE_SENTENCES,
            order_index=1,
            is_active=True,
        )
        db.add(content2)
        db.commit()

        item6 = ContentItem(
            id=6,
            content_id=3,
            order_index=1,
            text="Test item 6",
            translation="測試項目6",
        )
        db.add(item6)
        db.commit()
        db.close()

        # 複製公版課程
        response = client.post(
            "/api/programs/copy-from-template",
            headers=headers,
            json={
                "template_id": 1,
                "classroom_id": 1,
                "name": "複製的多單元課程",
            },
        )
        assert response.status_code == 200
        copied_program_id = response.json()["id"]

        db = TestingSessionLocal()

        # 驗證：公版課程的所有內容都保留
        original_lesson1_items = (
            db.query(ContentItem).join(Content).filter(Content.lesson_id == 1).all()
        )
        assert len(original_lesson1_items) == 3

        original_lesson2_items = (
            db.query(ContentItem).join(Content).filter(Content.lesson_id == 3).all()
        )
        assert len(original_lesson2_items) == 1

        # 驗證：複製課程有完整的結構
        copied_lessons = (
            db.query(Lesson)
            .filter(Lesson.program_id == copied_program_id)
            .order_by(Lesson.order_index)
            .all()
        )
        assert len(copied_lessons) == 2

        # 驗證第一個 lesson 的 contents
        copied_lesson1_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[0].id).all()
        )
        assert len(copied_lesson1_contents) == 1

        copied_lesson1_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copied_lesson1_contents[0].id)
            .all()
        )
        assert len(copied_lesson1_items) == 3

        # 驗證第二個 lesson 的 contents
        copied_lesson2_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[1].id).all()
        )
        assert len(copied_lesson2_contents) == 1

        copied_lesson2_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copied_lesson2_contents[0].id)
            .all()
        )
        assert len(copied_lesson2_items) == 1

        db.close()

    def test_copy_program_skips_inactive_lessons_and_contents(self, test_data):
        """測試：複製課程時跳過已軟刪除的 lessons 和 contents"""
        token = get_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        db = TestingSessionLocal()

        # 為公版課程添加一個軟刪除的 lesson
        deleted_lesson = Lesson(
            id=4,
            program_id=1,
            name="已刪除單元",
            order_index=3,
            is_active=False,  # 軟刪除
        )
        db.add(deleted_lesson)
        db.commit()

        # 為第一個 lesson 添加一個軟刪除的 content
        deleted_content = Content(
            id=4,
            lesson_id=1,
            title="已刪除內容",
            type=ContentType.EXAMPLE_SENTENCES,
            order_index=2,
            is_active=False,  # 軟刪除
        )
        db.add(deleted_content)
        db.commit()

        db.close()

        # 複製公版課程
        response = client.post(
            "/api/programs/copy-from-template",
            headers=headers,
            json={
                "template_id": 1,
                "classroom_id": 1,
                "name": "複製的課程(跳過刪除)",
            },
        )
        assert response.status_code == 200
        copied_program_id = response.json()["id"]

        db = TestingSessionLocal()

        # 驗證：只複製了 is_active=True 的 lessons
        copied_lessons = (
            db.query(Lesson).filter(Lesson.program_id == copied_program_id).all()
        )
        assert len(copied_lessons) == 1, "不應該複製軟刪除的 lesson"

        # 驗證：只複製了 is_active=True 的 contents
        copied_contents = (
            db.query(Content).filter(Content.lesson_id == copied_lessons[0].id).all()
        )
        assert len(copied_contents) == 1, "不應該複製軟刪除的 content"

        db.close()
