"""
配額管理服務 - 統一處理配額扣除與記錄

核心功能：
1. 扣除配額 (deduct_quota)
2. 檢查配額是否足夠 (check_quota)
3. 記錄使用明細 (log_usage)
4. 單位換算 (convert_unit_to_seconds)
"""

from sqlalchemy.orm import Session
from models import Teacher, PointUsageLog
from fastapi import HTTPException
from typing import Optional, Dict, Any


class QuotaService:
    """配額管理服務"""

    # ========== 單位換算規則 ==========
    # 基準：所有配額以「秒」為單位
    UNIT_CONVERSION = {
        "秒": 1,  # 1 秒 = 1 秒
        "字": 0.1,  # 1 字 = 0.1 秒 (500 字 = 50 秒)
        "張": 10,  # 1 張圖 = 10 秒
        "分鐘": 60,  # 1 分鐘 = 60 秒
    }

    @staticmethod
    def convert_unit_to_seconds(unit_count: float, unit_type: str) -> int:
        """
        將不同單位換算為秒數

        Args:
            unit_count: 單位數量 (30, 500, 1)
            unit_type: 單位類型 ("秒", "字", "張", "分鐘")

        Returns:
            秒數 (int)

        Examples:
            convert_unit_to_seconds(30, "秒") -> 30
            convert_unit_to_seconds(500, "字") -> 50
            convert_unit_to_seconds(2, "張") -> 20
        """
        if unit_type not in QuotaService.UNIT_CONVERSION:
            raise ValueError(f"不支援的單位類型: {unit_type}")

        seconds = int(unit_count * QuotaService.UNIT_CONVERSION[unit_type])
        return seconds

    @staticmethod
    def check_quota(teacher: Teacher, required_seconds: int) -> bool:
        """
        檢查配額是否足夠

        Args:
            teacher: 教師物件
            required_seconds: 需要的秒數

        Returns:
            True if 配額足夠
        """
        current_period = teacher.current_period
        if not current_period:
            return False

        remaining = current_period.quota_total - current_period.quota_used
        return remaining >= required_seconds

    @staticmethod
    def get_quota_info(teacher: Teacher) -> Dict[str, Any]:
        """
        取得配額資訊

        Returns:
            {
                "quota_total": 1800,
                "quota_used": 500,
                "quota_remaining": 1300,
                "status": "active"
            }
        """
        current_period = teacher.current_period
        if not current_period:
            return {
                "quota_total": 0,
                "quota_used": 0,
                "quota_remaining": 0,
                "status": "no_subscription",
            }

        return {
            "quota_total": current_period.quota_total,
            "quota_used": current_period.quota_used,
            "quota_remaining": max(
                0, current_period.quota_total - current_period.quota_used
            ),
            "status": current_period.status,
        }

    @staticmethod
    def deduct_quota(
        db: Session,
        teacher: Teacher,
        student_id: Optional[int],
        assignment_id: Optional[int],
        feature_type: str,
        unit_count: float,
        unit_type: str,
        feature_detail: Optional[Dict[str, Any]] = None,
    ) -> PointUsageLog:
        """
        扣除配額並記錄

        Args:
            db: 資料庫 session
            teacher: 教師物件
            student_id: 學生 ID (optional)
            assignment_id: 作業 ID (optional)
            feature_type: 功能類型 ("speech_recording", "speech_assessment", "text_correction")
            unit_count: 單位數量 (30秒, 500字, 1張)
            unit_type: 單位類型 ("秒", "字", "張")
            feature_detail: 功能詳細資訊 (optional)

        Returns:
            PointUsageLog 記錄

        Raises:
            HTTPException(402): 配額不足
            HTTPException(404): 無有效訂閱
        """
        # 1. 檢查是否有有效訂閱
        current_period = teacher.current_period
        if not current_period:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "NO_SUBSCRIPTION",
                    "message": "您目前沒有有效的訂閱，請先訂閱方案",
                },
            )

        # 2. 換算為秒數
        points_used = QuotaService.convert_unit_to_seconds(unit_count, unit_type)

        # 3. 檢查配額是否足夠
        quota_before = current_period.quota_used
        quota_after = quota_before + points_used
        quota_remaining = current_period.quota_total - quota_after

        if quota_remaining < 0:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "QUOTA_EXCEEDED",
                    "message": f"配額不足！還需要 {abs(quota_remaining)} 秒",
                    "quota_total": current_period.quota_total,
                    "quota_used": quota_before,
                    "quota_remaining": max(
                        0, current_period.quota_total - quota_before
                    ),
                    "required": points_used,
                },
            )

        # 4. 扣除配額
        current_period.quota_used = quota_after

        # 5. 記錄使用明細
        usage_log = PointUsageLog(
            subscription_period_id=current_period.id,
            teacher_id=teacher.id,
            student_id=student_id,
            assignment_id=assignment_id,
            feature_type=feature_type,
            feature_detail=feature_detail or {},
            points_used=points_used,
            quota_before=quota_before,
            quota_after=quota_after,
            unit_count=unit_count,
            unit_type=unit_type,
        )
        db.add(usage_log)

        # 6. Commit
        db.commit()
        db.refresh(usage_log)

        return usage_log


# ============ 使用範例 ============
if __name__ == "__main__":
    print("=" * 70)
    print("🧪 配額服務測試")
    print("=" * 70)

    # 測試單位換算
    print("\n1️⃣ 單位換算測試：")
    test_cases = [
        (30, "秒", 30),
        (500, "字", 50),
        (2, "張", 20),
        (1.5, "分鐘", 90),
    ]

    for count, unit, expected in test_cases:
        result = QuotaService.convert_unit_to_seconds(count, unit)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {count} {unit} = {result} 秒 (預期: {expected})")

    print("\n" + "=" * 70)
