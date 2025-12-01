"""
作業系統 API 路由
Phase 1: 基礎指派功能
"""

import logging
from typing import List, Optional, Dict, Any  # noqa: F401
from datetime import datetime, timezone  # noqa: F401
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from database import get_db
from performance_monitoring import trace_function, start_span, PerformanceSnapshot
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Content,
    ContentItem,
    Lesson,
    Program,
    Assignment,
    AssignmentContent,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
    AssignmentStatus,
)
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teachers", tags=["assignments"])


# ============ Helper Functions (Mock implementations) ============


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


# ============ Pydantic Models ============


class CreateAssignmentRequest(BaseModel):
    """建立作業請求（新架構）"""

    title: str
    description: Optional[str] = None
    classroom_id: int
    content_ids: List[int]  # 支援多個內容
    student_ids: List[int] = []  # 空陣列 = 全班
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None  # 開始日期


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
    student_number: Optional[str] = None  # 改為 student_number 對應資料庫欄位

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
    建立作業（新架構）
    - 建立 Assignment 主表記錄
    - 關聯多個 Content
    - 指派給指定學生或全班
    """
    # 驗證是教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can create assignments"
        )

    # 驗證教師訂閱狀態
    if not current_user.can_assign_homework:
        raise HTTPException(
            status_code=403,
            detail="Your subscription has expired. Please recharge to create assignments.",
        )

    # 驗證班級存在且屬於當前教師
    classroom = (
        db.query(Classroom)
        .filter(
            and_(
                Classroom.id == request.classroom_id,
                Classroom.teacher_id == current_user.id,
                Classroom.is_active.is_(True),
            )
        )
        .first()
    )

    if not classroom:
        raise HTTPException(
            status_code=404, detail="Classroom not found or you don't have permission"
        )

    # 驗證所有 Content 存在（只查詢模板內容，不包含作業副本）
    # 🔥 使用 eager loading 避免 N+1 查詢問題
    contents = (
        db.query(Content)
        .filter(
            Content.id.in_(request.content_ids),
            Content.is_assignment_copy.is_(False),  # 只允許從模板派作業
        )
        .options(selectinload(Content.content_items))
        .all()
    )
    if len(contents) != len(request.content_ids):
        raise HTTPException(
            status_code=404,
            detail="Some contents not found or cannot assign from assignment copies",
        )

    try:
        # 建立 Assignment 主表記錄
        assignment = Assignment(
            title=request.title,
            description=request.description,
            classroom_id=request.classroom_id,
            teacher_id=current_user.id,
            due_date=request.due_date,
            is_active=True,
        )
        db.add(assignment)
        db.flush()  # 取得 assignment.id

        # 🔥 複製 Content 和 ContentItem 作為作業副本
        content_copy_map = {}  # 原始 content_id -> 副本 content_id
        content_items_copy_map = {}  # 原始 content_item_id -> 副本 content_item_id

        for original_content in contents:
            # 複製 Content
            content_copy = Content(
                lesson_id=original_content.lesson_id,  # 保留 lesson_id（雖然副本不需要，但保持結構一致）
                type=original_content.type,
                title=original_content.title,
                order_index=original_content.order_index,
                is_active=True,
                target_wpm=original_content.target_wpm,
                target_accuracy=original_content.target_accuracy,
                time_limit_seconds=original_content.time_limit_seconds,
                level=original_content.level,
                tags=original_content.tags.copy() if original_content.tags else [],
                is_public=False,  # 副本不公開
                # 作業副本欄位
                is_assignment_copy=True,
                source_content_id=original_content.id,
            )
            db.add(content_copy)
            db.flush()  # 取得 content_copy.id
            content_copy_map[original_content.id] = content_copy.id

            # 複製所有 ContentItem（使用 eager loaded 的 content_items，避免 N+1）
            original_items = sorted(
                original_content.content_items,
                key=lambda x: x.order_index
            )

            for original_item in original_items:
                item_copy = ContentItem(
                    content_id=content_copy.id,  # 指向副本 Content
                    order_index=original_item.order_index,
                    text=original_item.text,
                    translation=original_item.translation,
                    audio_url=original_item.audio_url,  # 複製音檔 URL
                    item_metadata=original_item.item_metadata.copy()
                    if original_item.item_metadata
                    else {},
                )
                db.add(item_copy)
                db.flush()  # 取得 item_copy.id
                content_items_copy_map[original_item.id] = item_copy.id

        # 建立 AssignmentContent 關聯（指向副本）
        for idx, original_content_id in enumerate(request.content_ids, 1):
            copy_content_id = content_copy_map[original_content_id]
            assignment_content = AssignmentContent(
                assignment_id=assignment.id, content_id=copy_content_id, order_index=idx
            )
            db.add(assignment_content)

        # 取得要指派的學生列表
        if request.student_ids and len(request.student_ids) > 0:
            # 指派給指定學生
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

        # 🔥 Preload all ContentItems for copied contents (avoid N+1)
        copy_content_ids = list(content_copy_map.values())
        all_content_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id.in_(copy_content_ids))
            .order_by(ContentItem.content_id, ContentItem.order_index)
            .all()
        )
        # Build map: copy_content_id -> [items]
        content_items_map = {}
        for item in all_content_items:
            if item.content_id not in content_items_map:
                content_items_map[item.content_id] = []
            content_items_map[item.content_id].append(item)

        # 🔥 優化：批量收集所有要創建的物件，避免多次 flush
        all_student_assignments = []
        all_progress_records = []
        all_item_progress_records = []

        assigned_at_time = (
            request.start_date if request.start_date else datetime.now(timezone.utc)
        )

        for student in students:
            student_assignment = StudentAssignment(
                assignment_id=assignment.id,
                student_id=student.id,
                classroom_id=request.classroom_id,
                # 暫時保留舊欄位以兼容
                title=request.title,
                instructions=request.description,
                due_date=request.due_date,
                assigned_at=assigned_at_time,  # Use start_date from frontend
                status=AssignmentStatus.NOT_STARTED,
                is_active=True,
            )
            all_student_assignments.append(student_assignment)

            # 為每個內容建立進度記錄（使用副本 content_id）
            for idx, original_content_id in enumerate(request.content_ids, 1):
                copy_content_id = content_copy_map[original_content_id]
                progress = StudentContentProgress(
                    student_assignment_id=None,  # 稍後設置
                    content_id=copy_content_id,  # 使用副本 ID
                    status=AssignmentStatus.NOT_STARTED,
                    order_index=idx,
                    is_locked=False if idx == 1 else True,  # 只解鎖第一個
                )
                all_progress_records.append((progress, student_assignment))

                # 🔥 Get content items from preloaded map (no query)
                content_items = content_items_map.get(copy_content_id, [])

                for item in content_items:
                    item_progress = StudentItemProgress(
                        student_assignment_id=None,  # 稍後設置
                        content_item_id=item.id,  # 使用副本 ContentItem ID
                        status="NOT_STARTED",
                    )
                    all_item_progress_records.append((item_progress, student_assignment))

        # 🔥 批量添加 StudentAssignment（使用 add_all 以支持關聯）
        db.add_all(all_student_assignments)
        db.flush()  # 取得所有 student_assignment.id

        # 設置 progress 的 student_assignment_id
        for progress, student_assignment in all_progress_records:
            progress.student_assignment_id = student_assignment.id

        # 🔥 批量添加 StudentContentProgress
        db.add_all([p for p, _ in all_progress_records])
        db.flush()  # 取得所有 progress.id

        # 設置 item_progress 的 student_assignment_id
        for item_progress, student_assignment in all_item_progress_records:
            item_progress.student_assignment_id = student_assignment.id

        # 🔥 批量添加 StudentItemProgress
        db.add_all([p for p, _ in all_item_progress_records])

        # Commit all changes at once
        db.commit()
    except Exception as e:
        db.rollback()  # 回滾所有變更
        logger.error(f"Failed to create assignment: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create assignment: {str(e)}"
        )

    return {
        "success": True,
        "assignment_id": assignment.id,
        "student_count": len(students),
        "content_count": len(request.content_ids),
        "message": f"Successfully created assignment for {len(students)} students",
    }


@router.get("/assignments")
async def get_assignments(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得作業列表（新架構）
    - 教師看到自己建立的作業
    - 可依班級和狀態篩選
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access assignments"
        )

    # 建立查詢
    query = db.query(Assignment).filter(
        Assignment.teacher_id == current_user.id, Assignment.is_active.is_(True)
    )

    # 套用篩選
    if classroom_id:
        query = query.filter(Assignment.classroom_id == classroom_id)

    assignments = query.order_by(Assignment.created_at.desc()).all()

    # 🔥 Batch-load assignment content counts (avoid N+1)
    assignment_ids = [a.id for a in assignments]
    content_counts = (
        db.query(
            AssignmentContent.assignment_id,
            func.count(AssignmentContent.id).label("count"),
        )
        .filter(AssignmentContent.assignment_id.in_(assignment_ids))
        .group_by(AssignmentContent.assignment_id)
        .all()
    )
    content_count_map = {row.assignment_id: row.count for row in content_counts}

    # 🔥 Batch-load all student assignments (avoid N+1)
    all_student_assignments = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id.in_(assignment_ids),
            StudentAssignment.is_active.is_(True),
        )
        .all()
    )
    # Build map: assignment_id -> [student_assignments]
    student_assignments_map = {}
    for sa in all_student_assignments:
        if sa.assignment_id not in student_assignments_map:
            student_assignments_map[sa.assignment_id] = []
        student_assignments_map[sa.assignment_id].append(sa)

    # 組合回應
    result = []
    for assignment in assignments:
        # 🔥 Get from preloaded maps (no queries)
        content_count = content_count_map.get(assignment.id, 0)
        student_assignments = student_assignments_map.get(assignment.id, [])

        status_counts = {
            "not_started": 0,
            "in_progress": 0,
            "submitted": 0,
            "graded": 0,
            "returned": 0,
            "resubmitted": 0,
        }

        for sa in student_assignments:
            status_key = sa.status.value.lower()
            if status_key in status_counts:
                status_counts[status_key] += 1

        # 計算完成率
        total_students = len(student_assignments)
        completed = status_counts["graded"]
        completion_rate = (
            int((completed / total_students * 100)) if total_students > 0 else 0
        )

        result.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "classroom_id": assignment.classroom_id,
                "content_count": content_count,
                "student_count": total_students,
                "due_date": (
                    assignment.due_date.isoformat() if assignment.due_date else None
                ),
                "created_at": (
                    assignment.created_at.isoformat() if assignment.created_at else None
                ),
                "completion_rate": completion_rate,
                "status_distribution": status_counts,
            }
        )

    return result


@router.put("/assignments/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    編輯作業（新架構）
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can update assignments"
        )

    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 更新基本資訊
    assignment.title = request.title
    assignment.description = request.description
    assignment.due_date = request.due_date

    # 更新內容關聯（先刪除舊的，再建立新的）
    db.query(AssignmentContent).filter(
        AssignmentContent.assignment_id == assignment_id
    ).delete()

    for idx, content_id in enumerate(request.content_ids, 1):
        assignment_content = AssignmentContent(
            assignment_id=assignment_id, content_id=content_id, order_index=idx
        )
        db.add(assignment_content)

    # 更新所有相關的 StudentAssignment（暫時保留舊欄位）
    db.query(StudentAssignment).filter(
        StudentAssignment.assignment_id == assignment_id
    ).update(
        {
            "title": request.title,
            "instructions": request.description,
            "due_date": request.due_date,
        }
    )

    db.commit()

    return {
        "success": True,
        "assignment_id": assignment_id,
        "message": "Assignment updated successfully",
    }


@router.patch("/assignments/{assignment_id}")
async def patch_assignment(
    assignment_id: int,
    request: UpdateAssignmentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    部分更新作業（只更新提供的欄位）
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can update assignments"
        )

    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 只更新提供的欄位
    if request.title is not None:
        assignment.title = request.title

    if request.description is not None:
        assignment.description = request.description
    elif request.instructions is not None:  # Support 'instructions' as alias
        assignment.description = request.instructions

    if request.due_date is not None:
        assignment.due_date = request.due_date

    # 更新 StudentAssignment 記錄
    update_fields = {}
    if request.title is not None:
        update_fields["title"] = request.title
    if request.description is not None or request.instructions is not None:
        update_fields["instructions"] = request.description or request.instructions
    if request.due_date is not None:
        update_fields["due_date"] = request.due_date

    if update_fields:
        db.query(StudentAssignment).filter(
            StudentAssignment.assignment_id == assignment_id
        ).update(update_fields)

    # 如果要更新 student_ids
    if request.student_ids is not None:
        # 先找出要刪除的 StudentAssignment IDs
        assignments_to_delete = (
            db.query(StudentAssignment.id)
            .filter(
                StudentAssignment.assignment_id == assignment_id,
                StudentAssignment.status == AssignmentStatus.NOT_STARTED,
            )
            .all()
        )

        assignment_ids_to_delete = [a.id for a in assignments_to_delete]

        if assignment_ids_to_delete:
            # 先刪除相關的 StudentContentProgress 記錄
            db.query(StudentContentProgress).filter(
                StudentContentProgress.student_assignment_id.in_(
                    assignment_ids_to_delete
                )
            ).delete(synchronize_session=False)

            # 再刪除 StudentAssignment 記錄
            db.query(StudentAssignment).filter(
                StudentAssignment.id.in_(assignment_ids_to_delete)
            ).delete(synchronize_session=False)

        # 🔥 Preload existing student assignments (avoid N+1)
        existing_student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        existing_student_ids = {sa.student_id for sa in existing_student_assignments}

        # 🔥 Preload assignment contents (avoid N+1)
        assignment_contents = (
            db.query(AssignmentContent)
            .filter(AssignmentContent.assignment_id == assignment_id)
            .order_by(AssignmentContent.order_index)
            .all()
        )

        # 🔥 Preload all content items (avoid N+1)
        content_ids = [ac.content_id for ac in assignment_contents]
        all_content_items = (
            db.query(ContentItem)
            .filter(ContentItem.content_id.in_(content_ids))
            .order_by(ContentItem.content_id, ContentItem.order_index)
            .all()
        )
        content_items_map = {}
        for item in all_content_items:
            if item.content_id not in content_items_map:
                content_items_map[item.content_id] = []
            content_items_map[item.content_id].append(item)

        # 為新的學生列表創建 StudentAssignment
        for student_id in request.student_ids:
            # 🔥 Check from preloaded set (no query)
            if student_id in existing_student_ids:
                continue  # Already exists

            student_assignment = StudentAssignment(
                assignment_id=assignment_id,
                student_id=student_id,
                classroom_id=assignment.classroom_id,
                title=assignment.title,
                instructions=assignment.description,
                due_date=assignment.due_date,
                status=AssignmentStatus.NOT_STARTED,
                assigned_at=datetime.now(timezone.utc),
                is_active=True,
            )
            db.add(student_assignment)
            db.flush()  # 取得 student_assignment.id

            # 🔥 Use preloaded assignment_contents (no query)
            for ac in assignment_contents:
                progress = StudentContentProgress(
                    student_assignment_id=student_assignment.id,
                    content_id=ac.content_id,
                    status=AssignmentStatus.NOT_STARTED,
                    order_index=ac.order_index,
                    is_locked=False if ac.order_index == 1 else True,  # 只解鎖第一個
                )
                db.add(progress)
                db.flush()  # 取得 progress.id

                # 🔥 Use preloaded content_items (no query)
                content_items = content_items_map.get(ac.content_id, [])

                for item in content_items:
                    item_progress = StudentItemProgress(
                        student_assignment_id=student_assignment.id,
                        content_item_id=item.id,
                        status="NOT_STARTED",
                    )
                    db.add(item_progress)

    db.commit()

    return {
        "success": True,
        "assignment_id": assignment_id,
        "message": "Assignment updated successfully",
    }


@router.put("/assignments/{assignment_id}/contents/reorder")
async def reorder_assignment_contents(
    assignment_id: int,
    order_data: List[Dict[str, int]],  # [{"content_id": 1, "order_index": 1}, ...]
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    重新排序作業內容（AssignmentContent）
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can reorder assignment contents"
        )

    # 驗證作業屬於當前教師
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 批次查詢 AssignmentContent，避免 N+1 問題
    content_ids = [item["content_id"] for item in order_data]
    assignment_contents = (
        db.query(AssignmentContent)
        .filter(
            AssignmentContent.assignment_id == assignment_id,
            AssignmentContent.content_id.in_(content_ids),
        )
        .all()
    )
    assignment_contents_dict = {
        ac.content_id: ac for ac in assignment_contents
    }

    # 更新順序
    for item in order_data:
        ac = assignment_contents_dict.get(item["content_id"])
        if ac:
            ac.order_index = item["order_index"]

    db.commit()
    return {"success": True, "message": "Assignment contents reordered successfully"}


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    軟刪除作業（新架構）
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can delete assignments"
        )

    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 軟刪除 Assignment
    assignment.is_active = False

    # 軟刪除所有相關的 StudentAssignment
    db.query(StudentAssignment).filter(
        StudentAssignment.assignment_id == assignment_id
    ).update({"is_active": False})

    # 🔥 硬刪除作業副本（Content 和 ContentItem）
    # 透過 AssignmentContent 找出該作業關聯的所有 Content
    assignment_content_records = (
        db.query(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment_id)
        .all()
    )
    
    # 取得所有 content_id
    content_ids_in_assignment = [ac.content_id for ac in assignment_content_records]
    
    # 找出這些 content 中屬於作業副本的
    copy_contents = (
        db.query(Content)
        .filter(
            Content.id.in_(content_ids_in_assignment),
            Content.is_assignment_copy.is_(True),
        )
        .all()
    )

    copy_content_ids = [cc.id for cc in copy_contents]

    if copy_content_ids:
        # 找出所有副本的 ContentItem IDs
        copy_content_items = (
            db.query(ContentItem.id)
            .filter(ContentItem.content_id.in_(copy_content_ids))
            .all()
        )
        copy_content_item_ids = [item.id for item in copy_content_items]

        if copy_content_item_ids:
            # 先刪除依賴 ContentItem 的 StudentItemProgress
            db.query(StudentItemProgress).filter(
                StudentItemProgress.content_item_id.in_(copy_content_item_ids)
            ).delete(synchronize_session=False)

        # 硬刪除所有副本的 ContentItem
        if copy_content_item_ids:
            db.query(ContentItem).filter(
                ContentItem.id.in_(copy_content_item_ids)
            ).delete(synchronize_session=False)

        # 先刪除依賴 Content 的 StudentContentProgress
        db.query(StudentContentProgress).filter(
            StudentContentProgress.content_id.in_(copy_content_ids)
        ).delete(synchronize_session=False)

        # 先刪除 AssignmentContent 關聯（指向副本的）
        db.query(AssignmentContent).filter(
            AssignmentContent.content_id.in_(copy_content_ids)
        ).delete(synchronize_session=False)

        # 硬刪除所有副本 Content
        db.query(Content).filter(Content.id.in_(copy_content_ids)).delete(
            synchronize_session=False
        )

    db.commit()

    return {"success": True, "message": "Assignment deleted successfully"}


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
        # 簡化版 - 不查詢 Content
        content = None

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
                "assigned_at": (
                    assignment.assigned_at.isoformat()
                    if assignment.assigned_at
                    else None
                ),
                "due_date": (
                    assignment.due_date.isoformat() if assignment.due_date else None
                ),
                "submitted_at": (
                    assignment.submitted_at.isoformat()
                    if assignment.submitted_at
                    else None
                ),
                "score": assignment.score,
                "feedback": assignment.feedback,
                "time_remaining": time_remaining,
                "is_overdue": is_overdue,
                "content": (
                    {
                        "id": content.id,
                        "title": content.title,
                        "type": (
                            content.type.value
                            if hasattr(content.type, "value")
                            else str(content.type)
                        ),
                        "items_count": len(content.content_items)
                        if hasattr(content, "content_items")
                        else 0,
                    }
                    if content
                    else None
                ),
            }
        )

    return result


@router.get("/assignments/{assignment_id}")
async def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得作業詳細資訊（新架構）
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access assignment details"
        )

    # 取得作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 取得內容列表
    assignment_contents = (
        db.query(AssignmentContent)
        .filter(AssignmentContent.assignment_id == assignment_id)
        .order_by(AssignmentContent.order_index)
        .all()
    )

    # 優化：批次查詢所有 content，避免 N+1 問題
    content_ids = [ac.content_id for ac in assignment_contents]
    content_dict = {
        c.id: c for c in db.query(Content).filter(Content.id.in_(content_ids)).all()
    }

    contents = []
    for ac in assignment_contents:
        content = content_dict.get(ac.content_id)
        if content:
            contents.append(
                {
                    "id": content.id,
                    "title": content.title,
                    "type": (
                        content.type.value
                        if hasattr(content.type, "value")
                        else str(content.type)
                    ),
                    "order_index": ac.order_index,
                }
            )

    # 取得學生進度（使用 eager loading 避免 N+1）
    student_assignments = (
        db.query(StudentAssignment)
        .options(selectinload(StudentAssignment.content_progress))
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.is_active.is_(True),
        )
        .all()
    )

    # 收集已指派的學生 IDs
    student_ids = [sa.student_id for sa in student_assignments]

    # 🔥 修復：取得班級的全部學生，並標示指派狀態
    all_students = (
        db.query(Student)
        .join(ClassroomStudent, Student.id == ClassroomStudent.student_id)
        .filter(
            ClassroomStudent.classroom_id == assignment.classroom_id,
            ClassroomStudent.is_active.is_(True),
            Student.is_active.is_(True),
        )
        .order_by(Student.student_number)
        .all()
    )

    students_progress = []
    for student in all_students:
        # 檢查這個學生是否已被指派
        sa = None
        for student_assignment in student_assignments:
            if student_assignment.student_id == student.id:
                sa = student_assignment
                break

        is_assigned = sa is not None

        # 取得各內容進度（使用預先載入的資料，避免 N+1）
        content_progress = []
        if sa:  # 只有已指派的學生才有進度資料
            # 建立 content_id -> progress 的映射（從預先載入的資料）
            progress_map = {p.content_id: p for p in sa.content_progress}

            for content in contents:
                progress = progress_map.get(content["id"])

                if progress:
                    content_progress.append(
                        {
                            "content_id": content["id"],
                            "content_title": content["title"],
                            "status": (
                                progress.status.value
                                if progress.status
                                else "NOT_STARTED"
                            ),
                            "score": progress.score,
                            "checked": progress.checked,
                            "completed_at": (
                                progress.completed_at.isoformat()
                                if progress.completed_at
                                else None
                            ),
                        }
                    )

        students_progress.append(
            {
                "student_id": student.id,
                "student_name": student.name,
                "student_number": student.student_number,
                "is_assigned": is_assigned,  # 🔥 新增：指派狀態
                "overall_status": (
                    sa.status.value
                    if sa and sa.status
                    else ("NOT_STARTED" if is_assigned else "unassigned")
                ),
                "submitted_at": (
                    sa.submitted_at.isoformat() if sa and sa.submitted_at else None
                ),
                "content_progress": content_progress,
            }
        )

    return {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "classroom_id": assignment.classroom_id,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "created_at": (
            assignment.created_at.isoformat() if assignment.created_at else None
        ),
        "contents": contents,
        "student_ids": student_ids,  # 已指派的學生 IDs
        "students_progress": students_progress,
    }


@router.get("/assignments/{assignment_id}/progress")
async def get_assignment_progress(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取得作業的學生進度
    """
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access assignment progress"
        )

    # 確認作業存在且屬於當前教師
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_user.id,
            Assignment.is_active.is_(True),
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=404, detail="Assignment not found or you don't have permission"
        )

    # 🔥 修復：取得班級全部學生，並標示指派狀態
    # 取得學生作業進度
    student_assignments = (
        db.query(StudentAssignment)
        .filter(
            StudentAssignment.assignment_id == assignment_id,
            StudentAssignment.is_active.is_(True),
        )
        .all()
    )

    # 取得班級全部學生
    all_students = (
        db.query(Student)
        .join(ClassroomStudent, Student.id == ClassroomStudent.student_id)
        .filter(
            ClassroomStudent.classroom_id == assignment.classroom_id,
            ClassroomStudent.is_active.is_(True),
            Student.is_active.is_(True),
        )
        .order_by(Student.student_number)
        .all()
    )

    # 優化：使用字典查找避免嵌套循環 O(N*M) 問題
    student_assignments_dict = {sa.student_id: sa for sa in student_assignments}

    progress_list = []
    for student in all_students:
        # 使用字典快速查找，O(1) 時間複雜度
        sa = student_assignments_dict.get(student.id)
        is_assigned = sa is not None

        print(
            f"🔍 [DEBUG] Student {student.name} (ID: {student.id}) - is_assigned: {is_assigned}"
        )

        progress_list.append(
            {
                "student_id": student.id,
                "student_name": student.name,
                "student_number": student.student_number,  # 🔥 新增學號
                "is_assigned": is_assigned,  # 🔥 新增指派狀態
                "status": (
                    sa.status.value
                    if sa and sa.status
                    else ("NOT_STARTED" if is_assigned else "unassigned")
                ),
                "submission_date": (
                    sa.submitted_at.isoformat() if sa and sa.submitted_at else None
                ),
                "score": sa.score if sa else None,
                "attempts": 1 if sa and sa.submitted_at else 0,  # Simple attempt count
                "last_activity": (
                    sa.updated_at.isoformat()
                    if sa and sa.updated_at
                    else sa.created_at.isoformat()
                    if sa and sa.created_at
                    else None
                ),
                # 🔥 新增關鍵時間戳欄位用於狀態進度判斷
                "timestamps": {
                    "started_at": (
                        sa.started_at.isoformat() if sa and sa.started_at else None
                    ),
                    "submitted_at": (
                        sa.submitted_at.isoformat() if sa and sa.submitted_at else None
                    ),
                    "graded_at": (
                        sa.graded_at.isoformat() if sa and sa.graded_at else None
                    ),
                    "returned_at": (
                        sa.returned_at.isoformat() if sa and sa.returned_at else None
                    ),
                    "resubmitted_at": (
                        sa.resubmitted_at.isoformat()
                        if sa and sa.resubmitted_at
                        else None
                    ),
                    "created_at": (
                        sa.created_at.isoformat() if sa and sa.created_at else None
                    ),
                    "updated_at": (
                        sa.updated_at.isoformat() if sa and sa.updated_at else None
                    ),
                },
            }
        )

    return progress_list


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
                Student.is_active.is_(True),
                ClassroomStudent.is_active.is_(True),
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

    # 🔥 只返回模板內容，不包含作業副本
    query = query.filter(Content.is_assignment_copy.is_(False))

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
        items_count = (
            len(content.content_items) if hasattr(content, "content_items") else 0
        )
        response.append(
            ContentResponse(
                id=content.id,
                lesson_id=content.lesson_id,
                title=content.title,
                type=(
                    content.type.value
                    if hasattr(content.type, "value")
                    else str(content.type)
                ),
                level=content.level,
                items_count=items_count,
            )
        )

    return response


# 舊的 get_teacher_assignments 已移除，使用新的 get_assignments API


# ============ Student APIs ============


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

    # 更新 StudentContentProgress（新架構）
    # 這裡應該更新相關的 StudentContentProgress 記錄
    # 暫時簡化處理，後續完善

    db.commit()

    return {
        "success": True,
        "message": "作業提交成功" + ("（遲交）" if is_late else ""),
        "submission_time": datetime.now().isoformat(),
        "is_late": is_late,
    }


@router.post("/assignments/{assignment_id}/ai-grade", response_model=AIGradingResponse)
@trace_function("AI Grade Assignment")
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
    perf = PerformanceSnapshot(f"AI_Grade_Assignment_{assignment_id}")

    # 0. 驗證是教師身份
    with start_span("Verify Teacher Permission"):
        if not isinstance(current_user, Teacher):
            raise HTTPException(
                status_code=403, detail="Only teachers can trigger AI grading"
            )
        current_teacher = current_user
        perf.checkpoint("Permission Check")

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

            # 更新提交記錄（新架構應更新 StudentContentProgress）
            # 暫時註解，後續完善
            # submission.ai_scores = {
            #     "pronunciation": ai_scores.pronunciation,
            #     "fluency": ai_scores.fluency,
            #     "accuracy": ai_scores.accuracy,
            #     "wpm": ai_scores.wpm,
            #     "overall": overall_score,
            # }
            # submission.ai_feedback = feedback

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
            # StudentAssignment.content_id == base_assignment.content_id,  # 簡化版 - 不使用 content_id
            StudentAssignment.classroom_id
            == base_assignment.classroom_id,
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


@router.get("/assignments/{assignment_id}/students")
async def get_assignment_students(
    assignment_id: int,
    current_teacher: Teacher = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    獲取作業的所有學生列表（包含未指派的學生）
    """
    # 驗證教師身份
    if not isinstance(current_teacher, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access this endpoint"
        )

    # 查詢作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id, Assignment.teacher_id == current_teacher.id
        )
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # 獲取教師教室中的所有學生
    classroom_students = (
        db.query(Student)
        .join(ClassroomStudent, ClassroomStudent.student_id == Student.id)
        .filter(ClassroomStudent.classroom_id == assignment.classroom_id)
        .order_by(Student.name)
        .all()
    )

    # 獲取已指派此作業的學生狀態
    student_assignments_dict = {}
    student_assignments = (
        db.query(StudentAssignment)
        .filter(StudentAssignment.assignment_id == assignment_id)
        .all()
    )

    for sa in student_assignments:
        student_assignments_dict[sa.student_id] = (
            sa.status.value if sa.status else "NOT_STARTED"
        )

    students = []
    for student in classroom_students:
        # 如果學生有作業記錄，使用實際狀態；否則標示為未指派
        if student.id in student_assignments_dict:
            status = student_assignments_dict[student.id]
        else:
            status = "NOT_ASSIGNED"

        students.append(
            {
                "student_id": student.id,
                "student_name": student.name,
                "status": status,
            }
        )

    return {"students": students}


@router.get("/assignments/{assignment_id}/submissions/{student_id}")
async def get_student_submission(
    assignment_id: int,
    student_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """獲取單個學生的作業提交詳情（教師批改用）- 簡化版 v2"""

    # Verify user is a teacher (get_current_user returns a Teacher object from routers/auth.py)
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can access this endpoint"
        )

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
    # 使用 assignment (StudentAssignment) 的 assignment_id 來查詢
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

                # 不在這裡獲取 progress，改為在每個題目中單獨獲取

                # 使用 ContentItem 關聯
                items_data = list(content.content_items)
                for local_item_index, item in enumerate(items_data):
                    submission = {
                        "content_id": content.id,
                        "content_title": content.title,
                        "content_item_id": item.id,  # 加入 content_item_id
                        "question_text": item.text if hasattr(item, "text") else "",
                        "question_translation": item.translation
                        if hasattr(item, "translation")
                        else "",
                        "question_audio_url": item.audio_url
                        if hasattr(item, "audio_url")
                        else "",  # 題目參考音檔
                        "student_answer": "",  # 預設空字串
                        "student_audio_url": "",  # 學生錄音檔案
                        "transcript": "",  # 語音辨識結果
                        "duration": 0,
                        "item_index": item_index,  # 加入全局索引
                        "feedback": "",  # 預設空字串
                        "passed": None,  # 預設未評
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
                        # 學生錄音檔案 - 前端使用 audio_url 欄位
                        if item_progress.recording_url:
                            submission[
                                "audio_url"
                            ] = item_progress.recording_url  # 前端用 audio_url
                            submission[
                                "student_audio_url"
                            ] = item_progress.recording_url  # 保留相容性

                        # 作答狀態 - 使用 status 欄位
                        if item_progress.status == "SUBMITTED":
                            submission["status"] = "submitted"

                        # 創建 AI 評分物件 - 全部從 ai_feedback JSON 欄位讀取
                        if item_progress.ai_feedback:
                            # ai_feedback 是 JSON 字串，需要解析
                            import json

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
                        else:
                            # 統一只從 ai_feedback JSON 中取得分數
                            if item_progress.ai_feedback:
                                try:
                                    if isinstance(item_progress.ai_feedback, str):
                                        ai_feedback_data = json.loads(
                                            item_progress.ai_feedback
                                        )
                                    else:
                                        ai_feedback_data = item_progress.ai_feedback

                                    submission["ai_scores"] = {
                                        "accuracy_score": float(
                                            ai_feedback_data.get("accuracy_score", 0)
                                        ),
                                        "fluency_score": float(
                                            ai_feedback_data.get("fluency_score", 0)
                                        ),
                                        "pronunciation_score": float(
                                            ai_feedback_data.get(
                                                "pronunciation_score", 0
                                            )
                                        ),
                                        "completeness_score": float(
                                            ai_feedback_data.get(
                                                "completeness_score", 0
                                            )
                                        ),
                                        "overall_score": (
                                            (
                                                float(
                                                    ai_feedback_data.get(
                                                        "accuracy_score", 0
                                                    )
                                                )
                                                + float(
                                                    ai_feedback_data.get(
                                                        "fluency_score", 0
                                                    )
                                                )
                                                + float(
                                                    ai_feedback_data.get(
                                                        "pronunciation_score", 0
                                                    )
                                                )
                                            )
                                            / 3
                                        ),
                                        "word_details": ai_feedback_data.get(
                                            "word_details", []
                                        ),
                                    }
                                except (
                                    json.JSONDecodeError,
                                    TypeError,
                                    AttributeError,
                                ):
                                    # 如果 JSON 解析失敗，不顯示 AI 評分
                                    submission["ai_scores"] = None

                            # AI 評分已經設定完成，無需額外處理

                    submissions.append(submission)
                    group["submissions"].append(submission)
                    item_index += 1

                content_groups.append(group)

    # 如果沒有真實資料，使用模擬資料 (標記為 MOCK)
    if not submissions:
        print(
            f"WARNING: No real content found for assignment_id={actual_assignment_id}, using MOCK data"
        )
        # 通用 MOCK 資料 - 所有作業都使用相同的後備資料
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
            {
                "question_text": "[MOCK] What is your favorite color?",
                "question_translation": "[MOCK] 你最喜歡的顏色是什麼？",
                "student_answer": "My favorite color is blue.",
                "transcript": "My favorite color is blue",
                "duration": 4.2,
            },
            {
                "question_text": "[MOCK] Can you introduce yourself?",
                "question_translation": "[MOCK] 你能自我介紹嗎？",
                "student_answer": "My name is " + student.name + ". I am a student.",
                "transcript": "My name is " + student.name + " I am a student",
                "duration": 5.8,
            },
            {
                "question_text": "[MOCK] What do you like to do in your free time?",
                "question_translation": "[MOCK] 你空閒時喜歡做什麼？",
                "student_answer": "I like to read books and play games.",
                "transcript": "I like to read books and play games",
                "duration": 4.5,
            },
            {
                "question_text": "[MOCK] Tell me about your family.",
                "question_translation": "[MOCK] 告訴我關於你的家人。",
                "student_answer": "I have a father, mother, and one sister.",
                "transcript": "I have a father mother and one sister",
                "duration": 5.2,
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
        "content_groups": content_groups,  # 新增：按 content 分組的資料
        "current_score": assignment.score,
        "current_feedback": assignment.feedback,
    }


@router.post("/assignments/{assignment_id}/grade")
async def grade_student_assignment(
    assignment_id: int,
    grade_data: dict,
    current_teacher: Teacher = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """教師批改學生作業"""
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
    if grade_data.get("update_status", True):  # 預設為 True 保持向後相容
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
        # 因為每個 content 可能有多個 items，我們需要正確對應
        item_feedback_map = {}
        for item_result in grade_data["item_results"]:
            item_feedback_map[item_result.get("item_index")] = item_result

        # 優化：批次查詢所有 content，避免 N+1 問題
        content_ids = {progress.content_id for progress in progress_records}
        content_dict = {
            c.id: c
            for c in db.query(Content)
            .filter(Content.id.in_(content_ids))
            .options(selectinload(Content.content_items))  # 🔥 Eager load items
            .all()
        }

        # 🔥 Preload all StudentItemProgress (avoid N+1)
        all_item_progress = (
            db.query(StudentItemProgress)
            .filter(StudentItemProgress.student_assignment_id == assignment.id)
            .all()
        )
        # Build map: content_item_id -> item_progress
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
                        # 只要有 feedback 或 passed 欄位，就需要儲存
                        if (
                            item_data.get("feedback")
                            or item_data.get("passed") is not None
                        ):
                            # 🔥 Get from preloaded map (no query)
                            item_progress = item_progress_map.get(
                                content.content_items[i].id
                            )

                            # 方案A：按需創建 - 如果記錄不存在，就創建一個
                            if not item_progress:
                                logger.info(
                                    f"Creating StudentItemProgress on-demand: "
                                    f"assignment_id={assignment.id}, "
                                    f"content_item_id={content.content_items[i].id}"
                                )

                                try:
                                    item_progress = StudentItemProgress(
                                        student_assignment_id=assignment.id,
                                        content_item_id=content.content_items[i].id,
                                        status="NOT_SUBMITTED",  # 學生未提交
                                        answer_text=None,
                                        recording_url=None,
                                        # AI 評分欄位保持空白
                                        accuracy_score=None,
                                        fluency_score=None,
                                        pronunciation_score=None,
                                        ai_feedback=None,
                                        # 老師可以直接給評語
                                        review_status="PENDING",
                                    )
                                    db.add(item_progress)
                                    db.flush()  # 取得 ID 但還沒 commit
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
                            item_progress.teacher_passed = item_data.get(
                                "passed"
                            )  # 儲存通過與否狀態
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
                # 確保 response_data 是一個新的字典，這樣 SQLAlchemy 會偵測到變更
                new_response_data = (
                    progress.response_data.copy() if progress.response_data else {}
                )
                new_response_data["item_feedbacks"] = items_feedback
                progress.response_data = new_response_data
                # 明確標記欄位已修改，確保 SQLAlchemy 偵測到 JSON 欄位的變更
                flag_modified(progress, "response_data")

                # 更新整體的 checked 狀態（如果所有 items 都評過）
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


@router.post("/assignments/{assignment_id}/set-in-progress")
async def set_assignment_in_progress(
    assignment_id: int,
    data: dict,
    current_teacher: Teacher = Depends(get_current_user),
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
        # 如果是從「要求訂正」回到批改中，檢查是否有重新提交
        if assignment.resubmitted_at and (
            not assignment.submitted_at
            or assignment.resubmitted_at > assignment.submitted_at
        ):
            assignment.status = AssignmentStatus.RESUBMITTED
        else:
            assignment.status = AssignmentStatus.SUBMITTED
    elif assignment.status == AssignmentStatus.GRADED:
        # 從「已完成」回到批改中
        if assignment.resubmitted_at and (
            not assignment.submitted_at
            or assignment.resubmitted_at > assignment.submitted_at
        ):
            assignment.status = AssignmentStatus.RESUBMITTED
        else:
            assignment.status = AssignmentStatus.SUBMITTED
        # 清除批改時間
        assignment.graded_at = None

    db.commit()

    return {
        "message": "Assignment set to in progress",
        "assignment_id": assignment.id,
        "student_id": student_id,
        "status": assignment.status.value,
    }


@router.post("/assignments/{assignment_id}/return-for-revision")
async def return_for_revision(
    assignment_id: int,
    data: dict,
    current_teacher: Teacher = Depends(get_current_user),
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
                progress.checked = True  # 標記為已批改
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
