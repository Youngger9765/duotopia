"""
Pydantic models and validators for assignments
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class CreateAssignmentRequest(BaseModel):
    """建立作業請求（新架構）"""

    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int]  # 支援多個內容
    student_ids: List[int] = []  # 空陣列 = 全班
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    # 作答模式設定
    practice_mode: Optional[
        str
    ] = None  # reading, rearrangement, word_reading, word_selection
    answer_mode: Optional[str] = None  # speaking, listening, writing
    time_limit_per_question: Optional[int] = None
    shuffle_questions: Optional[bool] = False
    show_answer: Optional[bool] = False
    play_audio: Optional[bool] = False
    # 單字選擇模式設定
    target_proficiency: Optional[int] = None
    show_word: Optional[bool] = None
    show_image: Optional[bool] = None
    show_translation: Optional[bool] = None
    score_category: Optional[str] = None


class UpdateAssignmentRequest(BaseModel):
    """更新作業請求（部分更新）"""

    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None  # Alias for description
    due_date: Optional[datetime] = None
    student_ids: Optional[List[int]] = None


class AssignmentResponse(BaseModel):
    """作業回應"""

    id: int
    student_id: int
    content_id: int
    classroom_id: int
    title: str
    instructions: Optional[str]
    status: str
    assigned_at: datetime
    due_date: Optional[datetime]

    class Config:
        from_attributes = True


class StudentResponse(BaseModel):
    """學生回應"""

    id: int
    name: str
    email: Optional[str] = None
    student_number: Optional[str] = None

    class Config:
        from_attributes = True


class ContentResponse(BaseModel):
    """Content 回應"""

    id: int
    lesson_id: int
    title: str
    type: str
    level: Optional[str]
    items_count: int

    class Config:
        from_attributes = True


class AIGradingRequest(BaseModel):
    """AI 批改請求"""

    grading_mode: str = "full"  # "full" 或 "quick"
    audio_urls: List[str] = []
    mock_mode: bool = False
    mock_data: Optional[Dict[str, Any]] = None


class WordAnalysis(BaseModel):
    """單字分析"""

    word: str
    start_time: float
    end_time: float
    confidence: float
    is_correct: bool


class ItemGradingResult(BaseModel):
    """單項批改結果"""

    item_id: int
    expected_text: str
    transcribed_text: str
    accuracy_score: float
    pronunciation_score: float
    word_analysis: List[WordAnalysis]


class AIScores(BaseModel):
    """AI 評分"""

    pronunciation: float  # 發音評分 (0-100)
    fluency: float  # 流暢度評分 (0-100)
    accuracy: float  # 準確率評分 (0-100)
    wpm: float  # 每分鐘字數


class AIGradingResponse(BaseModel):
    """AI 批改回應"""

    assignment_id: int
    ai_scores: AIScores
    overall_score: float
    feedback: str
    detailed_feedback: List[Dict[str, Any]]
    graded_at: datetime
    processing_time_seconds: float
