"""
壓力測試 - 50 併發上傳
測試異步 GCS 上傳在高併發情況下的性能
"""
import os
import sys
import time
from unittest.mock import Mock, AsyncMock, MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Mock google.cloud.storage before importing service
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.storage"] = MagicMock()

# noqa: E402
import pytest  # noqa: E402
import asyncio  # noqa: E402
from fastapi import UploadFile  # noqa: E402
from services.audio_upload import AudioUploadService  # noqa: E402


class TestAudioUploadStress:
    """壓力測試 - 高併發場景"""

    @pytest.fixture
    def service(self):
        """創建測試用 service"""
        return AudioUploadService()

    def create_mock_file(self, size_kb=100, file_id=0):
        """創建指定大小的 mock 檔案"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/webm"
        mock_file.filename = f"test-{file_id}.webm"
        mock_file.read = AsyncMock(return_value=b"x" * (size_kb * 1024))
        return mock_file

    @pytest.mark.asyncio
    @pytest.mark.stress
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_stress_50_concurrent_uploads(
        self, mock_datetime, mock_uuid, service
    ):
        """壓力測試: 50 個併發上傳 (100KB 檔案)"""
        num_uploads = 50

        # Setup mocks
        mock_uuid.side_effect = [f"uuid-stress-{i}" for i in range(num_uploads)]
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        service.storage_client = mock_client
        mock_client.bucket.return_value = mock_bucket

        # Create mock blobs
        mock_blobs = []
        for i in range(num_uploads):
            mock_blob = Mock()
            mock_blob.upload_from_string = Mock()
            mock_blobs.append(mock_blob)

        mock_bucket.blob.side_effect = mock_blobs

        # Create 50 mock files (100KB each)
        files = [self.create_mock_file(100, i) for i in range(num_uploads)]

        # Upload concurrently and measure performance
        start_time = time.time()
        results = await asyncio.gather(
            *[service.upload_audio(file, duration_seconds=20) for file in files],
            return_exceptions=True,
        )
        elapsed_time = time.time() - start_time

        # Verify all uploads succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Found {len(errors)} errors in concurrent uploads"

        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) == num_uploads

        # Verify all URLs are correct
        for i, result in enumerate(successful_results):
            assert "https://storage.googleapis.com/duotopia-audio/recordings/" in result

        # Verify all blobs were uploaded
        for mock_blob in mock_blobs:
            mock_blob.upload_from_string.assert_called_once()

        # Performance metrics
        avg_time_per_upload = elapsed_time / num_uploads
        print("\n=== Stress Test Results (50 concurrent uploads) ===")
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"Average time per upload: {avg_time_per_upload*1000:.2f}ms")
        print(f"Throughput: {num_uploads/elapsed_time:.2f} uploads/sec")

        # Performance assertion: 50 uploads should complete in <3 seconds with async
        assert (
            elapsed_time < 3.0
        ), f"50 concurrent uploads took {elapsed_time:.2f}s (expected <3s)"

    @pytest.mark.asyncio
    @pytest.mark.stress
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_stress_50_concurrent_large_uploads(
        self, mock_datetime, mock_uuid, service
    ):
        """壓力測試: 50 個併發大檔案上傳 (1MB 檔案)"""
        num_uploads = 50

        # Setup mocks
        mock_uuid.side_effect = [f"uuid-large-{i}" for i in range(num_uploads)]
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        service.storage_client = mock_client
        mock_client.bucket.return_value = mock_bucket

        # Create mock blobs
        mock_blobs = []
        for i in range(num_uploads):
            mock_blob = Mock()
            mock_blob.upload_from_string = Mock()
            mock_blobs.append(mock_blob)

        mock_bucket.blob.side_effect = mock_blobs

        # Create 50 large files (1MB each)
        files = [self.create_mock_file(1000, i) for i in range(num_uploads)]

        # Upload concurrently and measure performance
        start_time = time.time()
        results = await asyncio.gather(
            *[service.upload_audio(file, duration_seconds=25) for file in files],
            return_exceptions=True,
        )
        elapsed_time = time.time() - start_time

        # Verify all uploads succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Found {len(errors)} errors in concurrent uploads"

        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) == num_uploads

        # Performance metrics
        total_mb = num_uploads * 1  # 1MB per file
        throughput_mbps = total_mb / elapsed_time
        print("\n=== Stress Test Results (50 x 1MB uploads) ===")
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"Total data: {total_mb}MB")
        print(f"Throughput: {throughput_mbps:.2f} MB/s")

        # Performance assertion: Should handle large files well
        assert (
            elapsed_time < 5.0
        ), f"50 x 1MB uploads took {elapsed_time:.2f}s (expected <5s)"

    @pytest.mark.asyncio
    @pytest.mark.stress
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_stress_100_concurrent_small_uploads(
        self, mock_datetime, mock_uuid, service
    ):
        """壓力測試: 100 個併發小檔案上傳 (10KB 檔案)"""
        num_uploads = 100

        # Setup mocks
        mock_uuid.side_effect = [f"uuid-small-{i}" for i in range(num_uploads)]
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        service.storage_client = mock_client
        mock_client.bucket.return_value = mock_bucket

        # Create mock blobs
        mock_blobs = []
        for i in range(num_uploads):
            mock_blob = Mock()
            mock_blob.upload_from_string = Mock()
            mock_blobs.append(mock_blob)

        mock_bucket.blob.side_effect = mock_blobs

        # Create 100 small files (10KB each)
        files = [self.create_mock_file(10, i) for i in range(num_uploads)]

        # Upload concurrently and measure performance
        start_time = time.time()
        results = await asyncio.gather(
            *[service.upload_audio(file, duration_seconds=15) for file in files],
            return_exceptions=True,
        )
        elapsed_time = time.time() - start_time

        # Verify all uploads succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Found {len(errors)} errors in concurrent uploads"

        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) == num_uploads

        # Performance metrics
        print("\n=== Stress Test Results (100 x 10KB uploads) ===")
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"Throughput: {num_uploads/elapsed_time:.2f} uploads/sec")

        # Performance assertion: Small files should be very fast
        assert (
            elapsed_time < 3.0
        ), f"100 x 10KB uploads took {elapsed_time:.2f}s (expected <3s)"

    @pytest.mark.asyncio
    @pytest.mark.stress
    @patch("services.audio_upload.uuid.uuid4")
    @patch("services.audio_upload.datetime")
    async def test_stress_realistic_classroom_scenario(
        self, mock_datetime, mock_uuid, service
    ):
        """壓力測試: 模擬真實教室場景 (30 學生同時提交作業)"""
        num_students = 30

        # Setup mocks
        mock_uuid.side_effect = [f"uuid-student-{i}" for i in range(num_students)]
        mock_now = Mock()
        mock_now.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value = mock_now

        # Mock GCS client
        mock_client = Mock()
        mock_bucket = Mock()
        service.storage_client = mock_client
        mock_client.bucket.return_value = mock_bucket

        # Create mock blobs
        mock_blobs = []
        for i in range(num_students):
            mock_blob = Mock()
            mock_blob.upload_from_string = Mock()
            mock_blobs.append(mock_blob)

        mock_bucket.blob.side_effect = mock_blobs

        # Create realistic sized files (200KB-500KB, 平均 350KB)
        import random

        random.seed(42)  # 固定種子以確保可重現性
        files = [
            self.create_mock_file(random.randint(200, 500), i)
            for i in range(num_students)
        ]

        # Upload concurrently and measure performance
        start_time = time.time()
        results = await asyncio.gather(
            *[service.upload_audio(file, duration_seconds=20) for file in files],
            return_exceptions=True,
        )
        elapsed_time = time.time() - start_time

        # Verify all uploads succeeded
        errors = [r for r in results if isinstance(r, Exception)]
        assert len(errors) == 0, f"Found {len(errors)} errors in classroom scenario"

        successful_results = [r for r in results if isinstance(r, str)]
        assert len(successful_results) == num_students

        # Performance metrics
        print("\n=== Classroom Scenario Results (30 students) ===")
        print(f"Total time: {elapsed_time:.2f}s")
        print(f"Average time per student: {elapsed_time/num_students*1000:.2f}ms")
        print(f"Students/second: {num_students/elapsed_time:.2f}")

        # Performance assertion: Real classroom should complete in <2 seconds
        assert (
            elapsed_time < 2.0
        ), f"Classroom scenario took {elapsed_time:.2f}s (expected <2s)"
