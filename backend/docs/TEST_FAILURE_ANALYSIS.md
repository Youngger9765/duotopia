# Organization Hierarchy Integration Tests - Failure Analysis

## 🔴 Test Failure Summary

**Date**: 2025-11-27
**Branch**: `feature/multi-tenant-organization-hierarchy`
**Total Tests**: 42
**Failed**: 24
**Passed**: 18
**Pass Rate**: 42.9%

---

## 📊 Failure Breakdown

### ✅ Passing Tests (18)

**Organization API (2/11)**:
- `test_create_organization_success` ✅
- `test_create_organization_auto_assign_owner` ✅

**School API (3/12)**:
- Tests that create data within the test function

**Teacher Relations API (0/8)**:
- All failed (查詢類測試)

**Casbin Integration (0/10)**:
- All failed (資料依賴問題)

---

## 🔍 Root Cause Analysis

### Primary Issue: Fixture Data Clearing

**Location**: `tests/conftest.py:89-95`

```python
# 🔧 清理所有資料（保留 schema）
try:
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()
except Exception:
    session.rollback()
```

**Problem**:
- `shared_test_session` fixture runs at **function scope**
- On initialization, it **deletes all data** from all tables
- Fixtures that depend on `shared_test_session` create data **before** the test runs
- But the test itself sees an **empty database** because data was cleared

**Execution Order**:
```
1. shared_test_session created → 🗑️ DELETE all data
2. test_teacher fixture runs → ✅ INSERT teacher
3. test_org fixture runs → ✅ INSERT org + teacher_org
4. 🔥 Test starts → Query returns []  (WHY?!)
```

**Why it fails**:
The issue is that each fixture gets its own session instance, but they all share the same database connection. When `shared_test_session` clears data, it affects all subsequent operations.

---

## 🛠️ Solution Strategies

### Strategy 1: Self-Contained Tests (Recommended)

Each test creates its own data within the test function:

```python
def test_list_organizations_as_owner(self, test_client, shared_test_session):
    # Create teacher
    teacher = Teacher(email="test@example.com", ...)
    shared_test_session.add(teacher)
    shared_test_session.commit()

    # Create org
    org = Organization(name="Test Org", ...)
    shared_test_session.add(org)
    shared_test_session.commit()

    # Create relationship
    teacher_org = TeacherOrganization(teacher_id=teacher.id, organization_id=org.id, ...)
    shared_test_session.add(teacher_org)
    shared_test_session.commit()

    # Generate token
    token = create_access_token({"sub": str(teacher.id), "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # NOW test the query
    response = test_client.get("/api/organizations", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
```

**Pros**:
- ✅ Each test is independent
- ✅ No fixture dependency issues
- ✅ Easy to understand test flow

**Cons**:
- ❌ More verbose
- ❌ Code duplication

---

### Strategy 2: Helper Functions

Create reusable helper functions to reduce duplication:

```python
def create_test_org_with_owner(session):
    """Helper to create org with owner"""
    teacher = Teacher(email=f"test_{uuid.uuid4().hex[:8]}@example.com", ...)
    session.add(teacher)
    session.flush()

    org = Organization(name=f"Test Org {uuid.uuid4().hex[:8]}", ...)
    session.add(org)
    session.flush()

    teacher_org = TeacherOrganization(teacher_id=teacher.id, organization_id=org.id, ...)
    session.add(teacher_org)
    session.commit()

    return teacher, org

def test_list_organizations(test_client, shared_test_session):
    teacher, org = create_test_org_with_owner(shared_test_session)
    token = create_access_token({"sub": str(teacher.id), "type": "teacher"})

    response = test_client.get("/api/organizations", headers={"Authorization": f"Bearer {token}"})
    assert len(response.json()) >= 1
```

**Pros**:
- ✅ Reusable code
- ✅ Still independent tests
- ✅ Less verbose than Strategy 1

**Cons**:
- ⚠️ Need to maintain helper functions

---

### Strategy 3: Fix Fixture Scope (NOT Recommended)

Change fixtures to `session` scope:

```python
@pytest.fixture(scope="session")
def test_teacher(shared_test_session: Session):
    ...
```

**Pros**:
- Minimal code changes

**Cons**:
- ❌ Tests become interdependent
- ❌ Harder to debug failures
- ❌ Not true unit/integration tests

---

## 📝 Recommended Action Plan

### Phase 1: Refactor Test Structure (Priority: HIGH)

1. **Create helper module** (`tests/integration/api/helpers.py`)
   - `create_teacher(session, **kwargs)`
   - `create_org_with_owner(session, teacher=None, **kwargs)`
   - `create_school(session, org_id, **kwargs)`
   - `create_teacher_org_relation(session, teacher_id, org_id, role)`
   - `create_teacher_school_relation(session, teacher_id, school_id, roles)`

2. **Refactor failing tests** to use helpers:
   - Organization API: 9 tests
   - School API: 9 tests
   - Teacher Relations API: 8 tests

3. **Update Casbin tests** to create own data

### Phase 2: Verify & Document (Priority: MEDIUM)

1. **Run all tests**: `pytest tests/integration/api/ -v`
2. **Verify 100% pass rate**
3. **Update** `TESTING_GUIDE.md` with best practices

### Phase 3: CI/CD Integration (Priority: LOW)

1. Add test coverage reporting
2. Set minimum coverage threshold (80%)
3. Block PR merge if tests fail

---

## 📌 Quick Fix Example

**Before** (Failing):
```python
def test_list_organizations_as_owner(self, test_client, auth_headers, test_org):
    response = test_client.get("/api/organizations", headers=auth_headers)
    assert len(response.json()) >= 1  # ❌ FAILS - returns []
```

**After** (Passing):
```python
def test_list_organizations_as_owner(self, test_client, shared_test_session):
    # Create test data
    teacher = Teacher(email="test@example.com", password_hash="hash", name="Test", is_active=True)
    shared_test_session.add(teacher)
    shared_test_session.commit()

    org = Organization(name="Test Org", is_active=True)
    shared_test_session.add(org)
    shared_test_session.commit()

    teacher_org = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org.id,
        role="org_owner",
        is_active=True
    )
    shared_test_session.add(teacher_org)
    shared_test_session.commit()

    # Create auth token
    token = create_access_token({"sub": str(teacher.id), "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Test the API
    response = test_client.get("/api/organizations", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1  # ✅ PASSES
    assert data[0]["name"] == "Test Org"
```

---

## 🎯 Expected Outcome

After refactoring:
- ✅ All 42 tests passing
- ✅ 100% test independence
- ✅ Clear test structure
- ✅ Easy to maintain

---

## 📚 References

- [Pytest Fixtures Best Practices](https://docs.pytest.org/en/stable/fixture.html#scope-sharing-fixtures-across-classes-modules-packages-or-session)
- [SQLAlchemy Testing Patterns](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

**Status**: 🔴 **Action Required**
**Owner**: Development Team
**Due**: Before merging to `develop`
