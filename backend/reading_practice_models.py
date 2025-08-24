# Reading Practice Data Models for JSON content structure

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class TTSAccent(str, Enum):
    AMERICAN = "american"
    BRITISH = "british"
    INDIAN = "indian"
    AUSTRALIAN = "australian"

class TTSGender(str, Enum):
    MALE = "male"
    FEMALE = "female"

class TTSSpeed(float, Enum):
    SLOW = 0.75
    NORMAL = 1.0
    FAST = 1.5

class AudioSource(str, Enum):
    TTS = "tts"
    TEACHER_RECORDED = "teacher_recorded"
    NONE = "none"

class DefinitionLanguage(str, Enum):
    TRADITIONAL_CHINESE = "zh-tw"
    SIMPLIFIED_CHINESE = "zh-cn"
    ENGLISH = "en"

class TTSSettings(BaseModel):
    """TTS generation settings"""
    text: str  # Text to generate (may differ from original text)
    accent: TTSAccent = TTSAccent.AMERICAN
    gender: TTSGender = TTSGender.MALE
    speed: TTSSpeed = TTSSpeed.NORMAL

class AudioData(BaseModel):
    """Audio information for a reading item"""
    source: AudioSource = AudioSource.NONE
    audio_url: Optional[str] = None
    tts_settings: Optional[TTSSettings] = None
    recorded_at: Optional[str] = None  # ISO datetime string

class ImageData(BaseModel):
    """Image information for a reading item"""
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    alt_text: Optional[str] = None
    source: Optional[str] = None  # "upload", "google_search", "paste"

class DefinitionData(BaseModel):
    """Definition/translation for a reading item"""
    text: Optional[str] = None
    language: DefinitionLanguage = DefinitionLanguage.TRADITIONAL_CHINESE
    auto_generated: bool = False
    generated_at: Optional[str] = None  # ISO datetime string

class ReadingItem(BaseModel):
    """Single item in a reading practice set"""
    id: str  # Unique identifier for this item
    text: str  # The text student needs to read
    order: int  # Display order (0-based)
    audio: AudioData = AudioData()
    image: ImageData = ImageData()
    definition: DefinitionData = DefinitionData()

class ReadingPracticeContent(BaseModel):
    """Content structure for reading practice activities"""
    title: str
    level: str  # DifficultyLevel enum value
    description: Optional[str] = None
    items: List[ReadingItem]
    
    # Teacher preferences (saved for next time)
    default_tts_accent: TTSAccent = TTSAccent.AMERICAN
    default_tts_gender: TTSGender = TTSGender.MALE
    default_tts_speed: TTSSpeed = TTSSpeed.NORMAL
    default_definition_language: DefinitionLanguage = DefinitionLanguage.TRADITIONAL_CHINESE

class ReadingPracticeCreateRequest(BaseModel):
    """Request model for creating reading practice"""
    title: str
    level: str
    description: Optional[str] = None
    items: List[Dict[str, Any]]  # Flexible format for frontend

class ReadingPracticeUpdateRequest(BaseModel):
    """Request model for updating reading practice"""
    title: Optional[str] = None
    level: Optional[str] = None
    description: Optional[str] = None
    items: Optional[List[Dict[str, Any]]] = None

# Example content structure:
EXAMPLE_READING_PRACTICE_CONTENT = {
    "title": "Daily Greetings",
    "level": "A1",
    "description": "Basic greeting phrases for beginners",
    "items": [
        {
            "id": "item-1",
            "text": "Good morning!",
            "order": 0,
            "audio": {
                "source": "tts",
                "audio_url": "https://storage.googleapis.com/audio/item-1.mp3",
                "tts_settings": {
                    "text": "Good morning!",
                    "accent": "american",
                    "gender": "female",
                    "speed": 1.0
                }
            },
            "image": {
                "image_url": "https://storage.googleapis.com/images/good-morning.jpg",
                "thumbnail_url": "https://storage.googleapis.com/images/good-morning-thumb.jpg",
                "alt_text": "People greeting each other in the morning",
                "source": "google_search"
            },
            "definition": {
                "text": "早安！用於早晨的問候語。",
                "language": "zh-tw",
                "auto_generated": true
            }
        },
        {
            "id": "item-2", 
            "text": "How are you?",
            "order": 1,
            "audio": {
                "source": "teacher_recorded",
                "audio_url": "https://storage.googleapis.com/audio/item-2-teacher.mp3",
                "recorded_at": "2024-08-22T10:30:00Z"
            },
            "image": {
                "image_url": null
            },
            "definition": {
                "text": "你好嗎？用來詢問對方的近況。",
                "language": "zh-tw",
                "auto_generated": true
            }
        }
    ],
    "default_tts_accent": "american",
    "default_tts_gender": "female", 
    "default_tts_speed": 1.0,
    "default_definition_language": "zh-tw"
}