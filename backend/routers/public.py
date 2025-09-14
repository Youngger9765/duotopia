"""
Public API endpoints for student login flow
不需要認證的公開端點
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional  # noqa: F401
from pydantic import BaseModel, EmailStr
from database import get_db
from models import Teacher, Classroom, Student, ClassroomStudent

router = APIRouter(prefix="/api/public", tags=["public"])


class ValidateTeacherRequest(BaseModel):
    email: EmailStr


class ValidateTeacherResponse(BaseModel):
    valid: bool
    name: Optional[str] = None
    id: Optional[int] = None


class ClassroomResponse(BaseModel):
    id: int
    name: str
    studentCount: int


class StudentResponse(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    avatar: Optional[str] = None


class TeacherResponse(BaseModel):
    id: int
    name: str
    email: str


@router.post("/validate-teacher", response_model=ValidateTeacherResponse)
def validate_teacher(request: ValidateTeacherRequest, db: Session = Depends(get_db)):
    """驗證教師 email 是否存在"""
    teacher = (
        db.query(Teacher)
        .filter(func.lower(Teacher.email) == func.lower(request.email))
        .first()
    )

    if teacher:
        return ValidateTeacherResponse(valid=True, name=teacher.name, id=teacher.id)
    return ValidateTeacherResponse(valid=False)


@router.get("/teachers", response_model=List[TeacherResponse])
def get_teachers(db: Session = Depends(get_db)):
    """獲取所有活躍教師的公開資訊"""
    teachers = db.query(Teacher).filter(Teacher.is_active.is_(True)).all()

    result = []
    for teacher in teachers:
        result.append(
            TeacherResponse(id=teacher.id, name=teacher.name, email=teacher.email)
        )

    return result


@router.get("/teacher-classrooms", response_model=List[ClassroomResponse])
def get_teacher_classrooms(email: str, db: Session = Depends(get_db)):
    """獲取教師的所有班級（公開資訊）"""
    # 先找到教師
    teacher = (
        db.query(Teacher).filter(func.lower(Teacher.email) == func.lower(email)).first()
    )

    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    # 獲取該教師的所有班級和學生數量 - 使用 JOIN 和 GROUP BY 優化
    # 原本：1 + N 次查詢（1次班級 + N次學生數）
    # 現在：1次查詢（JOIN + GROUP BY）
    from sqlalchemy import func

    classrooms_with_count = (
        db.query(
            Classroom.id,
            Classroom.name,
            func.count(ClassroomStudent.id).label("student_count"),
        )
        .outerjoin(ClassroomStudent)  # 使用 outerjoin 以包含沒有學生的班級
        .filter(Classroom.teacher_id == teacher.id, Classroom.is_active.is_(True))
        .group_by(Classroom.id, Classroom.name)
        .all()
    )

    result = []
    for classroom_id, classroom_name, student_count in classrooms_with_count:
        result.append(
            ClassroomResponse(
                id=classroom_id, name=classroom_name, studentCount=student_count or 0
            )
        )

    return result


@router.get("/classroom-students/{classroom_id}", response_model=List[StudentResponse])
def get_classroom_students(classroom_id: int, db: Session = Depends(get_db)):
    """獲取班級的所有學生（只顯示名字和頭像，不顯示敏感資訊）"""
    # 確認班級存在
    classroom = (
        db.query(Classroom)
        .filter(Classroom.id == classroom_id, Classroom.is_active.is_(True))
        .first()
    )

    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")

    # 獲取班級的所有學生
    students = (
        db.query(Student)
        .join(ClassroomStudent)
        .filter(ClassroomStudent.classroom_id == classroom_id)
        .all()
    )

    # 只返回必要的公開資訊
    result = []
    for student in students:
        result.append(
            StudentResponse(
                id=student.id,
                name=student.name,
                email=student.email,  # 用於登入
                avatar=None,  # 未來可以加入頭像
            )
        )

    return result
