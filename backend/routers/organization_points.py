from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from database import get_db
from models import Organization, Teacher, TeacherOrganization
from routers.teachers import get_current_teacher
from utils.permissions import has_manage_materials_permission


router = APIRouter(prefix="/api/organizations", tags=["organization-points"])


class PointsBalanceResponse(BaseModel):
    organization_id: uuid.UUID
    total_points: int
    used_points: int
    remaining_points: int
    last_points_update: Optional[datetime]


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
