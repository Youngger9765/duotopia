"""
測試配額緩衝機制 (Quota Buffer with Hard Limit)

測試目標：
1. ✅ 基本配額內正常使用
2. ⚠️ 超過基本配額但在緩衝區內（允許使用）
3. ❌ 超過硬限制（拒絕使用）
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import Teacher, SubscriptionPeriod
from services.quota_service import QuotaService
from auth import get_password_hash
from fastapi import HTTPException


@pytest.fixture
def teacher_with_quota(db_session: Session):
    """創建有配額的老師"""
    teacher = Teacher(
        email="quota_test@test.com",
        password_hash=get_password_hash("test123"),
        name="配額測試老師",
        email_verified=True,
        is_active=True,
    )
    db_session.add(teacher)
    db_session.flush()

    # 創建訂閱週期 - 配額 1000 秒
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=299,
        quota_total=1000,  # 基本配額 1000 秒
        quota_used=0,
        start_date=datetime.now(timezone.utc),
        end_date=datetime.now(timezone.utc) + timedelta(days=30),
        payment_method="manual",
        payment_status="paid",
        status="active",
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(teacher)
    return teacher


class TestQuotaBuffer:
    """測試配額緩衝機制"""

    def test_01_normal_usage_within_quota(self, db_session, teacher_with_quota):
        """✅ 測試 1：基本配額內正常使用"""
        teacher = teacher_with_quota
        period = teacher.current_period

        # 使用 500 秒（配額內）
        QuotaService.deduct_quota(
            db=db_session,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_assessment",
            unit_count=500,
            unit_type="秒",
        )

        db_session.refresh(period)
        assert period.quota_used == 500
        assert period.quota_total == 1000

    def test_02_buffer_zone_usage(self, db_session, teacher_with_quota):
        """⚠️ 測試 2：超過基本配額但在緩衝區內（允許使用）"""
        teacher = teacher_with_quota
        period = teacher.current_period

        # 先用掉 1000 秒（到達基本配額上限）
        period.quota_used = 1000
        db_session.commit()

        # 再使用 100 秒（進入緩衝區）
        # 緩衝區：1000 * 0.20 = 200 秒
        # 當前：1000 → 1100（在緩衝區內）
        QuotaService.deduct_quota(
            db=db_session,
            teacher=teacher,
            student_id=None,
            assignment_id=None,
            feature_type="speech_assessment",
            unit_count=100,
            unit_type="秒",
        )

        db_session.refresh(period)
        assert period.quota_used == 1100  # 允許使用
        assert period.quota_used > period.quota_total  # 超過基本配額

    def test_03_hard_limit_exceeded(self, db_session, teacher_with_quota):
        """❌ 測試 3：超過硬限制（拒絕使用）"""
        teacher = teacher_with_quota
        period = teacher.current_period

        # 用掉 1200 秒（已在緩衝區）
        # 硬限制：1000 * 1.20 = 1200 秒
        period.quota_used = 1200
        db_session.commit()

        # 嘗試再使用 1 秒（超過硬限制）
        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db_session,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=1,
                unit_type="秒",
            )

        # 驗證錯誤訊息
        assert exc_info.value.status_code == 402
        error_detail = exc_info.value.detail
        assert error_detail["error"] == "QUOTA_HARD_LIMIT_EXCEEDED"
        assert "老師的配額已用完" in error_detail["message"]
        assert error_detail["quota_total"] == 1000
        assert error_detail["quota_limit"] == 1200
        assert error_detail["buffer_percentage"] == 20

    def test_04_buffer_calculation(self, db_session):
        """📊 測試 4：驗證不同配額的緩衝計算"""
        test_cases = [
            (1000, 1200),  # 1000 秒 → 1200 秒
            (2000, 2400),  # 2000 秒 → 2400 秒
            (6000, 7200),  # 6000 秒 → 7200 秒
        ]

        for quota_total, expected_limit in test_cases:
            teacher = Teacher(
                email=f"test_{quota_total}@test.com",
                password_hash=get_password_hash("test123"),
                name="測試老師",
                email_verified=True,
                is_active=True,
            )
            db_session.add(teacher)
            db_session.flush()

            period = SubscriptionPeriod(
                teacher_id=teacher.id,
                plan_name="Test Plan",
                amount_paid=0,
                quota_total=quota_total,
                quota_used=0,
                start_date=datetime.now(timezone.utc),
                end_date=datetime.now(timezone.utc) + timedelta(days=30),
                payment_method="manual",
                payment_status="paid",
                status="active",
            )
            db_session.add(period)
            db_session.commit()

            # 用到硬限制
            period.quota_used = expected_limit
            db_session.commit()

            # 嘗試超過硬限制
            with pytest.raises(HTTPException) as exc_info:
                QuotaService.deduct_quota(
                    db=db_session,
                    teacher=teacher,
                    student_id=None,
                    assignment_id=None,
                    feature_type="speech_assessment",
                    unit_count=1,
                    unit_type="秒",
                )

            error_detail = exc_info.value.detail
            assert error_detail["quota_limit"] == expected_limit

    def test_05_buffer_zone_exhaustion(self, db_session, teacher_with_quota):
        """⚠️ 測試 5：逐步耗盡緩衝區"""
        teacher = teacher_with_quota
        period = teacher.current_period

        # 用掉基本配額
        period.quota_used = 1000
        db_session.commit()

        # 緩衝區可用 200 秒
        # 分批使用：50 + 50 + 50 + 50 = 200 秒
        for i in range(4):
            QuotaService.deduct_quota(
                db=db_session,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=50,
                unit_type="秒",
            )
            db_session.refresh(period)
            expected_used = 1000 + (i + 1) * 50
            assert period.quota_used == expected_used

        # 緩衝區用完（1200 秒）
        assert period.quota_used == 1200

        # 嘗試再使用 1 秒 → 應被拒絕
        with pytest.raises(HTTPException) as exc_info:
            QuotaService.deduct_quota(
                db=db_session,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_assessment",
                unit_count=1,
                unit_type="秒",
            )

        assert exc_info.value.status_code == 402
