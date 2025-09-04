from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from database import get_db
from models import Teacher, Student
from auth import verify_password, create_access_token, get_password_hash
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Request/Response Models ============
class TeacherLoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TeacherRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


# ============ Teacher Authentication ============
@router.post("/teacher/login", response_model=TokenResponse)
async def teacher_login(request: TeacherLoginRequest, db: Session = Depends(get_db)):
    """教師登入"""
    teacher = db.query(Teacher).filter(Teacher.email == request.email).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Email not found"
        )

    if not verify_password(request.password, teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )

    if not teacher.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    # Create token
    access_token = create_access_token(
        data={
            "sub": str(teacher.id),
            "email": teacher.email,
            "type": "teacher",
            "name": teacher.name,
        },
        expires_delta=timedelta(hours=24),  # 24 hours for development
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": teacher.id,
            "email": teacher.email,
            "name": teacher.name,
            "is_demo": teacher.is_demo,
        },
    }


@router.post("/teacher/register", response_model=TokenResponse)
async def teacher_register(
    request: TeacherRegisterRequest, db: Session = Depends(get_db)
):
    """教師註冊"""
    # Check if email exists
    existing = db.query(Teacher).filter(Teacher.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    # Create new teacher
    new_teacher = Teacher(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        phone=request.phone,
        is_active=True,
        is_demo=False,
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    # Auto login after registration
    access_token = create_access_token(
        data={
            "sub": str(new_teacher.id),
            "email": new_teacher.email,
            "type": "teacher",
            "name": new_teacher.name,
        },
        expires_delta=timedelta(hours=24),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": new_teacher.id,
            "email": new_teacher.email,
            "name": new_teacher.name,
            "is_demo": False,
        },
    }


# ============ Student Authentication ============
@router.post("/student/login", response_model=TokenResponse)
async def student_login(request: StudentLoginRequest, db: Session = Depends(get_db)):
    """學生登入"""
    student = db.query(Student).filter(Student.email == request.email).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # 驗證密碼
    if not verify_password(request.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )

    # 創建 JWT token
    access_token = create_access_token(
        data={
            "sub": str(student.id),
            "email": student.email,
            "type": "student",
            "name": student.name,
            "student_id": student.student_id,
        },
        expires_delta=timedelta(hours=24),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": student.id,
            "email": student.email,
            "name": student.name,
            "student_id": student.student_id,
        },
    }


@router.get("/me")
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """取得當前登入的使用者資訊"""
    from auth import verify_token

    # 解碼 token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 取得使用者類型和 ID
    user_id = payload.get("sub")
    user_type = payload.get("type")

    if not user_id or not user_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    # 根據類型取得使用者
    if user_type == "teacher":
        user = db.query(Teacher).filter(Teacher.id == int(user_id)).first()
    elif user_type == "student":
        user = db.query(Student).filter(Student.id == int(user_id)).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user type"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


@router.get("/validate")
async def validate_token():
    """驗證 API 是否正常運作"""
    return {"status": "auth endpoint working", "version": "1.0.0"}
