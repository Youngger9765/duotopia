"""
課程管理 API - 支援公版模板和班級課程
"""

from datetime import datetime  # noqa: F401
from typing import List  # noqa: F401
from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload, selectinload

from database import get_db
from models import Program, Lesson, Teacher, Classroom, Content, ContentItem
from schemas import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramCopyFromTemplate,
    ProgramCopyFromClassroom,
)
from auth import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")

router = APIRouter(prefix="/api/programs", tags=["programs"])


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

    return programs


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
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """取得教師班級的課程（只顯示班級課程，不含公版模板），並標記重複狀態"""
    # 只取得班級課程 - 使用 joinedload 來載入 classroom 關聯

    classroom_programs = (
        db.query(Program)
        .options(joinedload(Program.classroom))
        .join(Classroom)
        .filter(
            Program.is_template.is_(False),
            Classroom.teacher_id == current_teacher.id,
            Program.is_active.is_(True),
        )
        .all()
    )

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
    program.deleted_at = datetime.now()

    db.commit()

    return {"message": "Program deleted successfully"}
