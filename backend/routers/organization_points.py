from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid

from database import get_db
from models import Organization, Teacher, TeacherOrganization, OrganizationPointsLog
from routers.teachers import get_current_teacher
from utils.permissions import has_manage_materials_permission


router = APIRouter(prefix="/api/organizations", tags=["organization-points"])


class PointsBalanceResponse(BaseModel):
    organization_id: uuid.UUID
    total_points: int
    used_points: int
    remaining_points: int
    last_points_update: Optional[datetime]


class PointsDeductionRequest(BaseModel):
    points: int
    feature_type: str  # 'ai_generation', 'translation', etc.
    description: Optional[str] = None


class PointsDeductionResponse(BaseModel):
    organization_id: uuid.UUID
    points_deducted: int
    remaining_points: int
    transaction_id: int


class PointsLogItem(BaseModel):
    id: int
    organization_id: uuid.UUID
    teacher_id: Optional[int]
    teacher_name: Optional[str]  # Joined data
    points_used: int
    feature_type: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PointsHistoryResponse(BaseModel):
    items: List[PointsLogItem]
    total: int
    limit: int
    offset: int


@router.get("/{organization_id}/points", response_model=PointsBalanceResponse)
async def get_organization_points(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Query organization points balance.

    Permissions: org_owner or org_admin with manage_materials permission
    """
    # Check organization exists
    organization = db.query(Organization).filter(
        Organization.id == organization_id,
        Organization.is_active.is_(True)
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check permission
    membership = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == current_teacher.id,
        TeacherOrganization.organization_id == organization_id,
        TeacherOrganization.is_active.is_(True)
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    # org_owner always has access, org_admin needs manage_materials
    if membership.role != "org_owner":
        if not has_manage_materials_permission(current_teacher.id, organization_id, db):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view points"
            )

    return PointsBalanceResponse(
        organization_id=organization.id,
        total_points=organization.total_points,
        used_points=organization.used_points,
        remaining_points=organization.total_points - organization.used_points,
        last_points_update=organization.last_points_update
    )


@router.post("/{organization_id}/points/deduct", response_model=PointsDeductionResponse)
async def deduct_organization_points(
    organization_id: uuid.UUID,
    deduction: PointsDeductionRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Deduct points for AI feature usage (internal API).

    Permissions: org_owner or org_admin with manage_materials permission
    """
    # Validation
    if deduction.points <= 0:
        raise HTTPException(status_code=400, detail="Points must be positive")

    # Check organization exists
    organization = db.query(Organization).filter(
        Organization.id == organization_id,
        Organization.is_active.is_(True)
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check permission (same as GET points)
    membership = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == current_teacher.id,
        TeacherOrganization.organization_id == organization_id,
        TeacherOrganization.is_active.is_(True)
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if membership.role != "org_owner":
        if not has_manage_materials_permission(current_teacher.id, organization_id, db):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to deduct points"
            )

    # Check sufficient balance
    available = organization.total_points - organization.used_points
    if deduction.points > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient points. Available: {available}, Requested: {deduction.points}"
        )

    # Deduct points
    organization.used_points += deduction.points
    organization.last_points_update = datetime.now(timezone.utc)

    # Create log entry
    log_entry = OrganizationPointsLog(
        organization_id=organization_id,
        teacher_id=current_teacher.id,
        points_used=deduction.points,
        feature_type=deduction.feature_type,
        description=deduction.description
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return PointsDeductionResponse(
        organization_id=organization.id,
        points_deducted=deduction.points,
        remaining_points=organization.total_points - organization.used_points,
        transaction_id=log_entry.id
    )


@router.get("/{organization_id}/points/history", response_model=PointsHistoryResponse)
async def get_organization_points_history(
    organization_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """
    Get organization points usage history.

    Permissions: org_owner or org_admin with manage_materials permission
    Returns: Paginated list of points log entries, sorted by created_at DESC
    """
    # Check organization exists
    organization = db.query(Organization).filter(
        Organization.id == organization_id,
        Organization.is_active.is_(True)
    ).first()

    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check permission (same as GET points)
    membership = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == current_teacher.id,
        TeacherOrganization.organization_id == organization_id,
        TeacherOrganization.is_active.is_(True)
    ).first()

    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    if membership.role != "org_owner":
        if not has_manage_materials_permission(current_teacher.id, organization_id, db):
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions to view points history"
            )

    # Get total count
    total = db.query(OrganizationPointsLog).filter(
        OrganizationPointsLog.organization_id == organization_id
    ).count()

    # Get paginated logs with teacher info
    logs = (
        db.query(OrganizationPointsLog, Teacher.name)
        .outerjoin(Teacher, OrganizationPointsLog.teacher_id == Teacher.id)
        .filter(OrganizationPointsLog.organization_id == organization_id)
        .order_by(OrganizationPointsLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items = [
        PointsLogItem(
            id=log.id,
            organization_id=log.organization_id,
            teacher_id=log.teacher_id,
            teacher_name=teacher_name,
            points_used=log.points_used,
            feature_type=log.feature_type,
            description=log.description,
            created_at=log.created_at
        )
        for log, teacher_name in logs
    ]

    return PointsHistoryResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset
    )
