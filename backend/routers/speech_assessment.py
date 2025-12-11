"""
Azure Speech Assessment Router
處理微軟發音評估 API 的請求
"""

import os
import logging
import asyncio
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
from performance_monitoring import trace_function, start_span, PerformanceSnapshot
from core.thread_pool import get_speech_thread_pool, get_audio_thread_pool
from models import (
    Student,
    StudentContentProgress,
    StudentAssignment,
    StudentItemProgress,
    ContentItem,
    Assignment,
)
from services.quota_service import QuotaService
from services.bigquery_logger import get_bigquery_logger
from sqlalchemy.orm import joinedload

# 設定 logger
logger = logging.getLogger(__name__)

# 🕐 Azure Speech API Timeout 設定（秒）
AZURE_SPEECH_TIMEOUT = 20  # Azure Speech API timeout in seconds

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
    "audio/mp4",  # macOS Safari 使用 MP4 格式
    "video/mp4",  # 某些瀏覽器可能用 video/mp4
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


# Commented out - no longer using Cloud Tasks for background analysis
# class AssessAsyncRequest(BaseModel):
#     """非同步發音評估請求 schema (Cloud Tasks)"""
#     progress_id: int
#     audio_url: str
#     reference_text: str


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
        elif "mp4" in content_type:
            # MP4 格式（macOS Safari）
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_in:
                temp_in.write(audio_data)
                temp_in_path = temp_in.name
            # 使用 pydub 轉換（需要 ffmpeg）
            audio = AudioSegment.from_file(temp_in_path, format="mp4")
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


@trace_function("Azure Speech Assessment")
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
    import time

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

    # 🕐 記錄開始時間（用於計算 Azure API 延遲）
    start_time = time.time()

    try:
        # 設定 Speech SDK
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key, region=speech_region
        )

        # 🔥 設定語言為美式英語以支援韻律評估
        speech_config.speech_recognition_language = "en-US"

        # ⏱️ 設定連線與識別超時（Issue #92 優化）
        # 連線超時：10 秒（比預設的 30 秒快 3 倍）
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            "10000",  # 10 seconds
        )
        # 識別結束超時：2 秒（加快識別完成判斷）
        speech_config.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs,
            "2000",  # 2 seconds
        )
        logger.info(
            "✅ Azure Speech SDK timeout configured: connection=10s, end_silence=2s"
        )

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

        # 🕐 記錄 Azure API 呼叫開始時間
        azure_api_start = time.time()

        # 執行識別
        result = speech_recognizer.recognize_once()

        # 🕐 計算 Azure API 延遲
        azure_api_latency = time.time() - azure_api_start
        logger.info(f"⏱️ Azure Speech API latency: {azure_api_latency:.2f}s")

        # ⚠️ 如果 Azure API 延遲超過 5 秒，記錄警告
        if azure_api_latency > 5.0:
            logger.warning(
                f"⚠️ Azure Speech API slow response detected! "
                f"Latency: {azure_api_latency:.2f}s (threshold: 5s)"
            )

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
        # 🕐 計算總處理時間（包含失敗的情況）
        total_latency = time.time() - start_time

        logger.error(f"Azure Speech API error: {str(e)}")
        logger.error(f"Total processing time before failure: {total_latency:.2f}s")
        logger.debug(f"Error type: {type(e)}")
        import traceback

        logger.debug(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "SERVICE_UNAVAILABLE",
                "message": "Azure Speech API unavailable. Please try again later.",
                "latency_seconds": round(total_latency, 2),
            },
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
        logger.error(
            f"StudentItemProgress with id {progress_id} not found. "
            f"This usually means the recording was not uploaded successfully first."
        )
        raise HTTPException(
            status_code=404,
            detail="Progress record not found - please ensure recording was uploaded first",
        )
    # 更新 AI 評估分數 (StudentItemProgress 使用獨立欄位而非 JSON)
    progress.accuracy_score = assessment_result["accuracy_score"]
    progress.fluency_score = assessment_result["fluency_score"]
    progress.pronunciation_score = assessment_result["pronunciation_score"]
    progress.completeness_score = assessment_result["completeness_score"]

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
@trace_function("Speech Assessment API")
async def assess_pronunciation_endpoint(
    audio_file: UploadFile = File(...),
    reference_text: str = Form(...),
    progress_id: int = Form(...),
    item_index: Optional[int] = Form(None),  # 題目索引
    assignment_id: Optional[int] = Form(None),  # 🔥 這是 StudentAssignment.id (學生作業ID)
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    評估學生發音

    - **audio_file**: 音檔（WAV, WebM, MP3）
    - **reference_text**: 參考文本
    - **progress_id**: StudentContentProgress 記錄的 ID
    """
    perf = PerformanceSnapshot(f"Speech_Assessment_Student_{current_student.id}")

    # 檢查檔案格式
    if audio_file.content_type not in ALLOWED_AUDIO_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Allowed formats: {', '.join(ALLOWED_AUDIO_FORMATS)}",
        )

    # 檢查檔案大小
    with start_span("Read Audio File"):
        audio_data = await audio_file.read()
        if len(audio_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB",
            )
        perf.checkpoint("Audio File Read")

    # 轉換音檔格式為 WAV（Azure Speech SDK 需要）
    # ⚡ 音檔轉換也可能耗時，使用自訂線程池避免阻塞
    with start_span("Convert Audio to WAV"):
        import time

        conversion_start = time.time()
        loop = asyncio.get_event_loop()
        audio_pool = get_audio_thread_pool()
        wav_audio_data = await loop.run_in_executor(
            audio_pool, convert_audio_to_wav, audio_data, audio_file.content_type
        )
        conversion_time = time.time() - conversion_start
        logger.info(f"⏱️ Audio conversion time: {conversion_time:.2f}s")
        perf.checkpoint("Audio Conversion Complete")

    # 🎯 找到學生的 assignment 與老師（配額檢查）
    student_assignment_id = None
    teacher = None
    assignment = None

    # 🔍 Debug: 檢查前端傳入的 assignment_id (實際上是 StudentAssignment.id)
    print(
        f"🔍 Received assignment_id (StudentAssignment.id) from frontend: {assignment_id}"
    )
    logger.info(f"🔍 Received assignment_id (StudentAssignment.id): {assignment_id}")

    if assignment_id:
        print("✅ assignment_id exists, querying StudentAssignment by ID...")
        # 🔥 優化：使用 joinedload 減少資料庫查詢次數（3次 → 1次）
        student_assignment = (
            db.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment).joinedload(Assignment.teacher)
            )
            .filter(
                StudentAssignment.id == assignment_id,
                StudentAssignment.student_id == current_student.id,
            )
            .first()
        )
        if student_assignment:
            student_assignment_id = student_assignment.id
            print(
                "✅ Found StudentAssignment: "
                f"id={student_assignment.id}, "
                f"assignment_id={student_assignment.assignment_id}"
            )

            # 從已經 join 的物件直接取得 (不用再查詢)
            assignment = student_assignment.assignment
            if assignment:
                print(
                    f"✅ Found Assignment: {assignment.id}, teacher_id={assignment.teacher_id}"
                )
                teacher = assignment.teacher
                if teacher:
                    print(f"✅ Found Teacher: {teacher.id} ({teacher.name})")
                else:
                    print(f"❌ Teacher not found for assignment {assignment.id}")
            else:
                print(
                    f"❌ Assignment not found with id {student_assignment.assignment_id}"
                )
        else:
            print(
                f"❌ StudentAssignment not found for id={assignment_id}, student_id={current_student.id}"
            )

    # 📊 配額檢查（僅記錄狀態，不阻擋學生學習）
    if teacher and assignment:
        # 計算錄音時長
        try:
            audio = AudioSegment.from_file(BytesIO(audio_data))
            duration_seconds = len(audio) / 1000.0  # 毫秒轉秒

            # ⚠️ 業務需求：配額超限不應阻擋學生學習，只記錄使用量
            if not QuotaService.check_quota(teacher, int(duration_seconds)):
                quota_info = QuotaService.get_quota_info(teacher)
                logger.warning(
                    f"⚠️ Teacher {teacher.id} quota exceeded, but allowing student to continue learning. "
                    f"Required: {int(duration_seconds)}s, Available: {quota_info['quota_remaining']}s"
                )
            else:
                logger.info(
                    f"✅ Quota check passed: {duration_seconds:.1f}s for teacher {teacher.id}"
                )
        except Exception as e:
            logger.error(f"❌ Quota check failed: {e}")
            # 計算時長失敗，允許繼續評分

    # 進行發音評估（Azure Speech SDK）
    # ⚡ 使用自訂語音線程池避免阻塞 event loop
    # 🕐 加入 timeout 保護避免長時間阻塞
    with start_span(
        "Azure Speech API Call", {"reference_text_length": len(reference_text)}
    ):
        loop = asyncio.get_event_loop()
        speech_pool = get_speech_thread_pool()

        try:
            # 🕐 使用 asyncio.wait_for 加入 timeout（預設 20 秒）
            assessment_result = await asyncio.wait_for(
                loop.run_in_executor(
                    speech_pool, assess_pronunciation, wav_audio_data, reference_text
                ),
                timeout=AZURE_SPEECH_TIMEOUT,
            )
            perf.checkpoint("Azure Speech Assessment Complete")

        except asyncio.TimeoutError:
            # 🕐 Azure API timeout - 記錄到 BigQuery
            timeout_duration = AZURE_SPEECH_TIMEOUT
            logger.error(
                f"❌ Azure Speech API timeout after {timeout_duration}s "
                f"for student {current_student.id}"
            )

            # 📊 記錄到 BigQuery
            bigquery_logger = get_bigquery_logger()
            await bigquery_logger.log_audio_error(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error_type": "api_timeout",
                    "error_message": f"Azure Speech API timeout after {timeout_duration}s",
                    "student_id": current_student.id,
                    "assignment_id": assignment_id,
                    "audio_size_bytes": len(audio_data),
                    "reference_text": reference_text,
                    "timeout_seconds": timeout_duration,
                    "environment": os.getenv("ENVIRONMENT", "unknown"),
                }
            )

            raise HTTPException(
                status_code=503,
                detail={
                    "error": "API_TIMEOUT",
                    "message": f"語音評估服務處理超時（{timeout_duration} 秒），請稍後再試",
                    "timeout_seconds": timeout_duration,
                },
            )

        except HTTPException as e:
            # 🔥 捕捉 assess_pronunciation 內部的 503 錯誤並記錄到 BigQuery
            if e.status_code == 503:
                logger.error(
                    f"❌ Azure Speech API error (503) for student {current_student.id}: {e.detail}"
                )

                # 📊 記錄到 BigQuery
                bigquery_logger = get_bigquery_logger()
                error_detail = (
                    e.detail
                    if isinstance(e.detail, dict)
                    else {"message": str(e.detail)}
                )
                await bigquery_logger.log_audio_error(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "error_type": "api_error_503",
                        "error_message": error_detail.get("message", str(e.detail)),
                        "student_id": current_student.id,
                        "assignment_id": assignment_id,
                        "audio_size_bytes": len(audio_data),
                        "reference_text": reference_text,
                        "latency_seconds": error_detail.get("latency_seconds"),
                        "environment": os.getenv("ENVIRONMENT", "unknown"),
                    }
                )

            # 重新拋出原始 HTTPException
            raise

    # 📊 評分成功後扣除配額
    if teacher and assignment:
        try:
            audio = AudioSegment.from_file(BytesIO(audio_data))
            duration_seconds = len(audio) / 1000.0

            # 扣除老師的配額並記錄
            QuotaService.deduct_quota(
                db=db,
                teacher=teacher,
                student_id=current_student.id,
                assignment_id=assignment.id,
                feature_type="speech_assessment",
                unit_count=duration_seconds,
                unit_type="秒",
                feature_detail={
                    "reference_text": reference_text,
                    "accuracy_score": assessment_result["accuracy_score"],
                    "audio_size_bytes": len(audio_data),
                },
            )
            logger.info(
                f"✅ Deducted {duration_seconds:.1f}s quota from teacher {teacher.id} "
                f"for student {current_student.id} assignment {assignment.id}"
            )
        except HTTPException as e:
            # 配額扣除失敗（可能是硬限制超額），向學生顯示友善訊息
            if e.status_code == 402 and isinstance(e.detail, dict):
                error_type = e.detail.get("error")
                if error_type == "QUOTA_HARD_LIMIT_EXCEEDED":
                    # 硬限制超額，學生看到友善訊息
                    logger.error(
                        f"❌ Quota hard limit exceeded for teacher {teacher.id}, "
                        f"blocking student {current_student.id}"
                    )
                    raise HTTPException(
                        status_code=402,
                        detail={
                            "error": "QUOTA_HARD_LIMIT_EXCEEDED",
                            "message": "老師的配額已用完（含緩衝額度），請聯繫老師續費後再繼續使用",
                            "teacher_quota_info": e.detail,
                        },
                    )
            # 其他 HTTPException 直接拋出
            raise
        except Exception as e:
            logger.error(f"❌ Quota deduction failed: {e}")
            # 其他錯誤只記錄，不影響評分結果

    # 儲存結果到資料庫
    with start_span("Save Assessment Result to Database"):
        updated_progress = save_assessment_result(
            db=db,
            progress_id=progress_id,
            assessment_result=assessment_result,
            reference_text=reference_text,
            item_index=item_index,
            student_assignment_id=student_assignment_id,
        )
        perf.checkpoint("Database Save Complete")

    # 完成效能追蹤
    perf.finish()

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
    # 🔥 優化：使用 joinedload 預載 content，避免 N+1 查詢
    progress_records = (
        db.query(StudentContentProgress)
        .join(StudentContentProgress.student_assignment)
        .options(joinedload(StudentContentProgress.content))
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


@router.delete("/assessment/{assignment_id}/item/{item_index}")
async def delete_item_recording_and_assessment(
    assignment_id: int,
    item_index: int,
    db: Session = Depends(get_db),
    current_student: Student = Depends(get_current_student),
):
    """
    刪除學生作業的某個 item 的錄音和評估結果

    清空 StudentItemProgress 中的：
    - 錄音 URL (recording_url)
    - 評估分數 (accuracy_score, fluency_score, pronunciation_score)
    - AI 反饋 (ai_feedback, transcription)
    - 評估時間 (ai_assessed_at)

    Args:
        assignment_id: StudentAssignment ID
        item_index: Content item 的索引

    Returns:
        成功訊息
    """
    logger.info(
        f"Student {current_student.id} deleting recording for assignment {assignment_id}, item {item_index}"
    )

    # 1. 查找 StudentAssignment（確認權限）
    student_assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not student_assignment:
        logger.warning(
            f"Assignment {assignment_id} not found or not owned by student {current_student.id}"
        )
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or you don't have permission to delete this recording",
        )

    # 2. 獲取作業的所有 content_items（按 order_index 排序）
    # 首先獲取作業的 content_ids
    progress_records = (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id == student_assignment.id)
        .order_by(StudentContentProgress.order_index)
        .all()
    )

    if not progress_records:
        logger.warning(
            f"No content progress records found for assignment {assignment_id}"
        )
        return {"message": "No recording or assessment to delete", "deleted": False}

    # 獲取所有 content_items
    content_ids = [p.content_id for p in progress_records]
    all_content_items = []
    for content_id in content_ids:
        items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id == content_id)
            .order_by(ContentItem.order_index)
            .all()
        )
        all_content_items.extend(items)

    # 檢查 item_index 是否有效
    if item_index < 0 or item_index >= len(all_content_items):
        logger.warning(
            f"Invalid item_index {item_index} for assignment {assignment_id} (total items: {len(all_content_items)})"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Invalid item index {item_index}",
        )

    # 獲取對應的 ContentItem
    target_item = all_content_items[item_index]

    # 3. 查找 StudentItemProgress
    progress = (
        db.query(StudentItemProgress)
        .filter(
            StudentItemProgress.student_assignment_id == student_assignment.id,
            StudentItemProgress.content_item_id == target_item.id,
        )
        .first()
    )

    if not progress:
        # 如果沒有記錄，直接返回成功（冪等性）
        logger.info(
            f"No progress record for assignment {assignment_id}, "
            f"item {item_index} (content_item_id: {target_item.id})"
        )
        return {
            "message": "No recording or assessment to delete",
            "deleted": False,
        }

    # 4. 清空所有錄音和評估相關欄位
    progress.recording_url = None
    progress.answer_text = None
    progress.transcription = None
    progress.accuracy_score = None
    progress.fluency_score = None
    progress.pronunciation_score = None
    progress.completeness_score = None
    progress.ai_feedback = None
    progress.ai_assessed_at = None
    progress.submitted_at = None

    # 5. 重置狀態為未開始
    progress.status = "NOT_STARTED"

    db.commit()

    logger.info(
        f"Successfully cleared recording and assessment for assignment {assignment_id}, item {item_index}"
    )

    return {
        "message": "Recording and assessment deleted successfully",
        "deleted": True,
        "progress_id": progress.id,
    }


# ===== 測試 Endpoint：驗證 Thread Pool 並發 =====


@router.get("/test-concurrent")
async def test_thread_pool_concurrent():
    """
    測試 Thread Pool 並發處理能力
    模擬 Azure Speech API 的阻塞操作（1 秒）
    """
    import time

    loop = asyncio.get_event_loop()
    pool = get_speech_thread_pool()

    def simulate_azure_call():
        """模擬 Azure Speech API 呼叫（阻塞 1 秒）"""
        time.sleep(1)
        return {"simulation": True, "duration": 1.0, "worker": "speech_pool"}

    start = time.time()
    result = await loop.run_in_executor(pool, simulate_azure_call)
    elapsed = time.time() - start

    return {
        "result": result,
        "elapsed_seconds": round(elapsed, 2),
        "thread_pool": {"max_workers": 20, "type": "speech_pool"},
    }


# Commented out - no longer using Cloud Tasks for background analysis
# This endpoint can be re-enabled later for teacher-triggered batch analysis
# @router.post("/assess-async")
# async def assess_async(
#     request: AssessAsyncRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     非同步發音評估端點 (Cloud Task 呼叫)
#
#     此端點由 Cloud Tasks 呼叫，不需要認證 token，因為是內部服務呼叫。
#     如果需要加強安全性，可以檢查請求來源 IP 或使用服務帳號認證。
#     """
#     pass
