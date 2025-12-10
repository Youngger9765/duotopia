"""
Generate realistic test audio samples for load testing
Creates WebM audio files of various sizes
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Audio sample configurations
SAMPLES = [
    {
        "name": "small_3sec_50kb.webm",
        "duration": 3,
        "target_size_kb": 50,
        "description": "Short phrase (3 seconds)",
    },
    {
        "name": "medium_10sec_200kb.webm",
        "duration": 10,
        "target_size_kb": 200,
        "description": "Medium sentence (10 seconds)",
    },
    {
        "name": "large_20sec_500kb.webm",
        "duration": 20,
        "target_size_kb": 500,
        "description": "Long recording (20 seconds)",
    },
    {
        "name": "max_30sec_2mb.webm",
        "duration": 30,
        "target_size_kb": 2000,
        "description": "Maximum size (30 seconds, 2MB)",
    },
]


def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, check=True
        )
        print("✅ ffmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ ffmpeg is not installed")
        print(
            "   Install with: brew install ffmpeg (macOS) or apt-get install ffmpeg (Linux)"
        )
        return False


def generate_audio_file(output_path: str, duration: int, bitrate_kbps: int):
    """
    Generate a silent audio file with specified duration and bitrate

    Args:
        output_path: Output file path
        duration: Duration in seconds
        bitrate_kbps: Target bitrate in kbps
    """
    # Generate silent audio with ffmpeg
    # Using libopus codec (WebM standard)
    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=r=48000:cl=mono",  # Silent audio, 48kHz, mono
        "-t",
        str(duration),  # Duration
        "-c:a",
        "libopus",  # Opus codec (WebM)
        "-b:a",
        f"{bitrate_kbps}k",  # Bitrate
        "-vbr",
        "on",  # Variable bitrate
        "-y",  # Overwrite
        output_path,
    ]

    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating {output_path}: {e.stderr}")
        return False


def calculate_bitrate(target_size_kb: int, duration: int) -> int:
    """
    Calculate bitrate needed to achieve target file size

    Args:
        target_size_kb: Target file size in KB
        duration: Duration in seconds

    Returns:
        Bitrate in kbps
    """
    # Formula: bitrate (kbps) = (file_size_kb * 8) / duration_sec
    # Add 10% overhead for container format
    bitrate = int((target_size_kb * 8) / duration * 0.9)
    return max(bitrate, 8)  # Minimum 8kbps


def main():
    """Generate all audio samples"""
    print("🎵 Generating test audio samples...")
    print()

    # Check ffmpeg
    if not check_ffmpeg():
        print("\nFallback: Generating dummy binary files instead")
        use_ffmpeg = False
    else:
        use_ffmpeg = True

    # Create audio_samples directory
    samples_dir = Path(__file__).parent / "audio_samples"
    samples_dir.mkdir(exist_ok=True)

    print(f"📁 Output directory: {samples_dir}")
    print()

    # Generate each sample
    for sample in SAMPLES:
        output_path = samples_dir / sample["name"]
        print(f"Generating {sample['name']}...")
        print(f"  Description: {sample['description']}")
        print(f"  Duration:    {sample['duration']} seconds")
        print(f"  Target size: {sample['target_size_kb']} KB")

        if use_ffmpeg:
            # Generate real audio file
            bitrate = calculate_bitrate(sample["target_size_kb"], sample["duration"])
            print(f"  Bitrate:     {bitrate} kbps")

            success = generate_audio_file(str(output_path), sample["duration"], bitrate)

            if success:
                # Check actual file size
                actual_size = output_path.stat().st_size / 1024
                print(f"  ✅ Generated: {actual_size:.1f} KB")
            else:
                print("  ❌ Failed to generate")

        else:
            # Generate dummy binary file
            target_bytes = sample["target_size_kb"] * 1024
            with open(output_path, "wb") as f:
                f.write(os.urandom(target_bytes))
            print(f"  ✅ Generated dummy file: {sample['target_size_kb']} KB")

        print()

    print("✅ All samples generated!")
    print(f"\nSamples location: {samples_dir}")
    print("\nYou can now run load tests with these audio files.")


if __name__ == "__main__":
    main()
