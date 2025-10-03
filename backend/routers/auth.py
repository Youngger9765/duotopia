from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional  # noqa: F401
from pydantic import BaseModel, EmailStr
from database import get_db
from models import Teacher, Student
from auth import verify_password, create_access_token, get_password_hash, verify_token
from services.email_service import email_service
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Request/Response Models ============
class TeacherLoginRequest(BaseModel):
    email: EmailStr
    password: str


class StudentLoginRequest(BaseModel):
    id: int  # 學生資料庫主鍵 ID
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


class RegisterResponse(BaseModel):
    message: str
    email: str
    verification_required: bool


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
        # 檢查是否是因為 email 未驗證
        if not teacher.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in. Check your inbox for verification link.",
            )
        else:
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


@router.post("/teacher/register", response_model=RegisterResponse)
async def teacher_register(
    request: TeacherRegisterRequest, db: Session = Depends(get_db)
):
    """教師註冊"""
    # Check if email exists
    existing = db.query(Teacher).filter(Teacher.email == request.email).first()
    if existing:
        # 如果已經驗證，不允許重複註冊
        if existing.email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified",
            )
        else:
            # 如果未驗證，刪除舊的未驗證帳號，允許重新註冊
            db.delete(existing)
            db.commit()

    # Create new teacher (未啟用，需要 email 驗證)
    new_teacher = Teacher(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        phone=request.phone,
        is_active=False,  # 🔴 未啟用，需要 email 驗證
        is_demo=False,
        email_verified=False,  # 🔴 未驗證 email
        # subscription_end_date 留空，驗證後才設定
    )

    db.add(new_teacher)
    db.commit()
    db.refresh(new_teacher)

    # 🎯 發送驗證 email
    email_sent = email_service.send_teacher_verification_email(db, new_teacher)

    if not email_sent:
        # 如果發送失敗，仍然創建帳號但給予警告
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration successful but verification email failed to send. Please contact support.",
        )

    # 🔴 不再自動登入，需要先驗證 email
    return {
        "message": "Registration successful! Please check your email to verify your account.",
        "email": new_teacher.email,
        "verification_required": True,
    }


# ============ Email 驗證 ============
@router.get("/verify-teacher")
async def verify_teacher_email(token: str, db: Session = Depends(get_db)):
    """驗證教師 email 並啟動 30 天訂閱"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token is required",
        )

    # 驗證 token 並啟動訂閱
    teacher = email_service.verify_teacher_email_token(db, token)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    # 不自動登入，只返回驗證成功訊息
    return {
        "status": "success",
        "message": "Email verified successfully! Your 30-day free trial has started.",
        "user": {
            "id": teacher.id,
            "email": teacher.email,
            "name": teacher.name,
            "email_verified": True,
            "subscription_status": teacher.subscription_status,
            "days_remaining": teacher.days_remaining,
        },
    }


@router.post("/resend-verification")
async def resend_verification_email(request: dict, db: Session = Depends(get_db)):
    """重新發送驗證 email"""
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is required"
        )

    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    if teacher.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
        )

    success = email_service.resend_teacher_verification_email(db, teacher)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another verification email",
        )

    return {"message": "Verification email sent successfully"}


# ============ Student Authentication ============
@router.post("/student/login", response_model=TokenResponse)
async def student_login(request: StudentLoginRequest, db: Session = Depends(get_db)):
    """學生登入"""
    student = db.query(Student).filter(Student.id == request.id).first()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Student not found"
        )

    # 驗證密碼
    if not verify_password(request.password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password"
        )

    # 創建 JWT token
    access_token = create_access_token(
        data={
            "sub": str(student.id),
            "email": student.email,
            "type": "student",
            "name": student.name,
            "student_number": student.student_number,
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
            "student_number": student.student_number,
        },
    }


@router.get("/me")
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """取得當前登入的使用者資訊"""
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


# ========== 密碼重設功能 ==========


@router.post("/teacher/forgot-password")
async def forgot_password(
    email: str = Body(..., embed=True), db: Session = Depends(get_db)
):
    """教師忘記密碼 - 發送重設郵件"""
    # 查找教師
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    # 不論是否找到都返回相同訊息（安全性考量）
    if not teacher:
        return {"message": "如果該電子郵件存在，我們已發送密碼重設連結", "success": True}

    # 檢查是否已驗證 email
    if not teacher.email_verified:
        return {"message": "如果該電子郵件存在，我們已發送密碼重設連結", "success": True}

    # 檢查發送頻率限制（5分鐘內不能重複發送）
    if teacher.password_reset_sent_at:
        # 確保兩個時間都是 naive 或都是 aware
        current_time = datetime.utcnow()
        reset_time = teacher.password_reset_sent_at
        # 如果 reset_time 是 aware，轉換為 naive
        if reset_time.tzinfo is not None:
            reset_time = reset_time.replace(tzinfo=None)

        time_diff = current_time - reset_time
        if time_diff < timedelta(minutes=5):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="請稍後再試，密碼重設郵件每5分鐘只能發送一次",
            )

    # 發送密碼重設郵件
    success = email_service.send_password_reset_email(db, teacher)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="發送郵件失敗，請稍後再試"
        )

    return {"message": "如果該電子郵件存在，我們已發送密碼重設連結", "success": True}


@router.post("/teacher/reset-password")
async def reset_password(
    token: str = Body(...), new_password: str = Body(...), db: Session = Depends(get_db)
):
    """使用 token 重設密碼"""
    # 查找擁有此 token 的教師
    teacher = db.query(Teacher).filter(Teacher.password_reset_token == token).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="無效或過期的重設連結"
        )

    # 檢查 token 是否過期
    if teacher.password_reset_expires_at:
        current_time = datetime.utcnow()
        expires_at = teacher.password_reset_expires_at
        # 如果 expires_at 是 aware，轉換為 naive
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        if current_time > expires_at:
            # 清除過期的 token
            teacher.password_reset_token = None
            teacher.password_reset_expires_at = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="重設連結已過期，請重新申請"
            )

    # 驗證密碼強度
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="密碼至少需要6個字元"
        )

    # 更新密碼
    teacher.password_hash = get_password_hash(new_password)

    # 清除 token
    teacher.password_reset_token = None
    teacher.password_reset_sent_at = None
    teacher.password_reset_expires_at = None

    db.commit()

    return {"message": "密碼已成功重設", "success": True}


@router.get("/teacher/verify-reset-token")
async def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """驗證密碼重設 token 是否有效"""

    # 查找擁有此 token 的教師
    teacher = db.query(Teacher).filter(Teacher.password_reset_token == token).first()

    if not teacher:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無效的重設連結")

    # 檢查 token 是否過期
    if teacher.password_reset_expires_at:
        current_time = datetime.utcnow()
        expires_at = teacher.password_reset_expires_at
        # 如果 expires_at 是 aware，轉換為 naive
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)

        if current_time > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="重設連結已過期"
            )

    return {"valid": True, "email": teacher.email, "name": teacher.name}
