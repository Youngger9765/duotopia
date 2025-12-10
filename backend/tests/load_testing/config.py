"""
Load Testing Configuration
Manages environment settings and test scenario definitions for load testing.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env files
load_dotenv()


@dataclass
class EnvironmentConfig:
    """Configuration for a specific testing environment."""

    name: str
    base_url: str
    database_url: Optional[str]
    student_email: str
    student_password: str
    teacher_email: Optional[str] = None
    teacher_password: Optional[str] = None


@dataclass
class TestScenario:
    """Configuration for a specific test scenario."""

    name: str
    users: int
    spawn_rate: int  # users per second
    duration: str  # e.g., "5m", "10m", "30m"
    description: str


# Test Scenario Definitions
TEST_SCENARIOS: Dict[str, TestScenario] = {
    "normal": TestScenario(
        name="normal",
        users=20,
        spawn_rate=2,
        duration="5m",
        description="Typical usage pattern - baseline performance",
    ),
    "peak": TestScenario(
        name="peak",
        users=50,
        spawn_rate=5,
        duration="5m",
        description="High traffic period (e.g., after homework assignment)",
    ),
    "stress": TestScenario(
        name="stress",
        users=100,
        spawn_rate=10,
        duration="10m",
        description="Beyond normal capacity - find bottlenecks",
    ),
    "spike": TestScenario(
        name="spike",
        users=50,
        spawn_rate=25,
        duration="3m",
        description="Sudden burst of traffic",
    ),
    "endurance": TestScenario(
        name="endurance",
        users=30,
        spawn_rate=3,
        duration="30m",
        description="Sustained load over time - check for memory leaks",
    ),
    "breaking": TestScenario(
        name="breaking",
        users=200,
        spawn_rate=20,
        duration="10m",
        description="Find absolute system limits",
    ),
}


# Audio File Specifications
# Based on README.md specifications (adjusted from user requirements: 1MB, 3MB, 5MB, 8MB)
AUDIO_FILE_SPECS = {
    "small": {
        "filename": "small_3sec_50kb.webm",  # Using existing file
        "size_kb": 50,
        "probability": 0.40,  # 40% of uploads
        "description": "Small file - 3 seconds",
    },
    "medium": {
        "filename": "medium_10sec_200kb.webm",  # Using existing file
        "size_kb": 200,
        "probability": 0.30,  # 30% of uploads
        "description": "Medium file - 10 seconds",
    },
    "large": {
        "filename": "large_20sec_500kb.webm",  # Using existing file
        "size_kb": 500,
        "probability": 0.20,  # 20% of uploads
        "description": "Large file - 20 seconds",
    },
    "max": {
        "filename": "max_30sec_2mb.webm",  # Using existing file
        "size_kb": 2000,
        "probability": 0.10,  # 10% of uploads
        "description": "Maximum file - 30 seconds",
    },
}


def get_config(environment: str = None) -> EnvironmentConfig:
    """
    Get configuration for the specified environment.

    Args:
        environment: Environment name (staging, production, local).
                    If None, uses TEST_ENV environment variable.

    Returns:
        EnvironmentConfig object for the specified environment.

    Raises:
        ValueError: If environment is not recognized or required variables are missing.
    """
    if environment is None:
        environment = os.getenv("TEST_ENV", "staging")

    environment = environment.lower()

    if environment == "staging":
        return EnvironmentConfig(
            name="staging",
            base_url=os.getenv(
                "STAGING_BASE_URL",
                "https://duotopia-staging-backend-316409492201.asia-east1.run.app",
            ),
            database_url=os.getenv("STAGING_DATABASE_URL"),
            student_email=os.getenv("TEST_STUDENT_EMAIL", "student1@duotopia.com"),
            student_password=os.getenv("TEST_STUDENT_PASSWORD", "20120101"),
            teacher_email=os.getenv("TEST_TEACHER_EMAIL"),
            teacher_password=os.getenv("TEST_TEACHER_PASSWORD"),
        )

    elif environment == "production":
        # Require explicit configuration for production
        base_url = os.getenv("PRODUCTION_BASE_URL")
        if not base_url:
            raise ValueError(
                "PRODUCTION_BASE_URL must be set for production testing. "
                "This is intentionally required to prevent accidental production tests."
            )

        student_email = os.getenv("PROD_TEST_STUDENT_EMAIL")
        student_password = os.getenv("PROD_TEST_STUDENT_PASSWORD")

        if not student_email or not student_password:
            raise ValueError(
                "PROD_TEST_STUDENT_EMAIL and PROD_TEST_STUDENT_PASSWORD must be set "
                "for production testing."
            )

        return EnvironmentConfig(
            name="production",
            base_url=base_url,
            database_url=os.getenv("PRODUCTION_DATABASE_URL"),
            student_email=student_email,
            student_password=student_password,
            teacher_email=os.getenv("PROD_TEST_TEACHER_EMAIL"),
            teacher_password=os.getenv("PROD_TEST_TEACHER_PASSWORD"),
        )

    elif environment == "local":
        return EnvironmentConfig(
            name="local",
            base_url=os.getenv("LOCAL_BASE_URL", "http://localhost:8000"),
            database_url=os.getenv(
                "LOCAL_DATABASE_URL",
                "postgresql://postgres:postgres@localhost:5432/duotopia",
            ),
            student_email=os.getenv("LOCAL_TEST_STUDENT_EMAIL", "test@example.com"),
            student_password=os.getenv("LOCAL_TEST_STUDENT_PASSWORD", "test123"),
            teacher_email=os.getenv("LOCAL_TEST_TEACHER_EMAIL"),
            teacher_password=os.getenv("LOCAL_TEST_TEACHER_PASSWORD"),
        )

    else:
        raise ValueError(
            f"Unknown environment: {environment}. "
            f"Must be one of: staging, production, local"
        )


def get_scenario(scenario_name: str) -> TestScenario:
    """
    Get test scenario configuration by name.

    Args:
        scenario_name: Name of the test scenario.

    Returns:
        TestScenario object.

    Raises:
        ValueError: If scenario name is not recognized.
    """
    scenario_name = scenario_name.lower()

    if scenario_name not in TEST_SCENARIOS:
        available = ", ".join(TEST_SCENARIOS.keys())
        raise ValueError(
            f"Unknown scenario: {scenario_name}. " f"Available scenarios: {available}"
        )

    return TEST_SCENARIOS[scenario_name]


def get_audio_file_by_probability() -> Dict[str, Any]:
    """
    Select an audio file based on configured probability distribution.

    Returns:
        Dict containing audio file information (filename, size_kb, description).
    """
    import random

    # Create weighted list based on probabilities
    choices = []
    for file_type, spec in AUDIO_FILE_SPECS.items():
        weight = int(spec["probability"] * 100)  # Convert to integer weight
        choices.extend([file_type] * weight)

    # Random selection
    selected_type = random.choice(choices)
    return AUDIO_FILE_SPECS[selected_type]


def validate_config(config: EnvironmentConfig) -> None:
    """
    Validate that required configuration is present.

    Args:
        config: EnvironmentConfig to validate.

    Raises:
        ValueError: If required configuration is missing.
    """
    if not config.base_url:
        raise ValueError(f"base_url is required for environment: {config.name}")

    if not config.student_email or not config.student_password:
        raise ValueError(
            f"student_email and student_password are required for environment: {config.name}"
        )

    # Check that base_url is a valid URL
    if not config.base_url.startswith(("http://", "https://")):
        raise ValueError(
            f"base_url must start with http:// or https://, got: {config.base_url}"
        )


# Module-level configuration cache
_cached_config: Optional[EnvironmentConfig] = None


def get_current_config() -> EnvironmentConfig:
    """
    Get the current environment configuration (cached).
    Uses TEST_ENV environment variable to determine environment.

    Returns:
        EnvironmentConfig object for the current environment.
    """
    global _cached_config

    if _cached_config is None:
        _cached_config = get_config()
        validate_config(_cached_config)

    return _cached_config


# Export commonly used objects
__all__ = [
    "EnvironmentConfig",
    "TestScenario",
    "TEST_SCENARIOS",
    "AUDIO_FILE_SPECS",
    "get_config",
    "get_scenario",
    "get_audio_file_by_probability",
    "validate_config",
    "get_current_config",
]
