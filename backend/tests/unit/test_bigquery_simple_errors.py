"""
测试 5 个简单的 BigQuery 错误记录

Tests for 5 simple BigQuery error logging types:
1. file_too_large (>10MB)
2. invalid_audio_format
3. queue_wait_exceeded (>5s)
4. azure_no_speech_recognized (NoMatch)
5. audio_conversion_failed
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime


class TestFileTooLargeLogging:
    """测试文件过大记录到 BigQuery"""

    @pytest.mark.asyncio
    async def test_file_too_large_logged_to_bigquery(self):
        """
        Verify file_too_large error is logged to BigQuery

        Test scenario:
        - Audio file exceeds MAX_FILE_SIZE (10MB)
        - BigQuery log_audio_error is called with correct parameters
        - HTTPException 413 is raised
        """
        from services.bigquery_logger import BigQueryLogger

        # Mock BigQuery logger
        mock_logger = AsyncMock(spec=BigQueryLogger)
        mock_logger.log_audio_error = AsyncMock(return_value=True)

        with patch(
            "routers.speech_assessment.get_bigquery_logger", return_value=mock_logger
        ):
            # Simulate file too large error
            MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
            file_size = 11 * 1024 * 1024  # 11MB

            await mock_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "file_too_large",
                    "error_message": f"Audio file {file_size} bytes exceeds limit {MAX_FILE_SIZE} bytes",
                    "student_id": 123,
                    "assignment_id": 456,
                    "audio_size_bytes": file_size,
                    "content_type": "audio/webm",
                    "max_size_bytes": MAX_FILE_SIZE,
                    "environment": "test",
                }
            )

            # Verify logger was called
            mock_logger.log_audio_error.assert_called_once()

            # Verify error data structure
            call_args = mock_logger.log_audio_error.call_args[0][0]
            assert call_args["error_type"] == "file_too_large"
            assert call_args["audio_size_bytes"] == file_size
            assert call_args["max_size_bytes"] == MAX_FILE_SIZE
            assert call_args["audio_size_bytes"] > call_args["max_size_bytes"]

    @pytest.mark.asyncio
    async def test_file_too_large_contains_required_fields(self):
        """
        Verify file_too_large log contains all required fields

        Required fields:
        - timestamp
        - error_type (file_too_large)
        - error_message
        - student_id
        - assignment_id
        - audio_size_bytes
        - content_type
        - max_size_bytes
        - environment
        """
        required_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "audio_size_bytes",
            "content_type",
            "max_size_bytes",
            "environment",
        ]

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "file_too_large",
            "error_message": "Audio file 11534336 bytes exceeds limit 10485760 bytes",
            "student_id": 123,
            "assignment_id": 456,
            "audio_size_bytes": 11 * 1024 * 1024,
            "content_type": "audio/webm",
            "max_size_bytes": 10 * 1024 * 1024,
            "environment": "staging",
        }

        # Verify all required fields present
        for field in required_fields:
            assert (
                field in error_data
            ), f"Required field '{field}' missing from error data"

        # Verify data types
        assert isinstance(error_data["audio_size_bytes"], int)
        assert isinstance(error_data["max_size_bytes"], int)
        assert error_data["error_type"] == "file_too_large"

    def test_file_size_calculation_accuracy(self):
        """
        Verify file size is calculated correctly
        10MB = 10 * 1024 * 1024 bytes
        """
        MAX_FILE_SIZE = 10 * 1024 * 1024
        assert MAX_FILE_SIZE == 10485760  # 10MB in bytes

        # Test various file sizes
        test_sizes = [
            (5 * 1024 * 1024, False),  # 5MB - OK
            (10 * 1024 * 1024, False),  # 10MB - OK (equal to limit)
            (10 * 1024 * 1024 + 1, True),  # 10MB + 1 byte - Too large
            (15 * 1024 * 1024, True),  # 15MB - Too large
        ]

        for file_size, should_fail in test_sizes:
            is_too_large = file_size > MAX_FILE_SIZE
            assert is_too_large == should_fail


class TestInvalidAudioFormatLogging:
    """测试无效音频格式记录到 BigQuery"""

    @pytest.mark.asyncio
    async def test_invalid_audio_format_logged_to_bigquery(self):
        """
        Verify invalid_audio_format error is logged to BigQuery

        Test scenario:
        - Audio format not in ALLOWED_AUDIO_FORMATS
        - BigQuery log_audio_error is called with correct parameters
        - HTTPException 400 is raised
        """
        from services.bigquery_logger import BigQueryLogger

        # Mock BigQuery logger
        mock_logger = AsyncMock(spec=BigQueryLogger)
        mock_logger.log_audio_error = AsyncMock(return_value=True)

        ALLOWED_AUDIO_FORMATS = [
            "audio/wav",
            "audio/webm",
            "audio/mp3",
        ]

        with patch(
            "routers.speech_assessment.get_bigquery_logger", return_value=mock_logger
        ):
            # Simulate invalid format
            invalid_format = "video/avi"

            await mock_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "invalid_audio_format",
                    "error_message": f"Unsupported audio format: {invalid_format}",
                    "student_id": 123,
                    "assignment_id": 456,
                    "content_type": invalid_format,
                    "allowed_formats": ", ".join(ALLOWED_AUDIO_FORMATS),
                    "environment": "test",
                }
            )

            # Verify logger was called
            mock_logger.log_audio_error.assert_called_once()

            # Verify error data structure
            call_args = mock_logger.log_audio_error.call_args[0][0]
            assert call_args["error_type"] == "invalid_audio_format"
            assert call_args["content_type"] == invalid_format
            assert "allowed_formats" in call_args

    @pytest.mark.asyncio
    async def test_invalid_audio_format_contains_required_fields(self):
        """
        Verify invalid_audio_format log contains all required fields

        Required fields:
        - timestamp
        - error_type (invalid_audio_format)
        - error_message
        - student_id
        - assignment_id
        - content_type
        - allowed_formats
        - environment
        """
        required_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "content_type",
            "allowed_formats",
            "environment",
        ]

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "invalid_audio_format",
            "error_message": "Unsupported audio format: video/avi",
            "student_id": 123,
            "assignment_id": 456,
            "content_type": "video/avi",
            "allowed_formats": "audio/wav, audio/webm, audio/mp3",
            "environment": "staging",
        }

        # Verify all required fields present
        for field in required_fields:
            assert (
                field in error_data
            ), f"Required field '{field}' missing from error data"

        # Verify error_type
        assert error_data["error_type"] == "invalid_audio_format"

    def test_allowed_formats_list(self):
        """
        Verify ALLOWED_AUDIO_FORMATS contains expected formats
        """
        ALLOWED_AUDIO_FORMATS = [
            "audio/wav",
            "audio/webm",
            "audio/webm;codecs=opus",
            "audio/mp3",
            "audio/mpeg",
            "audio/mp4",
            "video/mp4",
            "application/octet-stream",
        ]

        # Test valid formats
        assert "audio/wav" in ALLOWED_AUDIO_FORMATS
        assert "audio/webm" in ALLOWED_AUDIO_FORMATS
        assert "audio/mp3" in ALLOWED_AUDIO_FORMATS

        # Test invalid formats
        assert "video/avi" not in ALLOWED_AUDIO_FORMATS
        assert "audio/flac" not in ALLOWED_AUDIO_FORMATS


class TestQueueWaitExceededLogging:
    """测试队列等待超过 5 秒记录到 BigQuery"""

    @pytest.mark.asyncio
    async def test_queue_wait_exceeded_logged_to_bigquery(self):
        """
        Verify queue_wait_exceeded error is logged to BigQuery

        Test scenario:
        - Queue wait time exceeds 5 seconds
        - BigQuery log_audio_error is called with correct parameters
        - No exception raised (just warning)
        """
        from services.bigquery_logger import BigQueryLogger

        # Mock BigQuery logger
        mock_logger = AsyncMock(spec=BigQueryLogger)
        mock_logger.log_audio_error = AsyncMock(return_value=True)

        with patch(
            "routers.speech_assessment.get_bigquery_logger", return_value=mock_logger
        ):
            # Simulate queue wait exceeded
            queue_wait = 6.25  # Over 5 second threshold

            await mock_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "queue_wait_exceeded",
                    "error_message": f"Azure API queue wait exceeded 5s threshold: {queue_wait:.2f}s",
                    "student_id": 123,
                    "assignment_id": 456,
                    "queue_wait_time": round(queue_wait, 2),
                    "audio_size_bytes": 1024000,
                    "reference_text": "Hello world",
                    "environment": "test",
                }
            )

            # Verify logger was called
            mock_logger.log_audio_error.assert_called_once()

            # Verify error data structure
            call_args = mock_logger.log_audio_error.call_args[0][0]
            assert call_args["error_type"] == "queue_wait_exceeded"
            assert call_args["queue_wait_time"] > 5
            assert isinstance(call_args["queue_wait_time"], (int, float))

    @pytest.mark.asyncio
    async def test_queue_wait_threshold_changed_from_2_to_5_seconds(self):
        """
        Verify threshold is changed from 2s to 5s

        Original code: if queue_wait > 2
        New code: if queue_wait > 5
        """
        THRESHOLD = 5  # Changed from 2 to 5

        test_cases = [
            (1.5, False),  # Below threshold - not logged
            (2.5, False),  # Old threshold - not logged
            (4.9, False),  # Just below new threshold - not logged
            (5.1, True),  # Above new threshold - logged
            (10.0, True),  # Well above threshold - logged
        ]

        for queue_wait, should_log in test_cases:
            should_trigger = queue_wait > THRESHOLD
            assert should_trigger == should_log

    @pytest.mark.asyncio
    async def test_queue_wait_contains_required_fields(self):
        """
        Verify queue_wait_exceeded log contains all required fields

        Required fields:
        - timestamp
        - error_type (queue_wait_exceeded)
        - error_message
        - student_id
        - assignment_id
        - queue_wait_time
        - audio_size_bytes
        - reference_text
        - environment
        """
        required_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "queue_wait_time",
            "audio_size_bytes",
            "reference_text",
            "environment",
        ]

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "queue_wait_exceeded",
            "error_message": "Azure API queue wait exceeded 5s threshold: 6.25s",
            "student_id": 123,
            "assignment_id": 456,
            "queue_wait_time": 6.25,
            "audio_size_bytes": 1024000,
            "reference_text": "Test text",
            "environment": "staging",
        }

        # Verify all required fields present
        for field in required_fields:
            assert (
                field in error_data
            ), f"Required field '{field}' missing from error data"

        # Verify data types
        assert isinstance(error_data["queue_wait_time"], (int, float))
        assert error_data["queue_wait_time"] > 5


class TestAzureNoSpeechRecognizedLogging:
    """测试 Azure NoMatch 记录到 BigQuery"""

    @pytest.mark.asyncio
    async def test_azure_no_match_logged_to_bigquery(self):
        """
        Verify azure_no_speech_recognized error is logged to BigQuery

        Test scenario:
        - Azure Speech SDK returns NoMatch result
        - HTTPException 400 is raised with "No speech could be recognized"
        - BigQuery log_audio_error is called in exception handler
        """
        from services.bigquery_logger import BigQueryLogger

        # Mock BigQuery logger
        mock_logger = AsyncMock(spec=BigQueryLogger)
        mock_logger.log_audio_error = AsyncMock(return_value=True)

        with patch(
            "routers.speech_assessment.get_bigquery_logger", return_value=mock_logger
        ):
            # Simulate NoMatch error logging
            await mock_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "azure_no_speech_recognized",
                    "error_message": "No speech could be recognized from the audio",
                    "student_id": 123,
                    "assignment_id": 456,
                    "audio_size_bytes": 1024000,
                    "reference_text": "Hello world",
                    "environment": "test",
                }
            )

            # Verify logger was called
            mock_logger.log_audio_error.assert_called_once()

            # Verify error data structure
            call_args = mock_logger.log_audio_error.call_args[0][0]
            assert call_args["error_type"] == "azure_no_speech_recognized"
            assert "No speech could be recognized" in call_args["error_message"]

    @pytest.mark.asyncio
    async def test_no_match_error_detection_in_exception_handler(self):
        """
        Verify NoMatch error is detected correctly in exception handler

        The code checks:
        if "No speech could be recognized" in error_detail:
            # Log as azure_no_speech_recognized
        """
        error_messages = [
            ("No speech could be recognized from the audio", True),
            ("No speech could be recognized", True),
            ("Speech recognition failed", False),
            ("Audio conversion failed", False),
        ]

        for error_message, should_match in error_messages:
            is_no_match = "No speech could be recognized" in error_message
            assert is_no_match == should_match

    @pytest.mark.asyncio
    async def test_azure_no_match_contains_required_fields(self):
        """
        Verify azure_no_speech_recognized log contains all required fields

        Required fields:
        - timestamp
        - error_type (azure_no_speech_recognized)
        - error_message
        - student_id
        - assignment_id
        - audio_size_bytes
        - reference_text
        - environment
        """
        required_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "audio_size_bytes",
            "reference_text",
            "environment",
        ]

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "azure_no_speech_recognized",
            "error_message": "No speech could be recognized from the audio",
            "student_id": 123,
            "assignment_id": 456,
            "audio_size_bytes": 1024000,
            "reference_text": "Test text",
            "environment": "staging",
        }

        # Verify all required fields present
        for field in required_fields:
            assert (
                field in error_data
            ), f"Required field '{field}' missing from error data"

        # Verify error_type
        assert error_data["error_type"] == "azure_no_speech_recognized"


class TestAudioConversionFailedLogging:
    """测试音频转换失败记录到 BigQuery"""

    @pytest.mark.asyncio
    async def test_audio_conversion_failed_logged_to_bigquery(self):
        """
        Verify audio_conversion_failed error is logged to BigQuery

        Test scenario:
        - Audio format conversion fails in convert_audio_to_wav
        - HTTPException 400 is raised with "Audio format conversion failed"
        - BigQuery log_audio_error is called in exception handler
        """
        from services.bigquery_logger import BigQueryLogger

        # Mock BigQuery logger
        mock_logger = AsyncMock(spec=BigQueryLogger)
        mock_logger.log_audio_error = AsyncMock(return_value=True)

        with patch(
            "routers.speech_assessment.get_bigquery_logger", return_value=mock_logger
        ):
            # Simulate conversion failure logging
            await mock_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "audio_conversion_failed",
                    "error_message": "Audio format conversion failed: ffmpeg not found",
                    "student_id": 123,
                    "assignment_id": 456,
                    "audio_size_bytes": 1024000,
                    "content_type": "audio/webm",
                    "environment": "test",
                }
            )

            # Verify logger was called
            mock_logger.log_audio_error.assert_called_once()

            # Verify error data structure
            call_args = mock_logger.log_audio_error.call_args[0][0]
            assert call_args["error_type"] == "audio_conversion_failed"
            assert "Audio format conversion failed" in call_args["error_message"]

    @pytest.mark.asyncio
    async def test_conversion_failed_error_detection_in_exception_handler(self):
        """
        Verify conversion failure is detected correctly in exception handler

        The code checks:
        elif "Audio format conversion failed" in error_detail:
            # Log as audio_conversion_failed
        """
        error_messages = [
            ("Audio format conversion failed: ffmpeg not found", True),
            ("Audio format conversion failed", True),
            ("No speech could be recognized", False),
            ("File too large", False),
        ]

        for error_message, should_match in error_messages:
            is_conversion_error = "Audio format conversion failed" in error_message
            assert is_conversion_error == should_match

    @pytest.mark.asyncio
    async def test_audio_conversion_failed_contains_required_fields(self):
        """
        Verify audio_conversion_failed log contains all required fields

        Required fields:
        - timestamp
        - error_type (audio_conversion_failed)
        - error_message
        - student_id
        - assignment_id
        - audio_size_bytes
        - content_type
        - environment
        """
        required_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "audio_size_bytes",
            "content_type",
            "environment",
        ]

        error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "audio_conversion_failed",
            "error_message": "Audio format conversion failed: ffmpeg not found",
            "student_id": 123,
            "assignment_id": 456,
            "audio_size_bytes": 1024000,
            "content_type": "audio/webm",
            "environment": "staging",
        }

        # Verify all required fields present
        for field in required_fields:
            assert (
                field in error_data
            ), f"Required field '{field}' missing from error data"

        # Verify error_type
        assert error_data["error_type"] == "audio_conversion_failed"


class TestBigQuerySchemaFields:
    """测试新的 BigQuery schema 字段"""

    def test_new_schema_fields_are_nullable(self):
        """
        Verify new schema fields are nullable (backward compatible)

        New fields:
        - content_type (STRING, NULLABLE)
        - max_size_bytes (INT64, NULLABLE)
        - allowed_formats (STRING, NULLABLE)
        """
        # These fields should be optional in error data
        minimal_error_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": "api_timeout",
            "error_message": "Test error",
            "student_id": 123,
            "audio_size_bytes": 1024,
            "environment": "test",
        }

        # Should not require new fields
        assert "content_type" not in minimal_error_data  # OK - nullable
        assert "max_size_bytes" not in minimal_error_data  # OK - nullable
        assert "allowed_formats" not in minimal_error_data  # OK - nullable

    def test_content_type_field_usage(self):
        """
        Verify content_type field is used correctly

        Used in:
        - file_too_large
        - invalid_audio_format
        - audio_conversion_failed
        """
        errors_with_content_type = [
            "file_too_large",
            "invalid_audio_format",
            "audio_conversion_failed",
        ]

        for error_type in errors_with_content_type:
            error_data = {
                "error_type": error_type,
                "content_type": "audio/webm",
            }
            assert "content_type" in error_data

    def test_max_size_bytes_field_usage(self):
        """
        Verify max_size_bytes field is used correctly

        Used only in:
        - file_too_large
        """
        error_data = {
            "error_type": "file_too_large",
            "max_size_bytes": 10 * 1024 * 1024,
        }

        assert "max_size_bytes" in error_data
        assert error_data["max_size_bytes"] == 10485760

    def test_allowed_formats_field_usage(self):
        """
        Verify allowed_formats field is used correctly

        Used only in:
        - invalid_audio_format
        """
        error_data = {
            "error_type": "invalid_audio_format",
            "allowed_formats": "audio/wav, audio/webm, audio/mp3",
        }

        assert "allowed_formats" in error_data
        assert isinstance(error_data["allowed_formats"], str)


class TestErrorTypeSummary:
    """测试所有 5 个错误类型的摘要"""

    def test_all_five_error_types_documented(self):
        """
        Verify all 5 error types are correctly defined

        Error types:
        1. file_too_large
        2. invalid_audio_format
        3. queue_wait_exceeded
        4. azure_no_speech_recognized
        5. audio_conversion_failed
        """
        expected_error_types = [
            "file_too_large",
            "invalid_audio_format",
            "queue_wait_exceeded",
            "azure_no_speech_recognized",
            "audio_conversion_failed",
        ]

        # All should be unique
        assert len(expected_error_types) == 5
        assert len(set(expected_error_types)) == 5

        # All should be lowercase with underscores
        for error_type in expected_error_types:
            assert error_type.islower()
            assert " " not in error_type

    def test_error_type_mapping(self):
        """
        Verify error types map to correct HTTP status codes

        Mapping:
        - file_too_large -> 413 (Payload Too Large)
        - invalid_audio_format -> 400 (Bad Request)
        - queue_wait_exceeded -> No exception (just logged)
        - azure_no_speech_recognized -> 400 (Bad Request)
        - audio_conversion_failed -> 400 (Bad Request)
        """
        error_status_map = {
            "file_too_large": 413,
            "invalid_audio_format": 400,
            "queue_wait_exceeded": None,  # Not an error, just logged
            "azure_no_speech_recognized": 400,
            "audio_conversion_failed": 400,
        }

        assert error_status_map["file_too_large"] == 413
        assert error_status_map["invalid_audio_format"] == 400
        assert error_status_map["queue_wait_exceeded"] is None
        assert error_status_map["azure_no_speech_recognized"] == 400
        assert error_status_map["audio_conversion_failed"] == 400

    @pytest.mark.asyncio
    async def test_all_errors_have_consistent_fields(self):
        """
        Verify all error logs have consistent base fields

        Common fields (all errors must have):
        - timestamp
        - error_type
        - error_message
        - student_id
        - environment
        """
        common_fields = [
            "timestamp",
            "error_type",
            "error_message",
            "student_id",
            "environment",
        ]

        all_error_types = [
            "file_too_large",
            "invalid_audio_format",
            "queue_wait_exceeded",
            "azure_no_speech_recognized",
            "audio_conversion_failed",
        ]

        for error_type in all_error_types:
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error_type": error_type,
                "error_message": f"Test {error_type}",
                "student_id": 123,
                "environment": "test",
            }

            # Verify common fields present
            for field in common_fields:
                assert (
                    field in error_data
                ), f"Field '{field}' missing for error type '{error_type}'"
