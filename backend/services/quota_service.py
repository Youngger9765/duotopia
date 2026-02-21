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
from models.organization import Organization, TeacherOrganization
from fastapi import HTTPException
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


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

    # ========== 配額超額緩衝 ==========
    # 允許超額使用 20% 作為緩衝（給老師續費的時間）
    # 例如：10,000 秒配額 → 最多可用到 12,000 秒
    QUOTA_BUFFER_PERCENTAGE = 0.20

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
    def check_ai_analysis_availability(teacher_id: int, db: Session) -> bool:
        """
        檢查教師是否有 AI 分析額度（舊版：基於教師身份判斷）。
        用於教師端 dashboard 等不需要作業 context 的場景。

        注意：學生端應使用 check_ai_analysis_availability_by_assignment，
        根據作業所屬班級判斷。
        """
        teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
        if not teacher:
            return False

        teacher_org = (
            db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == teacher_id,
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )

        if teacher_org:
            org = (
                db.query(Organization)
                .filter(
                    Organization.id == teacher_org.organization_id,
                    Organization.is_active.is_(True),
                )
                .first()
            )
            if org:
                remaining = org.total_points - org.used_points
                return remaining > 0

        return teacher.quota_remaining > 0

    @staticmethod
    def check_ai_analysis_availability_by_assignment(
        assignment, db: Session
    ) -> bool:
        """
        根據作業所屬的班級判斷是否有 AI 分析額度。
        與 speech_assessment.py 扣點邏輯一致：
        assignment → classroom → classroom_schools → school → organization

        規則：
        - 作業屬於機構班級 → 查機構 remaining_points > 0
        - 作業屬於個人班級 → 查教師 quota_remaining > 0
        """
        if not assignment:
            return True

        teacher = (
            db.query(Teacher).filter(Teacher.id == assignment.teacher_id).first()
        )
        if not teacher:
            return False

        # 透過 classroom → classroom_schools → school → org 判斷
        classroom = assignment.classroom
        org_id = QuotaService._get_org_id_from_classroom(classroom)

        if org_id:
            # 機構班級 → 查機構點數
            org = (
                db.query(Organization)
                .filter(
                    Organization.id == org_id,
                    Organization.is_active.is_(True),
                )
                .first()
            )
            if org:
                remaining = org.total_points - org.used_points
                return remaining > 0
            # org 不 active → fall through 到個人配額

        # 個人班級 → 查教師配額
        return teacher.quota_remaining > 0

    @staticmethod
    def _get_org_id_from_classroom(classroom) -> Optional[str]:
        """
        從 classroom 透過 classroom_schools 關係取得 organization_id。
        與 speech_assessment.py 的 get_organization_id_from_classroom 邏輯一致。
        """
        if not classroom or not classroom.classroom_schools:
            return None

        for cs in classroom.classroom_schools:
            if cs.is_active and cs.school and cs.school.organization_id:
                return str(cs.school.organization_id)

        return None

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

        # 3. 計算配額狀態
        quota_before = current_period.quota_used
        quota_after = quota_before + points_used
        quota_remaining = current_period.quota_total - quota_after

        # 4. 計算硬限制（基本配額 + 20% 緩衝）
        effective_limit = current_period.quota_total * (
            1 + QuotaService.QUOTA_BUFFER_PERCENTAGE
        )
        buffer_amount = (
            current_period.quota_total * QuotaService.QUOTA_BUFFER_PERCENTAGE
        )

        # 5. 檢查是否超過硬限制
        if quota_after > effective_limit:
            # ❌ 超過硬限制，拒絕操作
            over_limit = quota_after - effective_limit
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "QUOTA_HARD_LIMIT_EXCEEDED",
                    "message": "老師的配額已用完（含緩衝額度），請聯繫老師續費後再繼續使用",
                    "quota_used": quota_before,
                    "quota_total": current_period.quota_total,
                    "quota_limit": int(effective_limit),
                    "buffer_percentage": int(
                        QuotaService.QUOTA_BUFFER_PERCENTAGE * 100
                    ),
                    "over_limit": int(over_limit),
                },
            )

        # 6. 檢查是否在緩衝區間（超過基本配額但未超過硬限制）
        if quota_after > current_period.quota_total:
            buffer_used = quota_after - current_period.quota_total
            buffer_remaining = buffer_amount - buffer_used
            logger.warning(
                f"⚠️ Teacher {teacher.id} using buffer quota: "
                f"{int(buffer_used)}s/{int(buffer_amount)}s used, "
                f"{int(buffer_remaining)}s remaining before hard limit"
            )
        elif quota_remaining < 0:
            # 理論上不會進入（上面已經處理超額情況）
            logger.warning(
                f"⚠️ Teacher {teacher.id} quota exceeded: {abs(quota_remaining)}s over limit"
            )

        # 7. 扣除配額
        current_period.quota_used = quota_after

        # 8. 記錄使用明細
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

        # 9. Commit
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
