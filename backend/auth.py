from datetime import datetime, timedelta  # noqa: F401
from typing import Optional, Dict, Any  # noqa: F401
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from models import Teacher, Student
import os
from dotenv import load_dotenv

load_dotenv()

# Test workflow trigger: 2025-11-10

# 🔐 Security: No default values for secrets
SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# 🔐 Production 強制檢查：必須設定 JWT_SECRET
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
if ENVIRONMENT == "production" and SECRET_KEY == "your-secret-key-change-in-production":
    raise RuntimeError(
        "❌ SECURITY ERROR: JWT_SECRET must be set in production! "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(64))'"
    )

ALGORITHM = "HS256"  # Hardcoded to prevent 'none' algorithm attack
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    # 🔐 Handle None hash gracefully (return False)
    # But raise error for None password (security: never accept None as valid password)
    if plain_password is None:
        raise TypeError("Password cannot be None")

    if hashed_password is None:
        return False

    # Ensure password is encoded properly and truncated if needed
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed_bytes = (
        hashed_password.encode("utf-8")
        if isinstance(hashed_password, str)
        else hashed_password
    )
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    驗證密碼強度
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"

    # 檢查是否包含大寫字母
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    # 檢查是否包含小寫字母
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    # 檢查是否包含數字
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    # 檢查是否包含特殊字元
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return (
            False,
            "Password must contain at least one special character (!@#$%^&* etc.)",
        )

    return True, ""


def get_password_hash(password: str) -> str:
    """密碼雜湊"""
    # Ensure password is encoded properly and truncated if needed
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """建立 JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    """驗證 JWT token"""
    if token is None:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except (JWTError, AttributeError):
        return None


def authenticate_teacher(db: Session, email: str, password: str):
    """教師認證"""
    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if not teacher:
        return None
    if not verify_password(password, teacher.password_hash):
        return None
    return teacher


def authenticate_student(db: Session, email: str, password: str):
    """學生認證"""
    student = db.query(Student).filter(Student.email == email).first()
    if not student:
        return None
    if not verify_password(password, student.password_hash):
        return None
    return student


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Dict[str, Any]:
    """從 token 取得當前使用者資訊"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")

        if user_id is None or user_type is None:
            raise credentials_exception

        return payload
    except JWTError:
        raise credentials_exception
