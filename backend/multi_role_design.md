# 多重角色系統設計

## 概述
設計一個支援用戶在不同機構擁有多重角色的系統，例如：
- 張老師在台北校區是老師，同時也是學生（進修中）
- 李主任在新竹分校是管理員，在台中補習班是老師
- 王同學在多個機構都是學生，但在某個機構兼任助教

## 數據模型

### 1. 保持現有 User 表（平台級）
```sql
users (現有表，略作調整)
- id (UUID, PK)
- email (unique)
- full_name
- hashed_password
- platform_role (SUPER_ADMIN | PLATFORM_USER)  -- 平台級角色
- is_active
- created_at, updated_at
```

### 2. 新增 UserInstitutionRole 表（機構級多重角色）
```sql
user_institution_roles
- id (UUID, PK)
- user_id (FK to users)
- institution_id (FK to schools)
- roles (JSON array: ["admin", "teacher", "student", "assistant"])
- permissions (JSON object: {"can_create_class": true, "can_grade": true})
- is_active (boolean)
- start_date (date)
- end_date (date, nullable)  -- 支援角色有效期
- created_at, updated_at
- created_by (FK to users)  -- 誰分配的這個角色

UNIQUE KEY (user_id, institution_id)  -- 每個用戶在每個機構只能有一條記錄
INDEX (user_id)
INDEX (institution_id)
INDEX (user_id, institution_id, is_active)
```

### 3. 角色定義
```python
class InstitutionRole(str, enum.Enum):
    ADMIN = "admin"          # 機構管理員
    TEACHER = "teacher"      # 教師
    STUDENT = "student"      # 學生
    ASSISTANT = "assistant"  # 助教
    PARENT = "parent"        # 家長（未來擴展）
```

## 權限檢查邏輯

### 1. 平台級權限
```python
def has_platform_admin(user):
    return user.platform_role == "SUPER_ADMIN"
```

### 2. 機構級權限
```python
def has_institution_role(user_id, institution_id, required_role):
    role_record = get_user_institution_role(user_id, institution_id)
    if not role_record or not role_record.is_active:
        return False
    return required_role in role_record.roles

def has_any_institution_role(user_id, required_role):
    """檢查用戶在任何機構是否有特定角色"""
    role_records = get_user_all_institution_roles(user_id)
    return any(required_role in record.roles for record in role_records if record.is_active)
```

### 3. 複合權限檢查
```python
def can_access_resource(user_id, institution_id, action):
    # 1. 檢查平台管理員
    if has_platform_admin(user_id):
        return True
    
    # 2. 檢查機構級權限
    role_record = get_user_institution_role(user_id, institution_id)
    if not role_record:
        return False
    
    # 3. 根據動作檢查具體權限
    if action == "create_class":
        return "admin" in role_record.roles or "teacher" in role_record.roles
    elif action == "view_grades":
        return any(role in role_record.roles for role in ["admin", "teacher", "student"])
    elif action == "manage_users":
        return "admin" in role_record.roles
    
    return False
```

## API 設計

### 1. 角色管理 API
```python
# 獲取用戶所有角色
GET /api/users/{user_id}/roles

# 獲取用戶在特定機構的角色
GET /api/users/{user_id}/institutions/{institution_id}/roles

# 分配角色給用戶
POST /api/users/{user_id}/institutions/{institution_id}/roles
{
    "roles": ["teacher", "student"],
    "permissions": {"can_create_class": true},
    "start_date": "2024-01-01",
    "end_date": null
}

# 更新用戶角色
PUT /api/users/{user_id}/institutions/{institution_id}/roles
{
    "roles": ["admin", "teacher"],
    "is_active": true
}

# 撤銷角色
DELETE /api/users/{user_id}/institutions/{institution_id}/roles
```

### 2. 權限檢查裝飾器
```python
@require_institution_role("admin", "teacher")
async def create_class(institution_id: str, current_user: User):
    pass

@require_any_role("student", "teacher", "admin") 
async def view_class(class_id: str, current_user: User):
    pass

@require_platform_admin
async def manage_system():
    pass
```

## 前端實現

### 1. 角色切換界面
```jsx
function RoleSelector() {
    const [currentRole, setCurrentRole] = useState()
    const userRoles = useUserRoles()
    
    return (
        <select onChange={(e) => switchRole(e.target.value)}>
            {userRoles.map(role => (
                <option key={role.id} value={role.id}>
                    {role.institution_name} - {role.roles.join(', ')}
                </option>
            ))}
        </select>
    )
}
```

### 2. 權限導向路由
```jsx
function ProtectedRoute({ requiredRole, children }) {
    const hasPermission = usePermission(requiredRole)
    return hasPermission ? children : <AccessDenied />
}
```

## 使用案例

### 1. 張老師的多重身份
```json
{
    "user_id": "zhang-teacher-123",
    "email": "zhang@duotopia.com",
    "platform_role": "PLATFORM_USER",
    "institution_roles": [
        {
            "institution_id": "taipei-school",
            "institution_name": "台北總校",
            "roles": ["teacher"],
            "permissions": {"can_create_class": true, "can_grade": true}
        },
        {
            "institution_id": "hsinchu-school", 
            "institution_name": "新竹分校",
            "roles": ["student"],
            "permissions": {"can_view_grades": true}
        }
    ]
}
```

### 2. 權限檢查範例
```python
# 張老師想在台北校區創建班級
can_create = can_access_resource("zhang-teacher-123", "taipei-school", "create_class")  # True

# 張老師想查看在新竹分校的成績
can_view = can_access_resource("zhang-teacher-123", "hsinchu-school", "view_grades")  # True

# 張老師想管理新竹分校用戶
can_manage = can_access_resource("zhang-teacher-123", "hsinchu-school", "manage_users")  # False
```

## 遷移策略

### 階段1：保持向後兼容
- 保留現有 User.role 欄位
- 新增 UserInstitutionRole 表
- 創建數據遷移腳本將現有角色轉換

### 階段2：權限系統整合
- 更新所有權限檢查邏輯
- 實現新的 API 端點
- 前端角色切換功能

### 階段3：清理舊系統
- 移除舊的 User.role 欄位（可選）
- 完整測試所有功能

## 優勢
1. **靈活性**：支援複雜的角色分配需求
2. **擴展性**：易於添加新角色類型
3. **安全性**：細粒度權限控制
4. **可追蹤性**：角色分配歷史記錄
5. **時效性**：支援角色有效期限制