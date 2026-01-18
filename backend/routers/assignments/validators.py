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
    start_date: Optional[datetime] = None  # 開始日期

    # Legacy: 舊版造句練習答題模式（保留向後相容）
    answer_mode: str = "writing"  # @deprecated: 請使用 practice_mode 和 play_audio

    # ===== 例句集作答模式設定 =====
    # 作答模式：'reading' (例句朗讀) / 'rearrangement' (例句重組)
    practice_mode: str = "reading"

    # 每題時間限制（秒）：0（不限時）/10/20/30/40
    time_limit_per_question: int = 30

    # 是否打亂題目順序
    shuffle_questions: bool = False

    # 是否播放音檔（例句重組專用）
    play_audio: bool = False

    # 答題結束後是否顯示正確答案（例句重組專用）
    show_answer: bool = False

    # ===== Phase 2: 單字集作答模式設定 =====
    # 達標熟悉度（百分比，預設 80%）- 單字選擇模式專用
    target_proficiency: int = 80

    # 是否顯示翻譯（預設 true）- 單字朗讀模式可選擇隱藏
    show_translation: bool = True

    # 是否顯示單字（預設 true）- 單字選擇模式可選擇隱藏（只播音檔）
    show_word: bool = True

    # 是否顯示圖片（預設 true）- 單字集專用
    show_image: bool = True


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
