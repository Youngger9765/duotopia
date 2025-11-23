"""Audio Error Query Service - BigQuery Integration"""
import os
from datetime import datetime, timedelta
from google.cloud import bigquery
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Student, Classroom, Teacher, ClassroomStudent

logger = logging.getLogger(__name__)


class AudioErrorQueryService:
    """查詢 BigQuery 中的錄音錯誤日誌"""

    def __init__(self):
        self.client = None
        self._initialized = False

        # 從環境變數讀取專案 ID
        self.project_id = os.getenv("GCP_PROJECT_ID", "duotopia-472708")
        self.table_id = f"{self.project_id}.duotopia_logs.audio_playback_errors"

    def _ensure_client(self):
        """延遲初始化 BigQuery client"""
        if self._initialized and self.client is not None:
            return

        try:
            # 優先使用 Application Default Credentials
            self.client = bigquery.Client(project=self.project_id)
            logger.info(
                f"✅ BigQuery audio error client initialized (project: {self.project_id})"
            )
            logger.info(f"📊 BigQuery table: {self.table_id}")
            self._initialized = True
        except Exception as e:
            logger.error(f"⚠️ BigQuery client initialization failed: {e}")
            self._initialized = False  # 允許重試
            self.client = None

    async def get_error_stats(
        self, days: int = 7, teacher_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        取得錄音錯誤統計資料

        Args:
            days: 查詢天數
            teacher_id: 老師 ID（選填，用於過濾特定老師的資料）

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
        self._ensure_client()

        if self.client is None:
            return {"error": "BigQuery client not available", "data_available": False}

        try:
            # 檢查表格是否存在
            if not await self._check_table_exists():
                logger.info("📊 Audio error logs table not yet available")
                return {
                    "total_errors": 0,
                    "period": {
                        "start": (datetime.now() - timedelta(days=days)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end": datetime.now().strftime("%Y-%m-%d"),
                    },
                    "error_by_type": [],
                    "error_by_date": [],
                    "error_by_browser": [],
                    "data_available": False,
                    "message": "等待錯誤日誌資料",
                }

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 查詢參數設定
            params = [
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            ]

            if teacher_id:
                # Note: 目前 BigQuery table 沒有 teacher_id，暫時跳過
                # 未來可以透過 JOIN student_assignments 取得
                pass

            # 查詢統計資料 - timestamp 欄位在 BigQuery 中是 STRING，需要轉換
            query = f"""
            SELECT
                COUNT(*) as total_errors,
                error_type,
                DATE(CAST(timestamp AS TIMESTAMP)) as error_date,
                browser,
                platform
            FROM `{self.table_id}`
            WHERE CAST(timestamp AS TIMESTAMP) BETWEEN @start_date AND @end_date
            GROUP BY error_type, error_date, browser, platform
            """

            job_config = bigquery.QueryJobConfig(query_parameters=params)
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())

            # 計算總錯誤數
            total_errors = sum(row.total_errors for row in results)

            # 按錯誤類型統計
            error_by_type_dict = {}
            for row in results:
                error_type = row.error_type or "UNKNOWN"
                error_by_type_dict[error_type] = (
                    error_by_type_dict.get(error_type, 0) + row.total_errors
                )

            error_by_type = [
                {"error_type": error_type, "count": count}
                for error_type, count in sorted(
                    error_by_type_dict.items(), key=lambda x: x[1], reverse=True
                )
            ]

            # 按日期統計
            error_by_date_dict = {}
            for row in results:
                date_str = row.error_date.strftime("%Y-%m-%d")
                error_by_date_dict[date_str] = (
                    error_by_date_dict.get(date_str, 0) + row.total_errors
                )

            error_by_date = [
                {"date": date, "count": count}
                for date, count in sorted(error_by_date_dict.items())
            ]

            # 按瀏覽器統計
            error_by_browser_dict = {}
            for row in results:
                browser = row.browser or "Unknown"
                error_by_browser_dict[browser] = (
                    error_by_browser_dict.get(browser, 0) + row.total_errors
                )

            error_by_browser = [
                {"browser": browser, "count": count}
                for browser, count in sorted(
                    error_by_browser_dict.items(), key=lambda x: x[1], reverse=True
                )[:10]
            ]

            return {
                "total_errors": total_errors,
                "period": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                },
                "error_by_type": error_by_type,
                "error_by_date": error_by_date,
                "error_by_browser": error_by_browser,
                "data_available": True,
            }

        except Exception as e:
            logger.error(f"❌ Audio error stats query failed: {e}")
            return {
                "error": str(e),
                "data_available": False,
                "message": "查詢失敗，請檢查 BigQuery 權限",
            }

    async def get_error_list(
        self,
        days: int = 7,
        limit: int = 100,
        offset: int = 0,
        search: Optional[str] = None,
        error_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        取得錄音錯誤詳細列表

        Args:
            days: 查詢天數
            limit: 每頁筆數
            offset: 偏移量
            search: 搜尋關鍵字（搜尋 error_message, audio_url）
            error_type: 錯誤類型過濾

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
        self._ensure_client()

        if self.client is None:
            return {"error": "BigQuery client not available", "data": []}

        try:
            if not await self._check_table_exists():
                return {"total": 0, "data": [], "has_more": False}

            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # 建立查詢條件
            where_clauses = [
                "CAST(timestamp AS TIMESTAMP) BETWEEN @start_date AND @end_date"
            ]
            params = [
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            ]

            if error_type:
                where_clauses.append("error_type = @error_type")
                params.append(
                    bigquery.ScalarQueryParameter("error_type", "STRING", error_type)
                )

            if search:
                where_clauses.append(
                    "(LOWER(error_message) LIKE @search OR LOWER(audio_url) LIKE @search)"
                )
                params.append(
                    bigquery.ScalarQueryParameter(
                        "search", "STRING", f"%{search.lower()}%"
                    )
                )

            where_clause = " AND ".join(where_clauses)

            # 查詢總筆數
            count_query = f"""
            SELECT COUNT(*) as total
            FROM `{self.table_id}`
            WHERE {where_clause}
            """

            job_config = bigquery.QueryJobConfig(query_parameters=params)
            count_job = self.client.query(count_query, job_config=job_config)
            total = list(count_job.result())[0].total

            # 查詢資料列表 - 需要 JOIN PostgreSQL 的學生、班級、老師資料
            # 注意：BigQuery 無法直接 JOIN PostgreSQL，所以我們先查詢 BigQuery 資料，
            # 然後在 Python 中補充學生、班級、老師資訊
            data_query = f"""
            SELECT
                timestamp,
                error_type,
                error_code,
                error_message,
                audio_url,
                audio_size,
                audio_duration,
                content_type,
                user_agent,
                platform,
                browser,
                browser_version,
                device_model,
                is_mobile,
                screen_resolution,
                connection_type,
                student_id,
                assignment_id,
                page_url,
                can_play_webm,
                can_play_mp4,
                load_time_ms
            FROM `{self.table_id}`
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT @limit
            OFFSET @offset
            """

            params.extend(
                [
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                    bigquery.ScalarQueryParameter("offset", "INT64", offset),
                ]
            )

            job_config = bigquery.QueryJobConfig(query_parameters=params)
            data_job = self.client.query(data_query, job_config=job_config)
            rows = list(data_job.result())

            # 收集所有需要查詢的 student_id
            student_ids = [row.student_id for row in rows if row.student_id]

            # 從 PostgreSQL 查詢學生、班級、老師資訊
            student_info_map = {}
            if student_ids:
                student_info_map = await self._fetch_student_info(student_ids)

            # 轉換為字典列表，並補充學生、班級、老師資訊
            data = []
            for row in rows:
                student_info = student_info_map.get(row.student_id, {})
                data.append(
                    {
                        "timestamp": row.timestamp,
                        "error_type": row.error_type,
                        "error_code": row.error_code,
                        "error_message": row.error_message,
                        "audio_url": row.audio_url,
                        "audio_size": row.audio_size,
                        "audio_duration": row.audio_duration,
                        "content_type": row.content_type,
                        "user_agent": row.user_agent,
                        "platform": row.platform,
                        "browser": row.browser,
                        "browser_version": row.browser_version,
                        "device_model": row.device_model,
                        "is_mobile": row.is_mobile,
                        "screen_resolution": row.screen_resolution,
                        "connection_type": row.connection_type,
                        "student_id": row.student_id,
                        "assignment_id": row.assignment_id,
                        "page_url": row.page_url,
                        "can_play_webm": row.can_play_webm,
                        "can_play_mp4": row.can_play_mp4,
                        "load_time_ms": row.load_time_ms,
                        # 新增：學生、班級、老師資訊（含 ID）
                        "student_name": student_info.get("student_name"),
                        "classroom_id": student_info.get("classroom_id"),
                        "classroom_name": student_info.get("classroom_name"),
                        "teacher_id": student_info.get("teacher_id"),
                        "teacher_name": student_info.get("teacher_name"),
                    }
                )

            return {"total": total, "data": data, "has_more": (offset + limit) < total}

        except Exception as e:
            logger.error(f"❌ Audio error list query failed: {e}")
            return {"error": str(e), "data": []}

    async def _check_table_exists(self) -> bool:
        """檢查 BigQuery 表格是否存在"""
        try:
            self.client.get_table(self.table_id)
            return True
        except Exception as e:
            logger.error(f"⚠️ Failed to check table: {e}")
            return False

    async def _fetch_student_info(self, student_ids: List[int]) -> dict:
        """
        從生產環境 Supabase 查詢學生、班級、老師資訊

        ⚠️ 注意：此方法永遠連接到生產環境資料庫，不受當前環境影響
        原因：BigQuery 錯誤日誌是全局的，需要查詢生產環境的學生資料

        Returns:
            {
                student_id: {
                    "student_id": 123,
                    "student_name": "張三",
                    "classroom_id": 456,
                    "classroom_name": "三年一班",
                    "teacher_id": 789,
                    "teacher_name": "李老師"
                }
            }
        """
        try:
            # 🔥 從環境變數讀取生產環境資料庫 URL
            # 在所有環境 (.env.local, .env.staging, .env.production) 都需要設定此變數
            prod_db_url = os.getenv("PROD_DATABASE_POOLER_URL")

            if not prod_db_url:
                logger.error("❌ PROD_DATABASE_POOLER_URL not set in environment")
                return {}

            # 創建生產環境專用連接
            prod_engine = create_engine(
                prod_db_url,
                pool_size=2,
                max_overflow=0,
                pool_pre_ping=True,
            )

            with Session(prod_engine) as db:
                # 查詢學生及其關聯的班級、老師（透過 ClassroomStudent 關聯表）
                stmt = (
                    select(
                        Student.id.label("student_id"),
                        Student.name.label("student_name"),
                        Classroom.id.label("classroom_id"),
                        Classroom.name.label("classroom_name"),
                        Teacher.id.label("teacher_id"),
                        Teacher.name.label("teacher_name"),
                    )
                    .join(
                        ClassroomStudent,
                        Student.id == ClassroomStudent.student_id,
                        isouter=True,
                    )
                    .join(
                        Classroom,
                        ClassroomStudent.classroom_id == Classroom.id,
                        isouter=True,
                    )
                    .join(Teacher, Classroom.teacher_id == Teacher.id, isouter=True)
                    .where(Student.id.in_(student_ids))
                )

                result = db.execute(stmt)
                rows = result.fetchall()

                # 建立 student_id -> info 的 mapping
                student_info_map = {}
                for row in rows:
                    student_info_map[row.student_id] = {
                        "student_id": row.student_id,
                        "student_name": row.student_name,
                        "classroom_id": row.classroom_id,
                        "classroom_name": row.classroom_name,
                        "teacher_id": row.teacher_id,
                        "teacher_name": row.teacher_name,
                    }

                return student_info_map

        except Exception as e:
            logger.error(f"❌ Failed to fetch student info from production DB: {e}")
            return {}


# 單例模式
_audio_error_service = None


def get_audio_error_service() -> AudioErrorQueryService:
    """取得 AudioErrorQueryService 單例"""
    global _audio_error_service
    if _audio_error_service is None:
        _audio_error_service = AudioErrorQueryService()
    return _audio_error_service
