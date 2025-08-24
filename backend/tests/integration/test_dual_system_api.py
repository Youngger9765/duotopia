"""
測試雙體系 API 端點
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
from tests.conftest import db
from models import User, UserRole, Classroom, School
from auth import get_password_hash
import uuid


@pytest.fixture
def client(db):
    """創建測試客戶端"""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def institutional_teacher_token(client, db):
    """創建機構教師並返回 token"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="inst_teacher@test.com",
        full_name="機構教師",
        role=UserRole.TEACHER,
        is_individual_teacher=False,
        is_institutional_admin=True,
        current_role_context="institutional",
        hashed_password=get_password_hash("test123")
    )
    db.add(teacher)
    db.commit()
    
    response = client.post("/api/auth/login", data={
        "username": "inst_teacher@test.com",
        "password": "test123"
    })
    return response.json()["access_token"]


@pytest.fixture
def individual_teacher_token(client, db):
    """創建個體戶教師並返回 token"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="ind_teacher@test.com",
        full_name="個體戶教師",
        role=UserRole.TEACHER,
        is_individual_teacher=True,
        is_institutional_admin=False,
        current_role_context="individual",
        hashed_password=get_password_hash("test123")
    )
    db.add(teacher)
    db.commit()
    
    response = client.post("/api/auth/login", data={
        "username": "ind_teacher@test.com",
        "password": "test123"
    })
    return response.json()["access_token"]


class TestDualSystemAPI:
    """測試雙體系 API"""
    
    def test_institutional_teacher_creates_classroom(self, client, institutional_teacher_token, db):
        """測試機構教師創建教室"""
        # 先創建一個學校
        from models import School
        school = School(
            id=str(uuid.uuid4()),
            name="測試學校",
            code="TEST001"
        )
        db.add(school)
        db.commit()
        
        # 創建教室
        response = client.post(
            "/api/teachers/classrooms",
            json={
                "name": "數學教室 A",
                "grade_level": "國小三年級",
                "school_id": school.id
            },
            headers={"Authorization": f"Bearer {institutional_teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "數學教室 A"
        assert data["school_id"] == school.id
    
    def test_individual_teacher_creates_classroom(self, client, individual_teacher_token):
        """測試個體戶教師創建教室（不需要 school_id）"""
        response = client.post(
            "/api/teachers/classrooms",
            json={
                "name": "Amy 的英語小班",
                "grade_level": "國小1-3年級"
            },
            headers={"Authorization": f"Bearer {individual_teacher_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Amy 的英語小班"
        assert data.get("school_id") is None
    
    def test_role_context_affects_classroom_list(self, client, db):
        """測試角色上下文影響教室列表"""
        # 創建混合型教師
        teacher = User(
            id=str(uuid.uuid4()),
            email="hybrid@test.com",
            full_name="混合型教師",
            role=UserRole.TEACHER,
            is_individual_teacher=True,
            is_institutional_admin=True,
            current_role_context="individual",
            hashed_password=get_password_hash("test123")
        )
        db.add(teacher)
        
        # 創建學校
        school = School(
            id=str(uuid.uuid4()),
            name="測試學校",
            code="TEST002"
        )
        db.add(school)
        
        # 創建個體戶教室（無 school_id）
        ind_classroom = Classroom(
            id=str(uuid.uuid4()),
            name="個人教室",
            teacher_id=teacher.id,
            school_id=None  # 個體戶教室
        )
        db.add(ind_classroom)
        
        # 創建機構教室（有 school_id）
        inst_classroom = Classroom(
            id=str(uuid.uuid4()),
            name="機構教室",
            teacher_id=teacher.id,
            school_id=school.id  # 機構教室
        )
        db.add(inst_classroom)
        db.commit()
        
        # 登入
        response = client.post("/api/auth/login", data={
            "username": "hybrid@test.com",
            "password": "test123"
        })
        token = response.json()["access_token"]
        
        # 在個體戶模式下查詢
        response = client.get(
            "/api/individual/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        classrooms = response.json()
        # 應該只看到個人教室
        assert len([c for c in classrooms if c["name"] == "個人教室"]) == 1
        assert len([c for c in classrooms if c["name"] == "機構教室"]) == 0
        
        # 切換到機構模式
        teacher.current_role_context = "institutional"
        db.commit()
        
        # 再次查詢（使用機構 API）
        response = client.get(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        classrooms = response.json()
        # 現在應該看到機構教室
        assert any(c["name"] == "機構教室" for c in classrooms)