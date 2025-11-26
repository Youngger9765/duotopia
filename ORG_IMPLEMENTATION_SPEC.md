# 機構層級管理系統 - 前後端施工規格

> **基於**：`ORG_TODO.md` 的零破壞性架構設計
> **目標**：實作完整的機構/學校管理功能，同時保持向下相容

---

## 📋 目錄

1. [核心需求總覽](#核心需求總覽)
2. [現有架構分析](#現有架構分析)
3. [後端 API 設計](#後端-api-設計)
4. [資料庫 Migration](#資料庫-migration)
5. [前端 UI 設計](#前端-ui-設計)
6. [權限系統設計](#權限系統設計)
7. [金流整合](#金流整合)
8. [學生端改動](#學生端改動)
9. [實作順序](#實作順序)
10. [測試計畫](#測試計畫)

---

## 🎯 核心需求總覽

### 1. 後台管理（新增）

**機構管理者後台**：
- ✅ 管理所有學校（新增、編輯、停用）
- ✅ 管理所有老師（邀請、分配角色、跨校調動）
- ✅ 查看整個機構的成效（Dashboard）
- ✅ 查看所有課程（跨學校）
- ✅ 訂閱與金流管理（只有付費者）

**學校管理者後台**：
- ✅ 管理該校老師（邀請、分配角色）
- ✅ 查看該校成效（Dashboard）
- ✅ 查看該校所有班級與課程
- ❌ 無法管理其他學校
- ❌ 無法管理金流（由機構統一管理）

### 2. 前台共用（改良）

**設計原則**：
- ✅ 獨立工作者與機構老師使用**相同的前台介面**
- ✅ 根據 `organization.type` 和 `roles` 動態顯示功能
- ✅ 避免兩套完全不同的 UI
- ✅ 模組化設計，易於擴展

**差異點**：
```typescript
// 獨立工作者 (type=personal, roles=["teacher"])
- 看到：我的班級、我的學生、公版課程
- 看不到：機構管理、學校管理

// 機構老師 (type=organization, roles=["teacher"])
- 看到：我的班級、我的學生、公版課程、機構資訊
- 看不到：機構管理、學校管理

// 學校管理者 (type=organization, roles=["school_admin", "teacher"])
- 看到：我的班級、該校所有班級、該校老師管理、學校成效
- 看不到：機構管理、其他學校

// 機構管理者 (type=organization, roles=["org_owner"])
- 看到：所有功能（機構管理、所有學校、金流）
```

### 3. 金流限制

- ✅ 只有 `roles` 包含 `"org_owner"` 才能看到金流頁面
- ✅ 訂閱頁面顯示「請聯絡機構管理者」（非 org_owner）
- ✅ 獨立工作者（type=personal）正常顯示訂閱頁面

### 4. 學生端改動

**教室進入時顯示**：
```
上方麵包屑：
ABC 補習班 > 台北校區 > 國小英文班

或

王老師工作室 > 國小英文班  （獨立工作者，不顯示學校）
```

**學生 Sidebar 顯示**：
```
使用者資訊區域：
👤 小明
📚 國小英文班
🏫 台北校區（如果有）
🏢 ABC 補習班（如果有）
```

---

## 🔍 現有架構分析

### 前端架構

```
frontend/src/
├── pages/
│   ├── teacher/                    # 老師前台（需改良）
│   │   ├── TeacherDashboard.tsx    # 儀表板
│   │   ├── TeacherClassrooms.tsx   # 我的班級
│   │   ├── ClassroomDetail.tsx     # 班級詳情
│   │   ├── TeacherStudents.tsx     # 所有學生
│   │   ├── TeacherSubscription.tsx # 訂閱管理
│   │   └── TeacherProfile.tsx      # 個人資料
│   │
│   ├── student/                    # 學生前台（需改良）
│   │   ├── StudentDashboard.tsx    # 學生首頁
│   │   ├── StudentAssignmentList.tsx
│   │   └── StudentProfile.tsx
│   │
│   └── admin/                      # 系統管理（不動）
│       └── AdminDashboard.tsx
│
├── components/
│   ├── TeacherLayout.tsx           # 老師 Layout（需改良）
│   ├── StudentLayout.tsx           # 學生 Layout（需改良）
│   └── ...
│
└── lib/
    └── api.ts                      # API client（需擴充）
```

### 後端架構

```
backend/
├── models.py                       # ORM Models（需新增）
├── routes/
│   ├── teacher_routes.py           # 現有 API（不動）
│   ├── student_routes.py           # 現有 API（可能需調整）
│   └── organization_routes.py      # 新增：機構管理 API
│   └── school_routes.py            # 新增：學校管理 API
│
├── services/                       # 商業邏輯層（建議新增）
│   ├── organization_service.py
│   └── permission_service.py       # 權限檢查
│
└── migrations/                     # Alembic migrations
    └── versions/
        └── xxx_add_org_hierarchy.py
```

### 關鍵發現

1. **TeacherLayout** 已有動態選單邏輯（根據 `is_admin` 顯示）
   - ✅ 可擴充為根據 `roles` 動態顯示
   - ✅ 已有 sidebar collapse 功能

2. **StudentLayout** 顯示班級名稱但不顯示學校/機構
   - ⚠️ 需要新增機構/學校資訊顯示

3. **訂閱頁面** 已根據 `config.enablePayment` 動態顯示
   - ✅ 可擴充為同時檢查 `roles`

4. **現有 API** 都是以 `teacher_id` 為基礎查詢
   - ✅ 需要新增以 `organization_id` 和 `school_id` 查詢的 API
   - ✅ 舊 API 保持不變（向下相容）

---

## 🔌 後端 API 設計

### 1. 組織架構 API

#### 1.1 機構管理 API

```python
# GET /api/organizations/me
# 取得目前使用者所屬的機構
{
  "id": "uuid",
  "name": "ABC 補習班",
  "type": "organization",  # "personal" | "organization"
  "settings": {},
  "schools": [
    {"id": "uuid", "name": "台北校區"},
    {"id": "uuid", "name": "新竹校區"}
  ],
  "my_roles": ["org_owner"],  # 我在這個機構的角色
  "created_at": "2024-01-01T00:00:00Z"
}

# GET /api/organizations/{org_id}
# 取得機構詳情（需要 org_owner 或 school_admin 權限）
{
  "id": "uuid",
  "name": "ABC 補習班",
  "type": "organization",
  "schools_count": 5,
  "teachers_count": 30,
  "students_count": 500,
  "active_classrooms_count": 50,
  "schools": [...]
}

# POST /api/organizations/{org_id}/schools
# 新增學校（需要 org_owner 權限）
Request:
{
  "name": "高雄校區",
  "settings": {}
}
Response: School object

# PUT /api/organizations/{org_id}/schools/{school_id}
# 更新學校（需要 org_owner 權限）

# DELETE /api/organizations/{org_id}/schools/{school_id}
# 停用學校（軟刪除，需要 org_owner 權限）
```

#### 1.2 學校管理 API

```python
# GET /api/schools/{school_id}
# 取得學校詳情（需要該校 admin 或 org_owner）
{
  "id": "uuid",
  "name": "台北校區",
  "organization_id": "uuid",
  "organization_name": "ABC 補習班",
  "teachers_count": 8,
  "classrooms_count": 15,
  "students_count": 120,
  "teachers": [
    {
      "id": 123,
      "name": "王老師",
      "email": "wang@abc.com",
      "roles": ["teacher"],
      "classrooms_count": 3
    }
  ]
}

# GET /api/schools/{school_id}/classrooms
# 取得學校所有班級（需要該校 admin 或 org_owner）
[
  {
    "id": 1,
    "name": "國小英文班",
    "teacher_name": "王老師",
    "students_count": 20,
    "created_at": "2024-01-01T00:00:00Z"
  }
]

# GET /api/schools/{school_id}/teachers
# 取得學校所有老師（需要該校 admin 或 org_owner）

# POST /api/schools/{school_id}/teachers
# 邀請老師加入學校（需要該校 admin 或 org_owner）
Request:
{
  "email": "new@abc.com",
  "name": "新老師",
  "password": "temp123",  # 臨時密碼
  "roles": ["teacher"]     # ["teacher"] | ["school_admin", "teacher"]
}
Response: Teacher object

# PUT /api/schools/{school_id}/teachers/{teacher_id}/roles
# 更新老師角色（需要該校 admin 或 org_owner）
Request:
{
  "roles": ["school_admin", "teacher"]
}

# DELETE /api/schools/{school_id}/teachers/{teacher_id}
# 移除老師（軟刪除，需要 org_owner）
```

#### 1.3 權限與角色 API

```python
# GET /api/teachers/me/roles
# 取得我的所有角色（跨所有學校）
{
  "teacher_id": 123,
  "organization": {
    "id": "uuid",
    "name": "ABC 補習班",
    "type": "organization"
  },
  "roles_by_school": [
    {
      "school_id": null,
      "school_name": null,  # null = 機構層級
      "roles": ["org_owner"]
    },
    {
      "school_id": "uuid-taipei",
      "school_name": "台北校區",
      "roles": ["school_admin", "teacher"]
    },
    {
      "school_id": "uuid-hsinchu",
      "school_name": "新竹校區",
      "roles": ["teacher"]
    }
  ],
  "all_roles": ["org_owner", "school_admin", "teacher"]  # 合併後
}

# POST /api/teachers/{teacher_id}/transfer
# 老師調校（需要 org_owner）
Request:
{
  "from_school_id": "uuid-taipei",
  "to_school_id": "uuid-hsinchu",
  "keep_old_school": false  # true = 跨校任教，false = 完全調動
}
```

#### 1.4 成效與統計 API

```python
# GET /api/organizations/{org_id}/dashboard
# 機構總覽（需要 org_owner）
{
  "summary": {
    "total_schools": 5,
    "total_teachers": 30,
    "total_students": 500,
    "total_classrooms": 50,
    "active_assignments": 120
  },
  "schools_performance": [
    {
      "school_id": "uuid",
      "school_name": "台北校區",
      "students_count": 120,
      "avg_completion_rate": 0.85,
      "avg_score": 78.5
    }
  ],
  "top_teachers": [...],
  "recent_activities": [...]
}

# GET /api/schools/{school_id}/dashboard
# 學校總覽（需要該校 admin 或 org_owner）
{
  "summary": {
    "total_teachers": 8,
    "total_students": 120,
    "total_classrooms": 15,
    "active_assignments": 30
  },
  "classrooms_performance": [...],
  "top_students": [...],
  "recent_activities": [...]
}
```

### 2. 現有 API 調整

#### 2.1 Teacher Dashboard API（向下相容）

```python
# GET /api/teachers/dashboard
# 原有功能保持不變，新增機構資訊
{
  "teacher": {
    "id": 123,
    "email": "wang@abc.com",
    "name": "王老師",
    "is_demo": false,
    "is_active": true,
    "is_admin": false,
    # ✅ 新增欄位
    "organization": {
      "id": "uuid",
      "name": "ABC 補習班",
      "type": "organization"  # "personal" | "organization"
    },
    "schools": [
      {"id": "uuid", "name": "台北校區"},
      {"id": "uuid", "name": "新竹校區"}
    ],
    "roles": ["teacher"]  # 合併後的所有角色
  },
  "classrooms": [...],  # 不變
  "assignments": [...],  # 不變
  "stats": {...}  # 不變
}
```

#### 2.2 Student Login/Dashboard API

```python
# POST /api/students/login
# 新增回傳學校與機構資訊
Response:
{
  "token": "...",
  "student": {
    "id": 1,
    "name": "小明",
    "classroom_id": 1,
    "classroom_name": "國小英文班",
    # ✅ 新增欄位
    "school_name": "台北校區",       # 可能為 null（獨立工作者）
    "organization_name": "ABC 補習班"  # 可能為 null
  }
}

# GET /api/students/{student_id}/classroom
# 取得教室資訊時包含學校與機構
{
  "classroom": {
    "id": 1,
    "name": "國小英文班",
    "teacher_name": "王老師",
    # ✅ 新增欄位
    "school": {
      "id": "uuid",
      "name": "台北校區"
    },
    "organization": {
      "id": "uuid",
      "name": "ABC 補習班",
      "type": "organization"
    }
  }
}
```

### 3. 權限中介層設計（✅ 使用 Casbin）

> **⚠️ 更新**：我們決定使用 Casbin 作為權限管理框架
>
> - 完整評估報告：`CASBIN_EVALUATION.md`
> - 使用指南：`backend/services/CASBIN_USAGE.md`

#### 3.1 Casbin 配置

**backend/config/casbin_model.conf**:
```ini
[request_definition]
r = sub, dom, obj, act

[policy_definition]
p = sub, dom, obj, act

[role_definition]
g = _, _, _

[matchers]
m = g(r.sub, p.sub, r.dom) && (r.dom == p.dom || p.dom == "*") && r.obj == p.obj && r.act == p.act
```

**backend/config/casbin_policy.csv**:
```csv
# org_owner 權限
p, org_owner, *, manage_organization, write
p, org_owner, *, manage_schools, write
p, org_owner, *, manage_teachers, write
p, org_owner, *, view_analytics, read
p, org_owner, *, manage_billing, write

# school_admin 權限
p, school_admin, *, manage_teachers, write
p, school_admin, *, view_analytics, read
p, school_admin, *, manage_classrooms, write

# teacher 權限
p, teacher, *, manage_own_classrooms, write
p, teacher, *, view_students, read
```

#### 3.2 Casbin Service

**backend/services/casbin_service.py**:
```python
import casbin
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"
MODEL_PATH = str(CONFIG_DIR / "casbin_model.conf")
POLICY_PATH = str(CONFIG_DIR / "casbin_policy.csv")

class CasbinService:
    _instance = None
    _enforcer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._enforcer is None:
            self._enforcer = casbin.Enforcer(MODEL_PATH, POLICY_PATH)
            self._enforcer.load_policy()

    @property
    def enforcer(self):
        return self._enforcer

    def check_permission(self, teacher_id: int, domain: str, resource: str, action: str) -> bool:
        """
        檢查權限

        Args:
            teacher_id: 老師 ID
            domain: 'org-{uuid}' 或 'school-{uuid}'
            resource: 'manage_schools' | 'manage_teachers' | etc.
            action: 'read' | 'write'
        """
        return self.enforcer.enforce(str(teacher_id), domain, resource, action)

    def add_role_for_user(self, teacher_id: int, role: str, domain: str) -> bool:
        """新增角色"""
        success = self.enforcer.add_role_for_user_in_domain(
            str(teacher_id), role, domain
        )
        if success:
            self.enforcer.save_policy()
        return success

    def sync_from_database(self):
        """從 teacher_schools 表同步角色"""
        from models import TeacherSchool, TeacherOrganization, db

        self.enforcer.clear_policy()

        records = db.session.query(TeacherSchool).filter(
            TeacherSchool.is_active == True
        ).all()

        for record in records:
            if record.school_id:
                domain = f"school-{record.school_id}"
            else:
                org = db.session.query(TeacherOrganization).filter_by(
                    teacher_id=record.teacher_id,
                    is_active=True
                ).first()
                if org:
                    domain = f"org-{org.organization_id}"
                else:
                    continue

            for role in record.roles:
                self.add_role_for_user(record.teacher_id, role, domain)

# 全域 instance
casbin_service = None

def get_casbin_service():
    global casbin_service
    if casbin_service is None:
        casbin_service = CasbinService()
    return casbin_service

def init_casbin_service():
    global casbin_service
    casbin_service = CasbinService()
    # 可選：從資料庫同步
    # casbin_service.sync_from_database()
    return casbin_service
```

#### 3.3 權限 Decorator

**backend/services/permission_decorators.py**:
```python
from functools import wraps
from flask import request, jsonify
from typing import Optional
from services.casbin_service import get_casbin_service

def require_permission(
    resource: str,
    action: str = 'write',
    domain_param: Optional[str] = None
):
    """
    權限檢查裝飾器

    Examples:
        @require_permission('manage_schools', 'write', domain_param='org_id')
        def create_school(org_id):
            pass

        @require_permission('manage_teachers', 'write', domain_param='school_id')
        def invite_teacher(school_id):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            teacher_id = getattr(request, 'current_teacher_id', None)

            if not teacher_id:
                return jsonify({"error": "Unauthorized"}), 401

            # 決定 domain
            domain = _get_domain(domain_param, kwargs)

            if not domain:
                return jsonify({"error": "Bad Request"}), 400

            # 檢查權限
            casbin = get_casbin_service()

            if not casbin.check_permission(teacher_id, domain, resource, action):
                return jsonify({"error": "Permission Denied"}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def require_role(*roles, domain_param=None):
    """
    角色檢查裝飾器

    Examples:
        @require_role('org_owner', domain_param='org_id')
        def delete_organization(org_id):
            pass

        @require_role('org_owner', 'school_admin', domain_param='school_id')
        def update_school(school_id):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            teacher_id = getattr(request, 'current_teacher_id', None)

            if not teacher_id:
                return jsonify({"error": "Unauthorized"}), 401

            domain = _get_domain(domain_param, kwargs)

            if not domain:
                return jsonify({"error": "Bad Request"}), 400

            casbin = get_casbin_service()

            has_role = any(
                casbin.enforcer.has_role_for_user(str(teacher_id), role, domain)
                for role in roles
            )

            if not has_role:
                return jsonify({"error": "Permission Denied"}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

def _get_domain(domain_param, kwargs):
    """取得 domain"""
    if not domain_param:
        return None

    domain_value = kwargs.get(domain_param)
    if not domain_value:
        return None

    if domain_param == 'org_id' or domain_param == 'organization_id':
        return f"org-{domain_value}"
    elif domain_param == 'school_id':
        return f"school-{domain_value}"
    else:
        return f"school-{domain_value}"

# 簡化版裝飾器
def require_org_owner(domain_param=None):
    return require_role('org_owner', domain_param=domain_param)

def require_school_admin(domain_param):
    return require_role('org_owner', 'school_admin', domain_param=domain_param)
```

#### 3.4 使用範例

```python
# API routes

@app.route('/api/organizations/<org_id>/schools', methods=['POST'])
@require_permission('manage_schools', 'write', domain_param='org_id')
def create_school(org_id):
    # 自動檢查權限
    pass

@app.route('/api/schools/<school_id>/teachers', methods=['POST'])
@require_school_admin(domain_param='school_id')
def invite_teacher(school_id):
    # org_owner 或該校 school_admin 都可以執行
    pass
```

---

### 3.X 舊方案（參考用，已棄用）

<details>
<summary>展開查看原本自己寫的權限檢查方案</summary>

```python
# backend/services/permission_service.py

from functools import wraps
from flask import request, jsonify
from models import Teacher, TeacherSchool

class PermissionService:
    @staticmethod
    def has_role(teacher_id: int, role: str, school_id: str = None) -> bool:
        """
        檢查老師是否有特定角色

        Args:
            teacher_id: 老師 ID
            role: 角色名稱 ("org_owner" | "school_admin" | "teacher")
            school_id: 學校 ID（None = 檢查機構層級）
        """
        query = TeacherSchool.query.filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.is_active == True
        )

        if school_id:
            query = query.filter(TeacherSchool.school_id == school_id)
        else:
            query = query.filter(TeacherSchool.school_id == None)

        record = query.first()
        if not record:
            return False

        return role in record.roles

    @staticmethod
    def get_all_roles(teacher_id: int) -> list[str]:
        """取得老師所有角色（合併）"""
        records = TeacherSchool.query.filter(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.is_active == True
        ).all()

        all_roles = set()
        for record in records:
            all_roles.update(record.roles)

        return list(all_roles)

    @staticmethod
    def can_manage_school(teacher_id: int, school_id: str) -> bool:
        """檢查是否可以管理特定學校"""
        # org_owner 可以管理所有學校
        if PermissionService.has_role(teacher_id, "org_owner"):
            return True

        # school_admin 只能管理自己的學校
        return PermissionService.has_role(teacher_id, "school_admin", school_id)

# Decorator
def require_role(*roles, school_id_param=None):
    """
    權限檢查裝飾器

    Usage:
      @require_role("org_owner")
      @require_role("org_owner", "school_admin")
      @require_role("school_admin", school_id_param="school_id")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            teacher_id = request.current_teacher_id  # 從 JWT 取得

            # 如果指定了 school_id_param，從路徑參數取得
            school_id = kwargs.get(school_id_param) if school_id_param else None

            # 檢查是否有任一角色
            has_permission = any(
                PermissionService.has_role(teacher_id, role, school_id)
                for role in roles
            )

            if not has_permission:
                return jsonify({"error": "Permission denied"}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator

# 使用範例
@app.route('/api/organizations/<org_id>/schools', methods=['POST'])
@require_role("org_owner")
def create_school(org_id):
    # 只有 org_owner 可以新增學校
    pass

@app.route('/api/schools/<school_id>/teachers', methods=['POST'])
@require_role("org_owner", "school_admin", school_id_param="school_id")
def invite_teacher(school_id):
    # org_owner 或該校 school_admin 可以邀請老師
    pass
```

---

## 💾 資料庫 Migration

### Migration 腳本位置

`backend/migrations/versions/xxx_add_organization_hierarchy.py`

### 關鍵內容

（詳見 `ORG_TODO.md` 的完整 SQL schema）

```python
def upgrade():
    # 1. 建立 5 個新表
    #    - organizations
    #    - schools
    #    - teacher_organizations
    #    - teacher_schools
    #    - classroom_schools

    # 2. 建立 9 個索引

    # 3. 資料遷移（為每個現有老師建立個人機構）
    op.execute("""
        WITH new_orgs AS (
            INSERT INTO organizations (id, name, type, ...)
            SELECT gen_random_uuid(), name || '的工作室', 'personal', ...
            FROM teachers
            RETURNING id, name
        ),
        ...
    """)

def downgrade():
    # 完全回滾（DROP 5 個表）
    op.drop_table('classroom_schools')
    op.drop_table('teacher_schools')
    op.drop_table('teacher_organizations')
    op.drop_table('schools')
    op.drop_table('organizations')
```

### ORM Models 新增

`backend/models.py` 新增：

```python
class Organization(Base):
    __tablename__ = 'organizations'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), default='organization')
    settings = Column(JSONB, default={})

    schools = relationship("School", back_populates="organization")
    teacher_organizations = relationship("TeacherOrganization")

class School(Base):
    __tablename__ = 'schools'
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID, ForeignKey('organizations.id'))
    name = Column(String(255), nullable=False)

    organization = relationship("Organization", back_populates="schools")
    teacher_schools = relationship("TeacherSchool")
    classroom_schools = relationship("ClassroomSchool")

class TeacherOrganization(Base):
    __tablename__ = 'teacher_organizations'
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))
    organization_id = Column(UUID, ForeignKey('organizations.id', ondelete='CASCADE'))
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

class TeacherSchool(Base):
    __tablename__ = 'teacher_schools'
    teacher_id = Column(Integer, ForeignKey('teachers.id', ondelete='CASCADE'))
    school_id = Column(UUID, ForeignKey('schools.id', ondelete='CASCADE'), nullable=True)
    roles = Column(JSONB, nullable=False, default=["teacher"])
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

class ClassroomSchool(Base):
    __tablename__ = 'classroom_schools'
    classroom_id = Column(Integer, ForeignKey('classrooms.id', ondelete='CASCADE'))
    school_id = Column(UUID, ForeignKey('schools.id', ondelete='CASCADE'))
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

# 擴充現有 Teacher model
class Teacher(Base):
    # ... 原有欄位 ...

    teacher_organizations = relationship("TeacherOrganization")
    teacher_schools = relationship("TeacherSchool")

    @property
    def current_organization(self):
        active = [to for to in self.teacher_organizations if to.is_active]
        return active[0].organization if active else None

    @property
    def current_schools(self):
        return [ts.school for ts in self.teacher_schools
                if ts.is_active and ts.school_id]

    @property
    def roles(self):
        all_roles = set()
        for ts in self.teacher_schools:
            if ts.is_active:
                all_roles.update(ts.roles)
        return list(all_roles)
```

---

## 🎨 前端 UI 設計

### 1. Layout 改良

#### 1.1 TeacherLayout 改良

```typescript
// frontend/src/components/TeacherLayout.tsx

interface TeacherLayoutProps {
  children: ReactNode;
}

export default function TeacherLayout({ children }: TeacherLayoutProps) {
  const [teacherProfile, setTeacherProfile] = useState<TeacherProfile | null>(null);

  useEffect(() => {
    fetchTeacherProfile();
  }, []);

  const fetchTeacherProfile = async () => {
    const data = await apiClient.getTeacherDashboard();
    setTeacherProfile(data.teacher);
  };

  // ✅ 根據 roles 動態產生選單
  const sidebarItems = useMemo(() => {
    const items: SidebarItem[] = [
      { id: "dashboard", label: "首頁", icon: Home, path: "/teacher/dashboard" },
      { id: "classrooms", label: "我的班級", icon: GraduationCap, path: "/teacher/classrooms" },
      { id: "students", label: "我的學生", icon: Users, path: "/teacher/students" },
      { id: "programs", label: "公版課程", icon: BookOpen, path: "/teacher/programs" },
    ];

    const roles = teacherProfile?.roles || [];
    const orgType = teacherProfile?.organization?.type;

    // ✅ school_admin 可看學校管理
    if (roles.includes("school_admin")) {
      items.push({
        id: "school_management",
        label: "學校管理",
        icon: Building,
        path: "/teacher/school",
      });
    }

    // ✅ org_owner 可看機構管理
    if (roles.includes("org_owner")) {
      items.push({
        id: "org_management",
        label: "機構管理",
        icon: Building2,
        path: "/teacher/organization",
      });
    }

    // ✅ 訂閱頁面：personal 或 org_owner 才看得到
    if (orgType === "personal" || roles.includes("org_owner")) {
      items.push({
        id: "subscription",
        label: "訂閱管理",
        icon: CreditCard,
        path: "/teacher/subscription",
      });
    }

    return items;
  }, [teacherProfile]);

  // ✅ 顯示機構/學校資訊
  const organizationInfo = teacherProfile?.organization;
  const schools = teacherProfile?.schools || [];

  return (
    <div className="min-h-screen">
      {/* Sidebar */}
      <div className="sidebar">
        {/* Header */}
        <div className="p-4 border-b">
          <h1>Duotopia Teacher</h1>

          {/* ✅ 顯示機構資訊（如果不是 personal）*/}
          {organizationInfo && organizationInfo.type !== "personal" && (
            <div className="mt-2 text-xs text-gray-500">
              <div className="flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                <span>{organizationInfo.name}</span>
              </div>

              {/* ✅ 顯示學校（如果有多個）*/}
              {schools.length > 1 && (
                <div className="mt-1 text-xs">
                  任教：{schools.map(s => s.name).join(", ")}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav>
          {sidebarItems.map(item => (
            <Link key={item.id} to={item.path}>
              <Button variant={isActive(item.path) ? "default" : "ghost"}>
                <item.icon />
                {item.label}
              </Button>
            </Link>
          ))}
        </nav>
      </div>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
```

#### 1.2 StudentLayout 改良

```typescript
// frontend/src/components/StudentLayout.tsx

export default function StudentLayout() {
  const { user } = useStudentAuthStore();

  // ✅ user 已包含 school_name 和 organization_name（從 API）

  return (
    <div className="flex h-screen">
      <aside className="sidebar">
        {/* Logo */}
        <div className="p-6 border-b">
          <h1>Duotopia</h1>

          {/* ✅ 使用者資訊 */}
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-3">
              <div className="avatar">
                {user?.name?.charAt(0)}
              </div>
              <div className="flex-1">
                <p className="font-semibold">{user?.name}</p>

                {/* ✅ 顯示班級 */}
                <div className="text-xs text-gray-600 space-y-0.5">
                  <div className="flex items-center gap-1">
                    <GraduationCap className="h-3 w-3" />
                    {user?.classroom_name}
                  </div>

                  {/* ✅ 顯示學校（如果有）*/}
                  {user?.school_name && (
                    <div className="flex items-center gap-1">
                      <Building className="h-3 w-3" />
                      {user.school_name}
                    </div>
                  )}

                  {/* ✅ 顯示機構（如果有）*/}
                  {user?.organization_name && (
                    <div className="flex items-center gap-1">
                      <Building2 className="h-3 w-3" />
                      {user.organization_name}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav>{/* ... */}</nav>
      </aside>

      <main>
        {/* ✅ 麵包屑（在 ActivityPage 頂部）*/}
        <div className="breadcrumb">
          {user?.organization_name && (
            <>
              <span>{user.organization_name}</span>
              <ChevronRight className="h-4 w-4" />
            </>
          )}
          {user?.school_name && (
            <>
              <span>{user.school_name}</span>
              <ChevronRight className="h-4 w-4" />
            </>
          )}
          <span>{user?.classroom_name}</span>
        </div>

        <Outlet />
      </main>
    </div>
  );
}
```

### 2. 新頁面設計

#### 2.1 機構管理頁面

```typescript
// frontend/src/pages/teacher/OrganizationManagement.tsx

export default function OrganizationManagement() {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [schools, setSchools] = useState<School[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [stats, setStats] = useState<OrgStats | null>(null);

  useEffect(() => {
    fetchOrganizationData();
  }, []);

  const fetchOrganizationData = async () => {
    const [orgData, statsData] = await Promise.all([
      apiClient.getMyOrganization(),
      apiClient.getOrganizationDashboard()
    ]);
    setOrganization(orgData);
    setSchools(orgData.schools);
    setStats(statsData);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{organization?.name}</h1>
        <p className="text-gray-500">機構管理</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_schools}</div>
            <div className="text-sm text-gray-500">校區數</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_teachers}</div>
            <div className="text-sm text-gray-500">教師數</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_students}</div>
            <div className="text-sm text-gray-500">學生數</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_classrooms}</div>
            <div className="text-sm text-gray-500">班級數</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="schools">
        <TabsList>
          <TabsTrigger value="schools">校區管理</TabsTrigger>
          <TabsTrigger value="teachers">教師管理</TabsTrigger>
          <TabsTrigger value="analytics">成效分析</TabsTrigger>
          <TabsTrigger value="settings">機構設定</TabsTrigger>
        </TabsList>

        {/* 校區管理 */}
        <TabsContent value="schools">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>校區列表</CardTitle>
                <Button onClick={() => setShowAddSchoolDialog(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  新增校區
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>校區名稱</TableHead>
                    <TableHead>教師數</TableHead>
                    <TableHead>學生數</TableHead>
                    <TableHead>班級數</TableHead>
                    <TableHead>成效</TableHead>
                    <TableHead>操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {schools.map(school => (
                    <TableRow key={school.id}>
                      <TableCell>
                        <Link to={`/teacher/schools/${school.id}`}>
                          {school.name}
                        </Link>
                      </TableCell>
                      <TableCell>{school.teachers_count}</TableCell>
                      <TableCell>{school.students_count}</TableCell>
                      <TableCell>{school.classrooms_count}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Progress value={school.avg_completion_rate * 100} />
                          <span className="text-sm">{(school.avg_completion_rate * 100).toFixed(0)}%</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Button variant="ghost" size="sm">編輯</Button>
                        <Button variant="ghost" size="sm">停用</Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 教師管理 */}
        <TabsContent value="teachers">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>教師列表</CardTitle>
                <Button onClick={() => setShowInviteTeacherDialog(true)}>
                  <UserPlus className="h-4 w-4 mr-2" />
                  邀請教師
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <TeacherManagementTable
                teachers={teachers}
                schools={schools}
                onUpdateRole={handleUpdateRole}
                onTransfer={handleTransfer}
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* 成效分析 */}
        <TabsContent value="analytics">
          <OrganizationAnalytics stats={stats} />
        </TabsContent>

        {/* 機構設定 */}
        <TabsContent value="settings">
          <OrganizationSettings organization={organization} />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <AddSchoolDialog
        open={showAddSchoolDialog}
        onClose={() => setShowAddSchoolDialog(false)}
        onSuccess={fetchOrganizationData}
      />

      <InviteTeacherDialog
        open={showInviteTeacherDialog}
        schools={schools}
        onClose={() => setShowInviteTeacherDialog(false)}
        onSuccess={fetchOrganizationData}
      />
    </div>
  );
}
```

#### 2.2 學校管理頁面

```typescript
// frontend/src/pages/teacher/SchoolManagement.tsx

export default function SchoolManagement() {
  const { schoolId } = useParams<{ schoolId: string }>();
  const [school, setSchool] = useState<School | null>(null);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [teachers, setTeachers] = useState<Teacher[]>([]);

  useEffect(() => {
    if (schoolId) {
      fetchSchoolData(schoolId);
    }
  }, [schoolId]);

  const fetchSchoolData = async (id: string) => {
    const [schoolData, classroomsData, teachersData] = await Promise.all([
      apiClient.getSchool(id),
      apiClient.getSchoolClassrooms(id),
      apiClient.getSchoolTeachers(id)
    ]);
    setSchool(schoolData);
    setClassrooms(classroomsData);
    setTeachers(teachersData);
  };

  return (
    <div className="p-6 space-y-6">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Link to="/teacher/organization">機構管理</Link>
        <ChevronRight className="h-4 w-4" />
        <span className="text-gray-900">{school?.name}</span>
      </div>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{school?.name}</h1>
        <p className="text-gray-500">{school?.organization_name}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{school?.teachers_count}</div>
            <div className="text-sm text-gray-500">教師數</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{school?.students_count}</div>
            <div className="text-sm text-gray-500">學生數</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent>
            <div className="text-2xl font-bold">{school?.classrooms_count}</div>
            <div className="text-sm text-gray-500">班級數</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="classrooms">
        <TabsList>
          <TabsTrigger value="classrooms">班級管理</TabsTrigger>
          <TabsTrigger value="teachers">教師管理</TabsTrigger>
          <TabsTrigger value="analytics">成效分析</TabsTrigger>
        </TabsList>

        <TabsContent value="classrooms">
          <ClassroomList classrooms={classrooms} />
        </TabsContent>

        <TabsContent value="teachers">
          <SchoolTeacherList
            teachers={teachers}
            schoolId={schoolId!}
            onInvite={handleInviteTeacher}
            onUpdateRole={handleUpdateRole}
          />
        </TabsContent>

        <TabsContent value="analytics">
          <SchoolAnalytics schoolId={schoolId!} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### 3. 共用組件設計

#### 3.1 權限檢查組件

```typescript
// frontend/src/components/shared/RequireRole.tsx

interface RequireRoleProps {
  roles: string[];  // ["org_owner"] | ["school_admin"] | etc.
  fallback?: ReactNode;
  children: ReactNode;
}

export function RequireRole({ roles, fallback, children }: RequireRoleProps) {
  const { teacherProfile } = useTeacherAuth();

  const hasRole = roles.some(role =>
    teacherProfile?.roles?.includes(role)
  );

  if (!hasRole) {
    return fallback || null;
  }

  return <>{children}</>;
}

// 使用範例
<RequireRole roles={["org_owner"]}>
  <Button>機構管理</Button>
</RequireRole>

<RequireRole
  roles={["org_owner", "school_admin"]}
  fallback={<div>無權限</div>}
>
  <SchoolManagement />
</RequireRole>
```

#### 3.2 機構/學校選擇器

```typescript
// frontend/src/components/shared/SchoolSelector.tsx

interface SchoolSelectorProps {
  schools: School[];
  value: string | null;
  onChange: (schoolId: string) => void;
}

export function SchoolSelector({ schools, value, onChange }: SchoolSelectorProps) {
  return (
    <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger>
        <SelectValue placeholder="選擇校區" />
      </SelectTrigger>
      <SelectContent>
        {schools.map(school => (
          <SelectItem key={school.id} value={school.id}>
            {school.name}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
```

---

## 🔐 權限系統設計

### 權限矩陣

| 功能 | org_owner | school_admin | teacher |
|------|-----------|--------------|---------|
| **機構層級** | | | |
| 查看機構資訊 | ✅ | ✅（只看自己學校） | ❌ |
| 修改機構設定 | ✅ | ❌ | ❌ |
| 新增/刪除學校 | ✅ | ❌ | ❌ |
| 邀請老師（機構） | ✅ | ❌ | ❌ |
| 查看機構成效 | ✅ | ❌ | ❌ |
| **學校層級** | | | |
| 查看學校資訊 | ✅ | ✅（自己的） | ✅（自己的） |
| 修改學校設定 | ✅ | ✅ | ❌ |
| 邀請老師（學校） | ✅ | ✅ | ❌ |
| 管理老師角色 | ✅ | ✅ | ❌ |
| 查看學校成效 | ✅ | ✅ | ❌ |
| 查看所有班級 | ✅ | ✅ | ❌ |
| **班級層級** | | | |
| 建立班級 | ✅ | ✅ | ✅ |
| 管理自己的班級 | ✅ | ✅ | ✅ |
| 管理他人班級 | ✅ | ✅ | ❌ |
| 查看班級數據 | ✅ | ✅ | ✅（只看自己的） |
| **金流** | | | |
| 查看訂閱資訊 | ✅ | ❌ | ❌ |
| 修改訂閱 | ✅ | ❌ | ❌ |
| 管理信用卡 | ✅ | ❌ | ❌ |

### 前端權限檢查邏輯

```typescript
// frontend/src/lib/permissions.ts

export const Permissions = {
  canViewOrganization: (roles: string[]) =>
    roles.includes("org_owner") || roles.includes("school_admin"),

  canManageOrganization: (roles: string[]) =>
    roles.includes("org_owner"),

  canManageSchool: (roles: string[], schoolId: string) => {
    // TODO: 需要更複雜的邏輯檢查是否是該校的 admin
    return roles.includes("org_owner") || roles.includes("school_admin");
  },

  canViewBilling: (roles: string[], orgType: string) => {
    // 獨立工作者 或 org_owner 可以看金流
    return orgType === "personal" || roles.includes("org_owner");
  },

  canManageBilling: (roles: string[], orgType: string) => {
    return orgType === "personal" || roles.includes("org_owner");
  },
};

// 使用範例
const { roles, organization } = teacherProfile;

if (Permissions.canViewBilling(roles, organization.type)) {
  // 顯示訂閱頁面
}
```

---

## 💳 金流整合

### 訂閱頁面改良

```typescript
// frontend/src/pages/teacher/TeacherSubscription.tsx

export default function TeacherSubscription() {
  const { teacherProfile } = useTeacherAuth();
  const roles = teacherProfile?.roles || [];
  const orgType = teacherProfile?.organization?.type;

  // ✅ 權限檢查
  const canViewBilling = Permissions.canViewBilling(roles, orgType);
  const canManageBilling = Permissions.canManageBilling(roles, orgType);

  if (!canViewBilling) {
    return (
      <div className="p-6">
        <Card>
          <CardHeader>
            <CardTitle>訂閱管理</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>無權限</AlertTitle>
              <AlertDescription>
                訂閱管理由機構管理者統一處理。
                <br />
                請聯絡 <strong>{teacherProfile?.organization?.name}</strong> 的管理者。
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ✅ 顯示訂閱管理介面
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">訂閱管理</h1>
        {orgType !== "personal" && (
          <p className="text-gray-500">
            管理 {teacherProfile?.organization?.name} 的訂閱
          </p>
        )}
      </div>

      {/* 現有的訂閱管理 UI */}
      <SubscriptionCardManagement />
      <CurrentPlanDisplay />
      <BillingHistory />
    </div>
  );
}
```

---

## 👨‍🎓 學生端改動

### 學生 Store 擴充

```typescript
// frontend/src/stores/studentAuthStore.ts

interface StudentUser {
  id: number;
  name: string;
  classroom_id: number;
  classroom_name: string;
  // ✅ 新增欄位
  school_id?: string;
  school_name?: string;
  organization_id?: string;
  organization_name?: string;
}

export const useStudentAuthStore = create<StudentAuthStore>((set) => ({
  user: null,

  login: async (credentials) => {
    const response = await apiClient.studentLogin(credentials);
    // response.student 已包含 school_name 和 organization_name
    set({ user: response.student, token: response.token });
  },

  // ... 其他方法
}));
```

### 學生活動頁面麵包屑

```typescript
// frontend/src/pages/student/StudentActivityPage.tsx

export default function StudentActivityPage() {
  const { user } = useStudentAuthStore();

  return (
    <div className="p-6">
      {/* ✅ 麵包屑 */}
      <div className="flex items-center gap-2 text-sm text-gray-500 mb-4">
        {user?.organization_name && (
          <>
            <Building2 className="h-4 w-4" />
            <span>{user.organization_name}</span>
            <ChevronRight className="h-3 w-3" />
          </>
        )}

        {user?.school_name && (
          <>
            <Building className="h-4 w-4" />
            <span>{user.school_name}</span>
            <ChevronRight className="h-3 w-3" />
          </>
        )}

        <GraduationCap className="h-4 w-4" />
        <span className="text-gray-900 font-medium">
          {user?.classroom_name}
        </span>
      </div>

      {/* 活動內容 */}
      <StudentActivityPageContent />
    </div>
  );
}
```

---

## 🚀 實作順序

### Phase 1: 資料庫與後端基礎（Week 1-2）

1. ✅ **資料庫 Migration**
   - 建立 5 個新表
   - 建立索引
   - 資料遷移腳本
   - 測試 migration 與 rollback

2. ✅ **ORM Models 新增**
   - Organization, School, TeacherSchool 等 models
   - 測試 relationships

3. ✅ **權限服務實作**
   - `PermissionService` 類別
   - `@require_role` 裝飾器
   - 單元測試

4. ✅ **基礎 API - 讀取**
   - `GET /api/organizations/me`
   - `GET /api/teachers/me/roles`
   - 調整 `GET /api/teachers/dashboard`（向下相容）

5. ✅ **測試**
   - 資料庫完整性測試
   - API 測試
   - 權限測試

### Phase 2: 機構管理 API（Week 3）

1. ✅ **機構 API**
   - `GET /api/organizations/{org_id}`
   - `GET /api/organizations/{org_id}/dashboard`
   - `POST /api/organizations/{org_id}/schools`

2. ✅ **學校 API**
   - `GET /api/schools/{school_id}`
   - `GET /api/schools/{school_id}/classrooms`
   - `GET /api/schools/{school_id}/teachers`
   - `POST /api/schools/{school_id}/teachers`（邀請）
   - `PUT /api/schools/{school_id}/teachers/{teacher_id}/roles`

3. ✅ **測試**
   - 整合測試
   - 權限測試

### Phase 3: 前端 Layout 改良（Week 4）

1. ✅ **TeacherLayout 改良**
   - 動態選單（根據 roles）
   - 顯示機構/學校資訊
   - 權限檢查

2. ✅ **StudentLayout 改良**
   - 顯示機構/學校資訊
   - 麵包屑組件

3. ✅ **共用組件**
   - `RequireRole` 組件
   - `SchoolSelector` 組件

4. ✅ **測試**
   - 組件測試
   - E2E 測試

### Phase 4: 機構管理前端（Week 5-6）

1. ✅ **機構管理頁面**
   - 機構總覽 Dashboard
   - 校區管理
   - 教師管理
   - 成效分析

2. ✅ **學校管理頁面**
   - 學校總覽 Dashboard
   - 班級列表
   - 教師管理
   - 成效分析

3. ✅ **Dialogs**
   - 新增校區
   - 邀請教師
   - 調動教師
   - 編輯角色

4. ✅ **測試**
   - 組件測試
   - E2E 測試

### Phase 5: 金流整合（Week 7）

1. ✅ **訂閱頁面改良**
   - 權限檢查
   - 提示訊息（非 org_owner）

2. ✅ **API 調整**
   - 檢查 org_owner 權限

3. ✅ **測試**
   - 金流測試
   - 權限測試

### Phase 6: 學生端改動（Week 8）

1. ✅ **API 調整**
   - 學生登入回傳機構/學校資訊
   - 教室資訊 API 擴充

2. ✅ **前端改動**
   - StudentLayout 顯示機構/學校
   - 麵包屑
   - Store 擴充

3. ✅ **測試**
   - E2E 測試

### Phase 7: 整合測試與優化（Week 9-10）

1. ✅ **完整測試**
   - 完整 E2E 測試流程
   - 效能測試
   - 跨瀏覽器測試

2. ✅ **優化**
   - 查詢效能優化
   - UI/UX 優化
   - 錯誤處理

3. ✅ **文件**
   - API 文件
   - 使用者文件
   - 開發文件

### Phase 8: 部署（Week 11）

1. ✅ **Staging 部署**
   - 執行 migration
   - 驗證功能
   - 效能監控

2. ✅ **Production 部署**
   - 資料庫備份
   - 執行 migration
   - 監控與回滾準備

---

## 🧪 測試計畫

### 後端測試

```python
# backend/tests/integration/test_organization_api.py

def test_get_my_organization(client, auth_token):
    """測試取得我的機構"""
    response = client.get(
        '/api/organizations/me',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    assert 'organization' in response.json
    assert 'schools' in response.json

def test_create_school_as_org_owner(client, org_owner_token):
    """測試 org_owner 新增學校"""
    response = client.post(
        f'/api/organizations/{org_id}/schools',
        headers={'Authorization': f'Bearer {org_owner_token}'},
        json={'name': '新竹校區'}
    )
    assert response.status_code == 201

def test_create_school_as_teacher_fails(client, teacher_token):
    """測試一般老師無法新增學校"""
    response = client.post(
        f'/api/organizations/{org_id}/schools',
        headers={'Authorization': f'Bearer {teacher_token}'},
        json={'name': '新竹校區'}
    )
    assert response.status_code == 403

def test_invite_teacher_to_school(client, school_admin_token):
    """測試 school_admin 邀請老師"""
    response = client.post(
        f'/api/schools/{school_id}/teachers',
        headers={'Authorization': f'Bearer {school_admin_token}'},
        json={
            'email': 'new@abc.com',
            'name': '新老師',
            'password': 'temp123',
            'roles': ['teacher']
        }
    )
    assert response.status_code == 201
```

### 前端測試

```typescript
// frontend/src/components/__tests__/TeacherLayout.test.tsx

describe('TeacherLayout', () => {
  it('shows org management for org_owner', () => {
    const profile = {
      roles: ['org_owner'],
      organization: { type: 'organization', name: 'ABC 補習班' }
    };

    render(<TeacherLayout profile={profile} />);

    expect(screen.getByText('機構管理')).toBeInTheDocument();
  });

  it('hides org management for regular teacher', () => {
    const profile = {
      roles: ['teacher'],
      organization: { type: 'organization', name: 'ABC 補習班' }
    };

    render(<TeacherLayout profile={profile} />);

    expect(screen.queryByText('機構管理')).not.toBeInTheDocument();
  });

  it('shows subscription for personal type', () => {
    const profile = {
      roles: ['teacher'],
      organization: { type: 'personal', name: '王老師工作室' }
    };

    render(<TeacherLayout profile={profile} />);

    expect(screen.getByText('訂閱管理')).toBeInTheDocument();
  });
});
```

### E2E 測試

```typescript
// frontend/e2e/organization-management.spec.ts

test.describe('Organization Management', () => {
  test('org owner can create school', async ({ page }) => {
    // 1. 登入為 org_owner
    await page.goto('/teacher/login');
    await login(page, 'owner@abc.com', 'password');

    // 2. 前往機構管理
    await page.click('text=機構管理');
    await expect(page).toHaveURL('/teacher/organization');

    // 3. 新增校區
    await page.click('text=新增校區');
    await page.fill('input[name="name"]', '高雄校區');
    await page.click('button:has-text("確認")');

    // 4. 驗證新校區出現
    await expect(page.locator('text=高雄校區')).toBeVisible();
  });

  test('school admin can invite teacher', async ({ page }) => {
    // 1. 登入為 school_admin
    await login(page, 'admin@abc.com', 'password');

    // 2. 前往學校管理
    await page.goto(`/teacher/schools/${schoolId}`);

    // 3. 邀請教師
    await page.click('text=邀請教師');
    await page.fill('input[name="email"]', 'new@abc.com');
    await page.fill('input[name="name"]', '新老師');
    await page.click('button:has-text("送出邀請")');

    // 4. 驗證教師出現
    await expect(page.locator('text=新老師')).toBeVisible();
  });
});
```

---

## ⚠️ 注意事項

### 1. 向下相容

- ✅ 所有現有 API 保持不變
- ✅ 現有前端頁面正常運作
- ✅ 獨立工作者體驗完全不變

### 2. 效能考量

- ⚠️ 新增的 JOIN 可能影響效能
- ✅ 解決方案：
  - 正確建立索引
  - 使用 ORM eager loading
  - 監控查詢效能

### 3. 安全性

- ✅ 所有管理 API 都有權限檢查
- ✅ 前端權限檢查是輔助，後端是最後防線
- ✅ 避免資料洩漏（其他機構的資料）

### 4. 資料遷移

- ✅ 測試環境先測試
- ✅ 備份資料庫
- ✅ 準備回滾腳本
- ✅ 監控執行時間

### 5. UI/UX

- ✅ 獨立工作者與機構老師體驗一致
- ✅ 根據角色動態顯示功能
- ✅ 避免混淆的 UI

---

## 📝 總結

### 核心原則

1. **零破壞性** - 現有功能完全不受影響
2. **模組化** - 前台共用，後台獨立
3. **權限清晰** - 後端嚴格檢查，前端輔助
4. **易擴展** - 未來可輕鬆新增功能

### 技術亮點

1. **關聯表設計** - 完全不動現有表
2. **動態選單** - 根據 roles 自動顯示
3. **權限中介層** - 統一權限檢查邏輯
4. **麵包屑導航** - 清楚顯示層級關係

### 下一步

1. 開始 Phase 1：資料庫與後端基礎
2. 建立測試環境
3. 執行 migration
4. 實作基礎 API

---

**文件版本**: v1.0
**建立日期**: 2024-11-26
**依據**: `ORG_TODO.md` 零破壞性架構設計
