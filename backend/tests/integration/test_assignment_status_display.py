"""
整合測試：作業指派狀態顯示
測試目的：防止 is_assigned 被硬編碼或錯誤處理

這個測試是因為 2025-09-13 的 bug：
前端硬編碼 is_assigned: true，導致所有學生都顯示為已指派
"""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Assignment,
    StudentAssignment,
)
from auth import create_access_token


@pytest.fixture
def test_data(db: Session):
    """建立測試資料"""
    # 建立老師
    teacher = Teacher(
        email="test_teacher@example.com", name="測試老師", password_hash="hashed_password"
    )
    db.add(teacher)

    # 建立班級
    classroom = Classroom(name="測試班級", teacher_id=1)
    db.add(classroom)

    # 建立學生
    students = []
    for i in range(5):
        student = Student(
            student_number=f"S00{i+1}",
            name=f"學生{i+1}",
            email=f"student{i+1}@example.com",
            password_hash="hashed_password",
            birthdate=datetime(2010, 1, 1).date(),  # 必填欄位
        )
        students.append(student)
        db.add(student)

    db.flush()

    # 將學生加入班級
    for i, student in enumerate(students):
        cs = ClassroomStudent(
            classroom_id=classroom.id, student_id=student.id, is_active=True
        )
        db.add(cs)

    # 建立作業
    assignment = Assignment(
        title="測試作業",
        classroom_id=classroom.id,
        teacher_id=teacher.id,  # 修正：使用 teacher_id 而不是 created_by
    )
    db.add(assignment)
    db.flush()

    # 只指派給前2個學生
    from models import AssignmentStatus  # 導入 enum

    for i in range(2):
        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=students[i].id,
            classroom_id=classroom.id,  # 必須提供
            title=assignment.title,  # 必須提供
            status=AssignmentStatus.NOT_STARTED,  # 使用 enum 而不是字串
        )
        db.add(sa)

    db.commit()

    return {
        "teacher": teacher,
        "classroom": classroom,
        "students": students,
        "assignment": assignment,
    }


def test_assignment_progress_shows_correct_is_assigned_status(test_data, db: Session):
    """
    測試：作業進度 API 正確返回 is_assigned 狀態
    預期：只有被指派的學生 is_assigned 為 true
    """
    client = TestClient(app)

    # 建立老師 token
    token = create_access_token(
        data={
            "sub": test_data["teacher"].email,
            "user_type": "teacher",
            "user_id": test_data["teacher"].id,
        }
    )

    # 呼叫作業進度 API
    response = client.get(
        f"/api/teachers/assignments/{test_data['assignment'].id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    progress_data = response.json()

    # 驗證返回資料
    assert len(progress_data) == 5  # 班級有5個學生

    # 建立學生ID對照表
    assigned_student_ids = {test_data["students"][0].id, test_data["students"][1].id}

    # 檢查每個學生的 is_assigned 狀態
    for student_progress in progress_data:
        student_id = student_progress["student_id"]
        is_assigned = student_progress["is_assigned"]

        if student_id in assigned_student_ids:
            # 被指派的學生
            assert (
                is_assigned is True
            ), f"學生 {student_id} 應該被指派但 is_assigned={is_assigned}"
        else:
            # 未被指派的學生
            assert (
                is_assigned is False
            ), f"學生 {student_id} 不應該被指派但 is_assigned={is_assigned}"


def test_assignment_detail_shows_correct_student_list(test_data, db: Session):
    """
    測試：作業詳情 API 正確返回學生列表
    預期：students 欄位只包含被指派的學生
    """
    from database import get_db

    # Override database dependency
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # 建立老師 token
    token = create_access_token(
        data={
            "sub": test_data["teacher"].email,
            "user_type": "teacher",
            "user_id": test_data["teacher"].id,
        }
    )

    # 呼叫作業詳情 API
    response = client.get(
        f"/api/assignments/{test_data['assignment'].id}",  # 修正：正確的端點路徑
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assignment_data = response.json()

    # 檢查 students 欄位
    assert "students" in assignment_data
    assert len(assignment_data["students"]) == 2  # 只有2個學生被指派

    # 檢查是否為正確的學生
    assigned_student_numbers = {"S001", "S002"}
    for student in assignment_data["students"]:
        assert student["student_number"] in assigned_student_numbers


def test_partial_assignment_statistics(test_data, db: Session):
    """
    測試：部分指派的統計資料正確性
    預期：正確顯示指派人數和完成率
    """
    client = TestClient(app)

    # 建立老師 token
    token = create_access_token(
        data={
            "sub": test_data["teacher"].email,
            "user_type": "teacher",
            "user_id": test_data["teacher"].id,
        }
    )

    # 呼叫作業進度 API
    response = client.get(
        f"/api/teachers/assignments/{test_data['assignment'].id}/progress",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    progress_data = response.json()

    # 統計指派狀態
    assigned_count = sum(1 for p in progress_data if p["is_assigned"] is True)
    unassigned_count = sum(1 for p in progress_data if p["is_assigned"] is False)

    assert assigned_count == 2, f"應該有2個學生被指派，但實際是 {assigned_count}"
    assert unassigned_count == 3, f"應該有3個學生未被指派，但實際是 {unassigned_count}"


def test_frontend_should_respect_api_response():
    """
    提醒：前端必須使用 API 返回的 is_assigned 值
    不可硬編碼或覆蓋

    這個測試是文件化的提醒，實際前端測試應該在前端測試檔案中
    """
    frontend_best_practices = """
    1. 永遠使用 API 返回的值：
       ✅ is_assigned: response.is_assigned
       ❌ is_assigned: true

    2. 不要假設資料結構：
       ✅ is_assigned: item.is_assigned ?? false
       ❌ is_assigned: true

    3. 加入資料驗證：
       if (typeof item.is_assigned !== 'boolean') {
           console.error('Invalid is_assigned value');
       }
    """
    assert frontend_best_practices != ""  # 這只是文件化用途


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
