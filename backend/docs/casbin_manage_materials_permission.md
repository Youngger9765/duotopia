# Casbin `manage_materials` Permission

## Overview

The `manage_materials` permission has been added to the Casbin RBAC system to control access to organization-level materials management features.

## Permission Configuration

### Policy Definition

**File**: `/Users/young/project/duotopia/backend/config/casbin_policy.csv`

### Roles with `manage_materials` Permission

| Role | Domain | Permission | Action | Description |
|------|--------|------------|--------|-------------|
| `org_owner` | `org-*` | `manage_materials` | `write` | Full access to manage organization materials |
| `org_admin` | `org-*` | `manage_materials` | `write` | Can manage materials with proper role assignment |

### Roles WITHOUT `manage_materials` Permission

| Role | Reason |
|------|--------|
| `school_admin` | Materials management is organization-level only |
| `school_director` | Materials management is organization-level only |
| `teacher` | Regular teachers cannot manage organization materials |

## Usage in API Endpoints

### Example 1: Using Permission Decorator

```python
from services.permission_decorators import require_permission

@router.post("/api/organizations/{org_id}/programs")
@require_permission('manage_materials', 'write', domain_param='org_id')
async def create_organization_program(org_id: str):
    """
    Create an organization program/material

    Automatically checks if current user has manage_materials permission
    in the specified organization domain
    """
    # Implementation here
    pass
```

### Example 2: Manual Permission Check

```python
from services.casbin_service import get_casbin_service

def check_materials_access(teacher_id: int, org_id: str) -> bool:
    """
    Manually check if teacher can manage materials in organization
    """
    casbin = get_casbin_service()

    return casbin.check_permission(
        teacher_id=teacher_id,
        domain=f"org-{org_id}",
        resource="manage_materials",
        action="write"
    )
```

## Permission Behavior

### org_owner
- **Automatic**: Has `manage_materials` permission for their organization
- **No explicit grant needed**: Permission is inherent to the role
- **Scope**: Can manage materials across entire organization

### org_admin
- **Conditional**: Has `manage_materials` permission by role definition
- **Role assignment required**: Must be assigned `org_admin` role in organization
- **Scope**: Can manage materials in organizations where they have the role

### Multi-Organization Isolation

Teachers with `org_owner` or `org_admin` role in **Organization A** can:
- ✅ Manage materials in Organization A
- ❌ NOT manage materials in Organization B (different organization)

This ensures proper tenant isolation in the multi-tenant system.

## Testing

### Test Coverage

**File**: `/Users/young/project/duotopia/backend/tests/test_manage_materials_permission.py`

The following scenarios are tested:

1. ✅ org_owner can manage materials
2. ✅ org_admin can manage materials
3. ✅ school_admin CANNOT manage materials (org-level only)
4. ✅ Regular teacher CANNOT manage materials
5. ✅ Organizations are properly isolated

### Running Tests

```bash
# Run all manage_materials tests
python -m pytest tests/test_manage_materials_permission.py -v

# Run with coverage
python -m pytest tests/test_manage_materials_permission.py --cov=services.casbin_service
```

## Related Files

| File | Purpose |
|------|---------|
| `/Users/young/project/duotopia/backend/config/casbin_model.conf` | Casbin RBAC model definition |
| `/Users/young/project/duotopia/backend/config/casbin_policy.csv` | Permission policy definitions |
| `/Users/young/project/duotopia/backend/services/casbin_service.py` | Casbin service implementation |
| `/Users/young/project/duotopia/backend/services/permission_decorators.py` | Permission decorator utilities |
| `/Users/young/project/duotopia/backend/tests/test_manage_materials_permission.py` | Permission tests |

## Integration Checklist

When creating organization materials endpoints:

- [ ] Import Casbin service or decorators
- [ ] Use `require_permission('manage_materials', 'write', domain_param='org_id')`
- [ ] Ensure organization domain format: `org-{uuid}`
- [ ] Test with different roles (org_owner, org_admin, school_admin, teacher)
- [ ] Verify organization isolation (can't access other orgs' materials)

## Future Considerations

### Read-Only Access

Currently, `manage_materials` only defines `write` action. If read-only access is needed in the future:

```csv
# Add read permission for specific roles
p, teacher, *, manage_materials, read
```

### School-Level Materials

If school-level materials are needed (separate from org-level):

```csv
# Define school-level material permissions
p, school_admin, *, manage_school_materials, write
p, school_director, *, manage_school_materials, write
```

## References

- [Casbin Documentation](https://casbin.org/docs/)
- [RBAC with Domains](https://casbin.org/docs/rbac-with-domains/)
- [Project Casbin Usage Guide](/Users/young/project/duotopia/backend/services/CASBIN_USAGE.md)
