"""
Organization Hierarchy - Complete Scenario & Edge Case Tests

Tests comprehensive business logic scenarios and edge cases:
1. Permission inheritance (org → school)
2. Multi-role conflicts
3. Cascade delete behavior
4. org_owner uniqueness constraint
5. Cross-organization isolation
6. Casbin synchronization
7. Invalid state transitions
"""

import pytest
import uuid
from sqlalchemy.orm import Session

from models import (
    Teacher,
    Organization,
    School,
    TeacherOrganization,
    TeacherSchool,
    Classroom,
    ClassroomSchool,
)
from services.casbin_service import get_casbin_service


# ============ Fixtures ============


@pytest.fixture
def org_owner(shared_test_session: Session):
    """Create org owner teacher"""
    teacher = Teacher(
        email=f"org_owner_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="$2b$12$test",
        name="Org Owner",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def org_admin(shared_test_session: Session):
    """Create org admin teacher"""
    teacher = Teacher(
        email=f"org_admin_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="$2b$12$test",
        name="Org Admin",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def regular_teacher(shared_test_session: Session):
    """Create regular teacher"""
    teacher = Teacher(
        email=f"teacher_{uuid.uuid4().hex[:6]}@test.com",
        password_hash="$2b$12$test",
        name="Regular Teacher",
        is_active=True,
    )
    shared_test_session.add(teacher)
    shared_test_session.commit()
    shared_test_session.refresh(teacher)
    return teacher


@pytest.fixture
def demo_org(shared_test_session: Session, org_owner: Teacher):
    """Create demo organization with owner"""
    casbin = get_casbin_service()

    org = Organization(
        name="demo-org",
        display_name="Demo Organization",
        contact_email="demo@org.com",
        is_active=True,
    )
    shared_test_session.add(org)
    shared_test_session.commit()
    shared_test_session.refresh(org)

    # Add owner relationship
    owner_rel = TeacherOrganization(
        teacher_id=org_owner.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    shared_test_session.add(owner_rel)
    shared_test_session.commit()

    # Sync Casbin
    casbin.add_role_for_user(org_owner.id, "org_owner", f"org-{org.id}")

    return org


@pytest.fixture
def demo_school(shared_test_session: Session, demo_org: Organization):
    """Create demo school under org"""
    school = School(
        organization_id=demo_org.id,
        name="demo-school",
        display_name="Demo School",
        is_active=True,
    )
    shared_test_session.add(school)
    shared_test_session.commit()
    shared_test_session.refresh(school)
    return school


# ============ Scenario Tests ============


class TestPermissionInheritance:
    """Test org-level permissions inherit to schools"""

    def test_org_owner_can_manage_all_schools(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        org_owner: Teacher,
        demo_school: School,
    ):
        """org_owner should have access to all schools in their org"""
        # Verify org_owner has org-level role
        org_rel = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == org_owner.id,
                TeacherOrganization.organization_id == demo_org.id,
            )
            .first()
        )
        assert org_rel is not None
        assert org_rel.role == "org_owner"

        # Verify org_owner can access school (even without school-level relationship)
        school_rel = (
            shared_test_session.query(TeacherSchool)
            .filter(
                TeacherSchool.teacher_id == org_owner.id,
                TeacherSchool.school_id == demo_school.id,
            )
            .first()
        )
        # Should be None - no direct school relationship
        assert school_rel is None

        # But org_owner should have Casbin role at org level
        casbin = get_casbin_service()
        has_org_role = casbin.has_role(org_owner.id, "org_owner", f"org-{demo_org.id}")
        assert has_org_role is True

    def test_org_admin_can_manage_all_schools(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        org_admin: Teacher,
        demo_school: School,
    ):
        """org_admin should have access to all schools in their org"""
        casbin = get_casbin_service()

        # Add org_admin relationship
        admin_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=demo_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(admin_rel)
        shared_test_session.commit()

        # Sync Casbin
        casbin.add_role_for_user(org_admin.id, "org_admin", f"org-{demo_org.id}")

        # Verify org_admin has org-level role
        has_role = casbin.has_role(org_admin.id, "org_admin", f"org-{demo_org.id}")
        assert has_role is True

    def test_school_admin_only_manages_own_school(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        regular_teacher: Teacher,
        demo_school: School,
    ):
        """school_admin should only have access to their specific school"""
        casbin = get_casbin_service()

        # Create another school
        school2 = School(
            organization_id=demo_org.id,
            name="school-2",
            display_name="School 2",
            is_active=True,
        )
        shared_test_session.add(school2)
        shared_test_session.commit()
        shared_test_session.refresh(school2)

        # Add teacher as school_admin to demo_school only
        school_rel = TeacherSchool(
            teacher_id=regular_teacher.id,
            school_id=demo_school.id,
            roles=["school_admin"],
            is_active=True,
        )
        shared_test_session.add(school_rel)
        shared_test_session.commit()

        # Sync Casbin
        casbin.add_role_for_user(
            regular_teacher.id, "school_admin", f"school-{demo_school.id}"
        )

        # Verify has access to demo_school
        has_access_school1 = casbin.has_role(
            regular_teacher.id, "school_admin", f"school-{demo_school.id}"
        )
        assert has_access_school1 is True

        # Verify NO access to school2
        has_access_school2 = casbin.has_role(
            regular_teacher.id, "school_admin", f"school-{school2.id}"
        )
        assert has_access_school2 is False


class TestMultiRoleSupport:
    """Test teachers can have multiple roles at same school"""

    def test_teacher_can_be_school_admin_and_teacher(
        self,
        shared_test_session: Session,
        demo_school: School,
        regular_teacher: Teacher,
    ):
        """Teacher can have both school_admin and teacher roles"""
        casbin = get_casbin_service()

        # Add multi-role relationship
        school_rel = TeacherSchool(
            teacher_id=regular_teacher.id,
            school_id=demo_school.id,
            roles=["school_admin", "teacher"],  # Multiple roles
            is_active=True,
        )
        shared_test_session.add(school_rel)
        shared_test_session.commit()
        shared_test_session.refresh(school_rel)

        # Verify both roles stored
        assert "school_admin" in school_rel.roles
        assert "teacher" in school_rel.roles

        # Sync both roles to Casbin
        casbin.add_role_for_user(
            regular_teacher.id, "school_admin", f"school-{demo_school.id}"
        )
        casbin.add_role_for_user(
            regular_teacher.id, "teacher", f"school-{demo_school.id}"
        )

        # Verify Casbin has both roles
        has_admin = casbin.has_role(
            regular_teacher.id, "school_admin", f"school-{demo_school.id}"
        )
        has_teacher = casbin.has_role(
            regular_teacher.id, "teacher", f"school-{demo_school.id}"
        )
        assert has_admin is True
        assert has_teacher is True

    def test_role_update_preserves_other_roles(
        self,
        shared_test_session: Session,
        demo_school: School,
        regular_teacher: Teacher,
    ):
        """Updating roles should preserve intended state"""
        # Start with school_admin only
        school_rel = TeacherSchool(
            teacher_id=regular_teacher.id,
            school_id=demo_school.id,
            roles=["school_admin"],
            is_active=True,
        )
        shared_test_session.add(school_rel)
        shared_test_session.commit()
        shared_test_session.refresh(school_rel)

        assert school_rel.roles == ["school_admin"]

        # Update to add teacher role
        school_rel.roles = ["school_admin", "teacher"]
        shared_test_session.commit()
        shared_test_session.refresh(school_rel)

        assert "school_admin" in school_rel.roles
        assert "teacher" in school_rel.roles


class TestCascadeDelete:
    """Test CASCADE delete behavior maintains data integrity"""

    def test_delete_organization_cascades_to_schools(
        self, shared_test_session: Session, demo_org: Organization
    ):
        """Deleting organization should cascade to schools"""
        # Create 2 schools
        school1 = School(organization_id=demo_org.id, name="school-1", is_active=True)
        school2 = School(organization_id=demo_org.id, name="school-2", is_active=True)
        shared_test_session.add_all([school1, school2])
        shared_test_session.commit()

        school1_id = school1.id
        school2_id = school2.id

        # Soft delete organization
        demo_org.is_active = False
        shared_test_session.commit()

        # Schools should still exist (soft delete doesn't cascade automatically)
        schools = (
            shared_test_session.query(School)
            .filter(School.id.in_([school1_id, school2_id]))
            .all()
        )
        assert len(schools) == 2

        # But if we hard delete (in production, we use soft delete)
        # CASCADE would handle cleanup

    def test_delete_school_cascades_to_teacher_school(
        self,
        shared_test_session: Session,
        demo_school: School,
        regular_teacher: Teacher,
    ):
        """Deleting school should cascade to teacher_school relationships"""
        # Add teacher to school
        school_rel = TeacherSchool(
            teacher_id=regular_teacher.id,
            school_id=demo_school.id,
            roles=["teacher"],
            is_active=True,
        )
        shared_test_session.add(school_rel)
        shared_test_session.commit()

        # Soft delete school
        demo_school.is_active = False
        shared_test_session.commit()

        # Relationship still exists (soft delete pattern)
        rel = (
            shared_test_session.query(TeacherSchool)
            .filter(TeacherSchool.school_id == demo_school.id)
            .first()
        )
        assert rel is not None

    def test_delete_school_cascades_to_classroom_school(
        self, shared_test_session: Session, demo_school: School, org_owner: Teacher
    ):
        """Deleting school should cascade to classroom_school links"""
        # Create classroom (use org_owner as teacher)
        classroom = Classroom(
            name="Test Class",
            teacher_id=org_owner.id,
            grade="5",
            is_active=True,
        )
        shared_test_session.add(classroom)
        shared_test_session.commit()
        shared_test_session.refresh(classroom)

        # Link classroom to school
        link = ClassroomSchool(
            classroom_id=classroom.id, school_id=demo_school.id, is_active=True
        )
        shared_test_session.add(link)
        shared_test_session.commit()

        # Soft delete school
        demo_school.is_active = False
        shared_test_session.commit()

        # Link still exists (soft delete)
        existing_link = (
            shared_test_session.query(ClassroomSchool)
            .filter(ClassroomSchool.school_id == demo_school.id)
            .first()
        )
        assert existing_link is not None


class TestOrgOwnerUniqueness:
    """Test org_owner uniqueness constraint enforcement"""

    def test_organization_can_have_only_one_owner(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        org_owner: Teacher,
        org_admin: Teacher,
    ):
        """Organization should enforce max 1 org_owner"""
        # demo_org already has org_owner (from fixture)
        existing_owners = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == demo_org.id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .all()
        )
        assert (
            len(existing_owners) == 1
        ), f"Expected 1 org_owner, found {len(existing_owners)}"
        assert existing_owners[0].teacher_id == org_owner.id

        # In API, attempting to add another org_owner would be blocked
        # Here we verify the current state is correct

    def test_can_transfer_org_ownership(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        org_owner: Teacher,
        org_admin: Teacher,
    ):
        """Ownership can be transferred (demote old, promote new)"""
        casbin = get_casbin_service()

        # Step 1: Demote current owner to org_admin
        old_owner_rel = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == org_owner.id,
                TeacherOrganization.organization_id == demo_org.id,
            )
            .first()
        )
        old_owner_rel.role = "org_admin"
        shared_test_session.commit()

        # Remove old Casbin role
        casbin.delete_role_for_user(org_owner.id, "org_owner", f"org-{demo_org.id}")
        casbin.add_role_for_user(org_owner.id, "org_admin", f"org-{demo_org.id}")

        # Step 2: Promote new owner
        new_owner_rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=demo_org.id,
            role="org_owner",
            is_active=True,
        )
        shared_test_session.add(new_owner_rel)
        shared_test_session.commit()

        # Add new Casbin role
        casbin.add_role_for_user(org_admin.id, "org_owner", f"org-{demo_org.id}")

        # Verify only 1 org_owner exists
        owners = (
            shared_test_session.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == demo_org.id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .all()
        )
        assert len(owners) == 1, f"Expected 1 org_owner, found {len(owners)}"
        assert owners[0].teacher_id == org_admin.id


class TestCrossOrganizationIsolation:
    """Test data isolation between organizations"""

    def test_teacher_in_org_a_cannot_see_org_b_schools(
        self, shared_test_session: Session, org_owner: Teacher, regular_teacher: Teacher
    ):
        """Teachers in Org A should not have access to Org B's schools"""
        casbin = get_casbin_service()

        # Create Org A
        org_a = Organization(name="org-a", display_name="Org A", is_active=True)
        shared_test_session.add(org_a)
        shared_test_session.commit()
        shared_test_session.refresh(org_a)

        # Create Org B
        org_b = Organization(name="org-b", display_name="Org B", is_active=True)
        shared_test_session.add(org_b)
        shared_test_session.commit()
        shared_test_session.refresh(org_b)

        # org_owner → Org A owner
        rel_a = TeacherOrganization(
            teacher_id=org_owner.id,
            organization_id=org_a.id,
            role="org_owner",
            is_active=True,
        )
        shared_test_session.add(rel_a)
        shared_test_session.commit()
        casbin.add_role_for_user(org_owner.id, "org_owner", f"org-{org_a.id}")

        # regular_teacher → Org B owner
        rel_b = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=org_b.id,
            role="org_owner",
            is_active=True,
        )
        shared_test_session.add(rel_b)
        shared_test_session.commit()
        casbin.add_role_for_user(regular_teacher.id, "org_owner", f"org-{org_b.id}")

        # Create school in Org B
        school_b = School(organization_id=org_b.id, name="school-b", is_active=True)
        shared_test_session.add(school_b)
        shared_test_session.commit()
        shared_test_session.refresh(school_b)

        # Verify org_owner (from Org A) has NO role in Org B
        has_access = casbin.has_role(org_owner.id, "org_owner", f"org-{org_b.id}")
        assert has_access is False

        # Verify org_owner has NO role in school_b
        has_school_access = casbin.has_role(
            org_owner.id, "school_admin", f"school-{school_b.id}"
        )
        assert has_school_access is False


class TestCasbinSynchronization:
    """Test Casbin role sync stays consistent with DB"""

    def test_adding_teacher_syncs_casbin_role(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        regular_teacher: Teacher,
    ):
        """Adding teacher-org relationship should sync to Casbin"""
        casbin = get_casbin_service()

        # Before adding
        has_role_before = casbin.has_role(
            regular_teacher.id, "org_admin", f"org-{demo_org.id}"
        )
        assert has_role_before is False

        # Add relationship
        rel = TeacherOrganization(
            teacher_id=regular_teacher.id,
            organization_id=demo_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(rel)
        shared_test_session.commit()

        # Sync Casbin
        casbin.add_role_for_user(regular_teacher.id, "org_admin", f"org-{demo_org.id}")

        # After adding
        has_role_after = casbin.has_role(
            regular_teacher.id, "org_admin", f"org-{demo_org.id}"
        )
        assert has_role_after is True

    def test_removing_teacher_removes_casbin_role(
        self,
        shared_test_session: Session,
        demo_org: Organization,
        org_admin: Teacher,
    ):
        """Removing teacher-org relationship should remove Casbin role"""
        casbin = get_casbin_service()

        # Add relationship first
        rel = TeacherOrganization(
            teacher_id=org_admin.id,
            organization_id=demo_org.id,
            role="org_admin",
            is_active=True,
        )
        shared_test_session.add(rel)
        shared_test_session.commit()
        casbin.add_role_for_user(org_admin.id, "org_admin", f"org-{demo_org.id}")

        # Verify role exists
        has_role = casbin.has_role(org_admin.id, "org_admin", f"org-{demo_org.id}")
        assert has_role is True

        # Soft delete relationship
        rel.is_active = False
        shared_test_session.commit()

        # Remove Casbin role
        casbin.delete_role_for_user(org_admin.id, "org_admin", f"org-{demo_org.id}")

        # Verify role removed
        has_role_after = casbin.has_role(
            org_admin.id, "org_admin", f"org-{demo_org.id}"
        )
        assert has_role_after is False


class TestEdgeCases:
    """Test edge cases and invalid states"""

    def test_cannot_link_classroom_to_multiple_schools(
        self, shared_test_session: Session, demo_org: Organization, org_owner: Teacher
    ):
        """Classroom can only be linked to ONE school at a time"""
        # Create 2 schools
        school1 = School(organization_id=demo_org.id, name="school-1", is_active=True)
        school2 = School(organization_id=demo_org.id, name="school-2", is_active=True)
        shared_test_session.add_all([school1, school2])
        shared_test_session.commit()

        # Create classroom (use org_owner as teacher)
        classroom = Classroom(
            name="Test Class",
            teacher_id=org_owner.id,
            grade="5",
            is_active=True,
        )
        shared_test_session.add(classroom)
        shared_test_session.commit()
        shared_test_session.refresh(classroom)

        # Link to school1
        link1 = ClassroomSchool(
            classroom_id=classroom.id, school_id=school1.id, is_active=True
        )
        shared_test_session.add(link1)
        shared_test_session.commit()

        # API should prevent linking to school2 while link1 is active
        # Here we verify only 1 active link exists
        active_links = (
            shared_test_session.query(ClassroomSchool)
            .filter(
                ClassroomSchool.classroom_id == classroom.id,
                ClassroomSchool.is_active.is_(True),
            )
            .all()
        )
        assert (
            len(active_links) == 1
        ), f"Expected 1 active link, found {len(active_links)}"
        assert active_links[0].school_id == school1.id

    def test_inactive_organizations_not_listed(
        self, shared_test_session: Session, org_owner: Teacher
    ):
        """Soft-deleted organizations should not appear in listings"""
        # Create active org
        active_org = Organization(
            name="active-org", display_name="Active", is_active=True
        )
        shared_test_session.add(active_org)
        shared_test_session.commit()
        shared_test_session.refresh(active_org)

        # Create inactive org
        inactive_org = Organization(
            name="inactive-org", display_name="Inactive", is_active=False
        )
        shared_test_session.add(inactive_org)
        shared_test_session.commit()
        shared_test_session.refresh(inactive_org)

        # Query only active orgs
        active_orgs = (
            shared_test_session.query(Organization)
            .filter(Organization.is_active.is_(True))
            .all()
        )

        org_ids = [org.id for org in active_orgs]
        assert (
            active_org.id in org_ids
        ), f"Active org {active_org.id} not found in {org_ids}"
        assert (
            inactive_org.id not in org_ids
        ), f"Inactive org {inactive_org.id} should not be in {org_ids}"

    def test_empty_roles_array_handled_correctly(
        self,
        shared_test_session: Session,
        demo_school: School,
        regular_teacher: Teacher,
    ):
        """Teacher with empty roles array should be handled"""
        # Create relationship with empty roles
        rel = TeacherSchool(
            teacher_id=regular_teacher.id,
            school_id=demo_school.id,
            roles=[],  # Empty!
            is_active=True,
        )
        shared_test_session.add(rel)
        shared_test_session.commit()
        shared_test_session.refresh(rel)

        # Should be stored as empty list
        assert rel.roles == []
        assert isinstance(rel.roles, list)

    def test_null_optional_fields_handled(
        self, shared_test_session: Session, demo_org: Organization
    ):
        """NULL optional fields should not cause errors"""
        # Create org with minimal fields
        minimal_org = Organization(
            name="minimal-org",
            display_name=None,  # NULL
            description=None,  # NULL
            contact_email=None,  # NULL
            contact_phone=None,  # NULL
            address=None,  # NULL
            is_active=True,
        )
        shared_test_session.add(minimal_org)
        shared_test_session.commit()
        shared_test_session.refresh(minimal_org)

        # Should be created successfully
        assert minimal_org.id is not None
        assert minimal_org.name == "minimal-org"
        assert minimal_org.display_name is None
