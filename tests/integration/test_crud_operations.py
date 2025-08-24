"""
Integration Test for CRUD Operations
Tests complete create, read, update, delete workflows
"""
import pytest
import uuid
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Classroom, Student, Course, ClassroomStudent
from backend.routers import individual_v2


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture
def db_session():
    """Create test database session"""
    Base.metadata.create_all(bind=engine)
    session = Session(bind=engine)
    
    def override_get_db():
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def test_teacher(db_session):
    """Create test teacher"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="crud_test@teacher.com",
        full_name="CRUD Test Teacher",
        role="teacher",
        is_individual_teacher=True,
        hashed_password="hashed"
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher


@pytest.fixture
def client(test_teacher, monkeypatch):
    """Create test client with auth mocked"""
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    return TestClient(app)


class TestClassroomCRUD:
    """Test complete CRUD operations for classrooms"""
    
    def test_complete_classroom_lifecycle(self, db_session, test_teacher, client):
        """Test create, read, update, delete lifecycle for classroom"""
        # 1. CREATE - Create new classroom
        create_data = {
            "name": "Test Classroom",
            "grade_level": "Grade 5",
            "difficulty_level": "A2"
        }
        create_response = client.post("/api/individual/classrooms", json=create_data)
        assert create_response.status_code == 201
        
        classroom = create_response.json()
        classroom_id = classroom["id"]
        assert classroom["name"] == "Test Classroom"
        assert classroom["grade_level"] == "Grade 5"
        assert classroom["student_count"] == 0
        
        # 2. READ - Get classroom list
        list_response = client.get("/api/individual/classrooms")
        assert list_response.status_code == 200
        classrooms = list_response.json()
        assert len(classrooms) == 1
        assert classrooms[0]["id"] == classroom_id
        
        # 3. READ - Get classroom detail
        detail_response = client.get(f"/api/individual/classrooms/{classroom_id}")
        assert detail_response.status_code == 200
        detail = detail_response.json()
        assert detail["id"] == classroom_id
        assert detail["name"] == "Test Classroom"
        assert detail["teacher_name"] == test_teacher.full_name
        assert detail["students"] == []
        assert detail["courses"] == []
        
        # 4. UPDATE - Currently no update endpoint, but we can add students
        # Create a student first
        student_data = {
            "name": "Test Student",
            "email": "student@test.com",
            "birth_date": "2010-01-01"
        }
        student_response = client.post("/api/individual/students", json=student_data)
        student_id = student_response.json()["id"]
        
        # Add student to classroom
        add_response = client.post(f"/api/individual/classrooms/{classroom_id}/students/{student_id}")
        assert add_response.status_code == 200
        
        # Verify student was added
        updated_detail = client.get(f"/api/individual/classrooms/{classroom_id}").json()
        assert updated_detail["student_count"] == 1
        assert len(updated_detail["students"]) == 1
        
        # 5. DELETE - Delete classroom
        delete_response = client.delete(f"/api/individual/classrooms/{classroom_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "教室已刪除"
        
        # Verify classroom is deleted (soft delete - marked inactive)
        list_after_delete = client.get("/api/individual/classrooms").json()
        assert len(list_after_delete) == 0
        
        # Verify in database it's marked inactive
        db_classroom = db_session.query(Classroom).filter_by(id=classroom_id).first()
        assert db_classroom is not None
        assert db_classroom.is_active == False


class TestStudentCRUD:
    """Test complete CRUD operations for students"""
    
    def test_complete_student_lifecycle(self, db_session, test_teacher, client):
        """Test create, read, update, delete lifecycle for student"""
        # Setup - Create a classroom first
        classroom_response = client.post("/api/individual/classrooms", json={"name": "Student Test Class"})
        classroom_id = classroom_response.json()["id"]
        
        # 1. CREATE - Create new student
        create_data = {
            "name": "John Doe",
            "email": "john.doe@test.com",
            "birth_date": "2010-05-15"
        }
        create_response = client.post("/api/individual/students", json=create_data)
        assert create_response.status_code == 201
        
        student = create_response.json()
        student_id = student["id"]
        assert student["full_name"] == "John Doe"
        assert student["email"] == "john.doe@test.com"
        assert student["birth_date"] == "2010-05-15"
        assert student["classroom_names"] == []
        
        # 2. READ - Get student list (empty since not in any classroom)
        list_response = client.get("/api/individual/students")
        assert list_response.status_code == 200
        assert len(list_response.json()) == 0
        
        # Add student to classroom
        client.post(f"/api/individual/classrooms/{classroom_id}/students/{student_id}")
        
        # Now student should appear in list
        list_response = client.get("/api/individual/students")
        assert list_response.status_code == 200
        students = list_response.json()
        assert len(students) == 1
        assert students[0]["id"] == student_id
        assert "Student Test Class" in students[0]["classroom_names"]
        
        # 3. UPDATE - Update student information
        update_data = {
            "name": "John Smith",
            "email": "john.smith@test.com",
            "birth_date": "2010-05-16"
        }
        update_response = client.put(f"/api/individual/students/{student_id}", json=update_data)
        assert update_response.status_code == 200
        
        # Verify update
        updated_list = client.get("/api/individual/students").json()
        assert updated_list[0]["full_name"] == "John Smith"
        assert updated_list[0]["email"] == "john.smith@test.com"
        
        # 4. DELETE - Delete student
        delete_response = client.delete(f"/api/individual/students/{student_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "學生已刪除"
        
        # Verify student is deleted
        list_after_delete = client.get("/api/individual/students").json()
        assert len(list_after_delete) == 0
        
        # Verify student is completely removed from database
        db_student = db_session.query(Student).filter_by(id=student_id).first()
        assert db_student is None


class TestCourseCRUD:
    """Test complete CRUD operations for courses"""
    
    def test_complete_course_lifecycle(self, db_session, test_teacher, client):
        """Test create, read, update (if available), delete lifecycle for course"""
        # 1. CREATE - Create new course
        create_data = {
            "title": "English Conversation 101",
            "description": "Basic English conversation skills",
            "difficulty_level": "A1"
        }
        create_response = client.post("/api/individual/courses", json=create_data)
        assert create_response.status_code == 201
        
        course = create_response.json()
        course_id = course["id"]
        assert course["title"] == "English Conversation 101"
        assert course["description"] == "Basic English conversation skills"
        assert course["difficulty_level"] == "A1"
        assert course["lesson_count"] == 0
        
        # 2. READ - Get course list
        list_response = client.get("/api/individual/courses")
        assert list_response.status_code == 200
        courses = list_response.json()
        assert len(courses) == 1
        assert courses[0]["id"] == course_id
        
        # 3. UPDATE - No update endpoint currently, but we can verify lesson count updates
        # Would need to add lessons through a lesson endpoint
        
        # 4. DELETE - No delete endpoint for courses currently
        # This is a design decision - courses might be kept for historical records


class TestClassroomStudentRelationship:
    """Test CRUD operations for classroom-student relationships"""
    
    def test_complete_relationship_lifecycle(self, db_session, test_teacher, client):
        """Test add/remove students from classrooms"""
        # Setup - Create classrooms and students
        classroom1 = client.post("/api/individual/classrooms", json={"name": "Class A"}).json()
        classroom2 = client.post("/api/individual/classrooms", json={"name": "Class B"}).json()
        
        student1 = client.post("/api/individual/students", json={
            "name": "Student 1",
            "email": "student1@test.com",
            "birth_date": "2010-01-01"
        }).json()
        
        student2 = client.post("/api/individual/students", json={
            "name": "Student 2",
            "email": "student2@test.com",
            "birth_date": "2010-02-02"
        }).json()
        
        # 1. CREATE - Add students to classrooms
        assert client.post(f"/api/individual/classrooms/{classroom1['id']}/students/{student1['id']}").status_code == 200
        assert client.post(f"/api/individual/classrooms/{classroom1['id']}/students/{student2['id']}").status_code == 200
        assert client.post(f"/api/individual/classrooms/{classroom2['id']}/students/{student1['id']}").status_code == 200
        
        # 2. READ - Get classroom students
        class1_students = client.get(f"/api/individual/classrooms/{classroom1['id']}/students").json()
        assert len(class1_students) == 2
        assert any(s["id"] == student1["id"] for s in class1_students)
        assert any(s["id"] == student2["id"] for s in class1_students)
        
        class2_students = client.get(f"/api/individual/classrooms/{classroom2['id']}/students").json()
        assert len(class2_students) == 1
        assert class2_students[0]["id"] == student1["id"]
        
        # Verify student list shows correct classroom assignments
        students = client.get("/api/individual/students").json()
        student1_data = next(s for s in students if s["id"] == student1["id"])
        assert set(student1_data["classroom_names"]) == {"Class A", "Class B"}
        
        student2_data = next(s for s in students if s["id"] == student2["id"])
        assert student2_data["classroom_names"] == ["Class A"]
        
        # 3. DELETE - Remove student from classroom
        assert client.delete(f"/api/individual/classrooms/{classroom1['id']}/students/{student1['id']}").status_code == 200
        
        # Verify removal
        class1_students_after = client.get(f"/api/individual/classrooms/{classroom1['id']}/students").json()
        assert len(class1_students_after) == 1
        assert class1_students_after[0]["id"] == student2["id"]
        
        # Student 1 should now only be in Class B
        students_after = client.get("/api/individual/students").json()
        student1_after = next(s for s in students_after if s["id"] == student1["id"])
        assert student1_after["classroom_names"] == ["Class B"]
        
        # 4. ERROR CASES - Test error handling
        # Try to add student again (should fail - already exists)
        response = client.post(f"/api/individual/classrooms/{classroom2['id']}/students/{student1['id']}")
        assert response.status_code == 400
        assert "學生已在教室中" in response.json()["detail"]
        
        # Try to remove non-existent relationship
        response = client.delete(f"/api/individual/classrooms/{classroom2['id']}/students/{student2['id']}")
        assert response.status_code == 404
        assert "學生不在此教室中" in response.json()["detail"]


class TestCascadingOperations:
    """Test cascading effects of CRUD operations"""
    
    def test_classroom_deletion_cascade(self, db_session, test_teacher, client):
        """Test effects of classroom deletion on students"""
        # Create classroom with students
        classroom = client.post("/api/individual/classrooms", json={"name": "Cascade Test"}).json()
        
        students = []
        for i in range(3):
            student = client.post("/api/individual/students", json={
                "name": f"Cascade Student {i}",
                "email": f"cascade{i}@test.com",
                "birth_date": "2010-01-01"
            }).json()
            students.append(student)
            client.post(f"/api/individual/classrooms/{classroom['id']}/students/{student['id']}")
        
        # Verify setup
        assert len(client.get("/api/individual/students").json()) == 3
        
        # Delete classroom
        client.delete(f"/api/individual/classrooms/{classroom['id']}")
        
        # Students should no longer appear in teacher's list (no classroom association)
        assert len(client.get("/api/individual/students").json()) == 0
        
        # But students still exist in database
        for student in students:
            db_student = db_session.query(Student).filter_by(id=student["id"]).first()
            assert db_student is not None
    
    def test_student_deletion_cascade(self, db_session, test_teacher, client):
        """Test effects of student deletion on classroom associations"""
        # Create classrooms and student
        classroom1 = client.post("/api/individual/classrooms", json={"name": "Class 1"}).json()
        classroom2 = client.post("/api/individual/classrooms", json={"name": "Class 2"}).json()
        
        student = client.post("/api/individual/students", json={
            "name": "Delete Test Student",
            "email": "delete@test.com",
            "birth_date": "2010-01-01"
        }).json()
        
        # Add to both classrooms
        client.post(f"/api/individual/classrooms/{classroom1['id']}/students/{student['id']}")
        client.post(f"/api/individual/classrooms/{classroom2['id']}/students/{student['id']}")
        
        # Verify setup
        assert len(client.get(f"/api/individual/classrooms/{classroom1['id']}/students").json()) == 1
        assert len(client.get(f"/api/individual/classrooms/{classroom2['id']}/students").json()) == 1
        
        # Delete student
        client.delete(f"/api/individual/students/{student['id']}")
        
        # Verify student removed from all classrooms
        assert len(client.get(f"/api/individual/classrooms/{classroom1['id']}/students").json()) == 0
        assert len(client.get(f"/api/individual/classrooms/{classroom2['id']}/students").json()) == 0
        
        # Verify classrooms still exist
        assert len(client.get("/api/individual/classrooms").json()) == 2


class TestDataConsistency:
    """Test data consistency across CRUD operations"""
    
    def test_concurrent_modifications(self, db_session, test_teacher, client):
        """Test data consistency with rapid modifications"""
        # Create initial data
        classroom = client.post("/api/individual/classrooms", json={"name": "Consistency Test"}).json()
        
        student_ids = []
        for i in range(10):
            student = client.post("/api/individual/students", json={
                "name": f"Student {i}",
                "email": f"student{i}@test.com",
                "birth_date": "2010-01-01"
            }).json()
            student_ids.append(student["id"])
        
        # Rapidly add and remove students
        for i, student_id in enumerate(student_ids):
            # Add to classroom
            client.post(f"/api/individual/classrooms/{classroom['id']}/students/{student_id}")
            
            # Every third student, immediately remove
            if i % 3 == 0:
                client.delete(f"/api/individual/classrooms/{classroom['id']}/students/{student_id}")
        
        # Verify final state
        classroom_students = client.get(f"/api/individual/classrooms/{classroom['id']}/students").json()
        classroom_detail = client.get(f"/api/individual/classrooms/{classroom['id']}").json()
        
        # Should have 7 students (10 - 3 removed)
        assert len(classroom_students) == 7
        assert classroom_detail["student_count"] == 7
        
        # Verify student list consistency
        all_students = client.get("/api/individual/students").json()
        assert len(all_students) == 7
        
        # All students should show correct classroom
        for student in all_students:
            assert "Consistency Test" in student["classroom_names"]
    
    def test_data_integrity_after_errors(self, db_session, test_teacher, client):
        """Test data remains consistent after failed operations"""
        # Create classroom and student
        classroom = client.post("/api/individual/classrooms", json={"name": "Integrity Test"}).json()
        student = client.post("/api/individual/students", json={
            "name": "Integrity Student",
            "email": "integrity@test.com",
            "birth_date": "2010-01-01"
        }).json()
        
        # Add student to classroom
        client.post(f"/api/individual/classrooms/{classroom['id']}/students/{student['id']}")
        
        # Try invalid operations
        # 1. Add same student again (should fail)
        response = client.post(f"/api/individual/classrooms/{classroom['id']}/students/{student['id']}")
        assert response.status_code == 400
        
        # 2. Delete non-existent student from classroom
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/individual/classrooms/{classroom['id']}/students/{fake_id}")
        assert response.status_code == 404
        
        # 3. Create student with duplicate email
        response = client.post("/api/individual/students", json={
            "name": "Duplicate Email",
            "email": "integrity@test.com",
            "birth_date": "2010-01-01"
        })
        assert response.status_code == 400
        
        # Verify data integrity after errors
        classroom_detail = client.get(f"/api/individual/classrooms/{classroom['id']}").json()
        assert classroom_detail["student_count"] == 1
        
        students = client.get("/api/individual/students").json()
        assert len(students) == 1
        assert students[0]["email"] == "integrity@test.com"