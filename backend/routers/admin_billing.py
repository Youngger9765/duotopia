"""Admin billing endpoints for GCP cost monitoring."""

from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
import logging

from models import Teacher
from routers.admin import get_current_admin
from services.billing_service import get_billing_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin-billing"])


@router.get("/billing/summary")
async def get_billing_summary(
    days: int = Query(default=30, ge=1, le=90, description="查詢天數 (1-90)"),
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    取得 GCP 帳單摘要

    **權限**: Admin only

    **參數**:
    - days: 查詢過去 N 天的資料 (預設 30 天)

    **回傳**:
    ```json
    {
        "total_cost": 123.45,
        "period": {"start": "2025-01-01", "end": "2025-01-31"},
        "top_services": [
            {"service": "Cloud Run", "cost": 50.00},
            {"service": "Cloud Storage", "cost": 25.00}
        ],
        "daily_costs": [
            {"date": "2025-01-15", "cost": 4.50}
        ],
        "data_available": true
    }
    ```

    **注意**: 啟用 BigQuery Billing Export 後需等待 24 小時，data_available 才會變成 true
    """
    billing_service = get_billing_service()
    return await billing_service.get_billing_summary(days=days)


@router.get("/billing/service-breakdown")
async def get_service_breakdown(
    service: Optional[str] = Query(
        default=None,
        description="服務名稱 (例: 'Cloud Run', 'Cloud Storage')",
    ),
    days: int = Query(default=30, ge=1, le=90, description="查詢天數 (1-90)"),
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    取得特定服務的費用明細

    **權限**: Admin only

    **參數**:
    - service: 服務名稱（選填，不提供則顯示所有服務）
    - days: 查詢過去 N 天的資料

    **回傳**:
    ```json
    {
        "service": "Cloud Run",
        "total_cost": 50.00,
        "period": {"start": "2025-01-01", "end": "2025-01-31"},
        "daily_breakdown": [
            {"date": "2025-01-15", "cost": 2.50}
        ],
        "sku_breakdown": [
            {"sku": "Cloud Run CPU", "cost": 30.00},
            {"sku": "Cloud Run Memory", "cost": 20.00}
        ],
        "data_available": true
    }
    ```
    """
    billing_service = get_billing_service()
    return await billing_service.get_service_breakdown(service_name=service, days=days)


@router.get("/billing/anomaly-check")
async def check_billing_anomalies(
    threshold_percent: float = Query(
        default=50.0,
        ge=10.0,
        le=500.0,
        description="異常閾值百分比 (預設 50% 增長視為異常)",
    ),
    days: int = Query(default=7, ge=1, le=30, description="比較天數"),
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    檢查帳單異常（與前期比較）

    **權限**: Admin only

    **參數**:
    - threshold_percent: 異常閾值（預設 50%，即增長超過 50% 視為異常）
    - days: 比較天數（預設 7 天）

    **回傳**:
    ```json
    {
        "has_anomaly": true,
        "current_period": {"cost": 100.00, "period": "..."},
        "previous_period": {"cost": 50.00, "period": "..."},
        "increase_percent": 100.0,
        "anomalies": [
            {
                "service": "Cloud Storage",
                "current_cost": 80.00,
                "previous_cost": 10.00,
                "increase_percent": 700.0
            }
        ]
    }
    ```

    **用途**: 檢測類似 11/18 的 GCS 費用異常事件
    """
    billing_service = get_billing_service()

    # 查詢當前期間和前一期間
    current = await billing_service.get_billing_summary(days=days)
    previous = await billing_service.get_billing_summary(days=days * 2)

    if not current.get("data_available") or not previous.get("data_available"):
        return {
            "has_anomaly": False,
            "data_available": False,
            "message": "等待 BigQuery 資料",
        }

    current_cost = current.get("total_cost", 0)

    # 計算前一期間的費用（總費用 - 當前期間）
    total_cost = previous.get("total_cost", 0)
    previous_cost = total_cost - current_cost

    # 避免除以零
    if previous_cost == 0:
        increase_percent = 100.0 if current_cost > 0 else 0.0
    else:
        increase_percent = ((current_cost - previous_cost) / previous_cost) * 100

    has_anomaly = increase_percent > threshold_percent

    # 檢查各服務的異常
    anomalies = []
    current_services = {
        s["service"]: s["cost"] for s in current.get("top_services", [])
    }
    previous_services = {
        s["service"]: s["cost"] for s in previous.get("top_services", [])
    }

    for service, current_service_cost in current_services.items():
        previous_service_cost = previous_services.get(service, 0)

        if previous_service_cost == 0:
            service_increase = 100.0 if current_service_cost > 0 else 0.0
        else:
            service_increase = (
                (current_service_cost - previous_service_cost) / previous_service_cost
            ) * 100

        if service_increase > threshold_percent:
            anomalies.append(
                {
                    "service": service,
                    "current_cost": round(current_service_cost, 2),
                    "previous_cost": round(previous_service_cost, 2),
                    "increase_percent": round(service_increase, 2),
                }
            )

    return {
        "has_anomaly": has_anomaly,
        "current_period": {
            "cost": round(current_cost, 2),
            "period": current.get("period"),
        },
        "previous_period": {
            "cost": round(previous_cost, 2),
            "period": previous.get("period"),
        },
        "increase_percent": round(increase_percent, 2),
        "anomalies": sorted(
            anomalies, key=lambda x: x["increase_percent"], reverse=True
        ),
        "data_available": True,
    }


@router.get("/billing/health")
async def billing_health_check(
    _: Teacher = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    檢查 Billing BigQuery 連線狀態

    **權限**: Admin only

    **回傳**:
    ```json
    {
        "status": "healthy",
        "bigquery_connected": true,
        "tables_available": true,
        "dataset": "duotopia-472708.billing_export"
    }
    ```
    """
    billing_service = get_billing_service()

    try:
        # 嘗試初始化 client
        billing_service._ensure_client()

        if billing_service.client is None:
            return {
                "status": "unhealthy",
                "bigquery_connected": False,
                "error": "Failed to initialize BigQuery client",
            }

        # 檢查表格是否存在
        tables_exist = await billing_service._check_tables_exist()

        return {
            "status": "healthy" if tables_exist else "waiting_for_data",
            "bigquery_connected": True,
            "tables_available": tables_exist,
            "dataset": f"{billing_service.project_id}.{billing_service.dataset_id}",
            "message": "OK" if tables_exist else "等待 GCP 匯出資料（需 24 小時）",
        }

    except Exception as e:
        logger.error(f"Billing health check failed: {e}")
        return {
            "status": "unhealthy",
            "bigquery_connected": False,
            "error": str(e),
        }
