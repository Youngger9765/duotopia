# Casbin 使用指南

## 🎯 快速開始

### 1. 初始化（應用啟動時）

```python
# app.py 或 main.py

from services.casbin_service import init_casbin_service

# 應用啟動時初始化
@app.before_first_request
def initialize():
    init_casbin_service()

    # 可選：從資料庫同步角色
    # casbin_service.sync_from_database()
```

### 2. 在 API 中使用 Decorator

```python
from services.permission_decorators import (
    require_permission,
    require_role,
    require_org_owner,
    require_school_admin
)

# ============================================
# 範例 1: 檢查具體權限
# ============================================

@app.route('/api/organizations/<org_id>/schools', methods=['POST'])
@require_permission('manage_schools', 'write', domain_param='org_id')
def create_school(org_id):
    """
    建立學校
    自動檢查：當前使用者是否有在 org-{org_id} 管理學校的權限
    """
    # 你的業務邏輯
    return jsonify({"message": "School created"})

@app.route('/api/schools/<school_id>/teachers', methods=['POST'])
@require_permission('manage_teachers', 'write', domain_param='school_id')
def invite_teacher(school_id):
    """
    邀請老師
    自動檢查：當前使用者是否有在 school-{school_id} 管理老師的權限
    """
    return jsonify({"message": "Teacher invited"})

# ============================================
# 範例 2: 檢查角色（更簡單）
# ============================================

@app.route('/api/organizations/<org_id>', methods=['DELETE'])
@require_org_owner(domain_param='org_id')
def delete_organization(org_id):
    """
    刪除機構
    只有 org_owner 可以執行
    """
    return jsonify({"message": "Organization deleted"})

@app.route('/api/schools/<school_id>', methods=['PUT'])
@require_school_admin(domain_param='school_id')
def update_school(school_id):
    """
    更新學校
    school_admin 或 org_owner 都可以執行
    """
    return jsonify({"message": "School updated"})

# ============================================
# 範例 3: 使用機構 domain
# ============================================

@app.route('/api/organizations/my/analytics', methods=['GET'])
@require_permission('view_analytics', 'read', use_org_domain=True)
def get_my_org_analytics():
    """
    查看機構分析
    自動使用當前使用者的機構 domain
    """
    return jsonify({"analytics": {...}})

# ============================================
# 範例 4: 手動檢查權限（不用 decorator）
# ============================================

@app.route('/api/classrooms/<classroom_id>', methods=['GET'])
def get_classroom(classroom_id):
    from services.casbin_service import get_casbin_service

    teacher_id = request.current_teacher_id

    # 取得班級所屬學校
    classroom = Classroom.query.get(classroom_id)
    school_id = classroom.school_id

    # 手動檢查權限
    casbin = get_casbin_service()

    if not casbin.check_permission(
        teacher_id,
        f"school-{school_id}",
        'view_students',
        'read'
    ):
        return jsonify({"error": "Permission denied"}), 403

    # 權限檢查通過
    return jsonify({"classroom": classroom.to_dict()})
```

---

## 📊 資料庫同步

### 方案 A: 應用啟動時同步（推薦）

```python
from services.casbin_service import get_casbin_service

# 應用啟動時
casbin = get_casbin_service()
casbin.sync_from_database()
```

### 方案 B: 動態同步（當角色變更時）

```python
from services.casbin_service import get_casbin_service

# 當老師的角色變更時
def update_teacher_role(teacher_id, school_id, new_roles):
    # 1. 更新資料庫
    ts = TeacherSchool.query.filter_by(
        teacher_id=teacher_id,
        school_id=school_id
    ).first()

    ts.roles = new_roles
    db.session.commit()

    # 2. 同步到 Casbin
    casbin = get_casbin_service()
    casbin.sync_teacher_roles(teacher_id)
```

### 方案 C: 定期同步（Cron job）

```python
# scripts/sync_casbin.py

from services.casbin_service import get_casbin_service

def sync_all():
    casbin = get_casbin_service()
    casbin.sync_from_database()
    print("Casbin policies synced from database")

if __name__ == "__main__":
    sync_all()
```

```bash
# crontab
*/5 * * * * cd /path/to/app && python scripts/sync_casbin.py
```

---

## 🔧 管理 API

### 新增角色

```python
from services.casbin_service import get_casbin_service

casbin = get_casbin_service()

# 新增機構層級角色
casbin.add_role_for_user(
    teacher_id=123,
    role='org_owner',
    domain='org-uuid-abc'
)

# 新增學校層級角色
casbin.add_role_for_user(
    teacher_id=456,
    role='school_admin',
    domain='school-uuid-def'
)
```

### 移除角色

```python
# 移除特定角色
casbin.delete_role_for_user(
    teacher_id=123,
    role='school_admin',
    domain='school-uuid-def'
)

# 移除所有角色
casbin.delete_all_roles_for_user(teacher_id=123)
```

### 查詢角色

```python
# 查詢使用者在特定 domain 的角色
roles = casbin.get_roles_for_user(
    teacher_id=123,
    domain='school-uuid-def'
)
# => ['school_admin', 'teacher']

# 查詢使用者在所有 domain 的角色
all_roles = casbin.get_all_roles_for_user(teacher_id=123)
# => [('org_owner', 'org-uuid-abc'), ('teacher', 'school-uuid-def')]
```

### 檢查權限

```python
# 檢查具體權限
has_perm = casbin.check_permission(
    teacher_id=123,
    domain='org-uuid-abc',
    resource='manage_schools',
    action='write'
)

# 檢查是否有角色
has_role = casbin.has_role(
    teacher_id=123,
    role='org_owner',
    domain='org-uuid-abc'
)
```

---

## 🎨 前端整合

### 取得使用者權限（用於 UI 顯示）

```python
from services.permission_decorators import get_teacher_permissions

@app.route('/api/teachers/me/permissions', methods=['GET'])
def get_my_permissions():
    teacher_id = request.current_teacher_id

    permissions = get_teacher_permissions(teacher_id)

    return jsonify(permissions)
```

**回應範例**:
```json
{
  "roles": [
    {"role": "org_owner", "domain": "org-uuid-123"},
    {"role": "teacher", "domain": "school-uuid-456"}
  ],
  "permissions": {
    "org-uuid-123": [
      "manage_organization",
      "manage_schools",
      "manage_teachers",
      "view_analytics",
      "manage_billing"
    ],
    "school-uuid-456": [
      "manage_own_classrooms",
      "view_students",
      "assign_homework"
    ]
  }
}
```

### 前端使用

```typescript
// frontend/src/lib/permissions.ts

const { roles, permissions } = await api.getMyPermissions();

// 檢查權限
function canManageSchools(orgId: string): boolean {
  const domain = `org-${orgId}`;
  return permissions[domain]?.includes('manage_schools') || false;
}

// 根據權限顯示 UI
{canManageSchools(orgId) && (
  <Button onClick={createSchool}>新增學校</Button>
)}
```

---

## 📝 配置檔案說明

### model.conf

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

**說明**:
- `r = sub, dom, obj, act`: 請求格式（使用者, domain, 資源, 動作）
- `p = sub, dom, obj, act`: 政策格式（角色, domain, 資源, 動作）
- `g = _, _, _`: 使用者-角色-domain 對應
- matcher: 權限匹配邏輯，支援 wildcard `*`

### policy.csv

```csv
# 權限定義
p, org_owner, *, manage_schools, write
p, school_admin, *, manage_teachers, write

# 使用者-角色-domain 對應（由程式動態管理）
g, 123, org_owner, org-uuid-abc
g, 456, teacher, school-uuid-def
```

**注意**: `g` 規則通常由程式動態管理，不需要手動編輯。

---

## 🧪 測試

### 單元測試

```python
# tests/test_casbin.py

import pytest
from services.casbin_service import CasbinService

def test_check_permission():
    casbin = CasbinService()

    # 新增測試角色
    casbin.add_role_for_user(123, 'org_owner', 'org-test')

    # 測試權限檢查
    assert casbin.check_permission(123, 'org-test', 'manage_schools', 'write') == True
    assert casbin.check_permission(123, 'org-test', 'invalid', 'write') == False

    # 清理
    casbin.delete_all_roles_for_user(123)

def test_role_management():
    casbin = CasbinService()

    # 新增角色
    casbin.add_role_for_user(456, 'teacher', 'school-test')

    # 驗證角色
    assert casbin.has_role(456, 'teacher', 'school-test') == True

    # 取得角色
    roles = casbin.get_roles_for_user(456, 'school-test')
    assert 'teacher' in roles

    # 移除角色
    casbin.delete_role_for_user(456, 'teacher', 'school-test')
    assert casbin.has_role(456, 'teacher', 'school-test') == False
```

---

## ⚠️ 注意事項

### 1. Domain 格式

- **機構**: `org-{uuid}`
- **學校**: `school-{uuid}`
- 保持一致性！

### 2. 權限同步

當角色變更時，記得同步到 Casbin：

```python
casbin.sync_teacher_roles(teacher_id)
```

### 3. JWT 整合

確保 `request.current_teacher_id` 已正確設定：

```python
# middleware.py

@app.before_request
def set_current_teacher():
    token = request.headers.get('Authorization')
    if token:
        payload = decode_jwt(token)
        request.current_teacher_id = payload['teacher_id']
```

### 4. 效能優化

如果政策很多，考慮：
- 使用 Redis 快取
- 定期而非即時同步
- 使用 SQLAlchemy adapter（政策存資料庫）

---

## 📖 更多資源

- [Casbin 官方文件](https://casbin.org/docs/)
- [RBAC with Domains](https://casbin.org/docs/rbac-with-domains/)
- [線上編輯器](https://casbin.org/editor/)
- [PyCasbin GitHub](https://github.com/casbin/pycasbin)
