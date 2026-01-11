"""
Profile Ops operations for teachers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload, joinedload
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import Teacher, Classroom, Student, Program, Lesson, Content, ContentItem
from models import ClassroomStudent, Assignment, AssignmentContent
from models import (
    ProgramLevel,
    TeacherOrganization,
    TeacherSchool,
    Organization,
    School,
)
from .dependencies import get_current_teacher
from .validators import *
from .utils import TEST_SUBSCRIPTION_WHITELIST, parse_birthdate
from auth import verify_password, get_password_hash, validate_password_strength

router = APIRouter()


@router.get("/me", response_model=TeacherProfile)
async def get_teacher_profile(current_teacher: Teacher = Depends(get_current_teacher)):
    """取得教師個人資料"""
    return current_teacher


@router.get("/me/roles", response_model=TeacherRolesResponse)
async def get_teacher_roles(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    取得教師在所有機構和學校的角色

    Returns:
        - organization_roles: 機構層級的角色 (org_owner, org_admin)
        - school_roles: 學校層級的角色 (school_admin, teacher)
        - all_roles: 所有角色的扁平化列表
    """

    organization_roles = []
    school_roles = []
    all_roles_set = set()

    # 查詢機構角色
    teacher_orgs = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == current_teacher.id,
            TeacherOrganization.is_active.is_(True),
        )
        .all()
    )

    for to in teacher_orgs:
        org = (
            db.query(Organization).filter(Organization.id == to.organization_id).first()
        )
        if org and org.is_active:
            organization_roles.append(
                OrganizationRole(
                    organization_id=str(to.organization_id),
                    organization_name=org.display_name or org.name,
                    role=to.role,
                )
            )
            all_roles_set.add(to.role)

    # 查詢學校角色
    teacher_schools = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == current_teacher.id,
            TeacherSchool.is_active.is_(True),
        )
        .all()
    )

    for ts in teacher_schools:
        school = db.query(School).filter(School.id == ts.school_id).first()
        if school and school.is_active:
            org = (
                db.query(Organization)
                .filter(Organization.id == school.organization_id)
                .first()
            )
            if org:
                school_roles.append(
                    SchoolRole(
                        school_id=str(ts.school_id),
                        school_name=school.display_name or school.name,
                        organization_id=str(school.organization_id),
                        organization_name=org.display_name or org.name,
                        roles=ts.roles if ts.roles else [],
                    )
                )
                # 將學校角色加入 all_roles
                if ts.roles:
                    all_roles_set.update(ts.roles)

    return TeacherRolesResponse(
        teacher_id=current_teacher.id,
        organization_roles=organization_roles,
        school_roles=school_roles,
        all_roles=sorted(list(all_roles_set)),
    )


@router.put("/me", response_model=TeacherProfile)
async def update_teacher_profile(
    request: UpdateTeacherProfileRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """更新教師個人資料"""
    if request.name is not None:
        current_teacher.name = request.name
    if request.phone is not None:
        current_teacher.phone = request.phone

    db.commit()
    db.refresh(current_teacher)
    return current_teacher


@router.put("/me/password")
async def update_teacher_password(
    request: UpdatePasswordRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """更新教師密碼"""
    # Verify current password
    if not verify_password(request.current_password, current_teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Check if new password is same as current password
    if verify_password(request.new_password, current_teacher.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    # Validate new password strength (same as registration)
    is_valid, error_msg = validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Update password
    current_teacher.password_hash = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password updated successfully"}
