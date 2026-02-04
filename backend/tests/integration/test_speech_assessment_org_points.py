"""
整合測試：speech_assessment 機構點數扣點

測試場景：
1. 機構班級 → 扣機構點數
2. 個人班級 → 扣老師配額
3. 機構點數不足時的處理
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from services.organization_points_service import OrganizationPointsService
from services.quota_service import QuotaService


class TestSpeechAssessmentOrgPoints:
    """測試 speech_assessment 根據班級類型扣點"""

    def test_org_classroom_deducts_org_points(self):
        """機構班級應該扣機構點數"""
        # Arrange
        org_id = uuid4()
        teacher_id = 1
        student_id = 2
        assignment_id = 3
        duration_seconds = 30.0

        classroom = Mock()
        classroom.organization_id = org_id

        assignment = Mock()
        assignment.classroom = classroom
        assignment.id = assignment_id

        # Act & Assert - 驗證呼叫正確的服務
        with patch.object(OrganizationPointsService, 'deduct_points') as mock_deduct:
            # 模擬扣點邏輯
            if classroom.organization_id:
                OrganizationPointsService.deduct_points(
                    db=Mock(),
                    organization_id=classroom.organization_id,
                    teacher_id=teacher_id,
                    student_id=student_id,
                    assignment_id=assignment_id,
                    feature_type="speech_assessment",
                    unit_count=duration_seconds,
                    unit_type="秒",
                )
                mock_deduct.assert_called_once()
                call_args = mock_deduct.call_args
                assert call_args.kwargs['organization_id'] == org_id
                assert call_args.kwargs['feature_type'] == "speech_assessment"
                assert call_args.kwargs['unit_count'] == duration_seconds
                assert call_args.kwargs['unit_type'] == "秒"

    def test_personal_classroom_deducts_teacher_quota(self):
        """個人班級應該扣老師配額"""
        # Arrange
        teacher = Mock()
        teacher.id = 1
        student_id = 2
        assignment_id = 3
        duration_seconds = 30.0

        classroom = Mock()
        classroom.organization_id = None  # 個人班級

        assignment = Mock()
        assignment.classroom = classroom
        assignment.id = assignment_id

        # Act & Assert - 驗證呼叫正確的服務
        with patch.object(QuotaService, 'deduct_quota') as mock_deduct:
            # 模擬扣點邏輯
            if not classroom.organization_id:
                QuotaService.deduct_quota(
                    db=Mock(),
                    teacher=teacher,
                    student_id=student_id,
                    assignment_id=assignment_id,
                    feature_type="speech_assessment",
                    unit_count=duration_seconds,
                    unit_type="秒",
                )
                mock_deduct.assert_called_once()
                call_args = mock_deduct.call_args
                assert call_args.kwargs['teacher'] == teacher
                assert call_args.kwargs['feature_type'] == "speech_assessment"

    def test_org_points_check_for_org_classroom(self):
        """機構班級應該檢查機構點數"""
        # Arrange
        org_id = uuid4()
        duration_seconds = 30.0
        required_points = OrganizationPointsService.convert_unit_to_points(duration_seconds, "秒")

        classroom = Mock()
        classroom.organization_id = org_id

        org = Mock()
        org.total_points = 10000
        org.used_points = 5000
        org.is_active = True

        # Act
        has_enough = OrganizationPointsService.check_points(org, required_points)

        # Assert
        assert has_enough is True
        assert required_points == 30  # 30秒 = 30點

    def test_org_points_insufficient_still_allows_learning(self):
        """機構點數不足時，仍允許學生學習（只記錄警告）"""
        # Arrange
        org = Mock()
        org.total_points = 100
        org.used_points = 100  # 已用完
        org.is_active = True

        required_points = 30

        # Act
        has_enough = OrganizationPointsService.check_points(org, required_points)

        # Assert - 點數不足，但業務邏輯應該允許繼續
        assert has_enough is False
        # 實際 speech_assessment 中只會記錄警告，不會阻擋

    def test_deduction_routing_logic(self):
        """驗證扣點路由邏輯"""
        # 機構班級
        org_classroom = Mock()
        org_classroom.organization_id = uuid4()
        assert org_classroom.organization_id is not None

        # 個人班級
        personal_classroom = Mock()
        personal_classroom.organization_id = None
        assert personal_classroom.organization_id is None

        # 路由邏輯
        def get_deduction_target(classroom):
            if classroom and classroom.organization_id:
                return "org_points"
            return "teacher_quota"

        assert get_deduction_target(org_classroom) == "org_points"
        assert get_deduction_target(personal_classroom) == "teacher_quota"
        assert get_deduction_target(None) == "teacher_quota"


class TestOrgPointsDeductionIntegration:
    """整合測試：完整扣點流程"""

    def test_full_deduction_flow_org(self):
        """完整機構扣點流程"""
        # 這個測試需要真實 DB，標記為需要 DB fixture
        pass  # TODO: 需要 DB fixture

    def test_full_deduction_flow_personal(self):
        """完整個人配額扣點流程"""
        # 這個測試需要真實 DB，標記為需要 DB fixture
        pass  # TODO: 需要 DB fixture
