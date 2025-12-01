"""
測試派作業時的權限過濾：
1. 公版課程：所有老師都能看到
2. 班級課程：只能看到自己班級的課程
3. 作業副本：不應該出現在課程列表中
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Base, Teacher, SubscriptionPeriod, Classroom, Program, Lesson, Content, ContentItem
from routers.auth import get_password_hash
from database import get_db
from datetime import datetime, timedelta, timezone

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 啟用 SQLite 外鍵約束
from sqlalchemy import event
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def test_data():
    """設置測試數據"""
    db = TestingSessionLocal()
    
    try:
        # 清空資料庫
        db.query(ContentItem).delete()
        db.query(Content).delete()
        db.query(Lesson).delete()
        db.query(Program).delete()
        db.query(Classroom).delete()
        db.query(SubscriptionPeriod).delete()
        db.query(Teacher).delete()
        db.commit()

        # 創建兩個老師
        teacher1 = Teacher(
            id=1,
            name="老師A",
            email="teacher1@test.com",
            password_hash=get_password_hash("password123"),
        )
        teacher2 = Teacher(
            id=2,
            name="老師B",
            email="teacher2@test.com",
            password_hash=get_password_hash("password123"),
        )
        db.add(teacher1)
        db.add(teacher2)
        db.flush()

        # 為兩個老師創建訂閱
        sub1 = SubscriptionPeriod(
            teacher_id=1,
            quota_total=10000,
            quota_used=0,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
            plan_name="Basic",
        )
        sub2 = SubscriptionPeriod(
            teacher_id=2,
            quota_total=10000,
            quota_used=0,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc) + timedelta(days=30),
            is_active=True,
            plan_name="Basic",
        )
        db.add(sub1)
        db.add(sub2)
        db.flush()

        # 老師 A 創建班級 1
        classroom1 = Classroom(
            id=1,
            name="班級 A-1",
            teacher_id=1,
        )
        # 老師 B 創建班級 2
        classroom2 = Classroom(
            id=2,
            name="班級 B-1",
            teacher_id=2,
        )
        db.add(classroom1)
        db.add(classroom2)
        db.flush()

        # 創建公版課程（is_template=True，不屬於任何班級）
        template_program = Program(
            id=1,
            name="公版課程",
            teacher_id=1,  # 由老師 A 創建
            is_template=True,
            classroom_id=None,
            is_active=True,
        )
        db.add(template_program)
        db.flush()

        # 老師 A 在班級 1 中創建課程
        classroom1_program = Program(
            id=2,
            name="班級 A-1 的課程",
            teacher_id=1,
            is_template=False,
            classroom_id=1,
            is_active=True,
        )
        db.add(classroom1_program)
        db.flush()

        # 老師 B 在班級 2 中創建課程
        classroom2_program = Program(
            id=3,
            name="班級 B-1 的課程",
            teacher_id=2,
            is_template=False,
            classroom_id=2,
            is_active=True,
        )
        db.add(classroom2_program)
        db.flush()

        # 為每個課程創建單元和內容
        for program in [template_program, classroom1_program, classroom2_program]:
            lesson = Lesson(
                program_id=program.id,
                name=f"{program.name} 單元 1",
                order_index=1,
                is_active=True,
            )
            db.add(lesson)
            db.flush()

            content = Content(
                lesson_id=lesson.id,
                title=f"{program.name} 內容 1",
                type="reading_assessment",
                order_index=1,
                is_active=True,
                is_assignment_copy=False,  # 正常內容
            )
            db.add(content)
            db.flush()

            # 添加一個 ContentItem
            item = ContentItem(
                content_id=content.id,
                order_index=1,
                text="Hello",
                translation="你好",
            )
            db.add(item)

        # 創建一個作業副本內容（應該被過濾掉）
        lesson_for_copy = Lesson(
            program_id=template_program.id,
            name="測試單元（用於副本）",
            order_index=2,
            is_active=True,
        )
        db.add(lesson_for_copy)
        db.flush()

        assignment_copy_content = Content(
            lesson_id=lesson_for_copy.id,
            title="作業副本內容",
            type="reading_assessment",
            order_index=1,
            is_active=True,
            is_assignment_copy=True,  # 🔥 標記為作業副本
            source_content_id=None,
        )
        db.add(assignment_copy_content)
        db.flush()

        db.commit()

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

    yield

    # 清理
    db = TestingSessionLocal()
    try:
        db.query(ContentItem).delete()
        db.query(Content).delete()
        db.query(Lesson).delete()
        db.query(Program).delete()
        db.query(Classroom).delete()
        db.query(SubscriptionPeriod).delete()
        db.query(Teacher).delete()
        db.commit()
    finally:
        db.close()


def get_teacher_token(email: str, password: str) -> str:
    """獲取老師的登入 token"""
    response = client.post(
        "/api/auth/teacher/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestAssignmentPermissionFiltering:
    """測試派作業時的權限過濾"""

    def test_teacher_can_see_template_programs(self, test_data):
        """測試：老師可以看到公版課程"""
        token = get_teacher_token("teacher1@test.com", "password123")
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get(
            "/api/teachers/programs?is_template=true",
            headers=headers,
        )
        assert response.status_code == 200
        programs = response.json()

        # 應該能看到公版課程
        template_names = [p["name"] for p in programs]
        assert "公版課程" in template_names

    def test_teacher_can_only_see_own_classroom_programs(self, test_data):
        """測試：老師只能看到自己班級的課程"""
        # 老師 A 查詢班級 1 的課程
        token_a = get_teacher_token("teacher1@test.com", "password123")
        headers_a = {"Authorization": f"Bearer {token_a}"}

        response_a = client.get(
            "/api/teachers/programs?classroom_id=1",
            headers=headers_a,
        )
        assert response_a.status_code == 200
        programs_a = response_a.json()

        # 老師 A 應該能看到班級 1 的課程
        classroom1_names = [p["name"] for p in programs_a]
        assert "班級 A-1 的課程" in classroom1_names

        # 老師 A 查詢班級 2 的課程（不屬於他）
        response_a_cross = client.get(
            "/api/teachers/programs?classroom_id=2",
            headers=headers_a,
        )
        assert response_a_cross.status_code == 200
        programs_a_cross = response_a_cross.json()

        # 老師 A 應該看不到班級 2 的課程（因為他不擁有班級 2）
        assert len(programs_a_cross) == 0

    def test_assignment_copy_content_not_visible(self, test_data):
        """測試：作業副本內容不應該出現在課程列表中"""
        token = get_teacher_token("teacher1@test.com", "password123")
        headers = {"Authorization": f"Bearer {token}"}

        # 獲取公版課程
        response = client.get(
            "/api/teachers/programs?is_template=true",
            headers=headers,
        )
        assert response.status_code == 200
        programs = response.json()

        # 檢查公版課程的內容
        for program in programs:
            if program["name"] == "公版課程":
                for lesson in program.get("lessons", []):
                    for content in lesson.get("contents", []):
                        # 作業副本內容不應該出現
                        assert content["title"] != "作業副本內容"

    def test_teacher_cannot_access_other_teacher_classroom_programs(self, test_data):
        """測試：老師 B 無法看到老師 A 的班級課程"""
        # 老師 B 嘗試查詢老師 A 的班級 1
        token_b = get_teacher_token("teacher2@test.com", "password123")
        headers_b = {"Authorization": f"Bearer {token_b}"}

        response_b = client.get(
            "/api/teachers/programs?classroom_id=1",
            headers=headers_b,
        )
        assert response_b.status_code == 200
        programs_b = response_b.json()

        # 老師 B 應該看不到任何結果（因為班級 1 不屬於他）
        assert len(programs_b) == 0

