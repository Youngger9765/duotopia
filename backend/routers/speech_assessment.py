"""
Azure Speech Assessment Router
處理微軟發音評估 API 的請求
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from io import BytesIO
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pydub import AudioSegment

from database import get_db
from auth import get_current_user
from models import (
    Student,
    StudentContentProgress,
    StudentAssignment,
    StudentItemProgress,
)

# 設定 logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/speech",
    tags=["speech_assessment"],
    responses={404: {"description": "Not found"}},
)

# 設定限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_AUDIO_FORMATS = [
    "audio/wav",
    "audio/webm",
    "audio/webm;codecs=opus",
    "audio/mp3",
    "audio/mpeg",
    "application/octet-stream",  # 瀏覽器上傳時的通用類型
]


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
    words: List[Dict[str, Any]]  # 保留舊版相容性
    detailed_words: Optional[List[Dict[str, Any]]] = None  # 新版詳細資料
    word_details: Optional[List[Dict[str, Any]]] = None  # 舊版簡化資料
    reference_text: str
    recognized_text: Optional[str] = None
    prosody_score: Optional[float] = None
    analysis_summary: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


def convert_audio_to_wav(audio_data: bytes, content_type: str) -> bytes:
    """
    將音檔轉換為 WAV 格式（16000Hz, 16bit, mono）
    Azure Speech SDK 需要特定格式的 WAV
    """
    logger.debug(f"Converting audio from {content_type} to WAV")

    try:
        # 根據 content type 選擇格式
        if "webm" in content_type:
            # WebM 格式（瀏覽器錄音）
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name

            # 使用 pydub 轉換（需要 ffmpeg）
            audio = AudioSegment.from_file(temp_in_path, format="webm")
        elif "mp3" in content_type or "mpeg" in content_type:
            # MP3 格式
            audio = AudioSegment.from_mp3(BytesIO(audio_data))
        elif "wav" in content_type:
            # 已經是 WAV，但可能需要轉換採樣率
            audio = AudioSegment.from_wav(BytesIO(audio_data))
        else:
            # 嘗試自動偵測格式
            audio = AudioSegment.from_file(BytesIO(audio_data))

        # 轉換為 Azure Speech SDK 需要的格式
        # 16000Hz 採樣率, 單聲道, 16bit
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        audio = audio.set_sample_width(2)  # 16bit = 2 bytes

        # 輸出為 WAV
        wav_buffer = BytesIO()
        audio.export(wav_buffer, format="wav")
        wav_data = wav_buffer.getvalue()

        logger.debug(
            f"Converted audio: {len(audio_data)} bytes -> {len(wav_data)} bytes WAV"
        )
        logger.debug(f"Audio duration: {len(audio) / 1000.0} seconds")

        # 清理暫存檔
        if "temp_in_path" in locals():
            os.unlink(temp_in_path)

        return wav_data

    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        raise HTTPException(
            status_code=400, detail=f"Audio format conversion failed: {str(e)}"
        )


def assess_pronunciation(audio_data: bytes, reference_text: str) -> Dict[str, Any]:
    """
    呼叫 Azure Speech API 進行發音評估

    Args:
        audio_data: 音檔二進位資料
        reference_text: 參考文本

    Returns:
        評估結果字典（包含詳細的音節和音素資訊）
    """
    import azure.cognitiveservices.speech as speechsdk

    # 取得 Azure 設定
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_SPEECH_REGION", "eastasia")

    logger.debug(f"Azure Speech Key configured: {bool(speech_key)}")
    logger.debug(f"Azure Speech Region: {speech_region}")
    logger.debug(f"Processing audio: {len(audio_data)} bytes")
    logger.debug(f"Reference text: {reference_text}")

    if not speech_key:
        logger.error("AZURE_SPEECH_KEY not configured!")
        raise ValueError("AZURE_SPEECH_KEY not configured")

    try:
        # 設定 Speech SDK
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region
        )

        # 🔥 設定語言為美式英語以支援韻律評估
        speech_config.speech_recognition_language = "en-US"

        # 設定發音評估 - 啟用韻律評估
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=reference_text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
            enable_miscue=True,
        )

        # 啟用韻律評估（如果 SDK 支援）
        try:
            pronunciation_config.enable_prosody_assessment = True
            logger.info("✅ Prosody assessment enabled successfully")
        except Exception as e:
            logger.warning(f"⚠️ Prosody assessment not available: {e}")
            logger.info("韻律評估可能需要特定的 SDK 版本或語言支援")

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

            # 記錄原始結果以便調試
            import json

            result_json = json.loads(result.json)
            nbest = result_json.get("NBest", [{}])[0]
            print("\n🔍 Azure Speech API Raw Result:")
            print(f"Words count: {len(nbest.get('Words', []))}")
            if nbest.get("Words"):
                first_word = nbest["Words"][0]
                print(f"First word: {first_word.get('Word')}")
                print(f"Has Syllables: {'Syllables' in first_word}")
                print(f"Has Phonemes: {'Phonemes' in first_word}")
                if "Syllables" in first_word:
                    print(f"Syllables count: {len(first_word.get('Syllables', []))}")
                if "Phonemes" in first_word:
                    print(f"Phonemes count: {len(first_word.get('Phonemes', []))}")
            print(json.dumps(nbest, indent=2)[:2000])  # 只印前2000字元

            # 解析結果 - 包含韻律分數（如果有）
            assessment_result = {
                "accuracy_score": pronunciation_result.accuracy_score,
                "fluency_score": pronunciation_result.fluency_score,
                "completeness_score": pronunciation_result.completeness_score,
                "pronunciation_score": pronunciation_result.pronunciation_score,
                "recognized_text": result.text,
                "reference_text": reference_text,
                "words": [],
            }

            # 嘗試取得韻律分數
            if hasattr(pronunciation_result, "prosody_score"):
                prosody_score = pronunciation_result.prosody_score
                assessment_result["prosody_score"] = prosody_score
                logger.info(f"🎵 韻律分數: {prosody_score}")
            else:
                assessment_result["prosody_score"] = None
                logger.info("ℹ️ 韻律分數不可用 - 可能因為語言不支援或 SDK 版本限制")

            # 🔥 修復：直接解析 JSON 資料而不依賴 SDK 物件屬性
            # Azure Speech SDK 的 Python 物件沒有正確暴露 Syllables/Phonemes 屬性
            # 但 result.json 包含完整的資料
            words_from_json = nbest.get("Words", [])
            logger.debug(f"Parsing {len(words_from_json)} words from JSON...")

            for idx, word_json in enumerate(words_from_json):
                logger.debug(f"Processing word {idx}: {word_json.get('Word')}")
                try:
                    # 建立單字資料結構
                    word_data = {
                        "index": idx,
                        "word": word_json.get("Word", ""),
                        "accuracy_score": word_json.get(
                            "PronunciationAssessment", {}
                        ).get("AccuracyScore", 0),
                        "error_type": word_json.get("PronunciationAssessment", {}).get(
                            "ErrorType", "None"
                        ),
                        "syllables": [],
                        "phonemes": [],
                    }

                    # 解析音節資訊（從 JSON）
                    syllables_json = word_json.get("Syllables", [])
                    logger.debug(
                        f"Found {len(syllables_json)} syllables for word '{word_data['word']}'"
                    )

                    for syl_idx, syllable_json in enumerate(syllables_json):
                        syllable_data = {
                            "index": syl_idx,
                            "syllable": syllable_json.get("Syllable", ""),
                            "accuracy_score": syllable_json.get(
                                "PronunciationAssessment", {}
                            ).get("AccuracyScore", 0),
                        }
                        word_data["syllables"].append(syllable_data)
                        logger.debug(f"  Syllable {syl_idx}: {syllable_data}")

                    # 解析音素資訊（從 JSON）
                    phonemes_json = word_json.get("Phonemes", [])
                    logger.debug(
                        f"Found {len(phonemes_json)} phonemes for word '{word_data['word']}'"
                    )

                    for pho_idx, phoneme_json in enumerate(phonemes_json):
                        phoneme_data = {
                            "index": pho_idx,
                            "phoneme": phoneme_json.get("Phoneme", ""),
                            "accuracy_score": phoneme_json.get(
                                "PronunciationAssessment", {}
                            ).get("AccuracyScore", 0),
                        }
                        word_data["phonemes"].append(phoneme_data)
                        logger.debug(f"  Phoneme {pho_idx}: {phoneme_data}")

                    assessment_result["words"].append(word_data)
                    logger.debug(
                        f"✅ Processed word: {word_data['word']} (score: {word_data['accuracy_score']}, "
                        f"syllables: {len(word_data['syllables'])}, phonemes: {len(word_data['phonemes'])})"
                    )

                except Exception as e:
                    logger.error(f"Error processing word {idx}: {e}")
                    logger.debug(f"Word JSON details: {word_json}")
                    # 不要中斷，繼續處理其他單字
                    word_data = {
                        "index": idx,
                        "word": word_json.get("Word", "") if word_json else "",
                        "accuracy_score": word_json.get(
                            "PronunciationAssessment", {}
                        ).get("AccuracyScore", 0)
                        if word_json
                        else 0,
                        "error_type": "ProcessingError",
                        "syllables": [],
                        "phonemes": [],
                    }
                    assessment_result["words"].append(word_data)

            # 🔥 修復：在原始結果中加入 detailed_words 便於前端使用
            assessment_result["detailed_words"] = assessment_result["words"]

            # 為相容性加入 word_details
            assessment_result["word_details"] = [
                {
                    "word": w["word"],
                    "accuracy_score": w["accuracy_score"],
                    "error_type": w["error_type"],
                }
                for w in assessment_result["words"]
            ]

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
        logger.debug(f"Error type: {type(e)}")
        import traceback

        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=503, detail="Service unavailable. Please try again later."
        )


def save_assessment_result(
    db: Session,
    progress_id: int,
    assessment_result: Dict[str, Any],
    reference_text: str = "",
    item_index: Optional[int] = None,
    audio_url: Optional[str] = None,
    student_assignment_id: Optional[int] = None,
) -> StudentItemProgress:
    """
    儲存評估結果到 StudentItemProgress
    progress_id 應該是 StudentItemProgress 的 ID
    """
    # 查找 StudentItemProgress 記錄
    progress = (
        db.query(StudentItemProgress)
        .filter(StudentItemProgress.id == progress_id)
        .first()
    )

    if not progress:
        logger.warning(
            f"StudentItemProgress with id {progress_id} not found - "
            "this is normal if the progress record was deleted or never created"
        )
        # 不拋錯，而是嘗試通過其他方式查找或創建記錄
        # 如果有 student_assignment_id，嘗試查找對應的進度記錄
        if student_assignment_id and item_index is not None:
            # 通過 student_assignment_id 和 item_index 查找
            progress = (
                db.query(StudentItemProgress)
                .filter(
                    StudentItemProgress.student_assignment_id == student_assignment_id,
                    StudentItemProgress.item_index == item_index,
                )
                .first()
            )

            if progress:
                logger.info(
                    f"Found existing progress record via student_assignment_id "
                    f"{student_assignment_id} and item_index {item_index}: {progress.id}"
                )
            else:
                logger.warning(
                    f"No progress record found for student_assignment_id "
                    f"{student_assignment_id} and item_index {item_index}"
                )
                raise HTTPException(
                    status_code=404,
                    detail="Progress record not found - please ensure recording was uploaded first",
                )
        else:
            logger.error(
                f"StudentItemProgress with id {progress_id} not found and insufficient data to locate alternative"
            )
            raise HTTPException(
                status_code=404,
                detail="Progress record not found - please ensure recording was uploaded first",
            )
    # 更新 AI 評估分數 (StudentItemProgress 使用獨立欄位而非 JSON)
    progress.accuracy_score = assessment_result["accuracy_score"]
    progress.fluency_score = assessment_result["fluency_score"]
    progress.pronunciation_score = assessment_result["pronunciation_score"]

    # 將完整評估結果和詞彙細節儲存為 JSON 格式的 ai_feedback
    # 這個 JSON 包含完整的 Word→Syllable→Phoneme 層級資訊
    import json

    ai_feedback = {
        # 總體分數
        "accuracy_score": assessment_result["accuracy_score"],
        "fluency_score": assessment_result["fluency_score"],
        "pronunciation_score": assessment_result["pronunciation_score"],
        "completeness_score": assessment_result["completeness_score"],
        # 文本資訊
        "reference_text": assessment_result.get("reference_text", reference_text),
        "recognized_text": assessment_result.get("recognized_text", ""),
        # 舊版相容（簡化的單字詳情）
        "word_details": [
            {
                "word": w["word"],
                "accuracy_score": w["accuracy_score"],
                "error_type": w["error_type"],
            }
            for w in assessment_result["words"]
        ],
        # 新版詳細資訊（包含音節和音素）
        "detailed_words": assessment_result["words"],
        # 分析摘要
        "analysis_summary": {
            "total_words": len(assessment_result["words"]),
            "problematic_words": [
                w["word"]
                for w in assessment_result["words"]
                if w["accuracy_score"] < 80
            ],
            "low_score_phonemes": [],  # 收集低分音素
            "assessment_time": datetime.now().isoformat(),
        },
    }

    # 收集低分音素用於教學建議
    for word in assessment_result["words"]:
        for phoneme in word.get("phonemes", []):
            if phoneme["accuracy_score"] < 70:
                ai_feedback["analysis_summary"]["low_score_phonemes"].append(
                    {
                        "phoneme": phoneme["phoneme"],
                        "score": phoneme["accuracy_score"],
                        "in_word": word["word"],
                    }
                )

    # 如果有韻律分數，加入
    if "prosody_score" in assessment_result:
        ai_feedback["prosody_score"] = assessment_result["prosody_score"]

    progress.ai_feedback = json.dumps(ai_feedback)

    # 更新評估時間
    progress.ai_assessed_at = datetime.now()

    # 更新狀態為已完成
    progress.status = "SUBMITTED"
    progress.submitted_at = datetime.now()

    db.commit()
    db.refresh(progress)

    return progress


@router.post("/assess", response_model=AssessmentResponse)
async def assess_pronunciation_endpoint(
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    progress_id: int = Form(...),
    item_index: Optional[int] = Form(None),  # 題目索引
    assignment_id: Optional[int] = Form(None),
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

    # 轉換音檔格式為 WAV（Azure Speech SDK 需要）
    wav_audio_data = convert_audio_to_wav(audio_data, audio_file.content_type)

    # 進行發音評估
    assessment_result = assess_pronunciation(wav_audio_data, reference_text)

    # 找到學生的 assignment 記錄
    student_assignment_id = None
    if assignment_id:
        student_assignment = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.assignment_id == assignment_id,
                StudentAssignment.student_id == current_student.id,
            )
            .first()
        )
        if student_assignment:
            student_assignment_id = student_assignment.id

    # 儲存結果到資料庫
    updated_progress = save_assessment_result(
        db=db,
        progress_id=progress_id,
        assessment_result=assessment_result,
        reference_text=reference_text,
        item_index=item_index,
        student_assignment_id=student_assignment_id,
    )

    # 回傳結果 - 包含完整的詳細資料
    return AssessmentResponse(
        id=updated_progress.id,
        accuracy_score=assessment_result["accuracy_score"],
        fluency_score=assessment_result["fluency_score"],
        completeness_score=assessment_result["completeness_score"],
        pronunciation_score=assessment_result["pronunciation_score"],
        words=assessment_result["words"],  # 保留舊版相容性
        detailed_words=assessment_result.get("detailed_words"),  # 🔥 新版詳細資料
        word_details=assessment_result.get("word_details"),  # 舊版簡化資料
        reference_text=reference_text,
        recognized_text=assessment_result.get("recognized_text"),
        prosody_score=assessment_result.get("prosody_score"),
        analysis_summary=assessment_result.get("analysis_summary"),
        created_at=updated_progress.submitted_at,
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
    # 查詢有 ai_scores 的 StudentContentProgress 記錄，只顯示當前學生的記錄
    progress_records = (
        db.query(StudentContentProgress)
        .join(StudentContentProgress.student_assignment)
        .filter(
            StudentContentProgress.ai_scores.isnot(None),
            StudentAssignment.student_id == current_student.id,
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
