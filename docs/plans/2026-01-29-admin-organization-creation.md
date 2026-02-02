# Admin Organization Creation Interface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Enable platform administrators to create organizations and assign existing registered teachers as organization owners through an admin interface.

**Architecture:** Create admin-only endpoint at `/api/admin/organizations` that validates owner email exists, creates organization, and assigns org_owner role via TeacherOrganization + Casbin. Frontend admin page at `/admin/organizations/create` with form validation.

**Tech Stack:** FastAPI, SQLAlchemy, Casbin, React, TypeScript, React Hook Form

---

## Task 1: Backend - Create Admin Organization Schema

**Files:**
- Create: `backend/routers/schemas/admin_organization.py`

**Step 1: Create schema file**

Create `backend/routers/schemas/admin_organization.py`:

```python
"""Admin-only organization creation schemas"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional


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
                "owner_email": "wang@abc.edu.tw"
            }
        }


class AdminOrganizationResponse(BaseModel):
    """Response after creating organization"""

    organization_id: str
    organization_name: str
    owner_email: str
    owner_id: int
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "organization_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_name": "ABC Education",
                "owner_email": "wang@abc.edu.tw",
                "owner_id": 42,
                "message": "Organization created successfully. Owner wang@abc.edu.tw has been assigned org_owner role."
            }
        }
```

**Step 2: Commit**

```bash
git add backend/routers/schemas/admin_organization.py
git commit -m "feat: add admin organization creation schemas"
```

---

## Task 2: Backend - Create Admin Organization Endpoint

**Files:**
- Modify: `backend/routers/admin.py`

**Reference:**
- Existing admin pattern: `backend/routers/admin.py:get_current_admin()`
- Organization creation logic: `backend/routers/organizations.py:create_organization()`

**Step 1: Add imports**

At top of `backend/routers/admin.py`, add:

```python
from backend.routers.schemas.admin_organization import (
    AdminOrganizationCreate,
    AdminOrganizationResponse,
)
from backend.models.organization import Organization, TeacherOrganization
from backend.services.casbin_service import CasbinService
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import uuid
```

**Step 2: Write the failing test**

Create `backend/tests/test_admin_organizations.py`:

```python
"""Tests for admin organization creation endpoint"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db
from backend.models.teacher import Teacher


client = TestClient(app)


def test_create_organization_as_admin_success(db_session, admin_teacher, regular_teacher):
    """Admin can create organization and assign existing teacher as owner"""

    # Login as admin
    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_teacher.email, "password": "admin_password"}
    )
    assert login_response.status_code == 200
    admin_token = login_response.json()["access_token"]

    # Create organization
    response = client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Org",
            "display_name": "測試機構",
            "tax_id": "12345678",
            "teacher_limit": 10,
            "owner_email": regular_teacher.email
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["organization_name"] == "Test Org"
    assert data["owner_email"] == regular_teacher.email
    assert "organization_id" in data

    # Verify organization created
    org = db_session.query(Organization).filter(
        Organization.name == "Test Org"
    ).first()
    assert org is not None
    assert org.tax_id == "12345678"

    # Verify owner role assigned
    teacher_org = db_session.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == org.id,
        TeacherOrganization.teacher_id == regular_teacher.id
    ).first()
    assert teacher_org is not None
    assert teacher_org.role == "org_owner"


def test_create_organization_non_admin_forbidden(db_session, regular_teacher):
    """Non-admin cannot create organization"""

    login_response = client.post(
        "/api/auth/login",
        json={"email": regular_teacher.email, "password": "regular_password"}
    )
    admin_token = login_response.json()["access_token"]

    response = client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Org",
            "owner_email": regular_teacher.email
        }
    )

    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


def test_create_organization_owner_not_found(db_session, admin_teacher):
    """Cannot create organization with non-existent owner email"""

    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_teacher.email, "password": "admin_password"}
    )
    admin_token = login_response.json()["access_token"]

    response = client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "Test Org",
            "owner_email": "nonexistent@example.com"
        }
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_organization_duplicate_name(db_session, admin_teacher, regular_teacher):
    """Cannot create organization with duplicate name"""

    # Create first org
    login_response = client.post(
        "/api/auth/login",
        json={"email": admin_teacher.email, "password": "admin_password"}
    )
    admin_token = login_response.json()["access_token"]

    client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Duplicate Org", "owner_email": regular_teacher.email}
    )

    # Try to create duplicate
    response = client.post(
        "/api/admin/organizations",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Duplicate Org", "owner_email": regular_teacher.email}
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()
```

**Step 3: Run test to verify it fails**

Run:
```bash
cd backend
pytest tests/test_admin_organizations.py::test_create_organization_as_admin_success -v
```

Expected: FAIL with "404 Not Found" (endpoint doesn't exist yet)

**Step 4: Implement the endpoint**

In `backend/routers/admin.py`, add new endpoint:

```python
@router.post(
    "/organizations",
    response_model=AdminOrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization and assign owner (Admin only)",
)
async def create_organization_as_admin(
    org_data: AdminOrganizationCreate,
    current_admin: Teacher = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new organization and assign an existing registered teacher as org_owner.

    **Admin only endpoint.**

    Requirements:
    - Caller must have is_admin = True
    - owner_email must exist in database
    - owner_email must be verified (is_verified = True)
    - Organization name must be unique

    This endpoint:
    1. Validates owner email exists and is verified
    2. Creates organization with provided info
    3. Creates TeacherOrganization record with role="org_owner"
    4. Adds Casbin role for authorization

    Returns organization ID and owner info.
    """

    # Validate owner exists and is verified
    owner = db.query(Teacher).filter(
        Teacher.email == org_data.owner_email,
        Teacher.is_verified == True
    ).first()

    if not owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with email {org_data.owner_email} not found or not verified. "
                   "Owner must be a registered and verified user."
        )

    # Check duplicate organization name
    existing_org = db.query(Organization).filter(
        Organization.name == org_data.name
    ).first()

    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with name '{org_data.name}' already exists."
        )

    # Create organization
    new_org = Organization(
        id=str(uuid.uuid4()),
        name=org_data.name,
        display_name=org_data.display_name,
        description=org_data.description,
        tax_id=org_data.tax_id,
        teacher_limit=org_data.teacher_limit,
        contact_email=org_data.contact_email,
        contact_phone=org_data.contact_phone,
        address=org_data.address,
        is_active=True,
    )

    db.add(new_org)
    db.flush()  # Get org.id for next step

    # Create TeacherOrganization with org_owner role
    teacher_org = TeacherOrganization(
        teacher_id=owner.id,
        organization_id=new_org.id,
        role="org_owner",
        is_active=True,
    )

    db.add(teacher_org)

    # Add Casbin role
    casbin_service = CasbinService()
    casbin_service.add_role_for_user(
        user=str(owner.id),
        role="org_owner",
        domain=new_org.id
    )

    db.commit()
    db.refresh(new_org)

    return AdminOrganizationResponse(
        organization_id=new_org.id,
        organization_name=new_org.name,
        owner_email=owner.email,
        owner_id=owner.id,
        message=f"Organization created successfully. Owner {owner.email} has been assigned org_owner role."
    )
```

**Step 5: Run test to verify it passes**

Run:
```bash
pytest tests/test_admin_organizations.py -v
```

Expected: All 4 tests PASS

**Step 6: Manual API test**

Run:
```bash
# Start backend
cd backend
uvicorn main:app --reload

# In another terminal, test the endpoint
curl -X POST "http://localhost:8000/api/admin/organizations" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manual Test Org",
    "display_name": "手動測試機構",
    "tax_id": "87654321",
    "teacher_limit": 5,
    "owner_email": "existing_user@example.com"
  }'
```

Expected: 201 Created with organization details

**Step 7: Commit**

```bash
git add backend/routers/admin.py backend/tests/test_admin_organizations.py
git commit -m "feat: add admin endpoint to create organization and assign owner"
```

---

## Task 3: Frontend - Create Admin Organization Page

**Files:**
- Create: `frontend/src/pages/admin/CreateOrganization.tsx`
- Create: `frontend/src/types/admin.ts`

**Step 1: Create TypeScript types**

Create `frontend/src/types/admin.ts`:

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
}

export interface AdminOrganizationCreateResponse {
  organization_id: string;
  organization_name: string;
  owner_email: string;
  owner_id: number;
  message: string;
}
```

**Step 2: Create admin organization page**

Create `frontend/src/pages/admin/CreateOrganization.tsx`:

```typescript
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Grid,
  Divider,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import apiClient from "../../services/apiClient";
import {
  AdminOrganizationCreateRequest,
  AdminOrganizationCreateResponse,
} from "../../types/admin";

interface FormData {
  name: string;
  display_name: string;
  description: string;
  tax_id: string;
  teacher_limit: number | null;
  contact_email: string;
  contact_phone: string;
  address: string;
  owner_email: string;
}

const CreateOrganization: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<FormData>();

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Prepare request data
      const requestData: AdminOrganizationCreateRequest = {
        name: data.name,
        display_name: data.display_name || undefined,
        description: data.description || undefined,
        tax_id: data.tax_id || undefined,
        teacher_limit: data.teacher_limit || undefined,
        contact_email: data.contact_email || undefined,
        contact_phone: data.contact_phone || undefined,
        address: data.address || undefined,
        owner_email: data.owner_email,
      };

      // Call API
      const response = await apiClient.post<AdminOrganizationCreateResponse>(
        "/api/admin/organizations",
        requestData
      );

      setSuccess(
        `機構創建成功！機構名稱：${response.organization_name}，擁有人：${response.owner_email}`
      );
      reset();

      // Redirect after 2 seconds
      setTimeout(() => {
        navigate("/admin/organizations");
      }, 2000);
    } catch (err: any) {
      console.error("Failed to create organization:", err);

      if (err.response?.status === 403) {
        setError("權限不足：您必須是平台管理員才能創建機構");
      } else if (err.response?.status === 404) {
        setError("找不到指定的擁有人 Email，請確認該用戶已註冊並完成驗證");
      } else if (err.response?.status === 400) {
        setError(
          err.response.data?.detail || "創建失敗：機構名稱可能已存在"
        );
      } else {
        setError("創建機構失敗，請稍後再試");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: "auto", p: 3 }}>
      <Typography variant="h4" gutterBottom>
        創建機構
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        平台管理員可以創建新機構並指定已註冊的老師為機構擁有人
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Card>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)}>
            {/* Basic Info Section */}
            <Typography variant="h6" gutterBottom>
              基本資訊
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="機構英文名稱 *"
                  {...register("name", {
                    required: "機構名稱為必填",
                    minLength: {
                      value: 1,
                      message: "機構名稱至少需要 1 個字元",
                    },
                    maxLength: {
                      value: 100,
                      message: "機構名稱不能超過 100 個字元",
                    },
                  })}
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="機構顯示名稱（中文）"
                  {...register("display_name", {
                    maxLength: {
                      value: 200,
                      message: "顯示名稱不能超過 200 個字元",
                    },
                  })}
                  error={!!errors.display_name}
                  helperText={errors.display_name?.message}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="機構描述"
                  multiline
                  rows={3}
                  {...register("description")}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="統一編號"
                  {...register("tax_id", {
                    maxLength: {
                      value: 20,
                      message: "統一編號不能超過 20 個字元",
                    },
                  })}
                  error={!!errors.tax_id}
                  helperText={errors.tax_id?.message}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="教師授權總數"
                  type="number"
                  {...register("teacher_limit", {
                    min: {
                      value: 1,
                      message: "教師授權總數至少為 1",
                    },
                  })}
                  error={!!errors.teacher_limit}
                  helperText={errors.teacher_limit?.message}
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            {/* Contact Info Section */}
            <Typography variant="h6" gutterBottom>
              聯絡資訊
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="聯絡 Email"
                  type="email"
                  {...register("contact_email", {
                    pattern: {
                      value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                      message: "請輸入有效的 Email 格式",
                    },
                  })}
                  error={!!errors.contact_email}
                  helperText={errors.contact_email?.message}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="聯絡電話"
                  {...register("contact_phone", {
                    maxLength: {
                      value: 50,
                      message: "聯絡電話不能超過 50 個字元",
                    },
                  })}
                  error={!!errors.contact_phone}
                  helperText={errors.contact_phone?.message}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="地址"
                  {...register("address")}
                />
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            {/* Owner Assignment Section */}
            <Typography variant="h6" gutterBottom>
              機構擁有人
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              請輸入已註冊並完成驗證的老師 Email。該老師將被指派為機構擁有人（org_owner）。
            </Alert>

            <TextField
              fullWidth
              label="擁有人 Email *"
              type="email"
              {...register("owner_email", {
                required: "擁有人 Email 為必填",
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: "請輸入有效的 Email 格式",
                },
              })}
              error={!!errors.owner_email}
              helperText={
                errors.owner_email?.message ||
                "請確認該 Email 已在平台註冊並完成驗證"
              }
            />

            <Box sx={{ mt: 3, display: "flex", gap: 2 }}>
              <Button
                type="submit"
                variant="contained"
                disabled={loading}
                startIcon={loading && <CircularProgress size={20} />}
              >
                {loading ? "創建中..." : "創建機構"}
              </Button>

              <Button
                variant="outlined"
                onClick={() => navigate("/admin/organizations")}
                disabled={loading}
              >
                取消
              </Button>
            </Box>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CreateOrganization;
```

**Step 3: Add route**

In `frontend/src/App.tsx`, add the new route:

```typescript
import CreateOrganization from "./pages/admin/CreateOrganization";

// In the Routes section:
<Route
  path="/admin/organizations/create"
  element={
    <PrivateRoute>
      <CreateOrganization />
    </PrivateRoute>
  }
/>
```

**Step 4: Manual browser test**

1. Start frontend: `npm run dev`
2. Login as admin user
3. Navigate to `/admin/organizations/create`
4. Fill in form with:
   - 機構英文名稱: "Test Org"
   - 機構顯示名稱: "測試機構"
   - 統一編號: "12345678"
   - 教師授權總數: 10
   - 擁有人 Email: (existing registered user email)
5. Click "創建機構"

Expected: Success message appears, redirects after 2 seconds

**Step 5: Test error cases**

1. Try with non-existent owner_email → See error: "找不到指定的擁有人 Email"
2. Try with duplicate org name → See error: "創建失敗：機構名稱可能已存在"
3. Login as non-admin user and navigate to page → See error: "權限不足"

**Step 6: Commit**

```bash
git add frontend/src/pages/admin/CreateOrganization.tsx \
        frontend/src/types/admin.ts \
        frontend/src/App.tsx
git commit -m "feat: add admin UI for organization creation"
```

---

## Task 4: Add Admin Navigation Link

**Files:**
- Modify: `frontend/src/components/Navigation.tsx` (or similar nav component)

**Step 1: Add navigation link**

In the admin section of your navigation component, add:

```typescript
{currentUser?.is_admin && (
  <MenuItem onClick={() => navigate("/admin/organizations/create")}>
    <ListItemIcon>
      <BusinessIcon fontSize="small" />
    </ListItemIcon>
    <ListItemText primary="創建機構" />
  </MenuItem>
)}
```

**Step 2: Test navigation**

1. Login as admin
2. Check that "創建機構" link appears in admin menu
3. Click link → Navigates to create organization page
4. Login as non-admin → Link should NOT appear

**Step 3: Commit**

```bash
git add frontend/src/components/Navigation.tsx
git commit -m "feat: add navigation link for admin organization creation"
```

---

## Task 5: Documentation and Testing

**Files:**
- Create: `docs/admin/organization-creation-guide.md`
- Modify: `README.md` (add link to new doc)

**Step 1: Create admin guide**

Create `docs/admin/organization-creation-guide.md`:

```markdown
# Admin Organization Creation Guide

## Overview

Platform administrators can create organizations and assign existing registered teachers as organization owners through the admin interface.

## Prerequisites

- User must have `is_admin = True` in database
- Owner must be already registered and verified (`is_verified = True`)

## Steps

### 1. Access Admin Panel

Navigate to: `/admin/organizations/create`

Or click: **Admin Menu → 創建機構**

### 2. Fill Organization Information

**Required Fields:**
- 機構英文名稱 (Organization Name)
- 擁有人 Email (Owner Email - must exist)

**Optional Fields:**
- 機構顯示名稱 (Display Name)
- 機構描述 (Description)
- 統一編號 (Tax ID)
- 教師授權總數 (Teacher Limit)
- Contact Information (email, phone, address)

### 3. Submit

Click "創建機構" button.

### 4. Verification

After successful creation:
- Organization appears in organization list
- Owner can login and see organization in workspace switcher
- Owner has `org_owner` role with full permissions

## API Reference

### Endpoint

```
POST /api/admin/organizations
```

**Authentication:** Admin only (`is_admin = True`)

**Request Body:**
```json
{
  "name": "ABC Education",
  "display_name": "ABC 教育集團",
  "description": "Professional English education",
  "tax_id": "12345678",
  "teacher_limit": 10,
  "contact_email": "contact@abc.edu.tw",
  "contact_phone": "02-1234-5678",
  "address": "台北市信義區信義路五段7號",
  "owner_email": "wang@abc.edu.tw"
}
```

**Response:**
```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_name": "ABC Education",
  "owner_email": "wang@abc.edu.tw",
  "owner_id": 42,
  "message": "Organization created successfully."
}
```

## Error Handling

| Status Code | Error | Solution |
|-------------|-------|----------|
| 403 | Admin access required | User must have `is_admin = True` |
| 404 | Owner email not found | Verify owner is registered and verified |
| 400 | Organization name exists | Choose different name |

## Testing

Run backend tests:
```bash
cd backend
pytest tests/test_admin_organizations.py -v
```

## Related Documentation

- [Organization Specification](../spec/features/organization/機構設定與擁有人註冊.feature)
- [RBAC Permissions](../backend/docs/RBAC_PERMISSIONS.md)
```

**Step 2: Update README**

In `README.md`, add to "Admin Features" section:

```markdown
### Admin Features

- [Organization Creation Guide](docs/admin/organization-creation-guide.md) - Create organizations and assign owners
```

**Step 3: Run full test suite**

```bash
# Backend
cd backend
pytest tests/test_admin_organizations.py -v

# Frontend type check
cd frontend
npm run typecheck

# Frontend lint
npm run lint
```

Expected: All tests pass, no type errors, no lint errors

**Step 4: Commit**

```bash
git add docs/admin/organization-creation-guide.md README.md
git commit -m "docs: add admin organization creation guide"
```

---

## Verification Checklist

Before marking complete:

- [ ] Backend endpoint `POST /api/admin/organizations` works
- [ ] Admin permission check enforces `is_admin = True`
- [ ] Owner email validation works (must exist and be verified)
- [ ] Organization creation assigns org_owner role
- [ ] Casbin role added successfully
- [ ] Frontend form validates all required fields
- [ ] Frontend displays success/error messages
- [ ] Frontend redirects after successful creation
- [ ] Navigation link visible only to admins
- [ ] All backend tests pass (4 tests)
- [ ] Frontend type check passes
- [ ] Frontend lint passes
- [ ] Documentation complete and accurate
- [ ] Owner can login and see organization in workspace switcher

## Out of Scope (Future Issues)

The following features are **NOT** included in this implementation:

1. **Points Mechanism**
   - `total_points` field not implemented
   - Will be separate issue: "Organization Points System"

2. **Unregistered Owner Flow**
   - Verification email sending
   - Password setup flow
   - Owner registration wizard
   - Will be added in Phase 2 if needed

3. **Project Staff Assignment**
   - `org_admin` role assignment
   - Will be separate feature when org management UI is built

4. **Organization Management UI**
   - List organizations
   - Edit organization
   - Deactivate organization
   - Will be separate admin dashboard feature

---

## Execution Handoff

Plan complete and saved to `docs/plans/2026-01-29-admin-organization-creation.md`.

**Two execution options:**

1. **Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

2. **Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
