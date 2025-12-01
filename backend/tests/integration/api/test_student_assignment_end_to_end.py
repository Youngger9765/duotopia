"""
學生作業端到端測試 (End-to-End Student Assignment Flow)
驗證學生實際使用作業的完整流程，確保作業副本機制正確運作

這是最關鍵的測試套件，確保：
1. 學生看到的是作業副本內容
2. 學生的答案對應到正確的 ContentItem
3. 老師修改作業後學生仍能正確對應
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from main import app
from database import Base, get_db
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    StudentItemProgress,
    StudentContentProgress,
    AssignmentStatus,
    ContentType,
    SubscriptionPeriod,
)
from auth import get_password_hash

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_student_e2e.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)

# 啟用 SQLite 外鍵約束
from sqlalchemy import event

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

    # 創建有效的訂閱週期
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=10000,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
    )
    db.add(period)
    db.commit()

    # 創建班級
    classroom = Classroom(
        id=1,
        name="測試班級",
        teacher_id=teacher.id,
        is_active=True,
    )
    db.add(classroom)
    db.commit()

    # 創建學生
    student = Student(
        id=1,
        name="測試學生",
        email="student@test.com",
        password_hash=get_password_hash("password123"),
        email_verified=True,
        is_active=True,
        birthdate=datetime(2010, 1, 1).date(),  # 加上 birthdate
    )
    db.add(student)
    db.commit()

    # 將學生加入班級
    classroom_student = ClassroomStudent(
        classroom_id=classroom.id,
        student_id=student.id,
        is_active=True,
    )
    db.add(classroom_student)
    db.commit()

    # 創建課程（模板）
    program = Program(
        id=1,
        name="測試課程",
        description="測試描述",
        teacher_id=teacher.id,
        level="A1",
        is_template=False,
        is_active=True,
    )
    db.add(program)
    db.commit()

    # 創建課堂
    lesson = Lesson(
        id=1,
        name="測試課堂",
        program_id=program.id,
        order_index=1,
        is_active=True,
    )
    db.add(lesson)
    db.commit()

    # 創建內容（模板）
    content = Content(
        id=1,
        lesson_id=lesson.id,
        title="測試內容",
        type=ContentType.READING_ASSESSMENT,
        order_index=1,
        is_active=True,
        is_assignment_copy=False,  # 模板
    )
    db.add(content)
    db.commit()

    # 創建題目（模板）
    item1 = ContentItem(
        id=1,
        content_id=content.id,
        order_index=1,
        text="Good morning",
        translation="早安",
        audio_url="https://example.com/audio1.mp3",
    )
    item2 = ContentItem(
        id=2,
        content_id=content.id,
        order_index=2,
        text="Good afternoon",
        translation="午安",
        audio_url="https://example.com/audio2.mp3",
    )
    db.add(item1)
    db.add(item2)
    db.commit()

    db.close()

    yield {
        "teacher_id": 1,
        "student_id": 1,
        "classroom_id": 1,
        "program_id": 1,
        "lesson_id": 1,
        "content_id": 1,
    }


def get_teacher_auth_token():
    """獲取教師認證 token"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": "teacher@test.com", "password": "password123"},
    )
    return response.json()["access_token"]


def get_student_auth_token():
    """獲取學生認證 token"""
    response = client.post(
        "/api/auth/student/login",
        json={"id": 1, "password": "password123"},  # 學生登入使用 id，不是 email
    )
    return response.json()["access_token"]


class TestStudentAssignmentEndToEnd:
    """學生作業端到端測試"""

    def test_student_end_to_end_flow(self, test_data):
        """
        完整的端到端流程測試：
        1. 教師派作業（創建副本）
        2. 學生獲取作業（驗證看到的是副本內容）
        3. 學生提交第一題答案
        4. 驗證 StudentItemProgress 對應副本 ContentItem
        5. 教師修改第一題文字（智能更新）
        6. 學生再次獲取作業
        7. 驗證學生的答案仍在，且題目已更新
        8. 驗證 content_item_id 沒變
        """
        teacher_token = get_teacher_auth_token()
        student_token = get_student_auth_token()
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # === Step 1: 教師派作業 ===
        create_response = client.post(
            "/api/teachers/assignments/create",
            headers=teacher_headers,
            json={
                "title": "測試作業",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [test_data["content_id"]],
                "student_ids": [test_data["student_id"]],
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assert create_response.status_code == 200
        assignment_id = create_response.json()["assignment_id"]

        db = TestingSessionLocal()

        # 驗證：創建了作業副本
        assignment_contents = db.query(AssignmentContent).filter(
            AssignmentContent.assignment_id == assignment_id
        ).all()
        assert len(assignment_contents) == 1
        copy_content_id = assignment_contents[0].content_id

        copy_content = db.query(Content).filter(Content.id == copy_content_id).first()
        assert copy_content.is_assignment_copy is True  # ✅ 是副本
        assert copy_content.source_content_id == test_data["content_id"]  # ✅ 指向原始模板

        copy_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == copy_content_id)
            .order_by(ContentItem.order_index)
            .all()
        )
        assert len(copy_items) == 2
        copy_item1_id = copy_items[0].id
        copy_item2_id = copy_items[1].id
        assert copy_items[0].text == "Good morning"
        assert copy_items[1].text == "Good afternoon"

        # 獲取 StudentAssignment
        student_assignment = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.assignment_id == assignment_id,
                StudentAssignment.student_id == test_data["student_id"],
            )
            .first()
        )
        assert student_assignment is not None
        student_assignment_id = student_assignment.id

        db.close()

        # === Step 2: 學生獲取作業 ===
        get_activities_response = client.get(
            f"/api/students/assignments/{student_assignment_id}/activities",
            headers=student_headers,
        )
        assert get_activities_response.status_code == 200
        activities_data = get_activities_response.json()

        # ✅ 驗證：學生看到的是副本內容
        assert len(activities_data["activities"]) == 1
        activity = activities_data["activities"][0]
        assert activity["content_id"] == copy_content_id  # ✅ 是副本的 content_id
        assert activity["title"] == "測試內容"
        assert len(activity["items"]) == 2
        assert activity["items"][0]["id"] == copy_item1_id  # ✅ 是副本的 item_id
        assert activity["items"][0]["text"] == "Good morning"
        assert activity["items"][1]["id"] == copy_item2_id
        assert activity["items"][1]["text"] == "Good afternoon"

        # === Step 3: 學生提交第一題答案 ===
        db = TestingSessionLocal()
        student_progress = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == student_assignment_id)
            .first()
        )
        progress_id = student_progress.id
        db.close()

        save_response = client.post(
            f"/api/students/assignments/{student_assignment_id}/activities/{progress_id}/save",
            headers=student_headers,
            json={
                "audio_url": "https://example.com/student_recording1.mp3",
                "item_index": 0,
            },
        )
        assert save_response.status_code == 200

        # === Step 4: 驗證 StudentItemProgress 對應副本 ContentItem ===
        db = TestingSessionLocal()
        item_progress = (
            db.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id == student_assignment_id,
                StudentItemProgress.content_item_id == copy_item1_id,
            )
            .first()
        )
        assert item_progress is not None  # ✅ 找到進度記錄
        assert item_progress.content_item_id == copy_item1_id  # ✅ 對應到副本的 item

        # 模擬有分數
        item_progress.accuracy_score = 85.0
        db.commit()
        db.close()

        # === Step 5: 教師修改第一題文字（智能更新） ===
        update_response = client.put(
            f"/api/teachers/contents/{copy_content_id}",
            headers=teacher_headers,
            json={
                "title": "測試內容",
                "items": [
                    {
                        "text": "Hello there",  # 修改文字
                        "translation": "哈囉（修改）",
                        "audio_url": "https://example.com/audio1.mp3",  # audio_url 不變
                    },
                    {
                        "text": "Good afternoon",
                        "translation": "午安",
                        "audio_url": "https://example.com/audio2.mp3",
                    },
                ],
            },
        )
        assert update_response.status_code == 200

        # === Step 6: 學生再次獲取作業 ===
        get_activities_response2 = client.get(
            f"/api/students/assignments/{student_assignment_id}/activities",
            headers=student_headers,
        )
        assert get_activities_response2.status_code == 200
        activities_data2 = get_activities_response2.json()

        # ✅ 驗證：題目已更新
        assert activities_data2["activities"][0]["items"][0]["text"] == "Hello there"
        assert activities_data2["activities"][0]["items"][0]["translation"] == "哈囉（修改）"

        # === Step 7 & 8: 驗證學生的答案仍在，且 content_item_id 沒變 ===
        db = TestingSessionLocal()

        # 重新查詢 ContentItem（應該是同一個 ID，只是內容更新了）
        updated_item = db.query(ContentItem).filter(ContentItem.id == copy_item1_id).first()
        assert updated_item is not None
        assert updated_item.id == copy_item1_id  # ✅ ID 沒變
        assert updated_item.text == "Hello there"  # ✅ 文字已更新

        # 重新查詢 StudentItemProgress（應該仍然存在，並且對應相同的 item）
        item_progress_after = (
            db.query(StudentItemProgress)
            .filter(
                StudentItemProgress.student_assignment_id == student_assignment_id,
                StudentItemProgress.content_item_id == copy_item1_id,
            )
            .first()
        )
        assert item_progress_after is not None  # ✅ 進度記錄仍然存在
        assert item_progress_after.content_item_id == copy_item1_id  # ✅ content_item_id 沒變
        assert item_progress_after.accuracy_score == 85.0  # ✅ 分數保留

        db.close()

        print("✅ 端到端測試通過！學生流程完全正確！")

    def test_modifying_template_does_not_affect_student_assignment(self, test_data):
        """
        驗證：修改原始模板不會影響學生的作業
        """
        teacher_token = get_teacher_auth_token()
        student_token = get_student_auth_token()
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        student_headers = {"Authorization": f"Bearer {student_token}"}

        # Step 1: 派作業
        create_response = client.post(
            "/api/teachers/assignments/create",
            headers=teacher_headers,
            json={
                "title": "測試作業",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [test_data["content_id"]],
                "student_ids": [test_data["student_id"]],
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )
        assignment_id = create_response.json()["assignment_id"]

        db = TestingSessionLocal()
        student_assignment = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .first()
        )
        student_assignment_id = student_assignment.id
        db.close()

        # Step 2: 學生獲取作業（第一次）
        activities_before = client.get(
            f"/api/students/assignments/{student_assignment_id}/activities",
            headers=student_headers,
        ).json()
        original_text = activities_before["activities"][0]["items"][0]["text"]
        assert original_text == "Good morning"

        # Step 3: 教師修改**原始模板**（不是作業副本）
        update_template_response = client.put(
            f"/api/teachers/contents/{test_data['content_id']}",  # 修改原始模板
            headers=teacher_headers,
            json={
                "title": "測試內容（模板已修改）",
                "items": [
                    {
                        "text": "Modified template text",  # 修改模板
                        "translation": "修改後的模板",
                        "audio_url": "https://example.com/audio1.mp3",
                    },
                    {
                        "text": "Good afternoon",
                        "translation": "午安",
                        "audio_url": "https://example.com/audio2.mp3",
                    },
                ],
            },
        )
        assert update_template_response.status_code == 200

        # Step 4: 學生再次獲取作業
        activities_after = client.get(
            f"/api/students/assignments/{student_assignment_id}/activities",
            headers=student_headers,
        ).json()

        # ✅ 驗證：學生看到的仍然是原始文字，模板修改不影響作業副本
        assert activities_after["activities"][0]["items"][0]["text"] == "Good morning"
        assert activities_after["activities"][0]["items"][0]["text"] != "Modified template text"

        print("✅ 模板修改不影響作業副本！")

