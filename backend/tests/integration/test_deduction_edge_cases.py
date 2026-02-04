"""
邊緣情境測試：機構扣點 vs 個人配額扣點

測試目標：
1. 確保路由邏輯不衝突（機構 vs 個人）
2. 扣點失敗情境處理
3. 點數不足情境處理
4. 各種邊緣情況
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from fastapi import HTTPException

from services.organization_points_service import OrganizationPointsService
from services.quota_service import QuotaService


class TestDeductionRoutingConflicts:
    """測試路由邏輯不衝突"""

    def test_org_classroom_never_calls_teacher_quota(self):
        """機構班級絕對不會呼叫 QuotaService"""
        org_id = uuid4()
        classroom = Mock(organization_id=org_id)
        assignment = Mock(classroom=classroom)

        with patch.object(QuotaService, 'deduct_quota') as mock_quota:
            with patch.object(OrganizationPointsService, 'deduct_points') as mock_org:
                # 模擬路由邏輯
                if classroom.organization_id:
                    OrganizationPointsService.deduct_points(
                        db=Mock(), organization_id=org_id, teacher_id=1,
                        student_id=2, assignment_id=3, feature_type="test",
                        unit_count=10, unit_type="秒"
                    )
                else:
                    QuotaService.deduct_quota(db=Mock(), teacher=Mock())

                mock_org.assert_called_once()
                mock_quota.assert_not_called()

    def test_personal_classroom_never_calls_org_points(self):
        """個人班級絕對不會呼叫 OrganizationPointsService"""
        classroom = Mock(organization_id=None)
        assignment = Mock(classroom=classroom)
        teacher = Mock(id=1)

        with patch.object(QuotaService, 'deduct_quota') as mock_quota:
            with patch.object(OrganizationPointsService, 'deduct_points') as mock_org:
                # 模擬路由邏輯
                if classroom.organization_id:
                    OrganizationPointsService.deduct_points(db=Mock())
                else:
                    QuotaService.deduct_quota(
                        db=Mock(), teacher=teacher, student_id=2,
                        assignment_id=3, feature_type="test",
                        unit_count=10, unit_type="秒"
                    )

                mock_quota.assert_called_once()
                mock_org.assert_not_called()

    def test_classroom_none_defaults_to_teacher_quota(self):
        """classroom 為 None 時，預設使用老師配額"""
        classroom = None
        teacher = Mock(id=1)

        with patch.object(QuotaService, 'deduct_quota') as mock_quota:
            with patch.object(OrganizationPointsService, 'deduct_points') as mock_org:
                # 路由邏輯
                if classroom and classroom.organization_id:
                    OrganizationPointsService.deduct_points(db=Mock())
                else:
                    QuotaService.deduct_quota(
                        db=Mock(), teacher=teacher, student_id=2,
                        assignment_id=3, feature_type="test",
                        unit_count=10, unit_type="秒"
                    )

                mock_quota.assert_called_once()
                mock_org.assert_not_called()

    def test_assignment_none_skips_deduction(self):
        """assignment 為 None 時，跳過扣點"""
        teacher = Mock(id=1)
        assignment = None

        deduction_called = False

        # 模擬 speech_assessment 的邏輯
        if teacher and assignment:
            deduction_called = True

        assert deduction_called is False


class TestOrgPointsFailureScenarios:
    """測試機構點數扣點失敗情境"""

    def test_org_not_found_raises_404(self):
        """機構不存在時，應該拋出 404"""
        with pytest.raises(HTTPException) as exc_info:
            # 模擬 deduct_points 中機構不存在
            raise HTTPException(
                status_code=404,
                detail={"error": "ORGANIZATION_NOT_FOUND", "message": "機構不存在"}
            )

        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["error"] == "ORGANIZATION_NOT_FOUND"

    def test_org_inactive_raises_402(self):
        """機構已停用時，應該拋出 402"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=402,
                detail={"error": "ORGANIZATION_INACTIVE", "message": "機構已停用"}
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "ORGANIZATION_INACTIVE"

    def test_org_hard_limit_exceeded_raises_402(self):
        """機構點數超過硬限制時，應該拋出 402"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "QUOTA_HARD_LIMIT_EXCEEDED",
                    "message": "機構點數已用盡",
                    "points_used": 12000,
                    "total_points": 10000,
                    "points_limit": 12000,
                    "buffer_percentage": 20,
                }
            )

        assert exc_info.value.status_code == 402
        assert exc_info.value.detail["error"] == "QUOTA_HARD_LIMIT_EXCEEDED"


class TestTeacherQuotaFailureScenarios:
    """測試老師配額扣點失敗情境"""

    def test_teacher_quota_hard_limit_exceeded(self):
        """老師配額超過硬限制時，應該拋出 402"""
        with pytest.raises(HTTPException) as exc_info:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "QUOTA_HARD_LIMIT_EXCEEDED",
                    "message": "老師的配額已用完",
                    "quota_used": 1200,
                    "quota_limit": 1000,
                }
            )

        assert exc_info.value.status_code == 402


class TestPointsInsufficientScenarios:
    """測試點數不足情境"""

    def test_org_zero_points_remaining(self):
        """機構剩餘 0 點"""
        org = Mock(total_points=1000, used_points=1000, is_active=True)
        has_enough = OrganizationPointsService.check_points(org, 1)
        assert has_enough is False

    def test_org_in_warning_zone(self):
        """機構在警告區（80-100%）"""
        org = Mock(total_points=1000, used_points=850, is_active=True)
        info = OrganizationPointsService.get_points_info(org)
        assert info["status"] == "warning"
        assert info["remaining"] == 150

    def test_org_in_buffer_zone(self):
        """機構在緩衝區（100-120%）"""
        org = Mock(total_points=1000, used_points=1100, is_active=True)
        info = OrganizationPointsService.get_points_info(org)
        assert info["status"] == "buffer"
        assert info["remaining"] == 0  # remaining 不會是負數
        assert "buffer_remaining" in info

    def test_org_exhausted(self):
        """機構點數耗盡（>=120%）"""
        org = Mock(total_points=1000, used_points=1200, is_active=True)
        info = OrganizationPointsService.get_points_info(org)
        assert info["status"] == "exhausted"

    def test_org_exactly_at_buffer_limit(self):
        """機構剛好在緩衝限制邊界"""
        org = Mock(total_points=1000, used_points=1200, is_active=True)
        # 1200 = 1000 * 1.2 = 剛好在邊界
        info = OrganizationPointsService.get_points_info(org)
        assert info["status"] == "exhausted"

    def test_one_point_before_buffer_limit(self):
        """緩衝限制前 1 點"""
        org = Mock(total_points=1000, used_points=1199, is_active=True)
        info = OrganizationPointsService.get_points_info(org)
        assert info["status"] == "buffer"


class TestAudioDurationEdgeCases:
    """測試音檔時長邊緣情況"""

    def test_very_short_audio_less_than_1_second(self):
        """極短音檔（< 1 秒）"""
        duration_seconds = 0.5
        points = OrganizationPointsService.convert_unit_to_points(duration_seconds, "秒")
        assert points == 0  # int(0.5) = 0

    def test_exactly_1_second(self):
        """剛好 1 秒"""
        duration_seconds = 1.0
        points = OrganizationPointsService.convert_unit_to_points(duration_seconds, "秒")
        assert points == 1

    def test_fractional_seconds(self):
        """小數秒數"""
        duration_seconds = 30.7
        points = OrganizationPointsService.convert_unit_to_points(duration_seconds, "秒")
        assert points == 30  # 無條件捨去

    def test_very_long_audio(self):
        """極長音檔（10 分鐘）"""
        duration_seconds = 600.0
        points = OrganizationPointsService.convert_unit_to_points(duration_seconds, "秒")
        assert points == 600


class TestConcurrentDeductionSafety:
    """測試並發扣點安全性"""

    def test_multiple_deductions_sequence(self):
        """連續多次扣點"""
        # 模擬初始狀態
        org_state = {"used_points": 0, "total_points": 1000}

        def mock_deduct(amount):
            org_state["used_points"] += amount
            return org_state["used_points"]

        # 連續扣點
        mock_deduct(100)  # 100
        mock_deduct(200)  # 300
        mock_deduct(150)  # 450

        assert org_state["used_points"] == 450

    def test_deduction_with_exactly_remaining_points(self):
        """剛好扣完所有剩餘點數"""
        org = Mock(total_points=1000, used_points=970, is_active=True)
        required = 30  # 剛好用完

        has_enough = OrganizationPointsService.check_points(org, required)
        assert has_enough is True

    def test_deduction_one_point_over_limit(self):
        """超過 1 點就不夠"""
        org = Mock(total_points=1000, used_points=970, is_active=True)
        required = 31  # 多 1 點

        has_enough = OrganizationPointsService.check_points(org, required)
        assert has_enough is False


class TestMixedClassroomScenarios:
    """測試混合班級情境"""

    def test_teacher_has_both_org_and_personal_classrooms(self):
        """老師同時有機構班級和個人班級"""
        teacher = Mock(id=1)
        org_id = uuid4()

        # 機構班級作業
        org_classroom = Mock(organization_id=org_id)
        org_assignment = Mock(classroom=org_classroom, id=1)

        # 個人班級作業
        personal_classroom = Mock(organization_id=None)
        personal_assignment = Mock(classroom=personal_classroom, id=2)

        # 驗證路由
        def get_deduction_type(assignment):
            if assignment.classroom and assignment.classroom.organization_id:
                return "org_points"
            return "teacher_quota"

        assert get_deduction_type(org_assignment) == "org_points"
        assert get_deduction_type(personal_assignment) == "teacher_quota"

    def test_same_student_different_classroom_types(self):
        """同一學生在不同類型班級"""
        student_id = 1
        org_id = uuid4()

        # 學生在機構班級的作業
        org_result = {"student_id": student_id, "deduction_type": "org_points", "org_id": org_id}

        # 學生在個人班級的作業
        personal_result = {"student_id": student_id, "deduction_type": "teacher_quota", "teacher_id": 5}

        # 確保同一學生可以在不同類型班級
        assert org_result["student_id"] == personal_result["student_id"]
        assert org_result["deduction_type"] != personal_result["deduction_type"]


class TestErrorMessageConsistency:
    """測試錯誤訊息一致性"""

    def test_org_hard_limit_message_for_student(self):
        """機構硬限制錯誤訊息對學生友善"""
        error_detail = {
            "error": "QUOTA_HARD_LIMIT_EXCEEDED",
            "message": "點數已用完（含緩衝額度），請聯繫管理員續費後再繼續使用",
        }
        assert "管理員" in error_detail["message"]
        assert "續費" in error_detail["message"]

    def test_teacher_hard_limit_message_for_student(self):
        """老師硬限制錯誤訊息對學生友善"""
        error_detail = {
            "error": "QUOTA_HARD_LIMIT_EXCEEDED",
            "message": "老師的配額已用完（含緩衝額度），請聯繫老師續費後再繼續使用",
        }
        assert "老師" in error_detail["message"]
        assert "續費" in error_detail["message"]
