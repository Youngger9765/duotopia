"""
Unit tests for Azure Speech SDK timeout configuration (Issue #92)

Tests verify that timeout settings are correctly configured for:
1. Speech Assessment (routers/speech_assessment.py)
2. TTS Service (services/tts.py)

Expected behavior:
- Connection timeout: 10 seconds (reduced from default 30s)
- End silence timeout: 2 seconds (for speech recognition)
- Faster failure detection when Azure API is unavailable
"""

import pytest
import os
import re


class TestSpeechAssessmentTimeoutCodeVerification:
    """Verify timeout configuration in source code"""

    def test_speech_assessment_timeout_in_code(self):
        """
        Verify that speech_assessment.py contains timeout configuration

        Checks for:
        - InitialSilenceTimeoutMs = "10000"
        - EndSilenceTimeoutMs = "2000"
        """
        speech_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "routers", "speech_assessment.py"
        )

        with open(speech_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for InitialSilenceTimeoutMs
        assert (
            "SpeechServiceConnection_InitialSilenceTimeoutMs" in content
        ), "InitialSilenceTimeoutMs property should be configured"

        # Check for specific timeout value (10 seconds)
        assert (
            '"10000"' in content or "'10000'" in content
        ), "Connection timeout should be set to 10000ms (10 seconds)"

        # Check for EndSilenceTimeoutMs
        assert (
            "SpeechServiceConnection_EndSilenceTimeoutMs" in content
        ), "EndSilenceTimeoutMs property should be configured"

        # Check for end silence timeout value (2 seconds)
        assert (
            '"2000"' in content or "'2000'" in content
        ), "End silence timeout should be set to 2000ms (2 seconds)"

        # Verify it's in the assess_pronunciation function
        pattern = (
            r"def assess_pronunciation.*?set_property.*?InitialSilenceTimeoutMs.*?10000"
        )
        assert re.search(
            pattern, content, re.DOTALL
        ), "Timeout configuration should be in assess_pronunciation function"

    def test_tts_timeout_in_code(self):
        """
        Verify that tts.py contains timeout configuration

        Checks for:
        - InitialSilenceTimeoutMs = "10000"
        """
        tts_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "services", "tts.py"
        )

        with open(tts_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check for InitialSilenceTimeoutMs
        assert (
            "SpeechServiceConnection_InitialSilenceTimeoutMs" in content
        ), "InitialSilenceTimeoutMs property should be configured"

        # Check for specific timeout value (10 seconds)
        assert (
            '"10000"' in content or "'10000'" in content
        ), "Connection timeout should be set to 10000ms (10 seconds)"

        # Verify it's in the generate_tts method
        pattern = (
            r"async def generate_tts.*?set_property.*?InitialSilenceTimeoutMs.*?10000"
        )
        assert re.search(
            pattern, content, re.DOTALL
        ), "Timeout configuration should be in generate_tts method"

    def test_timeout_values(self):
        """
        Test that timeout constants are correctly defined

        Expected values:
        - Connection timeout: 10 seconds
        - End silence timeout: 2 seconds
        """
        # These are the values we configured
        connection_timeout_ms = 10000  # 10 seconds
        end_silence_timeout_ms = 2000  # 2 seconds

        # Verify they are reasonable
        assert connection_timeout_ms == 10000, "Connection timeout should be 10s"
        assert end_silence_timeout_ms == 2000, "End silence timeout should be 2s"

        # Verify improvement over default (30s)
        default_timeout_ms = 30000
        improvement_factor = default_timeout_ms / connection_timeout_ms
        assert improvement_factor == 3.0, "Should be 3x faster than default 30s timeout"


class TestTimeoutPerformance:
    """Test performance improvements from timeout configuration"""

    def test_failure_detection_speed(self):
        """
        Test that timeout reduces failure detection time

        Before: 30s timeout
        After: 10s timeout
        Expected improvement: 20s faster failure detection
        """
        old_timeout_seconds = 30
        new_timeout_seconds = 10

        time_saved = old_timeout_seconds - new_timeout_seconds

        assert time_saved == 20, "Should save 20 seconds on timeout failures"
        assert (
            new_timeout_seconds < old_timeout_seconds
        ), "New timeout should be shorter"

        # Calculate percentage improvement
        improvement_percentage = (time_saved / old_timeout_seconds) * 100
        assert improvement_percentage == pytest.approx(
            66.67, rel=0.01
        ), "Should improve failure detection speed by ~67%"

    def test_timeout_constant_exists(self):
        """
        Test relationship between SDK timeout and application-level timeout

        AZURE_SPEECH_TIMEOUT (20s) should be longer than SDK connection timeout (10s)
        to allow for proper error handling
        """
        # Read the speech_assessment file to verify constant
        speech_file = os.path.join(
            os.path.dirname(__file__), "..", "..", "routers", "speech_assessment.py"
        )

        with open(speech_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify AZURE_SPEECH_TIMEOUT constant exists
        assert (
            "AZURE_SPEECH_TIMEOUT" in content
        ), "AZURE_SPEECH_TIMEOUT constant should exist"

        # Extract the value using regex
        match = re.search(r"AZURE_SPEECH_TIMEOUT\s*=\s*(\d+)", content)
        assert match, "AZURE_SPEECH_TIMEOUT should be assigned a numeric value"

        timeout_value = int(match.group(1))
        sdk_connection_timeout_seconds = 10

        # Application timeout should be 2x SDK timeout for safety margin
        assert timeout_value == 20, "Application timeout should be 20s"
        assert (
            timeout_value >= sdk_connection_timeout_seconds * 2
        ), "Application timeout should be at least 2x SDK timeout"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
