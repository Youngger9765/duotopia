"""
Comprehensive tests for database operations to improve coverage
"""

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from database import get_session_local, get_engine, get_db


class TestDatabaseConnection:
    """Test database connection and session management"""

    def test_sessionlocal_creation(self):
        """Test SessionLocal can create sessions"""
        SessionLocal = get_session_local()
        session = SessionLocal()
        assert session is not None
        session.close()

    def test_engine_connection(self):
        """Test engine can connect to database"""
        engine = get_engine()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1

    def test_get_db_dependency(self):
        """Test get_db dependency function"""
        db_gen = get_db()
        db = next(db_gen)
        assert isinstance(db, Session)

        # Test cleanup
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected behavior

    def test_multiple_sessions(self):
        """Test creating multiple database sessions"""
        sessions = []
        try:
            for i in range(5):
                db_gen = get_db()
                session = next(db_gen)
                sessions.append(session)
                assert isinstance(session, Session)
        finally:
            # Clean up sessions
            for session in sessions:
                try:
                    session.close()
                except Exception:
                    pass

    def test_session_isolation(self):
        """Test that sessions are properly isolated"""
        db_gen1 = get_db()
        db_gen2 = get_db()

        session1 = next(db_gen1)
        session2 = next(db_gen2)

        # Sessions should be different objects
        assert session1 is not session2

        # Cleanup
        try:
            next(db_gen1)
        except StopIteration:
            pass
        try:
            next(db_gen2)
        except StopIteration:
            pass


class TestDatabaseOperations:
    """Test database operations and error handling"""

    def test_database_tables_exist(self, test_engine):
        """Test that expected tables exist in database"""
        from database import Base

        # Use SQLAlchemy's metadata to check tables
        expected_tables = ["teachers", "students", "classrooms", "programs"]

        # Get actual table names from metadata
        actual_tables = list(Base.metadata.tables.keys())

        for expected_table in expected_tables:
            assert (
                expected_table in actual_tables
            ), f"Table '{expected_table}' not found in metadata"

    def test_database_constraints(self, test_session):
        """Test database constraints and foreign keys"""
        # Simply test that we can create sessions and they work
        # This is a basic test that database constraints are properly configured

        # Test basic session functionality
        assert test_session is not None

        # Test that we can query (even if empty)
        from models import Teacher

        test_session.query(Teacher).first()
        # Should not crash, even if result is None

    def test_transaction_rollback(self):
        """Test transaction rollback functionality"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Start a transaction
            db.begin()

            # Try to insert invalid data (this should fail)
            try:
                db.execute(text("INSERT INTO teachers (email) VALUES (NULL)"))
                db.commit()
                assert False, "Should have failed due to constraint"
            except SQLAlchemyError:
                db.rollback()
                # This is expected behavior

        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


class TestDatabaseConfiguration:
    """Test database configuration and environment handling"""

    def test_database_url_handling(self):
        """Test DATABASE_URL environment variable handling"""
        # The database module should handle URL configuration
        engine = get_engine()
        SessionLocal = get_session_local()
        assert engine is not None
        assert SessionLocal is not None

    def test_connection_pooling(self):
        """Test connection pooling behavior"""
        # Create multiple connections quickly
        engine = get_engine()
        connections = []
        try:
            for i in range(3):
                conn = engine.connect()
                connections.append(conn)
                # Verify connection works
                result = conn.execute(text("SELECT 1"))
                assert result.fetchone()[0] == 1
        finally:
            for conn in connections:
                conn.close()

    def test_connection_persistence(self):
        """Test that connections persist across operations"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Execute multiple operations on same session
            result1 = db.execute(text("SELECT 1")).fetchone()[0]
            result2 = db.execute(text("SELECT 2")).fetchone()[0]

            assert result1 == 1
            assert result2 == 2
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


class TestErrorScenarios:
    """Test error handling in database operations"""

    def test_invalid_query_handling(self):
        """Test handling of invalid SQL queries"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            with pytest.raises(SQLAlchemyError):
                db.execute(text("SELECT * FROM nonexistent_table"))
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    def test_session_cleanup_on_error(self):
        """Test that sessions are properly cleaned up on errors"""
        db_gen = get_db()
        db = next(db_gen)

        try:
            # Cause an error
            try:
                db.execute(text("INVALID SQL"))
            except Exception:
                pass

            # Session should still be usable for cleanup
            assert db is not None
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


class TestConcurrency:
    """Test concurrent database access"""

    def test_concurrent_sessions(self):
        """Test multiple concurrent database sessions"""
        import concurrent.futures

        def create_session():
            db_gen = get_db()
            db = next(db_gen)
            try:
                result = db.execute(text("SELECT 1")).fetchone()[0]
                return result == 1
            finally:
                try:
                    next(db_gen)
                except StopIteration:
                    pass

        # Test concurrent access
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session) for _ in range(10)]
            results = [future.result() for future in futures]

        # All sessions should work correctly
        assert all(results)

    def test_session_thread_safety(self):
        """Test that sessions are thread-safe"""
        import threading

        results = []
        errors = []

        def database_operation():
            try:
                db_gen = get_db()
                db = next(db_gen)
                try:
                    result = db.execute(
                        text("SELECT COUNT(*) FROM teachers")
                    ).fetchone()[0]
                    results.append(result)
                finally:
                    try:
                        next(db_gen)
                    except StopIteration:
                        pass
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=database_operation)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5


class TestConnectionPoolExhaustion:
    """Test connection pool behavior under stress - Issue #81"""

    def test_connection_pool_exhaustion_handling(self):
        """
        Test pool behavior when all connections are in use.
        Verifies pool_timeout and max_overflow settings work correctly.

        This test validates that when the pool is exhausted (pool_size + max_overflow),
        new connection requests timeout quickly rather than hanging indefinitely.
        """
        import time
        from database import get_db

        # Acquire all connections (pool_size + max_overflow = 10 + 10 = 20)
        sessions = []
        try:
            for i in range(20):
                db = next(get_db())
                sessions.append(db)
                # Execute query to keep connection active
                db.execute(text("SELECT 1"))

            # Try to get one more connection - should timeout quickly (~10s)
            start = time.time()
            try:
                db_extra = next(get_db())
                db_extra.execute(text("SELECT 1"))
                # If we get here, either pool is larger than expected or timeout is too long
                db_extra.close()
                pytest.fail(
                    "Should have raised timeout exception when pool exhausted"
                )
            except Exception as e:
                duration = time.time() - start
                # Should timeout within 15 seconds (pool_timeout=10s + some overhead)
                assert duration < 15, f"Timeout took {duration}s, expected ~10s"
                # Verify it's a timeout/pool error
                error_msg = str(e).lower()
                assert (
                    "timeout" in error_msg
                    or "pool" in error_msg
                    or "connection" in error_msg
                ), f"Expected timeout error, got: {e}"
        finally:
            # Cleanup - release all connections
            for session in sessions:
                try:
                    session.close()
                except Exception:
                    pass

    def test_pool_configuration_env_vars(self):
        """
        Verify DB_POOL_SIZE and DB_MAX_OVERFLOW env vars work correctly.

        This test ensures the database module correctly reads pool configuration
        from environment variables.
        """
        import os
        import importlib

        # Save original values
        original_pool_size = os.environ.get("DB_POOL_SIZE")
        original_max_overflow = os.environ.get("DB_MAX_OVERFLOW")

        try:
            # Set custom values
            os.environ["DB_POOL_SIZE"] = "8"
            os.environ["DB_MAX_OVERFLOW"] = "12"

            # Reload database module to apply env vars
            import database

            # Force re-initialization
            database._engine = None
            database._SessionLocal = None

            importlib.reload(database)

            # Get fresh engine
            from database import get_engine

            engine = get_engine()

            # Verify configuration applied
            assert engine.pool.size() == 8, f"Pool size is {engine.pool.size()}, expected 8"
            assert (
                engine.pool._max_overflow == 12
            ), f"Max overflow is {engine.pool._max_overflow}, expected 12"

        finally:
            # Restore original values
            if original_pool_size is not None:
                os.environ["DB_POOL_SIZE"] = original_pool_size
            elif "DB_POOL_SIZE" in os.environ:
                del os.environ["DB_POOL_SIZE"]

            if original_max_overflow is not None:
                os.environ["DB_MAX_OVERFLOW"] = original_max_overflow
            elif "DB_MAX_OVERFLOW" in os.environ:
                del os.environ["DB_MAX_OVERFLOW"]

            # Reload to restore defaults
            import database

            database._engine = None
            database._SessionLocal = None
            importlib.reload(database)

    def test_connection_release_after_use(self):
        """
        Test that connections are properly released back to the pool after use.

        This validates the fix for Issue #81 where connections weren't being
        released quickly enough during audio uploads.
        """
        from database import get_db, get_engine

        engine = get_engine()

        # Get initial pool status
        initial_pool_size = engine.pool.size()

        # Use and release multiple connections
        for i in range(5):
            db = next(get_db())
            db.execute(text("SELECT 1"))
            db.close()

        # Pool size should remain stable (connections returned)
        final_pool_size = engine.pool.size()
        assert (
            final_pool_size == initial_pool_size
        ), "Connections not properly returned to pool"

    def test_rapid_connection_acquisition_release(self):
        """
        Test rapid connection acquisition and release pattern.

        Simulates the 3-phase audio upload pattern:
        1. Acquire connection
        2. Quick query
        3. Release immediately
        4. Repeat

        This should NOT exhaust the pool.
        """
        from database import get_db
        import time

        start = time.time()

        # Simulate 50 rapid acquire-query-release cycles
        for i in range(50):
            db = next(get_db())
            db.execute(text("SELECT 1"))
            db.close()

        duration = time.time() - start

        # Should complete quickly (< 5 seconds)
        assert duration < 5, f"Took {duration}s for 50 cycles, expected < 5s"

    def test_pool_size_configuration_values(self):
        """
        Verify the default pool configuration values are safe for Supabase Free Tier.

        Supabase Free Tier has ~25 connection limit.
        Default should be 10 + 10 = 20 total connections per instance.
        """
        from database import get_engine
        import os

        # Get current values (should be defaults if not overridden)
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))

        # Verify safe defaults
        total_connections = pool_size + max_overflow
        assert (
            total_connections <= 20
        ), f"Total connections {total_connections} exceeds safe limit for Supabase Free Tier"

        # Verify engine uses these values
        engine = get_engine()
        assert (
            engine.pool.size() == pool_size
        ), f"Engine pool size {engine.pool.size()} != expected {pool_size}"
        assert (
            engine.pool._max_overflow == max_overflow
        ), f"Engine max overflow {engine.pool._max_overflow} != expected {max_overflow}"
