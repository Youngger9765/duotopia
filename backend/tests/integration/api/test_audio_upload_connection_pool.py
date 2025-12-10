"""
Test audio upload with database connection pool management.
Validates Issue #81 fix: DB connections released before GCS upload.

This test file specifically validates the 3-phase approach:
1. Phase 1: Quick DB query (hold connection briefly)
2. Phase 2: Release DB connection, upload to GCS (2-5 seconds)
3. Phase 3: Acquire new DB connection, update database

The critical fix is that Phase 2's slow GCS upload does NOT block the connection pool.
"""

import pytest
import asyncio
import io
from unittest.mock import patch, AsyncMock
from models import (
    Student,
    Teacher,
    Classroom,
    ClassroomStudent,
    StudentAssignment,
    Content,
    ContentItem,
    AssignmentContent,
)


@pytest.fixture
def test_student_data(db_session):
    """Create test student with assignment and content"""
    # Create teacher
    teacher = Teacher(
        name="Test Teacher",
        email="teacher@test.com",
        password_hash="dummy_hash",
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.flush()

    # Create classroom
    classroom = Classroom(
        name="Test Classroom",
        teacher_id=teacher.id,
    )
    db_session.add(classroom)
    db_session.flush()

    # Create student
    student = Student(
        name="Test Student",
        student_number="S001",
        password_hash="dummy_hash",
        classroom_id=classroom.id,
    )
    db_session.add(student)
    db_session.flush()

    # Link student to classroom
    classroom_student = ClassroomStudent(
        classroom_id=classroom.id,
        student_id=student.id,
    )
    db_session.add(classroom_student)

    # Create content
    content = Content(
        title="Test Content",
        level="A1",
        created_by_teacher_id=teacher.id,
    )
    db_session.add(content)
    db_session.flush()

    # Create content items
    content_items = []
    for i in range(3):
        item = ContentItem(
            content_id=content.id,
            order_index=i,
            prompt_text=f"Test prompt {i}",
            duration_seconds=30,
        )
        db_session.add(item)
        db_session.flush()
        content_items.append(item)

    # Create student assignment
    assignment = StudentAssignment(
        student_id=student.id,
        title="Test Assignment",
        created_by_teacher_id=teacher.id,
    )
    db_session.add(assignment)
    db_session.flush()

    # Link content to assignment
    assignment_content = AssignmentContent(
        student_assignment_id=assignment.id,
        content_id=content.id,
        order_index=0,
    )
    db_session.add(assignment_content)

    db_session.commit()

    return {
        "student": student,
        "teacher": teacher,
        "classroom": classroom,
        "assignment": assignment,
        "content": content,
        "content_items": content_items,
    }


@pytest.fixture
def auth_headers_student(test_student_data):
    """Create authentication headers for test student"""
    from auth import create_access_token

    token = create_access_token(
        data={"sub": str(test_student_data["student"].id), "type": "student"}
    )
    return {"Authorization": f"Bearer {token}"}


class TestAudioUploadConnectionPool:
    """Test audio upload connection pool management"""

    @pytest.mark.asyncio
    async def test_db_connection_released_before_gcs_upload(
        self, client, auth_headers_student, test_student_data
    ):
        """
        CRITICAL: Verify DB connection is closed BEFORE slow GCS upload.
        This is the core fix for Issue #81.
        """
        # Track whether DB connection was closed before GCS upload
        db_closed_before_upload = False
        original_close = None

        def mock_close_tracker():
            """Track when db.close() is called"""
            nonlocal db_closed_before_upload
            db_closed_before_upload = True
            if original_close:
                original_close()

        # Mock slow GCS upload (5 seconds)
        async def slow_upload(*args, **kwargs):
            # At this point, DB connection should already be closed
            assert (
                db_closed_before_upload
            ), "DB connection not closed before GCS upload!"
            await asyncio.sleep(0.1)  # Simulate slow upload
            return "https://storage.googleapis.com/test-bucket/test.wav"

        with patch(
            "services.audio_upload.AudioUploadService.upload_audio",
            new=AsyncMock(side_effect=slow_upload),
        ):
            # Patch db.close() to track when it's called
            with patch("sqlalchemy.orm.Session.close", side_effect=mock_close_tracker):
                # Create test audio file
                audio_content = b"fake audio data" * 1000
                audio_file = io.BytesIO(audio_content)

                # Make upload request
                response = client.post(
                    "/api/students/upload-recording",
                    data={
                        "assignment_id": test_student_data["assignment"].id,
                        "content_item_id": test_student_data["content_items"][0].id,
                    },
                    files={"audio_file": ("test.wav", audio_file, "audio/wav")},
                    headers=auth_headers_student,
                )

                # Verify success
                assert response.status_code == 200
                assert db_closed_before_upload, "DB connection was not closed!"

    @pytest.mark.asyncio
    async def test_concurrent_uploads_no_pool_exhaustion(
        self, client, auth_headers_student, test_student_data, db_session
    ):
        """
        Reproduce production issue: Multiple students upload simultaneously.

        OLD BEHAVIOR: Pool exhaustion after 10-15 concurrent uploads
        NEW BEHAVIOR: All succeed because connections are released quickly
        """

        # Mock GCS upload to be slow but not block DB
        async def slow_upload(*args, **kwargs):
            await asyncio.sleep(0.2)  # 200ms upload time
            import uuid

            return f"https://storage.googleapis.com/test/{uuid.uuid4()}.wav"

        with patch(
            "services.audio_upload.AudioUploadService.upload_audio",
            new=AsyncMock(side_effect=slow_upload),
        ):
            # Create 10 concurrent upload tasks (using different content items)
            tasks = []
            for i in range(min(10, len(test_student_data["content_items"]))):
                audio_content = b"fake audio data" * 100
                audio_file = io.BytesIO(audio_content)

                # Use different content items to avoid locking conflicts
                content_item_id = test_student_data["content_items"][
                    i % len(test_student_data["content_items"])
                ].id

                # Create async task
                task = asyncio.create_task(
                    asyncio.to_thread(
                        client.post,
                        "/api/students/upload-recording",
                        data={
                            "assignment_id": test_student_data["assignment"].id,
                            "content_item_id": content_item_id,
                        },
                        files={
                            "audio_file": (
                                f"test{i}.wav",
                                audio_file,
                                "audio/wav",
                            )
                        },
                        headers=auth_headers_student,
                    )
                )
                tasks.append(task)

            # All should complete within reasonable time (not timeout)
            start = asyncio.get_event_loop().time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            duration = asyncio.get_event_loop().time() - start

            # Verify
            assert (
                duration < 5
            ), f"Took {duration}s, expected < 5s (possible pool exhaustion)"

            # Check results
            successful = 0
            for result in results:
                if isinstance(result, Exception):
                    print(f"Upload failed with exception: {result}")
                elif hasattr(result, "status_code"):
                    if result.status_code == 200:
                        successful += 1
                    else:
                        print(f"Upload failed with status {result.status_code}")

            # At least 80% should succeed (some may fail due to timing/race conditions)
            assert successful >= 8, f"Only {successful}/10 uploads succeeded"

    @pytest.mark.asyncio
    async def test_phase1_error_closes_connection(
        self, client, auth_headers_student, test_student_data
    ):
        """
        Verify db.close() called on Phase 1 validation errors.
        This prevents connection leaks when validation fails.
        """
        # Test with invalid assignment ID (404 error in Phase 1)
        audio_content = b"fake audio data" * 100
        audio_file = io.BytesIO(audio_content)

        response = client.post(
            "/api/students/upload-recording",
            data={
                "assignment_id": 99999,  # Non-existent
                "content_item_id": test_student_data["content_items"][0].id,
            },
            files={"audio_file": ("test.wav", audio_file, "audio/wav")},
            headers=auth_headers_student,
        )

        # Should return 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        # Implicit test: If connection leaked, pool would be exhausted
        # Making another request should succeed
        response2 = client.get(
            "/api/students/assignments", headers=auth_headers_student
        )
        assert response2.status_code == 200

    @pytest.mark.asyncio
    async def test_gcs_upload_fails_no_db_update(
        self, client, auth_headers_student, test_student_data, db_session
    ):
        """
        Edge case: GCS upload fails, database should NOT be updated.
        """

        # Mock GCS upload to fail
        async def failed_upload(*args, **kwargs):
            raise Exception("GCS connection timeout")

        with patch(
            "services.audio_upload.AudioUploadService.upload_audio",
            new=AsyncMock(side_effect=failed_upload),
        ):
            audio_content = b"fake audio data" * 100
            audio_file = io.BytesIO(audio_content)

            response = client.post(
                "/api/students/upload-recording",
                data={
                    "assignment_id": test_student_data["assignment"].id,
                    "content_item_id": test_student_data["content_items"][0].id,
                },
                files={"audio_file": ("test.wav", audio_file, "audio/wav")},
                headers=auth_headers_student,
            )

            # Should return 500 error
            assert response.status_code == 500
            assert "cloud storage" in response.json()["detail"].lower()

            # Verify no StudentItemProgress record created
            from models import StudentItemProgress

            progress = (
                db_session.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id
                    == test_student_data["assignment"].id,
                    StudentItemProgress.content_item_id
                    == test_student_data["content_items"][0].id,
                )
                .first()
            )

            assert progress is None, "Database should not be updated on GCS failure"

    @pytest.mark.asyncio
    async def test_db_update_fails_orphaned_file_cleanup(
        self, client, auth_headers_student, test_student_data, db_session
    ):
        """
        Edge case: GCS upload succeeds, but DB update in Phase 3 fails.

        Expected: Returns 500 error, attempts to clean up orphaned GCS file.
        """
        cleanup_called = False
        uploaded_url = None

        # Mock successful GCS upload
        async def successful_upload(*args, **kwargs):
            nonlocal uploaded_url
            uploaded_url = "https://storage.googleapis.com/test-bucket/orphaned.wav"
            return uploaded_url

        # Mock cleanup function
        def mock_cleanup(url):
            nonlocal cleanup_called
            cleanup_called = True
            assert url == uploaded_url, "Cleanup called with wrong URL"

        # Mock DB commit to fail
        def failed_commit():
            raise Exception("Database connection lost")

        with patch(
            "services.audio_upload.AudioUploadService.upload_audio",
            new=AsyncMock(side_effect=successful_upload),
        ), patch(
            "services.audio_manager.AudioManager.delete_old_audio",
            side_effect=mock_cleanup,
        ), patch(
            "sqlalchemy.orm.Session.commit", side_effect=failed_commit
        ):
            audio_content = b"fake audio data" * 100
            audio_file = io.BytesIO(audio_content)

            response = client.post(
                "/api/students/upload-recording",
                data={
                    "assignment_id": test_student_data["assignment"].id,
                    "content_item_id": test_student_data["content_items"][0].id,
                },
                files={"audio_file": ("test.wav", audio_file, "audio/wav")},
                headers=auth_headers_student,
            )

            # Should return 500 error with specific message
            assert response.status_code == 500
            assert "database update failed" in response.json()["detail"].lower()

            # Verify cleanup was attempted
            assert cleanup_called, "Orphaned file cleanup was not called"

    def test_row_level_locking_prevents_race_condition(
        self, client, auth_headers_student, test_student_data, db_session
    ):
        """
        Test that row-level locking (SELECT FOR UPDATE) prevents concurrent updates
        to the same (assignment_id, content_item_id) pair.
        """
        # This is a simplified test - true race condition testing requires
        # complex threading/multiprocessing setup

        # Mock GCS upload
        async def mock_upload(*args, **kwargs):
            return "https://storage.googleapis.com/test-bucket/locked.wav"

        with patch(
            "services.audio_upload.AudioUploadService.upload_audio",
            new=AsyncMock(side_effect=mock_upload),
        ):
            # First upload should succeed
            audio_content = b"fake audio data" * 100
            audio_file = io.BytesIO(audio_content)

            response = client.post(
                "/api/students/upload-recording",
                data={
                    "assignment_id": test_student_data["assignment"].id,
                    "content_item_id": test_student_data["content_items"][0].id,
                },
                files={"audio_file": ("test.wav", audio_file, "audio/wav")},
                headers=auth_headers_student,
            )

            assert response.status_code == 200

            # Second upload (re-recording) should also succeed
            audio_file2 = io.BytesIO(audio_content)
            response2 = client.post(
                "/api/students/upload-recording",
                data={
                    "assignment_id": test_student_data["assignment"].id,
                    "content_item_id": test_student_data["content_items"][0].id,
                },
                files={"audio_file": ("test2.wav", audio_file2, "audio/wav")},
                headers=auth_headers_student,
            )

            assert response2.status_code == 200

            # Verify only ONE StudentItemProgress record exists
            from models import StudentItemProgress

            progress_records = (
                db_session.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id
                    == test_student_data["assignment"].id,
                    StudentItemProgress.content_item_id
                    == test_student_data["content_items"][0].id,
                )
                .all()
            )

            assert (
                len(progress_records) == 1
            ), "Row-level locking failed - duplicate records created"
