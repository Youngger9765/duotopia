"""
課程管理 API - 支援公版模板和班級課程
"""

from datetime import datetime, timezone  # noqa: F401
from typing import List, Literal, Optional  # noqa: F401
from copy import deepcopy
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import SQLAlchemyError
from services import program_service

from database import get_db
from models import (
    Program,
    Lesson,
    Teacher,
    Classroom,
    Content,
    ContentItem,
    Organization,
    TeacherOrganization,
    School,
    TeacherSchool,
)
from schemas import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramCopyFromTemplate,
    ProgramCopyFromClassroom,
    ProgramCopyRequest,
    LessonCreate,
    LessonUpdate,
    LessonResponse,
    ContentCreate,
)
from auth import verify_token
from utils.permissions import (
    has_manage_materials_permission,
    has_school_materials_permission,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")

router = APIRouter(prefix="/api/programs", tags=["programs"])

logger = logging.getLogger(__name__)


# ============ 認證輔助函數 ============


async def get_current_teacher(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """取得當前登入的教師"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    teacher_id = payload.get("sub")
    teacher_type = payload.get("type")

    if teacher_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a teacher"
        )

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


# ============ 公版模板管理 ============


@router.get("/templates", response_model=List[ProgramResponse])
async def get_template_programs(
    classroom_id: int = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得所有公版課程模板（只看得到自己建立的），並標記重複狀態"""
    templates = (
        db.query(Program)
        .options(joinedload(Program.lessons).joinedload(Lesson.contents))
        .filter(
            Program.is_template.is_(True),
            Program.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
            Program.deleted_at.is_(None),
        )
        .order_by(Program.order_index)
        .all()
    )

    # 手動排序 lessons 和 contents
    for template in templates:
        if template.lessons:
            template.lessons = sorted(template.lessons, key=lambda x: x.order_index)
            for lesson in template.lessons:
                if lesson.contents:
                    lesson.contents = sorted(
                        lesson.contents, key=lambda x: x.order_index
                    )

    # 如果提供了 classroom_id，檢查重複狀態
    if classroom_id:
        # 獲取目標班級中已存在的課程
        existing_programs = (
            db.query(Program)
            .filter(
                Program.classroom_id == classroom_id,
                Program.is_active.is_(True),
                Program.deleted_at.is_(None),
            )
            .all()
        )

        # 建立已存在模板 ID 集合
        existing_template_ids = set()
        for existing_program in existing_programs:
            if (
                existing_program.source_metadata
                and existing_program.source_type == "template"
            ):
                if "template_id" in existing_program.source_metadata:
                    existing_template_ids.add(
                        existing_program.source_metadata["template_id"]
                    )

        # 標記重複狀態
        for template in templates:
            template.is_duplicate = template.id in existing_template_ids
    else:
        # 沒有提供 classroom_id，不標記重複狀態
        for template in templates:
            template.is_duplicate = False

    return templates


@router.post("/templates", response_model=ProgramResponse)
async def create_template_program(
    program: ProgramCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """建立新的公版課程模板"""
    db_program = Program(
        name=program.name,
        description=program.description,
        level=program.level,
        is_template=True,
        classroom_id=None,  # 公版課程無班級
        teacher_id=current_teacher.id,
        estimated_hours=program.estimated_hours,
        tags=program.tags,
        source_type=None,  # 原創
        source_metadata={
            "created_by": "manual",
            "created_at": datetime.now().isoformat(),
        },
    )

    db.add(db_program)
    db.commit()
    db.refresh(db_program)

    return db_program


@router.get("/templates/{program_id}")
async def get_template_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得單一公版課程模板詳情（包含 lessons 和 contents）"""
    template = (
        db.query(Program)
        .options(
            selectinload(Program.lessons)
            .selectinload(Lesson.contents)
            .selectinload(Content.content_items)
        )
        .filter(
            Program.id == program_id,
            Program.is_template.is_(True),
            Program.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 轉換成包含完整資料的回應
    result = {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "level": template.level,
        "estimated_hours": template.estimated_hours,
        "tags": template.tags,
        "is_template": template.is_template,
        "lessons": [],
    }

    for lesson in template.lessons:
        # 跳過已被軟刪除的單元
        if not lesson.is_active:
            continue

        lesson_data = {
            "id": lesson.id,
            "name": lesson.name,  # 使用 name 欄位
            "description": lesson.description,
            "estimated_minutes": lesson.estimated_minutes,
            "order_index": lesson.order_index,
            "contents": [],
        }

        for content in lesson.contents:
            # 跳過已被軟刪除的內容
            if hasattr(content, "is_active") and not content.is_active:
                continue
            content_items = content.content_items or []
            content_data = {
                "id": content.id,
                "title": content.title,
                "type": content.type,
                "items_count": len(content_items),
                "items": [
                    {
                        "id": item.id,
                        "text": item.text,
                        "translation": item.translation,
                        "audio_url": item.audio_url,
                        "example_sentence": item.example_sentence,
                        "example_sentence_translation": item.example_sentence_translation,
                    }
                    for item in content_items
                ],
            }
            lesson_data["contents"].append(content_data)

        result["lessons"].append(lesson_data)

    return result


@router.put("/templates/{program_id}", response_model=ProgramResponse)
async def update_template_program(
    program_id: int,
    program_update: ProgramUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """更新公版課程模板"""
    template = (
        db.query(Program)
        .filter(
            Program.id == program_id,
            Program.is_template.is_(True),
            Program.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 更新欄位
    if program_update.name is not None:
        template.name = program_update.name
    if program_update.description is not None:
        template.description = program_update.description
    if program_update.level is not None:
        template.level = program_update.level
    if program_update.estimated_hours is not None:
        template.estimated_hours = program_update.estimated_hours
    if program_update.tags is not None:
        template.tags = program_update.tags

    template.updated_at = datetime.now()

    db.commit()
    db.refresh(template)

    return template


# ============ 班級課程管理 ============


@router.get("/classroom/{classroom_id}", response_model=List[ProgramResponse])
async def get_classroom_programs(
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得特定班級的所有課程"""
    # 驗證班級存在且屬於當前教師
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id, Classroom.teacher_id == current_teacher.id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    programs = (
        db.query(Program)
        .filter(
            Program.classroom_id == classroom_id,
            Program.is_active.is_(True),
            Program.deleted_at.is_(None),
        )
        .order_by(Program.order_index, Program.created_at)
        .all()
    )

    result = []
    for program in programs:
        result.append(
            ProgramResponse(
                id=program.id,
                name=program.name,
                description=program.description,
                level=program.level,
                estimated_hours=program.estimated_hours,
                tags=program.tags,
                is_template=program.is_template,
                classroom_id=program.classroom_id,
                teacher_id=program.teacher_id,
                organization_id=str(program.organization_id)
                if program.organization_id
                else None,
                school_id=str(program.school_id) if program.school_id else None,
                source_type=program.source_type,
                source_metadata=program.source_metadata,
                is_active=program.is_active,
                created_at=program.created_at or datetime.now(),
                updated_at=program.updated_at,
                classroom_name=getattr(program, "classroom_name", None),
                teacher_name=getattr(program, "teacher_name", None),
                lesson_count=len(program.lessons) if program.lessons else 0,
                is_duplicate=getattr(program, "is_duplicate", None),
                lessons=[],
            )
        )

    return result


# ============ 三種複製方式 ============


def _deep_copy_content_with_items(
    content: Content, new_lesson_id: int, db: Session
) -> Content:
    """Deep copy a Content object and all its ContentItems.

    Args:
        content: Source Content to copy from
        new_lesson_id: ID of the new lesson to attach content to
        db: Database session

    Returns:
        New Content object with all items copied
    """
    new_content = Content(
        lesson_id=new_lesson_id,
        title=content.title,
        type=content.type,
        level=content.level if hasattr(content, "level") else "A1",
        tags=content.tags.copy() if hasattr(content, "tags") and content.tags else [],
        is_public=content.is_public if hasattr(content, "is_public") else False,
        target_wpm=content.target_wpm if hasattr(content, "target_wpm") else None,
        target_accuracy=content.target_accuracy
        if hasattr(content, "target_accuracy")
        else None,
        time_limit_seconds=content.time_limit_seconds
        if hasattr(content, "time_limit_seconds")
        else None,
        order_index=content.order_index if hasattr(content, "order_index") else 0,
    )
    db.add(new_content)
    db.flush()

    # Deep copy each ContentItem
    for original_item in content.content_items:
        item_copy = ContentItem(
            content_id=new_content.id,
            order_index=original_item.order_index,
            text=original_item.text,
            translation=original_item.translation
            if hasattr(original_item, "translation")
            else None,
            audio_url=original_item.audio_url
            if hasattr(original_item, "audio_url")
            else None,
            item_metadata=deepcopy(original_item.item_metadata)
            if hasattr(original_item, "item_metadata") and original_item.item_metadata
            else {},
        )
        db.add(item_copy)

    return new_content


@router.post("/copy-from-template", response_model=ProgramResponse)
async def copy_from_template(
    data: ProgramCopyFromTemplate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """從公版模板複製課程到班級"""
    # 驗證模板存在 (with eager loading to prevent N+1 queries)
    template = (
        db.query(Program)
        .options(
            selectinload(Program.lessons)
            .selectinload(Lesson.contents)
            .selectinload(Content.content_items)
        )
        .filter(
            Program.id == data.template_id,
            Program.is_template.is_(True),
            Program.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # 驗證目標班級存在
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == data.classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # 建立新課程
    new_program = Program(
        name=data.name or f"{template.name} (複製)",
        description=template.description,
        level=template.level,
        is_template=False,
        classroom_id=data.classroom_id,
        teacher_id=current_teacher.id,
        estimated_hours=template.estimated_hours,
        tags=template.tags,
        source_type="template",
        source_metadata={
            "template_id": template.id,
            "template_name": template.name,
            "copied_at": datetime.now().isoformat(),
        },
    )

    db.add(new_program)
    db.flush()  # 取得 new_program.id

    # 深度複製 Lessons (只複製 is_active=True 的單元)
    for lesson in template.lessons:
        # 跳過已被軟刪除的單元
        if not lesson.is_active:
            continue

        new_lesson = Lesson(
            program_id=new_program.id,
            name=lesson.name,
            description=lesson.description,
            order_index=lesson.order_index,
            estimated_minutes=lesson.estimated_minutes,
        )
        db.add(new_lesson)
        db.flush()

        # 複製 lesson 的 contents
        for content in lesson.contents:
            # 跳過已被軟刪除的內容
            if hasattr(content, "is_active") and not content.is_active:
                continue

            # 🔥 跳過作業副本（這些是建立作業時產生的副本，不應該被複製到新課程）
            if hasattr(content, "is_assignment_copy") and content.is_assignment_copy:
                continue

            # 使用 helper function 進行深度複製
            _deep_copy_content_with_items(content, new_lesson.id, db)

    db.commit()
    db.refresh(new_program)

    return new_program


@router.post("/copy-from-classroom", response_model=ProgramResponse)
async def copy_from_classroom(
    data: ProgramCopyFromClassroom,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """從其他班級複製課程"""
    # 驗證來源課程存在且屬於當前教師 (with eager loading to prevent N+1 queries)
    source_program = (
        db.query(Program)
        .options(
            selectinload(Program.lessons)
            .selectinload(Lesson.contents)
            .selectinload(Content.content_items)
        )
        .join(Classroom)
        .filter(
            Program.id == data.source_program_id,
            Program.is_template.is_(False),
            Classroom.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
        .first()
    )

    if not source_program:
        raise HTTPException(status_code=404, detail="Source program not found")

    # 驗證目標班級存在
    target_classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == data.target_classroom_id,
            Classroom.teacher_id == current_teacher.id,
        )
        .first()
    )

    if not target_classroom:
        raise HTTPException(status_code=404, detail="Target classroom not found")

    # 建立新課程
    new_program = Program(
        name=data.name or f"{source_program.name} (從{source_program.classroom.name}複製)",
        description=source_program.description,
        level=source_program.level,
        is_template=False,
        classroom_id=data.target_classroom_id,
        teacher_id=current_teacher.id,
        estimated_hours=source_program.estimated_hours,
        tags=source_program.tags,
        source_type="classroom",
        source_metadata={
            "source_classroom_id": source_program.classroom_id,
            "source_classroom_name": source_program.classroom.name,
            "source_program_id": source_program.id,
            "source_program_name": source_program.name,
            "copied_at": datetime.now().isoformat(),
        },
    )

    db.add(new_program)
    db.flush()

    # 深度複製 Lessons (只複製 is_active=True 的單元)
    for lesson in source_program.lessons:
        # 跳過已被軟刪除的單元
        if not lesson.is_active:
            continue

        new_lesson = Lesson(
            program_id=new_program.id,
            name=lesson.name,
            description=lesson.description,
            order_index=lesson.order_index,
            estimated_minutes=lesson.estimated_minutes,
        )
        db.add(new_lesson)
        db.flush()  # 取得 new_lesson.id

        # 複製 lesson 的 contents (Issue #81 修復)
        for content in lesson.contents:
            # 跳過已被軟刪除的內容
            if hasattr(content, "is_active") and not content.is_active:
                continue

            # 🔥 跳過作業副本（這些是建立作業時產生的副本，不應該被複製到新課程）
            if hasattr(content, "is_assignment_copy") and content.is_assignment_copy:
                continue

            # 使用 helper function 進行深度複製
            _deep_copy_content_with_items(content, new_lesson.id, db)

    db.commit()
    db.refresh(new_program)

    return new_program


@router.post("/create-custom", response_model=ProgramResponse)
async def create_custom_program(
    program: ProgramCreate,
    classroom_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """在班級中自建課程"""
    # 驗證班級存在
    classroom = (
        db.query(Classroom)
        .filter(
            Classroom.id == classroom_id, Classroom.teacher_id == current_teacher.id
        )
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # 建立新課程
    new_program = Program(
        name=program.name,
        description=program.description,
        level=program.level,
        is_template=False,
        classroom_id=classroom_id,
        teacher_id=current_teacher.id,
        estimated_hours=program.estimated_hours,
        tags=program.tags,
        source_type="custom",
        source_metadata={
            "created_by": "manual",
            "created_at": datetime.now().isoformat(),
        },
    )

    db.add(new_program)
    db.commit()
    db.refresh(new_program)

    return new_program


# ============ 輔助功能 ============


@router.get("/copyable", response_model=List[ProgramResponse])
async def get_copyable_programs(
    classroom_id: int,
    school_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得教師班級的課程（只顯示班級課程，不含公版模板），並標記重複狀態

    Args:
        classroom_id: 目標班級 ID
        school_id: 可選，如果提供則只顯示該學校的班級課程（學校模式）
    """
    # 只取得班級課程 - 使用 joinedload 來載入 classroom 關聯
    query = (
        db.query(Program)
        .options(joinedload(Program.classroom))
        .join(Classroom)
        .filter(
            Program.is_template.is_(False),
            Classroom.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
    )

    # 如果提供 school_id，只顯示該學校的班級課程
    if school_id:
        try:
            school_uuid = uuid.UUID(school_id)
            query = query.filter(Classroom.school_id == school_uuid)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid school_id format",
            )

    classroom_programs = query.all()

    # 獲取目標班級中已存在的課程，用於重複檢測
    target_classroom_programs = (
        db.query(Program)
        .filter(
            Program.classroom_id == classroom_id,
            Program.is_active.is_(True),
            Program.deleted_at.is_(None),
        )
        .all()
    )

    # 建立重複檢測映射
    existing_template_ids = set()
    existing_program_ids = set()

    for existing_program in target_classroom_programs:
        if existing_program.source_metadata:
            # 檢查從模板複製的課程
            if (
                existing_program.source_type == "template"
                and "template_id" in existing_program.source_metadata
            ):
                existing_template_ids.add(
                    existing_program.source_metadata["template_id"]
                )
            # 檢查從其他班級複製的課程
            elif (
                existing_program.source_type == "classroom"
                and "source_program_id" in existing_program.source_metadata
            ):
                existing_program_ids.add(
                    existing_program.source_metadata["source_program_id"]
                )

    # 手動添加 classroom_name 和 is_duplicate 標記
    result = []

    # 只添加班級課程（有班級名稱）
    for program in classroom_programs:
        program.classroom_name = program.classroom.name if program.classroom else None

        # 檢查是否重複
        is_duplicate = False
        if program.source_metadata:
            if (
                program.source_type == "template"
                and "template_id" in program.source_metadata
            ):
                is_duplicate = (
                    program.source_metadata["template_id"] in existing_template_ids
                )
            elif (
                program.source_type == "classroom"
                and "source_program_id" in program.source_metadata
            ):
                is_duplicate = (
                    program.source_metadata["source_program_id"] in existing_program_ids
                )

        # 添加自定義屬性（不在數據庫模型中）
        program.is_duplicate = is_duplicate
        result.append(program)

    return result


@router.delete("/{program_id}")
async def soft_delete_program(
    program_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """軟刪除課程"""
    program = (
        db.query(Program)
        .filter(Program.id == program_id, Program.teacher_id == current_teacher.id)
        .first()
    )

    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # 軟刪除
    program.is_active = False
    program.deleted_at = datetime.now(timezone.utc)

    db.commit()

    return {"message": "Program deleted successfully"}


# ============================================================================
# UNIFIED PROGRAMS API (TDD Implementation)
# Supports both teacher and organization scopes
# ============================================================================


@router.get("", response_model=List[ProgramResponse])
async def list_programs(
    scope: Literal["teacher", "organization", "school"] = Query(
        ..., description="Scope: teacher, organization, or school"
    ),
    organization_id: str = Query(None, description="Required if scope=organization"),
    school_id: str = Query(None, description="Required if scope=school"),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: List programs based on scope.

    - scope=teacher: Returns teacher's personal programs
    - scope=organization: Returns organization programs (requires organization_id)
    - scope=school: Returns school programs (requires school_id)
    """
    # Validate parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when scope=organization",
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id is required when scope=school",
        )

    try:
        import uuid as uuid_module

        org_uuid = uuid_module.UUID(organization_id) if organization_id else None
        sch_uuid = uuid_module.UUID(school_id) if school_id else None
        programs = program_service.get_programs_by_scope(
            scope=scope,
            teacher_id=current_teacher.id,
            db=db,
            organization_id=org_uuid,
            school_id=sch_uuid,
        )

        # Build response with hierarchy
        result = []
        for program in sorted(programs, key=lambda x: x.order_index):
            program_data = ProgramResponse(
                id=program.id,
                name=program.name,
                description=program.description,
                level=program.level,
                estimated_hours=program.estimated_hours,
                tags=program.tags,
                is_template=program.is_template,
                classroom_id=program.classroom_id,
                teacher_id=program.teacher_id,
                organization_id=str(program.organization_id)
                if program.organization_id
                else None,
                school_id=str(program.school_id) if program.school_id else None,
                source_type=program.source_type,
                source_metadata=program.source_metadata,
                is_active=program.is_active,
                created_at=program.created_at or datetime.now(),
                updated_at=program.updated_at,
                classroom_name=getattr(program, "classroom_name", None),
                teacher_name=getattr(program, "teacher_name", None),
                lesson_count=len(program.lessons) if program.lessons else 0,
                is_duplicate=getattr(program, "is_duplicate", None),
                lessons=[],
            )
            program_data.lessons = []

            for lesson in sorted(program.lessons, key=lambda x: x.order_index):
                lesson_data = {
                    "id": lesson.id,
                    "program_id": lesson.program_id,
                    "name": lesson.name,
                    "description": lesson.description,
                    "order_index": lesson.order_index,
                    "is_active": lesson.is_active,
                    "contents": [],
                }

                for content in sorted(lesson.contents, key=lambda x: x.order_index):
                    content_data = {
                        "id": content.id,
                        "lesson_id": content.lesson_id,
                        "type": content.type,
                        "title": content.title,
                        "order_index": content.order_index,
                        "is_active": content.is_active,
                        "items": [
                            {
                                "id": item.id,
                                "content_id": item.content_id,
                                "order_index": item.order_index,
                                "text": item.text,
                                "translation": item.translation,
                                "audio_url": item.audio_url,
                            }
                            for item in sorted(
                                content.content_items, key=lambda x: x.order_index
                            )
                        ],
                    }
                    lesson_data["contents"].append(content_data)

                program_data.lessons.append(lesson_data)

            result.append(program_data)

        return result

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def _has_school_access(teacher_id: int, school_id: uuid.UUID, db: Session) -> bool:
    # 1. Get school's organization_id
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return False

    # 2. Check if teacher is org_owner or org_admin (organization-level access)
    if school.organization_id:
        org_membership = (
            db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == teacher_id,
                TeacherOrganization.organization_id == school.organization_id,
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )

        if org_membership and org_membership.role in ["org_owner", "org_admin"]:
            return True

    # 3. Check school-level membership
    membership = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == school_id,
            TeacherSchool.is_active.is_(True),
        )
        .first()
    )

    if not membership or not membership.roles:
        return False

    return any(
        role in ["school_admin", "school_director", "teacher"]
        for role in membership.roles
    )


def _has_school_manage_permission(
    teacher_id: int, school_id: uuid.UUID, db: Session
) -> bool:
    # 1. Get school's organization_id
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        return False

    # 2. Check if teacher is org_owner or org_admin
    org_membership = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher_id,
            TeacherOrganization.organization_id == school.organization_id,
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if org_membership and org_membership.role in ["org_owner", "org_admin"]:
        return True

    # 3. Original teacher_schools check
    membership = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == school_id,
            TeacherSchool.is_active.is_(True),
        )
        .first()
    )

    if not membership or not membership.roles:
        return False

    return any(role in ["school_admin", "school_director"] for role in membership.roles)


@router.post("/{program_id}/copy", response_model=ProgramResponse, status_code=201)
async def copy_program(
    program_id: int,
    payload: ProgramCopyRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Unified program copy API (supports classroom target for now)."""
    if payload.target_scope not in ["classroom", "teacher", "school"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid target_scope",
        )

    target_id_int = None
    target_school_id = None
    if payload.target_scope in ["classroom", "teacher"]:
        try:
            target_id_int = int(payload.target_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_id for classroom/teacher",
            )
    else:
        try:
            target_school_id = uuid.UUID(payload.target_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid target_id for school",
            )

    source_program = (
        db.query(Program)
        .options(
            joinedload(Program.classroom),
            joinedload(Program.lessons)
            .joinedload(Lesson.contents)
            .joinedload(Content.content_items),
        )
        .filter(Program.id == program_id, Program.is_active.is_(True))
        .first()
    )
    if not source_program:
        raise HTTPException(status_code=404, detail="Program not found")

    source_metadata = {}
    source_type = None
    source_scope = None

    if source_program.organization_id:
        source_scope = "organization"
    elif source_program.school_id:
        source_scope = "school"
    elif source_program.classroom_id:
        source_scope = "classroom"
    elif source_program.is_template:
        source_scope = "teacher"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported program scope for copy",
        )

    if source_scope == "organization":
        if not has_manage_materials_permission(
            current_teacher.id, source_program.organization_id, db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access organization materials",
            )

        organization = (
            db.query(Organization)
            .filter(Organization.id == source_program.organization_id)
            .first()
        )
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")

        if payload.target_scope != "school":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization materials can only be copied to school",
            )

        source_type = "org_template"
        source_metadata = {
            "source_scope": "organization",
            "organization_id": str(organization.id),
            "organization_name": organization.display_name or organization.name,
            "program_id": source_program.id,
            "program_name": source_program.name,
        }
    elif source_scope == "school":
        if not _has_school_access(current_teacher.id, source_program.school_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access school materials",
            )

        if payload.target_scope not in ["teacher", "classroom"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="School materials can only be copied to teacher or classroom",
            )

        school = db.query(School).filter(School.id == source_program.school_id).first()
        if not school:
            raise HTTPException(status_code=404, detail="School not found")

        source_type = "school_template"
        source_metadata = {
            "source_scope": "school",
            "school_id": str(school.id),
            "school_name": school.display_name or school.name,
            "program_id": source_program.id,
            "program_name": source_program.name,
        }
    elif source_scope == "classroom":
        if source_program.classroom:
            if source_program.classroom.teacher_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Classroom has no assigned teacher",
                )
            if source_program.classroom.teacher_id != current_teacher.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to copy this classroom program",
                )

        if payload.target_scope not in ["teacher", "classroom"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Classroom programs can only be copied to teacher or classroom",
            )

        source_type = "classroom"
        source_metadata = {
            "source_scope": "classroom",
            "source_classroom_id": source_program.classroom_id,
            "source_classroom_name": source_program.classroom.name
            if source_program.classroom
            else None,
            "source_program_id": source_program.id,
            "source_program_name": source_program.name,
            "copied_at": datetime.now().isoformat(),
        }
    else:
        if source_program.teacher_id != current_teacher.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to copy this template",
            )

        if payload.target_scope == "school":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Teacher templates cannot be copied to school",
            )

        source_type = "template"
        source_metadata = {
            "source_scope": "teacher",
            "teacher_id": current_teacher.id,
            "template_id": source_program.id,
            "template_name": source_program.name,
            "copied_at": datetime.now().isoformat(),
        }

    if payload.name:
        new_name = payload.name
    elif source_type == "template":
        new_name = f"{source_program.name} (複製)"
    elif source_type == "classroom":
        source_classroom_name = (
            source_program.classroom.name if source_program.classroom else "班級"
        )
        new_name = f"{source_program.name} (從{source_classroom_name}複製)"
    else:
        new_name = source_program.name

    try:
        if payload.target_scope == "classroom":
            target_classroom = (
                db.query(Classroom).filter(Classroom.id == target_id_int).first()
            )
            if not target_classroom:
                raise HTTPException(status_code=404, detail="Classroom not found")

            if target_classroom.teacher_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Classroom has no assigned teacher",
                )
            if target_classroom.teacher_id != current_teacher.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You are not the teacher of this classroom",
                )

            new_program = program_service.copy_program_tree(
                source_program=source_program,
                target_classroom=target_classroom,
                target_teacher_id=current_teacher.id,
                db=db,
                source_type=source_type,
                source_metadata=source_metadata,
                name=new_name,
            )
        elif payload.target_scope == "teacher":
            if target_id_int != current_teacher.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot copy to another teacher",
                )

            new_program = program_service.copy_program_tree_to_template(
                source_program=source_program,
                target_teacher_id=current_teacher.id,
                target_school_id=None,
                db=db,
                source_type=source_type,
                source_metadata=source_metadata,
                name=new_name,
            )
        else:
            target_school = (
                db.query(School).filter(School.id == target_school_id).first()
            )
            if not target_school:
                raise HTTPException(status_code=404, detail="School not found")

            if not _has_school_manage_permission(
                current_teacher.id, target_school.id, db
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No permission to manage school materials",
                )

            if source_scope == "organization":
                if target_school.organization_id != source_program.organization_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="School does not belong to source organization",
                    )

            new_program = program_service.copy_program_tree_to_template(
                source_program=source_program,
                target_teacher_id=current_teacher.id,
                target_school_id=target_school.id,
                db=db,
                source_type=source_type,
                source_metadata=source_metadata,
                name=new_name,
            )
        db.commit()
        db.refresh(new_program)

        new_program = (
            db.query(Program)
            .options(
                joinedload(Program.lessons)
                .joinedload(Lesson.contents)
                .joinedload(Content.content_items)
            )
            .filter(Program.id == new_program.id)
            .first()
        )
    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to copy program {program_id} to classroom {payload.target_id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to copy program. Please try again later.",
        )

    program_data = ProgramResponse.from_orm(new_program)
    program_data.lessons = []

    for lesson in sorted(new_program.lessons, key=lambda x: x.order_index):
        lesson_data = {
            "id": lesson.id,
            "program_id": lesson.program_id,
            "name": lesson.name,
            "description": lesson.description,
            "order_index": lesson.order_index,
            "is_active": lesson.is_active,
            "contents": [],
        }

        for content in sorted(lesson.contents, key=lambda x: x.order_index):
            content_data = {
                "id": content.id,
                "lesson_id": content.lesson_id,
                "type": content.type,
                "title": content.title,
                "order_index": content.order_index,
                "is_active": content.is_active,
                "items": [
                    {
                        "id": item.id,
                        "content_id": item.content_id,
                        "order_index": item.order_index,
                        "text": item.text,
                        "translation": item.translation,
                        "audio_url": item.audio_url,
                    }
                    for item in sorted(
                        content.content_items, key=lambda x: x.order_index
                    )
                ],
            }
            lesson_data["contents"].append(content_data)

        program_data.lessons.append(lesson_data)

    return program_data


@router.post("", response_model=ProgramResponse, status_code=201)
async def create_program(
    payload: ProgramCreate,
    scope: Literal["teacher", "organization", "school"] = Query(
        ..., description="Scope: teacher, organization, or school"
    ),
    organization_id: str = Query(None, description="Required if scope=organization"),
    school_id: str = Query(None, description="Required if scope=school"),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Create program.

    - scope=teacher: Creates personal program for teacher
    - scope=organization: Creates organization program (requires organization_id and permission)
    - scope=school: Creates school program (requires school_id and permission)
    """
    # Validate parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="organization_id is required when scope=organization",
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="school_id is required when scope=school",
        )

    try:
        import uuid as uuid_module

        org_uuid = uuid_module.UUID(organization_id) if organization_id else None
        sch_uuid = uuid_module.UUID(school_id) if school_id else None
        program = program_service.create_program(
            scope=scope,
            teacher_id=current_teacher.id,
            data={"name": payload.name, "description": payload.description},
            db=db,
            organization_id=org_uuid,
            school_id=sch_uuid,
        )

        return ProgramResponse.from_orm(program)

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: int,
    payload: ProgramUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Update program.

    Automatically checks program ownership and permissions via service layer.
    """
    try:
        program = program_service.update_program(
            program_id=program_id,
            teacher_id=current_teacher.id,
            data={"name": payload.name, "description": payload.description},
            db=db,
        )

        return ProgramResponse.from_orm(program)

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Lesson endpoints
@router.post("/{program_id}/lessons", status_code=201)
async def create_lesson(
    program_id: int,
    payload: LessonCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Create lesson in program.

    Automatically checks program permission (works for both teacher and org programs).
    """
    import logging

    logger = logging.getLogger(__name__)

    logger.info(
        "[CREATE_LESSON_ENDPOINT] Called with program_id=%s teacher_id=%s lesson_name=%s",
        program_id,
        current_teacher.id,
        payload.name,
    )

    try:
        lesson = program_service.create_lesson(
            program_id=program_id,
            teacher_id=current_teacher.id,
            data=payload.dict(),
            db=db,
        )

        logger.info(
            "[CREATE_LESSON_ENDPOINT] Service returned lesson_id=%s name=%s",
            lesson.id,
            lesson.name,
        )

        # Double-check: Count lessons with same name in this program
        from models import Lesson

        duplicate_count = (
            db.query(Lesson)
            .filter(
                Lesson.program_id == program_id,
                Lesson.name == lesson.name,
                Lesson.is_active.is_(True),
            )
            .count()
        )
        logger.info(
            "[CREATE_LESSON_ENDPOINT] Duplicate check: %s lessons found in program %s",
            duplicate_count,
            program_id,
        )

        response = {
            "id": lesson.id,
            "program_id": lesson.program_id,
            "name": lesson.name,
            "description": lesson.description,
            "order_index": lesson.order_index,
            "is_active": lesson.is_active,
        }

        logger.info(
            "[CREATE_LESSON_ENDPOINT] Returning response for lesson_id=%s", lesson.id
        )
        return response

    except PermissionError as e:
        logger.error("[CREATE_LESSON_ENDPOINT] PermissionError: %s", str(e))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.error("[CREATE_LESSON_ENDPOINT] ValueError: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/lessons/{lesson_id}", response_model=LessonResponse)
async def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Update lesson.

    Automatically checks lesson->program permission chain.
    """
    try:
        # Convert payload to dict, excluding unset fields
        data = payload.dict(exclude_unset=True)

        lesson = program_service.update_lesson(
            lesson_id=lesson_id,
            teacher_id=current_teacher.id,
            data=data,
            db=db,
        )

        return LessonResponse.from_orm(lesson)

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/lessons/{lesson_id}")
async def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Soft delete lesson.

    Automatically checks lesson->program permission chain.
    """
    try:
        result = program_service.delete_lesson(
            lesson_id=lesson_id,
            teacher_id=current_teacher.id,
            db=db,
        )

        return result

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# Content endpoints
@router.post("/lessons/{lesson_id}/contents", status_code=201)
async def create_content(
    lesson_id: int,
    payload: ContentCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Create content in lesson.

    Automatically checks lesson->program permission chain.
    """
    logger.info(
        "[CREATE_CONTENT_ENDPOINT] Called with lesson_id=%s teacher_id=%s type=%s",
        lesson_id,
        current_teacher.id,
        payload.type,
    )
    try:
        content = program_service.create_content(
            lesson_id=lesson_id,
            teacher_id=current_teacher.id,
            data=payload.dict(),
            db=db,
        )
        logger.info(
            "[CREATE_CONTENT_ENDPOINT] Content created successfully: id=%s", content.id
        )

        return {
            "id": content.id,
            "lesson_id": content.lesson_id,
            "type": content.type,
            "title": content.title,
            "order_index": content.order_index,
            "is_active": content.is_active,
        }

    except PermissionError as e:
        logger.error(
            "Permission denied creating content in lesson %s: %s", lesson_id, e
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        logger.error("Invalid data creating content in lesson %s: %s", lesson_id, e)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("Database error creating content in lesson %s: %s", lesson_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
    except Exception as e:
        logger.error("Unexpected error creating content in lesson %s: %s", lesson_id, e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        )


@router.delete("/contents/{content_id}")
async def delete_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Unified API: Soft delete content.

    Automatically checks content->lesson->program permission chain.
    """
    try:
        result = program_service.delete_content(
            content_id=content_id,
            teacher_id=current_teacher.id,
            db=db,
        )

        return result

    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ============================================================================
# Reorder Endpoints (Scope-Aware)
# ============================================================================


@router.put("/reorder")
async def reorder_programs(
    order_data: List[dict],
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Reorder programs based on scope.

    - scope=teacher: Reorder teacher's personal programs
    - scope=organization: Reorder organization programs (requires organization_id)
    - scope=school: Reorder school programs (requires school_id)
    """
    # Validate required parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required when scope=organization",
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="school_id is required when scope=school",
        )

    # Build query based on scope
    query = db.query(Program).filter(Program.is_template.is_(True))

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.organization_id.is_(None),
            Program.school_id.is_(None),
            Program.classroom_id.is_(None),
        )
    elif scope == "organization":
        try:
            org_uuid = uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization_id format",
            )
        if not has_manage_materials_permission(current_teacher.id, org_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder organization materials",
            )
        # Organization programs don't have teacher_id (they are NULL)
        query = query.filter(Program.organization_id == org_uuid)
    elif scope == "school":
        try:
            sch_uuid = uuid.UUID(school_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid school_id format",
            )
        if not has_school_materials_permission(current_teacher.id, sch_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder school materials",
            )
        # School programs don't have teacher_id (they are NULL)
        query = query.filter(Program.school_id == sch_uuid)

    # Get all programs in scope
    programs = query.all()
    program_dict = {str(p.id): p for p in programs}

    # Update order_index
    for item in order_data:
        program_id = str(item.get("id"))
        new_order = item.get("order_index")

        if program_id in program_dict:
            program_dict[program_id].order_index = new_order

    db.commit()

    return {"message": "Programs reordered successfully"}


@router.put("/{program_id}/lessons/reorder")
async def reorder_lessons(
    program_id: int,
    order_data: List[dict],
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Reorder lessons within a program (scope-aware)"""
    # Validate required parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required when scope=organization",
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="school_id is required when scope=school",
        )

    # Verify program exists and matches scope
    query = db.query(Program).filter(Program.id == program_id)

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.is_template.is_(True),
            Program.classroom_id.is_(None),
            Program.organization_id.is_(None),
            Program.school_id.is_(None),
        )
    elif scope == "organization":
        try:
            org_uuid = uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization_id format",
            )
        if not has_manage_materials_permission(current_teacher.id, org_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder organization materials",
            )
        # Organization programs don't have teacher_id (they are NULL)
        query = query.filter(Program.organization_id == org_uuid)
    elif scope == "school":
        try:
            sch_uuid = uuid.UUID(school_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid school_id format",
            )
        if not has_school_materials_permission(current_teacher.id, sch_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder school materials",
            )
        # School programs don't have teacher_id (they are NULL)
        query = query.filter(Program.school_id == sch_uuid)

    program = query.first()
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")

    # Reorder lessons
    lesson_ids = [item["id"] for item in order_data]
    lessons_list = (
        db.query(Lesson)
        .filter(Lesson.id.in_(lesson_ids), Lesson.program_id == program_id)
        .all()
    )

    lessons_dict = {lesson.id: lesson for lesson in lessons_list}

    for item in order_data:
        lesson = lessons_dict.get(item["id"])
        if lesson:
            lesson.order_index = item["order_index"]

    db.commit()

    return {"message": "Lessons reordered successfully"}


@router.put("/lessons/{lesson_id}/contents/reorder")
async def reorder_contents(
    lesson_id: int,
    order_data: List[dict],
    scope: Literal["teacher", "organization", "school"] = Query(...),
    organization_id: str = Query(None),
    school_id: str = Query(None),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """Reorder contents within a lesson (scope-aware)"""
    # Validate required parameters
    if scope == "organization" and not organization_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is required when scope=organization",
        )
    if scope == "school" and not school_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="school_id is required when scope=school",
        )

    # Verify lesson's program matches scope
    query = db.query(Lesson).join(Program).filter(Lesson.id == lesson_id)

    if scope == "teacher":
        query = query.filter(
            Program.teacher_id == current_teacher.id,
            Program.is_template.is_(True),
            Program.classroom_id.is_(None),
            Program.organization_id.is_(None),
            Program.school_id.is_(None),
        )
    elif scope == "organization":
        try:
            org_uuid = uuid.UUID(organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid organization_id format",
            )
        if not has_manage_materials_permission(current_teacher.id, org_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder organization materials",
            )
        # Organization programs don't have teacher_id (they are NULL)
        query = query.filter(Program.organization_id == org_uuid)
    elif scope == "school":
        try:
            sch_uuid = uuid.UUID(school_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid school_id format",
            )
        if not has_school_materials_permission(current_teacher.id, sch_uuid, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to reorder school materials",
            )
        # School programs don't have teacher_id (they are NULL)
        query = query.filter(Program.school_id == sch_uuid)

    lesson = query.first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Reorder contents
    content_ids = [item["id"] for item in order_data]
    contents_list = (
        db.query(Content)
        .filter(Content.id.in_(content_ids), Content.lesson_id == lesson_id)
        .all()
    )

    contents_dict = {content.id: content for content in contents_list}

    for item in order_data:
        content = contents_dict.get(item["id"])
        if content:
            content.order_index = item["order_index"]

    db.commit()

    return {"message": "Contents reordered successfully"}
