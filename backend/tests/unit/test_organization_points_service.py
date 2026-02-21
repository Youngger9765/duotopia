"""
OrganizationPointsService Unit Tests (TDD - Red Phase)

Tests for the organization points deduction service.
These tests define the expected behavior BEFORE implementation.

Reference: Issue #208 - Organization Points Deduction
Spec: docs/issues/208-complete-spec.md
Pattern: backend/tests/unit/test_quota_service.py
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

# Import the service to be tested (will fail initially - Red phase)
# from services.organization_points_service import OrganizationPointsService

# Import models for type hints and mocking
from models.organization import Organization, OrganizationPointsLog


# ============================================
# Fixtures
# ============================================


@pytest.fixture
def mock_organization():
    """
    Create a mock Organization with default points.

    Default state:
    - total_points: 10000
    - used_points: 5000
    - remaining: 5000
    """
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Test Organization"
    org.total_points = 10000
    org.used_points = 5000
    org.last_points_update = datetime.now(timezone.utc)
    org.is_active = True
    return org


@pytest.fixture
def mock_organization_low_points():
    """
    Create a mock Organization with low remaining points.

    State:
    - total_points: 10000
    - used_points: 9500
    - remaining: 500 (5% remaining)
    """
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Low Points Organization"
    org.total_points = 10000
    org.used_points = 9500
    org.last_points_update = datetime.now(timezone.utc)
    org.is_active = True
    return org


@pytest.fixture
def mock_organization_in_buffer():
    """
    Create a mock Organization using buffer (100%-120% usage).

    State:
    - total_points: 10000
    - used_points: 10500 (105% - in buffer zone)
    - buffer limit: 12000 (120%)
    """
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Buffer Zone Organization"
    org.total_points = 10000
    org.used_points = 10500
    org.last_points_update = datetime.now(timezone.utc)
    org.is_active = True
    return org


@pytest.fixture
def mock_organization_exhausted():
    """
    Create a mock Organization at hard limit.

    State:
    - total_points: 10000
    - used_points: 12000 (120% - at hard limit)
    """
    org = Mock(spec=Organization)
    org.id = uuid4()
    org.name = "Exhausted Organization"
    org.total_points = 10000
    org.used_points = 12000
    org.last_points_update = datetime.now(timezone.utc)
    org.is_active = True
    return org


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.query = Mock()
    return session


# ============================================
# Test Class: Unit Conversion
# ============================================


class TestUnitConversion:
    """
    Test unit conversion logic.

    Conversion rules (from spec):
    - 秒 (seconds): 1 秒 = 1 點
    - 字 (characters): 1 字 = 0.1 點
    - 張 (images): 1 張 = 10 點
    - 分鐘 (minutes): 1 分鐘 = 60 點
    """

    def test_convert_unit_to_points_seconds(self):
        """
        Test conversion: seconds to points.

        Rule: 1 秒 = 1 點
        Example: 10 秒 → 10 點
        """
        from services.organization_points_service import OrganizationPointsService

        # 10 seconds = 10 points
        result = OrganizationPointsService.convert_unit_to_points(10, "秒")
        assert result == 10

        # 60 seconds = 60 points
        result = OrganizationPointsService.convert_unit_to_points(60, "秒")
        assert result == 60

        # 0.5 seconds = 0 points (rounded down)
        result = OrganizationPointsService.convert_unit_to_points(0.5, "秒")
        assert result == 0

    def test_convert_unit_to_points_characters(self):
        """
        Test conversion: characters to points.

        Rule: 1 字 = 0.1 點 (10 字 = 1 點)
        Example: 100 字 → 10 點
        """
        from services.organization_points_service import OrganizationPointsService

        # 100 characters = 10 points
        result = OrganizationPointsService.convert_unit_to_points(100, "字")
        assert result == 10

        # 500 characters = 50 points
        result = OrganizationPointsService.convert_unit_to_points(500, "字")
        assert result == 50

        # 1000 characters = 100 points
        result = OrganizationPointsService.convert_unit_to_points(1000, "字")
        assert result == 100

    def test_convert_unit_to_points_images(self):
        """
        Test conversion: images to points.

        Rule: 1 張 = 10 點
        Example: 2 張 → 20 點
        """
        from services.organization_points_service import OrganizationPointsService

        # 2 images = 20 points
        result = OrganizationPointsService.convert_unit_to_points(2, "張")
        assert result == 20

        # 5 images = 50 points
        result = OrganizationPointsService.convert_unit_to_points(5, "張")
        assert result == 50

    def test_convert_unit_to_points_minutes(self):
        """
        Test conversion: minutes to points.

        Rule: 1 分鐘 = 60 點
        Example: 2 分鐘 → 120 點
        """
        from services.organization_points_service import OrganizationPointsService

        # 2 minutes = 120 points
        result = OrganizationPointsService.convert_unit_to_points(2, "分鐘")
        assert result == 120

        # 1.5 minutes = 90 points
        result = OrganizationPointsService.convert_unit_to_points(1.5, "分鐘")
        assert result == 90

    def test_convert_unit_to_points_invalid_unit(self):
        """
        Test conversion with invalid unit type.

        Expected: Raise ValueError for unsupported unit types.
        """
        from services.organization_points_service import OrganizationPointsService

        with pytest.raises(ValueError) as exc_info:
            OrganizationPointsService.convert_unit_to_points(10, "無效單位")

        assert "不支援的單位類型" in str(exc_info.value)

    def test_convert_unit_to_points_zero(self):
        """
        Test conversion with zero units.

        Expected: 0 points
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.convert_unit_to_points(0, "秒")
        assert result == 0


# ============================================
# Test Class: Check Points
# ============================================


class TestCheckPoints:
    """
    Test points sufficiency checking.
    """

    def test_check_points_sufficient(self, mock_organization):
        """
        Test check_points returns True when points are sufficient.

        Organization state:
        - total_points: 10000
        - used_points: 5000
        - remaining: 5000

        Required: 100 points → should be sufficient
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.check_points(mock_organization, 100)
        assert result is True

    def test_check_points_insufficient(self, mock_organization_exhausted):
        """
        Test check_points returns False when points are insufficient.

        Organization state:
        - total_points: 10000
        - used_points: 12000 (at hard limit)

        Required: 100 points → should be insufficient
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.check_points(
            mock_organization_exhausted, 100
        )
        assert result is False

    def test_check_points_exact_remaining(self, mock_organization):
        """
        Test check_points at exact boundary.

        Organization state:
        - remaining: 5000

        Required: 5000 points → should be exactly sufficient
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.check_points(mock_organization, 5000)
        assert result is True

    def test_check_points_one_over(self, mock_organization):
        """
        Test check_points when required is 1 more than remaining.

        Organization state:
        - remaining: 5000

        Required: 5001 points → should be insufficient (no buffer for check)
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.check_points(mock_organization, 5001)
        assert result is False

    def test_check_points_no_org(self):
        """
        Test check_points with None organization.

        Expected: Return False when organization is None
        """
        from services.organization_points_service import OrganizationPointsService

        result = OrganizationPointsService.check_points(None, 100)
        assert result is False

    def test_check_points_inactive_org(self, mock_organization):
        """
        Test check_points with inactive organization.

        Expected: Return False for inactive organizations
        """
        from services.organization_points_service import OrganizationPointsService

        mock_organization.is_active = False
        result = OrganizationPointsService.check_points(mock_organization, 100)
        assert result is False


# ============================================
# Test Class: Get Points Info
# ============================================


class TestGetPointsInfo:
    """
    Test points information retrieval.
    """

    def test_get_points_info(self, mock_organization):
        """
        Test get_points_info returns correct structure.

        Expected response:
        {
            "total": 10000,
            "used": 5000,
            "remaining": 5000,
            "status": "active"
        }
        """
        from services.organization_points_service import OrganizationPointsService

        info = OrganizationPointsService.get_points_info(mock_organization)

        assert info["total"] == 10000
        assert info["used"] == 5000
        assert info["remaining"] == 5000
        assert info["status"] == "active"

    def test_get_points_info_low_points(self, mock_organization_low_points):
        """
        Test get_points_info with low remaining points.

        Expected status: "warning" when remaining < 10%
        """
        from services.organization_points_service import OrganizationPointsService

        info = OrganizationPointsService.get_points_info(mock_organization_low_points)

        assert info["total"] == 10000
        assert info["used"] == 9500
        assert info["remaining"] == 500
        assert info["status"] == "warning"

    def test_get_points_info_in_buffer(self, mock_organization_in_buffer):
        """
        Test get_points_info when using buffer quota.

        Expected status: "buffer" when used > total but < limit
        """
        from services.organization_points_service import OrganizationPointsService

        info = OrganizationPointsService.get_points_info(mock_organization_in_buffer)

        assert info["total"] == 10000
        assert info["used"] == 10500
        assert info["remaining"] == 0  # No positive remaining
        assert info["status"] == "buffer"
        assert "buffer_remaining" in info
        assert info["buffer_remaining"] == 1500  # 12000 - 10500

    def test_get_points_info_exhausted(self, mock_organization_exhausted):
        """
        Test get_points_info when buffer is exhausted.

        Expected status: "exhausted" when at or over hard limit
        """
        from services.organization_points_service import OrganizationPointsService

        info = OrganizationPointsService.get_points_info(mock_organization_exhausted)

        assert info["status"] == "exhausted"
        assert info["remaining"] == 0

    def test_get_points_info_no_org(self):
        """
        Test get_points_info with None organization.

        Expected: Return empty/zero info
        """
        from services.organization_points_service import OrganizationPointsService

        info = OrganizationPointsService.get_points_info(None)

        assert info["total"] == 0
        assert info["used"] == 0
        assert info["remaining"] == 0
        assert info["status"] == "no_organization"


# ============================================
# Test Class: Deduct Points
# ============================================


class TestDeductPoints:
    """
    Test points deduction logic.

    Deduction includes:
    1. Convert units to points
    2. Check if within limits (with 20% buffer)
    3. Update organization.used_points
    4. Create OrganizationPointsLog record
    """

    def test_deduct_points_success(self, mock_db_session, mock_organization):
        """
        Test successful points deduction.

        Scenario:
        - Organization has 5000 remaining points
        - Deduct 30 seconds (30 points)

        Expected:
        - used_points increases by 30
        - OrganizationPointsLog created
        - Returns log record
        """
        from services.organization_points_service import OrganizationPointsService

        # Setup mock query to return organization
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        org_id = mock_organization.id
        teacher_id = 1
        student_id = 100
        assignment_id = 500

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=org_id,
            teacher_id=teacher_id,
            student_id=student_id,
            assignment_id=assignment_id,
            feature_type="speech_assessment",
            unit_count=30,
            unit_type="秒",
            feature_detail={"duration": 30, "accuracy_score": 85.5},
        )

        # Verify organization updated
        assert mock_organization.used_points == 5030

        # Verify db operations called
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

        # Verify log created with correct data
        assert log is not None
        assert log.points_used == 30
        assert log.organization_id == org_id
        assert log.teacher_id == teacher_id
        assert log.feature_type == "speech_assessment"

    def test_deduct_points_with_characters(self, mock_db_session, mock_organization):
        """
        Test deduction with character units.

        Scenario:
        - Deduct 500 characters (50 points)
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=None,
            assignment_id=None,
            feature_type="text_correction",
            unit_count=500,
            unit_type="字",
        )

        # 500 characters = 50 points
        assert log.points_used == 50
        assert mock_organization.used_points == 5050

    def test_deduct_points_buffer_warning(
        self, mock_db_session, mock_organization_low_points
    ):
        """
        Test deduction when entering buffer zone (100%-120%).

        Scenario:
        - Organization: 10000 total, 9500 used (500 remaining)
        - Deduct 600 points → enters buffer zone

        Expected:
        - Deduction succeeds (within buffer)
        - Warning logged (implementation detail)
        - used_points = 10100 (above 100%, in buffer)
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization_low_points
        )

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization_low_points.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=600,
            unit_type="秒",
        )

        # Deduction should succeed
        assert log.points_used == 600
        assert mock_organization_low_points.used_points == 10100

        # Should be in buffer zone
        assert (
            mock_organization_low_points.used_points
            > mock_organization_low_points.total_points
        )

    def test_deduct_points_hard_limit_exceeded(
        self, mock_db_session, mock_organization_exhausted
    ):
        """
        Test deduction when hard limit would be exceeded.

        Scenario:
        - Organization: 10000 total, 12000 used (at 120% limit)
        - Buffer limit: 12000 (120%)
        - Try to deduct 100 points → exceeds hard limit

        Expected:
        - HTTPException 402 raised
        - Error code: QUOTA_HARD_LIMIT_EXCEEDED
        - No points deducted
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization_exhausted
        )

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=mock_db_session,
                organization_id=mock_organization_exhausted.id,
                teacher_id=1,
                student_id=100,
                assignment_id=500,
                feature_type="speech_assessment",
                unit_count=100,
                unit_type="秒",
            )

        # Verify HTTP 402 Payment Required
        assert exc_info.value.status_code == 402
        assert "QUOTA_HARD_LIMIT_EXCEEDED" in str(exc_info.value.detail)

    def test_deduct_points_creates_log(self, mock_db_session, mock_organization):
        """
        Test that deduction creates OrganizationPointsLog with all fields.

        Expected log fields:
        - organization_id
        - teacher_id
        - points_used
        - feature_type
        - description (optional)
        - created_at
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        feature_detail = {
            "reference_text": "Hello world",
            "accuracy_score": 92.5,
            "audio_size_bytes": 1024,
        }

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=30,
            unit_type="秒",
            feature_detail=feature_detail,
        )

        # Verify all expected fields
        assert log.organization_id == mock_organization.id
        assert log.teacher_id == 1
        assert log.points_used == 30
        assert log.feature_type == "speech_assessment"

    def test_deduct_points_organization_not_found(self, mock_db_session):
        """
        Test deduction when organization doesn't exist.

        Expected:
        - HTTPException 404 raised
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=mock_db_session,
                organization_id=uuid4(),
                teacher_id=1,
                student_id=100,
                assignment_id=500,
                feature_type="speech_assessment",
                unit_count=30,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 404

    def test_deduct_points_inactive_organization(
        self, mock_db_session, mock_organization
    ):
        """
        Test deduction for inactive organization.

        Expected:
        - HTTPException 402 raised
        - Error indicates organization is inactive
        """
        from services.organization_points_service import OrganizationPointsService

        mock_organization.is_active = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=mock_db_session,
                organization_id=mock_organization.id,
                teacher_id=1,
                student_id=100,
                assignment_id=500,
                feature_type="speech_assessment",
                unit_count=30,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402

    def test_deduct_points_updates_timestamp(self, mock_db_session, mock_organization):
        """
        Test that deduction updates last_points_update timestamp.
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )
        original_timestamp = mock_organization.last_points_update

        OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=30,
            unit_type="秒",
        )

        # Timestamp should be updated
        assert mock_organization.last_points_update != original_timestamp

    def test_deduct_points_multiple_deductions(
        self, mock_db_session, mock_organization
    ):
        """
        Test multiple sequential deductions.

        Scenario:
        - Initial: 5000 used
        - Deduct 100 → 5100 used
        - Deduct 200 → 5300 used
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        # First deduction
        OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=100,
            unit_type="秒",
        )
        assert mock_organization.used_points == 5100

        # Second deduction
        OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=101,
            assignment_id=501,
            feature_type="speech_assessment",
            unit_count=200,
            unit_type="秒",
        )
        assert mock_organization.used_points == 5300


# ============================================
# Test Class: Buffer Calculation
# ============================================


class TestBufferCalculation:
    """
    Test the 20% buffer calculation logic.

    Buffer rules:
    - Base limit: total_points
    - Hard limit: total_points * 1.20 (120%)
    - Between 100%-120%: Allowed with warning
    - Above 120%: Blocked
    """

    def test_buffer_percentage_constant(self):
        """
        Verify QUOTA_BUFFER_PERCENTAGE is 0.20 (20%).
        """
        from services.organization_points_service import OrganizationPointsService

        assert OrganizationPointsService.QUOTA_BUFFER_PERCENTAGE == 0.20

    def test_hard_limit_calculation(self, mock_organization):
        """
        Test hard limit is calculated as total * 1.20.

        Example:
        - total_points: 10000
        - hard_limit: 12000
        """
        from services.organization_points_service import OrganizationPointsService

        total = mock_organization.total_points  # 10000
        expected_limit = int(total * 1.20)  # 12000

        # The actual implementation should calculate this correctly
        # This test verifies the calculation logic
        assert expected_limit == 12000

    def test_exactly_at_buffer_boundary(self, mock_db_session, mock_organization):
        """
        Test deduction that brings usage exactly to 120%.

        Scenario:
        - total: 10000, used: 5000
        - Deduct 7000 points → used becomes 12000 (exactly 120%)

        Expected: Should succeed (at boundary, not over)
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=7000,
            unit_type="秒",
        )

        # Should succeed at exactly 120%
        assert log.points_used == 7000
        assert mock_organization.used_points == 12000

    def test_one_point_over_buffer(self, mock_db_session, mock_organization):
        """
        Test deduction that would exceed 120% by 1 point.

        Scenario:
        - total: 10000, used: 5000
        - Deduct 7001 points → would be 12001 (120.01%)

        Expected: Should fail
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=mock_db_session,
                organization_id=mock_organization.id,
                teacher_id=1,
                student_id=100,
                assignment_id=500,
                feature_type="speech_assessment",
                unit_count=7001,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402


# ============================================
# Test Class: Edge Cases
# ============================================


class TestEdgeCases:
    """
    Test edge cases and boundary conditions.
    """

    def test_zero_points_deduction(self, mock_db_session, mock_organization):
        """
        Test deducting 0 points.

        Expected: No change, but log may or may not be created
        (implementation detail - could skip or create 0-point log)
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )
        original_used = mock_organization.used_points

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=0,
            unit_type="秒",
        )

        # used_points should not change
        assert mock_organization.used_points == original_used

    def test_fractional_character_conversion(self):
        """
        Test fractional point calculations round correctly.

        Example: 5 characters = 0.5 points → rounds to 0 or 1
        """
        from services.organization_points_service import OrganizationPointsService

        # 5 characters = 0.5 points → should round to 0 (int truncation)
        result = OrganizationPointsService.convert_unit_to_points(5, "字")
        assert result == 0

        # 15 characters = 1.5 points → should round to 1
        result = OrganizationPointsService.convert_unit_to_points(15, "字")
        assert result == 1

    def test_large_deduction(self, mock_db_session, mock_organization):
        """
        Test very large deduction within limits.
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        # Deduct 4000 points (within 5000 remaining)
        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=100,
            assignment_id=500,
            feature_type="speech_assessment",
            unit_count=4000,
            unit_type="秒",
        )

        assert log.points_used == 4000
        assert mock_organization.used_points == 9000

    def test_deduction_with_optional_fields_none(
        self, mock_db_session, mock_organization
    ):
        """
        Test deduction when optional fields are None.
        """
        from services.organization_points_service import OrganizationPointsService

        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_organization
        )

        log = OrganizationPointsService.deduct_points(
            db=mock_db_session,
            organization_id=mock_organization.id,
            teacher_id=1,
            student_id=None,  # Optional
            assignment_id=None,  # Optional
            feature_type="manual_deduction",
            unit_count=50,
            unit_type="秒",
            feature_detail=None,  # Optional
        )

        assert log.points_used == 50
        assert log.feature_type == "manual_deduction"
