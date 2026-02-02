# Organization Points System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement organization points tracking system with admin controls, API endpoints, and frontend display for AI feature usage metering.

**Architecture:** Add points management to existing organization admin endpoints, create dedicated points API endpoints for querying/deducting/history, update organization dashboard to display points balance and usage history. Uses existing organization permission model (org_owner/org_admin).

**Tech Stack:** FastAPI (backend), SQLAlchemy (ORM), React/TypeScript (frontend), existing organization hierarchy models

---

## Prerequisites Completed

✅ **Phase 1: Database & Models** (Already done in migration branch)
- Migration: `backend/alembic/versions/20260203_0143_add_organization_points_system.py`
- Models: `backend/models/organization.py` (Organization + OrganizationPointsLog)

---

## Phase 2: Admin Interface (Points Setup)

### Task 1: Update Admin Organization Schemas

**Files:**
- Modify: `backend/routers/schemas/admin_organization.py`

**Step 1: Write failing test for admin organization creation with points**

Create: `backend/tests/test_admin_organizations_points.py`

```python
import pytest
from fastapi.testclient import TestClient
from main import app
from tests.conftest import override_get_db, override_get_current_user
from models import Organization, Teacher
from sqlalchemy.orm import Session


def test_admin_create_organization_with_points(client: TestClient, db: Session, admin_user: Teacher):
    """Admin can set initial points when creating organization"""
    response = client.post(
        "/admin/organizations",
        json={
            "name": "test-org",
            "display_name": "Test Organization",
            "total_points": 10000,
            "teacher_ids": [],
            "program_ids": []
        },
        headers={"Authorization": f"Bearer {admin_user.access_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["total_points"] == 10000
    assert data["used_points"] == 0

    # Verify in database
    org = db.query(Organization).filter(Organization.name == "test-org").first()
    assert org.total_points == 10000
    assert org.used_points == 0


def test_admin_update_organization_points(client: TestClient, db: Session, admin_user: Teacher, test_organization):
    """Admin can update organization total points"""
    response = client.put(
        f"/admin/organizations/{test_organization.id}",
        json={
            "total_points": 20000
        },
        headers={"Authorization": f"Bearer {admin_user.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 20000
```

**Step 2: Run test to verify it fails**

```bash
cd backend
pytest tests/test_admin_organizations_points.py -v
```

Expected: FAIL - "total_points" not in schema

**Step 3: Add points fields to admin schemas**

Modify: `backend/routers/schemas/admin_organization.py`

```python
# Add to OrganizationCreate
class OrganizationCreate(BaseModel):
    name: str = Field(..., description="Unique name for the organization")
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Organization description")
    tax_id: Optional[str] = Field(None, description="Taiwan Business ID")
    contact_email: Optional[str] = Field(None, description="Contact email")
    contact_phone: Optional[str] = Field(None, description="Contact phone")
    address: Optional[str] = Field(None, description="Physical address")
    teacher_limit: Optional[int] = Field(None, description="Maximum teachers")
    total_points: int = Field(
        default=0,
        description="Initial AI usage points for the organization"
    )
    settings: Optional[Dict[str, Any]] = Field(None, description="Organization settings")
    teacher_ids: List[int] = Field(
        default_factory=list,
        description="Teacher IDs to add to this organization (admin creates accounts)"
    )
    program_ids: List[int] = Field(
        default_factory=list, description="Program IDs to add to this organization"
    )


# Add to OrganizationUpdate
class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated name of the organization")
    display_name: Optional[str] = Field(None, description="Updated display name")
    description: Optional[str] = Field(None, description="Updated description")
    tax_id: Optional[str] = Field(None, description="Updated tax ID")
    contact_email: Optional[str] = Field(None, description="Updated contact email")
    contact_phone: Optional[str] = Field(None, description="Updated contact phone")
    address: Optional[str] = Field(None, description="Updated address")
    teacher_limit: Optional[int] = Field(None, description="Updated teacher limit")
    total_points: Optional[int] = Field(
        None,
        description="Updated total points (increases available balance)"
    )
    is_active: Optional[bool] = Field(None, description="Organization active status")
    settings: Optional[Dict[str, Any]] = Field(None, description="Updated settings")
    teacher_ids: List[int] = Field(
        default_factory=list,
        description="Teacher IDs to update in this organization (admin manages accounts)"
    )
    program_ids: List[int] = Field(
        default_factory=list, description="Program IDs to update"
    )


# Add to OrganizationResponse
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    tax_id: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    teacher_limit: Optional[int]
    total_points: int
    used_points: int
    available_points: int  # Computed field
    last_points_update: Optional[datetime]
    settings: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_orm_with_points(cls, org: Organization):
        data = {
            "id": org.id,
            "name": org.name,
            "display_name": org.display_name,
            "description": org.description,
            "tax_id": org.tax_id,
            "contact_email": org.contact_email,
            "contact_phone": org.contact_phone,
            "address": org.address,
            "is_active": org.is_active,
            "teacher_limit": org.teacher_limit,
            "total_points": org.total_points,
            "used_points": org.used_points,
            "available_points": org.total_points - org.used_points,
            "last_points_update": org.last_points_update,
            "settings": org.settings,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
        }
        return cls(**data)
```

**Step 4: Update admin router to handle points**

Modify: `backend/routers/admin.py` (create_organization_endpoint and update_organization_endpoint)

```python
# In create_organization_endpoint
@router.post("/organizations", response_model=OrganizationResponse, status_code=201)
async def create_organization_endpoint(
    org_data: OrganizationCreate,
    db: Session = Depends(get_db_wrapper),
    current_user: Teacher = Depends(get_current_user),
):
    # ... existing permission checks ...

    # Create organization with points
    new_org = Organization(
        name=org_data.name,
        display_name=org_data.display_name,
        description=org_data.description,
        tax_id=org_data.tax_id,
        contact_email=org_data.contact_email,
        contact_phone=org_data.contact_phone,
        address=org_data.address,
        teacher_limit=org_data.teacher_limit,
        total_points=org_data.total_points,
        used_points=0,
        last_points_update=datetime.now(timezone.utc) if org_data.total_points > 0 else None,
        settings=org_data.settings,
        is_active=True,
    )

    # ... rest of existing code ...

    return OrganizationResponse.from_orm_with_points(new_org)


# In update_organization_endpoint
@router.put("/organizations/{organization_id}", response_model=OrganizationResponse)
async def update_organization_endpoint(
    organization_id: UUID,
    org_update: OrganizationUpdate,
    db: Session = Depends(get_db_wrapper),
    current_user: Teacher = Depends(get_current_user),
):
    # ... existing permission checks ...

    # Update points if provided
    if org_update.total_points is not None:
        organization.total_points = org_update.total_points
        organization.last_points_update = datetime.now(timezone.utc)

    # ... rest of existing update code ...

    return OrganizationResponse.from_orm_with_points(organization)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_admin_organizations_points.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/routers/schemas/admin_organization.py backend/routers/admin.py backend/tests/test_admin_organizations_points.py
git commit -m "feat(admin): add points management to organization admin endpoints

- Add total_points field to OrganizationCreate schema
- Add total_points update to OrganizationUpdate schema
- Add points fields to OrganizationResponse (with computed available_points)
- Update admin endpoints to handle points on create/update
- Add tests for admin points management"
```

---

## Phase 3: Points API Endpoints

### Task 2: Create Points Query Endpoint

**Files:**
- Create: `backend/routers/organization_points.py`
- Create: `backend/tests/test_organization_points_api.py`

**Step 1: Write failing test for GET points endpoint**

Create: `backend/tests/test_organization_points_api.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from models import Organization, Teacher, TeacherOrganization, OrganizationPointsLog
from datetime import datetime, timezone
import uuid


def test_get_organization_points_as_owner(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Org owner can query organization points"""
    # Setup: Make teacher an org owner
    TeacherOrganization.create(
        db=db,
        teacher_id=test_teacher.id,
        organization_id=test_organization.id,
        role="org_owner"
    )

    # Setup: Set points
    test_organization.total_points = 10000
    test_organization.used_points = 3000
    db.commit()

    response = client.get(
        f"/api/organizations/{test_organization.id}/points",
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_points"] == 10000
    assert data["used_points"] == 3000
    assert data["available_points"] == 7000
    assert data["organization_id"] == str(test_organization.id)


def test_get_organization_points_unauthorized(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Non-member cannot query organization points"""
    response = client.get(
        f"/api/organizations/{test_organization.id}/points",
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 403
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_organization_points_api.py::test_get_organization_points_as_owner -v
```

Expected: FAIL - route not found

**Step 3: Create points router with GET endpoint**

Create: `backend/routers/organization_points.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import uuid

from database import get_db
from models import Organization, Teacher, TeacherOrganization
from routers.dependencies import get_current_user
from utils.permissions import has_manage_materials_permission


router = APIRouter(prefix="/api/organizations", tags=["organization-points"])


class PointsBalanceResponse(BaseModel):
    organization_id: uuid.UUID
    total_points: int
    used_points: int
    available_points: int
    last_points_update: Optional[datetime]


@router.get("/{organization_id}/points", response_model=PointsBalanceResponse)
async def get_organization_points(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_user),
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
        available_points=organization.total_points - organization.used_points,
        last_points_update=organization.last_points_update
    )
```

**Step 4: Register router in main.py**

Modify: `backend/main.py`

```python
# Add import
from routers.organization_points import router as organization_points_router

# Add router registration (after other organization routers)
app.include_router(organization_points_router)
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_organization_points_api.py::test_get_organization_points_as_owner -v
pytest tests/test_organization_points_api.py::test_get_organization_points_unauthorized -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/routers/organization_points.py backend/tests/test_organization_points_api.py backend/main.py
git commit -m "feat(api): add GET /organizations/{id}/points endpoint

- Create organization_points router
- Add points balance query endpoint
- Enforce org_owner/org_admin permissions
- Add tests for authorized and unauthorized access"
```

---

### Task 3: Create Points Deduction Endpoint (Internal API)

**Step 1: Write failing test for POST points deduction**

Add to: `backend/tests/test_organization_points_api.py`

```python
def test_deduct_organization_points(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Org owner can deduct points for AI usage"""
    # Setup
    TeacherOrganization.create(
        db=db,
        teacher_id=test_teacher.id,
        organization_id=test_organization.id,
        role="org_owner"
    )
    test_organization.total_points = 10000
    test_organization.used_points = 0
    db.commit()

    response = client.post(
        f"/api/organizations/{test_organization.id}/points/deduct",
        json={
            "points": 500,
            "feature_type": "ai_generation",
            "description": "Generated 10 questions with AI"
        },
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["points_deducted"] == 500
    assert data["remaining_points"] == 9500

    # Verify points updated
    db.refresh(test_organization)
    assert test_organization.used_points == 500

    # Verify log created
    log = db.query(OrganizationPointsLog).filter(
        OrganizationPointsLog.organization_id == test_organization.id
    ).first()
    assert log is not None
    assert log.points_used == 500
    assert log.feature_type == "ai_generation"
    assert log.teacher_id == test_teacher.id


def test_deduct_points_insufficient_balance(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Cannot deduct more points than available"""
    # Setup
    TeacherOrganization.create(
        db=db,
        teacher_id=test_teacher.id,
        organization_id=test_organization.id,
        role="org_owner"
    )
    test_organization.total_points = 100
    test_organization.used_points = 0
    db.commit()

    response = client.post(
        f"/api/organizations/{test_organization.id}/points/deduct",
        json={
            "points": 500,
            "feature_type": "ai_generation",
            "description": "Test"
        },
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 400
    assert "Insufficient points" in response.json()["detail"]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_organization_points_api.py::test_deduct_organization_points -v
```

Expected: FAIL - route not found

**Step 3: Add deduction endpoint to router**

Modify: `backend/routers/organization_points.py`

```python
from models import OrganizationPointsLog
from datetime import timezone


class PointsDeductionRequest(BaseModel):
    points: int
    feature_type: str  # 'ai_generation', 'translation', etc.
    description: Optional[str] = None


class PointsDeductionResponse(BaseModel):
    organization_id: uuid.UUID
    points_deducted: int
    remaining_points: int
    transaction_id: int


@router.post("/{organization_id}/points/deduct", response_model=PointsDeductionResponse)
async def deduct_organization_points(
    organization_id: uuid.UUID,
    deduction: PointsDeductionRequest,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_user),
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_organization_points_api.py::test_deduct_organization_points -v
pytest tests/test_organization_points_api.py::test_deduct_points_insufficient_balance -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/routers/organization_points.py backend/tests/test_organization_points_api.py
git commit -m "feat(api): add POST /organizations/{id}/points/deduct endpoint

- Add points deduction endpoint for AI feature usage
- Validate sufficient balance before deduction
- Create audit log entry in OrganizationPointsLog
- Enforce same permissions as points query
- Add tests for successful deduction and insufficient balance"
```

---

### Task 4: Create Points Usage History Endpoint

**Step 1: Write failing test for GET points history**

Add to: `backend/tests/test_organization_points_api.py`

```python
def test_get_organization_points_history(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Org owner can view points usage history"""
    # Setup
    TeacherOrganization.create(
        db=db,
        teacher_id=test_teacher.id,
        organization_id=test_organization.id,
        role="org_owner"
    )

    # Create some log entries
    for i in range(3):
        log = OrganizationPointsLog(
            organization_id=test_organization.id,
            teacher_id=test_teacher.id,
            points_used=100 * (i + 1),
            feature_type="ai_generation",
            description=f"Test usage {i+1}"
        )
        db.add(log)
    db.commit()

    response = client.get(
        f"/api/organizations/{test_organization.id}/points/history",
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 3
    assert data["total"] == 3

    # Verify sorted by created_at DESC (most recent first)
    assert data["items"][0]["points_used"] == 300
    assert data["items"][1]["points_used"] == 200
    assert data["items"][2]["points_used"] == 100


def test_get_points_history_with_pagination(
    client: TestClient,
    db: Session,
    test_teacher: Teacher,
    test_organization: Organization
):
    """Points history supports pagination"""
    # Setup
    TeacherOrganization.create(
        db=db,
        teacher_id=test_teacher.id,
        organization_id=test_organization.id,
        role="org_owner"
    )

    # Create 25 log entries
    for i in range(25):
        log = OrganizationPointsLog(
            organization_id=test_organization.id,
            teacher_id=test_teacher.id,
            points_used=10,
            feature_type="ai_generation"
        )
        db.add(log)
    db.commit()

    # Get first page
    response = client.get(
        f"/api/organizations/{test_organization.id}/points/history?limit=10&offset=0",
        headers={"Authorization": f"Bearer {test_teacher.access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["limit"] == 10
    assert data["offset"] == 0
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_organization_points_api.py::test_get_organization_points_history -v
```

Expected: FAIL - route not found

**Step 3: Add history endpoint to router**

Modify: `backend/routers/organization_points.py`

```python
from typing import List


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


@router.get("/{organization_id}/points/history", response_model=PointsHistoryResponse)
async def get_organization_points_history(
    organization_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_user),
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
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_organization_points_api.py::test_get_organization_points_history -v
pytest tests/test_organization_points_api.py::test_get_points_history_with_pagination -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/routers/organization_points.py backend/tests/test_organization_points_api.py
git commit -m "feat(api): add GET /organizations/{id}/points/history endpoint

- Add points usage history endpoint with pagination
- Include teacher name in response via join
- Sort by created_at DESC (most recent first)
- Enforce same permissions as points query
- Add tests for history retrieval and pagination"
```

---

## Phase 4: Frontend Display

### Task 5: Create Points Display Components

**Files:**
- Create: `frontend/src/components/OrganizationPointsBalance.tsx`
- Create: `frontend/src/components/OrganizationPointsHistory.tsx`
- Create: `frontend/src/types/points.ts`

**Step 1: Create types for points data**

Create: `frontend/src/types/points.ts`

```typescript
export interface PointsBalance {
  organization_id: string;
  total_points: number;
  used_points: number;
  available_points: number;
  last_points_update: string | null;
}

export interface PointsLogItem {
  id: number;
  organization_id: string;
  teacher_id: number | null;
  teacher_name: string | null;
  points_used: number;
  feature_type: string | null;
  description: string | null;
  created_at: string;
}

export interface PointsHistory {
  items: PointsLogItem[];
  total: number;
  limit: number;
  offset: number;
}
```

**Step 2: Create points balance component**

Create: `frontend/src/components/OrganizationPointsBalance.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { PointsBalance } from '../types/points';
import { API_BASE_URL } from '../config';

interface Props {
  organizationId: string;
}

export const OrganizationPointsBalance: React.FC<Props> = ({ organizationId }) => {
  const [balance, setBalance] = useState<PointsBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(
          `${API_BASE_URL}/api/organizations/${organizationId}/points`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch points balance');
        }

        const data = await response.json();
        setBalance(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchBalance();
  }, [organizationId]);

  if (loading) {
    return <div className="animate-pulse">Loading points balance...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  if (!balance) {
    return null;
  }

  const percentageUsed = (balance.used_points / balance.total_points) * 100;
  const isLow = balance.available_points < balance.total_points * 0.2;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">AI Usage Points</h3>

      {/* Balance Display */}
      <div className="mb-4">
        <div className="flex justify-between items-baseline mb-2">
          <span className="text-3xl font-bold">
            {balance.available_points.toLocaleString()}
          </span>
          <span className="text-gray-500">
            / {balance.total_points.toLocaleString()} total
          </span>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div
            className={`h-2.5 rounded-full ${
              isLow ? 'bg-red-600' : 'bg-blue-600'
            }`}
            style={{ width: `${100 - percentageUsed}%` }}
          />
        </div>
      </div>

      {/* Low Balance Warning */}
      {isLow && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">
          <p className="text-yellow-800 text-sm">
            ⚠️ Points running low. Contact admin to add more points.
          </p>
        </div>
      )}

      {/* Usage Stats */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="text-gray-500">Used</p>
          <p className="font-semibold">{balance.used_points.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-gray-500">Available</p>
          <p className="font-semibold">{balance.available_points.toLocaleString()}</p>
        </div>
      </div>

      {balance.last_points_update && (
        <p className="text-xs text-gray-400 mt-4">
          Last updated: {new Date(balance.last_points_update).toLocaleString()}
        </p>
      )}
    </div>
  );
};
```

**Step 3: Create points history component**

Create: `frontend/src/components/OrganizationPointsHistory.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { PointsHistory, PointsLogItem } from '../types/points';
import { API_BASE_URL } from '../config';

interface Props {
  organizationId: string;
}

export const OrganizationPointsHistory: React.FC<Props> = ({ organizationId }) => {
  const [history, setHistory] = useState<PointsHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const limit = 20;

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('access_token');
        const offset = page * limit;

        const response = await fetch(
          `${API_BASE_URL}/api/organizations/${organizationId}/points/history?limit=${limit}&offset=${offset}`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch points history');
        }

        const data = await response.json();
        setHistory(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [organizationId, page]);

  if (loading) {
    return <div className="animate-pulse">Loading history...</div>;
  }

  if (error) {
    return <div className="text-red-600">Error: {error}</div>;
  }

  if (!history || history.items.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">Points Usage History</h3>
        <p className="text-gray-500">No usage history yet.</p>
      </div>
    );
  }

  const totalPages = Math.ceil(history.total / limit);

  const getFeatureTypeBadge = (featureType: string | null) => {
    const badges: Record<string, string> = {
      ai_generation: 'bg-purple-100 text-purple-800',
      translation: 'bg-blue-100 text-blue-800',
      default: 'bg-gray-100 text-gray-800',
    };

    return badges[featureType || 'default'] || badges.default;
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b">
        <h3 className="text-lg font-semibold">Points Usage History</h3>
        <p className="text-sm text-gray-500">Total entries: {history.total}</p>
      </div>

      {/* History Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Date
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Feature
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Description
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Points
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {history.items.map((item: PointsLogItem) => (
              <tr key={item.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(item.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {item.teacher_name || 'Unknown'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getFeatureTypeBadge(
                      item.feature_type
                    )}`}
                  >
                    {item.feature_type || 'N/A'}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {item.description || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium text-gray-900">
                  -{item.points_used.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-gray-50 px-6 py-3 flex items-center justify-between border-t">
          <div className="text-sm text-gray-700">
            Showing {page * limit + 1} to {Math.min((page + 1) * limit, history.total)} of{' '}
            {history.total} results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(page - 1)}
              disabled={page === 0}
              className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(page + 1)}
              disabled={page >= totalPages - 1}
              className="px-4 py-2 border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Step 4: Commit frontend components**

```bash
git add frontend/src/types/points.ts frontend/src/components/OrganizationPointsBalance.tsx frontend/src/components/OrganizationPointsHistory.tsx
git commit -m "feat(frontend): add organization points display components

- Add PointsBalance type definitions
- Create OrganizationPointsBalance component with low balance warning
- Create OrganizationPointsHistory component with pagination
- Add visual indicators for points usage percentage
- Display teacher names and feature types in history"
```

---

### Task 6: Integrate Components into Organization Dashboard

**Files:**
- Modify: `frontend/src/pages/OrganizationDashboard.tsx` (or equivalent)

**Step 1: Import and add points components to dashboard**

Modify: `frontend/src/pages/OrganizationDashboard.tsx`

```typescript
import { OrganizationPointsBalance } from '../components/OrganizationPointsBalance';
import { OrganizationPointsHistory } from '../components/OrganizationPointsHistory';

// Inside the dashboard component, add points section
export const OrganizationDashboard: React.FC = () => {
  const { organizationId } = useParams<{ organizationId: string }>();

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Organization Dashboard</h1>

      {/* Points Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        <div className="lg:col-span-1">
          <OrganizationPointsBalance organizationId={organizationId} />
        </div>

        {/* Other dashboard widgets */}
        <div className="lg:col-span-2">
          {/* Existing dashboard content */}
        </div>
      </div>

      {/* Points History */}
      <div className="mt-8">
        <OrganizationPointsHistory organizationId={organizationId} />
      </div>
    </div>
  );
};
```

**Step 2: Test frontend display**

Manual testing steps:
1. Start frontend: `npm run dev`
2. Navigate to organization dashboard
3. Verify points balance displays correctly
4. Verify low balance warning appears when < 20%
5. Verify history table shows usage logs
6. Test pagination controls

**Step 3: Commit dashboard integration**

```bash
git add frontend/src/pages/OrganizationDashboard.tsx
git commit -m "feat(frontend): integrate points display into organization dashboard

- Add OrganizationPointsBalance to dashboard sidebar
- Add OrganizationPointsHistory to dashboard main area
- Update dashboard layout to accommodate points widgets"
```

---

## Testing Checklist

### Backend Tests
```bash
# Run all points-related tests
pytest backend/tests/test_admin_organizations_points.py -v
pytest backend/tests/test_organization_points_api.py -v

# Verify migration
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

### Frontend Tests
```bash
# Start dev server
cd frontend
npm run dev

# Manual testing:
# 1. Admin creates org with 10000 points
# 2. Navigate to org dashboard
# 3. Verify points balance shows 10000/10000
# 4. Deduct 3000 points via API (use Postman or curl)
# 5. Refresh dashboard, verify 7000/10000
# 6. Verify history shows deduction log
```

### Integration Tests
```bash
# End-to-end flow
# 1. Admin creates org with points
# 2. Org owner queries points
# 3. Org owner deducts points
# 4. Org owner views history
# 5. Verify all data consistency
```

---

## Deployment Notes

### Database Migration
```bash
# Run migration on staging
cd backend
alembic upgrade head

# Verify tables created
psql -d duotopia_staging -c "\d organizations"
psql -d duotopia_staging -c "\d organization_points_log"
```

### Environment Variables
No new environment variables needed.

### API Documentation
Update API docs to include new endpoints:
- `GET /api/organizations/{id}/points`
- `POST /api/organizations/{id}/points/deduct`
- `GET /api/organizations/{id}/points/history`

---

## Future Enhancements (Out of Scope)

- Points recharge workflow (payment integration)
- Points expiration mechanism
- Points transfer between organizations
- Advanced usage analytics dashboard
- Points usage forecasting
- Email alerts for low balance
- Bulk points operations for admin

---

## References

- Issue: #198
- Migration: `backend/alembic/versions/20260203_0143_add_organization_points_system.py`
- Models: `backend/models/organization.py`
- Permissions: `backend/utils/permissions.py`
- Spec: `spec/features/organization/機構設定與擁有人註冊.feature`

---

**Estimated Time:** 8-10 hours total
- Phase 2: 2-3 hours
- Phase 3: 3-4 hours
- Phase 4: 2-3 hours
- Testing & Integration: 1 hour
