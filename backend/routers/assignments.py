"""
作業系統 API 路由
Phase 1: 基礎指派功能
"""

from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from database import get_db
from models import (
    Teacher, Student, Classroom, ClassroomStudent,
    Content, Lesson, Program,
    StudentAssignment, AssignmentStatus, AssignmentSubmission
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


# ============ API Endpoints ============

@router.post("/assignments/create")
async def create_assignment(
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_teacher = Depends(get_current_user)
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
    
    # 1. 驗證 Content 存在
    content = db.query(Content).filter(Content.id == request.content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # 2. 驗證班級存在且屬於當前教師
    classroom = db.query(Classroom).filter(
        and_(
            Classroom.id == request.classroom_id,
            Classroom.teacher_id == current_teacher.id,
            Classroom.is_active == True
        )
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found or you don't have permission"
        )
    
    # 3. 取得要指派的學生列表
    if request.student_ids:
        # 指派給特定學生
        students = db.query(Student).join(ClassroomStudent).filter(
            and_(
                ClassroomStudent.classroom_id == request.classroom_id,
                Student.id.in_(request.student_ids),
                Student.is_active == True,
                ClassroomStudent.is_active == True
            )
        ).all()
        
        if len(students) != len(request.student_ids):
            raise HTTPException(
                status_code=400,
                detail="Some students not found in this classroom"
            )
    else:
        # 指派給全班
        students = db.query(Student).join(ClassroomStudent).filter(
            and_(
                ClassroomStudent.classroom_id == request.classroom_id,
                Student.is_active == True,
                ClassroomStudent.is_active == True
            )
        ).all()
        
        if not students:
            raise HTTPException(
                status_code=400,
                detail="No active students in this classroom"
            )
    
    # 4. 建立作業記錄
    assignments = []
    for student in students:
        # 檢查是否已有相同作業
        existing = db.query(StudentAssignment).filter(
            and_(
                StudentAssignment.student_id == student.id,
                StudentAssignment.content_id == request.content_id,
                StudentAssignment.classroom_id == request.classroom_id,
                StudentAssignment.status != AssignmentStatus.GRADED
            )
        ).first()
        
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
            due_date=request.due_date
        )
        db.add(assignment)
        assignments.append(assignment)
    
    # 5. 提交到資料庫
    if assignments:
        db.commit()
    
    return {
        "success": True,
        "count": len(assignments),
        "message": f"Successfully created {len(assignments)} assignments"
    }


@router.get("/classrooms/{classroom_id}/students", response_model=List[StudentResponse])
async def get_classroom_students(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher = Depends(get_current_user)
):
    """取得班級的學生列表"""
    
    # 驗證班級存在且屬於當前教師
    classroom = db.query(Classroom).filter(
        and_(
            Classroom.id == classroom_id,
            Classroom.teacher_id == current_teacher.id,
            Classroom.is_active == True
        )
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="Classroom not found or you don't have permission"
        )
    
    # 取得班級學生
    students = db.query(Student).join(ClassroomStudent).filter(
        and_(
            ClassroomStudent.classroom_id == classroom_id,
            Student.is_active == True,
            ClassroomStudent.is_active == True
        )
    ).all()
    
    return students


@router.get("/contents", response_model=List[ContentResponse])
async def get_available_contents(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    db: Session = Depends(get_db),
    current_teacher = Depends(get_current_user)
):
    """
    取得可用的 Content 列表
    如果提供 classroom_id，只回傳該班級的 Content
    """
    
    query = db.query(Content).join(Lesson).join(Program)
    
    if classroom_id:
        # 驗證班級權限
        classroom = db.query(Classroom).filter(
            and_(
                Classroom.id == classroom_id,
                Classroom.teacher_id == current_teacher.id,
                Classroom.is_active == True
            )
        ).first()
        
        if not classroom:
            raise HTTPException(
                status_code=404,
                detail="Classroom not found or you don't have permission"
            )
        
        # 篩選該班級的 Content
        query = query.filter(Program.classroom_id == classroom_id)
    else:
        # 回傳該教師所有的 Content
        query = query.filter(Program.teacher_id == current_teacher.id)
    
    contents = query.all()
    
    # 轉換為回應格式
    response = []
    for content in contents:
        items_count = len(content.items) if content.items else 0
        response.append(ContentResponse(
            id=content.id,
            lesson_id=content.lesson_id,
            title=content.title,
            type=content.type.value if hasattr(content.type, 'value') else str(content.type),
            level=content.level,
            items_count=items_count
        ))
    
    return response


@router.get("/assignments/teacher")
async def get_teacher_assignments(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_teacher = Depends(get_current_user)
):
    """
    取得教師的作業列表
    可依班級和狀態篩選
    """
    
    # 建立查詢
    query = db.query(StudentAssignment).join(Classroom).filter(
        Classroom.teacher_id == current_teacher.id
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
    
    # 排序：最新的在前
    assignments = query.order_by(StudentAssignment.assigned_at.desc()).all()
    
    # 統計資訊
    from sqlalchemy import func, case
    stats = db.query(
        StudentAssignment.content_id,
        StudentAssignment.classroom_id,
        StudentAssignment.title,
        func.count(StudentAssignment.id).label("total_count"),
        func.sum(
            case((StudentAssignment.status == AssignmentStatus.NOT_STARTED, 1), else_=0)
        ).label("not_started"),
        func.sum(
            case((StudentAssignment.status == AssignmentStatus.IN_PROGRESS, 1), else_=0)
        ).label("in_progress"),
        func.sum(
            case((StudentAssignment.status == AssignmentStatus.SUBMITTED, 1), else_=0)
        ).label("submitted"),
        func.sum(
            case((StudentAssignment.status == AssignmentStatus.GRADED, 1), else_=0)
        ).label("graded"),
        func.sum(
            case((StudentAssignment.status == AssignmentStatus.RETURNED, 1), else_=0)
        ).label("returned")
    ).join(Classroom).filter(
        Classroom.teacher_id == current_teacher.id
    )
    
    if classroom_id:
        stats = stats.filter(StudentAssignment.classroom_id == classroom_id)
    
    stats = stats.group_by(
        StudentAssignment.content_id,
        StudentAssignment.classroom_id,
        StudentAssignment.title
    ).all()
    
    # 組合回應
    result = []
    for stat in stats:
        result.append({
            "content_id": stat.content_id,
            "classroom_id": stat.classroom_id,
            "title": stat.title,
            "total_students": stat.total_count,
            "status_distribution": {
                "not_started": stat.not_started or 0,
                "in_progress": stat.in_progress or 0,
                "submitted": stat.submitted or 0,
                "graded": stat.graded or 0,
                "returned": stat.returned or 0
            }
        })
    
    return result


# ============ Student APIs ============

@router.get("/assignments/student")
async def get_student_assignments(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    取得學生的作業列表
    學生只能看到自己的作業
    """
    
    # 確認是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403,
            detail="Only students can access this endpoint"
        )
    
    # 建立查詢
    query = db.query(StudentAssignment).filter(
        StudentAssignment.student_id == current_user.id
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
        StudentAssignment.assigned_at.desc()
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
        
        result.append({
            "id": assignment.id,
            "title": assignment.title,
            "instructions": assignment.instructions,
            "status": assignment.status.value,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "submitted_at": assignment.submitted_at.isoformat() if assignment.submitted_at else None,
            "score": assignment.score,
            "feedback": assignment.feedback,
            "time_remaining": time_remaining,
            "is_overdue": is_overdue,
            "content": {
                "id": content.id,
                "title": content.title,
                "type": content.type.value if hasattr(content.type, 'value') else str(content.type),
                "items_count": len(content.items) if content.items else 0
            } if content else None
        })
    
    return result


@router.post("/assignments/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    submission_data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    提交作業
    學生只能提交自己的作業
    """
    
    # 確認是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403,
            detail="Only students can submit assignments"
        )
    
    # 取得作業
    assignment = db.query(StudentAssignment).filter(
        StudentAssignment.id == assignment_id,
        StudentAssignment.student_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or you don't have permission"
        )
    
    # 檢查作業狀態
    if assignment.status == AssignmentStatus.GRADED:
        raise HTTPException(
            status_code=400,
            detail="Assignment has already been graded"
        )
    
    # 檢查是否過期（但仍允許提交）
    is_late = False
    if assignment.due_date and assignment.due_date < datetime.now(timezone.utc):
        is_late = True
    
    # 更新作業狀態
    assignment.status = AssignmentStatus.SUBMITTED
    assignment.submitted_at = datetime.now(timezone.utc)
    
    # 檢查是否已有提交記錄
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).first()
    
    if submission:
        # 更新現有提交
        submission.submission_data = submission_data
        submission.submitted_at = datetime.now(timezone.utc)
    else:
        # 建立新提交
        submission = AssignmentSubmission(
            assignment_id=assignment_id,
            submission_data=submission_data
        )
        db.add(submission)
    
    db.commit()
    
    return {
        "success": True,
        "message": "作業提交成功" + ("（遲交）" if is_late else ""),
        "submission_time": datetime.now().isoformat(),
        "is_late": is_late
    }


@router.get("/assignments/{assignment_id}/detail")
async def get_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    取得作業詳細資訊
    學生只能查看自己的作業
    """
    
    # 確認是學生身份
    if not isinstance(current_user, Student):
        raise HTTPException(
            status_code=403,
            detail="Only students can access this endpoint"
        )
    
    # 取得作業
    assignment = db.query(StudentAssignment).filter(
        StudentAssignment.id == assignment_id,
        StudentAssignment.student_id == current_user.id
    ).first()
    
    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found or you don't have permission"
        )
    
    # 取得 Content 詳細資訊
    content = db.query(Content).filter(Content.id == assignment.content_id).first()
    
    # 取得提交記錄
    submission = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).first()
    
    return {
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "instructions": assignment.instructions,
            "status": assignment.status.value,
            "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
            "score": assignment.score,
            "feedback": assignment.feedback
        },
        "content": {
            "id": content.id,
            "title": content.title,
            "type": content.type.value if hasattr(content.type, 'value') else str(content.type),
            "items": content.items,
            "level": content.level,
            "tags": content.tags
        } if content else None,
        "submission": {
            "id": submission.id,
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "submission_data": submission.submission_data,
            "ai_scores": submission.ai_scores,
            "ai_feedback": submission.ai_feedback
        } if submission else None
    }