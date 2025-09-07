#!/usr/bin/env python3
"""
測試未分配班級學生的可見性

測試案例：
1. 建立未分配班級的學生
2. 確認該學生出現在學生列表中（24小時內）
3. 確認警告訊息正確顯示
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from models import Teacher, Student, Classroom, ClassroomStudent
from auth import get_password_hash


@pytest.fixture
def test_teacher(db: Session):
    """建立測試教師"""
    teacher = Teacher(
        name="Test Teacher",
        email="test_unassigned@test.com",
        password_hash=get_password_hash("testpass123"),
        is_active=True,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(test_teacher: Teacher):
    """取得認證標頭"""
    client = TestClient(app)
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": test_teacher.email, "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestUnassignedStudentVisibility:
    """測試未分配班級學生的可見性"""

    def test_create_student_without_classroom_shows_warning(self, client: TestClient, auth_headers: dict, db: Session):
        """測試建立未分配班級的學生時會顯示警告"""
        # 建立學生（不指定班級）
        student_data = {
            "name": "未分配學生",
            "birthdate": "2012-01-01",
            "email": f"unassigned_{datetime.now().timestamp()}@test.com",
        }

        response = client.post("/api/teachers/students", json=student_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # 確認有警告訊息
        assert "warning" in data
        assert "24小時" in data["warning"]
        assert "請儘快分配班級" in data["warning"]

        # 確認學生已建立
        assert data["name"] == student_data["name"]
        assert data["classroom_id"] is None

    def test_unassigned_student_appears_in_list_within_24_hours(
        self, client: TestClient, auth_headers: dict, db: Session, test_teacher: Teacher
    ):
        """測試未分配班級的學生在24小時內會出現在列表中"""
        # 建立一個未分配班級的學生
        student = Student(
            name="24小時內未分配學生",
            email=f"recent_unassigned_{datetime.now().timestamp()}@test.com",
            birthdate=datetime(2012, 1, 1).date(),
            password_hash=get_password_hash("20120101"),
            is_active=True,
            created_at=datetime.utcnow() - timedelta(hours=12),  # 12小時前建立
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # 取得學生列表
        response = client.get("/api/teachers/students", headers=auth_headers)
        assert response.status_code == 200

        students = response.json()

        # 確認未分配學生出現在列表中
        found = False
        for s in students:
            if s["id"] == student.id:
                found = True
                assert s["classroom_name"] == "未分配"
                assert s["classroom_id"] is None
                break

        assert found, "未分配學生應該出現在列表中（24小時內）"

    def test_old_unassigned_student_not_in_list(
        self, client: TestClient, auth_headers: dict, db: Session, test_teacher: Teacher
    ):
        """測試超過24小時的未分配學生不會出現在列表中"""
        # 建立一個超過24小時的未分配學生
        old_student = Student(
            name="超過24小時未分配學生",
            email=f"old_unassigned_{datetime.now().timestamp()}@test.com",
            birthdate=datetime(2012, 1, 1).date(),
            password_hash=get_password_hash("20120101"),
            is_active=True,
            created_at=datetime.utcnow() - timedelta(hours=25),  # 25小時前建立
        )
        db.add(old_student)
        db.commit()
        db.refresh(old_student)

        # 取得學生列表
        response = client.get("/api/teachers/students", headers=auth_headers)
        assert response.status_code == 200

        students = response.json()

        # 確認超過24小時的未分配學生不在列表中
        found = False
        for s in students:
            if s["id"] == old_student.id:
                found = True
                break

        assert not found, "超過24小時的未分配學生不應該出現在列表中"

    def test_assigned_student_always_appears(
        self, client: TestClient, auth_headers: dict, db: Session, test_teacher: Teacher
    ):
        """測試已分配班級的學生永遠會出現在列表中"""
        # 建立班級
        classroom = Classroom(name="測試班級", teacher_id=test_teacher.id, is_active=True)
        db.add(classroom)
        db.commit()
        db.refresh(classroom)

        # 建立學生（超過24小時）
        student = Student(
            name="已分配班級學生",
            email=f"assigned_{datetime.now().timestamp()}@test.com",
            birthdate=datetime(2012, 1, 1).date(),
            password_hash=get_password_hash("20120101"),
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=30),  # 30天前建立
        )
        db.add(student)
        db.commit()
        db.refresh(student)

        # 分配到班級
        enrollment = ClassroomStudent(classroom_id=classroom.id, student_id=student.id, is_active=True)
        db.add(enrollment)
        db.commit()

        # 取得學生列表
        response = client.get("/api/teachers/students", headers=auth_headers)
        assert response.status_code == 200

        students = response.json()

        # 確認已分配班級的學生出現在列表中
        found = False
        for s in students:
            if s["id"] == student.id:
                found = True
                assert s["classroom_name"] == classroom.name
                assert s["classroom_id"] == classroom.id
                break

        assert found, "已分配班級的學生應該永遠出現在列表中"


if __name__ == "__main__":
    # 可以直接執行測試
    pytest.main([__file__, "-v"])
