"""Admin routes for seeding and managing the database."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db, engine, Base
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    ContentItem,
    Assignment,
    StudentAssignment,
    StudentContentProgress,
    StudentItemProgress,
)
import os
import subprocess
import sys

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/database/rebuild")
async def rebuild_database(seed: bool = True, db: Session = Depends(get_db)):
    """重建資料庫 - 刪除所有表格並重新創建"""
    # 檢查是否在允許的環境 (development 或 staging)
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rebuild operation not allowed in production environment",
        )

    try:
        # 關閉當前 session
        db.close()

        # Drop all tables
        Base.metadata.drop_all(bind=engine)

        # Recreate all tables
        Base.metadata.create_all(bind=engine)

        result = {
            "success": True,
            "message": "Database rebuilt successfully",
            "tables_created": list(Base.metadata.tables.keys()),
        }

        # 如果需要 seed
        if seed:
            try:
                seed_result = subprocess.run(
                    [sys.executable, "seed_data.py"],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if seed_result.returncode == 0:
                    result["seed_status"] = "success"
                    result["seed_output"] = seed_result.stdout
                else:
                    result["seed_status"] = "failed"
                    result["seed_error"] = seed_result.stderr
            except Exception as e:
                result["seed_status"] = "error"
                result["seed_error"] = str(e)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Rebuild operation failed: {str(e)}",
        )


@router.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    """Seed the database with initial data."""
    # 檢查是否在允許的環境 (development 或 staging)
    env = os.getenv("ENVIRONMENT", "development")  # 預設為 development
    if env == "production":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed operation not allowed in production environment",
        )

    try:
        # 執行 seed_data.py
        result = subprocess.run(
            [sys.executable, "seed_data.py"],
            capture_output=True,
            text=True,
            timeout=300,  # 5分鐘超時
        )

        if result.returncode != 0:
            return {
                "success": False,
                "message": "Seed failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        return {
            "success": True,
            "message": "Database seeded successfully",
            "output": result.stdout,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Seed operation timed out",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Seed operation failed: {str(e)}",
        )


@router.get("/database/stats")
def get_database_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """獲取資料庫統計資訊"""

    stats = {
        "teacher": db.query(Teacher).count(),
        "student": db.query(Student).count(),
        "classroom": db.query(Classroom).count(),
        "classroom_student": db.query(ClassroomStudent).count(),
        "program": db.query(Program).count(),
        "lesson": db.query(Lesson).count(),
        "content": db.query(Content).count(),
        "content_item": db.query(ContentItem).count(),
        "assignment": db.query(Assignment).count(),
        "student_assignment": db.query(StudentAssignment).count(),
        "student_content_progress": db.query(StudentContentProgress).count(),
        "student_item_progress": db.query(StudentItemProgress).count(),
    }

    total_records = sum(stats.values())

    return {"entities": stats, "total_records": total_records}


@router.get("/database/entity/{entity_type}")
def get_entity_data(
    entity_type: str, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
):
    """查詢特定 entity 的資料"""

    entity_map = {
        "teacher": Teacher,
        "student": Student,
        "classroom": Classroom,
        "classroom_student": ClassroomStudent,
        "program": Program,
        "lesson": Lesson,
        "content": Content,
        "content_item": ContentItem,
        "assignment": Assignment,
        "student_assignment": StudentAssignment,
        "student_content_progress": StudentContentProgress,
        "student_item_progress": StudentItemProgress,
    }

    if entity_type not in entity_map:
        raise HTTPException(
            status_code=404, detail=f"Entity type '{entity_type}' not found"
        )

    model = entity_map[entity_type]

    # 獲取資料
    query = db.query(model).offset(offset).limit(limit)
    items = query.all()
    total = db.query(model).count()

    # 轉換為字典格式
    data = []
    for item in items:
        item_dict = {}
        for column in model.__table__.columns:
            value = getattr(item, column.name)
            # 處理日期時間格式
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            item_dict[column.name] = value
        data.append(item_dict)

    return {
        "data": data,
        "total": total,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
        },
    }
