"""
Resource Materials Router

API endpoints for browsing and copying resource materials from the resource account.

Endpoints:
1. GET /api/resource-materials - List resource materials (filtered by scope/visibility)
2. GET /api/resource-materials/{program_id} - Get material detail (read-only)
3. POST /api/resource-materials/{program_id}/copy - Copy to individual or organization
4. GET /api/resource-materials/copy-status - Check today's copy status
5. PATCH /api/resource-materials/{program_id}/visibility - Update visibility (resource account only)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from database import get_db
from models import Teacher
from auth import verify_token
from services.resource_materials_service import (
    list_resource_materials,
    get_resource_material_detail,
    copy_resource_material,
    update_program_visibility,
    get_resource_account,
)
from utils.permissions import has_manage_materials_permission

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resource-materials", tags=["resource-materials"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Dependencies ============


async def get_current_teacher(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Teacher:
    """Verify token and return current teacher."""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    teacher_id = payload.get("teacher_id") or payload.get("sub")
    if not teacher_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )

    teacher = db.query(Teacher).filter(Teacher.id == int(teacher_id)).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


# ============ Schemas ============


class CopyRequest(BaseModel):
    target_type: str  # 'individual' or 'organization'
    organization_id: Optional[str] = None


class VisibilityUpdateRequest(BaseModel):
    visibility: str  # 'private', 'public', 'organization_only', 'individual_only'


# ============ Endpoints ============


@router.get("")
async def list_materials(
    scope: str = Query(
        "individual", description="Scope: 'individual' or 'organization'"
    ),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """List available resource materials filtered by scope and visibility."""
    if scope == "organization":
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id required for organization scope",
            )
        # Check org permission
        if not has_manage_materials_permission(teacher.id, organization_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to access organization resources",
            )

    materials = list_resource_materials(
        db=db,
        scope=scope,
        viewer_teacher_id=teacher.id,
        organization_id=organization_id,
    )
    return {"materials": materials, "count": len(materials)}


@router.get("/copy-status")
async def get_copy_status(
    scope: str = Query("individual"),
    organization_id: Optional[str] = Query(None),
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Get today's copy status for all resource materials."""
    from sqlalchemy import cast, Date
    from models import ProgramCopyLog
    from datetime import date

    today = date.today()

    if scope == "individual":
        copied_by_type = "individual"
        copied_by_id = str(teacher.id)
    elif scope == "organization":
        if not organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id required",
            )
        copied_by_type = "organization"
        copied_by_id = str(organization_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid scope"
        )

    logs = (
        db.query(ProgramCopyLog)
        .filter(
            ProgramCopyLog.copied_by_type == copied_by_type,
            ProgramCopyLog.copied_by_id == copied_by_id,
            cast(ProgramCopyLog.copied_at, Date) == today,
        )
        .all()
    )

    return {
        "copied_program_ids": [log.source_program_id for log in logs],
        "date": today.isoformat(),
    }


@router.get("/{program_id}")
async def get_material_detail(
    program_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Get detailed view of a resource material (read-only)."""
    detail = get_resource_material_detail(db, program_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource material not found",
        )

    # Check visibility permission
    resource_account = get_resource_account(db)
    if resource_account and teacher.id != resource_account.id:
        visibility = detail.get("visibility", "private")
        if visibility == "private":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource material not found",
            )

    return detail


@router.post("/{program_id}/copy")
async def copy_material(
    program_id: int,
    request: CopyRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Copy a resource material to individual's materials or organization."""
    if request.target_type == "organization":
        if not request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="organization_id required for organization copy",
            )
        if not has_manage_materials_permission(
            teacher.id, request.organization_id, db
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No permission to copy to this organization",
            )

    try:
        result = copy_resource_material(
            db=db,
            program_id=program_id,
            target_type=request.target_type,
            teacher_id=teacher.id,
            organization_id=request.organization_id,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )


@router.patch("/{program_id}/visibility")
async def update_visibility(
    program_id: int,
    request: VisibilityUpdateRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """Update resource material visibility (resource account only)."""
    try:
        result = update_program_visibility(
            db=db,
            program_id=program_id,
            teacher_id=teacher.id,
            visibility=request.visibility,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        )
