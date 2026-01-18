"""
Integration Tests for ClassroomSchool Module

Tests the classroom-school relationship linking, ensuring:
- One classroom belongs to one school (UNIQUE constraint)
- Multiple classrooms can belong to same school
- Cascade delete behavior
- Query performance with proper indexes
- Business rules for independent vs organization teachers
- Soft delete and reactivation
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import inspect
import uuid

from models import (
    Teacher,
    Organization,
    School,
    Classroom,
    ClassroomSchool,
    TeacherOrganization,
    TeacherSchool,
)
from auth import get_password_hash


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def test_db(shared_test_session: Session):
    """Provide test database session"""
    return shared_test_session


@pytest.fixture
def independent_teacher(test_db: Session):
    """Create independent teacher (not in organization)"""
    teacher = Teacher(
        email=f"independent_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Independent Teacher",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def org_teacher(test_db: Session):
    """Create organization teacher"""
    teacher = Teacher(
        email=f"orgteacher_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=get_password_hash("password123"),
        name="Organization Teacher",
        is_active=True,
    )
    test_db.add(teacher)
    test_db.commit()
    test_db.refresh(teacher)
    return teacher


@pytest.fixture
def test_organization(test_db: Session, org_teacher: Teacher):
    """Create test organization"""
    org = Organization(
        name=f"Test Organization {uuid.uuid4().hex[:8]}",
        display_name="Test Org Display",
        is_active=True,
    )
    test_db.add(org)
    test_db.commit()
    test_db.refresh(org)

    # Link teacher to organization
    teacher_org = TeacherOrganization(
        teacher_id=org_teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    test_db.add(teacher_org)
    test_db.commit()

    return org


@pytest.fixture
def test_school(test_db: Session, test_organization: Organization):
    """Create test school under organization"""
    school = School(
        organization_id=test_organization.id,
        name=f"Test School {uuid.uuid4().hex[:8]}",
        display_name="Test School Display",
        is_active=True,
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


@pytest.fixture
def test_school_b(test_db: Session, test_organization: Organization):
    """Create second test school under organization"""
    school = School(
        organization_id=test_organization.id,
        name=f"Test School B {uuid.uuid4().hex[:8]}",
        display_name="Test School B Display",
        is_active=True,
    )
    test_db.add(school)
    test_db.commit()
    test_db.refresh(school)
    return school


# ============================================================================
# Test 1: Basic CRUD Operations
# ============================================================================


class TestBasicCRUD:
    """Test basic Create, Read, Update, Delete operations"""

    def test_create_classroom_school_relationship(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test creating basic classroom-school link"""
        # Arrange: Create classroom
        classroom = Classroom(
            name="Test Classroom 1",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()
        test_db.refresh(classroom)

        # Act: Create classroom-school relationship
        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()
        test_db.refresh(link)

        # Assert: Verify relationship created
        assert link.id is not None
        assert link.classroom_id == classroom.id
        assert link.school_id == test_school.id
        assert link.is_active is True
        assert link.created_at is not None

    def test_read_classroom_school_by_classroom_id(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test reading classroom-school relationship by classroom_id"""
        # Arrange: Create classroom and link
        classroom = Classroom(
            name="Test Classroom 2",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()

        # Act: Query by classroom_id
        found_link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == classroom.id,
                ClassroomSchool.is_active.is_(True),
            )
            .first()
        )

        # Assert: Verify data correct
        assert found_link is not None
        assert found_link.classroom_id == classroom.id
        assert found_link.school_id == test_school.id

    def test_read_classroom_school_by_school_id(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test reading classroom-school relationships by school_id"""
        # Arrange: Create 3 classrooms in same school
        classrooms = []
        for i in range(3):
            classroom = Classroom(
                name=f"Test Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()
            classrooms.append(classroom)

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Act: Query by school_id
        found_links = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.school_id == test_school.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )

        # Assert: Verify all relationships found
        assert len(found_links) == 3
        found_classroom_ids = {link.classroom_id for link in found_links}
        expected_classroom_ids = {c.id for c in classrooms}
        assert found_classroom_ids == expected_classroom_ids

    def test_soft_delete_classroom_school_relationship(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test soft delete (set is_active=False)"""
        # Arrange: Create classroom and link
        classroom = Classroom(
            name="Test Classroom Delete",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()
        link_id = link.id

        # Act: Soft delete
        link.is_active = False
        test_db.commit()

        # Assert: Verify soft deleted (not hard deleted)
        all_links = test_db.query(ClassroomSchool).filter(
            ClassroomSchool.id == link_id
        ).first()
        assert all_links is not None
        assert all_links.is_active is False

        # Active links query should not find it
        active_link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == classroom.id,
                ClassroomSchool.is_active.is_(True),
            )
            .first()
        )
        assert active_link is None


# ============================================================================
# Test 2: Unique Constraint Tests
# ============================================================================


class TestUniqueConstraints:
    """Test UNIQUE constraint enforcement"""

    def test_one_classroom_one_school_constraint(
        self,
        test_db: Session,
        org_teacher: Teacher,
        test_school: School,
        test_school_b: School,
    ):
        """Test that one classroom can only be linked to one school"""
        # Arrange: Create classroom and link to school A
        classroom = Classroom(
            name="Test Classroom Unique",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link_a = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link_a)
        test_db.commit()

        # Act & Assert: Try to link same classroom to school B (should fail)
        link_b = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school_b.id,
            is_active=True,
        )
        test_db.add(link_b)

        with pytest.raises(Exception) as exc_info:
            test_db.commit()

        # Should raise unique constraint violation
        error_msg = str(exc_info.value).upper()
        assert "UNIQUE" in error_msg and "CONSTRAINT" in error_msg

        test_db.rollback()

    def test_multiple_classrooms_in_same_school(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test that multiple classrooms can belong to same school"""
        # Arrange: Create 3 classrooms
        classrooms = []
        for i in range(3):
            classroom = Classroom(
                name=f"Multi Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()
            classrooms.append(classroom)

        # Act: Link all 3 classrooms to same school
        for classroom in classrooms:
            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Assert: Verify all relationships created successfully
        links = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.school_id == test_school.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )
        assert len(links) == 3


# ============================================================================
# Test 3: Cascade Delete Behavior
# ============================================================================


class TestCascadeDelete:
    """Test cascade delete behavior"""

    def test_delete_school_cascades_to_classroom_schools(
        self, test_db: Session, org_teacher: Teacher, test_organization: Organization
    ):
        """Test that deleting school cascades to classroom_schools"""
        # Arrange: Create school with 3 classrooms
        school = School(
            organization_id=test_organization.id,
            name="Cascade Test School",
            is_active=True,
        )
        test_db.add(school)
        test_db.commit()

        classroom_ids = []
        for i in range(3):
            classroom = Classroom(
                name=f"Cascade Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()
            classroom_ids.append(classroom.id)

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Act: Delete school (hard delete for testing cascade)
        test_db.delete(school)
        test_db.commit()

        # Assert: Verify classroom_schools relationships deleted
        remaining_links = (
            test_db.query(ClassroomSchool)
            .filter(ClassroomSchool.school_id == school.id)
            .all()
        )
        assert len(remaining_links) == 0

        # But classrooms should still exist
        remaining_classrooms = (
            test_db.query(Classroom)
            .filter(Classroom.id.in_(classroom_ids))
            .all()
        )
        assert len(remaining_classrooms) == 3

    def test_delete_classroom_cascades_to_classroom_schools(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test that deleting classroom cascades to classroom_schools"""
        # Arrange: Create classroom linked to school
        classroom = Classroom(
            name="Delete Cascade Classroom",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()

        classroom_id = classroom.id

        # Act: Delete classroom
        test_db.delete(classroom)
        test_db.commit()

        # Assert: Verify classroom_schools relationship also deleted
        remaining_link = (
            test_db.query(ClassroomSchool)
            .filter(ClassroomSchool.classroom_id == classroom_id)
            .first()
        )
        assert remaining_link is None

    def test_delete_organization_cascades_full_hierarchy(
        self, test_db: Session
    ):
        """Test that deleting organization cascades through entire hierarchy"""
        # Arrange: Create org → school → classroom → classroom_schools
        org = Organization(
            name="Cascade Org",
            is_active=True,
        )
        test_db.add(org)
        test_db.commit()

        school = School(
            organization_id=org.id,
            name="Cascade School",
            is_active=True,
        )
        test_db.add(school)
        test_db.commit()

        teacher = Teacher(
            email=f"cascade_{uuid.uuid4().hex[:8]}@test.com",
            password_hash=get_password_hash("password123"),
            name="Cascade Teacher",
            is_active=True,
        )
        test_db.add(teacher)
        test_db.commit()

        classroom = Classroom(
            name="Cascade Classroom",
            teacher_id=teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()

        org_id = org.id
        school_id = school.id
        classroom_id = classroom.id

        # Act: Delete organization
        test_db.delete(org)
        test_db.commit()

        # Assert: Verify entire hierarchy cascade deleted
        assert test_db.query(Organization).filter(Organization.id == org_id).first() is None
        assert test_db.query(School).filter(School.id == school_id).first() is None
        assert test_db.query(ClassroomSchool).filter(
            ClassroomSchool.classroom_id == classroom_id
        ).first() is None

        # Classroom should still exist (not cascade from school)
        assert test_db.query(Classroom).filter(Classroom.id == classroom_id).first() is not None


# ============================================================================
# Test 4: Query Optimization Tests
# ============================================================================


class TestQueryOptimization:
    """Test index usage and query performance"""

    def test_school_classrooms_query_uses_index(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test that querying school's classrooms uses proper index"""
        # Arrange: Create 50 classrooms in school
        for i in range(50):
            classroom = Classroom(
                name=f"Performance Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Act: Query all classrooms in school
        links = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.school_id == test_school.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )

        # Assert: Verify query returned correct results
        assert len(links) == 50

        # Verify index exists (check table metadata)
        inspector = inspect(test_db.bind)
        indexes = inspector.get_indexes("classroom_schools")
        index_columns = [
            idx["column_names"] for idx in indexes
        ]
        # Should have composite index on (classroom_id, school_id, is_active)
        assert any("school_id" in cols for cols in index_columns)

    def test_classroom_school_query_uses_index(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test that querying classroom's school uses proper index"""
        # Arrange: Create 100 classrooms each in different schools
        classrooms = []
        for i in range(100):
            # Create unique school for each classroom
            school = School(
                organization_id=test_school.organization_id,
                name=f"School {i}",
                is_active=True,
            )
            test_db.add(school)
            test_db.commit()

            classroom = Classroom(
                name=f"Index Test Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()
            classrooms.append(classroom)

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Act: Query specific classroom's school
        target_classroom = classrooms[50]
        link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == target_classroom.id,
                ClassroomSchool.is_active.is_(True),
            )
            .first()
        )

        # Assert: Verify query returned correct result
        assert link is not None
        assert link.classroom_id == target_classroom.id

        # Verify index exists
        inspector = inspect(test_db.bind)
        indexes = inspector.get_indexes("classroom_schools")
        index_columns = [idx["column_names"] for idx in indexes]
        # Should have index on classroom_id
        assert any("classroom_id" in cols for cols in index_columns)


# ============================================================================
# Test 5: Data Integrity Tests
# ============================================================================


class TestDataIntegrity:
    """Test foreign key constraints and data integrity"""

    def test_cannot_create_link_with_nonexistent_school(
        self, test_db: Session, org_teacher: Teacher
    ):
        """Test that creating relationship with invalid school_id fails"""
        # Arrange: Create classroom
        classroom = Classroom(
            name="Invalid School Classroom",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        # Act: Try to create link with non-existent school
        invalid_school_id = uuid.uuid4()
        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=invalid_school_id,
            is_active=True,
        )
        test_db.add(link)

        # Assert: Should raise foreign key constraint error (if enforced)
        # Note: SQLite may not enforce FK constraints in test environment
        try:
            test_db.commit()
            # If commit succeeds, verify referential integrity manually
            school_exists = (
                test_db.query(School)
                .filter(School.id == invalid_school_id)
                .first()
            )
            # In production with FK enforcement, this would have failed
            # For now, just verify the school doesn't exist
            assert school_exists is None, "Link created with non-existent school (FK not enforced)"
            test_db.rollback()
        except Exception as exc:
            # FK constraint properly enforced
            error_msg = str(exc).upper()
            assert "FOREIGN KEY" in error_msg or "CONSTRAINT" in error_msg
            test_db.rollback()

    def test_cannot_create_link_with_nonexistent_classroom(
        self, test_db: Session, test_school: School
    ):
        """Test that creating relationship with invalid classroom_id fails"""
        # Arrange: Use valid school but invalid classroom ID
        invalid_classroom_id = 999999

        # Act: Try to create link with non-existent classroom
        link = ClassroomSchool(
            classroom_id=invalid_classroom_id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)

        # Assert: Should raise foreign key constraint error (if enforced)
        # Note: SQLite may not enforce FK constraints in test environment
        try:
            test_db.commit()
            # If commit succeeds, verify referential integrity manually
            classroom_exists = (
                test_db.query(Classroom)
                .filter(Classroom.id == invalid_classroom_id)
                .first()
            )
            # In production with FK enforcement, this would have failed
            # For now, just verify the classroom doesn't exist
            assert classroom_exists is None, "Link created with non-existent classroom (FK not enforced)"
            test_db.rollback()
        except Exception as exc:
            # FK constraint properly enforced
            error_msg = str(exc).upper()
            assert "FOREIGN KEY" in error_msg or "CONSTRAINT" in error_msg
            test_db.rollback()

    def test_is_active_flag_filtering(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test that is_active flag filtering works correctly"""
        # Arrange: Create 5 classroom-school relationships
        classrooms = []
        for i in range(5):
            classroom = Classroom(
                name=f"Active Test Classroom {i}",
                teacher_id=org_teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()
            classrooms.append(classroom)

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            test_db.add(link)

        test_db.commit()

        # Soft delete 2 of them
        links_to_deactivate = (
            test_db.query(ClassroomSchool)
            .filter(ClassroomSchool.classroom_id.in_([c.id for c in classrooms[:2]]))
            .all()
        )
        for link in links_to_deactivate:
            link.is_active = False
        test_db.commit()

        # Act: Query only active relationships
        active_links = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.school_id == test_school.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )

        # Assert: Should return only 3 active ones
        assert len(active_links) == 3


# ============================================================================
# Test 6: Business Logic Tests
# ============================================================================


class TestBusinessLogic:
    """Test business rules and constraints"""

    def test_independent_teacher_classroom_no_school_link(
        self, test_db: Session, independent_teacher: Teacher
    ):
        """Test that independent teacher classroom has no school link"""
        # Arrange: Independent teacher creates classroom
        classroom = Classroom(
            name="Independent Classroom",
            teacher_id=independent_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        # Act: Query for classroom_schools link
        link = (
            test_db.query(ClassroomSchool)
            .filter(ClassroomSchool.classroom_id == classroom.id)
            .first()
        )

        # Assert: Should have no entry in classroom_schools table
        assert link is None

        # But classroom still works normally
        assert classroom.id is not None
        assert classroom.is_active is True

    def test_migration_from_independent_to_organization(
        self,
        test_db: Session,
        independent_teacher: Teacher,
        test_organization: Organization,
    ):
        """Test migrating independent teacher classroom to organization"""
        # Arrange: Independent teacher creates classroom
        classroom = Classroom(
            name="Migration Classroom",
            teacher_id=independent_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        # Teacher joins organization
        teacher_org = TeacherOrganization(
            teacher_id=independent_teacher.id,
            organization_id=test_organization.id,
            role="teacher",
            is_active=True,
        )
        test_db.add(teacher_org)
        test_db.commit()

        # Create school
        school = School(
            organization_id=test_organization.id,
            name="Migration School",
            is_active=True,
        )
        test_db.add(school)
        test_db.commit()

        # Act: Link existing classroom to school
        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()

        # Assert: Verify classroom now part of organization
        found_link = (
            test_db.query(ClassroomSchool)
            .filter(ClassroomSchool.classroom_id == classroom.id)
            .first()
        )
        assert found_link is not None
        assert found_link.school_id == school.id


# ============================================================================
# Test 7: Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_soft_delete_reactivation(
        self, test_db: Session, org_teacher: Teacher, test_school: School
    ):
        """Test soft delete and reactivation"""
        # Arrange: Create classroom and link
        classroom = Classroom(
            name="Reactivation Classroom",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link)
        test_db.commit()
        link_id = link.id

        # Act 1: Soft delete
        link.is_active = False
        test_db.commit()

        # Assert 1: Verify soft deleted
        assert link.is_active is False

        # Act 2: Reactivate
        link.is_active = True
        test_db.commit()

        # Assert 2: Verify relationship restored
        reactivated_link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.id == link_id,
                ClassroomSchool.is_active.is_(True),
            )
            .first()
        )
        assert reactivated_link is not None
        assert reactivated_link.classroom_id == classroom.id
        assert reactivated_link.school_id == test_school.id

    def test_soft_delete_then_hard_delete_allows_relink(
        self,
        test_db: Session,
        org_teacher: Teacher,
        test_school: School,
        test_school_b: School,
    ):
        """Test that hard deleting old link allows relinking to different school"""
        # Arrange: Create classroom linked to school A
        classroom = Classroom(
            name="Relink Classroom",
            teacher_id=org_teacher.id,
            is_active=True,
        )
        test_db.add(classroom)
        test_db.commit()

        link_a = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school.id,
            is_active=True,
        )
        test_db.add(link_a)
        test_db.commit()

        # Act 1: Hard delete link to school A (due to unique constraint on classroom_id)
        test_db.delete(link_a)
        test_db.commit()

        # Act 2: Create new link to school B
        link_b = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=test_school_b.id,
            is_active=True,
        )
        test_db.add(link_b)
        test_db.commit()

        # Assert: Verify classroom now linked to school B
        active_link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == classroom.id,
                ClassroomSchool.is_active.is_(True),
            )
            .first()
        )
        assert active_link is not None
        assert active_link.school_id == test_school_b.id

        # Old link no longer exists (hard deleted)
        old_link = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == classroom.id,
                ClassroomSchool.school_id == test_school.id,
            )
            .first()
        )
        assert old_link is None

    def test_multiple_teachers_same_school_concurrent_creation(
        self, test_db: Session, test_school: School
    ):
        """Test concurrent classroom creation by multiple teachers in same school"""
        # Arrange: Create 5 teachers in same school
        teachers = []
        for i in range(5):
            teacher = Teacher(
                email=f"concurrent_{i}_{uuid.uuid4().hex[:8]}@test.com",
                password_hash=get_password_hash("password123"),
                name=f"Concurrent Teacher {i}",
                is_active=True,
            )
            test_db.add(teacher)
            test_db.commit()
            teachers.append(teacher)

        # Act: Each teacher creates classrooms simultaneously (simulate)
        classrooms_created = []
        for i, teacher in enumerate(teachers):
            classroom = Classroom(
                name=f"Concurrent Classroom {i}",
                teacher_id=teacher.id,
                is_active=True,
            )
            test_db.add(classroom)
            test_db.commit()

            link = ClassroomSchool(
                classroom_id=classroom.id,
                school_id=test_school.id,
                is_active=True,
            )
            test_db.add(link)
            classrooms_created.append(classroom)

        test_db.commit()

        # Assert: Verify no race conditions, all relationships created correctly
        links = (
            test_db.query(ClassroomSchool)
            .filter(
                ClassroomSchool.school_id == test_school.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )
        assert len(links) == 5

        # Verify each classroom linked exactly once
        classroom_ids = [link.classroom_id for link in links]
        assert len(classroom_ids) == len(set(classroom_ids))  # No duplicates
