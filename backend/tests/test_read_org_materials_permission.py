"""
Test has_read_org_materials_permission

Verifies that any active organization member can read organization materials,
while inactive members and non-members cannot.
"""

import uuid
import pytest
from unittest.mock import MagicMock, patch
from utils.permissions import has_read_org_materials_permission


class TestReadOrgMaterialsPermission:
    """Test read permission for organization materials"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up mock database session"""
        self.db = MagicMock()
        self.org_id = uuid.uuid4()
        self.teacher_id = 999

    def _mock_membership(self, is_active=True, role="teacher"):
        """Helper to mock TeacherOrganization query result"""
        membership = MagicMock()
        membership.is_active = is_active
        membership.role = role

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = membership
        self.db.query.return_value = query_mock
        return membership

    def _mock_no_membership(self):
        """Helper to mock no membership found"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        self.db.query.return_value = query_mock

    def test_active_member_can_read_org_materials(self):
        """Any active org member should have read permission"""
        self._mock_membership(is_active=True, role="teacher")

        result = has_read_org_materials_permission(
            self.teacher_id, self.org_id, self.db
        )

        assert result is True

    def test_active_org_owner_can_read_org_materials(self):
        """org_owner should have read permission"""
        self._mock_membership(is_active=True, role="org_owner")

        result = has_read_org_materials_permission(
            self.teacher_id, self.org_id, self.db
        )

        assert result is True

    def test_active_org_admin_can_read_org_materials(self):
        """org_admin should have read permission"""
        self._mock_membership(is_active=True, role="org_admin")

        result = has_read_org_materials_permission(
            self.teacher_id, self.org_id, self.db
        )

        assert result is True

    def test_inactive_member_cannot_read_org_materials(self):
        """Inactive members should not have read permission"""
        # Mock: query returns None because filter includes is_active=True
        self._mock_no_membership()

        result = has_read_org_materials_permission(
            self.teacher_id, self.org_id, self.db
        )

        assert result is False

    def test_non_member_cannot_read_org_materials(self):
        """Non-members should not have read permission"""
        self._mock_no_membership()

        result = has_read_org_materials_permission(
            self.teacher_id, self.org_id, self.db
        )

        assert result is False
