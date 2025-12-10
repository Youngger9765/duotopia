#!/usr/bin/env python3
"""
Audio Sample Generator for Load Testing
Generates test audio files in various sizes for load testing uploads.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def check_ffmpeg_available() -> bool:
    """
    Check if ffmpeg is installed and available.

    Returns:
        True if ffmpeg is available, False otherwise.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def calculate_duration_for_size(target_size_kb: int, bitrate_kbps: int = 64) -> int:
    """
    Calculate audio duration needed to achieve target file size.

    Args:
        target_size_kb: Target file size in kilobytes.
        bitrate_kbps: Audio bitrate in kbps (default: 64 for WebM Opus).

    Returns:
        Duration in seconds.
    """
    # Formula: size (KB) = (bitrate (kbps) * duration (s)) / 8
    # Rearranged: duration = (size * 8) / bitrate
    duration = (target_size_kb * 8) / bitrate_kbps
    return max(1, int(duration))  # At least 1 second


def generate_webm_audio(output_path: Path, duration_seconds: int) -> bool:
    """
    Generate a WebM audio file using ffmpeg.

    Args:
        output_path: Path where the audio file will be saved.
        duration_seconds: Duration of the audio in seconds.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # ffmpeg command to generate silent audio with Opus codec
        # anullsrc = null audio source (silence)
        # -c:a libopus = Opus audio codec (WebM compatible)
        # -b:a 64k = 64 kbps bitrate
        cmd = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            str(duration_seconds),
            "-c:a",
            "libopus",
            "-b:a",
            "64k",
            "-y",  # Overwrite output file
            str(output_path),
        ]

        logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )

        if result.returncode != 0:
            logger.error(f"ffmpeg failed: {result.stderr.decode()}")
            return False

        logger.info(f"Generated WebM audio: {output_path.name} ({duration_seconds}s)")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"ffmpeg timeout while generating {output_path.name}")
        return False
    except Exception as e:
        logger.error(f"Failed to generate WebM audio: {e}")
        return False


def generate_binary_dummy(output_path: Path, size_kb: int) -> bool:
    """
    Generate a dummy binary file as fallback when ffmpeg is unavailable.

    Args:
        output_path: Path where the file will be saved.
        size_kb: Size of the file in kilobytes.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Generate random binary data
        size_bytes = size_kb * 1024
        data = os.urandom(size_bytes)

        with open(output_path, "wb") as f:
            f.write(data)

        logger.info(f"Generated binary dummy: {output_path.name} ({size_kb} KB)")
        return True

    except Exception as e:
        logger.error(f"Failed to generate binary file: {e}")
        return False


def generate_audio_samples(use_ffmpeg: bool = True) -> bool:
    """
    Generate all audio sample files for load testing.

    Args:
        use_ffmpeg: Whether to use ffmpeg (True) or generate dummy files (False).

    Returns:
        True if all files generated successfully, False otherwise.
    """
    # Audio sample specifications
    # Note: Using existing spec from README (different from user's initial request)
    samples = [
        {"name": "small_3sec_50kb.webm", "duration_s": 3, "size_kb": 50},
        {"name": "medium_10sec_200kb.webm", "duration_s": 10, "size_kb": 200},
        {"name": "large_20sec_500kb.webm", "duration_s": 20, "size_kb": 500},
        {"name": "max_30sec_2mb.webm", "duration_s": 30, "size_kb": 2000},
    ]

    # Create output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / "audio_samples"
    output_dir.mkdir(exist_ok=True)

    logger.info(f"Output directory: {output_dir}")

    # Create .gitkeep to track empty directory
    gitkeep_path = output_dir / ".gitkeep"
    gitkeep_path.touch(exist_ok=True)

    success_count = 0
    total_count = len(samples)

    for sample in samples:
        file_name = sample["name"]
        output_path = output_dir / file_name

        # Skip if file already exists and is not empty
        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"File already exists: {file_name} (skipping)")
            success_count += 1
            continue

        # Generate file
        if use_ffmpeg:
            # Use ffmpeg to generate real WebM audio
            duration = sample["duration_s"]
            success = generate_webm_audio(output_path, duration)
        else:
            # Generate binary dummy file
            # Change extension to .bin for dummy files
            output_path = output_path.with_suffix(".bin")
            size_kb = sample["size_kb"]
            success = generate_binary_dummy(output_path, size_kb)

        if success:
            success_count += 1
            # Verify file size
            actual_size = output_path.stat().st_size
            logger.info(f"  Actual size: {actual_size / 1024:.1f} KB")
        else:
            logger.error(f"Failed to generate: {file_name}")

    # Summary
    logger.info("-" * 60)
    logger.info(f"Generation complete: {success_count}/{total_count} files created")

    if success_count < total_count:
        logger.warning(
            f"Some files failed to generate ({total_count - success_count} failures)"
        )
        return False

    logger.info("All audio samples generated successfully!")
    logger.info(f"Files location: {output_dir}")
    return True


def main():
    """Main entry point for the script."""
    logger.info("=" * 60)
    logger.info("Audio Sample Generator for Load Testing")
    logger.info("=" * 60)

    # Check if ffmpeg is available
    ffmpeg_available = check_ffmpeg_available()

    if ffmpeg_available:
        logger.info("✓ ffmpeg detected - will generate real WebM audio files")
        use_ffmpeg = True
    else:
        logger.warning("✗ ffmpeg not found - will generate binary dummy files")
        logger.warning("  To install ffmpeg:")
        logger.warning("    macOS:  brew install ffmpeg")
        logger.warning("    Linux:  sudo apt-get install ffmpeg")
        logger.warning("  Dummy files are sufficient for load testing")
        use_ffmpeg = False

    logger.info("")

    # Generate samples
    success = generate_audio_samples(use_ffmpeg=use_ffmpeg)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
