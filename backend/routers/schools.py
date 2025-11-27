"""
School API Routes

CRUD operations for schools with Casbin permission checks.
Only org_owner and org_admin can manage schools.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from models import Teacher, Organization, School, TeacherOrganization
from auth import verify_token
from services.casbin_service import get_casbin_service


router = APIRouter(prefix="/api/schools", tags=["schools"])
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


class SchoolCreate(BaseModel):
    """Request model for creating a school"""
    organization_id: str = Field(..., description="Organization UUID")
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None


class SchoolUpdate(BaseModel):
    """Request model for updating a school"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    contact_email: Optional[str] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SchoolResponse(BaseModel):
    """Response model for school"""
    id: str
    organization_id: str
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
    def from_orm(cls, school: School):
        """Convert School model to response"""
        return cls(
            id=str(school.id),
            organization_id=str(school.organization_id),
            name=school.name,
            display_name=school.display_name,
            description=school.description,
            contact_email=school.contact_email,
            contact_phone=school.contact_phone,
            address=school.address,
            is_active=school.is_active,
            created_at=school.created_at,
            updated_at=school.updated_at,
        )


# ============ Helper Functions ============


def check_org_permission(
    teacher_id: int,
    org_id: uuid.UUID,
    db: Session
) -> Organization:
    """
    Check if teacher has org-level access (org_owner or org_admin).
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

    # Check if teacher is org_owner or org_admin
    teacher_org = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher_id,
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.role.in_(["org_owner", "org_admin"]),
        TeacherOrganization.is_active == True
    ).first()

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage schools in this organization"
        )

    return org


def check_school_permission(
    teacher_id: int,
    school_id: uuid.UUID,
    db: Session
) -> School:
    """
    Check if teacher has access to school.
    Requires org_owner or org_admin of the school's organization.
    """
    # Check if school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )

    # Check org-level permission
    check_org_permission(teacher_id, school.organization_id, db)

    return school


# ============ API Endpoints ============


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SchoolResponse)
async def create_school(
    school_data: SchoolCreate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Create a new school.
    Requires org_owner or org_admin role in the organization.
    """
    org_id = uuid.UUID(school_data.organization_id)

    # Check permission (org_owner or org_admin)
    check_org_permission(teacher.id, org_id, db)

    # Create school
    school = School(
        organization_id=org_id,
        name=school_data.name,
        display_name=school_data.display_name,
        description=school_data.description,
        contact_email=school_data.contact_email,
        contact_phone=school_data.contact_phone,
        address=school_data.address,
        is_active=True,
    )

    db.add(school)
    db.commit()
    db.refresh(school)

    return SchoolResponse.from_orm(school)


@router.get("", response_model=List[SchoolResponse])
async def list_schools(
    organization_id: Optional[str] = Query(None, description="Filter by organization ID"),
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all schools that the current teacher has access to.
    If organization_id is provided, filter by that organization.
    """
    # Get all organizations where teacher is org_owner or org_admin
    teacher_orgs = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.role.in_(["org_owner", "org_admin"]),
        TeacherOrganization.is_active == True
    ).all()

    org_ids = [to.organization_id for to in teacher_orgs]

    # Build query
    query = db.query(School).filter(
        School.organization_id.in_(org_ids),
        School.is_active == True
    )

    # Apply organization filter if provided
    if organization_id:
        query = query.filter(School.organization_id == uuid.UUID(organization_id))

    schools = query.all()
    return [SchoolResponse.from_orm(school) for school in schools]


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Get school details.
    Requires org_owner or org_admin role.
    """
    school = check_school_permission(teacher.id, school_id, db)
    return SchoolResponse.from_orm(school)


@router.patch("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: uuid.UUID,
    school_data: SchoolUpdate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Update school details.
    Requires org_owner or org_admin role.
    """
    school = check_school_permission(teacher.id, school_id, db)

    # Update fields if provided
    if school_data.name is not None:
        school.name = school_data.name
    if school_data.display_name is not None:
        school.display_name = school_data.display_name
    if school_data.description is not None:
        school.description = school_data.description
    if school_data.contact_email is not None:
        school.contact_email = school_data.contact_email
    if school_data.contact_phone is not None:
        school.contact_phone = school_data.contact_phone
    if school_data.address is not None:
        school.address = school_data.address
    if school_data.is_active is not None:
        school.is_active = school_data.is_active

    db.commit()
    db.refresh(school)

    return SchoolResponse.from_orm(school)


@router.delete("/{school_id}")
async def delete_school(
    school_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Delete school (soft delete).
    Requires org_owner or org_admin role.
    """
    school = check_school_permission(teacher.id, school_id, db)

    # Soft delete
    school.is_active = False
    db.commit()

    return {"message": "School deleted successfully"}
