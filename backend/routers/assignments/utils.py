"""
Utility functions for assignment processing
"""

from typing import List, Dict, Any


async def process_audio_with_whisper(
    audio_urls: List[str], expected_texts: List[str]
) -> Dict[str, Any]:
    """
    Mock implementation for processing audio with Whisper API

    In production, this should integrate with OpenAI Whisper API:
    - Send audio files to Whisper for transcription
    - Compare transcriptions with expected texts
    - Return accuracy scores and detailed analysis

    For now, returns mock data for development/testing
    """
    return {
        "transcriptions": [
            {
                "item_id": i,
                "expected_text": text,
                "transcribed_text": text,  # Mock: return same as expected
                "words": [],
            }
            for i, text in enumerate(expected_texts)
        ],
        "audio_analysis": {"total_duration": 10.0},
    }


def calculate_text_similarity(expected: str, actual: str) -> float:
    """Calculate similarity between expected and actual text"""
    if not expected or not actual:
        return 0.0
    # Simple mock implementation - should use proper text similarity algorithm
    return 0.85 if expected.lower() == actual.lower() else 0.5


def calculate_pronunciation_score(words: List[Dict]) -> float:
    """Calculate pronunciation score from word-level analysis"""
    # Mock implementation
    return 85.0


def calculate_fluency_score(audio_analysis: Dict[str, Any]) -> float:
    """Calculate fluency score from audio analysis"""
    # Mock implementation
    return 80.0


def calculate_wpm(text: str, duration: float) -> int:
    """Calculate words per minute"""
    if duration <= 0:
        return 0
    word_count = len(text.split()) if text else 0
    return int((word_count / duration) * 60)


def generate_ai_feedback(ai_scores: "AIScores", detailed_results: List[Dict]) -> str:
    """Generate AI feedback based on scores"""
    # Mock implementation
    feedback = "Overall performance is good. "
    feedback += f"Pronunciation: {ai_scores.pronunciation}/100. "
    feedback += f"Fluency: {ai_scores.fluency}/100. "
    feedback += f"Accuracy: {ai_scores.accuracy}/100."
    return feedback
