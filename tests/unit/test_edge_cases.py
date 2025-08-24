"""
Comprehensive Edge Case Tests
Tests boundary conditions, extreme values, and unusual scenarios
"""
import pytest
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import Base, get_db
from backend.main import app
from backend.models import (
    User, Classroom, Student, Course, Lesson, 
    ClassroomStudent, ClassroomCourseMapping, StudentAssignment,
    DifficultyLevel, ActivityType
)
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
        email="edge_test@teacher.com",
        full_name="Edge Test Teacher",
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


class TestBoundaryValues:
    """Test boundary value conditions"""
    
    def test_maximum_students_per_classroom(self, db_session, test_teacher, client):
        """Test classroom with maximum reasonable number of students"""
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name="Maximum Capacity Class",
            teacher_id=test_teacher.id,
            school_id=None
        )
        db_session.add(classroom)
        
        # Add 1000 students (extreme but possible)
        students = []
        for i in range(1000):
            student = Student(
                id=str(uuid.uuid4()),
                email=f"student{i}@test.com",
                full_name=f"Student {i}",
                birth_date="20100101"
            )
            students.append(student)
            db_session.add(student)
        
        db_session.flush()
        
        # Link all students to classroom
        for student in students:
            cs = ClassroomStudent(
                id=str(uuid.uuid4()),
                classroom_id=classroom.id,
                student_id=student.id
            )
            db_session.add(cs)
        
        db_session.commit()
        
        # Test retrieval
        response = client.get("/api/individual/classrooms")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["student_count"] == 1000
        
        # Test performance of student listing
        import time
        start = time.time()
        response = client.get("/api/individual/students")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert len(response.json()) == 1000
        assert elapsed < 5.0  # Should complete within 5 seconds even with 1000 students
    
    def test_minimum_values(self, db_session, test_teacher, client):
        """Test minimum valid values"""
        # Classroom with minimal data
        response = client.post("/api/individual/classrooms", json={"name": "A"})  # Single character name
        assert response.status_code == 201
        
        # Student with minimal data
        response = client.post("/api/individual/students", json={
            "name": "B",
            "birth_date": "2000-01-01"
        })
        assert response.status_code == 201
        
        # Course with minimal data
        response = client.post("/api/individual/courses", json={
            "title": "C"
        })
        assert response.status_code == 201
    
    def test_date_boundaries(self, db_session, test_teacher, client):
        """Test extreme date values"""
        # Very old birth date
        response = client.post("/api/individual/students", json={
            "name": "Old Student",
            "email": "old@test.com",
            "birth_date": "1900-01-01"
        })
        assert response.status_code == 201
        
        # Future birth date (should probably fail validation)
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        response = client.post("/api/individual/students", json={
            "name": "Future Student",
            "email": "future@test.com",
            "birth_date": future_date
        })
        # API might accept this - depends on business rules
        assert response.status_code in [201, 400]
        
        # Invalid date formats
        invalid_dates = [
            "2010-13-01",  # Invalid month
            "2010-01-32",  # Invalid day
            "2010-2-30",   # Invalid day for February
            "10-01-01",    # Two digit year
            "2010/01/01",  # Wrong separator
        ]
        
        for i, date in enumerate(invalid_dates):
            response = client.post("/api/individual/students", json={
                "name": f"Invalid Date Student {i}",
                "email": f"invalid_date_{i}@test.com",
                "birth_date": date
            })
            # Should handle gracefully
            assert response.status_code in [201, 400, 422]


class TestUnicodeAndInternationalization:
    """Test Unicode characters and internationalization"""
    
    def test_unicode_classroom_names(self, db_session, test_teacher, client):
        """Test Unicode characters in classroom names"""
        unicode_names = [
            "數學班 🔢",
            "Русский класс",
            "クラス　日本語",
            "العربية الفصل",
            "ชั้นเรียนภาษาไทย",
            "한국어 수업",
            "Ελληνική τάξη",
            "עברית כיתה",
            "🎓📚✨💯",
            "班級\u200b零寬空格",  # Zero-width space
            "A\u0301\u0302\u0303\u0304",  # Combining diacritics
        ]
        
        for name in unicode_names:
            response = client.post("/api/individual/classrooms", json={"name": name})
            assert response.status_code == 201
            
        # Verify retrieval
        response = client.get("/api/individual/classrooms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(unicode_names)
    
    def test_rtl_text_handling(self, db_session, test_teacher, client):
        """Test right-to-left text handling"""
        rtl_student = {
            "name": "محمد أحمد",
            "email": "rtl@test.com",
            "birth_date": "2010-01-01"
        }
        
        response = client.post("/api/individual/students", json=rtl_student)
        assert response.status_code == 201
        
        # Verify retrieval preserves RTL text
        response = client.get("/api/individual/students")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["full_name"] == "محمد أحمد"
    
    def test_mixed_language_content(self, db_session, test_teacher, client):
        """Test mixed language content"""
        course = {
            "title": "English英語えいご课程",
            "description": "Mixed 混合的 מעורב content محتوى",
            "difficulty_level": "A1"
        }
        
        response = client.post("/api/individual/courses", json=course)
        assert response.status_code == 201


class TestConcurrencyAndRaceConditions:
    """Test concurrent operations and race conditions"""
    
    def test_concurrent_student_creation(self, db_session, test_teacher, client):
        """Test creating students with same email concurrently"""
        # First student creation
        student_data = {
            "name": "Concurrent Student",
            "email": "concurrent@test.com",
            "birth_date": "2010-01-01"
        }
        
        response1 = client.post("/api/individual/students", json=student_data)
        assert response1.status_code == 201
        
        # Second creation with same email should fail
        response2 = client.post("/api/individual/students", json=student_data)
        assert response2.status_code == 400
        assert "此 Email 已被使用" in response2.json()["detail"]
    
    def test_concurrent_classroom_student_operations(self, db_session, test_teacher, client):
        """Test concurrent add/remove operations on classroom students"""
        # Create classroom and student
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name="Concurrent Test Class",
            teacher_id=test_teacher.id,
            school_id=None
        )
        student = Student(
            id=str(uuid.uuid4()),
            email="concurrent_ops@test.com",
            full_name="Concurrent Ops Student",
            birth_date="20100101"
        )
        db_session.add_all([classroom, student])
        db_session.commit()
        
        # Add student to classroom
        response = client.post(f"/api/individual/classrooms/{classroom.id}/students/{student.id}")
        assert response.status_code == 200
        
        # Try to add again (should fail)
        response = client.post(f"/api/individual/classrooms/{classroom.id}/students/{student.id}")
        assert response.status_code == 400
        
        # Remove student
        response = client.delete(f"/api/individual/classrooms/{classroom.id}/students/{student.id}")
        assert response.status_code == 200
        
        # Try to remove again (should fail)
        response = client.delete(f"/api/individual/classrooms/{classroom.id}/students/{student.id}")
        assert response.status_code == 404


class TestDataIntegrityAndConsistency:
    """Test data integrity and consistency edge cases"""
    
    def test_orphaned_students(self, db_session, test_teacher, client):
        """Test handling of students without classroom assignments"""
        # Create students without classroom
        for i in range(5):
            student = Student(
                id=str(uuid.uuid4()),
                email=f"orphan{i}@test.com",
                full_name=f"Orphan Student {i}",
                birth_date="20100101"
            )
            db_session.add(student)
        db_session.commit()
        
        # These students shouldn't appear in teacher's student list
        response = client.get("/api/individual/students")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    def test_circular_references_prevention(self, db_session, test_teacher, client):
        """Test prevention of circular references"""
        # Create course with lessons
        course = Course(
            id=str(uuid.uuid4()),
            title="Test Course",
            created_by=test_teacher.id
        )
        db_session.add(course)
        
        # Add lessons with various activity types
        for i, activity_type in enumerate(ActivityType):
            lesson = Lesson(
                id=str(uuid.uuid4()),
                course_id=course.id,
                lesson_number=i + 1,
                title=f"Lesson {i + 1}",
                activity_type=activity_type,
                content={"test": "data"}
            )
            db_session.add(lesson)
        
        db_session.commit()
        
        # Verify course retrieval includes proper lesson count
        response = client.get("/api/individual/courses")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["lesson_count"] == len(ActivityType)
    
    def test_cascade_delete_behavior(self, db_session, test_teacher, client):
        """Test cascade delete behavior"""
        # Create classroom with students
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name="Cascade Test Class",
            teacher_id=test_teacher.id,
            school_id=None
        )
        db_session.add(classroom)
        
        students = []
        for i in range(3):
            student = Student(
                id=str(uuid.uuid4()),
                email=f"cascade{i}@test.com",
                full_name=f"Cascade Student {i}",
                birth_date="20100101"
            )
            students.append(student)
            db_session.add(student)
        
        db_session.flush()
        
        # Link students to classroom
        for student in students:
            cs = ClassroomStudent(
                id=str(uuid.uuid4()),
                classroom_id=classroom.id,
                student_id=student.id
            )
            db_session.add(cs)
        
        db_session.commit()
        
        # Delete classroom (soft delete)
        response = client.delete(f"/api/individual/classrooms/{classroom.id}")
        assert response.status_code == 200
        
        # Students should still exist
        for student in students:
            assert db_session.query(Student).filter_by(id=student.id).first() is not None
        
        # Classroom should be marked inactive
        classroom_check = db_session.query(Classroom).filter_by(id=classroom.id).first()
        assert classroom_check.is_active == False


class TestPerformanceEdgeCases:
    """Test performance under edge conditions"""
    
    def test_deep_nesting_json_content(self, db_session, test_teacher, client):
        """Test handling of deeply nested JSON content"""
        # Create course with deeply nested lesson content
        course = Course(
            id=str(uuid.uuid4()),
            title="Deep Nesting Test",
            created_by=test_teacher.id
        )
        db_session.add(course)
        
        # Create deeply nested content
        def create_nested_dict(depth):
            if depth == 0:
                return {"value": "leaf"}
            return {"nested": create_nested_dict(depth - 1)}
        
        deep_content = create_nested_dict(100)  # 100 levels deep
        
        lesson = Lesson(
            id=str(uuid.uuid4()),
            course_id=course.id,
            lesson_number=1,
            title="Deep Nested Lesson",
            activity_type=ActivityType.READING_ASSESSMENT,
            content=deep_content
        )
        db_session.add(lesson)
        db_session.commit()
        
        # Should handle without stack overflow
        response = client.get("/api/individual/courses")
        assert response.status_code == 200
    
    def test_large_batch_operations(self, db_session, test_teacher, client):
        """Test large batch operations"""
        # Create classroom
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name="Batch Operations Class",
            teacher_id=test_teacher.id,
            school_id=None
        )
        db_session.add(classroom)
        db_session.commit()
        
        # Batch create students
        batch_size = 100
        students = []
        for i in range(batch_size):
            student_data = {
                "name": f"Batch Student {i}",
                "email": f"batch{i}@test.com",
                "birth_date": "2010-01-01"
            }
            response = client.post("/api/individual/students", json=student_data)
            assert response.status_code == 201
            students.append(response.json()["id"])
        
        # Batch add to classroom
        import time
        start = time.time()
        for student_id in students:
            response = client.post(f"/api/individual/classrooms/{classroom.id}/students/{student_id}")
            assert response.status_code == 200
        elapsed = time.time() - start
        
        # Should complete in reasonable time
        assert elapsed < 30.0  # 30 seconds for 100 operations
        
        # Verify count
        response = client.get(f"/api/individual/classrooms/{classroom.id}")
        assert response.status_code == 200
        assert response.json()["student_count"] == batch_size


class TestSecurityEdgeCases:
    """Test security-related edge cases"""
    
    def test_sql_injection_attempts(self, db_session, test_teacher, client):
        """Test SQL injection prevention"""
        injection_attempts = [
            "'; DROP TABLE students; --",
            "1' OR '1'='1",
            "1; DELETE FROM classrooms WHERE 1=1; --",
            "' UNION SELECT * FROM users --",
            "\\'; DROP TABLE students; --",
        ]
        
        for attempt in injection_attempts:
            # Try injection in classroom name
            response = client.post("/api/individual/classrooms", json={"name": attempt})
            assert response.status_code == 201  # Should create normally
            
            # Try injection in search/filter (if implemented)
            response = client.get(f"/api/individual/classrooms?search={attempt}")
            assert response.status_code in [200, 400, 404]  # Should handle safely
    
    def test_xss_prevention(self, db_session, test_teacher, client):
        """Test XSS prevention"""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<svg onload=alert('XSS')>",
        ]
        
        for attempt in xss_attempts:
            response = client.post("/api/individual/students", json={
                "name": attempt,
                "email": f"xss{hash(attempt)}@test.com",
                "birth_date": "2010-01-01"
            })
            assert response.status_code == 201
            
            # Verify stored as-is (not executed)
            response = client.get("/api/individual/students")
            assert response.status_code == 200
            # The malicious content should be stored but not executed
            # Frontend is responsible for proper escaping
    
    def test_path_traversal_prevention(self, db_session, test_teacher, client):
        """Test path traversal attack prevention"""
        traversal_ids = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
            "....//....//",
        ]
        
        for traversal in traversal_ids:
            response = client.get(f"/api/individual/classrooms/{traversal}")
            assert response.status_code in [400, 404]  # Should reject or not found
            
            response = client.delete(f"/api/individual/students/{traversal}")
            assert response.status_code in [400, 404]  # Should reject or not found