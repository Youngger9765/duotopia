"""
Integration tests for Teachers Students API endpoints

Tests verify that student API responses return correct field names:
- Should return 'student_number' (not 'student_id')
- Related to Issue #31

Test Coverage:
- GET /api/teachers/classrooms - List students in classrooms
- GET /api/teachers/students/{id} - Get single student
- POST /api/teachers/students - Create new student
"""

import pytest
from fastapi import status
from models import Classroom, ClassroomStudent
from auth import create_access_token


@pytest.mark.integration
class TestTeachersStudentsAPI:
    """Test teachers students API response structure"""

    def test_list_classrooms_returns_students_with_student_number(
        self, test_client, demo_teacher, demo_student, test_db_session
    ):
        """
        Test: GET /api/teachers/classrooms returns student_number field

        Given: A student with student_number "TEST001"
        When: Teacher fetches classroom list
        Then: Response should contain 'student_number', not 'student_id'
        """
        # Arrange
        classroom = Classroom(
            name="測試班級",
            teacher_id=demo_teacher.id,
            level="A1",
            is_active=True,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        demo_student.student_number = "TEST001"
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
            is_active=True,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = test_client.get("/api/teachers/classrooms", headers=headers)

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

        test_classroom = next((c for c in data if c["id"] == classroom.id), None)
        assert test_classroom is not None
        assert "students" in test_classroom

        test_student = next(
            (s for s in test_classroom["students"] if s["id"] == demo_student.id),
            None,
        )
        assert test_student is not None
        assert (
            "student_number" in test_student
        ), "Response should contain 'student_number' field"
        assert (
            "student_id" not in test_student
        ), "Response should NOT contain 'student_id' field"
        assert test_student["student_number"] == "TEST001"

    def test_get_student_returns_student_number(
        self, test_client, demo_teacher, demo_student, test_db_session
    ):
        """
        Test: GET /api/teachers/students/{id} returns student_number field

        Given: A student with student_number "TEST002"
        When: Teacher fetches single student
        Then: Response should contain 'student_number', not 'student_id'
        """
        # Arrange
        classroom = Classroom(
            name="測試班級2",
            teacher_id=demo_teacher.id,
            level="A1",
            is_active=True,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        demo_student.student_number = "TEST002"
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
            is_active=True,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = test_client.get(
            f"/api/teachers/students/{demo_student.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert (
            "student_number" in data
        ), "Response should contain 'student_number' field"
        assert (
            "student_id" not in data
        ), "Response should NOT contain 'student_id' field"
        assert data["student_number"] == "TEST002"

    def test_create_student_returns_student_number(
        self, test_client, demo_teacher, test_db_session
    ):
        """
        Test: POST /api/teachers/students returns student_number field

        Given: Creating new student with student_number "TEST003"
        When: Teacher creates student
        Then: Response should contain 'student_number', not 'student_id'
        """
        # Arrange
        classroom = Classroom(
            name="測試班級3",
            teacher_id=demo_teacher.id,
            level="A1",
            is_active=True,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        new_student_data = {
            "name": "新學生",
            "email": "new_student_test@example.com",
            "birthdate": "2012-06-15",
            "student_number": "TEST003",
            "classroom_id": classroom.id,
        }

        # Act
        response = test_client.post(
            "/api/teachers/students",
            json=new_student_data,
            headers=headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert (
            "student_number" in data
        ), "Response should contain 'student_number' field"
        assert (
            "student_id" not in data
        ), "Response should NOT contain 'student_id' field"
        assert data["student_number"] == "TEST003"

        # Verify data persisted
        created_student_id = data["id"]
        verify_response = test_client.get(
            f"/api/teachers/students/{created_student_id}",
            headers=headers,
        )
        assert verify_response.status_code == status.HTTP_200_OK
        verify_data = verify_response.json()
        assert verify_data["student_number"] == "TEST003"

    def test_student_without_number_returns_null(
        self, test_client, demo_teacher, demo_student, test_db_session
    ):
        """
        Test: Student without student_number returns null (not undefined)

        Given: A student without student_number
        When: Teacher fetches student
        Then: Response should contain 'student_number': null
        """
        # Arrange
        classroom = Classroom(
            name="測試班級4",
            teacher_id=demo_teacher.id,
            level="A1",
            is_active=True,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        demo_student.student_number = None
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
            is_active=True,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        response = test_client.get(
            f"/api/teachers/students/{demo_student.id}",
            headers=headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "student_number" in data
        assert "student_id" not in data
        assert data["student_number"] is None
