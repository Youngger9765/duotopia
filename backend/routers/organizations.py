"""
Organization API Routes

CRUD operations for organizations with Casbin permission checks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models import Teacher, Organization, TeacherOrganization, TeacherSchool, School
from auth import verify_token, get_password_hash
from services.casbin_service import get_casbin_service
import secrets


router = APIRouter(prefix="/api/organizations", tags=["organizations"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Dependencies ============


async def get_current_teacher(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Teacher:
    """Get current authenticated teacher"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    teacher_id = payload.get("sub")
    teacher_type = payload.get("type")

    if teacher_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not a teacher"
        )

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    return teacher


# ============ Request/Response Models ============


class OrganizationCreate(BaseModel):
    """Request model for creating an organization"""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Request model for updating an organization"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationResponse(BaseModel):
    """Response model for organization"""

    id: str
    name: str
    display_name: Optional[str]
    description: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, org: Organization, owner: Optional[Teacher] = None):
        """Convert Organization model to response"""
        return cls(
            id=str(org.id),
            name=org.name,
            display_name=org.display_name,
            description=org.description,
            contact_email=org.contact_email,
            contact_phone=org.contact_phone,
            address=org.address,
            is_active=org.is_active,
            created_at=org.created_at,
            updated_at=org.updated_at,
            owner_name=owner.name if owner else None,
            owner_email=owner.email if owner else None,
        )


# ============ Helper Functions ============


def check_org_permission(
    teacher_id: int, org_id: uuid.UUID, db: Session
) -> Organization:
    """
    Check if teacher has access to organization.
    Raises HTTPException if not found or no permission.
    Returns organization if permission granted.
    """
    # Check if organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if teacher is org owner
    teacher_org = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher_id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this organization",
        )

    return org


# ============ API Endpoints ============


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=OrganizationResponse
)
async def create_organization(
    org_data: OrganizationCreate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Create a new organization.
    The creating teacher automatically becomes the org_owner.
    """
    casbin_service = get_casbin_service()

    # Create organization
    org = Organization(
        name=org_data.name,
        display_name=org_data.display_name,
        description=org_data.description,
        contact_email=org_data.contact_email,
        contact_phone=org_data.contact_phone,
        address=org_data.address,
        is_active=True,
    )

    db.add(org)
    db.commit()
    db.refresh(org)

    # Create teacher-organization relationship (org_owner)
    teacher_org = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True,
    )
    db.add(teacher_org)
    db.commit()

    # Add Casbin role
    casbin_service.add_role_for_user(teacher.id, "org_owner", f"org-{org.id}")

    return OrganizationResponse.from_orm(org)


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    owner_only: bool = False,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all organizations that the current teacher has access to.

    Args:
        owner_only: If True, only return organizations where teacher is org_owner

    Security: Returns 403 if teacher has no organization access.
    Performance: Fetches owners with joinedload to avoid N+1 queries.
    """
    # Get all teacher-organization relationships
    query = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.is_active.is_(True),
    )

    # Filter by owner role if requested
    if owner_only:
        query = query.filter(TeacherOrganization.role == "org_owner")

    teacher_orgs = query.all()

    # ✅ SECURITY FIX: Reject if no organization access
    if not teacher_orgs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此功能僅限組織成員使用。您目前不屬於任何組織。",
        )

    org_ids = [to.organization_id for to in teacher_orgs]

    # Get organizations
    organizations = (
        db.query(Organization)
        .filter(Organization.id.in_(org_ids), Organization.is_active.is_(True))
        .all()
    )

    # Build response with owner information
    result = []
    for org in organizations:
        # Get org_owner for this organization
        owner_rel = (
            db.query(TeacherOrganization)
            .options(joinedload(TeacherOrganization.teacher))
            .filter(
                TeacherOrganization.organization_id == org.id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )

        owner = owner_rel.teacher if owner_rel else None
        result.append(OrganizationResponse.from_orm(org, owner))

    return result


@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Get organization details.
    Requires teacher to be a member of the organization.
    """
    org = check_org_permission(teacher.id, org_id, db)
    return OrganizationResponse.from_orm(org)


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: uuid.UUID,
    org_data: OrganizationUpdate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Update organization details.
    Requires org_owner role.
    """
    org = check_org_permission(teacher.id, org_id, db)

    # Update fields if provided
    if org_data.name is not None:
        org.name = org_data.name
    if org_data.display_name is not None:
        org.display_name = org_data.display_name
    if org_data.description is not None:
        org.description = org_data.description
    if org_data.contact_email is not None:
        org.contact_email = org_data.contact_email
    if org_data.contact_phone is not None:
        org.contact_phone = org_data.contact_phone
    if org_data.address is not None:
        org.address = org_data.address
    if org_data.is_active is not None:
        org.is_active = org_data.is_active

    db.commit()
    db.refresh(org)

    return OrganizationResponse.from_orm(org)


@router.delete("/{org_id}")
async def delete_organization(
    org_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Delete organization (soft delete).
    Requires org_owner role.
    """
    org = check_org_permission(teacher.id, org_id, db)

    # Soft delete
    org.is_active = False
    db.commit()

    return {"message": "Organization deleted successfully"}


# ============ Teacher Management Endpoints ============


class AddTeacherRequest(BaseModel):
    """Request model for adding teacher to organization"""

    teacher_id: int
    role: str = Field(..., pattern="^(org_owner|org_admin)$")


class InviteTeacherRequest(BaseModel):
    """Request model for inviting teacher to organization"""

    email: str = Field(..., max_length=200)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="teacher", pattern="^(org_admin|teacher)$")


class TeacherRelationResponse(BaseModel):
    """Response model for teacher-organization relationship"""

    id: int
    teacher_id: int
    organization_id: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, rel: TeacherOrganization):
        return cls(
            id=rel.id,
            teacher_id=rel.teacher_id,
            organization_id=str(rel.organization_id),
            role=rel.role,
            is_active=rel.is_active,
            created_at=rel.created_at,
        )


class TeacherInfo(BaseModel):
    """Teacher information in organization"""

    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{org_id}/teachers", response_model=List[TeacherInfo])
async def list_organization_teachers(
    org_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all teachers in an organization.
    Requires teacher to be a member of the organization.

    Performance optimization: Uses joinedload to fetch teachers in a single query.
    """
    # Check permission
    check_org_permission(teacher.id, org_id, db)

    # Get all teacher relationships with eager loading (eliminates N+1 query)
    teacher_orgs = (
        db.query(TeacherOrganization)
        .options(joinedload(TeacherOrganization.teacher))
        .filter(
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
        )
        .all()
    )

    result = []
    for to in teacher_orgs:
        if to.teacher:
            result.append(
                TeacherInfo(
                    id=to.teacher.id,
                    email=to.teacher.email,
                    name=to.teacher.name,
                    role=to.role,
                    is_active=to.is_active,
                    created_at=to.created_at,
                )
            )

    return result


@router.post(
    "/{org_id}/teachers/invite",
    status_code=status.HTTP_201_CREATED,
    response_model=TeacherRelationResponse,
)
async def invite_teacher_to_organization(
    org_id: uuid.UUID,
    request: InviteTeacherRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Invite a teacher to organization by email.
    If teacher exists, adds them to org.
    If teacher doesn't exist, creates account and adds to org.
    Only org_owner can invite teachers.
    """
    casbin_service = get_casbin_service()

    # Check permission (only org_owner can invite teachers)
    check_org_permission(teacher.id, org_id, db)

    teacher_org_check = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher.id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role == "org_owner",
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can invite teachers to organization",
        )

    # Check if teacher already exists by email
    existing_teacher = db.query(Teacher).filter(Teacher.email == request.email).first()

    if existing_teacher:
        # Teacher exists - check if already in org
        existing_rel = (
            db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.teacher_id == existing_teacher.id,
                TeacherOrganization.organization_id == org_id,
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )

        if existing_rel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="此教師已在組織中",
            )

        # Add existing teacher to organization
        teacher_org = TeacherOrganization(
            teacher_id=existing_teacher.id,
            organization_id=org_id,
            role=request.role,
            is_active=True,
        )
        db.add(teacher_org)
        db.commit()
        db.refresh(teacher_org)

        # Sync Casbin roles
        try:
            casbin_service.sync_teacher_roles(existing_teacher.id)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Failed to sync Casbin roles for teacher {existing_teacher.id}: {e}"
            )

        return TeacherRelationResponse.from_orm(teacher_org)

    else:
        # Teacher doesn't exist - create new account
        # Generate random password (user should reset via "forgot password")
        random_password = secrets.token_urlsafe(16)

        new_teacher = Teacher(
            email=request.email,
            password_hash=get_password_hash(random_password),
            name=request.name,
            is_active=True,  # Active immediately for org invites
            is_demo=False,
            email_verified=True,  # Org invites are trusted, allow password reset
        )
        db.add(new_teacher)
        db.commit()
        db.refresh(new_teacher)

        # Add to organization
        teacher_org = TeacherOrganization(
            teacher_id=new_teacher.id,
            organization_id=org_id,
            role=request.role,
            is_active=True,
        )
        db.add(teacher_org)
        db.commit()
        db.refresh(teacher_org)

        # Sync Casbin roles
        try:
            casbin_service.sync_teacher_roles(new_teacher.id)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Failed to sync Casbin roles for teacher {new_teacher.id}: {e}"
            )

        # TODO: Send invitation email with password reset link
        # For now, just create the account

        return TeacherRelationResponse.from_orm(teacher_org)


@router.post(
    "/{org_id}/teachers",
    status_code=status.HTTP_201_CREATED,
    response_model=TeacherRelationResponse,
)
async def add_teacher_to_organization(
    org_id: uuid.UUID,
    request: AddTeacherRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Add a teacher to organization with specified role.
    Only org_owner can do this.
    Role can be org_owner or org_admin.
    """
    casbin_service = get_casbin_service()

    # Check permission (only org_owner can add teachers)
    check_org_permission(teacher.id, org_id, db)

    teacher_org_check = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher.id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role == "org_owner",
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can add teachers to organization",
        )

    # Check if adding org_owner and limit to 1
    if request.role == "org_owner":
        existing_owner = (
            db.query(TeacherOrganization)
            .filter(
                TeacherOrganization.organization_id == org_id,
                TeacherOrganization.role == "org_owner",
                TeacherOrganization.is_active.is_(True),
            )
            .first()
        )

        if existing_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization already has an owner",
            )

    # Check if teacher already has relationship
    existing = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == request.teacher_id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher already belongs to this organization",
        )

    # Verify teacher exists
    target_teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if not target_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    # Create relationship
    teacher_org = TeacherOrganization(
        teacher_id=request.teacher_id,
        organization_id=org_id,
        role=request.role,
        is_active=True,
    )
    db.add(teacher_org)
    db.commit()
    db.refresh(teacher_org)

    # Sync Casbin roles for this teacher
    try:
        casbin_service.sync_teacher_roles(request.teacher_id)
    except Exception as e:
        # Log error but don't fail the request
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"Failed to sync Casbin roles for teacher {request.teacher_id}: {e}"
        )

    return TeacherRelationResponse.from_orm(teacher_org)


@router.delete("/{org_id}/teachers/{teacher_id}")
async def remove_teacher_from_organization(
    org_id: uuid.UUID,
    teacher_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Remove a teacher from organization (soft delete).
    Only org_owner can do this.
    """
    casbin_service = get_casbin_service()

    # Check permission
    check_org_permission(teacher.id, org_id, db)

    teacher_org_check = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher.id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role == "org_owner",
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can remove teachers from organization",
        )

    # Find relationship
    teacher_org = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher_id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher relationship not found",
        )

    # Soft delete
    teacher_org.is_active = False
    db.commit()

    # Sync Casbin roles for this teacher (will remove inactive roles)
    try:
        casbin_service.sync_teacher_roles(teacher_id)
    except Exception as e:
        # Log error but don't fail the request
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to sync Casbin roles for teacher {teacher_id}: {e}")

    return {"message": "Teacher removed from organization successfully"}


# ============ Permission Management Endpoints ============


class TeacherPermissionsUpdate(BaseModel):
    """Request model for updating teacher permissions"""

    can_create_classrooms: Optional[bool] = None
    can_view_other_teachers: Optional[bool] = None
    can_manage_students: Optional[bool] = None
    max_classrooms: Optional[int] = None
    allowed_actions: Optional[
        List[str]
    ] = None  # ["create", "read", "update", "delete"]


class TeacherPermissionsResponse(BaseModel):
    """Response model for teacher permissions"""

    teacher_id: int
    school_id: str
    roles: List[str]
    permissions: Optional[dict] = None

    class Config:
        from_attributes = True


@router.put("/{org_id}/teachers/{teacher_id}/permissions")
async def update_teacher_permissions(
    org_id: uuid.UUID,
    teacher_id: int,
    permissions_data: TeacherPermissionsUpdate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Update teacher's custom permissions within schools of this organization.
    Only org_owner can set custom permissions.

    Permissions are stored in teacher_schools.permissions (JSONB) and override default role permissions.
    """
    # Check if current teacher is org_owner
    check_org_permission(teacher.id, org_id, db)

    teacher_org_check = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher.id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role == "org_owner",
            TeacherOrganization.is_active.is_(True),
        )
        .first()
    )

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can manage teacher permissions",
        )

    # Get teacher_school relationships with JOIN on schools (performance optimization)
    teacher_schools = (
        db.query(TeacherSchool)
        .join(School, School.id == TeacherSchool.school_id)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            School.organization_id == org_id,
            School.is_active.is_(True),
            TeacherSchool.is_active.is_(True),
        )
        .all()
    )

    if not teacher_schools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found in any schools of this organization",
        )

    # Build permissions dict from request
    new_permissions = {}
    if permissions_data.can_create_classrooms is not None:
        new_permissions[
            "can_create_classrooms"
        ] = permissions_data.can_create_classrooms
    if permissions_data.can_view_other_teachers is not None:
        new_permissions[
            "can_view_other_teachers"
        ] = permissions_data.can_view_other_teachers
    if permissions_data.can_manage_students is not None:
        new_permissions["can_manage_students"] = permissions_data.can_manage_students
    if permissions_data.max_classrooms is not None:
        new_permissions["max_classrooms"] = permissions_data.max_classrooms
    if permissions_data.allowed_actions is not None:
        new_permissions["allowed_actions"] = permissions_data.allowed_actions

    # Update permissions for all teacher_school relationships
    updated_count = 0
    for ts in teacher_schools:
        # Merge with existing permissions
        current_permissions = ts.permissions or {}
        current_permissions.update(new_permissions)
        ts.permissions = current_permissions
        updated_count += 1

    db.commit()

    return {
        "message": f"Permissions updated for teacher {teacher_id} in {updated_count} school(s)",
        "updated_schools": updated_count,
        "permissions": new_permissions,
    }


@router.get("/{org_id}/teachers/{teacher_id}/permissions")
async def get_teacher_permissions(
    org_id: uuid.UUID,
    teacher_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Get teacher's permissions across all schools in this organization.
    Requires org_owner or org_admin role.

    Performance optimization: Uses JOIN to fetch teacher_schools in a single query.
    """
    # Check if current teacher has access to org
    check_org_permission(teacher.id, org_id, db)

    # Get teacher_school relationships with JOIN on schools
    # This eliminates the need to query schools separately
    teacher_schools = (
        db.query(TeacherSchool)
        .join(School, School.id == TeacherSchool.school_id)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            School.organization_id == org_id,
            School.is_active.is_(True),
            TeacherSchool.is_active.is_(True),
        )
        .all()
    )

    if not teacher_schools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found in any schools of this organization",
        )

    # Return permissions for each school
    result = []
    for ts in teacher_schools:
        result.append(
            {
                "teacher_id": ts.teacher_id,
                "school_id": str(ts.school_id),
                "roles": ts.roles,
                "permissions": ts.permissions,
            }
        )

    return {"teacher_id": teacher_id, "schools": result}
