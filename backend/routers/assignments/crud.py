"""
Assignment CRUD operations
"""

from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, func

from database import get_db
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
from .validators import (
    CreateAssignmentRequest,
    UpdateAssignmentRequest,
    StudentResponse,
    ContentResponse,
)
from .dependencies import get_current_teacher

router = APIRouter()


@router.post("/create")
async def create_assignment(
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    建立作業（新架構）
    - 建立 Assignment 主表記錄
    - 關聯多個 Content
    - 指派給指定學生或全班
    """
    # 驗證教師訂閱狀態
    if not current_teacher.can_assign_homework:
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

    # 驗證所有 Content 存在
    contents = db.query(Content).filter(Content.id.in_(request.content_ids)).all()
    if len(contents) != len(request.content_ids):
        raise HTTPException(status_code=404, detail="Some contents not found")

    # 建立 Assignment 主表記錄
    assignment = Assignment(
        title=request.title,
        description=request.description,
        classroom_id=request.classroom_id,
        teacher_id=current_teacher.id,
        due_date=request.due_date,
        is_active=True,
        # 例句集作答模式設定
        answer_mode=request.answer_mode,
        practice_mode=request.practice_mode,
        time_limit_per_question=request.time_limit_per_question,
        shuffle_questions=request.shuffle_questions,
        play_audio=request.play_audio,
        show_answer=request.show_answer,
        # Phase 2: 單字集作答模式設定
        target_proficiency=request.target_proficiency,
        show_translation=request.show_translation,
        show_word=request.show_word,
        show_image=request.show_image,
    )
    db.add(assignment)
    db.flush()  # 取得 assignment.id

    # 建立 AssignmentContent 關聯
    for idx, content_id in enumerate(request.content_ids, 1):
        assignment_content = AssignmentContent(
            assignment_id=assignment.id, content_id=content_id, order_index=idx
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

    # Preload all ContentItems for all content_ids (avoid N+1)
    all_content_items = (
        db.query(ContentItem)
        .filter(ContentItem.content_id.in_(request.content_ids))
        .order_by(ContentItem.content_id, ContentItem.order_index)
        .all()
    )
    # Build map: content_id -> [items]
    content_items_map = {}
    for item in all_content_items:
        if item.content_id not in content_items_map:
            content_items_map[item.content_id] = []
        content_items_map[item.content_id].append(item)

    # 為每個學生建立 StudentAssignment
    for student in students:
        student_assignment = StudentAssignment(
            assignment_id=assignment.id,
            student_id=student.id,
            classroom_id=request.classroom_id,
            # 暫時保留舊欄位以兼容
            title=request.title,
            instructions=request.description,
            due_date=request.due_date,
            status=AssignmentStatus.NOT_STARTED,
            is_active=True,
        )
        db.add(student_assignment)
        db.flush()

        # 為每個內容建立進度記錄
        for idx, content_id in enumerate(request.content_ids, 1):
            progress = StudentContentProgress(
                student_assignment_id=student_assignment.id,
                content_id=content_id,
                status=AssignmentStatus.NOT_STARTED,
                order_index=idx,
                is_locked=False if idx == 1 else True,  # 只解鎖第一個
            )
            db.add(progress)
            db.flush()  # 取得 progress.id

            # Get content items from preloaded map (no query)
            content_items = content_items_map.get(content_id, [])

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
        "assignment_id": assignment.id,
        "student_count": len(students),
        "content_count": len(request.content_ids),
        "message": f"Successfully created assignment for {len(students)} students",
    }


@router.get("/")
async def get_assignments(
    classroom_id: Optional[int] = Query(None, description="Filter by classroom"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    取得作業列表（新架構）
    - 教師看到自己建立的作業
    - 可依班級和狀態篩選
    """
    # 建立查詢
    query = db.query(Assignment).filter(
        Assignment.teacher_id == current_teacher.id, Assignment.is_active.is_(True)
    )

    # 套用篩選
    if classroom_id:
        query = query.filter(Assignment.classroom_id == classroom_id)

    assignments = query.order_by(Assignment.created_at.desc()).all()

    # Batch-load assignment content counts (avoid N+1)
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

    # Batch-load all student assignments (avoid N+1)
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
        # Get from preloaded maps (no queries)
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


@router.put("/{assignment_id}")
async def update_assignment(
    assignment_id: int,
    request: CreateAssignmentRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    編輯作業（新架構）
    """
    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_teacher.id,
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


@router.patch("/{assignment_id}")
async def patch_assignment(
    assignment_id: int,
    request: UpdateAssignmentRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    部分更新作業（只更新提供的欄位）
    """
    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_teacher.id,
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

        # Preload existing student assignments (avoid N+1)
        existing_student_assignments = (
            db.query(StudentAssignment)
            .filter(StudentAssignment.assignment_id == assignment_id)
            .all()
        )
        existing_student_ids = {sa.student_id for sa in existing_student_assignments}

        # Preload assignment contents (avoid N+1)
        assignment_contents = (
            db.query(AssignmentContent)
            .filter(AssignmentContent.assignment_id == assignment_id)
            .order_by(AssignmentContent.order_index)
            .all()
        )

        # Preload all content items (avoid N+1)
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
            # Check from preloaded set (no query)
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

            # Use preloaded assignment_contents (no query)
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

                # Use preloaded content_items (no query)
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


@router.delete("/{assignment_id}")
async def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    軟刪除作業（新架構）
    """
    # 取得並驗證作業
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.teacher_id == current_teacher.id,
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

    db.commit()

    return {"success": True, "message": "Assignment deleted successfully"}


@router.get("/classrooms/{classroom_id}/students", response_model=List[StudentResponse])
async def get_classroom_students(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得班級的學生列表"""
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
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    取得可用的 Content 列表
    如果提供 classroom_id，只回傳該班級的 Content
    """
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
