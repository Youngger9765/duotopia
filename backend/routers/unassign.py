"""
取消指派作業 API
Unassign students from assignments with progress protection
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional  # noqa: F401
from datetime import datetime, timezone  # noqa: F401
from pydantic import BaseModel

from database import get_db
from models import (
    Teacher,
    Student,
    Assignment,
    StudentAssignment,
    AssignmentStatus,
    StudentContentProgress,
)
from routers.auth import get_current_user

router = APIRouter(prefix="/api/teachers", tags=["unassign"])


class UnassignRequest(BaseModel):
    """取消指派請求"""

    student_ids: List[int]
    force: bool = False  # 強制取消（即使學生已開始）


class UnassignResponse(BaseModel):
    """取消指派回應"""

    success: bool
    unassigned: List[int]  # 成功取消的學生 IDs
    protected: List[dict]  # 受保護的學生（已開始或完成）
    message: str


@router.post("/assignments/{assignment_id}/unassign")
async def unassign_students(
    assignment_id: int,
    request: UnassignRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    取消指派學生

    規則：
    1. NOT_STARTED: 直接取消
    2. IN_PROGRESS: 需要 force=True 才能取消
    3. SUBMITTED/COMPLETED: 不允許取消（除非是系統管理員）
    """

    # 驗證教師身份
    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can unassign students"
        )

    # 驗證作業存在且屬於當前教師
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

    unassigned = []
    protected = []

    for student_id in request.student_ids:
        # 查找學生作業記錄
        student_assignment = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.assignment_id == assignment_id,
                StudentAssignment.student_id == student_id,
                StudentAssignment.is_active.is_(True),
            )
            .first()
        )

        if not student_assignment:
            continue  # 學生本來就沒有被指派

        # 取得學生資訊
        student = db.query(Student).filter(Student.id == student_id).first()
        student_name = student.name if student else f"Student {student_id}"

        # 檢查作業狀態
        if student_assignment.status == AssignmentStatus.NOT_STARTED:
            # 未開始 - 可以直接取消
            # 先刪除相關的內容進度記錄
            db.query(StudentContentProgress).filter(
                StudentContentProgress.student_assignment_id == student_assignment.id
            ).delete()

            # 刪除作業記錄
            db.delete(student_assignment)
            unassigned.append(student_id)

        elif student_assignment.status == AssignmentStatus.IN_PROGRESS:
            # 進行中 - 需要強制標記
            if request.force:
                # 軟刪除：保留記錄但標記為非活躍
                student_assignment.is_active = False
                student_assignment.updated_at = datetime.now(timezone.utc)
                # 可選：加入取消原因
                # student_assignment.cancel_reason = "Teacher unassigned"
                unassigned.append(student_id)
            else:
                protected.append(
                    {
                        "student_id": student_id,
                        "student_name": student_name,
                        "status": student_assignment.status.value,
                        "reason": "學生已開始作業，需要確認才能取消",
                    }
                )

        elif student_assignment.status in [
            AssignmentStatus.SUBMITTED,
            AssignmentStatus.GRADED,
        ]:
            # 已提交或完成 - 不允許取消
            protected.append(
                {
                    "student_id": student_id,
                    "student_name": student_name,
                    "status": student_assignment.status.value,
                    "reason": "學生已完成作業，無法取消指派",
                }
            )
        else:
            # OVERDUE 或其他狀態 - 根據需求處理
            if request.force:
                student_assignment.is_active = False
                student_assignment.updated_at = datetime.now(timezone.utc)
                unassigned.append(student_id)
            else:
                protected.append(
                    {
                        "student_id": student_id,
                        "student_name": student_name,
                        "status": student_assignment.status.value,
                        "reason": "作業狀態需要確認",
                    }
                )

    # 提交變更
    db.commit()

    # 準備回應訊息
    message = f"成功取消 {len(unassigned)} 位學生的指派"
    if protected:
        message += f"，{len(protected)} 位學生因已有進度而受保護"

    return UnassignResponse(
        success=True, unassigned=unassigned, protected=protected, message=message
    )


@router.get("/assignments/{assignment_id}/unassign-preview")
async def preview_unassign(
    assignment_id: int,
    student_ids: str,  # Comma-separated list
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    預覽取消指派的影響
    顯示哪些學生可以取消，哪些需要確認
    """

    if not isinstance(current_user, Teacher):
        raise HTTPException(
            status_code=403, detail="Only teachers can preview unassign"
        )

    # 解析學生 IDs
    try:
        student_id_list = [int(id.strip()) for id in student_ids.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid student IDs format")

    # 驗證作業
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
        raise HTTPException(status_code=404, detail="Assignment not found")

    preview = {
        "can_unassign": [],  # 可以直接取消的
        "need_confirmation": [],  # 需要確認的
        "cannot_unassign": [],  # 不能取消的
    }

    for student_id in student_id_list:
        student_assignment = (
            db.query(StudentAssignment)
            .filter(
                StudentAssignment.assignment_id == assignment_id,
                StudentAssignment.student_id == student_id,
                StudentAssignment.is_active.is_(True),
            )
            .first()
        )

        if not student_assignment:
            continue

        student = db.query(Student).filter(Student.id == student_id).first()
        student_info = {
            "student_id": student_id,
            "student_name": student.name if student else f"Student {student_id}",
            "status": student_assignment.status.value,
            "started_at": student_assignment.started_at.isoformat()
            if student_assignment.started_at
            else None,
            "submitted_at": student_assignment.submitted_at.isoformat()
            if student_assignment.submitted_at
            else None,
        }

        if student_assignment.status == AssignmentStatus.NOT_STARTED:
            preview["can_unassign"].append(student_info)
        elif student_assignment.status == AssignmentStatus.IN_PROGRESS:
            # 計算進度
            progress_count = (
                db.query(StudentContentProgress)
                .filter(
                    StudentContentProgress.student_assignment_id
                    == student_assignment.id,
                    StudentContentProgress.status != AssignmentStatus.NOT_STARTED,
                )
                .count()
            )
            student_info["progress_count"] = progress_count
            preview["need_confirmation"].append(student_info)
        else:
            preview["cannot_unassign"].append(student_info)

    return preview
