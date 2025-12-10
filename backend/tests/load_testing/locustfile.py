"""
Locust Load Testing for Duotopia Audio Upload
Simulates concurrent users uploading audio recordings to test system capacity.
"""

import logging
from typing import Optional
from pathlib import Path
import random

from locust import HttpUser, task, between, events
from locust.exception import StopUser

from config import get_current_config, get_audio_file_by_probability

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global counters for metrics
total_uploads = 0
successful_uploads = 0
failed_uploads = 0
auth_failures = 0


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize test environment and validate configuration."""
    config = get_current_config()
    logger.info(f"Initializing load test for environment: {config.name}")
    logger.info(f"Target URL: {config.base_url}")
    logger.info(f"Test student: {config.student_email}")

    # Verify audio samples directory exists
    audio_dir = Path(__file__).parent / "audio_samples"
    if not audio_dir.exists():
        logger.error(f"Audio samples directory not found: {audio_dir}")
        logger.error("Run 'python generate_audio_samples.py' first!")
        raise FileNotFoundError(f"Audio samples directory not found: {audio_dir}")

    # Count available audio files
    audio_files = list(audio_dir.glob("*.webm")) + list(audio_dir.glob("*.bin"))
    logger.info(f"Found {len(audio_files)} audio sample files")

    if len(audio_files) == 0:
        logger.error("No audio sample files found!")
        logger.error("Run 'python generate_audio_samples.py' first!")
        raise FileNotFoundError("No audio sample files found in audio_samples/")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary statistics when test stops."""
    logger.info("=" * 60)
    logger.info("LOAD TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total upload attempts:    {total_uploads}")
    logger.info(f"Successful uploads:       {successful_uploads}")
    logger.info(f"Failed uploads:           {failed_uploads}")
    logger.info(f"Authentication failures:  {auth_failures}")

    if total_uploads > 0:
        success_rate = (successful_uploads / total_uploads) * 100
        logger.info(f"Success rate:             {success_rate:.2f}%")

    logger.info("=" * 60)


class AudioUploadUser(HttpUser):
    """
    Simulated user that uploads audio recordings.

    Behavior:
    1. Login to get JWT token (once per user)
    2. Repeatedly upload audio files of varying sizes
    3. Track success/failure metrics
    """

    # Wait between tasks (simulates user think time)
    wait_time = between(2, 5)  # 2-5 seconds between uploads

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = get_current_config()
        self.token: Optional[str] = None
        self.audio_dir = Path(__file__).parent / "audio_samples"

        # Set base URL from config
        self.host = self.config.base_url

    def on_start(self):
        """
        Called when a simulated user starts.
        Performs authentication to get JWT token.
        """
        self.authenticate()

    def authenticate(self):
        """
        Authenticate user and store JWT token.

        Uses POST /api/students/validate endpoint.
        """
        global auth_failures

        login_data = {
            "email": self.config.student_email,
            "password": self.config.student_password,
        }

        logger.debug(f"Authenticating user: {self.config.student_email}")

        try:
            with self.client.post(
                "/api/students/validate",
                json=login_data,
                catch_response=True,
                name="Login",
            ) as response:
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # API returns 'access_token', not 'token'
                        self.token = data.get("access_token") or data.get("token")

                        if not self.token:
                            logger.error("Login response missing 'access_token' or 'token' field")
                            response.failure("Login response missing token")
                            auth_failures += 1
                            raise StopUser()

                        logger.info(
                            f"Successfully authenticated: {self.config.student_email}"
                        )
                        response.success()
                    except Exception as e:
                        logger.error(f"Failed to parse login response: {e}")
                        response.failure(f"Invalid JSON response: {e}")
                        auth_failures += 1
                        raise StopUser()
                else:
                    logger.error(
                        f"Authentication failed: {response.status_code} - {response.text}"
                    )
                    response.failure(f"Authentication failed: {response.status_code}")
                    auth_failures += 1
                    raise StopUser()

        except Exception as e:
            logger.error(f"Authentication exception: {e}")
            auth_failures += 1
            raise StopUser()

    def get_random_audio_file(self) -> Path:
        """
        Select a random audio file based on configured probability distribution.

        Returns:
            Path to the selected audio file.
        """
        file_spec = get_audio_file_by_probability()
        file_path = self.audio_dir / file_spec["filename"]

        if not file_path.exists():
            # Fallback to any available file
            logger.warning(f"File not found: {file_path}, selecting random file")
            available_files = list(self.audio_dir.glob("*.webm")) + list(
                self.audio_dir.glob("*.bin")
            )
            if not available_files:
                raise FileNotFoundError("No audio files available for testing")
            file_path = random.choice(available_files)

        return file_path

    @task(10)  # Weight: 10 (most common task)
    def upload_audio(self):
        """
        Upload an audio file to the server.

        Uses POST /api/students/upload-recording endpoint.
        Simulates actual student recording upload behavior.
        """
        global total_uploads, successful_uploads, failed_uploads

        if not self.token:
            logger.error("No authentication token, skipping upload")
            return

        total_uploads += 1

        # Select audio file based on probability
        audio_file = self.get_random_audio_file()
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)

        logger.debug(f"Uploading file: {audio_file.name} ({file_size_mb:.2f} MB)")

        try:
            # Prepare multipart form data
            with open(audio_file, "rb") as f:
                files = {"audio": (audio_file.name, f, "audio/webm")}

                # Add authorization header
                headers = {"Authorization": f"Bearer {self.token}"}

                # Perform upload
                with self.client.post(
                    "/api/students/upload-recording",
                    files=files,
                    headers=headers,
                    catch_response=True,
                    name=f"Upload Audio ({audio_file.name})",
                    timeout=60,  # 60 second timeout for large files
                ) as response:
                    if response.status_code == 200:
                        successful_uploads += 1
                        logger.debug(f"Upload successful: {audio_file.name}")
                        response.success()

                    elif response.status_code == 401:
                        # Authentication error - token expired or invalid
                        logger.warning("Authentication error (401), re-authenticating")
                        response.failure("Authentication error (401)")
                        failed_uploads += 1
                        # Try to re-authenticate
                        self.authenticate()

                    elif response.status_code == 413:
                        # File too large
                        logger.warning(f"File too large (413): {audio_file.name}")
                        response.failure(f"File too large (413): {file_size_mb:.2f} MB")
                        failed_uploads += 1

                    elif response.status_code == 503:
                        # Service unavailable (overloaded)
                        logger.warning("Service unavailable (503)")
                        response.failure("Service overloaded (503)")
                        failed_uploads += 1

                    elif response.status_code == 500:
                        # Internal server error
                        logger.error(f"Server error (500): {response.text[:200]}")
                        response.failure("Internal server error (500)")
                        failed_uploads += 1

                    else:
                        # Other error
                        logger.error(
                            f"Upload failed ({response.status_code}): {response.text[:200]}"
                        )
                        response.failure(f"Upload failed ({response.status_code})")
                        failed_uploads += 1

        except Exception as e:
            logger.error(f"Upload exception: {e}")
            failed_uploads += 1

    @task(1)  # Weight: 1 (occasional task)
    def get_profile(self):
        """
        Get user profile (simulates checking progress between uploads).
        Lower priority task with weight 1 vs upload weight 10.
        """
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        with self.client.get(
            "/api/students/profile",
            headers=headers,
            catch_response=True,
            name="Get Profile",
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 401:
                logger.warning("Profile: Authentication error (401)")
                response.failure("Authentication error")
                self.authenticate()
            else:
                response.failure(f"Failed with status {response.status_code}")


# Additional user class for spike testing (optional)
class SpikeTester(AudioUploadUser):
    """
    Aggressive user for spike testing.
    Uploads continuously with minimal wait time.
    """

    wait_time = between(0.5, 1.5)  # Very short wait time

    @task
    def rapid_upload(self):
        """Upload with no profile checks, just continuous uploads."""
        self.upload_audio()


# Export user classes
__all__ = ["AudioUploadUser", "SpikeTester"]
