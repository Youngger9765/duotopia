# Seed Data - Complete Test Scenarios

## 📋 Overview

The seed data (`backend/seed_data.py`) provides **comprehensive test scenarios** covering all organization hierarchy features and edge cases.

---

## 🏢 Organization Hierarchy Data

### 1. Duotopia 示範學校 (Main Organization)

**Organization Details**:
- Name: `duotopia-demo-school`
- Display Name: "Duotopia 示範學校"
- Contact: contact@duotopia.com, +886-2-1234-5678
- Address: 台北市信義區信義路五段7號
- Status: `is_active=True`

**Members**:
- **demo@duotopia.com**: `org_owner` (機構擁有人)
  - Has org-level access to ALL schools
  - Can manage organization settings
  - Can add/remove org members
- **trial@duotopia.com**: `org_admin` (機構管理員)
  - Has org-level access to ALL schools
  - Cannot modify organization settings
  - Can manage schools and teachers

**Schools Under This Organization**:

#### 1.1 台北分校 (Taipei Branch)
- Name: `taipei-branch`
- Display Name: "台北分校"
- Contact: taipei@duotopia.com, +886-2-8888-0001
- Address: 台北市大安區復興南路一段390號
- Status: `is_active=True`

**Teachers**:
- **demo@duotopia.com**: `["school_admin", "teacher"]` (校長兼教師)
  - Multi-role: Both school administrator AND teacher
  - Can manage school and teach classes

**Classrooms**:
- 五年級A班 (12 students)
- 六年級B班 (15 students)

#### 1.2 台中分校 (Taichung Branch)
- Name: `taichung-branch`
- Display Name: "台中分校"
- Contact: taichung@duotopia.com, +886-4-2222-0002
- Address: 台中市西區公益路68號
- Status: `is_active=True`

**Teachers**:
- **trial@duotopia.com**: `["teacher"]` (教師)
  - Only teaching role (not school admin)

**Classrooms**:
- 三年級C班 (0 students - for testing)

#### 1.3 舊分校 (Inactive School)
- Name: `old-branch`
- Display Name: "舊分校"
- Status: `is_active=False` ⚠️ **SOFT DELETED**

**Purpose**: Test soft delete behavior
- Should NOT appear in school listings
- Relationships still exist in database
- Can be reactivated by setting `is_active=True`

---

### 2. 測試機構 (Test Organization)

**Organization Details**:
- Name: `test-organization`
- Display Name: "測試機構"
- Contact: test@example.com
- Status: `is_active=True`

**Members**:
- **expired@duotopia.com**: `org_owner`

**Purpose**: Test cross-organization isolation
- Teachers from "Duotopia 示範學校" should NOT see this organization
- Teachers from this organization should NOT see "Duotopia 示範學校" data
- Validates domain-based permission isolation

---

## 🎯 Test Scenarios Covered

### Scenario 1: Permission Inheritance ✅
**Test**: org_owner/org_admin can access all schools

**Data**:
- demo teacher (org_owner) → can access both 台北分校 and 台中分校
- trial teacher (org_admin) → can access both 台北分校 and 台中分校

**Validation**:
```bash
# Login as demo teacher
GET /api/schools
# Should return: 台北分校, 台中分校 (but NOT 舊分校)
```

### Scenario 2: Multi-Role Support ✅
**Test**: Teacher can have multiple roles at same school

**Data**:
- demo teacher @ 台北分校: `["school_admin", "teacher"]`

**Validation**:
```bash
GET /api/schools/{taipei_school_id}/teachers
# demo teacher should have roles: ["school_admin", "teacher"]
```

### Scenario 3: School-Level Isolation ✅
**Test**: school_admin/teacher only sees their school

**Data**:
- trial teacher @ 台中分校: `["teacher"]` only
- No relationship to 台北分校

**Validation**:
```bash
# Login as trial teacher
GET /api/schools/{taipei_school_id}
# Should return 403 Forbidden (no access to Taipei school)
```

### Scenario 4: Cross-Organization Isolation ✅
**Test**: Teachers cannot access other organizations

**Data**:
- demo/trial teachers → "Duotopia 示範學校"
- expired teacher → "測試機構"

**Validation**:
```bash
# Login as demo teacher
GET /api/organizations
# Should return ONLY: "Duotopia 示範學校" (NOT "測試機構")

# Login as expired teacher
GET /api/organizations
# Should return ONLY: "測試機構" (NOT "Duotopia 示範學校")
```

### Scenario 5: Soft Delete Filtering ✅
**Test**: Inactive schools not in listings

**Data**:
- 舊分校: `is_active=False`

**Validation**:
```bash
GET /api/schools
# Should return: 台北分校, 台中分校
# Should NOT return: 舊分校
```

### Scenario 6: Classroom-School Linking ✅
**Test**: Classrooms correctly linked to schools

**Data**:
- 五年級A班, 六年級B班 → 台北分校
- 三年級C班 → 台中分校

**Validation**:
```bash
GET /api/schools/{taipei_school_id}/classrooms
# Should return: 五年級A班, 六年級B班

GET /api/schools/{taichung_school_id}/classrooms
# Should return: 三年級C班

GET /api/classrooms/{classroom_a_id}/school
# Should return: 台北分校
```

### Scenario 7: org_owner Uniqueness ✅
**Test**: Each organization has exactly 1 org_owner

**Data**:
- "Duotopia 示範學校": demo teacher (org_owner)
- "測試機構": expired teacher (org_owner)

**Validation**:
```sql
SELECT COUNT(*) FROM teacher_organizations
WHERE organization_id = {org_id}
  AND role = 'org_owner'
  AND is_active = TRUE;
-- Should return: 1
```

### Scenario 8: Casbin Role Synchronization ✅
**Test**: DB relationships sync with Casbin

**Data**:
- All teacher-org and teacher-school relationships have corresponding Casbin roles

**Validation**:
```python
from services.casbin_service import get_casbin_service
casbin = get_casbin_service()

# Check org_owner role
assert casbin.has_role(demo_teacher.id, "org_owner", f"org-{demo_org.id}") == True

# Check school_admin role
assert casbin.has_role(demo_teacher.id, "school_admin", f"school-{taipei_school.id}") == True
```

---

## 📊 Complete Data Summary

### Teachers (3 total)
1. **demo@duotopia.com**
   - org_owner @ Duotopia 示範學校
   - school_admin + teacher @ 台北分校
   - Has 2 classrooms: 五年級A班, 六年級B班

2. **trial@duotopia.com**
   - org_admin @ Duotopia 示範學校
   - teacher @ 台中分校
   - Has 1 classroom: 三年級C班

3. **expired@duotopia.com**
   - org_owner @ 測試機構
   - No schools (for isolation testing)

### Organizations (2 total)
1. Duotopia 示範學校 (active)
2. 測試機構 (active)

### Schools (3 total, 1 inactive)
1. 台北分校 (active) - 2 classrooms
2. 台中分校 (active) - 1 classroom
3. 舊分校 (inactive) - 0 classrooms

### Classrooms (3 total)
1. 五年級A班 → 台北分校 (12 students)
2. 六年級B班 → 台北分校 (15 students)
3. 三年級C班 → 台中分校 (0 students)

### Teacher-Organization Relationships (3 total)
1. demo → Duotopia 示範學校 (org_owner)
2. trial → Duotopia 示範學校 (org_admin)
3. expired → 測試機構 (org_owner)

### Teacher-School Relationships (2 total)
1. demo → 台北分校 ["school_admin", "teacher"]
2. trial → 台中分校 ["teacher"]

### Classroom-School Links (3 total)
1. 五年級A班 → 台北分校
2. 六年級B班 → 台北分校
3. 三年級C班 → 台中分校

---

## 🧪 How to Use for Testing

### 1. Reset Database with Seed Data
```bash
cd backend
python seed_data.py
```

### 2. Manual API Testing
```bash
# Start server
uvicorn main:app --reload

# Test organization listing
curl -H "Authorization: Bearer {demo_token}" \
  http://localhost:8000/api/organizations

# Test school listing
curl -H "Authorization: Bearer {demo_token}" \
  http://localhost:8000/api/schools

# Test cross-org isolation
curl -H "Authorization: Bearer {expired_token}" \
  http://localhost:8000/api/schools/{taipei_school_id}
# Should return 403 Forbidden
```

### 3. Automated Testing
```bash
# Run manual test script
python tests/manual_test_organization_hierarchy.py

# Run scenario tests
pytest tests/integration/test_organization_hierarchy_scenarios.py -v
```

---

## 🔍 Expected Query Results

### As demo@duotopia.com (org_owner):
```bash
GET /api/organizations
→ [Duotopia 示範學校]

GET /api/schools
→ [台北分校, 台中分校]  # NOT 舊分校 (inactive)

GET /api/schools/{taipei_id}/teachers
→ [{demo teacher, roles: ["school_admin", "teacher"]}]

GET /api/schools/{taipei_id}/classrooms
→ [五年級A班, 六年級B班]
```

### As trial@duotopia.com (org_admin):
```bash
GET /api/organizations
→ [Duotopia 示範學校]

GET /api/schools
→ [台北分校, 台中分校]

GET /api/schools/{taichung_id}/teachers
→ [{trial teacher, roles: ["teacher"]}]

GET /api/schools/{taichung_id}/classrooms
→ [三年級C班]
```

### As expired@duotopia.com (different org):
```bash
GET /api/organizations
→ [測試機構]  # NOT Duotopia 示範學校

GET /api/schools
→ []  # No schools in 測試機構 yet

GET /api/schools/{taipei_id}
→ 403 Forbidden  # Cannot access other org's schools
```

---

## ✅ Verification Checklist

After running seed data, verify:

- [ ] 2 organizations created
- [ ] 3 schools created (2 active, 1 inactive)
- [ ] 3 classrooms created and linked to schools
- [ ] 3 teacher-organization relationships
- [ ] 2 teacher-school relationships
- [ ] demo teacher has multi-role at 台北分校
- [ ] trial teacher has single role at 台中分校
- [ ] 舊分校 is soft deleted (is_active=False)
- [ ] Cross-org isolation works (expired teacher isolated)
- [ ] Casbin roles synchronized with DB relationships

---

## 🚀 Production Considerations

When deploying to production:

1. **Remove Test Data**: Delete "測試機構" and expired teacher
2. **Keep Demo Data**: Keep "Duotopia 示範學校" for demos
3. **Clean Up**: Remove inactive schools or reactivate them
4. **Verify Casbin**: Ensure all roles are synced with `casbin_service.load_policy()`

---

*Last Updated*: November 27, 2025
*Seed Data Version*: 2.0 (Enhanced with organization hierarchy)
