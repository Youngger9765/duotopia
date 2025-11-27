"""
Organization API Routes

CRUD operations for organizations with Casbin permission checks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models import Teacher, Organization, TeacherOrganization
from auth import verify_token
from services.casbin_service import get_casbin_service


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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    teacher_id = payload.get("sub")
    teacher_type = payload.get("type")

    if teacher_type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a teacher"
        )

    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
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

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, org: Organization):
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
        )


# ============ Helper Functions ============


def check_org_permission(
    teacher_id: int,
    org_id: uuid.UUID,
    db: Session
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )

    # Check if teacher is org owner
    teacher_org = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher_id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.is_active == True
    ).first()

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this organization"
        )

    return org


# ============ API Endpoints ============


@router.post("", status_code=status.HTTP_201_CREATED, response_model=OrganizationResponse)
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
    casbin_service.add_role_for_user(
        teacher.id,
        "org_owner",
        f"org-{org.id}"
    )

    return OrganizationResponse.from_orm(org)


@router.get("", response_model=List[OrganizationResponse])
async def list_organizations(
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all organizations that the current teacher has access to.
    """
    # Get all teacher-organization relationships
    teacher_orgs = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.is_active == True
    ).all()

    org_ids = [to.organization_id for to in teacher_orgs]

    # Get organizations
    organizations = db.query(Organization).filter(
        Organization.id.in_(org_ids),
        Organization.is_active == True
    ).all()

    return [OrganizationResponse.from_orm(org) for org in organizations]


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
    """
    # Check permission
    check_org_permission(teacher.id, org_id, db)

    # Get all teacher relationships
    teacher_orgs = db.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.is_active == True
    ).all()

    result = []
    for to in teacher_orgs:
        t = db.query(Teacher).filter(Teacher.id == to.teacher_id).first()
        if t:
            result.append(TeacherInfo(
                id=t.id,
                email=t.email,
                name=t.name,
                role=to.role,
                is_active=to.is_active,
                created_at=to.created_at,
            ))

    return result


@router.post("/{org_id}/teachers", status_code=status.HTTP_201_CREATED, response_model=TeacherRelationResponse)
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
    org = check_org_permission(teacher.id, org_id, db)

    teacher_org_check = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.role == "org_owner",
        TeacherOrganization.is_active == True
    ).first()

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can add teachers to organization"
        )

    # Check if adding org_owner and limit to 1
    if request.role == "org_owner":
        existing_owner = db.query(TeacherOrganization).filter(
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role == "org_owner",
            TeacherOrganization.is_active == True
        ).first()

        if existing_owner:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Organization already has an owner"
            )

    # Check if teacher already has relationship
    existing = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == request.teacher_id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.is_active == True
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher already belongs to this organization"
        )

    # Verify teacher exists
    target_teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if not target_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
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

    # Add Casbin role
    casbin_service.add_role_for_user(
        request.teacher_id,
        request.role,
        f"org-{org_id}"
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

    teacher_org_check = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.role == "org_owner",
        TeacherOrganization.is_active == True
    ).first()

    if not teacher_org_check:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only org_owner can remove teachers from organization"
        )

    # Find relationship
    teacher_org = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher_id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.is_active == True
    ).first()

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher relationship not found"
        )

    # Soft delete
    teacher_org.is_active = False
    db.commit()

    # Remove Casbin role
    casbin_service.delete_role_for_user(
        teacher_id,
        teacher_org.role,
        f"org-{org_id}"
    )

    return {"message": "Teacher removed from organization successfully"}
