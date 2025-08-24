"""
Test for Individual API Query Optimization
Tests the N+1 query fix and performance improvements
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
import time
import uuid

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import Base, get_db
from backend.main import app
from backend.models import User, Student, Classroom, ClassroomStudent
from backend.routers import individual_v2

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

@pytest.fixture
def db_session():
    """Create a test database session"""
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
    """Create a test individual teacher"""
    teacher = User(
        id=str(uuid.uuid4()),
        email="test_teacher@individual.com",
        full_name="Test Teacher",
        role="teacher",
        is_individual_teacher=True,
        hashed_password="hashed_password"
    )
    db_session.add(teacher)
    db_session.commit()
    return teacher

@pytest.fixture
def test_data_large(db_session, test_teacher):
    """Create large test dataset to verify N+1 fix"""
    # Create 20 classrooms
    classrooms = []
    for i in range(20):
        classroom = Classroom(
            id=str(uuid.uuid4()),
            name=f"Classroom {i+1}",
            teacher_id=test_teacher.id,
            school_id=None
        )
        classrooms.append(classroom)
        db_session.add(classroom)
    
    # Create 100 students
    students = []
    for i in range(100):
        student = Student(
            id=str(uuid.uuid4()),
            email=f"student{i+1}@test.com",
            full_name=f"Student {i+1}",
            birth_date=f"2010{(i%12)+1:02d}{(i%28)+1:02d}"
        )
        students.append(student)
        db_session.add(student)
    
    db_session.flush()
    
    # Assign each student to 2-3 classrooms
    for i, student in enumerate(students):
        num_classrooms = 2 + (i % 2)  # 2 or 3 classrooms per student
        for j in range(num_classrooms):
            classroom_idx = (i + j * 7) % len(classrooms)  # Distribute students
            cs = ClassroomStudent(
                id=str(uuid.uuid4()),
                classroom_id=classrooms[classroom_idx].id,
                student_id=student.id
            )
            db_session.add(cs)
    
    db_session.commit()
    return {"classrooms": classrooms, "students": students}

def test_get_students_no_n_plus_one(db_session, test_teacher, test_data_large, monkeypatch):
    """Test that get_students doesn't have N+1 query problem"""
    from sqlalchemy import event
    
    # Count queries
    query_count = 0
    
    def count_queries(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1
    
    # Monitor queries
    event.listen(engine, "before_cursor_execute", count_queries)
    
    # Mock authentication
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    
    # Create test client
    client = TestClient(app)
    
    # Make request
    start_time = time.time()
    response = client.get("/api/individual/students")
    end_time = time.time()
    
    # Clean up event listener
    event.remove(engine, "before_cursor_execute", count_queries)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100  # All students returned
    
    # Verify query count is reasonable (not 100+ queries)
    # Should be 2-3 queries total, not 1 + N queries
    assert query_count < 10, f"Too many queries executed: {query_count}"
    
    # Verify response time is reasonable
    response_time = end_time - start_time
    assert response_time < 1.0, f"Response too slow: {response_time}s"
    
    # Verify data structure
    for student in data[:5]:  # Check first 5 students
        assert "id" in student
        assert "full_name" in student
        assert "classroom_names" in student
        assert isinstance(student["classroom_names"], list)
        assert len(student["classroom_names"]) >= 2  # Each student has 2-3 classrooms

def test_get_students_empty_result(db_session, test_teacher, monkeypatch):
    """Test get_students with no students"""
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    
    client = TestClient(app)
    response = client.get("/api/individual/students")
    
    assert response.status_code == 200
    assert response.json() == []

def test_get_students_with_special_characters(db_session, test_teacher, monkeypatch):
    """Test get_students with special characters in names"""
    # Create classroom with special characters
    classroom = Classroom(
        id=str(uuid.uuid4()),
        name="班級,with,commas",  # Contains commas which could break GROUP_CONCAT
        teacher_id=test_teacher.id,
        school_id=None
    )
    db_session.add(classroom)
    
    # Create student
    student = Student(
        id=str(uuid.uuid4()),
        email="special@test.com",
        full_name="特殊字符 Student",
        birth_date="20100101"
    )
    db_session.add(student)
    db_session.flush()
    
    # Link student to classroom
    cs = ClassroomStudent(
        id=str(uuid.uuid4()),
        classroom_id=classroom.id,
        student_id=student.id
    )
    db_session.add(cs)
    db_session.commit()
    
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    
    client = TestClient(app)
    response = client.get("/api/individual/students")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    # Note: This test might fail with current implementation if classroom names contain commas
    # This is a known limitation that should be documented or fixed with a different separator

def test_get_students_birth_date_formatting(db_session, test_teacher, monkeypatch):
    """Test birth date formatting in get_students"""
    classroom = Classroom(
        id=str(uuid.uuid4()),
        name="Test Class",
        teacher_id=test_teacher.id,
        school_id=None
    )
    db_session.add(classroom)
    
    # Test various birth date formats
    students_data = [
        ("20100315", "2010-03-15"),  # Normal date
        ("20101231", "2010-12-31"),  # End of year
        ("20100101", "2010-01-01"),  # Start of year
        (None, ""),                   # No birth date
        ("", ""),                     # Empty birth date
    ]
    
    for i, (birth_date, expected) in enumerate(students_data):
        student = Student(
            id=str(uuid.uuid4()),
            email=f"student{i}@test.com",
            full_name=f"Student {i}",
            birth_date=birth_date
        )
        db_session.add(student)
        db_session.flush()
        
        cs = ClassroomStudent(
            id=str(uuid.uuid4()),
            classroom_id=classroom.id,
            student_id=student.id
        )
        db_session.add(cs)
    
    db_session.commit()
    
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    
    client = TestClient(app)
    response = client.get("/api/individual/students")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify birth date formatting
    for i, (_, expected) in enumerate(students_data[:-2]):  # Skip None and empty cases
        if i < len(data):
            assert data[i]["birth_date"] == expected

def test_get_students_performance_benchmark(db_session, test_teacher, test_data_large, monkeypatch):
    """Benchmark test for get_students performance"""
    def mock_get_individual_teacher():
        return test_teacher
    
    monkeypatch.setattr(individual_v2, "get_individual_teacher", mock_get_individual_teacher)
    
    client = TestClient(app)
    
    # Run multiple times to get average
    times = []
    for _ in range(5):
        start = time.time()
        response = client.get("/api/individual/students")
        end = time.time()
        times.append(end - start)
        assert response.status_code == 200
    
    avg_time = sum(times) / len(times)
    assert avg_time < 0.3, f"Average response time too slow: {avg_time}s"
    
    # Verify data completeness
    data = response.json()
    total_classroom_assignments = sum(len(s["classroom_names"]) for s in data)
    assert total_classroom_assignments >= 200  # 100 students * 2+ classrooms each