"""
Integration tests for student batch import functionality.
Tests all possible error scenarios and edge cases with TDD approach.
"""

import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from models import Teacher, Student, Classroom, ClassroomStudent
from auth import get_password_hash


@pytest.fixture
def teacher_with_classrooms(test_session):
    """Create a teacher with multiple classrooms"""
    teacher = Teacher(
        name="Test Teacher",
        email="teacher@test.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    test_session.add(teacher)
    test_session.commit()

    # Create classrooms
    classroom_a = Classroom(name="A班", teacher_id=teacher.id, is_active=True)
    classroom_b = Classroom(name="B班", teacher_id=teacher.id, is_active=True)
    test_session.add_all([classroom_a, classroom_b])
    test_session.commit()

    return {"teacher": teacher, "classrooms": {"A班": classroom_a, "B班": classroom_b}}


@pytest.fixture
def auth_headers(teacher_with_classrooms):
    """Get auth headers for teacher"""
    from auth import create_access_token

    token = create_access_token(
        {
            "sub": teacher_with_classrooms["teacher"].id,  # Use teacher ID not email
            "type": "teacher",  # Required by get_current_teacher
        }
    )
    return {"Authorization": f"Bearer {token}"}


class TestStudentBatchImport:
    """Test batch import of students with CSV/Excel data"""

    def test_successful_batch_import_all_valid(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test successful import with all valid data"""
        batch_data = {
            "students": [
                {"name": "王小明", "classroom_name": "A班", "birthdate": "2012-01-01"},
                {"name": "李小華", "classroom_name": "A班", "birthdate": "2012-02-15"},
                {"name": "張小美", "classroom_name": "B班", "birthdate": "2012-03-20"},
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0
        assert len(data["errors"]) == 0

        # Verify students were created
        students = (
            test_session.query(Student)
            .filter(Student.name.in_(["王小明", "李小華", "張小美"]))
            .all()
        )
        assert len(students) == 3

        # Verify classroom assignments
        for student in students:
            if student.name in ["王小明", "李小華"]:
                enrollment = (
                    test_session.query(ClassroomStudent)
                    .filter(ClassroomStudent.student_id == student.id)
                    .first()
                )
                assert (
                    enrollment.classroom_id
                    == teacher_with_classrooms["classrooms"]["A班"].id
                )
            elif student.name == "張小美":
                enrollment = (
                    test_session.query(ClassroomStudent)
                    .filter(ClassroomStudent.student_id == student.id)
                    .first()
                )
                assert (
                    enrollment.classroom_id
                    == teacher_with_classrooms["classrooms"]["B班"].id
                )

    def test_batch_import_with_missing_classrooms(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with non-existent classrooms"""
        batch_data = {
            "students": [
                {
                    "name": "王小明",
                    "classroom_name": "A班",  # Exists
                    "birthdate": "2012-01-01",
                },
                {
                    "name": "李小華",
                    "classroom_name": "C班",  # Does not exist
                    "birthdate": "2012-02-15",
                },
                {
                    "name": "張小美",
                    "classroom_name": "D班",  # Does not exist
                    "birthdate": "2012-03-20",
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["error_count"] == 2
        assert len(data["errors"]) == 2
        assert "班級「C班」不存在" in data["errors"][0]["error"]
        assert "班級「D班」不存在" in data["errors"][1]["error"]

        # Verify only valid student was created
        students = test_session.query(Student).filter(Student.name == "王小明").all()
        assert len(students) == 1

    def test_batch_import_various_date_formats(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with various date formats"""
        batch_data = {
            "students": [
                {
                    "name": "學生1",
                    "classroom_name": "A班",
                    "birthdate": "20120101",  # YYYYMMDD format
                },
                {
                    "name": "學生2",
                    "classroom_name": "A班",
                    "birthdate": "2012-01-01",  # YYYY-MM-DD format
                },
                {
                    "name": "學生3",
                    "classroom_name": "A班",
                    "birthdate": "2012/01/01",  # YYYY/MM/DD format
                },
                {
                    "name": "學生4",
                    "classroom_name": "A班",
                    "birthdate": "01/01/2012",  # MM/DD/YYYY format
                },
                {
                    "name": "學生5",
                    "classroom_name": "A班",
                    "birthdate": "2012年1月1日",  # Chinese format
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] >= 3  # At least the first 3 formats should work

        # Verify dates were parsed correctly
        student1 = test_session.query(Student).filter(Student.name == "學生1").first()
        assert student1.birthdate == date(2012, 1, 1)

        student2 = test_session.query(Student).filter(Student.name == "學生2").first()
        assert student2.birthdate == date(2012, 1, 1)

        student3 = test_session.query(Student).filter(Student.name == "學生3").first()
        assert student3.birthdate == date(2012, 1, 1)

    def test_batch_import_invalid_date_formats(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with invalid date formats"""
        batch_data = {
            "students": [
                {"name": "學生1", "classroom_name": "A班", "birthdate": "invalid-date"},
                {
                    "name": "學生2",
                    "classroom_name": "A班",
                    "birthdate": "2012-13-45",  # Invalid month and day
                },
                {
                    "name": "學生3",
                    "classroom_name": "A班",
                    "birthdate": "",  # Empty string
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 3
        assert all("無效的日期格式" in error["error"] for error in data["errors"])

    def test_batch_import_duplicate_students(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with duplicate student names in same classroom"""
        # First create a student
        existing_student = Student(
            name="王小明",
            email="existing@test.com",
            birthdate=date(2012, 1, 1),
            password_hash=get_password_hash("20120101"),
            is_active=True,
        )
        test_session.add(existing_student)
        test_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=teacher_with_classrooms["classrooms"]["A班"].id,
            student_id=existing_student.id,
            is_active=True,
        )
        test_session.add(enrollment)
        test_session.commit()

        # Try to import duplicate
        batch_data = {
            "students": [
                {
                    "name": "王小明",  # Duplicate
                    "classroom_name": "A班",
                    "birthdate": "2012-01-01",
                },
                {
                    "name": "李小華",  # New student
                    "classroom_name": "A班",
                    "birthdate": "2012-02-15",
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1  # Only new student
        assert data["error_count"] == 1  # Duplicate rejected
        assert "學生「王小明」已存在於班級「A班」" in data["errors"][0]["error"]

    def test_batch_import_empty_data(self, test_client: TestClient, auth_headers):
        """Test import with empty data"""
        batch_data = {"students": []}

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "沒有提供學生資料" in data["detail"]

    def test_batch_import_missing_required_fields(
        self, test_client: TestClient, teacher_with_classrooms, auth_headers
    ):
        """Test import with missing required fields"""
        batch_data = {
            "students": [
                {
                    "name": "王小明",
                    "classroom_name": "A班"
                    # Missing birthdate
                },
                {
                    "classroom_name": "A班",
                    "birthdate": "2012-01-01"
                    # Missing name
                },
                {
                    "name": "張小美",
                    "birthdate": "2012-03-20"
                    # Missing classroom_name
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 3
        assert any("缺少必要欄位" in error["error"] for error in data["errors"])

    def test_batch_import_special_characters_in_names(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with special characters in names"""
        batch_data = {
            "students": [
                {
                    "name": "王·小明",  # Middle dot
                    "classroom_name": "A班",
                    "birthdate": "2012-01-01",
                },
                {
                    "name": "Mary Jane",  # English name
                    "classroom_name": "A班",
                    "birthdate": "2012-02-15",
                },
                {
                    "name": "王小明-2",  # With number
                    "classroom_name": "A班",
                    "birthdate": "2012-03-20",
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["error_count"] == 0

    def test_batch_import_excel_serial_dates(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with Excel serial date numbers"""
        batch_data = {
            "students": [
                {
                    "name": "學生1",
                    "classroom_name": "A班",
                    "birthdate": 40909,  # Excel serial for 2012-01-01
                },
                {
                    "name": "學生2",
                    "classroom_name": "A班",
                    "birthdate": "40909",  # String version
                },
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Should handle Excel serial dates
        assert data["success_count"] == 2

        # Verify dates were parsed correctly
        student1 = test_session.query(Student).filter(Student.name == "學生1").first()
        assert student1.birthdate == date(2012, 1, 1)

    def test_batch_import_large_batch(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test import with large number of students (100+)"""
        students_data = []
        for i in range(150):
            students_data.append(
                {
                    "name": f"學生{i+1:03d}",
                    "classroom_name": "A班" if i % 2 == 0 else "B班",
                    "birthdate": f"2012-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
                }
            )

        batch_data = {"students": students_data}

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 150
        assert data["error_count"] == 0

        # Verify all students were created
        students = test_session.query(Student).filter(Student.name.like("學生%")).all()
        assert len(students) == 150

    def test_batch_import_without_email_generation(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test that emails are NOT auto-generated - students can bind their own email later"""
        batch_data = {
            "students": [
                {
                    "name": "王小明",
                    "classroom_name": "A班",
                    "birthdate": "2012-01-01"
                    # No email provided
                }
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1

        # Verify email was NOT generated (should be None)
        student = test_session.query(Student).filter(Student.name == "王小明").first()
        assert student.email is None  # Students should bind email themselves later

    def test_batch_import_unauthorized(self, client: TestClient):
        """Test import without authentication"""
        batch_data = {
            "students": [
                {"name": "王小明", "classroom_name": "A班", "birthdate": "2012-01-01"}
            ]
        }

        response = client.post("/api/teachers/students/batch-import", json=batch_data)

        assert response.status_code == 401

    def test_batch_import_future_birthdate(
        self, test_client: TestClient, teacher_with_classrooms, auth_headers
    ):
        """Test import with future birthdates"""
        future_date = datetime.now().date().replace(year=datetime.now().year + 1)

        batch_data = {
            "students": [
                {
                    "name": "未來學生",
                    "classroom_name": "A班",
                    "birthdate": future_date.isoformat(),
                }
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["error_count"] == 1
        assert "生日不能是未來日期" in data["errors"][0]["error"]

    def test_batch_import_whitespace_handling(
        self,
        test_client: TestClient,
        test_session: Session,
        teacher_with_classrooms,
        auth_headers,
    ):
        """Test handling of whitespace in data"""
        batch_data = {
            "students": [
                {
                    "name": "  王小明  ",  # Leading/trailing spaces
                    "classroom_name": " A班 ",  # Leading/trailing spaces
                    "birthdate": " 2012-01-01 ",  # Leading/trailing spaces
                }
            ]
        }

        response = test_client.post(
            "/api/teachers/students/batch-import", json=batch_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1

        # Verify trimmed values were used
        student = test_session.query(Student).filter(Student.name == "王小明").first()
        assert student is not None
        enrollment = (
            test_session.query(ClassroomStudent)
            .filter(ClassroomStudent.student_id == student.id)
            .first()
        )
        assert enrollment.classroom_id == teacher_with_classrooms["classrooms"]["A班"].id
