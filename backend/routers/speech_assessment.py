"""
Azure Speech Assessment Router
處理微軟發音評估 API 的請求
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from auth import get_current_user
from models import Student, StudentContentProgress, AssignmentStatus

# 設定 logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/speech",
    tags=["speech_assessment"],
    responses={404: {"description": "Not found"}},
)

# 設定限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_AUDIO_FORMATS = ["audio/wav", "audio/webm", "audio/mp3", "audio/mpeg"]


async def get_current_student(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
) -> Student:
    """獲取當前認證的學生"""
    student_id = int(current_user.get("sub"))
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    return student


class AssessmentResponse(BaseModel):
    """發音評估回應 schema"""

    id: Optional[int] = None
    accuracy_score: float
    fluency_score: float
    completeness_score: float
    pronunciation_score: float
    words: List[Dict[str, Any]]
    reference_text: str
    created_at: Optional[datetime] = None


def assess_pronunciation(audio_data: bytes, reference_text: str) -> Dict[str, Any]:
    """
    呼叫 Azure Speech API 進行發音評估

    Args:
        audio_data: 音檔二進位資料
        reference_text: 參考文本

    Returns:
        評估結果字典
    """
    import azure.cognitiveservices.speech as speechsdk

    # 取得 Azure 設定
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")

    if not speech_key:
        raise ValueError("AZURE_SPEECH_KEY not configured")

    try:
        # 設定 Speech SDK
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region
        )

        # 設定發音評估
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,
        )

        # 從記憶體創建音訊流
        audio_stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

        # 創建語音識別器
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        # 套用發音評估配置
        pronunciation_config.apply_to(speech_recognizer)

        # 推送音訊資料
        audio_stream.write(audio_data)
        audio_stream.close()

        # 執行識別
        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            # 取得評估結果
            pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

            # 解析結果
            assessment_result = {
                "accuracy_score": pronunciation_result.accuracy_score,
                "fluency_score": pronunciation_result.fluency_score,
                "completeness_score": pronunciation_result.completeness_score,
                "pronunciation_score": pronunciation_result.pronunciation_score,
                "words": [],
            }

            # 解析單字詳細資料
            for word in pronunciation_result.words:
                word_data = {
                    "word": word.word,
                    "accuracy_score": word.accuracy_score,
                    "error_type": word.error_type.name if word.error_type else "None",
                }
                assessment_result["words"].append(word_data)

            return assessment_result

        elif result.reason == speechsdk.ResultReason.NoMatch:
            raise HTTPException(
                status_code=400, detail="No speech could be recognized from the audio"
            )
        else:
            raise HTTPException(
                status_code=503, detail=f"Speech recognition failed: {result.reason}"
            )

    except Exception as e:
        logger.error(f"Azure Speech API error: {str(e)}")
        raise HTTPException(
            status_code=503, detail="Service unavailable. Please try again later."
        )


def save_assessment_result(
    db: Session,
    progress_id: int,
    assessment_result: Dict[str, Any],
    audio_url: Optional[str] = None,
) -> StudentContentProgress:
    """
    儲存評估結果到 StudentContentProgress
    """
    progress = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.id == progress_id)
        .first()
    )

    if not progress:
        raise HTTPException(status_code=404, detail="Progress record not found")

    # 更新 response_data 儲存錄音 URL
    response_data = progress.response_data or {}
    response_data["audio_url"] = audio_url
    progress.response_data = response_data

    # 更新 ai_scores 儲存微軟評估結果
    progress.ai_scores = {
        "accuracy_score": assessment_result["accuracy_score"],
        "fluency_score": assessment_result["fluency_score"],
        "completeness_score": assessment_result["completeness_score"],
        "pronunciation_score": assessment_result["pronunciation_score"],
        "word_details": assessment_result["words"],
    }

    # 更新狀態為已完成
    progress.status = AssignmentStatus.SUBMITTED
    progress.completed_at = datetime.now()

    db.commit()
    db.refresh(progress)

    return progress


@router.post("/assess", response_model=AssessmentResponse)
async def assess_pronunciation_endpoint(
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    progress_id: int = Form(...),
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    評估學生發音

    - **audio_file**: 音檔（WAV, WebM, MP3）
    - **reference_text**: 參考文本
    - **progress_id**: StudentContentProgress 記錄的 ID
    """
    # 檢查檔案格式
    if audio_file.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed formats: {', '.join(ALLOWED_AUDIO_FORMATS)}",
        )

    # 檢查檔案大小
    audio_data = await audio_file.read()
    if len(audio_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB",
        )

    # 進行發音評估
    assessment_result = assess_pronunciation(audio_data, reference_text)

    # 儲存結果到資料庫
    updated_progress = save_assessment_result(
        db=db, progress_id=progress_id, assessment_result=assessment_result
    )

    # 回傳結果
    return AssessmentResponse(
        id=updated_progress.id,
        accuracy_score=assessment_result["accuracy_score"],
        fluency_score=assessment_result["fluency_score"],
        completeness_score=assessment_result["completeness_score"],
        pronunciation_score=assessment_result["pronunciation_score"],
        words=assessment_result["words"],
        reference_text=reference_text,
        created_at=updated_progress.completed_at,
    )


@router.get("/assessments", response_model=List[AssessmentResponse])
async def get_student_assessments(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    獲取學生的評估歷史記錄
    """
    # 查詢有 ai_scores 的 StudentContentProgress 記錄
    progress_records = (
        db.query(StudentContentProgress)
        .join(StudentContentProgress.student_assignment)
        .filter(
            StudentContentProgress.ai_scores.isnot(None),
            # TODO: 需要加入學生過濾條件
        )
        .order_by(StudentContentProgress.completed_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    results = []
    for progress in progress_records:
        ai_scores = progress.ai_scores or {}
        results.append(
            AssessmentResponse(
                id=progress.id,
                accuracy_score=ai_scores.get("accuracy_score", 0.0),
                fluency_score=ai_scores.get("fluency_score", 0.0),
                completeness_score=ai_scores.get("completeness_score", 0.0),
                pronunciation_score=ai_scores.get("pronunciation_score", 0.0),
                words=ai_scores.get("word_details", []),
                reference_text=progress.content.text if progress.content else "",
                created_at=progress.completed_at,
            )
        )

    return results


@router.get("/assessments/{progress_id}", response_model=AssessmentResponse)
async def get_assessment_by_id(
    progress_id: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    獲取特定評估的詳細資料
    """
    progress = (
        db.query(StudentContentProgress)
        .filter(
            StudentContentProgress.id == progress_id,
            StudentContentProgress.ai_scores.isnot(None),
        )
        .first()
    )

    if not progress:
        raise HTTPException(status_code=404, detail="Assessment not found")

    ai_scores = progress.ai_scores or {}

    return AssessmentResponse(
        id=progress.id,
        accuracy_score=ai_scores.get("accuracy_score", 0.0),
        fluency_score=ai_scores.get("fluency_score", 0.0),
        completeness_score=ai_scores.get("completeness_score", 0.0),
        pronunciation_score=ai_scores.get("pronunciation_score", 0.0),
        words=ai_scores.get("word_details", []),
        reference_text=progress.content.text if progress.content else "",
        created_at=progress.completed_at,
    )
