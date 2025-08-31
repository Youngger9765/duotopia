"""
作業系統 API 路由
Phase 1: 基礎指派功能
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from pydantic import BaseModel
from database import get_db
from models import (
    Teacher, Student, Classroom, ClassroomStudent,
    Content, Lesson, Program,
    StudentAssignment, AssignmentStatus
)
from .auth import get_current_user as get_current_teacher

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
    current_teacher: Teacher = Depends(get_current_teacher)
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
    current_teacher: Teacher = Depends(get_current_teacher)
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
    current_teacher: Teacher = Depends(get_current_teacher)
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
    current_teacher: Teacher = Depends(get_current_teacher)
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
    from sqlalchemy import func
    stats = db.query(
        StudentAssignment.content_id,
        StudentAssignment.classroom_id,
        StudentAssignment.title,
        func.count(StudentAssignment.id).label("total_count"),
        func.sum(
            (StudentAssignment.status == AssignmentStatus.NOT_STARTED).cast(int)
        ).label("not_started"),
        func.sum(
            (StudentAssignment.status == AssignmentStatus.IN_PROGRESS).cast(int)
        ).label("in_progress"),
        func.sum(
            (StudentAssignment.status == AssignmentStatus.SUBMITTED).cast(int)
        ).label("submitted"),
        func.sum(
            (StudentAssignment.status == AssignmentStatus.GRADED).cast(int)
        ).label("graded"),
        func.sum(
            (StudentAssignment.status == AssignmentStatus.RETURNED).cast(int)
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