# Organization Hierarchy API Documentation

## Overview

The Organization Hierarchy system provides a multi-tenant architecture where:
- **Organizations** contain **Schools**
- **Schools** contain **Classrooms**
- **Teachers** can have roles at both Organization and School levels
- All access control is managed via Casbin RBAC with domain isolation

## Table of Contents

- [Roles & Permissions](#roles--permissions)
- [Organization APIs](#organization-apis)
- [School APIs](#school-apis)
- [Teacher-Organization Relationship APIs](#teacher-organization-relationship-apis)
- [Teacher-School Relationship APIs](#teacher-school-relationship-apis)
- [Data Models](#data-models)
- [Error Handling](#error-handling)

---

## Roles & Permissions

### Organization-Level Roles

| Role | Count Limit | Permissions | Description |
|------|-------------|-------------|-------------|
| **org_owner** | 1 per org | Full control + subscription management | The organization owner/founder |
| **org_admin** | Unlimited | Full control (except subscription) | Organization administrators |

### School-Level Roles

| Role | Count Limit | Permissions | Description |
|------|-------------|-------------|-------------|
| **school_admin** | Unlimited | School-level management | School principals/administrators |
| **teacher** | Unlimited | Teaching functions only | Regular teachers |

### Permission Matrix

| Action | org_owner | org_admin | school_admin | teacher |
|--------|-----------|-----------|--------------|---------|
| Create Organization | ✅ | ❌ | ❌ | ❌ |
| Update Organization | ✅ | ✅ | ❌ | ❌ |
| Delete Organization | ✅ | ❌ | ❌ | ❌ |
| Manage Subscription | ✅ | ❌ | ❌ | ❌ |
| Create School | ✅ | ✅ | ❌ | ❌ |
| Update School | ✅ | ✅ | ✅ | ❌ |
| Delete School | ✅ | ✅ | ❌ | ❌ |
| Add Org Members | ✅ | ❌ | ❌ | ❌ |
| Add School Teachers | ✅ | ✅ | ✅ | ❌ |
| Create Classroom | ✅ | ✅ | ✅ | ❌ |
| Manage Assignments | ✅ | ✅ | ✅ | ✅ |

### Materials Copy Rules

- Organization → School only (no direct org → classroom/teacher)
- School → Teacher / Classroom (requires school_admin or teacher role in that school)
- Teacher ↔ Classroom (same teacher only)
- Classroom ↔ Classroom (same teacher only)

---

## Organization APIs

### 1. Create Organization

Create a new organization. The creator automatically becomes `org_owner`.

**Endpoint:** `POST /api/organizations`

**Auth:** Bearer token (teacher)

**Request Body:**
```json
{
  "name": "duotopia-hq",
  "display_name": "Duotopia Headquarters",
  "description": "Main organization for Duotopia",
  "contact_email": "admin@duotopia.com",
  "contact_phone": "+886-2-1234-5678",
  "address": "Taipei, Taiwan"
}
```

**Response:** `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "duotopia-hq",
  "display_name": "Duotopia Headquarters",
  "description": "Main organization for Duotopia",
  "contact_email": "admin@duotopia.com",
  "contact_phone": "+886-2-1234-5678",
  "address": "Taipei, Taiwan",
  "is_active": true,
  "created_at": "2025-11-27T10:00:00Z",
  "updated_at": null
}
```

**Side Effects:**
- Creates `TeacherOrganization` record with role `org_owner`
- Adds Casbin policy: `g, <teacher_id>, org_owner, org-<org_id>`

---

### 2. List Organizations

Get all organizations that the current teacher has access to.

**Endpoint:** `GET /api/organizations`

**Auth:** Bearer token (teacher)

**Response:** `200 OK`
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "duotopia-hq",
    "display_name": "Duotopia Headquarters",
    "is_active": true,
    "created_at": "2025-11-27T10:00:00Z",
    "updated_at": null
  }
]
```

---

### 3. Get Organization Details

Get details of a specific organization.

**Endpoint:** `GET /api/organizations/{org_id}`

**Auth:** Bearer token (teacher with org membership)

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "duotopia-hq",
  "display_name": "Duotopia Headquarters",
  "description": "Main organization for Duotopia",
  "contact_email": "admin@duotopia.com",
  "contact_phone": "+886-2-1234-5678",
  "address": "Taipei, Taiwan",
  "is_active": true,
  "created_at": "2025-11-27T10:00:00Z",
  "updated_at": null
}
```

**Errors:**
- `404 Not Found` - Organization doesn't exist
- `403 Forbidden` - Teacher is not a member of this organization

---

### 4. Update Organization

Update organization details.

**Endpoint:** `PATCH /api/organizations/{org_id}`

**Auth:** Bearer token (org_owner or org_admin)

**Request Body:** (all fields optional)
```json
{
  "display_name": "Duotopia International",
  "description": "Updated description",
  "contact_email": "new-email@duotopia.com",
  "is_active": false
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "duotopia-hq",
  "display_name": "Duotopia International",
  "description": "Updated description",
  "contact_email": "new-email@duotopia.com",
  "is_active": false,
  "created_at": "2025-11-27T10:00:00Z",
  "updated_at": "2025-11-27T11:00:00Z"
}
```

---

### 5. Delete Organization (Soft Delete)

Mark organization as inactive.

**Endpoint:** `DELETE /api/organizations/{org_id}`

**Auth:** Bearer token (org_owner only)

**Response:** `200 OK`
```json
{
  "message": "Organization deleted successfully"
}
```

**Note:** This is a soft delete - sets `is_active = False`.

---

## School APIs

### 1. Create School

Create a new school within an organization.

**Endpoint:** `POST /api/schools`

**Auth:** Bearer token (org_owner or org_admin)

**Request Body:**
```json
{
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "taipei-branch",
  "display_name": "Duotopia Taipei Branch",
  "description": "Our Taipei location",
  "contact_email": "taipei@duotopia.com",
  "contact_phone": "+886-2-8888-9999",
  "address": "123 Xinyi Road, Taipei"
}
```

**Response:** `201 Created`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "taipei-branch",
  "display_name": "Duotopia Taipei Branch",
  "description": "Our Taipei location",
  "contact_email": "taipei@duotopia.com",
  "contact_phone": "+886-2-8888-9999",
  "address": "123 Xinyi Road, Taipei",
  "is_active": true,
  "created_at": "2025-11-27T10:30:00Z",
  "updated_at": null
}
```

**Errors:**
- `403 Forbidden` - Not org_owner or org_admin
- `404 Not Found` - Organization doesn't exist

---

### 2. List Schools

Get schools, optionally filtered by organization.

**Endpoint:** `GET /api/schools?organization_id={org_id}`

**Auth:** Bearer token (teacher)

**Query Parameters:**
- `organization_id` (optional) - Filter schools by organization

**Response:** `200 OK`
```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "taipei-branch",
    "display_name": "Duotopia Taipei Branch",
    "is_active": true,
    "created_at": "2025-11-27T10:30:00Z"
  }
]
```

---

### 3. Get School Details

Get details of a specific school.

**Endpoint:** `GET /api/schools/{school_id}`

**Auth:** Bearer token (teacher with school or org access)

**Response:** `200 OK`
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "taipei-branch",
  "display_name": "Duotopia Taipei Branch",
  "description": "Our Taipei location",
  "contact_email": "taipei@duotopia.com",
  "contact_phone": "+886-2-8888-9999",
  "address": "123 Xinyi Road, Taipei",
  "is_active": true,
  "created_at": "2025-11-27T10:30:00Z",
  "updated_at": null
}
```

---

### 4. Update School

Update school details.

**Endpoint:** `PATCH /api/schools/{school_id}`

**Auth:** Bearer token (org_owner, org_admin, or school_admin)

**Request Body:** (all fields optional)
```json
{
  "display_name": "Duotopia Taipei HQ",
  "contact_phone": "+886-2-9999-8888"
}
```

**Response:** `200 OK`

---

### 5. Delete School (Soft Delete)

Mark school as inactive.

**Endpoint:** `DELETE /api/schools/{school_id}`

**Auth:** Bearer token (org_owner or org_admin only)

**Response:** `200 OK`
```json
{
  "message": "School deleted successfully"
}
```

---

## Teacher-Organization Relationship APIs

### 1. List Organization Members

Get all teachers in an organization with their roles.

**Endpoint:** `GET /api/organizations/{org_id}/teachers`

**Auth:** Bearer token (org member)

**Response:** `200 OK`
```json
[
  {
    "id": 123,
    "email": "owner@duotopia.com",
    "name": "Alice Wang",
    "role": "org_owner",
    "is_active": true,
    "created_at": "2025-11-27T10:00:00Z"
  },
  {
    "id": 456,
    "email": "admin@duotopia.com",
    "name": "Bob Chen",
    "role": "org_admin",
    "is_active": true,
    "created_at": "2025-11-27T10:15:00Z"
  }
]
```

---

### 2. Add Teacher to Organization

Add a teacher to organization with specified role.

**Endpoint:** `POST /api/organizations/{org_id}/teachers`

**Auth:** Bearer token (org_owner only)

**Request Body:**
```json
{
  "teacher_id": 456,
  "role": "org_admin"
}
```

**Valid Roles:**
- `org_owner` (max 1 per organization)
- `org_admin` (unlimited)

**Response:** `201 Created`
```json
{
  "id": 1,
  "teacher_id": 456,
  "organization_id": "550e8400-e29b-41d4-a716-446655440000",
  "role": "org_admin",
  "is_active": true,
  "created_at": "2025-11-27T10:15:00Z"
}
```

**Side Effects:**
- Adds Casbin policy: `g, 456, org_admin, org-550e8400-e29b-41d4-a716-446655440000`

**Errors:**
- `400 Bad Request` - Organization already has an owner (when adding org_owner)
- `400 Bad Request` - Teacher already belongs to this organization
- `403 Forbidden` - Only org_owner can add teachers
- `404 Not Found` - Teacher doesn't exist

---

### 3. Remove Teacher from Organization

Remove a teacher from organization (soft delete).

**Endpoint:** `DELETE /api/organizations/{org_id}/teachers/{teacher_id}`

**Auth:** Bearer token (org_owner only)

**Response:** `200 OK`
```json
{
  "message": "Teacher removed from organization successfully"
}
```

**Side Effects:**
- Sets `is_active = False` on TeacherOrganization record
- Removes Casbin policy for this teacher-org relationship

---

## Teacher-School Relationship APIs

### 1. List School Teachers

Get all teachers in a school with their roles.

**Endpoint:** `GET /api/schools/{school_id}/teachers`

**Auth:** Bearer token (school or org member)

**Response:** `200 OK`
```json
[
  {
    "id": 789,
    "email": "principal@duotopia.com",
    "name": "Carol Lin",
    "roles": ["school_admin", "teacher"],
    "is_active": true,
    "created_at": "2025-11-27T10:45:00Z"
  },
  {
    "id": 101,
    "email": "teacher1@duotopia.com",
    "name": "David Wu",
    "roles": ["teacher"],
    "is_active": true,
    "created_at": "2025-11-27T11:00:00Z"
  }
]
```

**Note:** Teachers can have **multiple roles** at the school level (e.g., both school_admin and teacher).

---

### 2. Add Teacher to School

Add a teacher to school with specified roles.

**Endpoint:** `POST /api/schools/{school_id}/teachers`

**Auth:** Bearer token (org_owner, org_admin, or school_admin)

**Request Body:**
```json
{
  "teacher_id": 789,
  "roles": ["school_admin", "teacher"]
}
```

**Valid Roles:**
- `school_admin` (unlimited)
- `teacher` (unlimited)

**Response:** `201 Created`
```json
{
  "id": 1,
  "teacher_id": 789,
  "school_id": "660e8400-e29b-41d4-a716-446655440000",
  "roles": ["school_admin", "teacher"],
  "is_active": true,
  "created_at": "2025-11-27T10:45:00Z"
}
```

**Side Effects:**
- Adds Casbin policies for each role:
  - `g, 789, school_admin, school-660e8400-e29b-41d4-a716-446655440000`
  - `g, 789, teacher, school-660e8400-e29b-41d4-a716-446655440000`

**Errors:**
- `400 Bad Request` - Invalid role
- `400 Bad Request` - Teacher already belongs to this school
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Teacher or school doesn't exist

---

### 3. Update Teacher Roles in School

Update a teacher's roles in a school.

**Endpoint:** `PATCH /api/schools/{school_id}/teachers/{teacher_id}`

**Auth:** Bearer token (org_owner, org_admin, or school_admin)

**Request Body:**
```json
{
  "roles": ["teacher"]
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "teacher_id": 789,
  "school_id": "660e8400-e29b-41d4-a716-446655440000",
  "roles": ["teacher"],
  "is_active": true,
  "created_at": "2025-11-27T10:45:00Z"
}
```

**Side Effects:**
- Removes old Casbin policies
- Adds new Casbin policies for updated roles

---

### 4. Remove Teacher from School

Remove a teacher from school (soft delete).

**Endpoint:** `DELETE /api/schools/{school_id}/teachers/{teacher_id}`

**Auth:** Bearer token (org_owner, org_admin, or school_admin)

**Response:** `200 OK`
```json
{
  "message": "Teacher removed from school successfully"
}
```

**Side Effects:**
- Sets `is_active = False` on TeacherSchool record
- Removes all Casbin policies for this teacher-school relationship

---

## Data Models

### Organization

```typescript
{
  id: UUID,                    // Primary key
  name: string,                // Unique identifier (slug-like)
  display_name?: string,       // Human-readable name
  description?: string,
  contact_email?: string,
  contact_phone?: string,
  address?: string,
  settings?: JSON,             // Organization-specific settings
  is_active: boolean,
  created_at: datetime,
  updated_at?: datetime
}
```

### School

```typescript
{
  id: UUID,                    // Primary key
  organization_id: UUID,       // Foreign key → organizations.id
  name: string,                // School identifier
  display_name?: string,
  description?: string,
  contact_email?: string,
  contact_phone?: string,
  address?: string,
  settings?: JSON,             // School-specific settings
  is_active: boolean,
  created_at: datetime,
  updated_at?: datetime
}
```

### TeacherOrganization

```typescript
{
  id: integer,                 // Primary key
  teacher_id: integer,         // Foreign key → teachers.id
  organization_id: UUID,       // Foreign key → organizations.id
  role: string,                // 'org_owner' | 'org_admin'
  is_active: boolean,
  created_at: datetime,
  updated_at?: datetime
}
```

### TeacherSchool

```typescript
{
  id: integer,                 // Primary key
  teacher_id: integer,         // Foreign key → teachers.id
  school_id: UUID,             // Foreign key → schools.id
  roles: string[],             // Array: ['school_admin', 'teacher']
  is_active: boolean,
  created_at: datetime,
  updated_at?: datetime
}
```

---

## Error Handling

### Common HTTP Status Codes

- `200 OK` - Successful GET/PATCH/DELETE
- `201 Created` - Successful POST
- `400 Bad Request` - Invalid input (validation errors, business rule violations)
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Messages

**Organization:**
- `"Organization not found"`
- `"You don't have permission to access this organization"`
- `"Organization already has an owner"` (when adding 2nd org_owner)

**School:**
- `"School not found"`
- `"You don't have permission to manage schools in this organization"`

**Teachers:**
- `"Teacher not found"`
- `"Teacher already belongs to this organization"`
- `"Teacher already belongs to this school"`
- `"Only org_owner can add teachers to organization"`
- `"Invalid role: {role}. Must be one of {valid_roles}"`

---

## Casbin Integration

All permission checks are enforced via Casbin with domain-based policies:

### Domain Format

- **Organization domain:** `org-{organization_id}`
- **School domain:** `school-{school_id}`

### Example Policies

```csv
# Organization Owner
g, 123, org_owner, org-550e8400-e29b-41d4-a716-446655440000

# Organization Admin
g, 456, org_admin, org-550e8400-e29b-41d4-a716-446655440000

# School Admin + Teacher (multiple roles)
g, 789, school_admin, school-660e8400-e29b-41d4-a716-446655440000
g, 789, teacher, school-660e8400-e29b-41d4-a716-446655440000
```

### Permission Check Example

```python
# Check if teacher 123 has org_owner role for organization
casbin_service.has_role(123, "org_owner", "org-550e8400-e29b-41d4-a716-446655440000")
# Returns: True

# Check if teacher 789 can create classrooms (requires school_admin or org-level role)
casbin_service.has_role(789, "school_admin", "school-660e8400-e29b-41d4-a716-446655440000")
# Returns: True
```

---

## Hierarchical Permission Inheritance

- **org_owner** and **org_admin** automatically have access to all schools in their organization
- Permission checks cascade: org-level roles → school-level roles → classroom-level access
- Example: An `org_admin` can manage all schools and classrooms in their organization without explicit school membership

---

## Frontend Integration

### Navigation Flow

```
Organizations List
  ↓ (click org)
Organization Detail
  - View org info
  - Manage members (org_owner only)
  - List schools
  ↓ (manage schools)
School Management
  - Create school
  - View schools in org
  ↓ (click school)
School Detail
  - View school info
  - Manage teachers
  - List classrooms
```

### API Call Examples

```typescript
// Fetch organizations
const response = await fetch('/api/organizations', {
  headers: { 'Authorization': `Bearer ${token}` }
});
const organizations = await response.json();

// Create organization
const response = await fetch('/api/organizations', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'my-org',
    display_name: 'My Organization'
  })
});

// Fetch teachers in organization
const response = await fetch(`/api/organizations/${orgId}/teachers`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const teachers = await response.json();
```

---

## Migration & Database Schema

See `backend/alembic/versions/20251127_0047_5106b545b6d2_add_organization_hierarchy_tables.py` for complete schema definitions.

**Key Features:**
- UUID primary keys for organizations and schools
- CASCADE DELETE on foreign keys for referential integrity
- JSONB fields for flexible settings storage (PostgreSQL) / JSON (SQLite)
- Soft delete via `is_active` flags
- Timestamps for audit trails

---

## Testing

All APIs are covered by integration tests:

```bash
# Run organization tests
pytest tests/integration/api/test_organization_api.py -v

# Run school tests
pytest tests/integration/api/test_school_api.py -v

# Run teacher relationship tests
pytest tests/integration/api/test_teacher_relations_api.py -v
```

Test coverage includes:
- ✅ CRUD operations for organizations
- ✅ CRUD operations for schools
- ✅ Teacher-organization relationship management
- ✅ Teacher-school relationship management (multi-role support)
- ✅ Permission enforcement
- ✅ Casbin policy synchronization
- ✅ Business rule validation (e.g., 1 org_owner limit)

---

## Next Steps

- [ ] Add subscription management APIs for org_owner
- [ ] Implement student interface breadcrumbs (show org/school context)
- [ ] Add analytics/reporting at organization level
- [ ] Implement organization-wide settings (branding, themes)
- [ ] Add bulk import/export for schools and teachers

---

**Last Updated:** 2025-11-27
**Version:** 1.0.0
