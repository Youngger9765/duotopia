"""Admin routes for seeding and managing the database."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from database import get_db
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    Program,
    Lesson,
    Content,
    Assignment,
    StudentAssignment,
)
import os
import subprocess
import sys

router = APIRouter(prefix="/api/admin", tags=["admin"])


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
        "assignment": db.query(Assignment).count(),
        "student_assignment": db.query(StudentAssignment).count(),
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
        "assignment": Assignment,
        "student_assignment": StudentAssignment,
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
