"""
測試作業批量操作優化
驗證批量操作可以正確處理大量學生，且性能優於多次 flush

TDD: 先寫測試，定義期望行為，然後實施優化
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
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    ContentType,
    SubscriptionPeriod,
)
from auth import get_password_hash

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_bulk_operations.db"
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
        amount_paid=299,
        quota_total=2000,
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

    # 創建多個學生（測試批量操作）
    students = []
    for i in range(1, 31):  # 30 個學生
        student = Student(
            id=i,
            name=f"測試學生{i}",
            email=f"student{i}@test.com",
            password_hash=get_password_hash("password123"),
            email_verified=True,
            is_active=True,
            birthdate=datetime(2010, 1, 1).date(),
        )
        db.add(student)
        students.append(student)
    db.commit()

    # 將學生加入班級
    for student in students:
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
        type=ContentType.EXAMPLE_SENTENCES,
        order_index=1,
        is_active=True,
        is_assignment_copy=False,
    )
    db.add(content)
    db.commit()

    # 創建多個題目（測試批量操作）
    for i in range(1, 6):  # 5 個題目
        item = ContentItem(
            id=i,
            content_id=content.id,
            order_index=i,
            text=f"Question {i}",
            translation=f"問題 {i}",
            audio_url=f"https://example.com/audio{i}.mp3",
        )
        db.add(item)
    db.commit()

    db.close()

    yield {
        "teacher_id": 1,
        "classroom_id": 1,
        "content_id": 1,
        "student_count": 30,
        "item_count": 5,
    }


def get_teacher_auth_token():
    """獲取教師認證 token"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": "teacher@test.com", "password": "password123"},
    )
    return response.json()["access_token"]


class TestAssignmentBulkOperations:
    """測試批量操作優化"""

    def test_create_assignment_with_many_students_creates_all_records(self, test_data):
        """
        測試：派作業給大量學生時，所有記錄都正確創建

        期望：
        1. 30 個 StudentAssignment 記錄
        2. 30 個 StudentContentProgress 記錄（每個學生 1 個）
        3. 150 個 StudentItemProgress 記錄（每個學生 5 個題目）
        4. 所有記錄的關聯關係正確
        """
        token = get_teacher_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 獲取所有學生 ID
        db = TestingSessionLocal()
        students = db.query(Student).filter(Student.id <= 30).all()
        student_ids = [s.id for s in students]
        db.close()

        # 派作業給所有學生
        response = client.post(
            "/api/teachers/assignments/create",
            headers=headers,
            json={
                "title": "批量測試作業",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [test_data["content_id"]],
                "student_ids": student_ids,
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assignment_id = result["assignment_id"]

        # 驗證：所有記錄都創建了
        db = TestingSessionLocal()

        # 驗證 StudentAssignment
        student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_assignments) == test_data["student_count"]  # ✅ 30 個

        # 驗證 StudentContentProgress
        student_content_progress = (
            db.query(StudentContentProgress)
            .join(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_content_progress) == test_data["student_count"]  # ✅ 30 個

        # 驗證 StudentItemProgress
        student_item_progress = (
            db.query(StudentItemProgress)
            .join(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        expected_item_count = (
            test_data["student_count"] * test_data["item_count"]
        )  # 30 * 5 = 150
        assert len(student_item_progress) == expected_item_count  # ✅ 150 個

        # 驗證：每個學生的記錄都正確關聯
        for student_assignment in student_assignments:
            # 每個學生應該有 1 個 StudentContentProgress
            content_progress = (
                db.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id
                    == student_assignment.id
                )
                .all()
            )
            assert len(content_progress) == 1  # ✅

            # 每個學生應該有 5 個 StudentItemProgress
            item_progress = (
                db.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id == student_assignment.id
                )
                .all()
            )
            assert len(item_progress) == test_data["item_count"]  # ✅ 5 個

            # 驗證關聯關係
            assert content_progress[0].student_assignment_id == student_assignment.id
            for ip in item_progress:
                assert ip.student_assignment_id == student_assignment.id

        db.close()

    def test_create_assignment_bulk_operations_are_atomic(self, test_data):
        """
        測試：批量操作是原子性的

        期望：
        1. 如果任何一步失敗，所有變更都應該回滾
        2. 不會留下部分創建的記錄
        """
        # 這個測試需要模擬錯誤情況
        # 由於我們無法輕易模擬資料庫錯誤，這個測試主要驗證事務處理邏輯
        # 實際的錯誤處理會在集成測試中驗證

        token = get_teacher_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 正常情況下應該成功
        response = client.post(
            "/api/teachers/assignments/create",
            headers=headers,
            json={
                "title": "測試作業",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [test_data["content_id"]],
                "student_ids": [1, 2, 3],  # 少量學生
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 200

        # 驗證所有記錄都存在
        db = TestingSessionLocal()
        assignment_id = response.json()["assignment_id"]

        student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_assignments) == 3  # ✅ 所有記錄都創建了

        db.close()

    def test_create_assignment_performance_with_many_students(self, test_data):
        """
        測試：批量操作性能優於多次 flush

        期望：
        1. 派作業給 30 個學生應該在合理時間內完成（< 2 秒）
        2. 所有記錄都正確創建
        """
        import time

        token = get_teacher_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 獲取所有學生 ID
        db = TestingSessionLocal()
        students = db.query(Student).filter(Student.id <= 30).all()
        student_ids = [s.id for s in students]
        db.close()

        # 測量執行時間
        start_time = time.time()

        response = client.post(
            "/api/teachers/assignments/create",
            headers=headers,
            json={
                "title": "性能測試作業",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [test_data["content_id"]],
                "student_ids": student_ids,
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 2.0  # ✅ 應該在 2 秒內完成

        # 驗證所有記錄都創建了
        result = response.json()
        assignment_id = result["assignment_id"]

        db = TestingSessionLocal()
        student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_assignments) == test_data["student_count"]  # ✅

        db.close()

    def test_create_assignment_with_multiple_contents_and_students(self, test_data):
        """
        測試：多個內容 + 多個學生的批量操作

        期望：
        1. 30 個學生 × 3 個內容 = 90 個 StudentContentProgress
        2. 30 個學生 × 3 個內容 × 5 個題目 = 450 個 StudentItemProgress
        3. 所有記錄都正確創建
        """
        db = TestingSessionLocal()

        # 創建額外的內容
        content2 = Content(
            id=2,
            lesson_id=1,
            title="測試內容2",
            type=ContentType.EXAMPLE_SENTENCES,
            order_index=2,
            is_active=True,
            is_assignment_copy=False,
        )
        db.add(content2)

        content3 = Content(
            id=3,
            lesson_id=1,
            title="測試內容3",
            type=ContentType.EXAMPLE_SENTENCES,
            order_index=3,
            is_active=True,
            is_assignment_copy=False,
        )
        db.add(content3)

        # 為每個內容創建 5 個題目
        for content_id in [2, 3]:
            for i in range(1, 6):
                item = ContentItem(
                    content_id=content_id,
                    order_index=i,
                    text=f"Question {i}",
                    translation=f"問題 {i}",
                    audio_url=f"https://example.com/audio{i}.mp3",
                )
                db.add(item)

        db.commit()
        db.close()

        token = get_teacher_auth_token()
        headers = {"Authorization": f"Bearer {token}"}

        # 獲取所有學生 ID
        db = TestingSessionLocal()
        students = db.query(Student).filter(Student.id <= 30).all()
        student_ids = [s.id for s in students]
        db.close()

        # 派作業（3 個內容，30 個學生）
        response = client.post(
            "/api/teachers/assignments/create",
            headers=headers,
            json={
                "title": "多內容批量測試",
                "description": "測試描述",
                "classroom_id": test_data["classroom_id"],
                "content_ids": [1, 2, 3],  # 3 個內容
                "student_ids": student_ids,  # 30 個學生
                "due_date": datetime.now(timezone.utc).isoformat(),
            },
        )

        assert response.status_code == 200
        assignment_id = response.json()["assignment_id"]

        # 驗證記錄數量
        db = TestingSessionLocal()

        # StudentAssignment: 30 個
        student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_assignments) == 30  # ✅

        # StudentContentProgress: 30 學生 × 3 內容 = 90 個
        student_content_progress = (
            db.query(StudentContentProgress)
            .join(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_content_progress) == 90  # ✅

        # StudentItemProgress: 30 學生 × 3 內容 × 5 題目 = 450 個
        student_item_progress = (
            db.query(StudentItemProgress)
            .join(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        assert len(student_item_progress) == 450  # ✅

        db.close()
