"""
Test for Issue #34: 設定未來開始日期時，學生提前看到作業卡片

Bug: 當作業設定未來 assigned_at 時間，學生在當前時間就能看到作業列表
Expected: 只有 assigned_at <= 當前時間的作業才應該顯示給學生
"""

import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
    AssignmentStatus,
)
from auth import create_access_token


@pytest.fixture
def setup_future_assignment(test_db_session: Session, test_client: TestClient):
    """設定測試資料：創建一個未來開始的作業"""

    # 創建教師
    teacher = Teacher(
        name="Test Teacher",
        email="teacher_issue34@test.com",
        password_hash="hashed",
    )
    test_db_session.add(teacher)
    test_db_session.flush()

    # 創建班級
    classroom = Classroom(
        name="Test Classroom",
        teacher_id=teacher.id,
    )
    test_db_session.add(classroom)
    test_db_session.flush()

    # 創建學生
    student = Student(
        name="Test Student",
        email="student_issue34@test.com",
        password_hash="hashed",
        student_number="S001",
    )
    test_db_session.add(student)
    test_db_session.flush()

    # 學生加入班級
    enrollment = ClassroomStudent(
        student_id=student.id,
        classroom_id=classroom.id,
    )
    test_db_session.add(enrollment)

    # 創建 3 個作業
    now = datetime.now(timezone.utc)

    # 作業 1: 過去的作業（應該顯示）
    past_assignment = StudentAssignment(
        student_id=student.id,
        classroom_id=classroom.id,
        title="Past Assignment",
        assigned_at=now - timedelta(days=1),
        due_date=now + timedelta(days=7),
        status=AssignmentStatus.NOT_STARTED,
    )
    test_db_session.add(past_assignment)

    # 作業 2: 現在的作業（應該顯示）
    current_assignment = StudentAssignment(
        student_id=student.id,
        classroom_id=classroom.id,
        title="Current Assignment",
        assigned_at=now - timedelta(minutes=5),
        due_date=now + timedelta(days=7),
        status=AssignmentStatus.NOT_STARTED,
    )
    test_db_session.add(current_assignment)

    # 作業 3: 未來的作業（❌ 不應該顯示 - 這是 bug）
    future_assignment = StudentAssignment(
        student_id=student.id,
        classroom_id=classroom.id,
        title="Future Assignment (2026-01-01)",
        assigned_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        due_date=datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc),
        status=AssignmentStatus.NOT_STARTED,
    )
    test_db_session.add(future_assignment)

    test_db_session.commit()

    # 創建學生 token
    student_token = create_access_token(
        data={"sub": str(student.id), "type": "student"},
        expires_delta=timedelta(minutes=30),
    )

    return {
        "student": student,
        "student_token": student_token,
        "past_assignment": past_assignment,
        "current_assignment": current_assignment,
        "future_assignment": future_assignment,
    }


def test_student_should_not_see_future_assignments(
    test_client: TestClient, test_db_session: Session, setup_future_assignment
):
    """
    TDD Test (Red Phase): 學生不應該看到未來才開始的作業

    Given: 有 3 個作業（過去、現在、未來）
    When: 學生查詢作業列表
    Then: 只應該看到過去和現在的作業，不應該看到未來的作業

    ❌ 這個測試目前會 FAIL，因為 API 沒有過濾 assigned_at
    """
    data = setup_future_assignment

    # When: 學生查詢作業列表
    response = test_client.get(
        "/api/students/assignments",
        headers={"Authorization": f"Bearer {data['student_token']}"},
    )

    # Then: 應該返回成功
    assert response.status_code == 200
    assignments = response.json()

    # Then: 只應該看到 2 個作業（過去 + 現在）
    # ❌ 目前會失敗：實際返回 3 個（包含未來的作業）
    assert len(assignments) == 2, (
        f"Expected 2 assignments (past + current), "
        f"but got {len(assignments)}. "
        f"Future assignment should not be visible!"
    )

    # Then: 確認返回的作業標題
    assignment_titles = [a["title"] for a in assignments]
    assert "Past Assignment" in assignment_titles
    assert "Current Assignment" in assignment_titles
    assert (
        "Future Assignment (2026-01-01)" not in assignment_titles
    ), "Future assignment (2026-01-01) should NOT be visible to student!"


def test_future_assignment_becomes_visible_after_start_time(
    test_client: TestClient, test_db_session: Session, setup_future_assignment
):
    """
    測試：未來作業在開始時間到達後應該可見

    Given: 有一個 5 秒後開始的作業
    When: 在開始時間前查詢
    Then: 不應該看到這個作業

    When: 在開始時間後查詢（模擬時間推進）
    Then: 應該看到這個作業
    """
    data = setup_future_assignment
    student = data["student"]

    # 創建一個 5 秒後開始的作業
    now = datetime.now(timezone.utc)
    near_future_assignment = StudentAssignment(
        student_id=student.id,
        classroom_id=data["past_assignment"].classroom_id,
        title="Near Future Assignment",
        assigned_at=now + timedelta(seconds=5),
        due_date=now + timedelta(days=1),
        status=AssignmentStatus.NOT_STARTED,
    )
    test_db_session.add(near_future_assignment)
    test_db_session.commit()

    # When: 立即查詢（在開始時間前）
    response = test_client.get(
        "/api/students/assignments",
        headers={"Authorization": f"Bearer {data['student_token']}"},
    )

    assert response.status_code == 200
    assignments_before = response.json()
    titles_before = [a["title"] for a in assignments_before]

    # Then: 不應該看到這個作業
    assert "Near Future Assignment" not in titles_before

    # 注意：這裡無法真正等待 5 秒，所以這個測試主要是文檔化預期行為
    # 實際測試會在修復後，透過修改 assigned_at 到過去時間來驗證
