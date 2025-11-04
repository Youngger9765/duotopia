"""
QuotaService 單元測試
"""
import pytest
from services.quota_service import QuotaService
from models import Teacher, SubscriptionPeriod, PointUsageLog
from database import SessionLocal
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException


class TestUnitConversion:
    """單位換算測試"""

    def test_seconds_conversion(self):
        """測試秒數換算"""
        assert QuotaService.convert_unit_to_seconds(30, "秒") == 30
        assert QuotaService.convert_unit_to_seconds(60, "秒") == 60

    def test_words_conversion(self):
        """測試字數換算 (1字 = 0.1秒)"""
        assert QuotaService.convert_unit_to_seconds(500, "字") == 50
        assert QuotaService.convert_unit_to_seconds(1000, "字") == 100

    def test_images_conversion(self):
        """測試圖片換算 (1張 = 10秒)"""
        assert QuotaService.convert_unit_to_seconds(2, "張") == 20
        assert QuotaService.convert_unit_to_seconds(5, "張") == 50

    def test_minutes_conversion(self):
        """測試分鐘換算"""
        assert QuotaService.convert_unit_to_seconds(1.5, "分鐘") == 90
        assert QuotaService.convert_unit_to_seconds(2, "分鐘") == 120

    def test_invalid_unit(self):
        """測試無效單位"""
        with pytest.raises(ValueError):
            QuotaService.convert_unit_to_seconds(10, "無效單位")


class TestQuotaCheck:
    """配額檢查測試"""

    def test_check_quota_sufficient(self):
        """測試配額足夠"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        assert teacher is not None

        # 確保有訂閱
        period = teacher.current_period
        if period:
            period.quota_used = 100
            db.commit()

            # 測試：需要 50 秒，應該足夠
            assert QuotaService.check_quota(teacher, 50) is True

        db.close()

    def test_check_quota_insufficient(self):
        """測試配額不足"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        period = teacher.current_period

        if period:
            # 設定已用 1750 秒（總共 1800）
            period.quota_used = 1750
            db.commit()
            db.refresh(teacher)

            # 測試：需要 100 秒，應該不足
            assert QuotaService.check_quota(teacher, 100) is False

        db.close()


class TestQuotaDeduction:
    """配額扣除測試"""

    def test_deduct_quota_success(self):
        """測試成功扣除配額"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        period = teacher.current_period

        if period:
            # 重置配額
            original_used = 0
            period.quota_used = original_used
            db.commit()
            db.refresh(teacher)

            # 扣除 30 秒
            usage_log = QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="speech_recording",
                unit_count=30,
                unit_type="秒",
                feature_detail={"duration": 30},
            )

            # 驗證
            assert usage_log.points_used == 30
            assert usage_log.quota_before == original_used
            assert usage_log.quota_after == original_used + 30

            # 驗證資料庫
            db.refresh(period)
            assert period.quota_used == original_used + 30

        db.close()

    def test_deduct_quota_exceeded(self):
        """測試配額不足時拋出錯誤"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        period = teacher.current_period

        if period:
            # 設定配額幾乎用完
            period.quota_used = period.quota_total - 10
            db.commit()
            db.refresh(teacher)

            # 嘗試扣除 50 秒（超過剩餘配額）
            with pytest.raises(HTTPException) as exc_info:
                QuotaService.deduct_quota(
                    db=db,
                    teacher=teacher,
                    student_id=None,
                    assignment_id=None,
                    feature_type="speech_recording",
                    unit_count=50,
                    unit_type="秒",
                )

            # 驗證錯誤訊息
            assert exc_info.value.status_code == 402
            assert "QUOTA_EXCEEDED" in str(exc_info.value.detail)

        db.close()

    def test_deduct_quota_different_units(self):
        """測試扣除不同單位的配額"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        period = teacher.current_period

        if period:
            # 重置
            period.quota_used = 0
            db.commit()

            # 1. 扣除 500 字（= 50 秒）
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="text_correction",
                unit_count=500,
                unit_type="字",
            )

            db.refresh(period)
            assert period.quota_used == 50

            # 2. 扣除 2 張圖（= 20 秒）
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=None,
                assignment_id=None,
                feature_type="image_correction",
                unit_count=2,
                unit_type="張",
            )

            db.refresh(period)
            assert period.quota_used == 70  # 50 + 20

        db.close()


class TestQuotaInfo:
    """配額資訊測試"""

    def test_get_quota_info(self):
        """測試取得配額資訊"""
        db = SessionLocal()

        teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
        period = teacher.current_period

        if period:
            period.quota_used = 500
            db.commit()
            db.refresh(teacher)

            info = QuotaService.get_quota_info(teacher)

            assert info["quota_total"] in [1800, 4000]
            assert info["quota_used"] == 500
            assert info["quota_remaining"] == info["quota_total"] - 500
            assert info["status"] == "active"

        db.close()
