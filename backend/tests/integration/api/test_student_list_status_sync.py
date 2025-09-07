"""
測試學生列表狀態同步更新
測試批改狀態改變時，學生列表的狀態是否同步更新
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone, date  # noqa: F401

from main import app
from models import (
    Teacher,
    Student,
    Classroom,
    Assignment,
    StudentAssignment,
    AssignmentStatus,
    ClassroomStudent,
)
from auth import create_access_token

client = TestClient(app)


@pytest.fixture
def teacher_token(db: Session):
    """創建測試教師並返回 JWT token"""
    teacher = Teacher(
        email="test_teacher@example.com",
        name="Test Teacher",
        password_hash="hashed_password",
    )
    db.add(teacher)
    db.commit()

    token = create_access_token(data={"sub": teacher.email, "user_type": "teacher"})
    return token


@pytest.fixture
def test_classroom_setup(db: Session):
    """設置測試用的班級和學生"""
    # 創建教師
    teacher = Teacher(
        email="test_teacher@example.com",
        name="Test Teacher",
        password_hash="hashed_password",
    )
    db.add(teacher)

    # 創建班級
    classroom = Classroom(name="Test Class", teacher_id=1)
    db.add(classroom)

    # 創建多個學生
    students = []
    for i in range(5):
        student = Student(
            email=f"student{i + 1}@example.com",
            name=f"學生{i + 1}",
            password_hash="hashed_password",
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        students.append(student)

    db.flush()

    # 將學生加入班級
    for i, student in enumerate(students):
        classroom_student = ClassroomStudent(classroom_id=1, student_id=i + 1)
        db.add(classroom_student)

    # 創建作業
    assignment = Assignment(
        title="Test Assignment",
        classroom_id=1,
        teacher_id=1,
        due_date=datetime.now(timezone.utc),
    )
    db.add(assignment)

    # 為每個學生創建作業提交
    statuses = [
        AssignmentStatus.SUBMITTED,  # 學生1 - 已提交
        AssignmentStatus.GRADED,  # 學生2 - 已批改
        AssignmentStatus.SUBMITTED,  # 學生3 - 已提交
        AssignmentStatus.RETURNED,  # 學生4 - 退回訂正
        AssignmentStatus.NOT_STARTED,  # 學生5 - 未開始
    ]

    for i, (student, status) in enumerate(zip(students, statuses)):
        student_assignment = StudentAssignment(
            assignment_id=1,
            student_id=i + 1,
            classroom_id=1,
            title="Test Assignment",
            status=status,
        )
        db.add(student_assignment)

    db.commit()

    return {
        "teacher": teacher,
        "students": students,
        "classroom": classroom,
        "assignment": assignment,
    }


class TestStudentListStatusSync:
    """測試學生列表狀態同步"""

    def test_get_student_list_with_status(self, test_classroom_setup, teacher_token):
        """測試獲取學生列表及其狀態"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert "students" in data
        assert len(data["students"]) == 5

        # 驗證每個學生的狀態
        students = data["students"]
        assert students[0]["status"] == "SUBMITTED"
        assert students[1]["status"] == "GRADED"
        assert students[2]["status"] == "SUBMITTED"
        assert students[3]["status"] == "RETURNED"
        assert students[4]["status"] == "NOT_STARTED"

    def test_status_update_to_graded(self, test_classroom_setup, teacher_token):
        """測試更新狀態為已完成"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 將學生1的狀態從 SUBMITTED 改為 GRADED
        response = client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 85,
                "feedback": "表現良好！",
                "item_results": [],
                "update_status": True,  # 更新狀態為 GRADED
            },
        )

        assert response.status_code == 200

        # 再次獲取學生列表，確認狀態已更新
        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        assert response.status_code == 200
        students = response.json()["students"]

        # 學生1的狀態應該變成 GRADED
        student1 = next(s for s in students if s["student_id"] == 1)
        assert student1["status"] == "GRADED"

    def test_status_update_to_submitted(self, test_classroom_setup, teacher_token):
        """測試更新狀態為批改中（SUBMITTED）"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 將學生2的狀態從 GRADED 改回 SUBMITTED
        response = client.post(
            "/api/teachers/assignments/1/set-in-progress",
            headers=headers,
            json={"student_id": 2},
        )

        assert response.status_code == 200

        # 再次獲取學生列表，確認狀態已更新
        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        assert response.status_code == 200
        students = response.json()["students"]

        # 學生2的狀態應該變成 SUBMITTED
        student2 = next(s for s in students if s["student_id"] == 2)
        assert student2["status"] == "SUBMITTED"

    def test_status_update_to_returned(self, test_classroom_setup, teacher_token):
        """測試更新狀態為退回訂正（RETURNED）"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 將學生3的狀態從 SUBMITTED 改為 RETURNED
        response = client.post(
            "/api/teachers/assignments/1/return-for-revision",
            headers=headers,
            json={"student_id": 3, "message": "請依照評語修改後重新提交"},
        )

        assert response.status_code == 200

        # 再次獲取學生列表，確認狀態已更新
        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        assert response.status_code == 200
        students = response.json()["students"]

        # 學生3的狀態應該變成 RETURNED
        student3 = next(s for s in students if s["student_id"] == 3)
        assert student3["status"] == "RETURNED"

    def test_multiple_status_changes(self, test_classroom_setup, teacher_token):
        """測試連續多次狀態改變"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 學生1: SUBMITTED -> GRADED -> RETURNED -> SUBMITTED

        # 1. SUBMITTED -> GRADED
        client.post(
            "/api/teachers/assignments/1/grade",
            headers=headers,
            json={
                "student_id": 1,
                "score": 90,
                "feedback": "Good",
                "update_status": True,
            },
        )

        # 2. GRADED -> RETURNED
        client.post(
            "/api/teachers/assignments/1/return-for-revision",
            headers=headers,
            json={"student_id": 1},
        )

        # 3. RETURNED -> SUBMITTED
        client.post(
            "/api/teachers/assignments/1/set-in-progress",
            headers=headers,
            json={"student_id": 1},
        )

        # 驗證最終狀態
        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        students = response.json()["students"]
        student1 = next(s for s in students if s["student_id"] == 1)
        assert student1["status"] == "SUBMITTED"

    def test_batch_operations_affect_list(self, test_classroom_setup, teacher_token):
        """測試批次操作對列表的影響"""
        headers = {"Authorization": f"Bearer {teacher_token}"}

        # 批次批改多個學生
        students_to_grade = [1, 3, 5]

        for student_id in students_to_grade:
            client.post(
                "/api/teachers/assignments/1/grade",
                headers=headers,
                json={
                    "student_id": student_id,
                    "score": 85,
                    "feedback": f"學生{student_id}的評語",
                    "update_status": True,
                },
            )

        # 獲取更新後的列表
        response = client.get("/api/teachers/assignments/1/students", headers=headers)

        students = response.json()["students"]

        # 驗證批改的學生狀態都變成 GRADED
        for student_id in students_to_grade:
            student = next(s for s in students if s["student_id"] == student_id)
            assert student["status"] == "GRADED"

        # 驗證沒有批改的學生狀態保持不變
        student2 = next(s for s in students if s["student_id"] == 2)
        assert student2["status"] == "GRADED"  # 原本就是 GRADED

        student4 = next(s for s in students if s["student_id"] == 4)
        assert student4["status"] == "RETURNED"  # 原本是 RETURNED
