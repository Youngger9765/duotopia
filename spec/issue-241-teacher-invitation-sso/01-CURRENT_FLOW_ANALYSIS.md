# 現狀流程分析

> 詳細分析機構邀請教師的當前實現與問題

## 📋 目錄

- [前端邀請 UI](#前端邀請-ui)
- [後端邀請端點](#後端邀請端點)
- [資料庫模型](#資料庫模型)
- [認證與登入流程](#認證與登入流程)
- [問題總結](#問題總結)

---

## 前端邀請 UI

### 組件位置

1. **機構級邀請**: [frontend/src/components/organization/InviteTeacherDialog.tsx](../../frontend/src/components/organization/InviteTeacherDialog.tsx)
2. **學校級邀請**: [frontend/src/components/organization/InviteTeacherToSchoolDialog.tsx](../../frontend/src/components/organization/InviteTeacherToSchoolDialog.tsx)

### 機構級邀請流程

```typescript
// API 端點
POST ${API_URL}/api/organizations/{organizationId}/teachers/invite

// 請求格式
{
  email: string,
  name: string,
  role: "teacher" | "org_admin"
}

// 前端流程
1. 管理員打開邀請對話框
2. 輸入教師郵箱、姓名、角色
3. 發送 POST 請求到後端
4. 顯示成功訊息
5. 刷新教師列表
```

### 學校級邀請流程（雙模式）

**模式 A：從組織選擇現有教師**

```typescript
// 步驟 1：列出組織教師
GET /api/organizations/{organizationId}/teachers

// 步驟 2：添加到學校
POST /api/schools/{schoolId}/teachers
{
  teacher_id: number,
  roles: ["teacher" | "school_director"]
}
```

**模式 B：邀請新教師**

```typescript
// 步驟 1：邀請到組織
POST /api/organizations/{organizationId}/teachers/invite
{
  email: string,
  name: string,
  role: "teacher"
}

// 步驟 2：自動添加到學校
POST /api/schools/{schoolId}/teachers
{
  teacher_id: number,
  roles: ["teacher"]
}
```

---

## 後端邀請端點

### 端點實現

**文件**: [backend/routers/organizations.py:717-915](../../backend/routers/organizations.py#L717-L915)

**端點**: `POST /api/organizations/{org_id}/teachers/invite`

### 請求模型

```python
class InviteTeacherRequest(BaseModel):
    email: str = Field(..., max_length=200)
    name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="teacher", pattern="^(org_admin|teacher)$")
```

### 完整流程

```python
@router.post("/{org_id}/teachers/invite")
async def invite_teacher_to_organization(
    org_id: UUID,
    request: InviteTeacherRequest,
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher)
):
    # === Step 1: 權限驗證 ===
    # 1.1 檢查當前教師是否屬於該機構
    teacher_org = db.query(TeacherOrganization).filter(...).first()
    if not teacher_org:
        raise HTTPException(403, "You don't belong to this organization")

    # 1.2 驗證 Casbin 權限
    if not casbin_service.has_permission(teacher.id, "manage_teachers", org_id):
        raise HTTPException(403, "No permission to manage teachers")

    # === Step 2: 獲取組織並鎖定（防止 TOCTOU） ===
    org = check_org_permission(teacher.id, org_id, db, for_update=True)

    # === Step 3: 檢查教師授權限制 ===
    if org.teacher_limit is not None:
        active_teacher_count = db.query(TeacherOrganization).filter(
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
            TeacherOrganization.role != "org_owner"  # owner 不計入
        ).count()

        if active_teacher_count >= org.teacher_limit:
            raise HTTPException(
                400,
                f"已達教師授權上限（{org.teacher_limit} 位）"
            )

    # === Step 4: 檢查教師是否已存在 ===
    existing_teacher = db.query(Teacher).filter(
        Teacher.email == request.email
    ).first()

    if existing_teacher:
        # === 情境 A: 教師已存在 ===
        existing_rel = db.query(TeacherOrganization).filter(
            TeacherOrganization.teacher_id == existing_teacher.id,
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True)
        ).first()

        if existing_rel:
            raise HTTPException(400, "此教師已在組織中")

        # 添加到機構
        teacher_org = TeacherOrganization(
            teacher_id=existing_teacher.id,
            organization_id=org_id,
            role=request.role,
            is_active=True
        )
        db.add(teacher_org)
        teacher_to_return = existing_teacher
    else:
        # === 情境 B: 教師不存在，創建新帳號 ===
        random_password = secrets.token_urlsafe(16)

        new_teacher = Teacher(
            email=request.email,
            password_hash=get_password_hash(random_password),
            name=request.name,
            is_active=True,         # ← 機構邀請直接啟用
            email_verified=True,    # ← 信任機構邀請
        )
        db.add(new_teacher)
        db.flush()

        teacher_org = TeacherOrganization(
            teacher_id=new_teacher.id,
            organization_id=org_id,
            role=request.role,
            is_active=True
        )
        db.add(teacher_org)
        teacher_to_return = new_teacher

    # === Step 5: TOCTOU 競態條件防護 ===
    db.flush()  # 寫入 DB 但保持事務開啟

    # 重新驗證計數（考慮並發插入）
    if org.teacher_limit is not None:
        actual_count = db.query(TeacherOrganization).filter(
            TeacherOrganization.organization_id == org_id,
            TeacherOrganization.is_active.is_(True),
            TeacherOrganization.role != "org_owner"
        ).count()

        if actual_count > org.teacher_limit:
            db.rollback()
            raise HTTPException(400, "已達教師授權上限")

    # === Step 6: 提交事務 ===
    db.commit()
    db.refresh(teacher_org)

    # === Step 7: 同步 Casbin 角色 ===
    casbin_service.sync_teacher_roles(teacher_to_return.id)

    # === Step 8: ❌ 缺失：發送邀請郵件 ===
    # TODO: Send invitation email with password reset link
    # For now, just create the account

    # === Step 9: 返回結果 ===
    return {
        "id": teacher_org.id,
        "teacher_id": teacher_org.teacher_id,
        "organization_id": str(teacher_org.organization_id),
        "role": teacher_org.role,
        "is_active": teacher_org.is_active,
    }
```

### 關鍵決策

#### Decision #1: 教師授權計數規則
- `org.teacher_limit` 限制非 owner 教師數量
- `org_owner` **不計入**限制
- 默認 `NULL` = 無限制

#### Decision #2: 機構邀請的教師自動啟用
```python
new_teacher = Teacher(
    is_active=True,         # ← 不需要 email 驗證
    email_verified=True,    # ← 信任機構邀請
)
```

**理由**：機構管理員已驗證過教師身份，不需要再次驗證 email。

#### Decision #3: TOCTOU 競態條件防護
```python
# SELECT FOR UPDATE 鎖定組織行
org = check_org_permission(..., for_update=True)

# 檢查 → 插入 → 重新檢查
db.flush()
actual_count = count(...)
if actual_count > limit:
    db.rollback()
```

**理由**：防止並發邀請超過授權限制。

---

## 資料庫模型

### TeacherOrganization（教師-機構關係）

```python
class TeacherOrganization(Base):
    __tablename__ = "teacher_organizations"

    id = Column(Integer, primary_key=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)

    # 角色
    role = Column(String(50), nullable=False, default="org_owner")
    # 可能值：
    # - org_owner: 機構擁有者（最高權限）
    # - org_admin: 機構管理員
    # - teacher: 普通教師

    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 唯一約束：一個教師在一個機構只能有一個關係
    __table_args__ = (
        UniqueConstraint("teacher_id", "organization_id",
                        name="uq_teacher_organization"),
    )
```

### Teacher（教師）

```python
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)

    # === 登入認證 ===
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # ← 目前必填
    name = Column(String(100), nullable=False)

    # === 帳號狀態 ===
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)

    # === Email 驗證 ===
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    email_verification_token = Column(String(100))
    email_verification_sent_at = Column(DateTime(timezone=True))

    # === 密碼重設 ===
    password_reset_token = Column(String(100))
    password_reset_sent_at = Column(DateTime(timezone=True))
    password_reset_expires_at = Column(DateTime(timezone=True))

    # === 關係 ===
    teacher_organizations = relationship("TeacherOrganization")
    teacher_schools = relationship("TeacherSchool")
```

### Organization（機構）

```python
class Organization(Base):
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    tax_id = Column(String(50), nullable=True)  # 統編

    # 教師授權限制
    teacher_limit = Column(Integer, nullable=True)  # NULL = 無限制

    is_active = Column(Boolean, nullable=False, default=True)
```

---

## 認證與登入流程

### 自主註冊流程

**文件**: [backend/routers/auth.py](../../backend/routers/auth.py)

```python
@router.post("/teacher/register")
async def teacher_register(register_req: TeacherRegisterRequest):
    # 1. 驗證密碼強度
    is_valid, error_msg = validate_password_strength(register_req.password)
    if not is_valid:
        raise HTTPException(400, detail=error_msg)

    # 2. 檢查 email 重複
    existing = db.query(Teacher).filter(Teacher.email == register_req.email).first()
    if existing:
        if existing.email_verified:
            raise HTTPException(400, "Email already registered")
        else:
            db.delete(existing)  # 刪除未驗證的舊帳號

    # 3. 創建新教師（未啟用）
    new_teacher = Teacher(
        email=register_req.email,
        password_hash=get_password_hash(register_req.password),
        name=register_req.name,
        is_active=False,        # ← 需要 email 驗證
        email_verified=False,   # ← 未驗證
    )
    db.add(new_teacher)
    db.commit()

    # 4. 發送驗證 email
    email_sent = email_service.send_teacher_verification_email(db, new_teacher)
    if not email_sent:
        raise HTTPException(500, "Email verification failed")

    return {
        "message": "Please check your email to verify your account.",
        "verification_required": True
    }
```

### Email 驗證流程

```python
@router.get("/verify-teacher")
async def verify_teacher_email(token: str):
    # 1. 驗證 token
    teacher = email_service.verify_teacher_email_token(db, token)
    if not teacher:
        raise HTTPException(400, "Invalid or expired token")

    # 2. EmailService.verify_teacher_email_token() 內部已執行：
    # - 檢查 token 是否過期（24小時）
    # - 標記 email_verified = True
    # - 啟用帳號 is_active = True
    # - 創建 30 天試用訂閱

    return {
        "status": "success",
        "message": "Email verified successfully!",
        "subscription_status": teacher.subscription_status
    }
```

### 登入流程

```python
@router.post("/teacher/login")
async def teacher_login(login_req: TeacherLoginRequest):
    # 1. 查找教師
    teacher = db.query(Teacher).filter(Teacher.email == login_req.email).first()
    if not teacher:
        raise HTTPException(401, "Invalid credentials")

    # 2. 驗證密碼
    if not verify_password(login_req.password, teacher.password_hash):
        raise HTTPException(401, "Invalid credentials")

    # 3. 檢查帳號狀態
    if not teacher.is_active:
        if not teacher.email_verified:
            raise HTTPException(
                403,
                "Please verify your email before logging in."
            )
        else:
            raise HTTPException(403, "Account is inactive")

    # 4. 同步 Casbin 角色
    casbin_service.sync_teacher_roles(teacher.id)

    # 5. 查詢角色（優先級：org > school > teacher）
    teacher_org = db.query(TeacherOrganization).filter(...).first()
    role = teacher_org.role if teacher_org else "teacher"

    # 6. 創建 JWT token
    access_token = create_access_token(
        data={
            "sub": str(teacher.id),
            "email": teacher.email,
            "type": "teacher",
            "role": role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {...}
    }
```

### 兩種註冊方式對比

| 欄位 | 自主註冊 | 機構邀請 |
|-----|---------|---------|
| `email` | 使用者輸入 | 管理員輸入 |
| `password_hash` | 使用者設定 | **隨機生成（16字符）** |
| `is_active` | **False** → 驗證後 True | **True**（直接啟用） |
| `email_verified` | **False** → 驗證後 True | **True**（信任機構） |
| 驗證 Email | **必須發送** | ❌ **未發送（TODO）** |
| 訂閱 | 驗證後創建 30 天試用 | 使用機構授權 |

---

## 問題總結

### 🔴 P0 關鍵問題

#### 問題 1: 被邀請教師無法登入

**症狀**:
- 管理員邀請未註冊教師
- 系統創建帳號並生成隨機密碼
- 教師**不知道密碼**，無法登入

**根本原因**:
```python
# backend/routers/organizations.py:906-908
# TODO: Send invitation email with password reset link
# For now, just create the account
```

**影響範圍**:
- 所有機構邀請的新教師
- 影響機構採購決策（功能不可用）

**解決優先級**: **P0 - 立即修復**

---

#### 問題 2: 教師不知道被邀請

**症狀**:
- 沒有任何通知（email, SMS, 推播）
- 教師無從得知被邀請

**根本原因**:
- 邀請郵件功能未實現
- 前端成功訊息只顯示給管理員

**影響範圍**:
- 邀請流程完成率低（教師不會主動登入）
- 需要管理員手動通知教師（糟糕的 UX）

**解決優先級**: **P0 - 立即修復**

---

### 🟡 P1 次要問題

#### 問題 3: 密碼安全性

**症狀**:
- 隨機密碼未告知教師
- 密碼存在但無人知曉

**潛在風險**:
- 如果未來實現「顯示臨時密碼」，可能洩漏（管理員截圖、日誌記錄）
- 不符合密碼管理最佳實踐

**建議方案**:
- 使用密碼重設連結取代臨時密碼
- 讓教師自行設置密碼

---

#### 問題 4: 未來 SSO 整合準備不足

**症狀**:
- `password_hash` 欄位不允許 NULL
- 沒有 SSO 相關欄位（sso_provider, sso_account）
- 帳號綁定機制缺失

**影響**:
- 未來整合 1Campus SSO 需要大幅修改資料模型
- 可能需要資料遷移

**建議方案**:
- 提前調整資料模型（Phase 1）
- 建立混合認證架構

---

### 📊 流程問題視覺化

```
現狀流程（有問題）:

管理員邀請 → 創建帳號 + 隨機密碼 → ❌ 沒有通知
                                    ↓
                                教師不知情
                                    ↓
                              無法登入使用
```

```
理想流程:

管理員邀請 → 創建帳號 → 發送邀請郵件 → 教師收到通知
                                        ↓
                                  設置密碼連結
                                        ↓
                                  教師設置密碼
                                        ↓
                                    登入使用
```

---

## 🔗 相關代碼位置

### 前端
- [InviteTeacherDialog.tsx](../../frontend/src/components/organization/InviteTeacherDialog.tsx) - 邀請對話框
- [InviteTeacherToSchoolDialog.tsx](../../frontend/src/components/organization/InviteTeacherToSchoolDialog.tsx) - 學校邀請

### 後端
- [organizations.py:717-915](../../backend/routers/organizations.py#L717-L915) - 邀請端點
- [auth.py](../../backend/routers/auth.py) - 認證端點
- [email_service.py](../../backend/services/email_service.py) - 郵件服務

### 測試
- [test_organization_teachers.py](../../backend/tests/test_organization_teachers.py)
- [test_organization_spec_decisions.py](../../backend/tests/integration/api/test_organization_spec_decisions.py)

---

## 下一步

閱讀 [02-PHASE1_IMMEDIATE_FIX.md](./02-PHASE1_IMMEDIATE_FIX.md) 了解修復方案。
