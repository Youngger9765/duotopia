"""Admin routes for seeding and managing the database."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
import os
import subprocess
import sys

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/seed-database")
async def seed_database(db: Session = Depends(get_db)):
    """Seed the database with initial data."""
    # 檢查是否在 staging 環境
    if os.getenv("ENVIRONMENT") != "staging":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed operation only allowed in staging environment",
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
