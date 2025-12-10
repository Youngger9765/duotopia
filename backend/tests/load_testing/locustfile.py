"""
Locust Load Testing for Duotopia Audio Upload
Tests audio upload functionality under various concurrency levels
"""

import os
import random
import time
import json
from io import BytesIO
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask
import logging

from config import get_config, AudioTestFiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment from ENV variable or default to staging
TEST_ENV = os.getenv("TEST_ENV", "staging")
config = get_config(TEST_ENV)

logger.info(f"🚀 Load testing against: {config.name}")
logger.info(f"   Base URL: {config.base_url}")

# Global metrics tracking
test_metrics = {
    "total_uploads": 0,
    "successful_uploads": 0,
    "failed_uploads": 0,
    "auth_failures": 0,
    "upload_times": [],
}


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Initialize test environment"""
    logger.info("=" * 80)
    logger.info(f"Starting load test: {config.name}")
    logger.info(f"Target: {config.base_url}")
    logger.info("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Report test results"""
    logger.info("=" * 80)
    logger.info("Load Test Complete - Summary:")
    logger.info(f"  Total uploads attempted: {test_metrics['total_uploads']}")
    logger.info(f"  Successful: {test_metrics['successful_uploads']}")
    logger.info(f"  Failed: {test_metrics['failed_uploads']}")
    logger.info(f"  Auth failures: {test_metrics['auth_failures']}")

    if test_metrics["upload_times"]:
        avg_time = sum(test_metrics["upload_times"]) / len(test_metrics["upload_times"])
        logger.info(f"  Average upload time: {avg_time:.2f}s")

    success_rate = (
        (test_metrics["successful_uploads"] / test_metrics["total_uploads"] * 100)
        if test_metrics["total_uploads"] > 0
        else 0
    )
    logger.info(f"  Success rate: {success_rate:.2f}%")
    logger.info("=" * 80)


class AudioUploadUser(HttpUser):
    """
    Simulates a student user uploading audio recordings

    Behavior:
    1. Authenticate as student
    2. Get assignment details
    3. Upload audio recording
    4. Wait (think time)
    5. Repeat
    """

    # Wait 1-5 seconds between tasks (simulates user think time)
    wait_time = between(1, 5)

    # Host is set from config
    host = config.base_url

    def on_start(self):
        """
        Called when a user starts
        Authenticates and gets necessary IDs
        """
        logger.info(f"👤 User {self.environment.runner.user_count} starting...")

        # Authenticate as student
        self.authenticate()

        # Get test assignment and content IDs
        self.get_test_assignment()

    def authenticate(self):
        """Authenticate student user and store token"""
        try:
            response = self.client.post(
                "/api/students/validate",
                json={
                    "email": config.student_email,
                    "password": config.student_password,
                },
                name="/api/students/validate",
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.student_id = data["student"]["id"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                logger.info(f"✅ User authenticated: Student ID {self.student_id}")
            else:
                test_metrics["auth_failures"] += 1
                logger.error(
                    f"❌ Authentication failed: {response.status_code} - {response.text}"
                )
                raise RescheduleTask()

        except Exception as e:
            test_metrics["auth_failures"] += 1
            logger.error(f"❌ Authentication error: {e}")
            raise RescheduleTask()

    def get_test_assignment(self):
        """
        Get a test assignment and content item IDs
        In real scenario, create test data beforehand
        """
        try:
            # Get student profile to find assignments
            response = self.client.get(
                "/api/students/profile",
                headers=self.headers,
                name="/api/students/profile",
            )

            if response.status_code != 200:
                logger.warning(f"⚠️ Failed to get profile: {response.status_code}")
                # Use default test IDs (must be created beforehand)
                self.assignment_id = int(os.getenv("TEST_ASSIGNMENT_ID", "1"))
                self.content_item_id = int(os.getenv("TEST_CONTENT_ITEM_ID", "1"))
                return

            # Try to get actual assignment
            response = self.client.get(
                f"/api/students/{self.student_id}/assignments",
                headers=self.headers,
                name="/api/students/assignments",
            )

            if response.status_code == 200:
                assignments = response.json()
                if assignments and len(assignments) > 0:
                    # Use first assignment
                    assignment = assignments[0]
                    self.assignment_id = assignment["id"]

                    # Get first content item from assignment
                    # This is simplified - in real test, iterate through all items
                    if "contents" in assignment and len(assignment["contents"]) > 0:
                        content = assignment["contents"][0]
                        if "items" in content and len(content["items"]) > 0:
                            self.content_item_id = content["items"][0]["id"]
                            logger.info(
                                f"📝 Using assignment {self.assignment_id}, "
                                f"item {self.content_item_id}"
                            )
                            return

            # Fallback to environment variables
            self.assignment_id = int(os.getenv("TEST_ASSIGNMENT_ID", "1"))
            self.content_item_id = int(os.getenv("TEST_CONTENT_ITEM_ID", "1"))
            logger.info(
                f"📝 Using fallback IDs: assignment {self.assignment_id}, "
                f"item {self.content_item_id}"
            )

        except Exception as e:
            logger.warning(f"⚠️ Error getting assignment: {e}")
            # Use defaults
            self.assignment_id = int(os.getenv("TEST_ASSIGNMENT_ID", "1"))
            self.content_item_id = int(os.getenv("TEST_CONTENT_ITEM_ID", "1"))

    def generate_audio_file(self, size_kb=200):
        """
        Generate a fake audio file for testing

        Args:
            size_kb: Target file size in kilobytes

        Returns:
            BytesIO object containing fake audio data
        """
        # Generate random binary data to simulate audio file
        # In real scenario, use actual WebM/MP3 files
        file_size = size_kb * 1024
        fake_audio_data = os.urandom(file_size)

        audio_file = BytesIO(fake_audio_data)
        audio_file.name = f"test_recording_{random.randint(1000, 9999)}.webm"
        audio_file.seek(0)

        return audio_file

    @task(10)
    def upload_audio_medium(self):
        """Upload medium-sized audio file (most common)"""
        self.upload_audio(AudioTestFiles.MEDIUM["size_kb"])

    @task(5)
    def upload_audio_small(self):
        """Upload small audio file"""
        self.upload_audio(AudioTestFiles.SMALL["size_kb"])

    @task(3)
    def upload_audio_large(self):
        """Upload large audio file"""
        self.upload_audio(AudioTestFiles.LARGE["size_kb"])

    @task(1)
    def upload_audio_max(self):
        """Upload maximum size audio file"""
        self.upload_audio(AudioTestFiles.MAX_SIZE["size_kb"])

    def upload_audio(self, size_kb):
        """
        Upload audio recording

        Args:
            size_kb: Size of audio file to upload
        """
        test_metrics["total_uploads"] += 1
        start_time = time.time()

        try:
            # Generate fake audio file
            audio_file = self.generate_audio_file(size_kb)

            # Prepare multipart form data
            files = {"audio_file": (audio_file.name, audio_file, "audio/webm")}
            data = {
                "assignment_id": str(self.assignment_id),
                "content_item_id": str(self.content_item_id),
            }

            # Upload audio
            with self.client.post(
                "/api/students/upload-recording",
                headers=self.headers,
                files=files,
                data=data,
                catch_response=True,
                timeout=config.upload_timeout_seconds,
                name=f"/api/students/upload-recording ({size_kb}KB)",
            ) as response:
                upload_time = time.time() - start_time

                if response.status_code == 200:
                    test_metrics["successful_uploads"] += 1
                    test_metrics["upload_times"].append(upload_time)

                    # Validate response
                    try:
                        result = response.json()
                        if "audio_url" not in result:
                            response.failure("Response missing audio_url")
                            test_metrics["failed_uploads"] += 1
                        else:
                            response.success()
                            logger.debug(
                                f"✅ Upload successful ({size_kb}KB) in {upload_time:.2f}s"
                            )
                    except json.JSONDecodeError:
                        response.failure("Invalid JSON response")
                        test_metrics["failed_uploads"] += 1

                elif response.status_code == 413:
                    # Payload too large
                    response.failure(f"File too large: {size_kb}KB")
                    test_metrics["failed_uploads"] += 1
                    logger.warning(f"⚠️ File too large: {size_kb}KB")

                elif response.status_code == 429:
                    # Rate limited
                    response.failure("Rate limited")
                    test_metrics["failed_uploads"] += 1
                    logger.warning("⚠️ Rate limited")

                elif response.status_code == 503:
                    # Service unavailable
                    response.failure("Service unavailable")
                    test_metrics["failed_uploads"] += 1
                    logger.error("❌ Service unavailable (overload?)")

                else:
                    # Other error
                    response.failure(f"HTTP {response.status_code}")
                    test_metrics["failed_uploads"] += 1
                    logger.error(
                        f"❌ Upload failed: {response.status_code} - {response.text[:200]}"
                    )

        except Exception as e:
            test_metrics["failed_uploads"] += 1
            logger.error(f"❌ Upload exception: {e}")


class TeacherMonitoringUser(HttpUser):
    """
    Simulates teacher viewing student progress
    Lighter load, runs occasionally to simulate real mixed traffic
    """

    wait_time = between(10, 30)  # Teachers check less frequently
    host = config.base_url

    def on_start(self):
        """Authenticate as teacher"""
        try:
            response = self.client.post(
                "/api/auth/teacher/login",
                json={
                    "email": config.teacher_email,
                    "password": config.teacher_password,
                },
                name="/api/auth/teacher/login",
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.teacher_id = data["teacher"]["id"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                logger.info(f"👨‍🏫 Teacher authenticated: ID {self.teacher_id}")
            else:
                raise RescheduleTask()

        except Exception as e:
            logger.error(f"❌ Teacher authentication error: {e}")
            raise RescheduleTask()

    @task
    def view_assignments(self):
        """Teacher views assignments"""
        self.client.get(
            f"/api/teachers/{self.teacher_id}/assignments",
            headers=self.headers,
            name="/api/teachers/assignments",
        )

    @task
    def view_students(self):
        """Teacher views student list"""
        self.client.get(
            f"/api/teachers/{self.teacher_id}/students",
            headers=self.headers,
            name="/api/teachers/students",
        )


# Custom wait time for spike test (no wait)
class SpikeTestUser(AudioUploadUser):
    """User for spike test - uploads immediately without waiting"""

    wait_time = between(0, 1)  # Minimal wait
