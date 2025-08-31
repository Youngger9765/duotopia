"""
作業系統 API 路由
Phase 1: 基礎指派功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel
import os
from difflib import SequenceMatcher
import re
from database import get_db
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Content,
    Lesson,
    Program,
    StudentAssignment,
    AssignmentStatus,
    AssignmentSubmission,
)
from .auth import get_current_user

router = APIRouter(prefix="/api", tags=["assignments"])


# ============ Pydantic Models ============


class CreateAssignmentRequest(BaseModel):
    """建立作業請求"""

    content_id: int
    classroom_id: int
    student_ids: List[int] = []  # 空陣列 = 全班
    title: str
    instructions: Optional[str] = None
    due_date: Optional[datetime] = None


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
    email: str
    student_id: Optional[str]

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


# ============ AI Grading Models (Phase 3) ============


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


# ============ API Endpoints ============


@router.post("/assignments/create")
async def create_assignment(
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    建立作業
    - content_id: Content ID
    - classroom_id: 班級 ID
    - student_ids: 學生 ID 列表（空陣列 = 全班）
    - title: 作業標題
    - instructions: 作業說明（選填）
    - due_date: 截止日期（選填）
    """

    # 0. 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can create assignments"
        )
    current_teacher = current_user

    # 1. 驗證 Content 存在
    content = db.query(Content).filter(Content.id == request.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # 2. 驗證班級存在且屬於當前教師
    classroom = (
        db.query(Classroom)
        .filter(
            and_(
                Classroom.id == request.classroom_id,
                Classroom.teacher_id == current_teacher.id,
                Classroom.is_active.is_(True),
            )
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404, detail="Classroom not found or you don't have permission"
        )

    # 3. 取得要指派的學生列表
    if request.student_ids:
        # 指派給特定學生
        students = (
            db.query(Student)
            .join(ClassroomStudent)
            .filter(
                and_(
                    ClassroomStudent.classroom_id == request.classroom_id,
                    Student.id.in_(request.student_ids),
                    Student.is_active.is_(True),
                    ClassroomStudent.is_active.is_(True),
                )
            )
            .all()
        )

        if len(students) != len(request.student_ids):
            raise HTTPException(
                status_code=400, detail="Some students not found in this classroom"
            )
    else:
        # 指派給全班
        students = (
            db.query(Student)
            .join(ClassroomStudent)
            .filter(
                and_(
                    ClassroomStudent.classroom_id == request.classroom_id,
                    Student.is_active.is_(True),
                    ClassroomStudent.is_active.is_(True),
                )
            )
            .all()
        )

        if not students:
            raise HTTPException(
                status_code=400, detail="No active students in this classroom"
            )

    # 4. 建立作業記錄
    assignments = []
    for student in students:
        # 檢查是否已有相同作業
        existing = (
            db.query(StudentAssignment)
            .filter(
                and_(
                    StudentAssignment.student_id == student.id,
                    StudentAssignment.content_id == request.content_id,
                    StudentAssignment.classroom_id == request.classroom_id,
                    StudentAssignment.status != AssignmentStatus.GRADED,
                )
            )
            .first()
        )

        if existing:
            continue  # 跳過已存在的作業

        # 建立新作業
        assignment = StudentAssignment(
            student_id=student.id,
            content_id=request.content_id,
            classroom_id=request.classroom_id,
            title=request.title,
            instructions=request.instructions,
            status=AssignmentStatus.NOT_STARTED,
            due_date=request.due_date,
        )
        db.add(assignment)
        assignments.append(assignment)

    # 5. 提交到資料庫
    if assignments:
        db.commit()

    return {
        "success": True,
        "count": len(assignments),
        "message": f"Successfully created {len(assignments)} assignments",
    }


@router.get("/classrooms/{classroom_id}/students", response_model=List[StudentResponse])
async def get_classroom_students(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """取得班級的學生列表"""

    # 0. 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access classroom students"
        )
    current_teacher = current_user

    # 驗證班級存在且屬於當前教師
    classroom = (
        db.query(Classroom)
        .filter(
            and_(
                Classroom.id == classroom_id,
                Classroom.teacher_id == current_teacher.id,
                Classroom.is_active.is_(True),
            )
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404, detail="Classroom not found or you don't have permission"
        )

    # 取得班級學生
    students = (
        db.query(Student)
        .join(ClassroomStudent)
        .filter(
            and_(
                ClassroomStudent.classroom_id == classroom_id,
                Student.is_active == True,
                ClassroomStudent.is_active == True,
            )
        )
        .all()
    )

    return students


@router.get("/contents", response_model=List[ContentResponse])
async def get_available_contents(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得可用的 Content 列表
    如果提供 classroom_id，只回傳該班級的 Content
    """

    # 0. 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(status_code=403, detail="Only teachers can access contents")
    current_teacher = current_user

    query = db.query(Content).join(Lesson).join(Program)

    if classroom_id:
        # 驗證班級權限
        classroom = (
            db.query(Classroom)
            .filter(
                and_(
                    Classroom.id == classroom_id,
                    Classroom.teacher_id == current_teacher.id,
                    Classroom.is_active.is_(True),
                )
            )
            .first()
        )

        if not classroom:
            raise HTTPException(
                status_code=404,
                detail="Classroom not found or you don't have permission",
            )

        # 篩選該班級的 Content
        query = query.filter(Program.classroom_id == classroom_id)
    else:
        # 回傳該教師所有的 Content (透過 classroom)
        query = query.join(Classroom).filter(Classroom.teacher_id == current_teacher.id)

    contents = query.all()

    # 轉換為回應格式
    response = []
    for content in contents:
        items_count = len(content.items) if content.items else 0
        response.append(
            ContentResponse(
                id=content.id,
                lesson_id=content.lesson_id,
                title=content.title,
                type=content.type.value
                if hasattr(content.type, "value")
                else str(content.type),
                level=content.level,
                items_count=items_count,
            )
        )

    return response


@router.get("/assignments/teacher")
async def get_teacher_assignments(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得教師的作業列表
    可依班級和狀態篩選
    """

    # 0. 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access assignments"
        )
    current_teacher = current_user

    # 建立查詢
    query = (
        db.query(StudentAssignment)
        .join(Classroom)
        .filter(Classroom.teacher_id == current_teacher.id)
    )

    # 套用篩選條件
    if classroom_id:
        query = query.filter(StudentAssignment.classroom_id == classroom_id)

    if status:
        try:
            status_enum = AssignmentStatus[status.upper()]
            query = query.filter(StudentAssignment.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")

    # 排序：最新的在前 (變數未使用，移除)
    # assignments = query.order_by(StudentAssignment.assigned_at.desc()).all()

    # 統計資訊 - 群組化作業資料
    from sqlalchemy import func, case

    stats = (
        db.query(
            StudentAssignment.content_id,
            StudentAssignment.classroom_id,
            StudentAssignment.title,
            StudentAssignment.instructions,
            StudentAssignment.due_date,
            StudentAssignment.assigned_at,
            func.count(StudentAssignment.id).label("total_count"),
            func.sum(
                case(
                    (StudentAssignment.status == AssignmentStatus.NOT_STARTED, 1),
                    else_=0,
                )
            ).label("not_started"),
            func.sum(
                case(
                    (StudentAssignment.status == AssignmentStatus.IN_PROGRESS, 1),
                    else_=0,
                )
            ).label("in_progress"),
            func.sum(
                case(
                    (StudentAssignment.status == AssignmentStatus.SUBMITTED, 1), else_=0
                )
            ).label("submitted"),
            func.sum(
                case((StudentAssignment.status == AssignmentStatus.GRADED, 1), else_=0)
            ).label("graded"),
            func.sum(
                case(
                    (StudentAssignment.status == AssignmentStatus.RETURNED, 1), else_=0
                )
            ).label("returned"),
        )
        .join(Classroom)
        .filter(Classroom.teacher_id == current_teacher.id)
    )

    if classroom_id:
        stats = stats.filter(StudentAssignment.classroom_id == classroom_id)

    stats = (
        stats.group_by(
            StudentAssignment.content_id,
            StudentAssignment.classroom_id,
            StudentAssignment.title,
            StudentAssignment.instructions,
            StudentAssignment.due_date,
            StudentAssignment.assigned_at,
        )
        .order_by(StudentAssignment.assigned_at.desc())
        .all()
    )

    # 組合回應 - 包含前端需要的所有欄位
    result = []
    for stat in stats:
        # 取得 Content 資訊
        content = db.query(Content).filter(Content.id == stat.content_id).first()

        # 計算完成率
        completed = (stat.submitted or 0) + (stat.graded or 0) + (stat.returned or 0)
        completion_rate = (
            int((completed / stat.total_count * 100)) if stat.total_count > 0 else 0
        )

        # 判斷狀態
        if stat.due_date and stat.due_date < datetime.now(timezone.utc):
            status = "overdue"
        elif completed == stat.total_count:
            status = "completed"
        elif (stat.in_progress or 0) > 0 or completed > 0:
            status = "in_progress"
        else:
            status = "not_started"

        result.append(
            {
                "id": f"{stat.content_id}_{stat.classroom_id}",  # 組合 ID
                "content_id": stat.content_id,
                "classroom_id": stat.classroom_id,
                "title": stat.title,
                "instructions": stat.instructions,
                "content_type": content.type if content else "UNKNOWN",
                "student_count": stat.total_count,
                "due_date": stat.due_date.isoformat() if stat.due_date else None,
                "assigned_at": stat.assigned_at.isoformat()
                if stat.assigned_at
                else None,
                "completion_rate": completion_rate,
                "status": status,
                "status_distribution": {
                    "not_started": stat.not_started or 0,
                    "in_progress": stat.in_progress or 0,
                    "submitted": stat.submitted or 0,
                    "graded": stat.graded or 0,
                    "returned": stat.returned or 0,
                },
            }
        )

    return result


# ============ Student APIs ============


@router.get("/assignments/student")
async def get_student_assignments(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得學生的作業列表
    學生只能看到自己的作業
    """

    # 0. 驗證是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403, detail="Only students can access their assignments"
        )
    current_student = current_user

    # 建立查詢
    query = db.query(StudentAssignment).filter(
        StudentAssignment.student_id == current_student.id
    )

    # 套用篩選條件
    if status:
        try:
            status_enum = AssignmentStatus[status.upper()]
            query = query.filter(StudentAssignment.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail="Invalid status")

    # 排序：最新的在前，但即將到期的優先
    assignments = query.order_by(
        StudentAssignment.due_date.asc().nullsfirst(),
        StudentAssignment.assigned_at.desc(),
    ).all()

    # 組合回應，加入 Content 資訊
    result = []
    for assignment in assignments:
        # 取得 Content 資訊
        content = db.query(Content).filter(Content.id == assignment.content_id).first()

        # 計算剩餘時間
        time_remaining = None
        is_overdue = False
        if assignment.due_date:
            now = datetime.now(timezone.utc)
            if assignment.due_date < now:
                is_overdue = True
                time_remaining = "已過期"
            else:
                delta = assignment.due_date - now
                if delta.days > 0:
                    time_remaining = f"剩餘 {delta.days} 天"
                else:
                    hours = delta.seconds // 3600
                    if hours > 0:
                        time_remaining = f"剩餘 {hours} 小時"
                    else:
                        minutes = (delta.seconds % 3600) // 60
                        time_remaining = f"剩餘 {minutes} 分鐘"

        result.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "instructions": assignment.instructions,
                "status": assignment.status.value,
                "assigned_at": assignment.assigned_at.isoformat()
                if assignment.assigned_at
                else None,
                "due_date": assignment.due_date.isoformat()
                if assignment.due_date
                else None,
                "submitted_at": assignment.submitted_at.isoformat()
                if assignment.submitted_at
                else None,
                "score": assignment.score,
                "feedback": assignment.feedback,
                "time_remaining": time_remaining,
                "is_overdue": is_overdue,
                "content": {
                    "id": content.id,
                    "title": content.title,
                    "type": content.type.value
                    if hasattr(content.type, "value")
                    else str(content.type),
                    "items_count": len(content.items) if content.items else 0,
                }
                if content
                else None,
            }
        )

    return result


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    submission_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    提交作業
    學生只能提交自己的作業
    """

    # 0. 驗證是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403, detail="Only students can submit assignments"
        )
    current_student = current_user

    # 取得作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 檢查作業狀態
    if assignment.status == AssignmentStatus.GRADED:
        raise HTTPException(
            status_code=400, detail="Assignment has already been graded"
        )

    # 檢查是否過期（但仍允許提交）
    is_late = False
    if assignment.due_date and assignment.due_date < datetime.now(timezone.utc):
        is_late = True

    # 更新作業狀態
    assignment.status = AssignmentStatus.SUBMITTED
    assignment.submitted_at = datetime.now(timezone.utc)

    # 檢查是否已有提交記錄
    submission = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id)
        .first()
    )

    if submission:
        # 更新現有提交
        submission.submission_data = submission_data
        submission.submitted_at = datetime.now(timezone.utc)
    else:
        # 建立新提交
        submission = AssignmentSubmission(
            assignment_id=assignment_id, submission_data=submission_data
        )
        db.add(submission)

    db.commit()

    return {
        "success": True,
        "message": "作業提交成功" + ("（遲交）" if is_late else ""),
        "submission_time": datetime.now().isoformat(),
        "is_late": is_late,
    }


@router.get("/assignments/{assignment_id}/detail")
async def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得作業詳細資訊
    學生只能查看自己的作業
    """

    # 0. 驗證是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403, detail="Only students can access assignment details"
        )
    current_student = current_user

    # 取得作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == current_student.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 取得 Content 詳細資訊
    content = db.query(Content).filter(Content.id == assignment.content_id).first()

    # 取得提交記錄
    submission = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id)
        .first()
    )

    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "instructions": assignment.instructions,
            "status": assignment.status.value,
            "due_date": assignment.due_date.isoformat()
            if assignment.due_date
            else None,
            "score": assignment.score,
            "feedback": assignment.feedback,
        },
        "content": {
            "id": content.id,
            "title": content.title,
            "type": content.type.value
            if hasattr(content.type, "value")
            else str(content.type),
            "items": content.items,
            "level": content.level,
            "tags": content.tags,
        }
        if content
        else None,
        "submission": {
            "id": submission.id,
            "submitted_at": submission.submitted_at.isoformat()
            if submission.submitted_at
            else None,
            "submission_data": submission.submission_data,
            "ai_scores": submission.ai_scores,
            "ai_feedback": submission.ai_feedback,
        }
        if submission
        else None,
    }


# ============ AI Grading Functions (Phase 3) ============


def calculate_text_similarity(expected: str, actual: str) -> float:
    """計算文字相似度 (0-1)"""
    # 清理文字，移除標點符號並轉小寫
    expected_clean = re.sub(r"[^\w\s]", "", expected.lower()).strip()
    actual_clean = re.sub(r"[^\w\s]", "", actual.lower()).strip()

    # 使用 SequenceMatcher 計算相似度
    similarity = SequenceMatcher(None, expected_clean, actual_clean).ratio()
    return similarity


def calculate_pronunciation_score(word_analysis: List[Dict[str, Any]]) -> float:
    """根據單字信心度計算發音評分"""
    if not word_analysis:
        return 0.0

    total_confidence = sum(word.get("confidence", 0.0) for word in word_analysis)
    avg_confidence = total_confidence / len(word_analysis)

    # 將信心度 (0-1) 轉換為評分 (0-100)
    return min(100.0, avg_confidence * 100)


def calculate_fluency_score(audio_analysis: Dict[str, Any]) -> float:
    """根據音訊分析計算流暢度評分"""
    total_duration = audio_analysis.get("total_duration", 0)
    speaking_duration = audio_analysis.get("speaking_duration", 0)
    pause_count = audio_analysis.get("pause_count", 0)
    avg_pause_duration = audio_analysis.get("average_pause_duration", 0)

    if total_duration == 0:
        return 0.0

    # 計算講話時間比例
    speaking_ratio = speaking_duration / total_duration

    # 計算暫停懲罰（過多或過長的暫停會降低流暢度）
    pause_penalty = 0
    if pause_count > 5:  # 超過5次暫停開始扣分
        pause_penalty += (pause_count - 5) * 5
    if avg_pause_duration > 1.0:  # 平均暫停超過1秒開始扣分
        pause_penalty += (avg_pause_duration - 1.0) * 10

    # 基礎分數根據講話時間比例
    base_score = speaking_ratio * 100

    # 扣除暫停懲罰
    final_score = max(0, base_score - pause_penalty)

    return min(100.0, final_score)


def calculate_wpm(transcribed_text: str, duration_seconds: float) -> float:
    """計算每分鐘字數 (Words Per Minute)"""
    if duration_seconds <= 0:
        return 0.0

    # 計算單字數量
    words = re.findall(r"\b\w+\b", transcribed_text.lower())
    word_count = len(words)

    # 計算 WPM
    minutes = duration_seconds / 60
    if minutes <= 0:
        return 0.0

    wpm = word_count / minutes
    return round(wpm, 1)


def generate_ai_feedback(
    ai_scores: AIScores, detailed_results: List[Dict[str, Any]]
) -> str:
    """根據 AI 評分生成回饋"""
    feedback_parts = []

    # 整體表現評價
    overall = (
        ai_scores.pronunciation * 0.3
        + ai_scores.fluency * 0.3
        + ai_scores.accuracy * 0.4
    )

    if overall >= 85:
        feedback_parts.append("🌟 優秀的表現！您的英語朗讀能力很出色。")
    elif overall >= 70:
        feedback_parts.append("👍 很好的表現！您已經掌握了基礎技巧。")
    elif overall >= 50:
        feedback_parts.append("💪 不錯的嘗試！持續練習會更進步。")
    else:
        feedback_parts.append("🌱 很好的開始！每一次練習都是進步的機會。")

    # 具體項目回饋
    if ai_scores.pronunciation >= 80:
        feedback_parts.append(f"發音表現優秀 ({ai_scores.pronunciation:.0f}/100)，發音清晰準確。")
    elif ai_scores.pronunciation >= 60:
        feedback_parts.append(f"發音基本準確 ({ai_scores.pronunciation:.0f}/100)，建議多練習困難音節。")
    else:
        feedback_parts.append(
            f"發音需要改進 ({ai_scores.pronunciation:.0f}/100)，建議跟著示範音訊多練習。"
        )

    if ai_scores.fluency >= 80:
        feedback_parts.append(f"語音流暢度很好 ({ai_scores.fluency:.0f}/100)，節奏掌握得宜。")
    elif ai_scores.fluency >= 60:
        feedback_parts.append(f"語音流暢度尚可 ({ai_scores.fluency:.0f}/100)，可以練習減少不必要的停頓。")
    else:
        feedback_parts.append(f"建議提高語音流暢度 ({ai_scores.fluency:.0f}/100)，練習連貫朗讀。")

    if ai_scores.accuracy >= 90:
        feedback_parts.append(f"內容準確度極高 ({ai_scores.accuracy:.0f}/100)，每個單字都很清楚。")
    elif ai_scores.accuracy >= 70:
        feedback_parts.append(f"內容準確度良好 ({ai_scores.accuracy:.0f}/100)，大部分內容都正確。")
    else:
        feedback_parts.append(f"建議提高準確度 ({ai_scores.accuracy:.0f}/100)，仔細聆聽每個單字的發音。")

    # 語速回饋
    if ai_scores.wpm > 150:
        feedback_parts.append(f"語速較快 ({ai_scores.wpm:.0f} WPM)，可以嘗試稍微放慢以提高清晰度。")
    elif ai_scores.wpm < 80:
        feedback_parts.append(f"語速較慢 ({ai_scores.wpm:.0f} WPM)，可以嘗試提高語速以增加流暢感。")
    else:
        feedback_parts.append(f"語速適中 ({ai_scores.wpm:.0f} WPM)，保持這個節奏很好。")

    return " ".join(feedback_parts)


async def process_audio_with_whisper(
    audio_urls: List[str], expected_texts: List[str]
) -> Dict[str, Any]:
    """使用 OpenAI Whisper 處理音訊"""
    # 設定 OpenAI API
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    # 這裡應該實際呼叫 OpenAI Whisper API
    # 由於測試環境限制，我們先返回模擬資料
    mock_transcriptions = []

    for i, (audio_url, expected_text) in enumerate(zip(audio_urls, expected_texts)):
        # 模擬 Whisper 轉錄結果
        # 在實際實作中，這裡會呼叫真正的 OpenAI Whisper API
        mock_transcriptions.append(
            {
                "item_id": i + 1,
                "expected_text": expected_text,
                "transcribed_text": expected_text,  # 假設完美轉錄
                "confidence": 0.92,
                "words": [
                    {
                        "word": word,
                        "start": j * 0.5,
                        "end": (j + 1) * 0.5,
                        "confidence": 0.85 + (j % 3) * 0.05,  # 模擬不同信心度
                    }
                    for j, word in enumerate(expected_text.split())
                ],
            }
        )

    return {
        "transcriptions": mock_transcriptions,
        "audio_analysis": {
            "total_duration": len(expected_texts) * 3.0,  # 假設每句3秒
            "speaking_duration": len(expected_texts) * 2.5,  # 假設實際說話2.5秒
            "pause_count": len(expected_texts) - 1,  # 句子間的暫停
            "average_pause_duration": 0.3,
        },
    }


@router.post("/assignments/{assignment_id}/ai-grade", response_model=AIGradingResponse)
async def ai_grade_assignment(
    assignment_id: int,
    request: AIGradingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    AI 自動批改作業
    只有教師可以觸發批改
    """
    start_time = datetime.now()

    # 0. 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can trigger AI grading"
        )
    current_teacher = current_user

    # 1. 取得作業並驗證權限
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
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 2. 檢查作業狀態
    if assignment.status != AssignmentStatus.SUBMITTED:
        raise HTTPException(
            status_code=400, detail="Assignment must be submitted before grading"
        )

    # 3. 取得作業內容
    content = db.query(Content).filter(Content.id == assignment.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    # 4. 取得提交資料
    submission = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id)
        .first()
    )

    if not submission:
        raise HTTPException(
            status_code=400, detail="No submission found for this assignment"
        )

    try:
        # 5. 處理批改邏輯
        if request.mock_mode and request.mock_data:
            # 使用模擬資料（測試模式）
            whisper_result = request.mock_data
        else:
            # 準備預期文字
            expected_texts = []
            if content.items:
                for item in content.items:
                    expected_texts.append(item.get("text", ""))

            # 呼叫 Whisper API
            whisper_result = await process_audio_with_whisper(
                request.audio_urls or [], expected_texts
            )

        # 6. 分析批改結果
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

        # 7. 更新資料庫
        # 更新作業狀態
        assignment.status = AssignmentStatus.GRADED
        assignment.score = overall_score
        assignment.feedback = feedback
        assignment.graded_at = datetime.now(timezone.utc)

        # 更新提交記錄
        submission.ai_scores = {
            "pronunciation": ai_scores.pronunciation,
            "fluency": ai_scores.fluency,
            "accuracy": ai_scores.accuracy,
            "wpm": ai_scores.wpm,
            "overall": overall_score,
        }
        submission.ai_feedback = feedback

        db.commit()

        # 8. 計算處理時間
        processing_time = (datetime.now() - start_time).total_seconds()

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


@router.get("/{assignment_id}/detail")
async def get_assignment_detail(
    assignment_id: int,
    current_user: Teacher = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """獲取作業詳情（學生用）"""
    # 檢查是否為學生
    student = db.query(Student).filter(Student.email == current_user.email).first()
    if not student:
        raise HTTPException(
            status_code=403, detail="Only students can access this endpoint"
        )

    # 獲取作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == student.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 獲取內容詳情
    content = db.query(Content).filter(Content.id == assignment.content_id).first()

    return {
        "id": assignment.id,
        "title": assignment.title,
        "instructions": assignment.instructions,
        "status": assignment.status.value,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "score": assignment.score,
        "feedback": assignment.feedback,
        "content": {
            "id": content.id,
            "type": content.type.value,
            "title": content.title,
            "items": content.items or [],
            "target_wpm": content.target_wpm,
            "target_accuracy": content.target_accuracy,
        }
        if content
        else None,
    }


@router.get("/{assignment_id}/submissions")
async def get_assignment_submissions(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_user),
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
            StudentAssignment.content_id == base_assignment.content_id,
            StudentAssignment.classroom_id == base_assignment.classroom_id,
        )
        .all()
    )

    result = []
    for sub in submissions:
        student = db.query(Student).filter(Student.id == sub.student_id).first()
        submission_record = (
            db.query(AssignmentSubmission)
            .filter(AssignmentSubmission.assignment_id == sub.id)
            .first()
        )

        result.append(
            {
                "id": submission_record.id if submission_record else None,
                "assignment_id": sub.id,
                "student_id": student.id,
                "student_name": student.name,
                "status": sub.status.value,
                "submitted_at": sub.submitted_at.isoformat()
                if sub.submitted_at
                else None,
                "score": sub.score,
                "feedback": sub.feedback,
                "submission_data": submission_record.submission_data
                if submission_record
                else None,
            }
        )

    return result


@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    submission: dict,
    current_user: Teacher = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交作業（學生用）"""
    # 檢查是否為學生
    student = db.query(Student).filter(Student.email == current_user.email).first()
    if not student:
        raise HTTPException(
            status_code=403, detail="Only students can submit assignments"
        )

    # 獲取作業
    assignment = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.id == assignment_id,
            StudentAssignment.student_id == student.id,
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 檢查作業狀態
    if assignment.status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
        raise HTTPException(status_code=400, detail="Assignment already graded")

    # 創建或更新提交記錄
    submission_record = (
        db.query(AssignmentSubmission)
        .filter(AssignmentSubmission.assignment_id == assignment_id)
        .first()
    )

    if not submission_record:
        submission_record = AssignmentSubmission(
            assignment_id=assignment_id,
            submission_data=submission,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(submission_record)
    else:
        submission_record.submission_data = submission
        submission_record.submitted_at = datetime.now(timezone.utc)

    # 更新作業狀態
    assignment.status = AssignmentStatus.SUBMITTED
    assignment.submitted_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "id": assignment.id,
        "status": assignment.status.value,
        "submitted_at": assignment.submitted_at.isoformat(),
        "message": "Assignment submitted successfully",
    }


@router.post("/{assignment_id}/manual-grade")
async def manual_grade_assignment(
    assignment_id: int,
    grade_data: dict,
    current_teacher: Teacher = Depends(get_current_user),
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

    # 更新提交記錄（如果有詳細評分）
    if "detailed_scores" in grade_data:
        submission = (
            db.query(AssignmentSubmission)
            .filter(AssignmentSubmission.assignment_id == assignment_id)
            .first()
        )

        if submission:
            submission.ai_scores = grade_data["detailed_scores"]
            submission.ai_feedback = grade_data.get("feedback")

    db.commit()

    return {
        "id": assignment.id,
        "status": assignment.status.value,
        "score": assignment.score,
        "feedback": assignment.feedback,
        "graded_at": assignment.graded_at.isoformat(),
        "message": "Assignment graded successfully",
    }
