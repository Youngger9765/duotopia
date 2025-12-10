"""
Database and Performance Monitoring for Load Tests
Tracks database connections, query performance, and generates reports.
"""

import logging
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logging.warning("psycopg2 not installed - database monitoring disabled")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseMonitor:
    """
    Monitors database performance during load tests.
    Tracks connections, query times, and locks.
    """

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database monitor.

        Args:
            database_url: PostgreSQL connection string.
                         If None, monitoring is disabled (graceful degradation).
        """
        self.database_url = database_url
        self.enabled = False
        self.connection = None

        if not database_url:
            logger.warning("No database URL provided - monitoring disabled")
            return

        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2 not installed - monitoring disabled")
            return

        try:
            self.connection = psycopg2.connect(database_url)
            self.enabled = True
            logger.info("Database monitoring enabled")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            logger.warning("Database monitoring disabled")

    def __del__(self):
        """Close database connection on cleanup."""
        if self.connection:
            self.connection.close()

    def get_active_connections(self) -> int:
        """
        Get count of active database connections.

        Returns:
            Number of active connections, or -1 if monitoring disabled.
        """
        if not self.enabled:
            return -1

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT count(*)
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND pid != pg_backend_pid()
                """
                )
                result = cursor.fetchone()
                return result[0] if result else 0

        except Exception as e:
            logger.error(f"Failed to get active connections: {e}")
            return -1

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get detailed connection statistics.

        Returns:
            Dict with connection statistics or empty dict if disabled.
        """
        if not self.enabled:
            return {}

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get connection statistics
                cursor.execute(
                    """
                    SELECT
                        count(*) as total_connections,
                        count(*) FILTER (WHERE state = 'active') as active_connections,
                        count(*) FILTER (WHERE state = 'idle') as idle_connections,
                        count(*) FILTER (WHERE state = 'idle in transaction') as idle_in_transaction,
                        count(*) FILTER (WHERE wait_event_type IS NOT NULL) as waiting_connections
                    FROM pg_stat_activity
                    WHERE pid != pg_backend_pid()
                """
                )
                stats = cursor.fetchone()

                return dict(stats) if stats else {}

        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}

    def get_slow_queries(self, min_duration_ms: int = 1000) -> List[Dict[str, Any]]:
        """
        Get currently running slow queries.

        Args:
            min_duration_ms: Minimum query duration in milliseconds.

        Returns:
            List of slow query information.
        """
        if not self.enabled:
            return []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        pid,
                        now() - query_start as duration,
                        state,
                        query
                    FROM pg_stat_activity
                    WHERE state = 'active'
                    AND pid != pg_backend_pid()
                    AND now() - query_start > interval '%s milliseconds'
                    ORDER BY duration DESC
                    LIMIT 10
                """,
                    (min_duration_ms,),
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return []

    def get_lock_info(self) -> List[Dict[str, Any]]:
        """
        Get information about database locks.

        Returns:
            List of lock information.
        """
        if not self.enabled:
            return []

        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        pl.pid,
                        pl.mode,
                        pl.granted,
                        pa.query,
                        pa.state
                    FROM pg_locks pl
                    JOIN pg_stat_activity pa ON pl.pid = pa.pid
                    WHERE pl.pid != pg_backend_pid()
                    ORDER BY pl.granted, pa.query_start
                    LIMIT 20
                """
                )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get lock info: {e}")
            return []

    async def monitor_continuously(
        self, interval_seconds: int = 5, duration_seconds: Optional[int] = None
    ):
        """
        Continuously monitor database and print statistics.

        Args:
            interval_seconds: Time between monitoring checks.
            duration_seconds: Total monitoring duration (None = infinite).
        """
        if not self.enabled:
            logger.warning("Database monitoring is disabled")
            return

        logger.info(f"Starting continuous monitoring (interval: {interval_seconds}s)")

        start_time = time.time()
        iteration = 0

        try:
            while True:
                iteration += 1
                elapsed = time.time() - start_time

                # Check if duration limit reached
                if duration_seconds and elapsed >= duration_seconds:
                    logger.info("Monitoring duration limit reached")
                    break

                # Get statistics
                stats = self.get_connection_stats()
                slow_queries = self.get_slow_queries()

                # Print statistics
                logger.info(
                    f"--- Database Stats (iteration {iteration}, {elapsed:.1f}s) ---"
                )
                logger.info(f"Total connections: {stats.get('total_connections', 0)}")
                logger.info(f"Active:            {stats.get('active_connections', 0)}")
                logger.info(f"Idle:              {stats.get('idle_connections', 0)}")
                logger.info(f"Waiting:           {stats.get('waiting_connections', 0)}")

                if slow_queries:
                    logger.warning(f"Slow queries detected: {len(slow_queries)}")
                    for query_info in slow_queries[:3]:  # Show top 3
                        logger.warning(
                            f"  PID {query_info['pid']}: {query_info['duration']} - "
                            f"{query_info['query'][:80]}..."
                        )

                # Wait before next iteration
                await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")


class PerformanceCollector:
    """
    Collects and aggregates performance metrics from Locust results.
    """

    def __init__(self):
        """Initialize performance collector."""
        self.metrics: List[Dict[str, Any]] = []

    def collect_from_csv(self, stats_csv_path: str) -> bool:
        """
        Load metrics from Locust CSV stats file.

        Args:
            stats_csv_path: Path to results_stats.csv file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            import csv

            with open(stats_csv_path, "r") as f:
                reader = csv.DictReader(f)
                self.metrics = list(reader)

            logger.info(f"Loaded {len(self.metrics)} metric entries from CSV")
            return True

        except FileNotFoundError:
            logger.error(f"CSV file not found: {stats_csv_path}")
            return False
        except Exception as e:
            logger.error(f"Failed to load CSV: {e}")
            return False

    def get_summary_statistics(self) -> Dict[str, Any]:
        """
        Calculate summary statistics from collected metrics.

        Returns:
            Dict with summary statistics.
        """
        if not self.metrics:
            return {}

        # Find the aggregated row (last row or "Aggregated" name)
        aggregated = None
        for row in reversed(self.metrics):
            if row.get("Name") == "Aggregated" or row == self.metrics[-1]:
                aggregated = row
                break

        if not aggregated:
            return {}

        return {
            "total_requests": int(aggregated.get("Request Count", 0)),
            "total_failures": int(aggregated.get("Failure Count", 0)),
            "median_response_ms": float(aggregated.get("Median Response Time", 0)),
            "p95_response_ms": float(aggregated.get("95%", 0)),
            "p99_response_ms": float(aggregated.get("99%", 0)),
            "average_response_ms": float(aggregated.get("Average Response Time", 0)),
            "min_response_ms": float(aggregated.get("Min Response Time", 0)),
            "max_response_ms": float(aggregated.get("Max Response Time", 0)),
            "requests_per_second": float(aggregated.get("Requests/s", 0)),
            "success_rate": self._calculate_success_rate(aggregated),
        }

    def _calculate_success_rate(self, aggregated: Dict[str, Any]) -> float:
        """Calculate success rate percentage."""
        total = int(aggregated.get("Request Count", 0))
        failures = int(aggregated.get("Failure Count", 0))

        if total == 0:
            return 0.0

        return ((total - failures) / total) * 100

    def generate_text_report(self, output_path: Optional[str] = None) -> str:
        """
        Generate a text report of performance metrics.

        Args:
            output_path: Optional file path to save report.

        Returns:
            Report text content.
        """
        summary = self.get_summary_statistics()

        if not summary:
            return "No metrics available"

        # Format report
        report_lines = [
            "=" * 60,
            "LOAD TEST PERFORMANCE REPORT",
            "=" * 60,
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "REQUEST STATISTICS:",
            f"  Total Requests:       {summary['total_requests']:,}",
            f"  Failed Requests:      {summary['total_failures']:,}",
            f"  Success Rate:         {summary['success_rate']:.2f}%",
            f"  Requests per Second:  {summary['requests_per_second']:.2f}",
            "",
            "RESPONSE TIME (ms):",
            f"  Minimum:              {summary['min_response_ms']:.0f}",
            f"  Median (p50):         {summary['median_response_ms']:.0f}",
            f"  Average:              {summary['average_response_ms']:.0f}",
            f"  95th Percentile:      {summary['p95_response_ms']:.0f}",
            f"  99th Percentile:      {summary['p99_response_ms']:.0f}",
            f"  Maximum:              {summary['max_response_ms']:.0f}",
            "",
            "=" * 60,
        ]

        report_text = "\n".join(report_lines)

        # Save to file if requested
        if output_path:
            try:
                Path(output_path).write_text(report_text)
                logger.info(f"Report saved to: {output_path}")
            except Exception as e:
                logger.error(f"Failed to save report: {e}")

        return report_text


def generate_html_summary(results_dir: str) -> bool:
    """
    Generate an HTML summary from load test results.

    Args:
        results_dir: Directory containing results CSV files.

    Returns:
        True if successful, False otherwise.
    """
    try:
        results_path = Path(results_dir)
        stats_csv = results_path / "results_stats.csv"

        if not stats_csv.exists():
            logger.error(f"Stats CSV not found: {stats_csv}")
            return False

        # Collect metrics
        collector = PerformanceCollector()
        collector.collect_from_csv(str(stats_csv))

        # Generate text report
        report_path = results_path / "summary.txt"
        report_text = collector.generate_text_report(str(report_path))

        logger.info(f"Summary report generated: {report_path}")
        print("\n" + report_text)

        return True

    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")
        return False


# Export main classes
__all__ = [
    "DatabaseMonitor",
    "PerformanceCollector",
    "generate_html_summary",
]
