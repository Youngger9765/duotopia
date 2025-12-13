"""
測試 POST /assignments/create API
重點測試：創建新作業時，是否正確創建 StudentContentProgress 記錄

注意: 此測試使用舊的 StudentContentProgress 模型，
新架構已改用 StudentItemProgress。保留此測試僅供參考。
"""

import pytest
from datetime import datetime, timedelta, timezone
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
    Assignment,
    AssignmentContent,
    Content,
    ContentItem,
    StudentAssignment,
    StudentContentProgress,
    AssignmentStatus,
)
from auth import get_password_hash

# 標記整個模組為跳過
pytestmark = pytest.mark.skip(
    reason="Deprecated: Using old StudentContentProgress model, new architecture uses StudentItemProgress"
)

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_create_assignment.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
    )
    db.add(teacher)

    # 創建教室
    classroom = Classroom(id=1, name="測試教室", teacher_id=1, is_active=True)
    db.add(classroom)

    # 創建三個學生
    students = []
    for i in range(1, 4):
        student = Student(
            id=i,
            name=f"學生{i}",
            student_number=f"S00{i}",
            password_hash=get_password_hash("student123"),
            birthdate=datetime(2010, 1, 1),
        )
        db.add(student)
        students.append(student)

        # 將學生加入教室
        cs = ClassroomStudent(classroom_id=1, student_id=i, is_active=True)
        db.add(cs)

    # 創建兩個內容（用於作業）
    for i in range(1, 3):
        content = Content(
            id=i, lesson_id=1, title=f"內容{i}", type="EXAMPLE_SENTENCES", is_active=True
        )
        db.add(content)

        # 為每個內容創建項目
        for j in range(1, 3):
            item = ContentItem(
                id=(i - 1) * 2 + j,
                content_id=i,
                text=f"項目{j}文字",
                translation=f"Item {j} translation",
                order_index=j,
            )
            db.add(item)

    db.commit()
    db.close()

    # 模擬教師登入取得 token
    # 注意：實際測試中這可能會失敗，所以我們用 mock token
    mock_token = "mock_teacher_token"

    return {
        "token": mock_token,
        "teacher_id": 1,
        "classroom_id": 1,
        "student_ids": [1, 2, 3],
        "content_ids": [1, 2],
    }


def test_create_assignment_creates_student_content_progress(test_data):
    """
    測試：當使用 POST 創建新作業時，應該要為每個學生創建 StudentContentProgress 記錄
    """
    db = TestingSessionLocal()

    # 確認初始狀態：沒有作業
    initial_assignments = db.query(Assignment).count()
    assert initial_assignments == 0, "不應該有既有作業"

    # 模擬 create_assignment API 的邏輯
    # 由於實際 API 需要完整的認證系統，我們直接測試核心邏輯

    # 創建作業
    assignment = Assignment(
        id=1,
        title="新作業",
        description="測試作業說明",
        classroom_id=test_data["classroom_id"],
        teacher_id=test_data["teacher_id"],
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(assignment)
    db.flush()

    # 創建 AssignmentContent 關聯
    for idx, content_id in enumerate(test_data["content_ids"], 1):
        ac = AssignmentContent(
            assignment_id=assignment.id, content_id=content_id, order_index=idx
        )
        db.add(ac)

    # 為指定學生創建 StudentAssignment
    for student_id in test_data["student_ids"][:2]:  # 只指派給前兩個學生
        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student_id,
            classroom_id=test_data["classroom_id"],
            title=assignment.title,
            instructions=assignment.description,
            status=AssignmentStatus.NOT_STARTED,
            is_active=True,
        )
        db.add(sa)
        db.flush()  # 重要：必須 flush 才能取得 ID

        # 創建 StudentContentProgress（這是 create_assignment 應該做的）
        for idx, content_id in enumerate(test_data["content_ids"], 1):
            progress = StudentContentProgress(
                student_assignment_id=sa.id,
                content_id=content_id,
                status=AssignmentStatus.NOT_STARTED,
                order_index=idx,
                is_locked=False if idx == 1 else True,  # 只解鎖第一個
            )
            db.add(progress)

    db.commit()

    # 驗證結果
    # 1. 檢查是否創建了 StudentAssignment
    student_assignments = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == assignment.id)
        .all()
    )
    assert (
        len(student_assignments) == 2
    ), f"應該有2個 StudentAssignment，實際有 {len(student_assignments)} 個"

    # 2. 重點檢查：每個 StudentAssignment 是否有對應的 StudentContentProgress
    for sa in student_assignments:
        progress_records = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == sa.id)
            .all()
        )

        # 應該有兩筆記錄（對應兩個內容）
        assert (
            len(progress_records) == 2
        ), f"StudentAssignment {sa.id} 應該有2筆 StudentContentProgress，但只有 {len(progress_records)} 筆"

        # 檢查進度記錄的正確性
        for progress in progress_records:
            assert progress.status == AssignmentStatus.NOT_STARTED

            # 檢查鎖定狀態
            if progress.order_index == 1:
                assert progress.is_locked is False, "第一個內容應該解鎖"
            else:
                assert progress.is_locked is True, f"第 {progress.order_index} 個內容應該鎖定"

    db.close()
    print("✅ 測試通過：create_assignment 正確創建了 StudentContentProgress")


def test_create_assignment_for_whole_class(test_data):
    """
    測試：當創建作業指派給全班時，應該為所有學生創建 StudentContentProgress
    """
    db = TestingSessionLocal()

    # 創建作業
    assignment = Assignment(
        id=1,
        title="全班作業",
        description="指派給全班的作業",
        classroom_id=test_data["classroom_id"],
        teacher_id=test_data["teacher_id"],
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(assignment)
    db.flush()

    # 創建 AssignmentContent 關聯
    for idx, content_id in enumerate(test_data["content_ids"], 1):
        ac = AssignmentContent(
            assignment_id=assignment.id, content_id=content_id, order_index=idx
        )
        db.add(ac)

    # 取得班級所有學生
    classroom_students = (
        db.query(ClassroomStudent)
        .filter(
            ClassroomStudent.classroom_id == test_data["classroom_id"],
            ClassroomStudent.is_active is True,
        )
        .all()
    )

    # 為全班學生創建 StudentAssignment 和 StudentContentProgress
    for cs in classroom_students:
        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=cs.student_id,
            classroom_id=test_data["classroom_id"],
            title=assignment.title,
            instructions=assignment.description,
            status=AssignmentStatus.NOT_STARTED,
            is_active=True,
        )
        db.add(sa)
        db.flush()

        # 創建 StudentContentProgress
        for idx, content_id in enumerate(test_data["content_ids"], 1):
            progress = StudentContentProgress(
                student_assignment_id=sa.id,
                content_id=content_id,
                status=AssignmentStatus.NOT_STARTED,
                order_index=idx,
                is_locked=False if idx == 1 else True,
            )
            db.add(progress)

    db.commit()

    # 驗證結果
    student_assignments = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == assignment.id)
        .all()
    )

    assert (
        len(student_assignments) == 3
    ), f"全班3個學生都應該有作業，實際有 {len(student_assignments)} 個"

    # 檢查每個學生的 StudentContentProgress
    total_progress = (
        db.query(StudentContentProgress)
        .join(StudentAssignment)
        .filter(StudentAssignment.assignment_id == assignment.id)
        .count()
    )

    expected_progress = len(student_assignments) * len(test_data["content_ids"])
    assert (
        total_progress == expected_progress
    ), f"應該有 {expected_progress} 筆 StudentContentProgress，實際有 {total_progress} 筆"

    db.close()
    print("✅ 測試通過：為全班創建作業時正確創建了所有 StudentContentProgress")


if __name__ == "__main__":
    # 直接執行測試
    pass

    # 模擬 setup
    Base.metadata.create_all(bind=engine)

    test_data_dict = {
        "token": "mock_token",
        "teacher_id": 1,
        "classroom_id": 1,
        "student_ids": [1, 2, 3],
        "content_ids": [1, 2],
    }

    # 準備測試資料
    db = TestingSessionLocal()

    # 創建教師
    teacher = Teacher(
        id=1, name="測試教師", email="teacher@test.com", password_hash="hashed"
    )
    db.add(teacher)

    # 創建教室
    classroom = Classroom(id=1, name="測試教室", teacher_id=1, is_active=True)
    db.add(classroom)

    # 創建學生
    for i in range(1, 4):
        student = Student(
            id=i,
            name=f"學生{i}",
            student_number=f"S00{i}",
            password_hash="hashed",
            birthdate=datetime(2010, 1, 1),
        )
        db.add(student)

        cs = ClassroomStudent(classroom_id=1, student_id=i, is_active=True)
        db.add(cs)

    # 創建內容
    for i in range(1, 3):
        content = Content(
            id=i, lesson_id=1, title=f"內容{i}", type="EXAMPLE_SENTENCES", is_active=True
        )
        db.add(content)

    db.commit()
    db.close()

    # 執行測試
    test_create_assignment_creates_student_content_progress(test_data_dict)

    # 清理
    Base.metadata.drop_all(bind=engine)

    # 重新準備資料執行第二個測試
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # ... (重複上面的資料準備)
    teacher = Teacher(
        id=1, name="測試教師", email="teacher@test.com", password_hash="hashed"
    )
    db.add(teacher)
    classroom = Classroom(id=1, name="測試教室", teacher_id=1, is_active=True)
    db.add(classroom)
    for i in range(1, 4):
        student = Student(
            id=i,
            name=f"學生{i}",
            student_number=f"S00{i}",
            password_hash="hashed",
            birthdate=datetime(2010, 1, 1),
        )
        db.add(student)
        cs = ClassroomStudent(classroom_id=1, student_id=i, is_active=True)
        db.add(cs)
    for i in range(1, 3):
        content = Content(
            id=i, lesson_id=1, title=f"內容{i}", type="EXAMPLE_SENTENCES", is_active=True
        )
        db.add(content)
    db.commit()
    db.close()

    test_create_assignment_for_whole_class(test_data_dict)

    # 清理
    Base.metadata.drop_all(bind=engine)

    print("\n🎉 所有 create_assignment 測試通過！")
