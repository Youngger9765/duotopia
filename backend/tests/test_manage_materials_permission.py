"""
Test manage_materials Permission

Verifies that the manage_materials permission is correctly configured in Casbin
for organization-level material management.
"""

import pytest
from services.casbin_service import CasbinService


class TestManageMaterialsPermission:
    """Test manage_materials permission for different roles"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Initialize Casbin service before each test"""
        self.casbin = CasbinService()
        # Clear only role assignments (g rules), preserve policy rules (p rules)
        all_grouping = self.casbin.enforcer.get_grouping_policy()
        for g in all_grouping:
            self.casbin.enforcer.remove_grouping_policy(*g)
        yield
        # Cleanup: Clear role assignments
        all_grouping = self.casbin.enforcer.get_grouping_policy()
        for g in all_grouping:
            self.casbin.enforcer.remove_grouping_policy(*g)

    def test_org_owner_can_manage_materials(self):
        """org_owner should have manage_materials permission"""
        # Add org_owner role
        self.casbin.add_role_for_user(
            teacher_id=123, role="org_owner", domain="org-test-uuid"
        )

        # Check permission
        can_manage = self.casbin.check_permission(
            teacher_id=123,
            domain="org-test-uuid",
            resource="manage_materials",
            action="write",
        )

        assert can_manage is True, "org_owner should have manage_materials permission"

    def test_org_admin_can_manage_materials(self):
        """org_admin should have manage_materials permission"""
        # Add org_admin role
        self.casbin.add_role_for_user(
            teacher_id=456, role="org_admin", domain="org-test-uuid"
        )

        # Check permission
        can_manage = self.casbin.check_permission(
            teacher_id=456,
            domain="org-test-uuid",
            resource="manage_materials",
            action="write",
        )

        assert can_manage is True, "org_admin should have manage_materials permission"

    def test_school_admin_cannot_manage_materials(self):
        """school_admin should NOT have manage_materials permission (org-level only)"""
        # Add school_admin role
        self.casbin.add_role_for_user(
            teacher_id=789, role="school_admin", domain="school-test-uuid"
        )

        # Check permission at school level
        can_manage = self.casbin.check_permission(
            teacher_id=789,
            domain="school-test-uuid",
            resource="manage_materials",
            action="write",
        )

        assert (
            can_manage is False
        ), "school_admin should NOT have manage_materials permission"

    def test_teacher_cannot_manage_materials(self):
        """Regular teacher should NOT have manage_materials permission"""
        # Add teacher role
        self.casbin.add_role_for_user(
            teacher_id=999, role="teacher", domain="school-test-uuid"
        )

        # Check permission
        can_manage = self.casbin.check_permission(
            teacher_id=999,
            domain="school-test-uuid",
            resource="manage_materials",
            action="write",
        )

        assert (
            can_manage is False
        ), "teacher should NOT have manage_materials permission"

    def test_different_organizations_isolated(self):
        """Materials permissions should be isolated between organizations"""
        # Teacher is org_owner in org-A
        self.casbin.add_role_for_user(teacher_id=123, role="org_owner", domain="org-A")

        # Can manage materials in org-A
        can_manage_org_a = self.casbin.check_permission(
            teacher_id=123, domain="org-A", resource="manage_materials", action="write"
        )

        # Cannot manage materials in org-B (different organization)
        can_manage_org_b = self.casbin.check_permission(
            teacher_id=123, domain="org-B", resource="manage_materials", action="write"
        )

        assert can_manage_org_a is True, "Should manage materials in own organization"
        assert (
            can_manage_org_b is False
        ), "Should NOT manage materials in other organizations"
