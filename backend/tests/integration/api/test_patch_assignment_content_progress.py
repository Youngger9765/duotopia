"""
測試 PATCH /assignments/{assignment_id} API
重點測試：當新增學生到既有作業時，是否正確創建 StudentContentProgress 記錄
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

# 測試資料庫設置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patch_assignment.db"
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
            birthdate=datetime(2010, 1, 1),  # 添加必需的 birthdate
        )
        db.add(student)
        students.append(student)

        # 將學生加入教室
        cs = ClassroomStudent(classroom_id=1, student_id=i, is_active=True)
        db.add(cs)

    # 創建兩個內容
    contents = []
    for i in range(1, 3):
        content = Content(
            id=i,
            lesson_id=1,  # 添加必需的 lesson_id
            title=f"內容{i}",
            type="READING_ASSESSMENT",
            is_active=True,
        )
        db.add(content)
        contents.append(content)

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

    # 創建作業（初始只指派給前兩個學生）
    assignment = Assignment(
        id=1,
        title="測試作業",
        description="測試作業說明",
        classroom_id=1,
        teacher_id=1,
        due_date=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(assignment)

    # 關聯作業與內容
    for idx, content in enumerate(contents, 1):
        ac = AssignmentContent(assignment_id=1, content_id=content.id, order_index=idx)
        db.add(ac)

    # 為前兩個學生創建 StudentAssignment 和 StudentContentProgress
    for student_id in [1, 2]:
        sa = StudentAssignment(
            assignment_id=1,
            student_id=student_id,
            classroom_id=1,
            title="測試作業",
            instructions="測試作業說明",
            status=AssignmentStatus.NOT_STARTED,
            is_active=True,
        )
        db.add(sa)
        db.flush()  # 取得 ID

        # 為每個內容創建進度記錄
        for idx, content in enumerate(contents, 1):
            progress = StudentContentProgress(
                student_assignment_id=sa.id,
                content_id=content.id,
                status=AssignmentStatus.NOT_STARTED,
                order_index=idx,
                is_locked=False if idx == 1 else True,
            )
            db.add(progress)

    db.commit()
    db.close()

    # 登入取得 token
    response = client.post(
        "/api/auth/login", json={"email": "teacher@test.com", "password": "password123"}
    )
    token = response.json()["access_token"]

    return {
        "token": token,
        "assignment_id": 1,
        "existing_students": [1, 2],
        "new_student": 3,
        "content_ids": [1, 2],
    }


def test_patch_assignment_adds_student_content_progress(test_data):
    """
    測試：當使用 PATCH 新增學生到既有作業時，應該要創建對應的 StudentContentProgress 記錄
    """
    db = TestingSessionLocal()

    # 確認初始狀態：學生3還沒有被指派作業
    initial_sa = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.student_id == test_data["new_student"])
        .first()
    )
    assert initial_sa is None, "學生3不應該有作業"

    # 使用 PATCH API 更新作業，加入學生3
    response = client.patch(
        f"/api/teachers/assignments/{test_data['assignment_id']}",
        headers={"Authorization": f"Bearer {test_data['token']}"},
        json={"student_ids": [1, 2, 3]},  # 加入學生3
    )

    assert response.status_code == 200

    # 檢查學生3是否有 StudentAssignment
    new_sa = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == test_data["new_student"],
            StudentAssignment.assignment_id == test_data["assignment_id"],
        )
        .first()
    )

    assert new_sa is not None, "學生3應該要有 StudentAssignment"
    assert new_sa.title == "測試作業"

    # 重點測試：檢查是否有創建 StudentContentProgress
    progress_records = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id == new_sa.id)
        .all()
    )

    # 應該要有兩筆記錄（對應兩個內容）
    assert (
        len(progress_records) == 2
    ), f"應該要有2筆 StudentContentProgress，但只有 {len(progress_records)} 筆"

    # 檢查每筆進度記錄的正確性
    progress_by_content = {p.content_id: p for p in progress_records}

    for content_id in test_data["content_ids"]:
        assert content_id in progress_by_content, f"缺少 content_id={content_id} 的進度記錄"

        progress = progress_by_content[content_id]
        assert progress.status == AssignmentStatus.NOT_STARTED

        # 第一個內容應該解鎖，其他應該鎖定
        expected_locked = False if progress.order_index == 1 else True
        assert (
            progress.is_locked == expected_locked
        ), f"content_id={content_id} 的 is_locked 應該是 {expected_locked}"

    # 確保原本的學生還是有作業
    existing_assignments = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == test_data["assignment_id"],
            StudentAssignment.student_id.in_(test_data["existing_students"]),
        )
        .all()
    )

    assert len(existing_assignments) == 2, "原本的學生應該還是有作業"

    db.close()


def test_patch_assignment_does_not_duplicate_existing_students(test_data):
    """
    測試：當學生已經有作業時，不應該重複創建
    """
    db = TestingSessionLocal()

    # 取得初始的 StudentAssignment 數量
    initial_count = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == test_data["assignment_id"])
        .count()
    )

    # 使用相同的學生列表更新
    response = client.patch(
        f"/api/teachers/assignments/{test_data['assignment_id']}",
        headers={"Authorization": f"Bearer {test_data['token']}"},
        json={"student_ids": [1, 2]},  # 相同的學生
    )

    assert response.status_code == 200

    # 檢查 StudentAssignment 數量沒有改變
    final_count = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == test_data["assignment_id"])
        .count()
    )

    assert final_count == initial_count, "不應該創建重複的 StudentAssignment"

    db.close()


def test_patch_assignment_removes_unassigned_students(test_data):
    """
    測試：當移除學生時，應該刪除相關的 StudentAssignment 和 StudentContentProgress
    """
    db = TestingSessionLocal()

    # 只保留學生1
    response = client.patch(
        f"/api/teachers/assignments/{test_data['assignment_id']}",
        headers={"Authorization": f"Bearer {test_data['token']}"},
        json={"student_ids": [1]},  # 只保留學生1
    )

    assert response.status_code == 200

    # 檢查學生2的作業應該被刪除
    removed_sa = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == 2,
            StudentAssignment.assignment_id == test_data["assignment_id"],
        )
        .first()
    )

    assert removed_sa is None, "學生2的作業應該被刪除"

    # 檢查學生1的作業還在
    kept_sa = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.student_id == 1,
            StudentAssignment.assignment_id == test_data["assignment_id"],
        )
        .first()
    )

    assert kept_sa is not None, "學生1的作業應該保留"

    db.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
