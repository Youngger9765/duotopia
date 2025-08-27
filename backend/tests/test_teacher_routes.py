"""
Tests for teacher routes (Dashboard, Classrooms, Students, Programs)
"""
import pytest
from datetime import date
from models import Teacher, Classroom, Student, ClassroomStudent, Program, ProgramLevel
from auth import get_password_hash


@pytest.fixture
def demo_teacher_with_data(db):
    """Create demo teacher with classrooms, students and programs"""
    # Create teacher
    teacher = Teacher(
        email="test@teacher.com",
        password_hash=get_password_hash("testpass"),
        name="Test Teacher",
        is_demo=False,
        is_active=True
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    
    # Create classrooms
    classroom1 = Classroom(
        name="Class A",
        description="Test Class A",
        level=ProgramLevel.A1,
        teacher_id=teacher.id,
        is_active=True
    )
    classroom2 = Classroom(
        name="Class B", 
        description="Test Class B",
        level=ProgramLevel.A2,
        teacher_id=teacher.id,
        is_active=True
    )
    db.add_all([classroom1, classroom2])
    db.commit()
    db.refresh(classroom1)
    db.refresh(classroom2)
    
    # Create students
    student1 = Student(
        name="Student 1",
        email="student1@test.com",
        password_hash=get_password_hash("20120101"),
        birthdate=date(2012, 1, 1),
        student_id="S001"
    )
    student2 = Student(
        name="Student 2",
        email="student2@test.com", 
        password_hash=get_password_hash("20120101"),
        birthdate=date(2012, 1, 1),
        student_id="S002"
    )
    db.add_all([student1, student2])
    db.commit()
    db.refresh(student1)
    db.refresh(student2)
    
    # Enroll students in classrooms
    enrollment1 = ClassroomStudent(classroom_id=classroom1.id, student_id=student1.id)
    enrollment2 = ClassroomStudent(classroom_id=classroom2.id, student_id=student2.id)
    db.add_all([enrollment1, enrollment2])
    
    # Create programs
    program1 = Program(
        name="Program 1",
        description="Test Program 1",
        level=ProgramLevel.A1,
        teacher_id=teacher.id,
        classroom_id=classroom1.id,
        estimated_hours=10
    )
    program2 = Program(
        name="Program 2", 
        description="Test Program 2",
        level=ProgramLevel.A2,
        teacher_id=teacher.id,
        classroom_id=classroom2.id,
        estimated_hours=20
    )
    db.add_all([program1, program2])
    db.commit()
    
    return {
        'teacher': teacher,
        'classrooms': [classroom1, classroom2],
        'students': [student1, student2],
        'programs': [program1, program2]
    }


class TestTeacherDashboard:
    """Test teacher dashboard endpoint"""
    
    def test_dashboard_success(self, client, demo_teacher_with_data):
        teacher = demo_teacher_with_data['teacher']
        
        # Login first
        login_response = client.post("/api/auth/teacher/login", json={
            "email": teacher.email,
            "password": "testpass"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # Get dashboard data
        response = client.get(
            "/api/teachers/dashboard",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "teacher" in data
        assert "classroom_count" in data
        assert "student_count" in data
        assert "program_count" in data
        assert "classrooms" in data
        assert "recent_students" in data
        
        # Verify counts
        assert data["classroom_count"] == 2
        assert data["student_count"] == 2
        assert data["program_count"] == 2
        
        # Verify teacher info
        assert data["teacher"]["email"] == teacher.email
        assert data["teacher"]["name"] == teacher.name
    
    def test_dashboard_unauthorized(self, client):
        response = client.get("/api/teachers/dashboard")
        assert response.status_code == 401


class TestTeacherClassrooms:
    """Test teacher classrooms endpoint"""
    
    def test_classrooms_success(self, client, demo_teacher_with_data):
        teacher = demo_teacher_with_data['teacher']
        
        # Login first
        login_response = client.post("/api/auth/teacher/login", json={
            "email": teacher.email,
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        # Get classrooms
        response = client.get(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        classrooms = response.json()
        
        assert len(classrooms) == 2
        
        # Verify first classroom
        classroom = classrooms[0]
        assert "id" in classroom
        assert "name" in classroom
        assert "description" in classroom
        assert "student_count" in classroom
        assert "students" in classroom
        
        # Verify students are included
        assert len(classroom["students"]) == 1
        student = classroom["students"][0]
        assert "id" in student
        assert "name" in student
        assert "email" in student
    
    def test_classrooms_unauthorized(self, client):
        response = client.get("/api/teachers/classrooms")
        assert response.status_code == 401


class TestTeacherPrograms:
    """Test teacher programs endpoint"""
    
    def test_programs_success(self, client, demo_teacher_with_data):
        teacher = demo_teacher_with_data['teacher']
        
        # Login first
        login_response = client.post("/api/auth/teacher/login", json={
            "email": teacher.email,
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        # Get programs
        response = client.get(
            "/api/teachers/programs",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        programs = response.json()
        
        assert len(programs) == 2
        
        # Verify first program
        program = programs[0]
        assert "id" in program
        assert "name" in program
        assert "description" in program
        assert "level" in program
        assert "classroom_id" in program
        assert "classroom_name" in program
        assert "estimated_hours" in program
        assert "is_active" in program
        assert "created_at" in program
        
        # Verify classroom relationship
        assert program["classroom_name"] in ["Class A", "Class B"]
    
    def test_programs_unauthorized(self, client):
        response = client.get("/api/teachers/programs")
        assert response.status_code == 401


class TestTeacherStudents:
    """Test teacher students endpoint (if exists)"""
    
    def test_teacher_can_see_all_students(self, client, demo_teacher_with_data):
        """Test that teacher can see students from all their classrooms"""
        teacher = demo_teacher_with_data['teacher']
        
        # Login first
        login_response = client.post("/api/auth/teacher/login", json={
            "email": teacher.email,
            "password": "testpass"
        })
        token = login_response.json()["access_token"]
        
        # Get classrooms (which include students)
        response = client.get(
            "/api/teachers/classrooms",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        classrooms = response.json()
        
        # Count total students across all classrooms
        total_students = sum(len(classroom["students"]) for classroom in classrooms)
        assert total_students == 2
        
        # Verify each classroom has its students
        for classroom in classrooms:
            assert len(classroom["students"]) >= 1
            for student in classroom["students"]:
                assert student["name"] in ["Student 1", "Student 2"]
                assert student["email"] in ["student1@test.com", "student2@test.com"]