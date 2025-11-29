"""
Integration tests for Issue #31 - Student Number Storage and Uniqueness Validation

Test Requirements:
1. Student number should be successfully stored when updating student data
2. Same classroom should not allow duplicate student numbers
3. Different classrooms can use the same student number
4. Empty student number should be allowed (optional field)
"""

import pytest
from fastapi import status
from datetime import date


@pytest.mark.integration
class TestStudentNumberStorage:
    """Test student number storage functionality"""

    def test_update_student_with_student_number_should_save(
        self, test_client, demo_teacher, demo_student, test_db_session
    ):
        """
        Test Case 1: Update student with student_number should save successfully

        Given: A student in a classroom
        When: Teacher updates student with student_number "A001"
        Then: Student number should be stored in database
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange - Create classroom and assign student
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        # Create auth headers
        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        update_data = {
            "name": demo_student.name,
            "student_number": "A001",
        }

        # Act
        response = test_client.put(
            f"/api/teachers/students/{demo_student.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["student_number"] == "A001"

        # Verify in database
        get_response = test_client.get(
            f"/api/teachers/classrooms/{classroom.id}/students",
            headers=auth_headers,
        )
        students = get_response.json()
        updated_student = next(s for s in students if s["id"] == demo_student.id)
        assert updated_student["student_number"] == "A001"


@pytest.mark.integration
class TestStudentNumberUniqueness:
    """Test student number uniqueness validation"""

    def test_duplicate_student_number_in_same_classroom_should_fail(
        self, test_client, demo_teacher, test_db_session
    ):
        """
        Test Case 2: Duplicate student number in same classroom should fail

        Given: Classroom has student with student_number "A001"
        When: Another student in same classroom tries to use "A001"
        Then: Should return 400 error with message
        """
        from models import Student, ClassroomStudent, Classroom
        from auth import get_password_hash, create_access_token

        # Create classroom
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        # Create auth headers
        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Arrange - Create first student with A001
        student1 = Student(
            name="Student 1",
            email="student1@test.com",
            password_hash=get_password_hash("20100101"),
            birthdate=date(2010, 1, 1),
            student_number="A001",
        )
        test_db_session.add(student1)
        test_db_session.commit()
        test_db_session.refresh(student1)

        # Assign to classroom
        enrollment1 = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student1.id,
        )
        test_db_session.add(enrollment1)
        test_db_session.commit()

        # Create second student
        student2 = Student(
            name="Student 2",
            email="student2@test.com",
            password_hash=get_password_hash("20100202"),
            birthdate=date(2010, 2, 2),
        )
        test_db_session.add(student2)
        test_db_session.commit()
        test_db_session.refresh(student2)

        # Assign to same classroom
        enrollment2 = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=student2.id,
        )
        test_db_session.add(enrollment2)
        test_db_session.commit()

        # Act - Try to update student2 with same student_number
        update_data = {
            "name": "Student 2",
            "student_number": "A001",  # Same as student1
        }
        response = test_client.put(
            f"/api/teachers/students/{student2.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Updated error message should NOT expose student number
        assert "在班級中已存在" in response.json()["detail"]
        # Error message should NOT contain the actual student number
        assert "A001" not in response.json()["detail"]

    def test_same_student_number_in_different_classrooms_should_succeed(
        self, test_client, demo_teacher, test_db_session
    ):
        """
        Test Case 3: Same student number in different classrooms should succeed

        Given: Student in Classroom A has student_number "A001"
        When: Student in Classroom B uses "A001"
        Then: Should succeed (different classrooms)
        """
        from models import Classroom, Student, ClassroomStudent
        from auth import get_password_hash, create_access_token

        # Create auth headers
        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Arrange - Create two classrooms
        classroom_a = Classroom(
            name="Classroom A",
            teacher_id=demo_teacher.id,
        )
        classroom_b = Classroom(
            name="Classroom B",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add_all([classroom_a, classroom_b])
        test_db_session.commit()

        # Create student in Classroom A with A001
        student_a = Student(
            name="Student A",
            email="student_a@test.com",
            password_hash=get_password_hash("20100101"),
            birthdate=date(2010, 1, 1),
            student_number="A001",
        )
        test_db_session.add(student_a)
        test_db_session.commit()

        enrollment_a = ClassroomStudent(
            classroom_id=classroom_a.id,
            student_id=student_a.id,
        )
        test_db_session.add(enrollment_a)
        test_db_session.commit()

        # Create student in Classroom B
        student_b = Student(
            name="Student B",
            email="student_b@test.com",
            password_hash=get_password_hash("20100202"),
            birthdate=date(2010, 2, 2),
        )
        test_db_session.add(student_b)
        test_db_session.commit()

        enrollment_b = ClassroomStudent(
            classroom_id=classroom_b.id,
            student_id=student_b.id,
        )
        test_db_session.add(enrollment_b)
        test_db_session.commit()

        # Act - Update student_b with same student_number (but different classroom)
        update_data = {
            "name": "Student B",
            "student_number": "A001",  # Same as student_a, but different classroom
        }
        response = test_client.put(
            f"/api/teachers/students/{student_b.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert - Should succeed
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["student_number"] == "A001"

    def test_empty_student_number_should_be_allowed(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Test Case 4: Empty student number should be allowed (optional field)

        Given: A student
        When: Update with empty student_number
        Then: Should succeed
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange - Create classroom and assign student
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        # Create auth headers
        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        update_data = {
            "name": demo_student.name,
            "student_number": "",  # Empty
        }
        response = test_client.put(
            f"/api/teachers/students/{demo_student.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        # Note: Empty string should be converted to None in database


@pytest.mark.integration
class TestStudentNumberValidation:
    """Test student number validation (Code Review Issue #31 fixes)"""

    def test_student_number_with_special_characters_should_fail(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Boundary Test 1: Student number with special characters should fail

        Given: A student
        When: Update with student_number containing special chars
        Then: Should return 422 validation error
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange - Create classroom and assign student
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        # Create auth headers
        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act - Test various special characters
        invalid_student_numbers = [
            "A001; DROP TABLE students--",  # SQL injection attempt
            "A001' OR '1'='1",  # SQL injection attempt
            "A001<script>alert('xss')</script>",  # XSS attempt
            "A001@#$%",  # Special characters
            "A001 空格",  # Contains space (not just whitespace)
            "A001/B002",  # Contains slash
            "A001.B002",  # Contains dot
        ]

        for invalid_number in invalid_student_numbers:
            update_data = {
                "name": demo_student.name,
                "student_number": invalid_number,
            }
            response = test_client.put(
                f"/api/teachers/students/{demo_student.id}",
                json=update_data,
                headers=auth_headers,
            )

            # Assert - Should fail validation
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"Expected validation error for: {repr(invalid_number)}, "
                f"got {response.status_code} with response: {response.json()}"
            )
            assert "學號只能包含字母、數字、連字號和底線" in str(response.json())

    def test_student_number_exceeding_max_length_should_fail(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Boundary Test 2: Student number exceeding 50 characters should fail

        Given: A student
        When: Update with student_number longer than 50 characters
        Then: Should return 422 validation error
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act - 51 characters (exceeds limit)
        update_data = {
            "name": demo_student.name,
            "student_number": "A" * 51,  # 51 characters
        }
        response = test_client.put(
            f"/api/teachers/students/{demo_student.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "長度" in str(response.json()) or "length" in str(response.json()).lower()

    def test_student_number_with_unicode_characters_should_fail(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Boundary Test 3: Student number with Unicode characters should fail

        Given: A student
        When: Update with student_number containing Unicode chars
        Then: Should return 422 validation error
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        unicode_numbers = [
            "A001中文",  # Chinese characters
            "A001日本語",  # Japanese characters
            "A001한국어",  # Korean characters
            "A001Ñ",  # Accented character
            "A001€",  # Currency symbol
            "A001😀",  # Emoji
        ]

        for unicode_number in unicode_numbers:
            update_data = {
                "name": demo_student.name,
                "student_number": unicode_number,
            }
            response = test_client.put(
                f"/api/teachers/students/{demo_student.id}",
                json=update_data,
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, (
                f"Expected validation error for Unicode: {unicode_number}, "
                f"got {response.status_code}"
            )

    def test_student_number_with_whitespace_should_be_trimmed(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Boundary Test 4: Student number with leading/trailing whitespace should be trimmed

        Given: A student
        When: Update with student_number containing whitespace
        Then: Whitespace should be trimmed and saved
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act
        update_data = {
            "name": demo_student.name,
            "student_number": "  A001  ",  # Leading and trailing whitespace
        }
        response = test_client.put(
            f"/api/teachers/students/{demo_student.id}",
            json=update_data,
            headers=auth_headers,
        )

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["student_number"] == "A001"  # Whitespace trimmed

    def test_student_number_valid_characters_should_succeed(
        self, test_client, demo_student, demo_teacher, test_db_session
    ):
        """
        Boundary Test 5: Student number with valid characters should succeed

        Given: A student
        When: Update with student_number using valid chars (alphanumeric, hyphen, underscore)
        Then: Should succeed
        """
        from models import Classroom, ClassroomStudent
        from auth import create_access_token

        # Arrange
        classroom = Classroom(
            name="Test Classroom",
            teacher_id=demo_teacher.id,
        )
        test_db_session.add(classroom)
        test_db_session.commit()

        enrollment = ClassroomStudent(
            classroom_id=classroom.id,
            student_id=demo_student.id,
        )
        test_db_session.add(enrollment)
        test_db_session.commit()

        access_token = create_access_token(
            data={"sub": str(demo_teacher.id), "type": "teacher"}
        )
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # Act - Test valid formats
        valid_student_numbers = [
            "A001",
            "A-001",
            "A_001",
            "123456",
            "ABC-123_XYZ",
            "Student-2024-001",
        ]

        for valid_number in valid_student_numbers:
            update_data = {
                "name": demo_student.name,
                "student_number": valid_number,
            }
            response = test_client.put(
                f"/api/teachers/students/{demo_student.id}",
                json=update_data,
                headers=auth_headers,
            )

            # Assert
            assert response.status_code == status.HTTP_200_OK, (
                f"Expected success for valid number: {valid_number}, "
                f"got {response.status_code}"
            )
            assert response.json()["student_number"] == valid_number
