"""
Real-time monitoring for load tests
Tracks database connections, system metrics, and performance
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

from config import MonitoringConfig

logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """Monitor database metrics during load test"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.metrics_history = []
        self.is_monitoring = False

    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def get_connection_stats(self) -> Dict:
        """
        Get current database connection statistics

        Returns:
            Dict with connection pool metrics
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Query active connections
            cursor.execute(
                """
                SELECT
                    count(*) FILTER (WHERE state = 'active') as active,
                    count(*) FILTER (WHERE state = 'idle') as idle,
                    count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                    count(*) as total,
                    max(EXTRACT(EPOCH FROM (now() - query_start))) as max_query_duration
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND pid != pg_backend_pid()
            """
            )

            stats = cursor.fetchone()
            cursor.close()
            conn.close()

            return {
                "timestamp": datetime.now().isoformat(),
                "active_connections": stats["active"] or 0,
                "idle_connections": stats["idle"] or 0,
                "idle_in_transaction": stats["idle_in_transaction"] or 0,
                "total_connections": stats["total"] or 0,
                "max_query_duration_seconds": float(stats["max_query_duration"] or 0),
            }

        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
            }

    def get_slow_queries(self, min_duration_seconds=1.0) -> List[Dict]:
        """
        Get currently running slow queries

        Args:
            min_duration_seconds: Minimum query duration to report

        Returns:
            List of slow query details
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    state,
                    EXTRACT(EPOCH FROM (now() - query_start)) as duration_seconds,
                    query
                FROM pg_stat_activity
                WHERE datname = current_database()
                AND state = 'active'
                AND query NOT LIKE '%%pg_stat_activity%%'
                AND EXTRACT(EPOCH FROM (now() - query_start)) > %s
                ORDER BY query_start
            """,
                (min_duration_seconds,),
            )

            queries = cursor.fetchall()
            cursor.close()
            conn.close()

            return [dict(q) for q in queries]

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def get_lock_waits(self) -> List[Dict]:
        """
        Get queries waiting on locks

        Returns:
            List of lock wait details
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT
                    blocked_locks.pid AS blocked_pid,
                    blocked_activity.usename AS blocked_user,
                    blocking_locks.pid AS blocking_pid,
                    blocking_activity.usename AS blocking_user,
                    blocked_activity.query AS blocked_statement,
                    blocking_activity.query AS blocking_statement,
                    blocked_activity.application_name AS blocked_application
                FROM pg_catalog.pg_locks blocked_locks
                JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                JOIN pg_catalog.pg_locks blocking_locks
                    ON blocking_locks.locktype = blocked_locks.locktype
                    AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                    AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                    AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                    AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                    AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                    AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                    AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                    AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                    AND blocking_locks.pid != blocked_locks.pid
                JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                WHERE NOT blocked_locks.granted
            """
            )

            locks = cursor.fetchall()
            cursor.close()
            conn.close()

            return [dict(lock) for lock in locks]

        except Exception as e:
            logger.error(f"Failed to get lock waits: {e}")
            return []

    async def monitor_continuously(self, interval_seconds=5):
        """
        Continuously monitor database and log metrics

        Args:
            interval_seconds: Time between monitoring checks
        """
        self.is_monitoring = True
        logger.info(f"🔍 Starting database monitoring (interval: {interval_seconds}s)")

        while self.is_monitoring:
            try:
                # Get connection stats
                stats = self.get_connection_stats()
                self.metrics_history.append(stats)

                # Log summary
                if "error" not in stats:
                    logger.info(
                        f"📊 DB Connections: {stats['active_connections']} active, "
                        f"{stats['idle_connections']} idle, "
                        f"{stats['total_connections']} total"
                    )

                    # Check for slow queries
                    slow_queries = self.get_slow_queries(min_duration_seconds=5.0)
                    if slow_queries:
                        logger.warning(f"⚠️ {len(slow_queries)} slow queries detected")
                        for query in slow_queries[:3]:  # Log first 3
                            logger.warning(
                                f"   PID {query['pid']}: {query['duration_seconds']:.2f}s - "
                                f"{query['query'][:100]}"
                            )

                    # Check for lock waits
                    lock_waits = self.get_lock_waits()
                    if lock_waits:
                        logger.error(f"🔒 {len(lock_waits)} lock waits detected!")
                        for lock in lock_waits[:3]:
                            logger.error(
                                f"   PID {lock['blocked_pid']} blocked by {lock['blocking_pid']}"
                            )

                else:
                    logger.error(f"❌ Monitoring error: {stats['error']}")

            except Exception as e:
                logger.error(f"Monitoring exception: {e}")

            await asyncio.sleep(interval_seconds)

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.is_monitoring = False
        logger.info("🛑 Stopping database monitoring")

    def save_metrics(self, filename: str):
        """
        Save collected metrics to file

        Args:
            filename: Output filename
        """
        output_path = os.path.join(MonitoringConfig.RESULTS_DIR, filename)
        os.makedirs(MonitoringConfig.RESULTS_DIR, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.metrics_history, f, indent=2)

        logger.info(f"💾 Metrics saved to: {output_path}")

    def get_summary(self) -> Dict:
        """
        Get summary statistics from collected metrics

        Returns:
            Dict with summary stats
        """
        if not self.metrics_history:
            return {"error": "No metrics collected"}

        # Filter out error entries
        valid_metrics = [m for m in self.metrics_history if "error" not in m]

        if not valid_metrics:
            return {"error": "No valid metrics collected"}

        # Calculate statistics
        active_conns = [m["active_connections"] for m in valid_metrics]
        total_conns = [m["total_connections"] for m in valid_metrics]
        max_durations = [m["max_query_duration_seconds"] for m in valid_metrics]

        return {
            "duration_seconds": len(valid_metrics) * MonitoringConfig.DB_QUERY_INTERVAL,
            "samples": len(valid_metrics),
            "connections": {
                "max_active": max(active_conns),
                "avg_active": sum(active_conns) / len(active_conns),
                "max_total": max(total_conns),
                "avg_total": sum(total_conns) / len(total_conns),
            },
            "query_duration": {
                "max_seconds": max(max_durations),
                "avg_seconds": sum(max_durations) / len(max_durations),
            },
        }


class PerformanceMonitor:
    """Monitor API performance metrics"""

    def __init__(self):
        self.requests = []
        self.errors = []

    def record_request(
        self,
        endpoint: str,
        method: str,
        duration: float,
        status_code: int,
        success: bool,
    ):
        """Record a request"""
        self.requests.append(
            {
                "timestamp": datetime.now().isoformat(),
                "endpoint": endpoint,
                "method": method,
                "duration": duration,
                "status_code": status_code,
                "success": success,
            }
        )

        if not success:
            self.errors.append(self.requests[-1])

    def get_statistics(self) -> Dict:
        """Calculate performance statistics"""
        if not self.requests:
            return {"error": "No requests recorded"}

        durations = [r["duration"] for r in self.requests]
        durations.sort()

        total_requests = len(self.requests)
        successful_requests = sum(1 for r in self.requests if r["success"])
        failed_requests = total_requests - successful_requests

        # Calculate percentiles
        def percentile(data, p):
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate_percent": (successful_requests / total_requests * 100)
            if total_requests > 0
            else 0,
            "latency": {
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
                "p50": percentile(durations, 50),
                "p95": percentile(durations, 95),
                "p99": percentile(durations, 99),
            },
            "errors_by_code": self._group_errors_by_code(),
        }

    def _group_errors_by_code(self) -> Dict:
        """Group errors by status code"""
        error_codes = {}
        for error in self.errors:
            code = error["status_code"]
            error_codes[code] = error_codes.get(code, 0) + 1
        return error_codes

    def save_results(self, filename: str):
        """Save performance results"""
        output_path = os.path.join(MonitoringConfig.RESULTS_DIR, filename)
        os.makedirs(MonitoringConfig.RESULTS_DIR, exist_ok=True)

        results = {
            "statistics": self.get_statistics(),
            "raw_data": self.requests if MonitoringConfig.SAVE_RAW_DATA else [],
        }

        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"💾 Performance results saved to: {output_path}")
