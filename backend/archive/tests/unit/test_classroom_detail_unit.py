#!/usr/bin/env python3
"""
個體戶教室詳細功能單元測試
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import get_db
from models_dual_system import DualBase
from main import app
from models_dual_system import (
    DualUser, IndividualClassroom, IndividualCourse,
    IndividualStudent, IndividualEnrollment, UserRole
)
from auth import get_password_hash, create_access_token
import uuid

# 測試資料庫設定
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_classroom_detail.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

DualBase.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def db_session():
    """建立測試資料庫 session"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_teacher(db_session):
    """建立測試教師"""
    teacher = DualUser(
        id=str(uuid.uuid4()),
        email="test_teacher@individual.com",
        full_name="測試教師",
        role=UserRole.TEACHER,
        hashed_password=get_password_hash("test123"),
        is_individual_teacher=True,
        current_role_context="individual"
    )
    db_session.add(teacher)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher

@pytest.fixture
def test_classroom(db_session, test_teacher):
    """建立測試教室"""
    classroom = IndividualClassroom(
        id=str(uuid.uuid4()),
        name="測試教室",
        teacher_id=test_teacher.id,
        location="線上",
        pricing=1000,
        max_students=10
    )
    db_session.add(classroom)
    db_session.commit()
    db_session.refresh(classroom)
    return classroom

@pytest.fixture
def test_public_course(db_session, test_teacher):
    """建立測試公版課程"""
    course = IndividualCourse(
        id=str(uuid.uuid4()),
        title="公版測試課程",
        description="這是公版課程",
        teacher_id=test_teacher.id,
        is_public=True,
        classroom_id=None,
        pricing_per_lesson=800
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    return course

@pytest.fixture
def test_students(db_session):
    """建立測試學生"""
    students = []
    for i in range(3):
        student = IndividualStudent(
            id=str(uuid.uuid4()),
            full_name=f"測試學生{i+1}",
            email=f"test_student{i+1}@example.com"
        )
        db_session.add(student)
        students.append(student)
    db_session.commit()
    return students

@pytest.fixture
def auth_headers(test_teacher):
    """建立認證標頭"""
    token = create_access_token(data={"sub": test_teacher.email})
    return {"Authorization": f"Bearer {token}"}


class TestClassroomDetailAPI:
    """教室詳細功能 API 測試"""
    
    def test_get_classroom_students(self, db_session, test_classroom, test_students, auth_headers):
        """測試獲取教室學生列表"""
        # 將學生加入教室
        for student in test_students[:2]:
            enrollment = IndividualEnrollment(
                student_id=student.id,
                classroom_id=test_classroom.id,
                payment_status="paid"
            )
            db_session.add(enrollment)
        db_session.commit()
        
        # 調用 API
        response = client.get(
            f"/api/individual/classrooms/{test_classroom.id}/students",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["full_name"] == "測試學生1"
        assert data[0]["payment_status"] == "paid"
    
    def test_add_student_to_classroom(self, db_session, test_classroom, test_students, auth_headers):
        """測試新增學生到教室"""
        student = test_students[0]
        
        response = client.post(
            f"/api/individual/classrooms/{test_classroom.id}/students",
            headers=auth_headers,
            json={
                "student_id": student.id,
                "payment_status": "pending"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == student.id
        assert data["classroom_id"] == test_classroom.id
        assert data["payment_status"] == "pending"
        
        # 驗證資料庫
        enrollment = db_session.query(IndividualEnrollment).filter_by(
            student_id=student.id,
            classroom_id=test_classroom.id
        ).first()
        assert enrollment is not None
        assert enrollment.is_active is True
    
    def test_remove_student_from_classroom(self, db_session, test_classroom, test_students, auth_headers):
        """測試從教室移除學生"""
        # 先加入學生
        student = test_students[0]
        enrollment = IndividualEnrollment(
            id=str(uuid.uuid4()),
            student_id=student.id,
            classroom_id=test_classroom.id
        )
        db_session.add(enrollment)
        db_session.commit()
        
        # 移除學生
        response = client.delete(
            f"/api/individual/enrollments/{enrollment.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        
        # 驗證軟刪除
        db_session.refresh(enrollment)
        assert enrollment.is_active is False
    
    def test_get_classroom_courses(self, db_session, test_classroom, test_teacher, auth_headers):
        """測試獲取教室課程列表"""
        # 建立教室課程
        course = IndividualCourse(
            title="教室專屬課程",
            teacher_id=test_teacher.id,
            classroom_id=test_classroom.id,
            is_public=False
        )
        db_session.add(course)
        db_session.commit()
        
        response = client.get(
            f"/api/individual/classrooms/{test_classroom.id}/courses",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "教室專屬課程"
        assert data[0]["classroom_id"] == test_classroom.id
    
    def test_get_public_courses(self, db_session, test_public_course, auth_headers):
        """測試獲取公版課程列表"""
        response = client.get(
            "/api/individual/courses/public",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "公版測試課程"
        assert data[0]["is_public"] is True
        assert data[0]["classroom_id"] is None
    
    def test_copy_course_to_classroom(self, db_session, test_classroom, test_public_course, auth_headers):
        """測試複製公版課程到教室"""
        response = client.post(
            f"/api/individual/classrooms/{test_classroom.id}/courses/copy",
            headers=auth_headers,
            json={"source_course_id": test_public_course.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_public_course.title
        assert data["classroom_id"] == test_classroom.id
        assert data["copied_from_id"] == test_public_course.id
        assert data["is_public"] is False
        
        # 驗證資料庫
        copied_course = db_session.query(IndividualCourse).filter_by(
            classroom_id=test_classroom.id,
            copied_from_id=test_public_course.id
        ).first()
        assert copied_course is not None
        assert copied_course.title == test_public_course.title
    
    def test_copy_nonexistent_course(self, test_classroom, auth_headers):
        """測試複製不存在的課程"""
        response = client.post(
            f"/api/individual/classrooms/{test_classroom.id}/courses/copy",
            headers=auth_headers,
            json={"source_course_id": "nonexistent-id"}
        )
        
        assert response.status_code == 404
        assert "找不到課程" in response.json()["detail"]
    
    def test_unauthorized_access(self, test_classroom):
        """測試未授權存取"""
        response = client.get(
            f"/api/individual/classrooms/{test_classroom.id}/students"
        )
        assert response.status_code == 401
    
    def test_access_other_teacher_classroom(self, db_session, test_classroom, auth_headers):
        """測試存取其他教師的教室"""
        # 建立另一個教師和教室
        other_teacher = DualUser(
            email="other_teacher@individual.com",
            full_name="其他教師",
            role=UserRole.TEACHER,
            hashed_password=get_password_hash("test123"),
            is_individual_teacher=True
        )
        db_session.add(other_teacher)
        db_session.commit()
        
        other_classroom = IndividualClassroom(
            name="其他教室",
            teacher_id=other_teacher.id,
            location="線上",
            pricing=1000
        )
        db_session.add(other_classroom)
        db_session.commit()
        
        # 嘗試存取其他教師的教室
        response = client.get(
            f"/api/individual/classrooms/{other_classroom.id}/students",
            headers=auth_headers
        )
        
        # 應該返回 403 或空資料
        assert response.status_code in [403, 404]


class TestClassroomBusinessLogic:
    """教室業務邏輯測試"""
    
    def test_student_enrollment_limit(self, db_session, test_classroom, test_students):
        """測試教室學生人數限制"""
        test_classroom.max_students = 2
        db_session.commit()
        
        # 加入兩個學生（達到上限）
        for i in range(2):
            enrollment = IndividualEnrollment(
                student_id=test_students[i].id,
                classroom_id=test_classroom.id
            )
            db_session.add(enrollment)
        db_session.commit()
        
        # 檢查是否達到上限
        active_enrollments = db_session.query(IndividualEnrollment).filter_by(
            classroom_id=test_classroom.id,
            is_active=True
        ).count()
        
        assert active_enrollments == test_classroom.max_students
    
    def test_course_copy_tracking(self, db_session, test_classroom, test_public_course, test_teacher):
        """測試課程複製追蹤"""
        # 複製課程
        copied_course = IndividualCourse(
            title=test_public_course.title,
            description=test_public_course.description,
            teacher_id=test_teacher.id,
            classroom_id=test_classroom.id,
            copied_from_id=test_public_course.id,
            is_public=False,
            pricing_per_lesson=test_public_course.pricing_per_lesson
        )
        db_session.add(copied_course)
        db_session.commit()
        
        # 驗證關聯
        db_session.refresh(copied_course)
        assert copied_course.copied_from == test_public_course
        assert copied_course.classroom == test_classroom
    
    def test_payment_status_tracking(self, db_session, test_classroom, test_students):
        """測試付款狀態追蹤"""
        statuses = ["paid", "pending", "overdue"]
        
        for i, student in enumerate(test_students):
            enrollment = IndividualEnrollment(
                student_id=student.id,
                classroom_id=test_classroom.id,
                payment_status=statuses[i % len(statuses)]
            )
            db_session.add(enrollment)
        db_session.commit()
        
        # 查詢各種付款狀態
        for status in statuses:
            count = db_session.query(IndividualEnrollment).filter_by(
                classroom_id=test_classroom.id,
                payment_status=status
            ).count()
            assert count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])