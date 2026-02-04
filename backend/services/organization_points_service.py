"""
機構點數管理服務 - 統一處理機構點數扣除與記錄

核心功能：
1. 扣除點數 (deduct_points)
2. 檢查點數是否足夠 (check_points)
3. 記錄使用明細 (OrganizationPointsLog)
4. 單位換算 (convert_unit_to_points)

參考: backend/services/quota_service.py (個人老師配額服務)
規格: docs/issues/208-complete-spec.md
"""

from sqlalchemy.orm import Session
from models.organization import Organization, OrganizationPointsLog
from fastapi import HTTPException
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class OrganizationPointsService:
    """機構點數管理服務"""

    # ========== 單位換算規則 ==========
    # 基準：所有配額以「點」為單位
    UNIT_CONVERSION = {
        "秒": 1,  # 1 秒 = 1 點
        "字": 0.1,  # 1 字 = 0.1 點 (10 字 = 1 點)
        "張": 10,  # 1 張圖 = 10 點
        "分鐘": 60,  # 1 分鐘 = 60 點
    }

    # ========== 配額超額緩衝 ==========
    # 允許超額使用 20% 作為緩衝（給機構續費的時間）
    # 例如：10,000 點配額 → 最多可用到 12,000 點
    QUOTA_BUFFER_PERCENTAGE = 0.20

    @staticmethod
    def convert_unit_to_points(unit_count: float, unit_type: str) -> int:
        """
        將不同單位換算為點數

        Args:
            unit_count: 單位數量 (30, 500, 1)
            unit_type: 單位類型 ("秒", "字", "張", "分鐘")

        Returns:
            點數 (int)

        Raises:
            ValueError: 不支援的單位類型

        Examples:
            convert_unit_to_points(30, "秒") -> 30
            convert_unit_to_points(500, "字") -> 50
            convert_unit_to_points(2, "張") -> 20
        """
        if unit_type not in OrganizationPointsService.UNIT_CONVERSION:
            raise ValueError(f"不支援的單位類型: {unit_type}")

        points = int(unit_count * OrganizationPointsService.UNIT_CONVERSION[unit_type])
        return points

    @staticmethod
    def check_points(
        organization: Optional[Organization], required_points: int
    ) -> bool:
        """
        檢查點數是否足夠（不含 buffer，用於事前檢查）

        Args:
            organization: 機構物件
            required_points: 需要的點數

        Returns:
            True if 點數足夠
        """
        if organization is None:
            return False

        if not organization.is_active:
            return False

        remaining = organization.total_points - organization.used_points
        return remaining >= required_points

    @staticmethod
    def get_points_info(organization: Optional[Organization]) -> Dict[str, Any]:
        """
        取得點數資訊

        Returns:
            {
                "total": 10000,
                "used": 5000,
                "remaining": 5000,
                "status": "active" | "warning" | "buffer" | "exhausted" | "no_organization"
            }

        Status definitions:
            - active: < 80% used (正常使用)
            - warning: 80-100% used (即將用完)
            - buffer: 100-120% used (使用緩衝區)
            - exhausted: >= 120% used (已耗盡)
            - no_organization: 無機構
        """
        if organization is None:
            return {
                "total": 0,
                "used": 0,
                "remaining": 0,
                "status": "no_organization",
            }

        total = organization.total_points
        used = organization.used_points
        remaining = max(0, total - used)
        buffer_limit = int(
            total * (1 + OrganizationPointsService.QUOTA_BUFFER_PERCENTAGE)
        )

        # Calculate status based on usage percentage
        if total == 0:
            status = "exhausted"
        elif used >= buffer_limit:
            status = "exhausted"
        elif used > total:
            status = "buffer"
        elif used >= total * 0.8:
            status = "warning"
        else:
            status = "active"

        result = {
            "total": total,
            "used": used,
            "remaining": remaining,
            "status": status,
        }

        # Add buffer_remaining for buffer status
        if status == "buffer":
            result["buffer_remaining"] = buffer_limit - used

        return result

    @staticmethod
    def deduct_points(
        db: Session,
        organization_id: UUID,
        teacher_id: int,
        student_id: Optional[int],
        assignment_id: Optional[int],
        feature_type: str,
        unit_count: float,
        unit_type: str,
        feature_detail: Optional[Dict[str, Any]] = None,
    ) -> OrganizationPointsLog:
        """
        扣除點數並記錄

        Args:
            db: 資料庫 session
            organization_id: 機構 ID
            teacher_id: 教師 ID
            student_id: 學生 ID (optional)
            assignment_id: 作業 ID (optional)
            feature_type: 功能類型 ("speech_assessment", "text_correction", etc.)
            unit_count: 單位數量 (30秒, 500字, 1張)
            unit_type: 單位類型 ("秒", "字", "張", "分鐘")
            feature_detail: 功能詳細資訊 (optional)

        Returns:
            OrganizationPointsLog 記錄

        Raises:
            HTTPException(404): 機構不存在
            HTTPException(402): 機構未啟用或點數超過緩衝限制
        """
        # 1. 查詢機構
        organization = (
            db.query(Organization).filter(Organization.id == organization_id).first()
        )

        if not organization:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "ORGANIZATION_NOT_FOUND",
                    "message": "機構不存在",
                },
            )

        # 2. 檢查機構是否啟用
        if not organization.is_active:
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "ORGANIZATION_INACTIVE",
                    "message": "機構已停用，無法使用點數",
                },
            )

        # 3. 換算為點數
        points_used = OrganizationPointsService.convert_unit_to_points(
            unit_count, unit_type
        )

        # 4. 計算點數狀態
        points_before = organization.used_points
        points_after = points_before + points_used

        # 5. 計算硬限制（基本配額 + 20% 緩衝）
        effective_limit = int(
            organization.total_points
            * (1 + OrganizationPointsService.QUOTA_BUFFER_PERCENTAGE)
        )
        buffer_amount = int(
            organization.total_points
            * OrganizationPointsService.QUOTA_BUFFER_PERCENTAGE
        )

        # 6. 檢查是否超過硬限制
        if points_after > effective_limit:
            # 超過硬限制，拒絕操作
            over_limit = points_after - effective_limit
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "QUOTA_HARD_LIMIT_EXCEEDED",
                    "message": "機構點數已用盡，請聯繫管理員續費",
                    "points_used": points_before,
                    "total_points": organization.total_points,
                    "points_limit": effective_limit,
                    "buffer_percentage": int(
                        OrganizationPointsService.QUOTA_BUFFER_PERCENTAGE * 100
                    ),
                    "over_limit": over_limit,
                },
            )

        # 7. 檢查是否在緩衝區間（超過基本配額但未超過硬限制）
        if points_after > organization.total_points:
            buffer_used = points_after - organization.total_points
            buffer_remaining = buffer_amount - buffer_used
            logger.warning(
                f"Organization {organization_id} using buffer points: "
                f"{buffer_used}/{buffer_amount} used, "
                f"{buffer_remaining} remaining before hard limit"
            )

        # 8. 扣除點數
        organization.used_points = points_after
        organization.last_points_update = datetime.now(timezone.utc)

        # 9. 記錄使用明細
        # Build description from feature_detail if provided
        description = None
        if feature_detail:
            description = f"feature_type={feature_type}, student_id={student_id}, assignment_id={assignment_id}"

        usage_log = OrganizationPointsLog(
            organization_id=organization_id,
            teacher_id=teacher_id,
            points_used=points_used,
            feature_type=feature_type,
            description=description,
        )
        db.add(usage_log)

        # 10. Commit
        db.commit()
        db.refresh(usage_log)

        return usage_log


# ============ 使用範例 ============
if __name__ == "__main__":
    print("=" * 70)
    print("Organization Points Service Test")
    print("=" * 70)

    # 測試單位換算
    print("\n1. Unit Conversion Test:")
    test_cases = [
        (30, "秒", 30),
        (500, "字", 50),
        (2, "張", 20),
        (1.5, "分鐘", 90),
    ]

    for count, unit, expected in test_cases:
        result = OrganizationPointsService.convert_unit_to_points(count, unit)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] {count} {unit} = {result} points (expected: {expected})")

    print("\n" + "=" * 70)

