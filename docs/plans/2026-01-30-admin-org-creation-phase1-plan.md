# Admin Organization Creation - Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend admin organization creation with 3 features using existing database fields (no migration required)

**Architecture:** Add backend API endpoints for statistics and owner lookup, extend Pydantic schemas to support project staff assignment, update frontend form to display owner info and allow multi-select for org_admin roles

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, React 18, TypeScript, Shadcn UI, Casbin RBAC

**Design Doc:** docs/plans/2026-01-30-admin-org-creation-extended-features-design.md

---

## Task 1: Teacher Statistics API (Backend)

**Goal:** Add endpoint to get organization teacher count statistics

**Files:**
- Modify: `backend/routers/organizations.py` (add new endpoint after line 800)
- Test: `backend/tests/test_admin_organizations.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_admin_organizations.py`:

```python
def test_get_organization_statistics_as_admin(client, admin_user_headers, test_db):
    """Test admin can get organization statistics"""
    # Create organization
    org_data = {
        "name": "Test Org Stats",
        "owner_email": "admin@duotopia.com",
        "teacher_limit": 10
    }
    create_response = client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=admin_user_headers
    )
    assert create_response.status_code == 201
    org_id = create_response.json()["organization_id"]

    # Add 3 more teachers to organization
    from models import Teacher, TeacherOrganization
    teacher1 = Teacher(email="t1@test.com", password_hash="hash", name="T1", email_verified=True)
    teacher2 = Teacher(email="t2@test.com", password_hash="hash", name="T2", email_verified=True)
    teacher3 = Teacher(email="t3@test.com", password_hash="hash", name="T3", email_verified=True)
    test_db.add_all([teacher1, teacher2, teacher3])
    test_db.flush()

    test_db.add_all([
        TeacherOrganization(teacher_id=teacher1.id, organization_id=org_id, role="teacher", is_active=True),
        TeacherOrganization(teacher_id=teacher2.id, organization_id=org_id, role="teacher", is_active=True),
        TeacherOrganization(teacher_id=teacher3.id, organization_id=org_id, role="org_admin", is_active=True),
    ])
    test_db.commit()

    # Get statistics
    response = client.get(
        f"/api/admin/organizations/{org_id}/statistics",
        headers=admin_user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_count"] == 4  # 1 owner + 3 added
    assert data["teacher_limit"] == 10
    assert data["usage_percentage"] == 40.0


def test_get_organization_statistics_no_limit(client, admin_user_headers, test_db):
    """Test statistics when teacher_limit is None (unlimited)"""
    org_data = {
        "name": "Test Org Unlimited",
        "owner_email": "admin@duotopia.com",
        # No teacher_limit
    }
    create_response = client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=admin_user_headers
    )
    org_id = create_response.json()["organization_id"]

    response = client.get(
        f"/api/admin/organizations/{org_id}/statistics",
        headers=admin_user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["teacher_count"] == 1
    assert data["teacher_limit"] is None
    assert data["usage_percentage"] == 0.0  # 0% when unlimited
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_admin_organizations.py::test_get_organization_statistics_as_admin -v
```

Expected: FAIL with "404 Not Found" (endpoint doesn't exist yet)

**Step 3: Add response schema**

Add to `backend/routers/schemas/admin_organization.py` after line 59:

```python
class OrganizationStatisticsResponse(BaseModel):
    """Organization teacher statistics"""

    teacher_count: int = Field(..., description="Active teachers in organization")
    teacher_limit: Optional[int] = Field(None, description="Maximum teachers allowed (None = unlimited)")
    usage_percentage: float = Field(..., description="Percentage of limit used (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "teacher_count": 5,
                "teacher_limit": 10,
                "usage_percentage": 50.0
            }
        }
```

**Step 4: Implement endpoint**

Add to `backend/routers/admin.py` after the create_organization_as_admin endpoint (around line 800):

```python
@router.get(
    "/organizations/{org_id}/statistics",
    response_model=OrganizationStatisticsResponse,
    summary="Get organization statistics (Admin only)"
)
async def get_organization_statistics(
    org_id: str,
    current_admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get organization teacher count and limit statistics.

    **Admin only endpoint.**

    Returns:
    - teacher_count: Number of active teachers
    - teacher_limit: Maximum allowed (None if unlimited)
    - usage_percentage: Percentage used (0 if unlimited)
    """
    # Validate organization exists
    org = db.query(Organization).filter(Organization.id == org_id).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {org_id} not found"
        )

    # Count active teachers
    active_teacher_count = (
        db.query(TeacherOrganization)
        .filter(
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active == True
        )
        .count()
    )

    # Calculate usage percentage
    if org.teacher_limit is None or org.teacher_limit == 0:
        usage_percentage = 0.0
    else:
        usage_percentage = (active_teacher_count / org.teacher_limit) * 100

    return OrganizationStatisticsResponse(
        teacher_count=active_teacher_count,
        teacher_limit=org.teacher_limit,
        usage_percentage=round(usage_percentage, 1)
    )
```

**Step 5: Update imports**

Add to imports in `backend/routers/admin.py`:

```python
from routers.schemas.admin_organization import (
    AdminOrganizationCreate,
    AdminOrganizationResponse,
    OrganizationStatisticsResponse,  # Add this
)
```

**Step 6: Run test to verify it passes**

```bash
pytest tests/test_admin_organizations.py::test_get_organization_statistics_as_admin -v
pytest tests/test_admin_organizations.py::test_get_organization_statistics_no_limit -v
```

Expected: PASS (both tests)

**Step 7: Commit**

```bash
git add backend/routers/admin.py backend/routers/schemas/admin_organization.py backend/tests/test_admin_organizations.py
git commit -m "feat(admin): add organization teacher statistics endpoint

- Add GET /api/admin/organizations/{id}/statistics
- Returns teacher_count, teacher_limit, usage_percentage
- Handles unlimited (None) teacher_limit case
- Add OrganizationStatisticsResponse schema
- Add 2 tests for statistics endpoint

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 2: Owner Lookup API (Backend)

**Goal:** Add endpoint to fetch teacher info by email for owner name/phone display

**Files:**
- Modify: `backend/routers/admin.py` (add new endpoint)
- Modify: `backend/routers/schemas/admin_organization.py` (add response schema)
- Test: `backend/tests/test_admin_organizations.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_admin_organizations.py`:

```python
def test_get_teacher_by_email_as_admin(client, admin_user_headers, test_db):
    """Test admin can lookup teacher by email"""
    # Create test teacher
    from models import Teacher
    teacher = Teacher(
        email="owner@test.com",
        password_hash="hash",
        name="王小明",
        phone="0912345678",
        email_verified=True
    )
    test_db.add(teacher)
    test_db.commit()

    # Lookup by email
    response = client.get(
        "/api/admin/teachers/lookup?email=owner@test.com",
        headers=admin_user_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "owner@test.com"
    assert data["name"] == "王小明"
    assert data["phone"] == "0912345678"
    assert data["email_verified"] is True
    assert "id" in data


def test_get_teacher_by_email_not_found(client, admin_user_headers):
    """Test lookup returns 404 for non-existent email"""
    response = client.get(
        "/api/admin/teachers/lookup?email=nonexistent@test.com",
        headers=admin_user_headers
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_teacher_by_email_non_admin_forbidden(client, teacher_user_headers):
    """Test non-admin cannot use lookup endpoint"""
    response = client.get(
        "/api/admin/teachers/lookup?email=any@test.com",
        headers=teacher_user_headers
    )
    assert response.status_code == 403
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_admin_organizations.py::test_get_teacher_by_email_as_admin -v
```

Expected: FAIL with "404 Not Found"

**Step 3: Add response schema**

Add to `backend/routers/schemas/admin_organization.py`:

```python
class TeacherLookupResponse(BaseModel):
    """Teacher lookup response for admin"""

    id: int
    email: str
    name: str
    phone: Optional[str]
    email_verified: bool

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 42,
                "email": "wang@abc.edu.tw",
                "name": "王小明",
                "phone": "0912345678",
                "email_verified": True
            }
        }
```

**Step 4: Implement endpoint**

Add to `backend/routers/admin.py`:

```python
@router.get(
    "/teachers/lookup",
    response_model=TeacherLookupResponse,
    summary="Lookup teacher by email (Admin only)"
)
async def lookup_teacher_by_email(
    email: EmailStr,
    current_admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Lookup teacher information by email.

    **Admin only endpoint.**

    Used to fetch owner name/phone when entering owner_email in org creation form.

    Returns: Teacher id, email, name, phone, email_verified
    """
    teacher = db.query(Teacher).filter(Teacher.email == email).first()

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with email {email} not found"
        )

    return TeacherLookupResponse(
        id=teacher.id,
        email=teacher.email,
        name=teacher.name,
        phone=teacher.phone,
        email_verified=teacher.email_verified
    )
```

**Step 5: Update imports**

Add to imports in `backend/routers/admin.py`:

```python
from pydantic import EmailStr  # Add to existing pydantic imports
from routers.schemas.admin_organization import (
    AdminOrganizationCreate,
    AdminOrganizationResponse,
    OrganizationStatisticsResponse,
    TeacherLookupResponse,  # Add this
)
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_admin_organizations.py::test_get_teacher_by_email_as_admin -v
pytest tests/test_admin_organizations.py::test_get_teacher_by_email_not_found -v
pytest tests/test_admin_organizations.py::test_get_teacher_by_email_non_admin_forbidden -v
```

Expected: PASS (all 3 tests)

**Step 7: Commit**

```bash
git add backend/routers/admin.py backend/routers/schemas/admin_organization.py backend/tests/test_admin_organizations.py
git commit -m "feat(admin): add teacher lookup by email endpoint

- Add GET /api/admin/teachers/lookup?email=xxx
- Returns teacher id, name, phone, email_verified
- Used for owner info display in org creation form
- Add TeacherLookupResponse schema
- Add 3 tests for lookup endpoint

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 3: Project Staff Assignment (Backend)

**Goal:** Support assigning multiple org_admin roles during organization creation

**Files:**
- Modify: `backend/routers/schemas/admin_organization.py` (extend request schema)
- Modify: `backend/routers/admin.py` (update create endpoint logic)
- Test: `backend/tests/test_admin_organizations.py`

**Step 1: Write the failing test**

Add to `backend/tests/test_admin_organizations.py`:

```python
def test_create_organization_with_project_staff(client, admin_user_headers, test_db):
    """Test creating organization with multiple project staff (org_admin)"""
    # Create test teachers for project staff
    from models import Teacher
    staff1 = Teacher(email="staff1@duotopia.com", password_hash="hash", name="Staff 1", email_verified=True)
    staff2 = Teacher(email="staff2@duotopia.com", password_hash="hash", name="Staff 2", email_verified=True)
    test_db.add_all([staff1, staff2])
    test_db.commit()

    # Create organization with project staff
    org_data = {
        "name": "Test Org With Staff",
        "owner_email": "admin@duotopia.com",
        "project_staff_emails": ["staff1@duotopia.com", "staff2@duotopia.com"]
    }

    response = client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=admin_user_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["organization_name"] == "Test Org With Staff"
    assert "project_staff_assigned" in data
    assert len(data["project_staff_assigned"]) == 2
    assert "staff1@duotopia.com" in data["project_staff_assigned"]
    assert "staff2@duotopia.com" in data["project_staff_assigned"]

    # Verify roles in database
    from models import TeacherOrganization
    org_id = data["organization_id"]

    staff_roles = test_db.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == org_id,
        TeacherOrganization.role == "org_admin"
    ).all()

    assert len(staff_roles) == 2
    staff_emails = [r.teacher.email for r in staff_roles]
    assert "staff1@duotopia.com" in staff_emails
    assert "staff2@duotopia.com" in staff_emails


def test_create_organization_staff_not_verified(client, admin_user_headers, test_db):
    """Test cannot assign unverified teacher as project staff"""
    from models import Teacher
    unverified = Teacher(email="unverified@test.com", password_hash="hash", name="Unverified", email_verified=False)
    test_db.add(unverified)
    test_db.commit()

    org_data = {
        "name": "Test Org",
        "owner_email": "admin@duotopia.com",
        "project_staff_emails": ["unverified@test.com"]
    }

    response = client.post(
        "/api/admin/organizations",
        json=org_data,
        headers=admin_user_headers
    )

    assert response.status_code == 400
    assert "unverified@test.com" in response.json()["detail"]
    assert "not verified" in response.json()["detail"].lower()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_admin_organizations.py::test_create_organization_with_project_staff -v
```

Expected: FAIL (field not in schema)

**Step 3: Update request schema**

Modify `AdminOrganizationCreate` in `backend/routers/schemas/admin_organization.py`:

```python
from typing import Optional, List  # Add List to imports

class AdminOrganizationCreate(BaseModel):
    """Request to create organization with owner assignment (admin only)"""

    # Organization info
    name: str = Field(..., min_length=1, max_length=100, description="機構英文名稱")
    display_name: Optional[str] = Field(None, max_length=200, description="機構顯示名稱（中文）")
    description: Optional[str] = Field(None, description="機構描述")
    tax_id: Optional[str] = Field(None, max_length=20, description="統一編號")
    teacher_limit: Optional[int] = Field(None, ge=1, description="教師授權總數")

    # Contact info (optional)
    contact_email: Optional[EmailStr] = Field(None, max_length=200)
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = None

    # Owner assignment
    owner_email: EmailStr = Field(..., description="機構擁有人 Email（必須已註冊）")

    # Project staff assignment (NEW)
    project_staff_emails: Optional[List[EmailStr]] = Field(
        default=None,
        description="專案服務人員 Email 列表（org_admin 角色）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "ABC Education",
                "display_name": "ABC 教育集團",
                "description": "Professional English education organization",
                "tax_id": "12345678",
                "teacher_limit": 10,
                "contact_email": "contact@abc.edu.tw",
                "contact_phone": "02-1234-5678",
                "address": "台北市信義區信義路五段7號",
                "owner_email": "wang@abc.edu.tw",
                "project_staff_emails": ["staff@duotopia.com"]  # Add to example
            }
        }
```

**Step 4: Update response schema**

Modify `AdminOrganizationResponse` in same file:

```python
class AdminOrganizationResponse(BaseModel):
    """Response after creating organization"""

    organization_id: str
    organization_name: str
    owner_email: str
    owner_id: int
    project_staff_assigned: Optional[List[str]] = Field(default=None, description="Project staff emails assigned as org_admin")  # NEW
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_name": "ABC Education",
                "owner_email": "wang@abc.edu.tw",
                "owner_id": 42,
                "project_staff_assigned": ["staff@duotopia.com"],  # Add to example
                "message": "Organization created successfully. Owner wang@abc.edu.tw has been assigned org_owner role. 1 project staff assigned."
            }
        }
```

**Step 5: Update create endpoint logic**

Modify `create_organization_as_admin` in `backend/routers/admin.py` (around line 708-800):

```python
async def create_organization_as_admin(
    org_data: AdminOrganizationCreate,
    current_admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # ... existing owner validation code ...

    # NEW: Validate project staff if provided
    project_staff_teachers = []
    if org_data.project_staff_emails:
        for staff_email in org_data.project_staff_emails:
            staff_teacher = db.query(Teacher).filter(
                Teacher.email == staff_email,
                Teacher.email_verified == True
            ).first()

            if not staff_teacher:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Teacher {staff_email} not found or not verified. "
                           "Project staff must be registered and verified users."
                )

            # Prevent owner from being in project staff
            if staff_email == org_data.owner_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Owner {staff_email} cannot also be project staff. "
                           "Owner already has org_owner role."
                )

            project_staff_teachers.append(staff_teacher)

    # ... existing organization creation code ...

    # ... existing owner assignment code ...

    # NEW: Assign project staff as org_admin
    for staff_teacher in project_staff_teachers:
        staff_org = TeacherOrganization(
            teacher_id=staff_teacher.id,
            organization_id=new_org.id,
            role="org_admin",
            is_active=True,
        )
        db.add(staff_org)

        # Add Casbin role for org_admin
        casbin_service.add_role_for_user(
            teacher_id=staff_teacher.id,
            role="org_admin",
            domain=new_org.id
        )

    db.commit()
    db.refresh(new_org)

    # Build response message
    staff_count = len(project_staff_teachers)
    staff_msg = f" {staff_count} project staff assigned." if staff_count > 0 else ""

    return AdminOrganizationResponse(
        organization_id=str(new_org.id),
        organization_name=new_org.name,
        owner_email=owner.email,
        owner_id=owner.id,
        project_staff_assigned=[t.email for t in project_staff_teachers] if project_staff_teachers else None,
        message=f"Organization created successfully. Owner {owner.email} has been assigned org_owner role.{staff_msg}"
    )
```

**Step 6: Run tests to verify they pass**

```bash
pytest tests/test_admin_organizations.py::test_create_organization_with_project_staff -v
pytest tests/test_admin_organizations.py::test_create_organization_staff_not_verified -v
# Also run existing test to ensure no regression
pytest tests/test_admin_organizations.py::test_create_organization_as_admin_success -v
```

Expected: PASS (all tests)

**Step 7: Commit**

```bash
git add backend/routers/admin.py backend/routers/schemas/admin_organization.py backend/tests/test_admin_organizations.py
git commit -m "feat(admin): support project staff assignment in org creation

- Add project_staff_emails field to AdminOrganizationCreate
- Validate staff are registered and verified
- Prevent owner from being project staff
- Assign org_admin role to project staff
- Add Casbin permissions for org_admin
- Return assigned staff in response
- Add 2 tests for project staff assignment

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 4: Frontend Types Update

**Goal:** Update TypeScript types to match new backend schemas

**Files:**
- Modify: `frontend/src/types/admin.ts`

**Step 1: Update types**

Replace content in `frontend/src/types/admin.ts`:

```typescript
/**
 * Admin-related types
 */

export interface AdminOrganizationCreateRequest {
  name: string;
  display_name?: string;
  description?: string;
  tax_id?: string;
  teacher_limit?: number;
  contact_email?: string;
  contact_phone?: string;
  address?: string;
  owner_email: string;
  project_staff_emails?: string[];  // NEW
}

export interface AdminOrganizationCreateResponse {
  organization_id: string;
  organization_name: string;
  owner_email: string;
  owner_id: number;
  project_staff_assigned?: string[];  // NEW
  message: string;
}

// NEW: Teacher lookup response
export interface TeacherLookupResponse {
  id: number;
  email: string;
  name: string;
  phone: string | null;
  email_verified: boolean;
}

// NEW: Organization statistics response
export interface OrganizationStatisticsResponse {
  teacher_count: number;
  teacher_limit: number | null;
  usage_percentage: number;
}
```

**Step 2: Run type check**

```bash
cd frontend
npm run typecheck
```

Expected: PASS (no type errors)

**Step 3: Commit**

```bash
git add frontend/src/types/admin.ts
git commit -m "feat(frontend): update admin types for Phase 1 features

- Add project_staff_emails to create request
- Add project_staff_assigned to response
- Add TeacherLookupResponse type
- Add OrganizationStatisticsResponse type

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 5: Owner Info Display (Frontend)

**Goal:** Fetch and display owner name/phone when email is entered

**Files:**
- Modify: `frontend/src/pages/admin/CreateOrganization.tsx`

**Step 1: Add owner info state**

Add after line 27 in CreateOrganization.tsx:

```typescript
const [ownerInfo, setOwnerInfo] = useState<{
  name: string;
  phone: string | null;
  email_verified: boolean;
} | null>(null);
const [ownerLookupError, setOwnerLookupError] = useState("");
```

**Step 2: Add owner lookup function**

Add after line 47 (after useEffect):

```typescript
const lookupOwner = async (email: string) => {
  if (!email || !email.includes("@")) {
    setOwnerInfo(null);
    setOwnerLookupError("");
    return;
  }

  try {
    const response = await apiClient.get<TeacherLookupResponse>(
      `/api/admin/teachers/lookup?email=${encodeURIComponent(email)}`
    );
    setOwnerInfo({
      name: response.name,
      phone: response.phone,
      email_verified: response.email_verified,
    });
    setOwnerLookupError("");

    // Show warning if not verified
    if (!response.email_verified) {
      setOwnerLookupError("警告：此教師尚未驗證 Email");
    }
  } catch (err) {
    setOwnerInfo(null);
    if (err && typeof err === "object" && "response" in err) {
      const apiError = err as { response?: { status?: number } };
      if (apiError.response?.status === 404) {
        setOwnerLookupError("此 Email 尚未註冊");
      } else {
        setOwnerLookupError("查詢失敗");
      }
    }
  }
};
```

**Step 3: Add import**

Add to imports at top of file:

```typescript
import {
  AdminOrganizationCreateRequest,
  AdminOrganizationCreateResponse,
  TeacherLookupResponse,  // Add this
} from "@/types/admin";
```

**Step 4: Add owner email change handler**

Modify the owner_email Input onChange (around line 334):

```tsx
<Input
  id="owner_email"
  type="email"
  placeholder="owner@example.com"
  value={formData.owner_email}
  onChange={(e) => {
    setFormData({ ...formData, owner_email: e.target.value });
    lookupOwner(e.target.value);  // Add this line
  }}
  className="pl-10"
  required
  disabled={isLoading}
/>
```

**Step 5: Add owner info display**

Add after the owner_email Input (around line 343):

```tsx
{ownerInfo && (
  <div className="mt-2 p-3 bg-blue-50 rounded-md border border-blue-200">
    <p className="text-sm font-medium text-blue-900">教師資訊</p>
    <p className="text-sm text-blue-700 mt-1">
      姓名：{ownerInfo.name}
    </p>
    {ownerInfo.phone && (
      <p className="text-sm text-blue-700">
        手機：{ownerInfo.phone}
      </p>
    )}
    {ownerInfo.email_verified && (
      <p className="text-xs text-green-600 mt-1">✓ Email 已驗證</p>
    )}
  </div>
)}
{ownerLookupError && (
  <p className="text-sm text-amber-600 mt-1">
    {ownerLookupError}
  </p>
)}
```

**Step 6: Test manually**

```bash
cd frontend
npm run dev
```

1. Login as admin
2. Go to /admin/organizations/create
3. Enter a valid teacher email in owner_email field
4. Verify name and phone appear below

**Step 7: Commit**

```bash
git add frontend/src/pages/admin/CreateOrganization.tsx
git commit -m "feat(frontend): display owner info when email entered

- Fetch teacher info by email on owner_email change
- Display name, phone, verification status
- Show error if teacher not found or unverified
- Add visual feedback with blue info box

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 6: Project Staff Multi-Select (Frontend)

**Goal:** Add multi-select field for project staff emails

**Files:**
- Modify: `frontend/src/pages/admin/CreateOrganization.tsx`

**Step 1: Add state**

Add to formData state (around line 28):

```typescript
const [formData, setFormData] = useState<AdminOrganizationCreateRequest>({
  name: "",
  display_name: "",
  description: "",
  tax_id: "",
  teacher_limit: undefined,
  contact_email: "",
  contact_phone: "",
  address: "",
  owner_email: "",
  project_staff_emails: [],  // Add this
});
```

**Step 2: Add input state**

Add new state for staff email input:

```typescript
const [staffEmailInput, setStaffEmailInput] = useState("");
```

**Step 3: Add staff management functions**

Add after the lookupOwner function:

```typescript
const addStaffEmail = () => {
  const email = staffEmailInput.trim();
  if (!email || !email.includes("@")) {
    return;
  }

  // Prevent duplicates
  if (formData.project_staff_emails?.includes(email)) {
    toast.error("此 Email 已在列表中");
    return;
  }

  // Prevent adding owner as staff
  if (email === formData.owner_email) {
    toast.error("擁有人不能同時是專案服務人員");
    return;
  }

  setFormData({
    ...formData,
    project_staff_emails: [...(formData.project_staff_emails || []), email],
  });
  setStaffEmailInput("");
};

const removeStaffEmail = (email: string) => {
  setFormData({
    ...formData,
    project_staff_emails: formData.project_staff_emails?.filter(e => e !== email),
  });
};
```

**Step 4: Update submit handler**

Modify handleSubmit to include project_staff_emails (around line 78):

```typescript
if (formData.address) requestData.address = formData.address;

// Add project staff if any
if (formData.project_staff_emails && formData.project_staff_emails.length > 0) {
  requestData.project_staff_emails = formData.project_staff_emails;
}
```

**Step 5: Add UI section**

Add new section after the "機構擁有人" section (around line 345):

```tsx
{/* Project Staff Section */}
<div className="space-y-4">
  <h3 className="text-lg font-semibold">專案服務人員（可選）</h3>

  <Alert>
    <AlertDescription>
      專案服務人員將被指派為 org_admin 角色，協助管理機構。可加入多位服務人員。
    </AlertDescription>
  </Alert>

  <div className="space-y-2">
    <Label htmlFor="staff_email">服務人員 Email</Label>
    <div className="flex gap-2">
      <div className="relative flex-1">
        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        <Input
          id="staff_email"
          type="email"
          placeholder="staff@duotopia.com"
          value={staffEmailInput}
          onChange={(e) => setStaffEmailInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addStaffEmail();
            }
          }}
          className="pl-10"
          disabled={isLoading}
        />
      </div>
      <Button
        type="button"
        variant="outline"
        onClick={addStaffEmail}
        disabled={isLoading || !staffEmailInput}
      >
        新增
      </Button>
    </div>
  </div>

  {formData.project_staff_emails && formData.project_staff_emails.length > 0 && (
    <div className="space-y-2">
      <p className="text-sm font-medium">已加入的服務人員（{formData.project_staff_emails.length}）</p>
      <div className="space-y-2">
        {formData.project_staff_emails.map((email) => (
          <div
            key={email}
            className="flex items-center justify-between p-2 bg-gray-50 rounded-md border"
          >
            <span className="text-sm">{email}</span>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => removeStaffEmail(email)}
              disabled={isLoading}
            >
              移除
            </Button>
          </div>
        ))}
      </div>
    </div>
  )}
</div>
```

**Step 6: Test manually**

```bash
npm run dev
```

1. Go to org creation form
2. Add multiple staff emails
3. Try adding duplicate (should show error)
4. Try adding owner email (should show error)
5. Remove a staff email
6. Submit form and verify project_staff_assigned in response

**Step 7: Commit**

```bash
git add frontend/src/pages/admin/CreateOrganization.tsx
git commit -m "feat(frontend): add project staff multi-select field

- Add input field and 'Add' button for staff emails
- Support multiple staff assignments
- Prevent duplicates and owner-as-staff
- Show staff list with remove buttons
- Include project_staff_emails in submit request
- Add validation and user feedback

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 7: Teacher Count Display (Frontend)

**Goal:** Display teacher usage statistics on organization pages

**Files:**
- Create: `frontend/src/components/organization/TeacherUsageCard.tsx`
- Modify: `frontend/src/pages/admin/AdminDashboard.tsx` (add to org tab)

**Step 1: Create reusable component**

Create `frontend/src/components/organization/TeacherUsageCard.tsx`:

```tsx
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Users, Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api";
import { OrganizationStatisticsResponse } from "@/types/admin";

interface TeacherUsageCardProps {
  organizationId: string;
}

export default function TeacherUsageCard({ organizationId }: TeacherUsageCardProps) {
  const [stats, setStats] = useState<OrganizationStatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<OrganizationStatisticsResponse>(
          `/api/admin/organizations/${organizationId}/statistics`
        );
        setStats(response);
        setError("");
      } catch (err) {
        console.error("Failed to fetch teacher statistics:", err);
        setError("無法載入教師統計");
      } finally {
        setLoading(false);
      }
    };

    if (organizationId) {
      fetchStats();
    }
  }, [organizationId]);

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    );
  }

  if (error || !stats) {
    return (
      <Card>
        <CardContent className="py-6">
          <p className="text-sm text-red-600">{error || "載入失敗"}</p>
        </CardContent>
      </Card>
    );
  }

  const isUnlimited = stats.teacher_limit === null;
  const isNearLimit = !isUnlimited && stats.usage_percentage >= 80;
  const isAtLimit = !isUnlimited && stats.usage_percentage >= 100;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">教師授權使用</CardTitle>
        <Users className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {stats.teacher_count} {!isUnlimited && `/ ${stats.teacher_limit}`}
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          {isUnlimited ? (
            "無限制"
          ) : (
            <>
              使用率 {stats.usage_percentage.toFixed(1)}%
              {isAtLimit && <span className="text-red-600 ml-2">已達上限</span>}
              {isNearLimit && !isAtLimit && (
                <span className="text-amber-600 ml-2">接近上限</span>
              )}
            </>
          )}
        </p>
      </CardContent>
    </Card>
  );
}
```

**Step 2: Add to admin dashboard**

Modify `frontend/src/pages/admin/AdminDashboard.tsx` organizations tab content (around line 78):

```tsx
{/* Organization Management Tab */}
<TabsContent value="organizations" className="space-y-4">
  <Card>
    <CardHeader>
      <CardTitle>組織管理</CardTitle>
      <CardDescription>
        創建和管理機構，分配組織擁有人權限
      </CardDescription>
    </CardHeader>
    <CardContent className="space-y-4">
      <div className="flex gap-4">
        <Button
          onClick={() => navigate("/admin/organizations/create")}
          className="flex items-center gap-2"
        >
          <Building className="h-4 w-4" />
          創建機構
        </Button>
      </div>
      <p className="text-sm text-gray-600">
        機構創建功能可以讓平台管理員為已註冊的老師創建組織並指派擁有人權限。
      </p>

      {/* Add teacher usage example (optional - requires org ID) */}
      {/* <TeacherUsageCard organizationId="example-org-id" /> */}
    </CardContent>
  </Card>
</TabsContent>
```

**Step 3: Test component in isolation**

Create a test page or add temporarily to CreateOrganization success state to verify component renders correctly.

**Step 4: Run type check**

```bash
cd frontend
npm run typecheck
```

Expected: PASS

**Step 5: Commit**

```bash
git add frontend/src/components/organization/TeacherUsageCard.tsx frontend/src/pages/admin/AdminDashboard.tsx
git commit -m "feat(frontend): add teacher usage statistics card component

- Create TeacherUsageCard component
- Fetch organization teacher statistics
- Display teacher_count / teacher_limit
- Show usage percentage with color coding
- Handle unlimited case (teacher_limit = null)
- Add loading and error states

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 8: End-to-End Testing

**Goal:** Verify all Phase 1 features work together

**Files:**
- Manual testing checklist

**Step 1: Backend API testing**

```bash
cd backend
# Run all new tests
pytest tests/test_admin_organizations.py -v

# Run full test suite to ensure no regressions
pytest -n auto
```

Expected: All tests PASS

**Step 2: Frontend type check and lint**

```bash
cd frontend
npm run typecheck
npm run lint
```

Expected: No errors

**Step 3: Manual E2E testing**

Start both servers:
```bash
# Terminal 1 - Backend
cd backend && uvicorn main:app --reload --port 8080

# Terminal 2 - Frontend
cd frontend && npm run dev
```

**Test Flow:**

1. **Teacher Lookup**
   - Login as admin
   - Go to /admin/organizations/create
   - Enter existing teacher email in "擁有人 Email"
   - Verify: Name and phone appear below
   - Enter non-existent email
   - Verify: Error "此 Email 尚未註冊" appears

2. **Project Staff Assignment**
   - Add 2 staff emails
   - Try adding duplicate → Verify error toast
   - Try adding owner email → Verify error toast
   - Remove one staff email
   - Submit form with 1 staff
   - Verify: Success toast mentions "1 project staff assigned"

3. **Teacher Statistics** (if component added to page)
   - Navigate to organization page with stats
   - Verify: Shows "X / Y" format
   - Verify: Percentage calculation correct
   - Test with unlimited (no teacher_limit)
   - Verify: Shows "無限制"

**Step 4: Verify database state**

```bash
# Check project staff was assigned org_admin role
cd backend
python -c "
from database import SessionLocal
from models import TeacherOrganization

db = SessionLocal()
org_id = 'YOUR_TEST_ORG_ID'  # From test
staff_roles = db.query(TeacherOrganization).filter(
    TeacherOrganization.organization_id == org_id,
    TeacherOrganization.role == 'org_admin'
).all()
print(f'Project staff count: {len(staff_roles)}')
for s in staff_roles:
    print(f'  - {s.teacher.email} (role: {s.role})')
"
```

**Step 5: Document testing results**

Create `docs/testing/2026-01-30-phase1-test-report.md`:

```markdown
# Phase 1 Test Report

**Date**: 2026-01-30
**Tester**: [Your Name]
**Environment**: Local development

## Test Results

### Backend Tests
- ✅ test_get_organization_statistics_as_admin
- ✅ test_get_organization_statistics_no_limit
- ✅ test_get_teacher_by_email_as_admin
- ✅ test_get_teacher_by_email_not_found
- ✅ test_get_teacher_by_email_non_admin_forbidden
- ✅ test_create_organization_with_project_staff
- ✅ test_create_organization_staff_not_verified

### Frontend Manual Tests
- ✅ Owner info displays when email entered
- ✅ Error shown for non-existent owner email
- ✅ Project staff can be added/removed
- ✅ Duplicate staff prevented
- ✅ Owner-as-staff prevented
- ✅ Form submission includes staff emails
- ✅ Success message shows staff count

### Database Verification
- ✅ org_admin roles created in TeacherOrganization
- ✅ Casbin roles added correctly

## Issues Found
[None or list any issues]

## Conclusion
Phase 1 implementation complete and verified.
```

**Step 6: Final commit**

```bash
git add docs/testing/2026-01-30-phase1-test-report.md
git commit -m "test: add Phase 1 E2E test report

- All 7 backend tests passing
- Frontend manual tests completed
- Database state verified
- No issues found

Phase 1 complete: Teacher statistics API, owner info display, project staff assignment

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Task 9: Documentation Update

**Goal:** Update project documentation to reflect Phase 1 completion

**Files:**
- Modify: `docs/plans/2026-01-30-admin-org-creation-extended-features-design.md`
- Modify: `TODO.md`
- Modify: `ORG_PRD.md`

**Step 1: Update design doc status**

Add to top of design doc after "Status:" line:

```markdown
**Status**: Phase 1 Complete ✅ (2026-01-30)
**Implemented**: Tasks 1-3 (Teacher statistics, Owner lookup, Project staff)
**Branch**: feat/issue-112-org-hierarchy
```

**Step 2: Update TODO.md**

Mark Phase 1 items as complete:

```markdown
**Phase 1: 不需要 Migration（優先實作）** ✅ COMPLETED
- ✅ **教師授權數顯示**（3-4h） - DONE 2026-01-30
  - ✅ Backend: GET /api/admin/organizations/{id}/statistics
  - ✅ Frontend: TeacherUsageCard component

- ✅ **擁有人姓名、手機欄位**（2-3h） - DONE 2026-01-30
  - ✅ Backend: GET /api/admin/teachers/lookup?email=xxx
  - ✅ Frontend: Auto-fetch on owner_email change

- ✅ **專案服務人員指派（org_admin）**（4-6h） - DONE 2026-01-30
  - ✅ Backend: project_staff_emails field support
  - ✅ Frontend: Multi-select input with validation
  - ✅ Casbin: org_admin role permissions
```

**Step 3: Update ORG_PRD.md**

Update Phase 1 status:

```markdown
**Phase 1: No Migration Required** ✅ COMPLETED (2026-01-30)
  1. ✅ **教師授權數顯示** - DONE
  2. ✅ **擁有人姓名、手機欄位** - DONE
  3. ✅ **專案服務人員指派（org_admin）** - DONE

**Implementation**: 7 backend tests, 2 new API endpoints, frontend form enhancements
**Commits**: 9 commits (Tasks 1-8)
**Test Coverage**: 100% for new features
```

**Step 4: Commit**

```bash
git add docs/plans/2026-01-30-admin-org-creation-extended-features-design.md TODO.md ORG_PRD.md
git commit -m "docs: mark Phase 1 as complete

- Update design doc status to 'Phase 1 Complete'
- Mark Phase 1 tasks as done in TODO.md
- Update ORG_PRD.md with completion status
- Document 7 tests, 2 endpoints, frontend enhancements

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>"
```

---

## Verification Checklist

Before considering Phase 1 complete, verify:

- [ ] All 7 backend tests pass
- [ ] `pytest -n auto` passes (no regressions)
- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes
- [ ] Manual E2E test completed
- [ ] Database state verified (org_admin roles exist)
- [ ] Test report documented
- [ ] Documentation updated (design doc, TODO, PRD)
- [ ] All 9 commits pushed to branch

---

## Next Steps

After Phase 1 completion:

1. **User Testing**: Have client test the new features
2. **Feedback Iteration**: Address any UX issues
3. **Phase 2 Decision**: Proceed with unregistered owner flow?
4. **Phase 3 Decision**: Get approval for migration (points system)?

**Reference**: See `docs/plans/2026-01-30-admin-org-creation-extended-features-design.md` for Phase 2-3 details.

---

**Estimated Total Time**: 13-18 hours (as designed)
**Actual Time**: [To be filled after completion]
