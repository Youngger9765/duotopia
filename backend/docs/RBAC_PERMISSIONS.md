# RBAC 權限規劃

## 角色定義

### 1. org_owner（機構擁有人）
- **人數限制**: 1 人
- **Domain**: `org-{organization_id}`
- **完整權限**: 對整個機構及所有分校有完全控制權

### 2. org_admin（機構管理人）
- **人數限制**: 無限制
- **Domain**: `org-{organization_id}`
- **管理權限**: 對整個機構及所有分校有管理權，但無法管理訂閱

### 3. school_admin（分校校長）
- **人數限制**: 無限制
- **Domain**: `school-{school_id}`
- **學校權限**: 對特定分校有完全管理權

### 4. teacher（分校老師）
- **人數限制**: 無限制
- **Domain**: `school-{school_id}`
- **教學權限**: 僅有教學相關功能，無管理權限

---

## 權限矩陣

| 權限功能 | org_owner | org_admin | school_admin | teacher |
|---------|-----------|-----------|--------------|---------|
| **人數限制** | 1 | 無限制 | 無限制 | 無限制 |
| **新增/檢視/編輯其管理階層以下的老師資料及權限** | ✅ | ✅ | ✅ | ❌ |
| **新增機構公版課程** | ✅ | ✅ | ✅ | ❌ |
| **個人用戶教師的全功能** | ✅ | ✅ | ✅ | ✅ |
| **新增/檢視/編輯其管理階層以下的班級** | ✅ | ✅ | ✅ | ❌ |
| **新增/檢視/編輯其管理階層以下的學生資料** | ✅ | ✅ | ✅ | ❌ |
| **檢視其管理階層以下班級的作業** | ✅ | ✅ | ✅ | ✅ |
| **訂閱管理介面** | ✅ | ❌ | ❌ | ❌ |
| **進入所有分校** | ✅ | ✅ | ❌ | ❌ |

---

## Casbin 策略配置

### Model 定義 (`backend/config/casbin_model.conf`)

```ini
[request_definition]
r = sub, obj, act, dom

[policy_definition]
p = sub, obj, act, dom

[role_definition]
g = _, _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub, r.dom) && r.obj == p.obj && r.act == p.act && r.dom == p.dom
```

### 策略規則 (`backend/config/casbin_policy.csv`)

```csv
# Organization Owner Permissions
p, org_owner, organization, create, org-*
p, org_owner, organization, read, org-*
p, org_owner, organization, update, org-*
p, org_owner, organization, delete, org-*
p, org_owner, school, create, org-*
p, org_owner, school, read, org-*
p, org_owner, school, update, org-*
p, org_owner, school, delete, org-*
p, org_owner, teacher, create, org-*
p, org_owner, teacher, read, org-*
p, org_owner, teacher, update, org-*
p, org_owner, teacher, delete, org-*
p, org_owner, classroom, create, org-*
p, org_owner, classroom, read, org-*
p, org_owner, classroom, update, org-*
p, org_owner, classroom, delete, org-*
p, org_owner, student, create, org-*
p, org_owner, student, read, org-*
p, org_owner, student, update, org-*
p, org_owner, student, delete, org-*
p, org_owner, assignment, read, org-*
p, org_owner, subscription, manage, org-*

# Organization Admin Permissions (same as owner, except subscription)
p, org_admin, organization, read, org-*
p, org_admin, organization, update, org-*
p, org_admin, school, create, org-*
p, org_admin, school, read, org-*
p, org_admin, school, update, org-*
p, org_admin, school, delete, org-*
p, org_admin, teacher, create, org-*
p, org_admin, teacher, read, org-*
p, org_admin, teacher, update, org-*
p, org_admin, teacher, delete, org-*
p, org_admin, classroom, create, org-*
p, org_admin, classroom, read, org-*
p, org_admin, classroom, update, org-*
p, org_admin, classroom, delete, org-*
p, org_admin, student, create, org-*
p, org_admin, student, read, org-*
p, org_admin, student, update, org-*
p, org_admin, student, delete, org-*
p, org_admin, assignment, read, org-*

# School Admin Permissions
p, school_admin, school, read, school-*
p, school_admin, school, update, school-*
p, school_admin, teacher, create, school-*
p, school_admin, teacher, read, school-*
p, school_admin, teacher, update, school-*
p, school_admin, teacher, delete, school-*
p, school_admin, classroom, create, school-*
p, school_admin, classroom, read, school-*
p, school_admin, classroom, update, school-*
p, school_admin, classroom, delete, school-*
p, school_admin, student, create, school-*
p, school_admin, student, read, school-*
p, school_admin, student, update, school-*
p, school_admin, student, delete, school-*
p, school_admin, assignment, read, school-*

# Teacher Permissions
p, teacher, classroom, read, school-*
p, teacher, student, read, school-*
p, teacher, assignment, create, school-*
p, teacher, assignment, read, school-*
p, teacher, assignment, update, school-*
p, teacher, assignment, delete, school-*
```

---

## 權限檢查範例

### 1. Organization Owner 檢查

```python
from services.casbin_service import get_casbin_service

casbin_service = get_casbin_service()

# 檢查是否為機構擁有人
is_owner = casbin_service.has_role(
    teacher_id,
    "org_owner",
    f"org-{organization_id}"
)

# 檢查是否可以管理訂閱
can_manage_subscription = casbin_service.enforce(
    teacher_id,
    "subscription",
    "manage",
    f"org-{organization_id}"
)
```

### 2. School Admin 檢查

```python
# 檢查是否為分校校長
is_school_admin = casbin_service.has_role(
    teacher_id,
    "school_admin",
    f"school-{school_id}"
)

# 檢查是否可以創建班級
can_create_classroom = casbin_service.enforce(
    teacher_id,
    "classroom",
    "create",
    f"school-{school_id}"
)
```

### 3. 階層式權限檢查

```python
# org_owner 和 org_admin 可以進入所有分校
# 檢查是否可以訪問特定學校
def can_access_school(teacher_id: int, school_id: str, org_id: str) -> bool:
    casbin_service = get_casbin_service()

    # 檢查是否為機構層級角色（可訪問所有分校）
    is_org_level = (
        casbin_service.has_role(teacher_id, "org_owner", f"org-{org_id}") or
        casbin_service.has_role(teacher_id, "org_admin", f"org-{org_id}")
    )

    # 檢查是否為該分校的角色
    is_school_level = (
        casbin_service.has_role(teacher_id, "school_admin", f"school-{school_id}") or
        casbin_service.has_role(teacher_id, "teacher", f"school-{school_id}")
    )

    return is_org_level or is_school_level
```

---

## 資料表關係

### TeacherOrganization（教師-機構關係）
- 記錄教師在機構的角色
- `role`: `org_owner` 或 `org_admin`
- 用於判斷是否可以「進入所有分校」

### TeacherSchool（教師-學校關係）
- 記錄教師在特定分校的角色
- `roles`: JSONB 陣列，可包含 `["school_admin", "teacher"]`
- 支援多重角色（校長同時也是老師）

---

## 實作注意事項

### 1. org_owner 人數限制

在創建或更新 TeacherOrganization 時，檢查 org_owner 數量：

```python
def check_org_owner_limit(db: Session, organization_id: str, exclude_teacher_id: int = None):
    """確保只有一個 org_owner"""
    query = db.query(TeacherOrganization).filter(
        TeacherOrganization.organization_id == organization_id,
        TeacherOrganization.role == "org_owner",
        TeacherOrganization.is_active == True
    )

    if exclude_teacher_id:
        query = query.filter(TeacherOrganization.teacher_id != exclude_teacher_id)

    owner_count = query.count()

    if owner_count >= 1:
        raise HTTPException(
            status_code=400,
            detail="Organization already has an owner"
        )
```

### 2. 階層式權限繼承

org_owner 和 org_admin 自動擁有所有分校的權限：

```python
def get_accessible_schools(teacher_id: int, db: Session) -> List[School]:
    """取得教師可訪問的所有學校"""

    # 1. 取得教師的機構角色
    org_roles = db.query(TeacherOrganization).filter(
        TeacherOrganization.teacher_id == teacher_id,
        TeacherOrganization.role.in_(["org_owner", "org_admin"]),
        TeacherOrganization.is_active == True
    ).all()

    # 2. 如果是機構層級角色，返回該機構的所有學校
    if org_roles:
        org_ids = [r.organization_id for r in org_roles]
        return db.query(School).filter(
            School.organization_id.in_(org_ids),
            School.is_active == True
        ).all()

    # 3. 否則只返回有直接關係的學校
    school_roles = db.query(TeacherSchool).filter(
        TeacherSchool.teacher_id == teacher_id,
        TeacherSchool.is_active == True
    ).all()

    school_ids = [r.school_id for r in school_roles]
    return db.query(School).filter(
        School.id.in_(school_ids),
        School.is_active == True
    ).all()
```

### 3. Casbin 同步

當建立或更新角色關係時，同步更新 Casbin：

```python
# 建立 TeacherOrganization 時
casbin_service.add_role_for_user(
    teacher_id,
    "org_owner",  # or "org_admin"
    f"org-{organization_id}"
)

# 建立 TeacherSchool 時
for role in roles:  # roles = ["school_admin", "teacher"]
    casbin_service.add_role_for_user(
        teacher_id,
        role,
        f"school-{school_id}"
    )

# 刪除角色時
casbin_service.delete_role_for_user(
    teacher_id,
    role,
    f"org-{organization_id}"  # or f"school-{school_id}"
)
```

---

## API 權限裝飾器

建議實作一個統一的權限檢查裝飾器：

```python
from functools import wraps
from typing import List

def require_permission(
    resource: str,
    action: str,
    get_domain_from_request: callable
):
    """
    權限檢查裝飾器

    Usage:
        @require_permission("school", "create", lambda req: f"org-{req.organization_id}")
        async def create_school(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 取得當前教師
            teacher = kwargs.get("teacher") or kwargs.get("current_user")

            # 取得 domain
            domain = get_domain_from_request(kwargs)

            # 檢查權限
            casbin_service = get_casbin_service()
            if not casbin_service.enforce(teacher.id, resource, action, domain):
                raise HTTPException(
                    status_code=403,
                    detail=f"No permission to {action} {resource}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

使用範例：

```python
@router.post("/schools")
@require_permission(
    "school",
    "create",
    lambda kwargs: f"org-{kwargs['org_id']}"
)
async def create_school(
    org_id: str,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db)
):
    # 如果執行到這裡，表示權限檢查已通過
    ...
```

---

## 測試建議

### 1. 單元測試

測試每個角色的權限：

```python
def test_org_owner_can_manage_subscription():
    casbin_service.add_role_for_user(teacher_id, "org_owner", "org-123")
    assert casbin_service.enforce(teacher_id, "subscription", "manage", "org-123")

def test_org_admin_cannot_manage_subscription():
    casbin_service.add_role_for_user(teacher_id, "org_admin", "org-123")
    assert not casbin_service.enforce(teacher_id, "subscription", "manage", "org-123")

def test_school_admin_cannot_access_other_schools():
    casbin_service.add_role_for_user(teacher_id, "school_admin", "school-A")
    assert casbin_service.enforce(teacher_id, "classroom", "create", "school-A")
    assert not casbin_service.enforce(teacher_id, "classroom", "create", "school-B")
```

### 2. 整合測試

測試完整的工作流程：

```python
def test_org_owner_workflow():
    # 1. 創建機構
    org = create_organization(teacher_id)

    # 2. 驗證 org_owner 角色
    assert has_role(teacher_id, "org_owner", f"org-{org.id}")

    # 3. 創建分校
    school = create_school(teacher_id, org.id)

    # 4. 驗證可以訪問分校
    assert can_access_school(teacher_id, school.id, org.id)

    # 5. 添加分校老師
    add_teacher_to_school(teacher_id, school.id, new_teacher_id, ["teacher"])

    # 6. 驗證新老師只有 teacher 權限
    assert has_role(new_teacher_id, "teacher", f"school-{school.id}")
    assert not can_create_classroom(new_teacher_id, school.id)
```

---

## 參考資源

- [Casbin 官方文件](https://casbin.org/)
- [RBAC with Domains](https://casbin.org/docs/rbac-with-domains)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
