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
from models import Teacher, Organization, School, TeacherOrganization, TeacherSchool
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
    admin_name: Optional[str] = None
    admin_email: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, school: School, admin_name: Optional[str] = None, admin_email: Optional[str] = None):
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
            admin_name=admin_name,
            admin_email=admin_email,
        )


# ============ Helper Functions ============


def check_org_permission(
    teacher_id: int, org_id: uuid.UUID, db: Session
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    # Check if teacher is org_owner or org_admin
    teacher_org = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher_id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.role.in_(["org_owner", "org_admin"]),
            TeacherOrganization.is_active == True,
        )
        .first()
    )

    if not teacher_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to manage schools in this organization",
        )

    return org


def check_school_permission(
    teacher_id: int, school_id: uuid.UUID, db: Session
) -> School:
    """
    Check if teacher has access to school.
    Requires org_owner or org_admin of the school's organization.
    """
    # Check if school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="School not found"
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
    organization_id: Optional[str] = Query(
        None, description="Filter by organization ID"
    ),
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all schools that the current teacher has access to.
    If organization_id is provided, filter by that organization.
    """
    # Get all organizations where teacher is org_owner or org_admin
    teacher_orgs = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.teacher_id == teacher.id,
            TeacherOrganization.role.in_(["org_owner", "org_admin"]),
            TeacherOrganization.is_active == True,
        )
        .all()
    )

    org_ids = [to.organization_id for to in teacher_orgs]

    # Build query
    query = db.query(School).filter(
        School.organization_id.in_(org_ids), School.is_active == True
    )

    # Apply organization filter if provided
    if organization_id:
        query = query.filter(School.organization_id == uuid.UUID(organization_id))

    schools = query.all()

    # Build response with admin info
    result = []
    for school in schools:
        # Find school admin
        admin_rel = (
            db.query(TeacherSchool)
            .filter(
                TeacherSchool.school_id == school.id,
                TeacherSchool.roles.op('@>')(["school_admin"]),
                TeacherSchool.is_active == True,
            )
            .first()
        )

        admin_name = None
        admin_email = None
        if admin_rel:
            admin_teacher = db.query(Teacher).filter(Teacher.id == admin_rel.teacher_id).first()
            if admin_teacher:
                admin_name = admin_teacher.name
                admin_email = admin_teacher.email

        result.append(SchoolResponse.from_orm(school, admin_name=admin_name, admin_email=admin_email))

    return result


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

    # Find school admin
    admin_rel = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.school_id == school.id,
            TeacherSchool.roles.op('@>')(["school_admin"]),
            TeacherSchool.is_active == True,
        )
        .first()
    )

    admin_name = None
    admin_email = None
    if admin_rel:
        admin_teacher = db.query(Teacher).filter(Teacher.id == admin_rel.teacher_id).first()
        if admin_teacher:
            admin_name = admin_teacher.name
            admin_email = admin_teacher.email

    return SchoolResponse.from_orm(school, admin_name=admin_name, admin_email=admin_email)


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


# ============ Teacher Management Endpoints ============


class AddTeacherToSchoolRequest(BaseModel):
    """Request model for adding teacher to school"""

    teacher_id: int
    roles: List[str] = Field(..., description="List of roles: school_admin, teacher")


class UpdateTeacherRolesRequest(BaseModel):
    """Request model for updating teacher roles"""

    roles: List[str] = Field(..., description="List of roles: school_admin, teacher")


class TeacherSchoolRelationResponse(BaseModel):
    """Response model for teacher-school relationship"""

    id: int
    teacher_id: int
    school_id: str
    roles: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, rel: TeacherSchool):
        return cls(
            id=rel.id,
            teacher_id=rel.teacher_id,
            school_id=str(rel.school_id),
            roles=rel.roles if rel.roles else [],
            is_active=rel.is_active,
            created_at=rel.created_at,
        )


class SchoolTeacherInfo(BaseModel):
    """Teacher information in school"""

    id: int
    email: str
    name: str
    roles: List[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{school_id}/teachers", response_model=List[SchoolTeacherInfo])
async def list_school_teachers(
    school_id: uuid.UUID,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    List all teachers in a school.
    Requires teacher to be a member of the school or organization.
    """
    # Check permission
    check_school_permission(teacher.id, school_id, db)

    # Get all teacher relationships
    teacher_schools = (
        db.query(TeacherSchool)
        .filter(TeacherSchool.school_id == school_id, TeacherSchool.is_active == True)
        .all()
    )

    result = []
    for ts in teacher_schools:
        t = db.query(Teacher).filter(Teacher.id == ts.teacher_id).first()
        if t:
            result.append(
                SchoolTeacherInfo(
                    id=t.id,
                    email=t.email,
                    name=t.name,
                    roles=ts.roles if ts.roles else [],
                    is_active=ts.is_active,
                    created_at=ts.created_at,
                )
            )

    return result


@router.post(
    "/{school_id}/teachers",
    status_code=status.HTTP_201_CREATED,
    response_model=TeacherSchoolRelationResponse,
)
async def add_teacher_to_school(
    school_id: uuid.UUID,
    request: AddTeacherToSchoolRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Add a teacher to school with specified roles.
    Requires org_owner or org_admin role.
    """
    casbin_service = get_casbin_service()

    # Check permission
    check_school_permission(teacher.id, school_id, db)

    # Validate roles
    valid_roles = ["school_admin", "teacher"]
    for role in request.roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of {valid_roles}",
            )

    # Check if teacher already has relationship
    existing = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == request.teacher_id,
            TeacherSchool.school_id == school_id,
            TeacherSchool.is_active == True,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Teacher already belongs to this school",
        )

    # Verify teacher exists
    target_teacher = db.query(Teacher).filter(Teacher.id == request.teacher_id).first()
    if not target_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found"
        )

    # Create relationship
    teacher_school = TeacherSchool(
        teacher_id=request.teacher_id,
        school_id=school_id,
        roles=request.roles,
        is_active=True,
    )
    db.add(teacher_school)
    db.commit()
    db.refresh(teacher_school)

    # Add Casbin roles
    for role in request.roles:
        casbin_service.add_role_for_user(
            request.teacher_id, role, f"school-{school_id}"
        )

    return TeacherSchoolRelationResponse.from_orm(teacher_school)


@router.patch(
    "/{school_id}/teachers/{teacher_id}", response_model=TeacherSchoolRelationResponse
)
async def update_teacher_school_roles(
    school_id: uuid.UUID,
    teacher_id: int,
    request: UpdateTeacherRolesRequest,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Update teacher's roles in school.
    Requires org_owner or org_admin role.
    """
    casbin_service = get_casbin_service()

    # Check permission
    check_school_permission(teacher.id, school_id, db)

    # Validate roles
    valid_roles = ["school_admin", "teacher"]
    for role in request.roles:
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of {valid_roles}",
            )

    # Find relationship
    teacher_school = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == school_id,
            TeacherSchool.is_active == True,
        )
        .first()
    )

    if not teacher_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher relationship not found",
        )

    # Get old roles for Casbin cleanup
    old_roles = teacher_school.roles if teacher_school.roles else []

    # Update roles
    teacher_school.roles = request.roles
    db.commit()
    db.refresh(teacher_school)

    # Update Casbin roles
    # Remove old roles
    for role in old_roles:
        casbin_service.delete_role_for_user(teacher_id, role, f"school-{school_id}")
    # Add new roles
    for role in request.roles:
        casbin_service.add_role_for_user(teacher_id, role, f"school-{school_id}")

    return TeacherSchoolRelationResponse.from_orm(teacher_school)


@router.delete("/{school_id}/teachers/{teacher_id}")
async def remove_teacher_from_school(
    school_id: uuid.UUID,
    teacher_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """
    Remove a teacher from school (soft delete).
    Requires org_owner or org_admin role.
    """
    casbin_service = get_casbin_service()

    # Check permission
    check_school_permission(teacher.id, school_id, db)

    # Find relationship
    teacher_school = (
        db.query(TeacherSchool)
        .filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == school_id,
            TeacherSchool.is_active == True,
        )
        .first()
    )

    if not teacher_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher relationship not found",
        )

    # Soft delete
    teacher_school.is_active = False
    db.commit()

    # Remove all Casbin roles
    roles = teacher_school.roles if teacher_school.roles else []
    for role in roles:
        casbin_service.delete_role_for_user(teacher_id, role, f"school-{school_id}")

    return {"message": "Teacher removed from school successfully"}
