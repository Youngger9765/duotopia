"""
Integration tests for School Programs API

Tests for /api/schools/{school_id}/programs endpoints
"""

import pytest
from fastapi import status
from sqlalchemy.orm import Session
import uuid

from models import Teacher, School, TeacherSchool, Program, Organization
from auth import create_access_token


@pytest.fixture
def test_organization(shared_test_session: Session):
    """Create a test organization"""
    org = Organization(
        id=uuid.uuid4(),
        name="Test Org",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)
    return org


@pytest.fixture
def school_admin(shared_test_session: Session):
    """Create a school admin teacher"""
    teacher = Teacher(
        email="school_admin@test.com",
        password_hash="hashed",
        name="School Admin",
        is_active=True,
        email_verified=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def test_school(shared_test_session: Session, test_organization: Organization):
    """Create a test school"""
    school = School(
        id=uuid.uuid4(),
        name="Test School",
        organization_id=test_organization.id,
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    return school


@pytest.fixture
def school_membership(
    shared_test_session: Session, school_admin: Teacher, test_school: School
):
    """Create school membership for admin"""
    membership = TeacherSchool(
        teacher_id=school_admin.id,
        school_id=test_school.id,
        roles=["school_admin"],
        is_active=True,
    )
    shared_test_session.add(membership)
    shared_test_session.commit()
    return membership


@pytest.fixture
def auth_headers(school_admin: Teacher):
    """Create auth headers for school admin"""
    token = create_access_token(data={"sub": str(school_admin.id), "type": "teacher"})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestSchoolProgramsAPI:
    """Test school programs CRUD operations"""

    def test_create_school_program(
        self,
        test_client,
        test_school,
        school_membership,
        auth_headers,
        shared_test_session,
    ):
        """Test creating a school program"""
        response = test_client.post(
            f"/api/schools/{test_school.id}/programs",
            json={"name": "Test Program", "description": "Test description"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Program"
        assert data["is_template"] is True
        assert data["school_id"] == str(test_school.id)

    def test_list_school_programs(
        self,
        test_client,
        test_school,
        school_admin,
        school_membership,
        auth_headers,
        shared_test_session,
    ):
        """Test listing school programs"""
        # Create a program first
        program = Program(
            name="List Test Program",
            is_template=True,
            teacher_id=school_admin.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(program)
        shared_test_session.commit()

        response = test_client.get(
            f"/api/schools/{test_school.id}/programs",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_school_program_detail(
        self,
        test_client,
        test_school,
        school_admin,
        school_membership,
        auth_headers,
        shared_test_session,
    ):
        """Test getting school program details"""
        program = Program(
            name="Detail Test Program",
            is_template=True,
            teacher_id=school_admin.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(program)
        shared_test_session.commit()
        shared_test_session.refresh(program)

        response = test_client.get(
            f"/api/schools/{test_school.id}/programs/{program.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Detail Test Program"

    def test_update_school_program(
        self,
        test_client,
        test_school,
        school_admin,
        school_membership,
        auth_headers,
        shared_test_session,
    ):
        """Test updating school program"""
        program = Program(
            name="Update Test Program",
            is_template=True,
            teacher_id=school_admin.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(program)
        shared_test_session.commit()
        shared_test_session.refresh(program)

        response = test_client.put(
            f"/api/schools/{test_school.id}/programs/{program.id}",
            json={"name": "Updated Program Name"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Program Name"

    def test_delete_school_program(
        self,
        test_client,
        test_school,
        school_admin,
        school_membership,
        auth_headers,
        shared_test_session,
    ):
        """Test soft deleting school program"""
        program = Program(
            name="Delete Test Program",
            is_template=True,
            teacher_id=school_admin.id,
            school_id=test_school.id,
            is_active=True,
        )
        shared_test_session.add(program)
        shared_test_session.commit()
        shared_test_session.refresh(program)

        response = test_client.delete(
            f"/api/schools/{test_school.id}/programs/{program.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify soft delete
        shared_test_session.refresh(program)
        assert program.is_active is False

    def test_non_member_cannot_access(
        self, test_client, test_school, shared_test_session
    ):
        """Test that non-members cannot access school programs"""
        # Create a different teacher
        other_teacher = Teacher(
            email="other@test.com",
            password_hash="hashed",
            name="Other Teacher",
            is_active=True,
            email_verified=True,
        )
        shared_test_session.add(other_teacher)
        shared_test_session.commit()

        token = create_access_token(
            data={"sub": str(other_teacher.id), "type": "teacher"}
        )
        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.get(
            f"/api/schools/{test_school.id}/programs",
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_regular_teacher_cannot_create(
        self, test_client, test_school, shared_test_session
    ):
        """Test that regular teachers cannot create school programs"""
        # Create a teacher with 'teacher' role (not admin)
        teacher = Teacher(
            email="regular@test.com",
            password_hash="hashed",
            name="Regular Teacher",
            is_active=True,
            email_verified=True,
        )
        shared_test_session.add(teacher)
        shared_test_session.commit()

        membership = TeacherSchool(
            teacher_id=teacher.id,
            school_id=test_school.id,
            roles=["teacher"],  # Not admin
            is_active=True,
        )
        shared_test_session.add(membership)
        shared_test_session.commit()

        token = create_access_token(data={"sub": str(teacher.id), "type": "teacher"})
        headers = {"Authorization": f"Bearer {token}"}

        response = test_client.post(
            f"/api/schools/{test_school.id}/programs",
            json={"name": "Should Fail"},
            headers=headers,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
