"""
Dashboard operations for teachers.
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

router = APIRouter()


@router.get("/dashboard", response_model=TeacherDashboard)
async def get_teacher_dashboard(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """取得教師儀表板資料"""

    # Query teacher's organization via TeacherOrganization (with eager loading)
    teacher_org = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == current_teacher.id,
            TeacherOrganization.is_active.is_(True),
        )
        .options(joinedload(TeacherOrganization.organization))
        .first()
    )

    organization_info = None
    if teacher_org and teacher_org.organization and teacher_org.organization.is_active:
        org = teacher_org.organization
        organization_info = OrganizationInfo(
            id=str(org.id),
            name=org.display_name or org.name,
            type="organization",
        )

    # Query teacher's schools via TeacherSchool (with eager loading)
    teacher_schools = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == current_teacher.id,
            TeacherSchool.is_active.is_(True),
        )
        .options(joinedload(TeacherSchool.school))
        .all()
    )

    schools_info = []
    all_roles_set = set()

    # Add organization role if exists
    if teacher_org:
        all_roles_set.add(teacher_org.role)

    # Process schools and collect roles
    for ts in teacher_schools:
        if ts.school and ts.school.is_active:
            schools_info.append(
                SchoolInfo(
                    id=str(ts.school.id),
                    name=ts.school.display_name or ts.school.name,
                )
            )
            # Add school roles
            if ts.roles:
                all_roles_set.update(ts.roles)

    # Get classrooms with student count (only active classrooms)
    classrooms = (
        db.query(Classroom)
        .filter(
            Classroom.teacher_id == current_teacher.id,
            Classroom.is_active.is_(True),  # Filter out soft-deleted classrooms
        )
        .options(
            selectinload(Classroom.students).selectinload(ClassroomStudent.student)
        )
        .all()
    )

    classroom_summaries = []
    total_students = 0
    recent_students = []

    for classroom in classrooms:
        # Only count active students in active enrollments
        # Also check that student exists (not None) to avoid null reference errors
        active_students = [
            cs
            for cs in classroom.students
            if cs.is_active and cs.student and cs.student.is_active
        ]
        student_count = len(active_students)
        total_students += student_count

        classroom_summaries.append(
            ClassroomSummary(
                id=classroom.id,
                name=classroom.name,
                description=classroom.description,
                student_count=student_count,
            )
        )

        # Add recent students (first 3 active students from each classroom)
        for classroom_student in active_students[:3]:
            if (
                len(recent_students) < 10 and classroom_student.student
            ):  # Limit to 10 recent students
                recent_students.append(
                    StudentSummary(
                        id=classroom_student.student.id,
                        name=classroom_student.student.name,
                        email=classroom_student.student.email,  # Can be None now
                        classroom_name=classroom.name,
                    )
                )

    # Get program count (programs created by this teacher)
    program_count = (
        db.query(Program)
        .filter(Program.teacher_id == current_teacher.id, Program.is_active.is_(True))
        .count()
    )

    # 測試訂閱白名單（與 routers/subscription.py 保持一致）
    TEST_SUBSCRIPTION_WHITELIST = [
        "demo@duotopia.com",
        "expired@duotopia.com",
        "trial@duotopia.com",
        "purpleice9765@msn.com",
        "kaddyeunice@apps.ntpc.edu.tw",
        "ceeks.edu@gmail.com",
    ]
    is_test_account = current_teacher.email in TEST_SUBSCRIPTION_WHITELIST

    return TeacherDashboard(
        teacher=TeacherProfile.from_orm(current_teacher),
        classroom_count=len(classrooms),
        student_count=total_students,
        program_count=program_count,
        classrooms=classroom_summaries,
        recent_students=recent_students,
        # Subscription information
        subscription_status=current_teacher.subscription_status,
        subscription_end_date=current_teacher.subscription_end_date.isoformat()
        if current_teacher.subscription_end_date
        else None,
        days_remaining=current_teacher.days_remaining,
        can_assign_homework=current_teacher.can_assign_homework,
        is_test_account=is_test_account,
        # Organization and roles information
        organization=organization_info,
        schools=schools_info,
        roles=sorted(list(all_roles_set)),
    )
