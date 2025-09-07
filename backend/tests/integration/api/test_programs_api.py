"""
測試課程管理 API - 公版模板和三種複製方式
"""

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from main import app
from database import SessionLocal
from models import Teacher, Program, Classroom, Lesson
from auth import get_password_hash


@pytest.fixture
def db():
    """建立測試用資料庫 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """建立測試客戶端"""
    return TestClient(app)


@pytest.fixture
def test_teacher(db: Session):
    """建立測試用教師"""
    # 先清理可能存在的測試資料 - 需要先刪除關聯的程式
    existing_teacher = (
        db.query(Teacher)
        .filter(Teacher.email == "test_programs_teacher@example.com")
        .first()
    )
    if existing_teacher:
        # 取得所有相關的 Programs
        programs = (
            db.query(Program).filter(Program.teacher_id == existing_teacher.id).all()
        )
        for program in programs:
            # 刪除關聯的 Lessons
            db.query(Lesson).filter(Lesson.program_id == program.id).delete()
        # 刪除 Programs
        db.query(Program).filter(Program.teacher_id == existing_teacher.id).delete()
        # 刪除 Classrooms
        db.query(Classroom).filter(Classroom.teacher_id == existing_teacher.id).delete()
        # 最後刪除 Teacher
        db.delete(existing_teacher)
        db.commit()

    teacher = Teacher(
        email="test_programs_teacher@example.com",
        password_hash=get_password_hash("password123"),
        name="Test Programs Teacher",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def auth_headers(client: TestClient, test_teacher):
    """取得認證 headers"""
    response = client.post(
        "/api/auth/teacher/login",
        json={"email": test_teacher.email, "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_classroom(db: Session, test_teacher):
    """建立測試用班級"""
    classroom = Classroom(name="Test Classroom", teacher_id=test_teacher.id, level="A1")
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


@pytest.fixture
def test_classroom_2(db: Session, test_teacher):
    """建立第二個測試用班級"""
    classroom = Classroom(
        name="Another Classroom", teacher_id=test_teacher.id, level="B1"
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


class TestProgramTemplates:
    """測試公版課程模板功能"""

    def test_create_template_program(self, client: TestClient, auth_headers):
        """測試建立公版課程模板"""
        response = client.post(
            "/api/programs/templates",
            headers=auth_headers,
            json={
                "name": "初級英語會話",
                "description": "適合初學者的英語會話課程",
                "level": "A1",
                "estimated_hours": 20,
                "tags": ["speaking", "beginner"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "初級英語會話"
        assert data["is_template"] is True
        assert data["classroom_id"] is None
        assert data["source_metadata"]["created_by"] == "manual"

    def test_get_template_programs(
        self, client: TestClient, db: Session, auth_headers, test_teacher
    ):
        """測試取得公版課程模板列表"""
        # 建立幾個公版課程
        for i in range(3):
            program = Program(
                name=f"Template {i}",
                is_template=True,
                teacher_id=test_teacher.id,
                classroom_id=None,
            )
            db.add(program)
        db.commit()

        response = client.get("/api/programs/templates", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(p["is_template"] for p in data)
        assert all(p["classroom_id"] is None for p in data)


class TestProgramCopy:
    """測試三種複製方式"""

    def test_copy_from_template(
        self,
        client: TestClient,
        db: Session,
        auth_headers,
        test_teacher,
        test_classroom,
    ):
        """測試從公版模板複製到班級"""
        # 建立公版模板
        template = Program(
            name="公版課程",
            description="這是公版課程",
            is_template=True,
            teacher_id=test_teacher.id,
            level="A1",
            estimated_hours=10,
        )
        db.add(template)
        db.commit()
        db.refresh(template)

        # 加入 lessons
        lesson = Lesson(
            program_id=template.id,
            name="第一課",
            description="第一課內容",
            order_index=0,
        )
        db.add(lesson)
        db.commit()

        # 複製到班級
        response = client.post(
            "/api/programs/copy-from-template",
            headers=auth_headers,
            json={
                "template_id": template.id,
                "classroom_id": test_classroom.id,
                "name": "班級版課程",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "班級版課程"
        assert data["is_template"] is False
        assert data["classroom_id"] == test_classroom.id
        assert data["source_type"] == "template"
        assert data["source_metadata"]["template_id"] == template.id

        # 檢查 lessons 是否也被複製
        new_program = db.query(Program).filter(Program.id == data["id"]).first()
        assert len(new_program.lessons) == 1
        assert new_program.lessons[0].name == "第一課"

    def test_copy_from_classroom(
        self,
        client: TestClient,
        db: Session,
        auth_headers,
        test_teacher,
        test_classroom,
        test_classroom_2,
    ):
        """測試從其他班級複製課程"""
        # 在第一個班級建立課程
        source_program = Program(
            name="班級課程",
            is_template=False,
            classroom_id=test_classroom.id,
            teacher_id=test_teacher.id,
            source_type="custom",
        )
        db.add(source_program)
        db.commit()
        db.refresh(source_program)

        # 複製到第二個班級
        response = client.post(
            "/api/programs/copy-from-classroom",
            headers=auth_headers,
            json={
                "source_program_id": source_program.id,
                "target_classroom_id": test_classroom_2.id,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert f"從{test_classroom.name}複製" in data["name"]
        assert data["classroom_id"] == test_classroom_2.id
        assert data["source_type"] == "classroom"
        assert data["source_metadata"]["source_program_id"] == source_program.id

    def test_create_custom_program(
        self, client: TestClient, auth_headers, test_classroom
    ):
        """測試在班級中自建課程"""
        response = client.post(
            f"/api/programs/create-custom?classroom_id={test_classroom.id}",
            headers=auth_headers,
            json={
                "name": "自訂課程",
                "description": "這是自訂的課程",
                "level": "B1",
                "estimated_hours": 15,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "自訂課程"
        assert data["is_template"] is False
        assert data["classroom_id"] == test_classroom.id
        assert data["source_type"] == "custom"
        assert data["source_metadata"]["created_by"] == "manual"


class TestProgramManagement:
    """測試課程管理功能"""

    def test_get_classroom_programs(
        self,
        client: TestClient,
        db: Session,
        auth_headers,
        test_teacher,
        test_classroom,
    ):
        """測試取得班級課程列表"""
        # 建立幾個班級課程
        for i in range(3):
            program = Program(
                name=f"Classroom Program {i}",
                is_template=False,
                classroom_id=test_classroom.id,
                teacher_id=test_teacher.id,
                order_index=i,
            )
            db.add(program)
        db.commit()

        response = client.get(
            f"/api/programs/classroom/{test_classroom.id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(p["classroom_id"] == test_classroom.id for p in data)

    def test_soft_delete_program(
        self, client: TestClient, db: Session, auth_headers, test_teacher
    ):
        """測試軟刪除課程"""
        # 建立課程
        program = Program(
            name="To Be Deleted", is_template=True, teacher_id=test_teacher.id
        )
        db.add(program)
        db.commit()
        db.refresh(program)

        # 軟刪除
        response = client.delete(f"/api/programs/{program.id}", headers=auth_headers)

        assert response.status_code == 200

        # 檢查資料庫
        db.refresh(program)
        assert program.is_active is False
        assert program.deleted_at is not None

    def test_get_copyable_programs(
        self,
        client: TestClient,
        db: Session,
        auth_headers,
        test_teacher,
        test_classroom,
    ):
        """測試取得可複製的課程列表"""
        # 建立公版模板
        template = Program(
            name="Template", is_template=True, teacher_id=test_teacher.id
        )
        db.add(template)

        # 建立班級課程
        classroom_program = Program(
            name="Classroom Program",
            is_template=False,
            classroom_id=test_classroom.id,
            teacher_id=test_teacher.id,
        )
        db.add(classroom_program)
        db.commit()

        response = client.get("/api/programs/copyable", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        names = [p["name"] for p in data]
        assert "Template" in names
        assert "Classroom Program" in names
