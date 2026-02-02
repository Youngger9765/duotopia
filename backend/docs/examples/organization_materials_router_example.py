"""
Example Organization Materials Router

This demonstrates how to use the manage_materials permission
in organization-level materials/programs endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request
from pydantic import BaseModel
from typing import List
from functools import wraps
from services.casbin_service import get_casbin_service
from dependencies import get_current_teacher

router = APIRouter(
    prefix="/api/organizations/{org_id}/programs", tags=["organization_programs"]
)


# ============================================
# Request/Response Models
# ============================================


class OrganizationProgramCreate(BaseModel):
    """Create organization program request"""

    name: str
    description: str | None = None
    is_public: bool = False


class OrganizationProgramResponse(BaseModel):
    """Organization program response"""

    id: int
    organization_id: str
    name: str
    description: str | None
    is_public: bool
    created_by: int


# ============================================
# Permission Check Helper
# ============================================


def check_manage_materials_permission(teacher_id: int, org_id: str) -> bool:
    """
    Check if teacher has manage_materials permission in organization

    Args:
        teacher_id: Teacher ID
        org_id: Organization UUID

    Returns:
        bool: True if has permission

    Raises:
        HTTPException: 403 if no permission
    """
    casbin = get_casbin_service()

    has_permission = casbin.check_permission(
        teacher_id=teacher_id,
        domain=f"org-{org_id}",
        resource="manage_materials",
        action="write",
    )

    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to manage organization materials. "
            "Requires org_owner or org_admin role.",
        )

    return True


# ============================================
# Endpoints
# ============================================


@router.post("", response_model=OrganizationProgramResponse)
async def create_organization_program(
    org_id: str,
    program: OrganizationProgramCreate,
    current_teacher=Depends(get_current_teacher),
):
    """
    Create a new organization program/material

    Required permission: manage_materials (write)
    Allowed roles: org_owner, org_admin
    """
    # Check permission
    check_manage_materials_permission(current_teacher.id, org_id)

    # Implementation here
    # db.add(new_program)
    # db.commit()

    return OrganizationProgramResponse(
        id=1,
        organization_id=org_id,
        name=program.name,
        description=program.description,
        is_public=program.is_public,
        created_by=current_teacher.id,
    )


@router.get("", response_model=List[OrganizationProgramResponse])
async def list_organization_programs(
    org_id: str,
    current_teacher=Depends(get_current_teacher),
):
    """
    List all organization programs/materials

    Required permission: manage_materials (write)
    Allowed roles: org_owner, org_admin
    """
    check_manage_materials_permission(current_teacher.id, org_id)

    # Implementation here
    # programs = db.query(OrganizationProgram).filter_by(org_id=org_id).all()

    return []


@router.get("/{program_id}", response_model=OrganizationProgramResponse)
async def get_organization_program(
    org_id: str,
    program_id: int,
    current_teacher=Depends(get_current_teacher),
):
    """
    Get specific organization program/material

    Required permission: manage_materials (write)
    Allowed roles: org_owner, org_admin
    """
    check_manage_materials_permission(current_teacher.id, org_id)

    # Implementation here
    # program = db.query(OrganizationProgram).get(program_id)

    return OrganizationProgramResponse(
        id=program_id,
        organization_id=org_id,
        name="Example Program",
        description="Example",
        is_public=False,
        created_by=current_teacher.id,
    )


@router.put("/{program_id}", response_model=OrganizationProgramResponse)
async def update_organization_program(
    org_id: str,
    program_id: int,
    program: OrganizationProgramCreate,
    current_teacher=Depends(get_current_teacher),
):
    """
    Update organization program/material

    Required permission: manage_materials (write)
    Allowed roles: org_owner, org_admin
    """
    check_manage_materials_permission(current_teacher.id, org_id)

    # Implementation here
    # db_program.name = program.name
    # db.commit()

    return OrganizationProgramResponse(
        id=program_id,
        organization_id=org_id,
        name=program.name,
        description=program.description,
        is_public=program.is_public,
        created_by=current_teacher.id,
    )


@router.delete("/{program_id}")
async def delete_organization_program(
    org_id: str,
    program_id: int,
    current_teacher=Depends(get_current_teacher),
):
    """
    Delete organization program/material

    Required permission: manage_materials (write)
    Allowed roles: org_owner, org_admin
    """
    check_manage_materials_permission(current_teacher.id, org_id)

    # Implementation here
    # db.delete(program)
    # db.commit()

    return {"message": "Program deleted successfully"}


# ============================================
# Alternative: Using Decorator Pattern
# ============================================


def require_manage_materials(org_param: str = "org_id"):
    """
    Decorator to require manage_materials permission

    Usage:
        @require_manage_materials()
        async def endpoint(org_id: str, ...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get org_id from path params
            org_id = kwargs.get(org_param)
            if not org_id:
                raise HTTPException(status_code=400, detail="Organization ID required")

            # Get current teacher from dependencies
            request: Request = kwargs.get("request")
            current_teacher = getattr(request.state, "current_teacher", None)
            if not current_teacher:
                raise HTTPException(status_code=401, detail="Not authenticated")

            # Check permission
            check_manage_materials_permission(current_teacher.id, org_id)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Example using decorator
@router.post("/bulk")
@require_manage_materials()
async def bulk_create_programs(
    org_id: str,
    programs: List[OrganizationProgramCreate],
    current_teacher=Depends(get_current_teacher),
):
    """
    Bulk create organization programs

    Permission check is handled by decorator
    """
    # Implementation here
    return {"created": len(programs)}
