# Admin Organization Creation Guide

## Overview

Platform administrators can create organizations and assign existing registered teachers as organization owners through the admin interface.

## Prerequisites

- User must have `is_admin = True` in database
- Owner must be already registered and verified (`email_verified = True`)

## Steps

### 1. Access Admin Panel

Navigate to: `/admin/organizations/create`

Or click: **Admin Dashboard → 組織管理 Tab → 創建機構**

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
- Success toast message appears
- Automatically redirects to `/admin/organizations` after 2 seconds
- Organization is created in database
- Owner has `org_owner` role with full permissions in Casbin

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

**Response (201 Created):**
```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_name": "ABC Education",
  "owner_email": "wang@abc.edu.tw",
  "owner_id": 42,
  "message": "Organization created successfully. Owner wang@abc.edu.tw has been assigned org_owner role."
}
```

## Error Handling

| Status Code | Error | Solution |
|-------------|-------|----------|
| 403 | Admin access required | User must have `is_admin = True` |
| 404 | Owner email not found | Verify owner is registered and verified |
| 400 | Organization name exists | Choose different name |

## Testing

### Backend Tests

Run backend tests:
```bash
cd backend
pytest tests/test_admin_organizations.py -v
```

Expected output:
```
test_create_organization_as_admin_success PASSED
test_create_organization_non_admin_forbidden PASSED
test_create_organization_owner_not_found PASSED
test_create_organization_duplicate_name PASSED
```

### Manual Testing

1. Login as admin user
2. Navigate to Admin Dashboard → 組織管理 Tab
3. Click "創建機構" button
4. Fill in form with:
   - Name: "Test Organization"
   - Display Name: "測試機構"
   - Owner Email: (existing verified teacher email)
5. Submit form
6. Verify success message appears
7. Check database to verify organization created

## Implementation Details

### Database Tables Affected

- `organization`: New row created
- `teacher_organization`: New row linking teacher to organization with `org_owner` role
- Casbin policy: New role assignment for teacher in organization domain

### Backend Files

- `backend/routers/admin.py`: Endpoint implementation (line ~708)
- `backend/routers/schemas/admin_organization.py`: Request/response schemas
- `backend/tests/test_admin_organizations.py`: Test suite (4 tests)

### Frontend Files

- `frontend/src/pages/admin/CreateOrganization.tsx`: Form component
- `frontend/src/pages/admin/AdminDashboard.tsx`: Navigation tab
- `frontend/src/types/admin.ts`: TypeScript types
- `frontend/src/App.tsx`: Route configuration

## Related Documentation

- [ORG_IMPLEMENTATION_SPEC.md](../../ORG_IMPLEMENTATION_SPEC.md) - Full organization hierarchy specification
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - General testing guidelines
- Feature Spec: `spec/features/organization/機構設定與擁有人註冊.feature`

## Known Limitations

### Out of Scope (Future Issues)

The following features are **NOT** included in this implementation:

1. **Points Mechanism**
   - `total_points` field not implemented
   - Will be separate issue: "Organization Points System"

2. **Unregistered Owner Flow**
   - Cannot create organization with unregistered owner
   - Owner must already exist in `teacher` table
   - Will be added in Phase 2 if needed

3. **Organization Management UI**
   - List organizations (view all)
   - Edit organization details
   - Deactivate/delete organization
   - Will be separate admin dashboard feature

4. **Project Staff Assignment**
   - `org_admin` role assignment UI
   - Will be added when org management UI is built
