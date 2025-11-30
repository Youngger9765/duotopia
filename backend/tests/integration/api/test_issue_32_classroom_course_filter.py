"""
Tests for Issue #32 - 老師指派作業時看到其他班級的非公版課程

Bug: Teachers can see courses from other classrooms when assigning homework.

Expected behavior:
- Teachers should only see:
  1. Public courses (is_template=True)
  2. Their own classroom's courses (classroom_id=X)
- Should NOT see courses from other classrooms

Test scenarios:
1. Get programs for classroom A should return public + classroom A courses
2. Get programs for classroom A should NOT return classroom B courses
3. Public courses should be visible in all classrooms
"""

import pytest
from sqlalchemy.orm import Session
from models import Teacher, Classroom, Program
from auth import get_password_hash


@pytest.fixture
def test_teacher(shared_test_session: Session):
    """Create a test teacher"""
    teacher = Teacher(
        name="Test Teacher",
        email="teacher_issue32@test.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def classroom_a(shared_test_session: Session, test_teacher: Teacher):
    """Create classroom A (五年A班)"""
    classroom = Classroom(
        name="五年A班",
        description="Grade 5 Class A",
        teacher_id=test_teacher.id,
    )
    shared_test_session.add(classroom)
    shared_test_session.commit()
    shared_test_session.refresh(classroom)
    return classroom


@pytest.fixture
def classroom_b(shared_test_session: Session, test_teacher: Teacher):
    """Create classroom B (六年A班)"""
    classroom = Classroom(
        name="六年A班",
        description="Grade 6 Class A",
        teacher_id=test_teacher.id,
    )
    shared_test_session.add(classroom)
    shared_test_session.commit()
    shared_test_session.refresh(classroom)
    return classroom


@pytest.fixture
def public_course(shared_test_session: Session, test_teacher: Teacher):
    """Create a public template course (visible to all classrooms)"""
    program = Program(
        name="公版課程 - 基礎英文",
        description="Public template course for all classrooms",
        teacher_id=test_teacher.id,
        is_template=True,  # Public course
        classroom_id=None,  # No classroom association
        is_active=True,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)
    return program


@pytest.fixture
def classroom_a_course(
    shared_test_session: Session, test_teacher: Teacher, classroom_a: Classroom
):
    """Create a course specific to classroom A"""
    program = Program(
        name="五年A班專屬課程",
        description="Course specific to Grade 5 Class A",
        teacher_id=test_teacher.id,
        is_template=False,  # NOT a public course
        classroom_id=classroom_a.id,  # Only for classroom A
        is_active=True,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)
    return program


@pytest.fixture
def classroom_b_course(
    shared_test_session: Session, test_teacher: Teacher, classroom_b: Classroom
):
    """Create a course specific to classroom B"""
    program = Program(
        name="六年A班專屬課程",
        description="Course specific to Grade 6 Class A",
        teacher_id=test_teacher.id,
        is_template=False,  # NOT a public course
        classroom_id=classroom_b.id,  # Only for classroom B
        is_active=True,
    )
    shared_test_session.add(program)
    shared_test_session.commit()
    shared_test_session.refresh(program)
    return program


@pytest.fixture
def auth_headers(test_client, test_teacher: Teacher):
    """Get authentication headers for the test teacher"""
    response = test_client.post(
        "/api/auth/teacher/login",
        json={
            "email": test_teacher.email,
            "password": "password123",
        },
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestClassroomCourseFilter:
    """Test course filtering for classroom-specific assignments"""

    def test_classroom_a_sees_public_and_own_courses(
        self,
        test_client,
        classroom_a: Classroom,
        classroom_b: Classroom,
        public_course: Program,
        classroom_a_course: Program,
        classroom_b_course: Program,
        auth_headers: dict,
    ):
        """Test that classroom A sees public courses + classroom A courses ONLY"""
        response = test_client.get(
            f"/api/teachers/programs?classroom_id={classroom_a.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        programs = response.json()

        # Extract program IDs
        program_ids = [p["id"] for p in programs]

        # Should see public course
        assert public_course.id in program_ids, "應該看到公版課程"

        # Should see classroom A's course
        assert classroom_a_course.id in program_ids, "應該看到五年A班專屬課程"

        # Should NOT see classroom B's course (這是重點！)
        assert classroom_b_course.id not in program_ids, "不應該看到六年A班專屬課程（Bug重現）"

    def test_classroom_b_sees_public_and_own_courses(
        self,
        test_client,
        classroom_a: Classroom,
        classroom_b: Classroom,
        public_course: Program,
        classroom_a_course: Program,
        classroom_b_course: Program,
        auth_headers: dict,
    ):
        """Test that classroom B sees public courses + classroom B courses ONLY"""
        response = test_client.get(
            f"/api/teachers/programs?classroom_id={classroom_b.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        programs = response.json()

        # Extract program IDs
        program_ids = [p["id"] for p in programs]

        # Should see public course
        assert public_course.id in program_ids, "應該看到公版課程"

        # Should see classroom B's course
        assert classroom_b_course.id in program_ids, "應該看到六年A班專屬課程"

        # Should NOT see classroom A's course
        assert classroom_a_course.id not in program_ids, "不應該看到五年A班專屬課程"

    def test_public_course_visible_in_all_classrooms(
        self,
        test_client,
        classroom_a: Classroom,
        classroom_b: Classroom,
        public_course: Program,
        auth_headers: dict,
    ):
        """Test that public courses are visible in all classrooms"""
        # Check classroom A
        response_a = test_client.get(
            f"/api/teachers/programs?classroom_id={classroom_a.id}",
            headers=auth_headers,
        )
        programs_a = response_a.json()
        program_ids_a = [p["id"] for p in programs_a]
        assert public_course.id in program_ids_a, "公版課程應在五年A班可見"

        # Check classroom B
        response_b = test_client.get(
            f"/api/teachers/programs?classroom_id={classroom_b.id}",
            headers=auth_headers,
        )
        programs_b = response_b.json()
        program_ids_b = [p["id"] for p in programs_b]
        assert public_course.id in program_ids_b, "公版課程應在六年A班可見"

    def test_without_classroom_filter_shows_all(
        self,
        test_client,
        public_course: Program,
        classroom_a_course: Program,
        classroom_b_course: Program,
        auth_headers: dict,
    ):
        """Test that without classroom_id filter, all teacher's courses are shown"""
        response = test_client.get(
            "/api/teachers/programs",  # No classroom_id parameter
            headers=auth_headers,
        )

        assert response.status_code == 200
        programs = response.json()
        program_ids = [p["id"] for p in programs]

        # Should see ALL courses
        assert public_course.id in program_ids
        assert classroom_a_course.id in program_ids
        assert classroom_b_course.id in program_ids

    def test_empty_classroom_shows_only_public_courses(
        self,
        shared_test_session: Session,
        test_client,
        test_teacher: Teacher,
        public_course: Program,
        classroom_a_course: Program,
        auth_headers: dict,
    ):
        """Test that an empty classroom only sees public courses"""
        # Create a new classroom with no specific courses
        empty_classroom = Classroom(
            name="空教室",
            description="Classroom with no specific courses",
            teacher_id=test_teacher.id,
        )
        shared_test_session.add(empty_classroom)
        shared_test_session.commit()
        shared_test_session.refresh(empty_classroom)

        response = test_client.get(
            f"/api/teachers/programs?classroom_id={empty_classroom.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        programs = response.json()
        program_ids = [p["id"] for p in programs]

        # Should only see public course
        assert public_course.id in program_ids, "應該看到公版課程"

        # Should NOT see classroom A's course
        assert classroom_a_course.id not in program_ids, "不應該看到其他班級專屬課程"

    def test_teacher_cannot_access_other_teacher_classroom(
        self,
        shared_test_session: Session,
        test_client,
        test_teacher: Teacher,
        classroom_a: Classroom,
        classroom_b: Classroom,
        classroom_a_course: Program,
        auth_headers: dict,
    ):
        """Test that teachers cannot access other teachers' classrooms

        Scenario:
        - test_teacher owns classroom_a with classroom_a_course
        - Create another_teacher who owns classroom_b
        - test_teacher requests programs with classroom_b.id
        - Should NOT see classroom_a_course (belongs to test_teacher)
        - Should only see public courses
        """
        # Create another teacher
        another_teacher = Teacher(
            name="Another Teacher",
            email="another_teacher@test.com",
            password_hash=get_password_hash("password456"),
            is_active=True,
            email_verified=True,
        )
        shared_test_session.add(another_teacher)
        shared_test_session.commit()

        # Transfer classroom_b ownership to another_teacher
        classroom_b.teacher_id = another_teacher.id
        shared_test_session.commit()

        # test_teacher tries to query with classroom_b's id
        response = test_client.get(
            f"/api/teachers/programs?classroom_id={classroom_b.id}",
            headers=auth_headers,  # test_teacher's token
        )

        assert response.status_code == 200
        programs = response.json()

        # Should not see classroom_a_course (belongs to classroom_a)
        program_ids = [p["id"] for p in programs]
        assert (
            classroom_a_course.id not in program_ids
        ), "Should not see other teacher's classroom-specific courses"

        # All returned programs should be either:
        # 1. Public (is_template=True), or
        # 2. Owned by test_teacher (not another_teacher)
        for program in programs:
            if not program.get("is_template"):
                # Non-public program should belong to test_teacher
                assert program.get("classroom_id") in [
                    classroom_a.id,
                    None,
                ], f"Non-public program {program['id']} should not belong to another teacher"
