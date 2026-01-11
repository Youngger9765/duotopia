"""
Grading operations (AI and manual)
"""

from typing import List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_
from sqlalchemy.orm.attributes import flag_modified

from database import get_db
from performance_monitoring import trace_function, start_span, PerformanceSnapshot
from models import (
    Teacher,
    Student,
    Classroom,
    Content,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    AssignmentStatus,
)
from .validators import AIGradingRequest, AIGradingResponse, AIScores
from .dependencies import get_current_teacher
from .utils import (
    process_audio_with_whisper,
    calculate_text_similarity,
    calculate_pronunciation_score,
    calculate_fluency_score,
    calculate_wpm,
    generate_ai_feedback,
)

router = APIRouter()


@router.post("/{assignment_id}/ai-grade", response_model=AIGradingResponse)
@trace_function("AI Grade Assignment")
async def ai_grade_assignment(
    assignment_id: int,
    request: AIGradingRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    AI 自動批改作業
    只有教師可以觸發批改
    """
    start_time = datetime.now()
    perf = PerformanceSnapshot(f"AI_Grade_Assignment_{assignment_id}")

    # 1. 取得作業並驗證權限
    with start_span("Database Query - Get Assignment"):
        assignment = (
            db.query(StudentAssignment)
            .join(Classroom)
            .filter(
                and_(
                    StudentAssignment.id == assignment_id,
                    Classroom.teacher_id == current_teacher.id,
                )
            )
            .first()
        )

        if not assignment:
            raise HTTPException(
                status_code=404,
                detail="Assignment not found or you don't have permission",
            )
        perf.checkpoint("Assignment Query")

    # 2. 檢查作業狀態
    with start_span("Validate Assignment Status"):
        if assignment.status != AssignmentStatus.SUBMITTED:
            raise HTTPException(
                status_code=400, detail="Assignment must be submitted before grading"
            )
        perf.checkpoint("Status Validation")

    # 3. 簡化版 - 不查詢 Content
    content = None

    # 4. 取得提交資料（新架構從 StudentContentProgress 取得）
    # 暫時簡化處理

    try:
        # 5. 處理批改邏輯
        if request.mock_mode and request.mock_data:
            # 使用模擬資料（測試模式）
            with start_span("Mock Mode - Load Test Data"):
                whisper_result = request.mock_data
                perf.checkpoint("Mock Data Loaded")
        else:
            # 準備預期文字
            with start_span("Prepare Expected Texts"):
                expected_texts = []
                if hasattr(content, "content_items"):
                    for item in content.content_items:
                        expected_texts.append(
                            item.text if hasattr(item, "text") else ""
                        )
                perf.checkpoint("Text Preparation")

            # 呼叫 Whisper API（這裡最可能慢）
            with start_span(
                "Whisper API Call", {"audio_count": len(request.audio_urls or [])}
            ):
                whisper_result = await process_audio_with_whisper(
                    request.audio_urls or [], expected_texts
                )
                perf.checkpoint("Whisper API Complete")

        # 6. 分析批改結果
        with start_span(
            "Calculate AI Scores",
            {"transcription_count": len(whisper_result.get("transcriptions", []))},
        ):
            transcriptions = whisper_result.get("transcriptions", [])
            audio_analysis = whisper_result.get("audio_analysis", {})

            # 計算各項評分
            total_accuracy = 0
            total_pronunciation = 0
            detailed_results = []

            for transcription in transcriptions:
                expected = transcription.get("expected_text", "")
                actual = transcription.get("transcribed_text", "")
                words = transcription.get("words", [])

                # 計算準確率
                accuracy = calculate_text_similarity(expected, actual) * 100

                # 計算發音評分
                pronunciation = calculate_pronunciation_score(words)

                total_accuracy += accuracy
                total_pronunciation += pronunciation

                detailed_results.append(
                    {
                        "item_id": transcription.get("item_id", 0),
                        "expected_text": expected,
                        "transcribed_text": actual,
                        "accuracy_score": accuracy,
                        "pronunciation_score": pronunciation,
                        "word_count": len(expected.split()) if expected else 0,
                    }
                )

            # 計算平均值
            item_count = len(transcriptions) if transcriptions else 1
            avg_accuracy = total_accuracy / item_count
            avg_pronunciation = total_pronunciation / item_count

            # 計算流暢度
            fluency = calculate_fluency_score(audio_analysis)

            # 計算語速
            all_transcribed = " ".join(
                [t.get("transcribed_text", "") for t in transcriptions]
            )
            total_duration = audio_analysis.get("total_duration", 10.0)
            wpm = calculate_wpm(all_transcribed, total_duration)

            # 建立評分物件
            ai_scores = AIScores(
                pronunciation=round(avg_pronunciation, 1),
                fluency=round(fluency, 1),
                accuracy=round(avg_accuracy, 1),
                wpm=wpm,
            )

            # 計算整體評分（加權平均）
            overall_score = round(
                ai_scores.pronunciation * 0.3
                + ai_scores.fluency * 0.3
                + ai_scores.accuracy * 0.4,
                1,
            )

            # 生成回饋
            feedback = generate_ai_feedback(ai_scores, detailed_results)
            perf.checkpoint("Score Calculation Complete")

        # 7. 更新資料庫
        with start_span("Database Update - Save Results"):
            # 更新作業狀態
            assignment.status = AssignmentStatus.GRADED
            assignment.score = overall_score
            assignment.feedback = feedback
            assignment.graded_at = datetime.now(timezone.utc)

            db.commit()
            perf.checkpoint("Database Update Complete")

        # 8. 計算處理時間
        processing_time = (datetime.now() - start_time).total_seconds()
        perf.finish()

        return AIGradingResponse(
            assignment_id=assignment_id,
            ai_scores=ai_scores,
            overall_score=overall_score,
            feedback=feedback,
            detailed_feedback=detailed_results,
            graded_at=datetime.now(),
            processing_time_seconds=round(processing_time, 2),
        )

    except Exception as e:
        # 發生錯誤時回滾
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI grading failed: {str(e)}")


@router.get("/{assignment_id}/submissions")
async def get_assignment_submissions(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """獲取作業的所有提交（教師用）"""
    # 獲取基礎作業資訊
    base_assignment = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.id == assignment_id)
        .first()
    )

    if not base_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 獲取同一內容的所有學生作業
    submissions = (
        db.query(StudentAssignment)
        .join(Student)
        .filter(
            StudentAssignment.classroom_id == base_assignment.classroom_id,
        )
        .all()
    )

    # 優化：批次查詢學生和進度資料，避免 N+1 問題
    student_ids = [sub.student_id for sub in submissions]
    students_dict = {
        s.id: s for s in db.query(Student).filter(Student.id.in_(student_ids)).all()
    }

    submission_ids = [sub.id for sub in submissions]
    from collections import defaultdict

    progress_dict = defaultdict(list)
    for progress in (
        db.query(StudentContentProgress)
        .filter(StudentContentProgress.student_assignment_id.in_(submission_ids))
        .all()
    ):
        progress_dict[progress.student_assignment_id].append(progress)

    result = []
    for sub in submissions:
        student = students_dict.get(sub.student_id)
        if not student:
            continue

        # 取得學生的內容進度（新架構）
        progress_list = progress_dict.get(sub.id, [])

        result.append(
            {
                "assignment_id": sub.id,
                "student_id": student.id,
                "student_name": student.name,
                "status": sub.status.value,
                "submitted_at": (
                    sub.submitted_at.isoformat() if sub.submitted_at else None
                ),
                "score": sub.score,
                "feedback": sub.feedback,
                "content_progress": [
                    {
                        "content_id": p.content_id,
                        "status": p.status.value if p.status else "NOT_STARTED",
                        "response_data": p.response_data,
                    }
                    for p in progress_list
                ],
            }
        )

    return result


@router.get("/{assignment_id}/submissions/{student_id}")
async def get_student_submission(
    assignment_id: int,
    student_id: int,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """獲取單個學生的作業提交詳情（教師批改用）"""
    import json

    # 直接查詢學生作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Student assignment not found")

    # 獲取學生資訊
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 從資料庫獲取真實的 content 題目資料
    actual_assignment_id = assignment.assignment_id

    # 查詢作業關聯的 contents (按 order_index 排序)
    assignment_contents = (
        db.query(AssignmentContent, Content)
        .join(Content)
        .filter(AssignmentContent.assignment_id == actual_assignment_id)
        .order_by(AssignmentContent.order_index)
        .all()
    )

    submissions = []
    content_groups = []  # 用於儲存分組資訊

    # 獲取所有 StudentItemProgress 記錄（新系統）
    item_progress_records = (
        db.query(StudentItemProgress)
        .filter(StudentItemProgress.student_assignment_id == assignment.id)
        .all()
    )

    # 建立以 content_item_id 為 key 的字典，方便查詢
    progress_by_item_id = {}
    for progress in item_progress_records:
        progress_by_item_id[progress.content_item_id] = progress

    # 如果有真實的 content 資料
    if assignment_contents:
        item_index = 0  # 全局題目索引
        for ac, content in assignment_contents:
            if hasattr(content, "content_items") and content.content_items:
                # 建立內容群組
                group = {
                    "content_id": content.id,
                    "content_title": content.title,
                    "content_type": (
                        content.type.value if content.type else "READING_ASSESSMENT"
                    ),
                    "submissions": [],
                }

                # 使用 ContentItem 關聯
                items_data = list(content.content_items)
                for local_item_index, item in enumerate(items_data):
                    submission = {
                        "content_id": content.id,
                        "content_title": content.title,
                        "content_item_id": item.id,
                        "question_text": item.text if hasattr(item, "text") else "",
                        "question_translation": item.translation
                        if hasattr(item, "translation")
                        else "",
                        "question_audio_url": item.audio_url
                        if hasattr(item, "audio_url")
                        else "",
                        "student_answer": "",
                        "student_audio_url": "",
                        "transcript": "",
                        "duration": 0,
                        "item_index": item_index,
                        "feedback": "",
                        "passed": None,
                    }

                    # 使用 content_item_id 來獲取對應的 StudentItemProgress 記錄
                    item_progress = progress_by_item_id.get(item.id)

                    # 從 StudentItemProgress 直接獲取資料
                    if item_progress:
                        # 加入老師批改的評語和通過狀態
                        if item_progress.teacher_feedback:
                            submission["feedback"] = item_progress.teacher_feedback
                        if item_progress.teacher_passed is not None:
                            submission["passed"] = item_progress.teacher_passed
                        # 學生錄音檔案
                        if item_progress.recording_url:
                            submission["audio_url"] = item_progress.recording_url
                            submission[
                                "student_audio_url"
                            ] = item_progress.recording_url

                        # 作答狀態
                        if item_progress.status == "SUBMITTED":
                            submission["status"] = "submitted"

                        # AI 評分物件
                        if item_progress.ai_feedback:
                            try:
                                ai_data = (
                                    json.loads(item_progress.ai_feedback)
                                    if isinstance(item_progress.ai_feedback, str)
                                    else item_progress.ai_feedback
                                )
                            except (json.JSONDecodeError, TypeError):
                                ai_data = None

                            if ai_data and isinstance(ai_data, dict):
                                submission["ai_scores"] = {
                                    "accuracy_score": float(
                                        ai_data.get("accuracy_score", 0)
                                    ),
                                    "fluency_score": float(
                                        ai_data.get("fluency_score", 0)
                                    ),
                                    "pronunciation_score": float(
                                        ai_data.get("pronunciation_score", 0)
                                    ),
                                    "completeness_score": float(
                                        ai_data.get("completeness_score", 0)
                                    ),
                                    "overall_score": float(
                                        ai_data.get("overall_score", 0)
                                    )
                                    if ai_data.get("overall_score")
                                    else (
                                        (
                                            float(ai_data.get("accuracy_score", 0))
                                            + float(ai_data.get("fluency_score", 0))
                                            + float(
                                                ai_data.get("pronunciation_score", 0)
                                            )
                                            + float(
                                                ai_data.get("completeness_score", 0)
                                            )
                                        )
                                        / 4
                                    ),
                                    "word_details": ai_data.get("word_details", []),
                                }

                    submissions.append(submission)
                    group["submissions"].append(submission)
                    item_index += 1

                content_groups.append(group)

    # 如果沒有真實資料，使用模擬資料 (標記為 MOCK)
    if not submissions:
        print(
            f"WARNING: No real content found for assignment_id={actual_assignment_id}, using MOCK data"
        )
        submissions = [
            {
                "question_text": "[MOCK] How are you today?",
                "question_translation": "[MOCK] 你今天好嗎？",
                "question_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
                "student_answer": "I am fine, thank you!",
                "student_audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
                "transcript": "I am fine thank you",
                "duration": 3.5,
                "feedback": "",
                "passed": None,
            },
        ]

    return {
        "student_id": student.id,
        "student_name": student.name,
        "student_email": student.email,
        "status": assignment.status.value,
        "submitted_at": (
            assignment.submitted_at.isoformat() if assignment.submitted_at else None
        ),
        "content_type": "SPEAKING_PRACTICE",
        "submissions": submissions,
        "content_groups": content_groups,
        "current_score": assignment.score,
        "current_feedback": assignment.feedback,
    }


@router.post("/{assignment_id}/grade")
async def grade_student_assignment(
    assignment_id: int,
    grade_data: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """教師批改學生作業"""
    import logging

    # 獲取學生ID
    student_id = grade_data.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID is required")

    # 使用 assignment_id (主作業ID) 和 student_id 查詢學生作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 確認教師有權限批改（檢查班級關聯）
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == assignment.classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=403, detail="Not authorized to grade this assignment"
        )

    # 更新評分資訊
    assignment.score = grade_data.get("score")
    assignment.feedback = grade_data.get("feedback")

    # 只有在 update_status 為 True 時才更新狀態
    if grade_data.get("update_status", True):
        assignment.status = AssignmentStatus.GRADED
        assignment.graded_at = datetime.now(timezone.utc)

    # 更新個別題目的評分和回饋
    if "item_results" in grade_data:
        # 獲取所有內容進度記錄
        progress_records = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == assignment.id)
            .order_by(StudentContentProgress.order_index)
            .all()
        )

        # 建立 item 結果的索引映射
        item_feedback_map = {}
        for item_result in grade_data["item_results"]:
            item_feedback_map[item_result.get("item_index")] = item_result

        # 優化：批次查詢所有 content，避免 N+1 問題
        content_ids = {progress.content_id for progress in progress_records}
        content_dict = {
            c.id: c
            for c in db.query(Content)
            .filter(Content.id.in_(content_ids))
            .options(selectinload(Content.content_items))
            .all()
        }

        # Preload all StudentItemProgress (avoid N+1)
        all_item_progress = (
            db.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == assignment.id)
            .all()
        )
        item_progress_map = {ip.content_item_id: ip for ip in all_item_progress}

        # 對每個 progress record，儲存其對應的所有 item 回饋
        current_item_index = 0
        for progress in progress_records:
            # 獲取此 content 的所有項目數量
            content = content_dict.get(progress.content_id)
            if content and hasattr(content, "content_items"):
                items_count = len(content.content_items)

                # 收集此 content 的所有 item 回饋
                items_feedback = []
                for i in range(items_count):
                    if current_item_index in item_feedback_map:
                        item_data = item_feedback_map[current_item_index]
                        items_feedback.append(
                            {
                                "feedback": item_data.get("feedback", ""),
                                "passed": item_data.get("passed"),
                                "score": item_data.get("score"),
                            }
                        )

                        # 更新 StudentItemProgress 表中的 teacher_feedback
                        if (
                            item_data.get("feedback")
                            or item_data.get("passed") is not None
                        ):
                            item_progress = item_progress_map.get(
                                content.content_items[i].id
                            )

                            # 如果記錄不存在，創建一個
                            if not item_progress:
                                logger = logging.getLogger(__name__)
                                logger.info(
                                    f"Creating StudentItemProgress on-demand: "
                                    f"assignment_id={assignment.id}, "
                                    f"content_item_id={content.content_items[i].id}"
                                )

                                try:
                                    item_progress = StudentItemProgress(
                                        student_assignment_id=assignment.id,
                                        content_item_id=content.content_items[i].id,
                                        status="NOT_SUBMITTED",
                                        answer_text=None,
                                        recording_url=None,
                                        accuracy_score=None,
                                        fluency_score=None,
                                        pronunciation_score=None,
                                        ai_feedback=None,
                                        review_status="PENDING",
                                    )
                                    db.add(item_progress)
                                    db.flush()
                                except Exception as e:
                                    logger.error(
                                        f"Failed to create StudentItemProgress: {e}"
                                    )
                                    raise HTTPException(
                                        status_code=500,
                                        detail="Failed to save teacher feedback",
                                    )

                            # 更新老師評語和相關欄位
                            item_progress.teacher_feedback = item_data.get(
                                "feedback", ""
                            )
                            item_progress.teacher_review_score = (
                                item_data.get("score")
                                if item_data.get("score")
                                else item_progress.teacher_review_score
                            )
                            item_progress.teacher_passed = item_data.get("passed")
                            item_progress.teacher_reviewed_at = datetime.now(
                                timezone.utc
                            )
                            item_progress.teacher_id = current_teacher.id
                            item_progress.review_status = "REVIEWED"
                    else:
                        items_feedback.append(
                            {"feedback": "", "passed": None, "score": None}
                        )
                    current_item_index += 1

                # 將所有 item 回饋儲存在 response_data JSON 欄位中
                new_response_data = (
                    progress.response_data.copy() if progress.response_data else {}
                )
                new_response_data["item_feedbacks"] = items_feedback
                progress.response_data = new_response_data
                flag_modified(progress, "response_data")

                # 更新整體的 checked 狀態
                all_passed = all(
                    item.get("passed") is True
                    for item in items_feedback
                    if item.get("passed") is not None
                )
                any_failed = any(item.get("passed") is False for item in items_feedback)
                if any_failed:
                    progress.checked = False
                elif all_passed and len(items_feedback) > 0:
                    progress.checked = True

    db.commit()

    return {
        "message": "Assignment graded successfully",
        "assignment_id": assignment.id,
        "student_id": student_id,
        "score": assignment.score,
        "feedback": assignment.feedback,
        "graded_at": assignment.graded_at.isoformat() if assignment.graded_at else None,
    }


@router.post("/{assignment_id}/set-in-progress")
async def set_assignment_in_progress(
    assignment_id: int,
    data: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """設定為批改中狀態"""
    # 獲取學生ID
    student_id = data.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID is required")

    # 使用 assignment_id (主作業ID) 和 student_id 查詢學生作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 確認教師有權限（檢查班級關聯）
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == assignment.classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this assignment"
        )

    # 檢查當前狀態
    if assignment.status in [AssignmentStatus.SUBMITTED, AssignmentStatus.RESUBMITTED]:
        return {
            "message": "Assignment is already in progress",
            "assignment_id": assignment.id,
            "student_id": student_id,
            "status": assignment.status.value,
        }

    # 根據之前的狀態決定要設定成哪種批改中狀態
    if assignment.status == AssignmentStatus.RETURNED:
        if assignment.resubmitted_at and (
            not assignment.submitted_at
            or assignment.resubmitted_at > assignment.submitted_at
        ):
            assignment.status = AssignmentStatus.RESUBMITTED
        else:
            assignment.status = AssignmentStatus.SUBMITTED
    elif assignment.status == AssignmentStatus.GRADED:
        if assignment.resubmitted_at and (
            not assignment.submitted_at
            or assignment.resubmitted_at > assignment.submitted_at
        ):
            assignment.status = AssignmentStatus.RESUBMITTED
        else:
            assignment.status = AssignmentStatus.SUBMITTED
        assignment.graded_at = None

    db.commit()

    return {
        "message": "Assignment set to in progress",
        "assignment_id": assignment.id,
        "student_id": student_id,
        "status": assignment.status.value,
    }


@router.post("/{assignment_id}/return-for-revision")
async def return_for_revision(
    assignment_id: int,
    data: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """要求訂正 - 要求學生修改作業"""
    # 獲取學生ID
    student_id = data.get("student_id")
    if not student_id:
        raise HTTPException(status_code=400, detail="Student ID is required")

    # 使用 assignment_id (主作業ID) 和 student_id 查詢學生作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.student_id == student_id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 確認教師有權限（檢查班級關聯）
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == assignment.classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=403, detail="Not authorized to return this assignment"
        )

    # 檢查是否已經是要求訂正狀態
    if assignment.status == AssignmentStatus.RETURNED:
        return {
            "message": "Assignment is already in returned status",
            "assignment_id": assignment.id,
            "student_id": student_id,
            "status": assignment.status.value,
            "returned_at": (
                assignment.returned_at.isoformat() if assignment.returned_at else None
            ),
        }

    # 更新狀態為 RETURNED（要求訂正）
    assignment.status = AssignmentStatus.RETURNED
    assignment.returned_at = datetime.now(timezone.utc)

    # 可選：儲存退回訊息
    message = data.get("message", "")
    if message and hasattr(assignment, "return_message"):
        assignment.return_message = message

    db.commit()

    return {
        "message": "Assignment returned for revision",
        "assignment_id": assignment.id,
        "student_id": student_id,
        "status": assignment.status.value,
        "returned_at": assignment.returned_at.isoformat(),
    }


@router.post("/{assignment_id}/manual-grade")
async def manual_grade_assignment(
    assignment_id: int,
    grade_data: dict,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """手動評分（教師用）"""
    # 獲取作業
    assignment = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 驗證教師權限（檢查作業是否屬於教師的班級）
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == assignment.classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=403, detail="Not authorized to grade this assignment"
        )

    # 更新評分
    assignment.score = grade_data.get("score")
    assignment.feedback = grade_data.get("feedback")
    assignment.status = AssignmentStatus.GRADED
    assignment.graded_at = datetime.now(timezone.utc)

    # 更新內容進度評分（新架構）
    if "detailed_scores" in grade_data:
        progress_records = (
            db.query(StudentContentProgress)
            .filter(StudentContentProgress.student_assignment_id == assignment_id)
            .all()
        )

        for progress in progress_records:
            if "ai_scores" in grade_data.get("detailed_scores", {}):
                progress.ai_scores = grade_data["detailed_scores"]["ai_scores"]
                progress.ai_feedback = grade_data.get("feedback")
                progress.checked = True
                progress.score = grade_data.get("score")

    db.commit()

    return {
        "id": assignment.id,
        "status": assignment.status.value,
        "score": assignment.score,
        "feedback": assignment.feedback,
        "graded_at": assignment.graded_at.isoformat(),
        "message": "Assignment graded successfully",
    }
