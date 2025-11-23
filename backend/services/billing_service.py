"""GCP Billing 查詢服務 - BigQuery Integration"""
import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BillingService:
    """GCP Billing 資料查詢服務（基於 BigQuery）"""

    def __init__(self):
        self.client = None
        self._initialized = False

        # 從環境變數讀取專案 ID
        self.project_id = os.getenv("GCP_PROJECT_ID", "duotopia-472708")
        self.dataset_id = "billing_export"

        # BigQuery 表格名稱（需等 24 小時後自動生成）
        self.standard_table_pattern = (
            f"{self.project_id}.{self.dataset_id}.gcp_billing_export_resource_v1_*"
        )
        self.detailed_table_pattern = (
            f"{self.project_id}.{self.dataset_id}.gcp_billing_export_v1_*"
        )

    def _ensure_client(self):
        """延遲初始化 BigQuery client"""
        if self._initialized and self.client is not None:
            return

        try:
            # 優先使用 Application Default Credentials（本機 + Cloud Run）
            self.client = bigquery.Client(project=self.project_id)
            logger.info(
                f"✅ BigQuery billing client initialized (project: {self.project_id})"
            )
            logger.info(f"📊 BigQuery dataset: {self.project_id}.{self.dataset_id}")
            self._initialized = True
        except Exception as e:
            logger.error(f"⚠️ BigQuery client initialization failed: {e}")
            self._initialized = False  # 允許重試
            self.client = None

    async def get_billing_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        取得帳單摘要（過去 N 天）

        Returns:
            {
                "total_cost": 123.45,
                "period": {"start": "2025-01-01", "end": "2025-01-31"},
                "top_services": [
                    {"service": "Cloud Run", "cost": 50.00},
                    {"service": "Cloud Storage", "cost": 25.00}
                ],
                "daily_costs": [
                    {"date": "2025-01-15", "cost": 4.50},
                    ...
                ],
                "data_available": true
            }
        """
        self._ensure_client()

        if self.client is None:
            return {"error": "BigQuery client not available", "data_available": False}

        try:
            # 檢查表格是否存在（data_available）
            tables_exist = await self._check_tables_exist()
            if not tables_exist:
                logger.info(
                    "📊 Billing tables not yet available (waiting for GCP export)"
                )
                return {
                    "total_cost": 0.0,
                    "period": {
                        "start": (datetime.now() - timedelta(days=days)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": datetime.now().strftime("%Y-%m-%d"),
                    },
                    "top_services": [],
                    "daily_costs": [],
                    "data_available": False,
                    "message": "等待 GCP 匯出資料（啟用後需 24 小時）",
                }

            # 查詢過去 N 天的總費用
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            query = f"""
            SELECT
                SUM(cost) as total_cost,
                service.description as service_name,
                DATE(usage_start_time) as usage_date
            FROM `{self.standard_table_pattern}`
            WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
            GROUP BY service_name, usage_date
            ORDER BY total_cost DESC
            """

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "start_date", "DATE", start_date.date()
                    ),
                    bigquery.ScalarQueryParameter("end_date", "DATE", end_date.date()),
                ]
            )

            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            # 計算總費用
            total_cost = sum(row.total_cost or 0 for row in results)

            # Top 服務
            service_costs = {}
            for row in results:
                service = row.service_name or "Unknown"
                service_costs[service] = service_costs.get(service, 0) + (
                    row.total_cost or 0
                )

            top_services = [
                {"service": service, "cost": round(cost, 2)}
                for service, cost in sorted(
                    service_costs.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            # 每日費用
            daily_costs_dict = {}
            for row in results:
                date_str = row.usage_date.strftime("%Y-%m-%d")
                daily_costs_dict[date_str] = daily_costs_dict.get(date_str, 0) + (
                    row.total_cost or 0
                )

            daily_costs = [
                {"date": date, "cost": round(cost, 2)}
                for date, cost in sorted(daily_costs_dict.items())
            ]

            return {
                "total_cost": round(total_cost, 2),
                "period": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                "top_services": top_services,
                "daily_costs": daily_costs,
                "data_available": True,
            }

        except Exception as e:
            logger.error(f"❌ Billing query failed: {e}")
            return {
                "error": str(e),
                "data_available": False,
                "message": "查詢失敗，請檢查 BigQuery 權限",
            }

    async def get_service_breakdown(
        self, service_name: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        取得服務費用明細

        Args:
            service_name: 服務名稱（例："Cloud Run", "Cloud Storage"）
            days: 查詢天數

        Returns:
            {
                "service": "Cloud Run",
                "total_cost": 50.00,
                "period": {...},
                "daily_breakdown": [...],
                "sku_breakdown": [...]
            }
        """
        self._ensure_client()

        if self.client is None:
            return {"error": "BigQuery client not available"}

        try:
            tables_exist = await self._check_tables_exist()
            if not tables_exist:
                return {
                    "service": service_name or "All",
                    "total_cost": 0.0,
                    "data_available": False,
                    "message": "等待 GCP 匯出資料",
                }

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 根據 service_name 決定 WHERE 條件
            service_filter = ""
            params = [
                bigquery.ScalarQueryParameter("start_date", "DATE", start_date.date()),
                bigquery.ScalarQueryParameter("end_date", "DATE", end_date.date()),
            ]

            if service_name:
                service_filter = "AND service.description = @service_name"
                params.append(
                    bigquery.ScalarQueryParameter(
                        "service_name", "STRING", service_name
                    )
                )

            query = f"""
            SELECT
                service.description as service_name,
                sku.description as sku_name,
                SUM(cost) as total_cost,
                DATE(usage_start_time) as usage_date
            FROM `{self.detailed_table_pattern}`
            WHERE DATE(usage_start_time) BETWEEN @start_date AND @end_date
            {service_filter}
            GROUP BY service_name, sku_name, usage_date
            ORDER BY total_cost DESC
            """

            job_config = bigquery.QueryJobConfig(query_parameters=params)
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            total_cost = sum(row.total_cost or 0 for row in results)

            # SKU breakdown
            sku_costs = {}
            for row in results:
                sku = row.sku_name or "Unknown"
                sku_costs[sku] = sku_costs.get(sku, 0) + (row.total_cost or 0)

            sku_breakdown = [
                {"sku": sku, "cost": round(cost, 2)}
                for sku, cost in sorted(
                    sku_costs.items(), key=lambda x: x[1], reverse=True
                )[:20]
            ]

            # Daily breakdown
            daily_breakdown = {}
            for row in results:
                date_str = row.usage_date.strftime("%Y-%m-%d")
                daily_breakdown[date_str] = daily_breakdown.get(date_str, 0) + (
                    row.total_cost or 0
                )

            daily_costs = [
                {"date": date, "cost": round(cost, 2)}
                for date, cost in sorted(daily_breakdown.items())
            ]

            return {
                "service": service_name or "All Services",
                "total_cost": round(total_cost, 2),
                "period": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                "daily_breakdown": daily_costs,
                "sku_breakdown": sku_breakdown,
                "data_available": True,
            }

        except Exception as e:
            logger.error(f"❌ Service breakdown query failed: {e}")
            return {"error": str(e), "data_available": False}

    async def _check_tables_exist(self) -> bool:
        """檢查 BigQuery 表格是否存在"""
        try:
            # 檢查 dataset 中是否有表格
            dataset_ref = self.client.dataset(self.dataset_id)
            tables = list(self.client.list_tables(dataset_ref))

            # 檢查是否有以 gcp_billing_export 開頭的表格
            billing_tables = [
                t for t in tables if t.table_id.startswith("gcp_billing_export")
            ]

            logger.info(
                f"📊 Found {len(billing_tables)} billing tables in {self.dataset_id}"
            )
            return len(billing_tables) > 0

        except Exception as e:
            logger.error(f"⚠️ Failed to check tables: {e}")
            return False


# 單例模式
_billing_service = None


def get_billing_service() -> BillingService:
    """取得 BillingService 單例"""
    global _billing_service
    if _billing_service is None:
        _billing_service = BillingService()
    return _billing_service
