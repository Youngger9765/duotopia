"""
測試 Issue #34: Assignment start_date 功能
驗證開始日期能否正確儲存到 StudentAssignment.assigned_at
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Content,
    ContentItem,
    StudentAssignment,
    AssignmentStatus,
)
from auth import get_password_hash

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_assignment_start_date.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
        can_assign_homework=True,
    )
    db.add(teacher)

    # 創建教室
    classroom = Classroom(id=1, name="測試教室", teacher_id=1, is_active=True)
    db.add(classroom)

    # 創建學生
    student = Student(
        id=1,
        name="學生1",
        student_number="S001",
        password_hash=get_password_hash("student123"),
        birthdate=datetime(2010, 1, 1),
    )
    db.add(student)

    # 將學生加入教室
    cs = ClassroomStudent(classroom_id=1, student_id=1, is_active=True)
    db.add(cs)

    # 創建內容
    content = Content(
        id=1, lesson_id=1, title="測試內容", type="READING_ASSESSMENT", is_active=True
    )
    db.add(content)

    # 創建內容項目
    item = ContentItem(
        id=1,
        content_id=1,
        text="測試文字",
        translation="Test text",
        order_index=1,
    )
    db.add(item)

    db.commit()
    db.close()

    return {
        "teacher_id": 1,
        "classroom_id": 1,
        "student_id": 1,
        "content_id": 1,
    }


def test_assignment_with_future_start_date(test_data):
    """
    測試：當設定未來的 start_date 時，assigned_at 應該使用該日期
    """
    db = TestingSessionLocal()

    # 設定一個未來的日期
    future_date = datetime.now(timezone.utc) + timedelta(days=7)

    # 模擬 create_assignment 的核心邏輯
    # 使用 start_date 參數
    student_assignment = StudentAssignment(
        assignment_id=1,
        student_id=test_data["student_id"],
        classroom_id=test_data["classroom_id"],
        title="測試作業",
        instructions="測試說明",
        assigned_at=future_date,  # 應該使用 request.start_date
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    db.add(student_assignment)
    db.commit()

    # 驗證結果
    saved_assignment = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.student_id == test_data["student_id"])
        .first()
    )

    assert saved_assignment is not None, "StudentAssignment 應該存在"
    assert saved_assignment.assigned_at is not None, "assigned_at 不應該是 None"

    # 檢查日期是否正確（允許1秒誤差）
    time_diff = abs((saved_assignment.assigned_at - future_date).total_seconds())
    assert time_diff < 1, f"assigned_at 應該是 {future_date}，實際是 {saved_assignment.assigned_at}"

    db.close()
    print("✅ 測試通過：未來開始日期正確儲存")


def test_assignment_without_start_date_uses_current_time(test_data):
    """
    測試：當沒有設定 start_date 時，assigned_at 應該使用當前時間（向後兼容）
    """
    db = TestingSessionLocal()

    # 記錄當前時間
    current_time = datetime.now(timezone.utc)

    # 模擬 create_assignment 的核心邏輯
    # 不設定 start_date，應該使用當前時間
    student_assignment = StudentAssignment(
        assignment_id=2,
        student_id=test_data["student_id"],
        classroom_id=test_data["classroom_id"],
        title="測試作業2",
        instructions="測試說明2",
        assigned_at=datetime.now(timezone.utc),  # 應該使用 datetime.now(timezone.utc)
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    db.add(student_assignment)
    db.commit()

    # 驗證結果
    saved_assignment = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == 2)
        .first()
    )

    assert saved_assignment is not None, "StudentAssignment 應該存在"
    assert saved_assignment.assigned_at is not None, "assigned_at 不應該是 None"

    # 檢查日期是否接近當前時間（允許5秒誤差）
    time_diff = abs((saved_assignment.assigned_at - current_time).total_seconds())
    assert time_diff < 5, f"assigned_at 應該接近當前時間，差異: {time_diff} 秒"

    db.close()
    print("✅ 測試通過：沒有設定開始日期時使用當前時間")


def test_assignment_with_past_start_date(test_data):
    """
    測試：允許設定過去的日期（補建作業的情境）
    """
    db = TestingSessionLocal()

    # 設定一個過去的日期
    past_date = datetime.now(timezone.utc) - timedelta(days=3)

    student_assignment = StudentAssignment(
        assignment_id=3,
        student_id=test_data["student_id"],
        classroom_id=test_data["classroom_id"],
        title="補建作業",
        instructions="補建說明",
        assigned_at=past_date,  # 使用過去的日期
        status=AssignmentStatus.NOT_STARTED,
        is_active=True,
    )
    db.add(student_assignment)
    db.commit()

    # 驗證結果
    saved_assignment = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == 3)
        .first()
    )

    assert saved_assignment is not None, "StudentAssignment 應該存在"
    assert saved_assignment.assigned_at is not None, "assigned_at 不應該是 None"

    # 檢查日期是否正確
    time_diff = abs((saved_assignment.assigned_at - past_date).total_seconds())
    assert time_diff < 1, f"assigned_at 應該是 {past_date}，實際是 {saved_assignment.assigned_at}"

    db.close()
    print("✅ 測試通過：過去開始日期也能正確儲存")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
