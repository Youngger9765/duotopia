"""
Integration tests for org points deduction chain (Issue #208)

Tests the fix in commit 73f201b4 that added joinedload for the
classroom -> classroom_schools -> school chain in speech_assessment.py.

Without the joinedload fix, lazy loading fails when accessing
classroom.classroom_schools to determine if a classroom belongs to an org.

Test chains:
1. ORG chain: org -> school -> classroom_schools -> classroom -> deduct org.used_points
2. INDIVIDUAL chain: classroom with NO classroom_schools -> deduct teacher's SubscriptionPeriod.quota_used
"""

import pytest
from unittest.mock import Mock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone, timedelta, date

from models.organization import Organization, School, ClassroomSchool
from models.classroom import Classroom
from models.user import Teacher, Student
from models.assignment import Assignment, StudentAssignment
from models.subscription import SubscriptionPeriod, PointUsageLog
from models.base import AssignmentStatus
from auth import get_password_hash
from services.organization_points_service import OrganizationPointsService
from services.quota_service import QuotaService
from routers.speech_assessment import get_organization_id_from_classroom
from sqlalchemy.orm import joinedload


# ============================================================
# Test: get_organization_id_from_classroom (pure function tests)
# ============================================================


class TestGetOrganizationIdFromClassroom:
    """Tests for the get_organization_id_from_classroom helper function"""

    def test_returns_org_id_when_classroom_linked_to_school(self):
        """Classroom linked to active school with org -> returns org_id"""
        org_id = uuid4()

        school = Mock()
        school.organization_id = org_id

        cs = Mock()
        cs.is_active = True
        cs.school = school

        classroom = Mock()
        classroom.classroom_schools = [cs]

        result = get_organization_id_from_classroom(classroom)
        assert result == str(org_id)

    def test_returns_none_when_classroom_has_no_classroom_schools(self):
        """Classroom with empty classroom_schools list -> returns None"""
        classroom = Mock()
        classroom.classroom_schools = []

        result = get_organization_id_from_classroom(classroom)
        assert result is None

    def test_returns_none_when_classroom_is_none(self):
        """None classroom -> returns None"""
        result = get_organization_id_from_classroom(None)
        assert result is None

    def test_returns_none_when_classroom_schools_is_falsy(self):
        """Classroom with classroom_schools=None -> returns None"""
        classroom = Mock()
        classroom.classroom_schools = None

        result = get_organization_id_from_classroom(classroom)
        assert result is None

    def test_returns_none_when_classroom_school_is_inactive(self):
        """Classroom linked to inactive classroom_school -> returns None"""
        org_id = uuid4()

        school = Mock()
        school.organization_id = org_id

        cs = Mock()
        cs.is_active = False  # inactive
        cs.school = school

        classroom = Mock()
        classroom.classroom_schools = [cs]

        result = get_organization_id_from_classroom(classroom)
        assert result is None

    def test_returns_none_when_school_is_none(self):
        """Active classroom_school but school is None -> returns None"""
        cs = Mock()
        cs.is_active = True
        cs.school = None

        classroom = Mock()
        classroom.classroom_schools = [cs]

        result = get_organization_id_from_classroom(classroom)
        assert result is None

    def test_returns_none_when_school_has_no_organization_id(self):
        """School exists but has no organization_id -> returns None"""
        school = Mock()
        school.organization_id = None

        cs = Mock()
        cs.is_active = True
        cs.school = school

        classroom = Mock()
        classroom.classroom_schools = [cs]

        result = get_organization_id_from_classroom(classroom)
        assert result is None

    def test_skips_inactive_and_finds_active(self):
        """Multiple classroom_schools: skips inactive, returns from active"""
        org_id = uuid4()

        school_inactive = Mock()
        school_inactive.organization_id = uuid4()
        cs_inactive = Mock()
        cs_inactive.is_active = False
        cs_inactive.school = school_inactive

        school_active = Mock()
        school_active.organization_id = org_id
        cs_active = Mock()
        cs_active.is_active = True
        cs_active.school = school_active

        classroom = Mock()
        classroom.classroom_schools = [cs_inactive, cs_active]

        result = get_organization_id_from_classroom(classroom)
        assert result == str(org_id)

    def test_returns_first_active_with_org(self):
        """Multiple active classroom_schools -> returns first one's org_id"""
        org_id_1 = uuid4()
        org_id_2 = uuid4()

        school_1 = Mock()
        school_1.organization_id = org_id_1
        cs_1 = Mock()
        cs_1.is_active = True
        cs_1.school = school_1

        school_2 = Mock()
        school_2.organization_id = org_id_2
        cs_2 = Mock()
        cs_2.is_active = True
        cs_2.school = school_2

        classroom = Mock()
        classroom.classroom_schools = [cs_1, cs_2]

        result = get_organization_id_from_classroom(classroom)
        assert result == str(org_id_1)


# ============================================================
# Test: Database integration - joinedload chain
# ============================================================


class TestJoinedloadChain:
    """
    Tests that the joinedload query correctly loads the full chain:
    StudentAssignment -> Assignment -> Classroom -> ClassroomSchool -> School
    """

    def test_org_chain_joinedload_query(self, shared_test_session):
        """
        Full ORG chain: query with joinedload loads classroom_schools and school
        without lazy loading (which would fail in detached session).
        """
        db = shared_test_session

        # Create org -> school -> classroom chain
        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Test Org for Chain",
            total_points=10000,
            used_points=0,
            is_active=True,
        )
        db.add(org)
        db.flush()

        school_id = uuid4()
        school = School(
            id=school_id,
            organization_id=org_id,
            name="Test School",
            is_active=True,
        )
        db.add(school)
        db.flush()

        teacher = Teacher(
            email="chain-test-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="Chain Test Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        classroom = Classroom(
            name="Chain Test Classroom",
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        cs = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school_id,
            is_active=True,
        )
        db.add(cs)
        db.flush()

        assignment = Assignment(
            title="Chain Test Assignment",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        student = Student(
            name="Chain Test Student",
            password_hash=get_password_hash("test123"),
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title="Chain Test SA",
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(sa)
        db.commit()

        # Now query with joinedload (same pattern as speech_assessment.py)
        loaded_sa = (
            db.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment)
                .joinedload(Assignment.classroom)
                .joinedload(Classroom.classroom_schools)
                .joinedload(ClassroomSchool.school),
            )
            .filter(StudentAssignment.id == sa.id)
            .first()
        )

        assert loaded_sa is not None
        assert loaded_sa.assignment is not None
        assert loaded_sa.assignment.classroom is not None
        assert loaded_sa.assignment.classroom.classroom_schools is not None
        assert len(loaded_sa.assignment.classroom.classroom_schools) == 1

        loaded_cs = loaded_sa.assignment.classroom.classroom_schools[0]
        assert loaded_cs.is_active is True
        assert loaded_cs.school is not None
        assert loaded_cs.school.organization_id == org_id

        # Now verify get_organization_id_from_classroom works with loaded data
        result_org_id = get_organization_id_from_classroom(
            loaded_sa.assignment.classroom
        )
        assert result_org_id == str(org_id)

    def test_individual_chain_joinedload_query(self, shared_test_session):
        """
        INDIVIDUAL chain: classroom with NO classroom_schools.
        Joinedload returns empty list, get_organization_id_from_classroom returns None.
        """
        db = shared_test_session

        teacher = Teacher(
            email="individual-chain-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="Individual Chain Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        classroom = Classroom(
            name="Individual Classroom",
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        assignment = Assignment(
            title="Individual Assignment",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        student = Student(
            name="Individual Student",
            password_hash=get_password_hash("test123"),
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title="Individual SA",
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(sa)
        db.commit()

        # Query with joinedload
        loaded_sa = (
            db.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment)
                .joinedload(Assignment.classroom)
                .joinedload(Classroom.classroom_schools)
                .joinedload(ClassroomSchool.school),
            )
            .filter(StudentAssignment.id == sa.id)
            .first()
        )

        assert loaded_sa is not None
        assert loaded_sa.assignment.classroom is not None
        # No classroom_schools for individual classroom
        assert loaded_sa.assignment.classroom.classroom_schools == []

        result_org_id = get_organization_id_from_classroom(
            loaded_sa.assignment.classroom
        )
        assert result_org_id is None


# ============================================================
# Test: ORG path - OrganizationPointsService.deduct_points
# ============================================================


class TestOrgPointsDeduction:
    """Tests for ORG chain: deduct from Organization.used_points"""

    def test_deduct_points_increases_used_points(self, shared_test_session):
        """
        ORG path: OrganizationPointsService.deduct_points correctly
        increments Organization.used_points.
        """
        db = shared_test_session

        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Deduct Test Org",
            total_points=10000,
            used_points=100,
            is_active=True,
        )
        db.add(org)
        db.flush()

        teacher = Teacher(
            email="deduct-org-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="Deduct Org Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.commit()

        # Deduct 30 seconds worth of points
        log = OrganizationPointsService.deduct_points(
            db=db,
            organization_id=org_id,
            teacher_id=teacher.id,
            student_id=None,
            assignment_id=None,
            feature_type="speech_assessment",
            unit_count=30.0,
            unit_type="秒",
            feature_detail=None,
        )

        assert log is not None
        assert log.points_used == 30
        assert log.feature_type == "speech_assessment"

        # Verify org.used_points was updated
        db.refresh(org)
        assert org.used_points == 130  # 100 + 30

    def test_deduct_points_org_not_found_raises_404(self, shared_test_session):
        """deduct_points with non-existent org_id raises 404"""
        from fastapi import HTTPException

        db = shared_test_session

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=db,
                organization_id=uuid4(),  # non-existent
                teacher_id=1,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=10.0,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == "ORGANIZATION_NOT_FOUND"

    def test_deduct_points_inactive_org_raises_402(self, shared_test_session):
        """deduct_points with inactive org raises 402"""
        from fastapi import HTTPException

        db = shared_test_session

        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Inactive Org",
            total_points=10000,
            used_points=0,
            is_active=False,  # inactive
        )
        db.add(org)
        db.commit()

        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=db,
                organization_id=org_id,
                teacher_id=1,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=10.0,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "ORGANIZATION_INACTIVE"

    def test_deduct_points_exceeds_hard_limit_raises_402(self, shared_test_session):
        """deduct_points exceeding 120% hard limit raises 402"""
        from fastapi import HTTPException

        db = shared_test_session

        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="Exhausted Org",
            total_points=1000,
            used_points=1190,  # 119% used, buffer limit is 1200
            is_active=True,
        )
        db.add(org)
        db.commit()

        # Try to deduct 11 more points -> 1201 > 1200 (hard limit)
        with pytest.raises(HTTPException) as exc_info:
            OrganizationPointsService.deduct_points(
                db=db,
                organization_id=org_id,
                teacher_id=1,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=11.0,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "QUOTA_HARD_LIMIT_EXCEEDED"


# ============================================================
# Test: INDIVIDUAL path - QuotaService.deduct_quota
# ============================================================


class TestTeacherQuotaDeduction:
    """Tests for INDIVIDUAL chain: deduct from SubscriptionPeriod.quota_used"""

    def test_deduct_quota_increases_quota_used(self, shared_test_session):
        """
        INDIVIDUAL path: QuotaService.deduct_quota correctly
        increments SubscriptionPeriod.quota_used.
        """
        db = shared_test_session

        teacher = Teacher(
            email="deduct-quota-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="Deduct Quota Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=200,
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            payment_method="manual",
            status="active",
        )
        db.add(period)
        db.commit()

        # Deduct 30 seconds
        log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_assessment",
            unit_count=30.0,
            unit_type="秒",
            feature_detail=None,
        )

        assert log is not None
        assert log.points_used == 30
        assert log.quota_before == 200
        assert log.quota_after == 230

        # Verify period.quota_used was updated
        db.refresh(period)
        assert period.quota_used == 230  # 200 + 30

    def test_deduct_quota_no_subscription_raises_402(self, shared_test_session):
        """deduct_quota with no active subscription raises 402"""
        from fastapi import HTTPException

        db = shared_test_session

        teacher = Teacher(
            email="no-sub-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="No Sub Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.commit()

        # No SubscriptionPeriod created -> current_period returns None
        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=10.0,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "NO_SUBSCRIPTION"

    def test_deduct_quota_hard_limit_exceeded_raises_402(self, shared_test_session):
        """deduct_quota exceeding hard limit (120%) raises 402"""
        from fastapi import HTTPException

        db = shared_test_session

        teacher = Teacher(
            email="hard-limit-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="Hard Limit Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=1000,
            quota_used=1190,  # 119% used, limit is 1200
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            payment_method="manual",
            status="active",
        )
        db.add(period)
        db.commit()

        # Deduct 11 -> 1201 > 1200 hard limit
        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=11.0,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "QUOTA_HARD_LIMIT_EXCEEDED"


# ============================================================
# Test: Full end-to-end routing logic (org vs individual)
# ============================================================


class TestDeductionRoutingWithRealChain:
    """
    End-to-end test: given a StudentAssignment loaded with joinedload,
    verify the routing logic correctly picks ORG vs INDIVIDUAL path.
    """

    def test_org_classroom_routes_to_org_deduction(self, shared_test_session):
        """
        Full chain: org -> school -> classroom_school -> classroom -> assignment
        -> get_organization_id_from_classroom returns org_id
        -> OrganizationPointsService.deduct_points deducts from org.used_points
        """
        db = shared_test_session

        org_id = uuid4()
        org = Organization(
            id=org_id,
            name="E2E Org",
            total_points=5000,
            used_points=0,
            is_active=True,
        )
        db.add(org)
        db.flush()

        school_id = uuid4()
        school = School(
            id=school_id,
            organization_id=org_id,
            name="E2E School",
            is_active=True,
        )
        db.add(school)
        db.flush()

        teacher = Teacher(
            email="e2e-org-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="E2E Org Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        classroom = Classroom(
            name="E2E Org Classroom",
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        cs = ClassroomSchool(
            classroom_id=classroom.id,
            school_id=school_id,
            is_active=True,
        )
        db.add(cs)
        db.flush()

        assignment = Assignment(
            title="E2E Org Assignment",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        student = Student(
            name="E2E Student",
            password_hash=get_password_hash("test123"),
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title="E2E SA",
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(sa)
        db.commit()

        # Query with joinedload (exact same pattern as speech_assessment.py)
        loaded_sa = (
            db.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment)
                .joinedload(Assignment.classroom)
                .joinedload(Classroom.classroom_schools)
                .joinedload(ClassroomSchool.school),
            )
            .filter(StudentAssignment.id == sa.id)
            .first()
        )

        # Route: determine org_id
        loaded_classroom = loaded_sa.assignment.classroom
        result_org_id = get_organization_id_from_classroom(loaded_classroom)
        assert result_org_id == str(org_id)

        # Deduct from org
        log = OrganizationPointsService.deduct_points(
            db=db,
            organization_id=result_org_id,
            teacher_id=teacher.id,
            student_id=student.id,
            assignment_id=assignment.id,
            feature_type="speech_assessment",
            unit_count=15.0,
            unit_type="秒",
            feature_detail={"reference_text": "hello world"},
        )

        assert log.points_used == 15
        db.refresh(org)
        assert org.used_points == 15

    def test_individual_classroom_routes_to_teacher_quota(self, shared_test_session):
        """
        Individual chain: classroom with NO classroom_schools
        -> get_organization_id_from_classroom returns None
        -> QuotaService.deduct_quota deducts from SubscriptionPeriod.quota_used
        """
        db = shared_test_session

        teacher = Teacher(
            email="e2e-individual-teacher@test.com",
            password_hash=get_password_hash("test123"),
            name="E2E Individual Teacher",
            is_active=True,
            is_demo=False,
            email_verified=True,
        )
        db.add(teacher)
        db.flush()

        now = datetime.now(timezone.utc)
        period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=now - timedelta(days=15),
            end_date=now + timedelta(days=15),
            payment_method="manual",
            status="active",
        )
        db.add(period)
        db.flush()

        classroom = Classroom(
            name="E2E Individual Classroom",
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        assignment = Assignment(
            title="E2E Individual Assignment",
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(assignment)
        db.flush()

        student = Student(
            name="E2E Individual Student",
            password_hash=get_password_hash("test123"),
            birthdate=date(2010, 1, 1),
        )
        db.add(student)
        db.flush()

        sa = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=classroom.id,
            title="E2E Individual SA",
            status=AssignmentStatus.IN_PROGRESS,
        )
        db.add(sa)
        db.commit()

        # Query with joinedload
        loaded_sa = (
            db.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment)
                .joinedload(Assignment.classroom)
                .joinedload(Classroom.classroom_schools)
                .joinedload(ClassroomSchool.school),
            )
            .filter(StudentAssignment.id == sa.id)
            .first()
        )

        # Route: determine org_id
        loaded_classroom = loaded_sa.assignment.classroom
        result_org_id = get_organization_id_from_classroom(loaded_classroom)
        assert result_org_id is None

        # Deduct from teacher quota
        log = QuotaService.deduct_quota(
            db=db,
            teacher=teacher,
            student_id=student.id,
            assignment_id=assignment.id,
            feature_type="speech_assessment",
            unit_count=20.0,
            unit_type="秒",
            feature_detail={"reference_text": "hello world"},
        )

        assert log.points_used == 20
        assert log.quota_before == 0
        assert log.quota_after == 20

        db.refresh(period)
        assert period.quota_used == 20

    def test_school_with_no_organization_returns_none(self, shared_test_session):
        """
        Edge case: ClassroomSchool links to a School that has
        organization_id = None (orphan school). Should return None.

        NOTE: In the current schema, School.organization_id is NOT nullable,
        so this scenario uses a mock to test the function's branch logic.
        """
        school = Mock()
        school.organization_id = None

        cs = Mock()
        cs.is_active = True
        cs.school = school

        classroom = Mock()
        classroom.classroom_schools = [cs]

        result = get_organization_id_from_classroom(classroom)
        assert result is None
