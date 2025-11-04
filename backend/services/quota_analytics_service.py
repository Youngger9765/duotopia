"""
配額使用統計分析服務

提供配額使用的各種統計分析功能
"""

from sqlalchemy.orm import Session as SessionType
from sqlalchemy import func
from models import Teacher, PointUsageLog, Student, Assignment
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone, timedelta


class QuotaAnalyticsService:
    """配額統計分析服務"""

    @staticmethod
    def get_usage_summary(
        teacher: Teacher, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        取得配額使用統計摘要

        Args:
            teacher: Teacher 物件
            start_date: 起始日期（選填）
            end_date: 結束日期（選填）

        Returns:
            {
                "summary": {
                    "total_used": 800,
                    "total_quota": 1800,
                    "percentage": 44
                },
                "daily_usage": [...],
                "top_students": [...],
                "top_assignments": [...],
                "feature_breakdown": {...}
            }
        """
        session = SessionType.object_session(teacher)
        if not session:
            raise ValueError("Teacher object must be attached to a session")

        # 預設時間範圍：當前週期
        if not start_date and teacher.current_period:
            start_date = teacher.current_period.start_date
        if not end_date:
            end_date = datetime.now(timezone.utc)

        # 取得統計資料
        summary = QuotaAnalyticsService._get_summary(teacher)
        daily_usage = QuotaAnalyticsService._get_daily_usage(
            session, teacher, start_date, end_date
        )
        top_students = QuotaAnalyticsService._get_top_students(
            session, teacher, start_date, end_date
        )
        top_assignments = QuotaAnalyticsService._get_top_assignments(
            session, teacher, start_date, end_date
        )
        feature_breakdown = QuotaAnalyticsService._get_feature_breakdown(
            session, teacher, start_date, end_date
        )

        return {
            "summary": summary,
            "daily_usage": daily_usage,
            "top_students": top_students,
            "top_assignments": top_assignments,
            "feature_breakdown": feature_breakdown,
        }

    @staticmethod
    def _get_summary(teacher: Teacher) -> Dict[str, int]:
        """取得配額使用摘要"""
        period = teacher.current_period
        if not period:
            return {"total_used": 0, "total_quota": 0, "percentage": 0}

        total_used = period.quota_used
        total_quota = period.quota_total
        percentage = int((total_used / total_quota * 100)) if total_quota > 0 else 0

        return {
            "total_used": total_used,
            "total_quota": total_quota,
            "percentage": percentage,
        }

    @staticmethod
    def _get_daily_usage(
        db: SessionType, teacher: Teacher, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """取得每日使用量趨勢"""
        results = (
            db.query(
                func.date(PointUsageLog.created_at).label("date"),
                func.sum(PointUsageLog.points_used).label("seconds"),
            )
            .filter(
                PointUsageLog.teacher_id == teacher.id,
                PointUsageLog.created_at >= start_date,
                PointUsageLog.created_at <= end_date,
            )
            .group_by(func.date(PointUsageLog.created_at))
            .order_by(func.date(PointUsageLog.created_at))
            .all()
        )

        return [
            {"date": str(row.date), "seconds": int(row.seconds or 0)} for row in results
        ]

    @staticmethod
    def _get_top_students(
        db: SessionType,
        teacher: Teacher,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """取得學生使用排行"""
        results = (
            db.query(
                Student.id,
                Student.name,
                func.sum(PointUsageLog.points_used).label("seconds"),
                func.count(PointUsageLog.id).label("count"),
            )
            .join(PointUsageLog, PointUsageLog.student_id == Student.id)
            .filter(
                PointUsageLog.teacher_id == teacher.id,
                PointUsageLog.created_at >= start_date,
                PointUsageLog.created_at <= end_date,
            )
            .group_by(Student.id, Student.name)
            .order_by(func.sum(PointUsageLog.points_used).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "student_id": row.id,
                "name": row.name,
                "seconds": int(row.seconds or 0),
                "count": int(row.count or 0),
            }
            for row in results
        ]

    @staticmethod
    def _get_top_assignments(
        db: SessionType,
        teacher: Teacher,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """取得作業使用排行"""
        results = (
            db.query(
                Assignment.id,
                Assignment.title,
                func.sum(PointUsageLog.points_used).label("seconds"),
                func.count(func.distinct(PointUsageLog.student_id)).label(
                    "student_count"
                ),
            )
            .join(PointUsageLog, PointUsageLog.assignment_id == Assignment.id)
            .filter(
                PointUsageLog.teacher_id == teacher.id,
                PointUsageLog.created_at >= start_date,
                PointUsageLog.created_at <= end_date,
            )
            .group_by(Assignment.id, Assignment.title)
            .order_by(func.sum(PointUsageLog.points_used).desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "assignment_id": row.id,
                "title": row.title,
                "seconds": int(row.seconds or 0),
                "students": int(row.student_count or 0),
            }
            for row in results
        ]

    @staticmethod
    def _get_feature_breakdown(
        db: SessionType, teacher: Teacher, start_date: datetime, end_date: datetime
    ) -> Dict[str, int]:
        """取得功能使用分佈"""
        results = (
            db.query(
                PointUsageLog.feature_type,
                func.sum(PointUsageLog.points_used).label("seconds"),
            )
            .filter(
                PointUsageLog.teacher_id == teacher.id,
                PointUsageLog.created_at >= start_date,
                PointUsageLog.created_at <= end_date,
            )
            .group_by(PointUsageLog.feature_type)
            .all()
        )

        return {row.feature_type: int(row.seconds or 0) for row in results}
