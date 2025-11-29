"""
Performance Monitoring Utilities

Provides query execution time logging, slow query alerts,
and request-level query count tracking.
"""

import time
import logging
from contextlib import contextmanager
from typing import Dict, Any
from sqlalchemy import event
from sqlalchemy.engine import Engine
from fastapi import Request
import contextvars

# Setup logging
logger = logging.getLogger(__name__)

# Context variables for tracking per-request stats
request_query_count = contextvars.ContextVar("request_query_count", default=0)
request_query_time = contextvars.ContextVar("request_query_time", default=0.0)

# Performance thresholds (in seconds)
SLOW_QUERY_THRESHOLD = 0.1  # 100ms
VERY_SLOW_QUERY_THRESHOLD = 0.5  # 500ms


class QueryStats:
    """Container for query statistics"""

    def __init__(self):
        self.count = 0
        self.total_time = 0.0
        self.queries = []

    def add_query(self, statement: str, duration: float):
        """Add a query execution record"""
        self.count += 1
        self.total_time += duration
        self.queries.append({"statement": statement, "duration": duration})

    def get_slow_queries(self, threshold: float = SLOW_QUERY_THRESHOLD):
        """Get queries that exceed the threshold"""
        return [q for q in self.queries if q["duration"] >= threshold]


@contextmanager
def track_query_performance():
    """Context manager to track query performance for a block of code"""
    stats = QueryStats()
    start_time = time.time()

    yield stats

    total_time = time.time() - start_time

    if stats.count > 0:
        logger.info(
            f"Query performance: {stats.count} queries in {total_time:.3f}s "
            f"(avg: {stats.total_time / stats.count:.3f}s per query)"
        )

        slow_queries = stats.get_slow_queries()
        if slow_queries:
            logger.warning(
                f"Detected {len(slow_queries)} slow queries (>{SLOW_QUERY_THRESHOLD}s)"
            )
            for query in slow_queries[:5]:  # Log first 5 slow queries
                logger.warning(
                    f"Slow query ({query['duration']:.3f}s): "
                    f"{query['statement'][:200]}..."
                )


def setup_query_logging(engine: Engine, log_all: bool = False):
    """
    Setup SQLAlchemy event listeners for query logging.

    Args:
        engine: SQLAlchemy engine instance
        log_all: If True, log all queries. If False, only log slow queries.
    """

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        """Record query start time"""
        context._query_start_time = time.time()

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log query execution time"""
        total_time = time.time() - context._query_start_time

        # Update request-level counters
        try:
            current_count = request_query_count.get()
            current_time = request_query_time.get()
            request_query_count.set(current_count + 1)
            request_query_time.set(current_time + total_time)
        except LookupError:
            # Not in request context
            pass

        # Log based on thresholds
        if total_time >= VERY_SLOW_QUERY_THRESHOLD:
            logger.error(
                f"VERY SLOW QUERY ({total_time:.3f}s): {statement[:500]}",
                extra={
                    "duration": total_time,
                    "statement": statement,
                    "parameters": parameters,
                },
            )
        elif total_time >= SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"SLOW QUERY ({total_time:.3f}s): {statement[:500]}",
                extra={
                    "duration": total_time,
                    "statement": statement,
                    "parameters": parameters,
                },
            )
        elif log_all:
            logger.debug(
                f"Query ({total_time:.3f}s): {statement[:200]}",
                extra={"duration": total_time, "statement": statement},
            )


async def performance_logging_middleware(request: Request, call_next):
    """
    FastAPI middleware for logging request performance.

    Tracks:
    - Total request duration
    - Number of database queries per request
    - Total database query time
    - Slow requests (>1s)
    """
    # Reset request-level counters
    request_query_count.set(0)
    request_query_time.set(0.0)

    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Request failed with exception")
        raise
    finally:
        duration = time.time() - start_time
        query_count = request_query_count.get()
        query_time = request_query_time.get()

        # Log request performance
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "duration": f"{duration:.3f}s",
            "query_count": query_count,
            "query_time": f"{query_time:.3f}s",
        }

        # Determine log level based on performance
        if duration >= 2.0:  # Very slow request (>2s)
            logger.error(f"VERY SLOW REQUEST: {log_data}")
        elif duration >= 1.0:  # Slow request (>1s)
            logger.warning(f"SLOW REQUEST: {log_data}")
        elif query_count > 20:  # Many queries (potential N+1)
            logger.warning(f"HIGH QUERY COUNT: {log_data}")
        else:
            logger.info(f"Request: {log_data}")

    return response


def get_request_stats() -> Dict[str, Any]:
    """Get current request statistics"""
    try:
        return {
            "query_count": request_query_count.get(),
            "query_time": request_query_time.get(),
        }
    except LookupError:
        return {"query_count": 0, "query_time": 0.0}
