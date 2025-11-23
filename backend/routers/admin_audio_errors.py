"""Admin Audio Error Monitoring API Endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any
import logging

from models import Teacher
from routers.admin import get_current_admin
from services.audio_error_query_service import get_audio_error_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/audio-errors", tags=["admin-audio-errors"])


@router.get("/stats")
async def get_audio_error_stats(
    days: int = Query(7, ge=1, le=90, description="查詢天數 (1-90)"),
    teacher_id: Optional[int] = Query(None, description="過濾特定老師的資料"),
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    取得錄音錯誤統計資料

    Returns:
        {
            "total_errors": 123,
            "period": {"start": "2025-01-01", "end": "2025-01-07"},
            "error_by_type": [
                {"error_type": "DECODE_ERROR", "count": 50},
                {"error_type": "NETWORK_ERROR", "count": 30}
            ],
            "error_by_date": [
                {"date": "2025-01-01", "count": 10},
                ...
            ],
            "error_by_browser": [
                {"browser": "Chrome", "count": 80},
                {"browser": "Safari", "count": 40}
            ],
            "data_available": true
        }
    """
    service = get_audio_error_service()
    stats = await service.get_error_stats(days=days, teacher_id=teacher_id)

    logger.info(
        f"📊 Admin requested audio error stats (days={days}, teacher_id={teacher_id})"
    )

    return stats


@router.get("/list")
async def get_audio_error_list(
    days: int = Query(7, ge=1, le=90, description="查詢天數"),
    limit: int = Query(100, ge=1, le=1000, description="每頁筆數"),
    offset: int = Query(0, ge=0, description="偏移量"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    error_type: Optional[str] = Query(None, description="錯誤類型過濾"),
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    取得錄音錯誤詳細列表

    Returns:
        {
            "total": 500,
            "data": [
                {
                    "timestamp": "2025-01-01T10:30:00",
                    "error_type": "DECODE_ERROR",
                    "error_message": "...",
                    "student_id": 123,
                    "assignment_id": 456,
                    "audio_url": "...",
                    "browser": "Chrome",
                    "platform": "macOS",
                    ...
                }
            ],
            "has_more": true
        }
    """
    service = get_audio_error_service()
    result = await service.get_error_list(
        days=days, limit=limit, offset=offset, search=search, error_type=error_type
    )

    logger.info(
        f"📋 Admin requested audio error list "
        f"(days={days}, limit={limit}, offset={offset}, search={search}, "
        f"error_type={error_type})"
    )

    return result


@router.get("/health")
async def audio_error_health_check(
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    檢查 Audio Error Monitoring 系統健康狀態

    Returns:
        {
            "status": "healthy",
            "bigquery_connected": true,
            "table_available": true,
            "table_id": "duotopia-472708.duotopia_logs.audio_playback_errors",
            "message": "OK"
        }
    """
    service = get_audio_error_service()
    service._ensure_client()

    table_exists = await service._check_table_exists()

    return {
        "status": "healthy" if service.client is not None else "degraded",
        "bigquery_connected": service.client is not None,
        "table_available": table_exists,
        "table_id": service.table_id,
        "message": "OK"
        if service.client is not None
        else "BigQuery client not available",
    }
