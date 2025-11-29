"""Student account management endpoints (account switching, linking, email binding)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Student, Classroom, ClassroomStudent
from auth import get_current_user, create_access_token, verify_password
from .validators import SwitchAccountRequest

router = APIRouter()


@router.get("/{student_id}/linked-accounts")
async def get_linked_accounts(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """獲取相同已驗證 email 的其他學生帳號"""
    # 確認是學生本人
    if (
        current_user.get("type") != "student"
        or int(current_user.get("sub")) != student_id
    ):
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 檢查是否有已驗證的 email
    if not student.email or not student.email_verified:
        return {"linked_accounts": [], "message": "No verified email"}

    # 找出所有相同 email 且已驗證的學生帳號
    linked_students = (
        db.query(Student)
        .filter(
            Student.email == student.email,
            Student.email_verified is True,
            Student.id != student_id,  # 排除自己
            Student.is_active.is_(True),
        )
        .all()
    )

    # 優化：批次查詢所有 linked students 的 classroom 資訊（避免 N+1）
    linked_student_ids = [s.id for s in linked_students]

    # 批次查詢所有 ClassroomStudent 關係
    classroom_enrollments = (
        db.query(ClassroomStudent)
        .filter(
            ClassroomStudent.student_id.in_(linked_student_ids),
            ClassroomStudent.is_active.is_(True),
        )
        .all()
    )

    # 建立 student_id -> classroom_id 的索引
    student_classroom_map = {
        ce.student_id: ce.classroom_id for ce in classroom_enrollments
    }

    # 批次查詢所有 Classroom（包含 teacher 關係）
    classroom_ids = list(set(student_classroom_map.values()))

    classrooms = (
        db.query(Classroom)
        .options(joinedload(Classroom.teacher))  # eager load teacher
        .filter(Classroom.id.in_(classroom_ids))
        .all()
    )

    # 建立 classroom_id -> classroom 的索引
    classroom_map = {c.id: c for c in classrooms}

    # 建立回應，包含班級資訊
    linked_accounts = []
    for linked_student in linked_students:
        # 從預先載入的 map 取得 classroom 資訊（不再查詢資料庫）
        classroom_id = student_classroom_map.get(linked_student.id)
        classroom = classroom_map.get(classroom_id) if classroom_id else None

        classroom_info = None
        if classroom:
            classroom_info = {
                "id": classroom.id,
                "name": classroom.name,
                "teacher_name": (classroom.teacher.name if classroom.teacher else None),
            }

        linked_accounts.append(
            {
                "student_id": linked_student.id,
                "name": linked_student.name,
                "classroom": classroom_info,
                "last_login": (
                    linked_student.last_login.isoformat()
                    if linked_student.last_login
                    else None
                ),
            }
        )

    return {"linked_accounts": linked_accounts, "current_email": student.email}


@router.post("/switch-account")
async def switch_account(
    request: SwitchAccountRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """切換到另一個已連結的學生帳號"""
    # 確認是學生
    if current_user.get("type") != "student":
        raise HTTPException(status_code=403, detail="Only students can switch accounts")

    current_student_id = int(current_user.get("sub"))
    current_student = db.query(Student).filter(Student.id == current_student_id).first()

    if not current_student:
        raise HTTPException(status_code=404, detail="Current student not found")

    # 檢查當前帳號是否有已驗證的 email
    if not current_student.email or not current_student.email_verified:
        raise HTTPException(
            status_code=400, detail="Current account has no verified email"
        )

    # 查找目標學生
    target_student = (
        db.query(Student).filter(Student.id == request.target_student_id).first()
    )

    if not target_student:
        raise HTTPException(status_code=404, detail="Target student not found")

    # 檢查目標學生是否有相同的已驗證 email
    if (
        target_student.email != current_student.email
        or not target_student.email_verified
    ):
        raise HTTPException(status_code=403, detail="Target account is not linked")

    # 驗證目標帳號的密碼
    if not verify_password(request.password, target_student.password_hash):
        raise HTTPException(
            status_code=401, detail="Invalid password for target account"
        )

    # 更新最後登入時間
    target_student.last_login = datetime.now()
    db.commit()

    # 建立新的 JWT token
    access_token = create_access_token(
        data={"sub": str(target_student.id), "type": "student"},
        expires_delta=timedelta(minutes=30),
    )

    # 取得班級資訊
    classroom_enrollment = (
        db.query(ClassroomStudent)
        .filter(
            ClassroomStudent.student_id == target_student.id,
            ClassroomStudent.is_active.is_(True),
        )
        .first()
    )

    classroom_info = None
    if classroom_enrollment:
        classroom = (
            db.query(Classroom)
            .filter(Classroom.id == classroom_enrollment.classroom_id)
            .first()
        )
        if classroom:
            classroom_info = {"id": classroom.id, "name": classroom.name}

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "student": {
            "id": target_student.id,
            "name": target_student.name,
            "email": target_student.email,
            "classroom": classroom_info,
        },
        "message": "Successfully switched to target account",
    }


@router.delete("/{student_id}/email-binding")
async def unbind_email(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """解除 email 綁定（學生自己或老師都可以操作）"""
    # 檢查權限：學生本人或老師
    is_student_self = (
        current_user.get("type") == "student"
        and int(current_user.get("sub")) == student_id
    )
    is_teacher = current_user.get("type") == "teacher"

    if not is_student_self and not is_teacher:
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 如果是老師，檢查學生是否在老師的班級中
    if is_teacher:
        teacher_id = int(current_user.get("sub"))
        # 檢查學生是否在該老師的任何班級中
        student_in_teacher_class = (
            db.query(ClassroomStudent)
            .join(Classroom)
            .filter(
                ClassroomStudent.student_id == student_id,
                Classroom.teacher_id == teacher_id,
                ClassroomStudent.is_active.is_(True),
            )
            .first()
        )
        if not student_in_teacher_class:
            raise HTTPException(
                status_code=403, detail="Student is not in your classroom"
            )

    # 清除 email 綁定相關資訊
    old_email = student.email
    student.email = None
    student.email_verified = False
    student.email_verified_at = None
    student.email_verification_token = None
    student.email_verification_sent_at = None

    db.commit()

    return {
        "message": "Email binding removed successfully",
        "student_id": student_id,
        "old_email": old_email,
        "removed_by": "teacher" if is_teacher else "student",
    }
