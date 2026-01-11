"""
Shared dependencies for teachers routers.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
from models import Teacher
from auth import verify_token
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


async def get_current_teacher(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """取得當前登入的教師"""
    logger = logging.getLogger(__name__)

    # 🔍 診斷 logging
    logger.info("🔍 get_current_teacher called")
    logger.info(f"🔍 Token received: {token[:30] if token else 'None'}...")

    payload = verify_token(token)
    logger.info(f"🔍 Token verification result: {payload}")

    if not payload:
        logger.error(
            f"❌ Token verification failed! Token: {token[:30] if token else 'None'}..."
        )
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
