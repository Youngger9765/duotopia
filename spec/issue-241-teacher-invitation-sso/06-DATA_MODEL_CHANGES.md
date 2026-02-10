# 資料模型變更

> 支援混合認證架構的資料模型設計

## 📋 目錄

- [變更摘要](#變更摘要)
- [Teacher 模型變更](#teacher-模型變更)
- [Organization 模型擴充](#organization-模型擴充)
- [新增模型](#新增模型)
- [Migration 腳本](#migration-腳本)
- [向後兼容性](#向後兼容性)

---

## 變更摘要

### 核心變更

| 模型 | 變更類型 | 目的 |
|-----|---------|------|
| **Teacher** | 欄位新增 + 約束修改 | 支援 SSO 認證 |
| **Organization** | 欄位新增 | 記錄 1Campus 學校識別碼 |
| **InvitationLog** | 新增模型 | 追蹤邀請狀態 |

### 影響範圍

- ✅ 向後兼容（現有資料不受影響）
- ⚠️ 需要 Migration（新增欄位 + 修改約束）
- ✅ 不影響現有 API（純新增功能）

---

## Teacher 模型變更

### 變更前後對比

```python
# ===== 變更前 =====
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # ❌ 不支援 SSO
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    # ... 其他欄位 ...

# ===== 變更後 =====
class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # ✅ 改為 nullable
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)

    # ===== 新增：SSO 支援欄位 =====
    sso_provider = Column(String(50), nullable=True)      # '1campus', 'google', None
    sso_account = Column(String(255), nullable=True)      # SSO 帳號（如 dev.teacher01@1campus.net）
    sso_teacher_id = Column(String(100), nullable=True)   # 1Campus teacherID（學校內唯一）
    sso_source_index = Column(String(100), nullable=True) # 1Campus sourceIndex（備用識別）

    # ===== 新增：認證方式標記 =====
    auth_method = Column(String(20), default='local')     # 'local', 'sso', 'hybrid'
    primary_auth = Column(String(20), default='local')    # 主要登入方式

    # ===== 新增：唯一約束 =====
    __table_args__ = (
        UniqueConstraint('sso_provider', 'sso_account', name='uq_sso_account'),
        # 部分唯一索引：同一 SSO 帳號不能重複
    )
```

### 欄位說明

#### sso_provider
- **型別**: `String(50)`, nullable
- **用途**: 標記 SSO 提供商
- **可能值**:
  - `'1campus'` - 教育部教育雲
  - `'google'` - Google SSO（未來）
  - `'line'` - LINE Login（未來）
  - `None` - 本地帳號

#### sso_account
- **型別**: `String(255)`, nullable
- **用途**: SSO 系統的帳號識別
- **範例**:
  - 1Campus: `dev.teacher01@1campus.net`
  - Google: `teacher@gmail.com`
- **索引**: 建立索引加速查詢

#### sso_teacher_id
- **型別**: `String(100)`, nullable
- **用途**: 1Campus 專用，教師在特定學校的系統編號
- **特性**: 學校內唯一，跨學校可能重複
- **範例**: `"T001"`, `"12345"`

#### sso_source_index
- **型別**: `String(100)`, nullable
- **用途**: 1Campus 備用識別欄位
- **需求**: 需特定 scope 才能取得

#### auth_method
- **型別**: `String(20)`, default='local'
- **用途**: 記錄教師支援的認證方式
- **可能值**:
  - `'local'` - 僅本地密碼
  - `'sso'` - 僅 SSO
  - `'hybrid'` - 兩種都支援（已綁定）

#### primary_auth
- **型別**: `String(20)`, default='local'
- **用途**: 偏好的登入方式（用於前端 UI）
- **可能值**: `'local'`, `'sso'`

---

## Organization 模型擴充

### 新增欄位

```python
class Organization(Base):
    __tablename__ = "organizations"

    # ... 現有欄位 ...

    # ===== 新增：1Campus 整合 =====
    campus_school_dsns = Column(String(100), nullable=True)  # 1Campus 學校識別碼
    campus_enabled = Column(Boolean, default=False)           # 是否啟用 1Campus SSO

    # ===== 新增：SSO 設定 =====
    sso_providers = Column(JSONType, default=list)  # 啟用的 SSO 提供商 ['1campus', 'google']
    sso_auto_create_account = Column(Boolean, default=True)   # SSO 登入時自動創建帳號
```

### 欄位說明

#### campus_school_dsns
- **型別**: `String(100)`, nullable
- **用途**: 1Campus API 所需的學校識別碼
- **範例**: `"dev"`, `"school123"`
- **來源**: 由 1Campus 平台提供

#### campus_enabled
- **型別**: `Boolean`, default=False
- **用途**: 控制是否啟用 1Campus SSO
- **管理**: 由機構管理員在設定頁面開啟

#### sso_providers
- **型別**: `JSONType` (Array)
- **用途**: 記錄機構啟用的 SSO 提供商
- **範例**: `["1campus"]`, `["1campus", "google"]`

#### sso_auto_create_account
- **型別**: `Boolean`, default=True
- **用途**: SSO 登入時，若教師不存在是否自動創建帳號
- **使用場景**:
  - `True`: 開放註冊（SSO 用戶可自動加入）
  - `False`: 僅限邀請（必須先邀請才能登入）

---

## 新增模型

### InvitationLog（邀請記錄）

```python
class InvitationLog(Base):
    """記錄邀請歷史，用於追蹤和重發"""
    __tablename__ = "invitation_logs"

    id = Column(Integer, primary_key=True)

    # 關聯
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    organization_id = Column(UUID, ForeignKey("organizations.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("teachers.id"), nullable=False)  # 邀請人

    # 邀請資訊
    invitation_type = Column(String(20), nullable=False)  # 'email', '1campus_push', 'both'
    invitation_token = Column(String(100), nullable=True)  # 密碼重設 token
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 狀態追蹤
    status = Column(String(20), default='pending')  # 'pending', 'accepted', 'expired', 'resent'
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)

    # 通知狀態
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True), nullable=True)
    push_sent = Column(Boolean, default=False)
    push_sent_at = Column(DateTime(timezone=True), nullable=True)

    # 額外資訊
    metadata = Column(JSONType, default=dict)  # 其他資訊（如錯誤訊息）

    # 關係
    teacher = relationship("Teacher", foreign_keys=[teacher_id])
    organization = relationship("Organization")
    inviter = relationship("Teacher", foreign_keys=[invited_by])

    # 索引
    __table_args__ = (
        Index('idx_invitation_teacher_org', 'teacher_id', 'organization_id'),
        Index('idx_invitation_status', 'status'),
        Index('idx_invitation_token', 'invitation_token'),
    )
```

### 用途

1. **追蹤邀請狀態**: pending → accepted/expired
2. **支援重發邀請**: 記錄歷史，避免重複發送
3. **統計分析**: 邀請接受率、平均接受時間
4. **問題排查**: 查看郵件/推播發送狀態

---

## Migration 腳本

### Phase 1 Migration

**文件**: `backend/alembic/versions/xxx_add_sso_support.py`

```python
"""Add SSO support and invitation tracking

Revision ID: xxx
Revises: yyy
Create Date: 2026-02-10
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    """
    ⚠️ Idempotent Migration - 可安全重複執行
    """
    op.execute("""
        DO $$ BEGIN
            -- ==========================================
            -- 1. 修改 teachers 表
            -- ==========================================

            -- 1.1 password_hash 改為 nullable
            ALTER TABLE teachers ALTER COLUMN password_hash DROP NOT NULL;

            -- 1.2 新增 SSO 欄位
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='teachers' AND column_name='sso_provider'
            ) THEN
                ALTER TABLE teachers
                    ADD COLUMN sso_provider VARCHAR(50),
                    ADD COLUMN sso_account VARCHAR(255),
                    ADD COLUMN sso_teacher_id VARCHAR(100),
                    ADD COLUMN sso_source_index VARCHAR(100),
                    ADD COLUMN auth_method VARCHAR(20) DEFAULT 'local',
                    ADD COLUMN primary_auth VARCHAR(20) DEFAULT 'local';
            END IF;

            -- 1.3 創建唯一約束
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_sso_account'
            ) THEN
                ALTER TABLE teachers
                    ADD CONSTRAINT uq_sso_account
                    UNIQUE (sso_provider, sso_account);
            END IF;

            -- 1.4 創建索引
            CREATE INDEX IF NOT EXISTS idx_teachers_sso_account
                ON teachers(sso_account);
            CREATE INDEX IF NOT EXISTS idx_teachers_auth_method
                ON teachers(auth_method);

            -- ==========================================
            -- 2. 擴充 organizations 表
            -- ==========================================

            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='organizations' AND column_name='campus_school_dsns'
            ) THEN
                ALTER TABLE organizations
                    ADD COLUMN campus_school_dsns VARCHAR(100),
                    ADD COLUMN campus_enabled BOOLEAN DEFAULT FALSE,
                    ADD COLUMN sso_providers JSONB DEFAULT '[]'::jsonb,
                    ADD COLUMN sso_auto_create_account BOOLEAN DEFAULT TRUE;
            END IF;

            -- ==========================================
            -- 3. 創建 invitation_logs 表
            -- ==========================================

            CREATE TABLE IF NOT EXISTS invitation_logs (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
                organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                invited_by INTEGER NOT NULL REFERENCES teachers(id),

                invitation_type VARCHAR(20) NOT NULL,
                invitation_token VARCHAR(100),
                token_expires_at TIMESTAMPTZ,

                status VARCHAR(20) DEFAULT 'pending',
                sent_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMPTZ,

                email_sent BOOLEAN DEFAULT FALSE,
                email_sent_at TIMESTAMPTZ,
                push_sent BOOLEAN DEFAULT FALSE,
                push_sent_at TIMESTAMPTZ,

                metadata JSONB DEFAULT '{}'::jsonb,

                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ
            );

            -- 3.1 創建索引
            CREATE INDEX IF NOT EXISTS idx_invitation_teacher_org
                ON invitation_logs(teacher_id, organization_id);
            CREATE INDEX IF NOT EXISTS idx_invitation_status
                ON invitation_logs(status);
            CREATE INDEX IF NOT EXISTS idx_invitation_token
                ON invitation_logs(invitation_token);
            CREATE INDEX IF NOT EXISTS idx_invitation_sent_at
                ON invitation_logs(sent_at);

        END $$;
    """)

def downgrade():
    """
    ⚠️ Idempotent Downgrade
    """
    op.execute("""
        DO $$ BEGIN
            -- 刪除 invitation_logs 表
            DROP TABLE IF EXISTS invitation_logs;

            -- 移除 organizations 欄位
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='organizations' AND column_name='campus_school_dsns'
            ) THEN
                ALTER TABLE organizations
                    DROP COLUMN campus_school_dsns,
                    DROP COLUMN campus_enabled,
                    DROP COLUMN sso_providers,
                    DROP COLUMN sso_auto_create_account;
            END IF;

            -- 移除 teachers 索引和約束
            DROP INDEX IF EXISTS idx_teachers_auth_method;
            DROP INDEX IF EXISTS idx_teachers_sso_account;

            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_sso_account'
            ) THEN
                ALTER TABLE teachers DROP CONSTRAINT uq_sso_account;
            END IF;

            -- 移除 teachers 欄位
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='teachers' AND column_name='sso_provider'
            ) THEN
                ALTER TABLE teachers
                    DROP COLUMN sso_provider,
                    DROP COLUMN sso_account,
                    DROP COLUMN sso_teacher_id,
                    DROP COLUMN sso_source_index,
                    DROP COLUMN auth_method,
                    DROP COLUMN primary_auth;
            END IF;

            -- password_hash 改回 NOT NULL（需先確保沒有 NULL 值）
            UPDATE teachers SET password_hash = '$2b$12$PLACEHOLDER'
                WHERE password_hash IS NULL;
            ALTER TABLE teachers ALTER COLUMN password_hash SET NOT NULL;
        END $$;
    """)
```

---

## 向後兼容性

### 資料遷移策略

#### 1. 現有教師自動轉換

```sql
-- Migration 後，所有現有教師自動設為 local 認證
UPDATE teachers
SET
    auth_method = 'local',
    primary_auth = 'local',
    sso_provider = NULL,
    sso_account = NULL
WHERE auth_method IS NULL;
```

#### 2. 保證現有功能不受影響

```python
# 登入邏輯向後兼容
@router.post("/teacher/login")
async def teacher_login(login_req: TeacherLoginRequest):
    teacher = db.query(Teacher).filter(Teacher.email == login_req.email).first()

    # ✅ 現有教師（auth_method='local'）正常登入
    if teacher.auth_method in ['local', 'hybrid', None]:
        if verify_password(login_req.password, teacher.password_hash):
            return create_token(teacher)

    # ✅ SSO 教師也可以設置密碼後使用本地登入（如果綁定）
    raise HTTPException(401, "Invalid credentials")
```

#### 3. API 回應向後兼容

```python
# 舊版 API 不返回 SSO 欄位（避免前端錯誤）
def teacher_to_dict(teacher: Teacher, include_sso: bool = False):
    base_dict = {
        "id": teacher.id,
        "email": teacher.email,
        "name": teacher.name,
        "is_active": teacher.is_active,
        # ... 其他欄位 ...
    }

    if include_sso:
        base_dict.update({
            "sso_provider": teacher.sso_provider,
            "auth_method": teacher.auth_method,
            "has_password": teacher.password_hash is not None,
        })

    return base_dict
```

---

## 資料完整性檢查

### 約束規則

```sql
-- 1. password_hash 和 sso_account 至少一個必須存在
ALTER TABLE teachers ADD CONSTRAINT check_auth_method
    CHECK (
        password_hash IS NOT NULL OR
        (sso_provider IS NOT NULL AND sso_account IS NOT NULL)
    );

-- 2. auth_method 必須匹配實際狀態
-- local: password_hash NOT NULL, sso_provider NULL
-- sso: password_hash NULL, sso_provider NOT NULL
-- hybrid: 兩者都 NOT NULL

-- 3. SSO 欄位一致性
ALTER TABLE teachers ADD CONSTRAINT check_sso_fields
    CHECK (
        (sso_provider IS NULL AND sso_account IS NULL) OR
        (sso_provider IS NOT NULL AND sso_account IS NOT NULL)
    );
```

### 驗證腳本

```python
# scripts/validate_teacher_data.py
def validate_teacher_integrity(db: Session):
    """驗證教師資料完整性"""
    errors = []

    # 檢查1: 至少有一種登入方式
    invalid_auth = db.query(Teacher).filter(
        Teacher.password_hash.is_(None),
        Teacher.sso_account.is_(None)
    ).all()

    if invalid_auth:
        errors.append(f"發現 {len(invalid_auth)} 個教師沒有任何登入方式")

    # 檢查2: SSO 欄位一致性
    invalid_sso = db.query(Teacher).filter(
        or_(
            and_(Teacher.sso_provider.isnot(None), Teacher.sso_account.is_(None)),
            and_(Teacher.sso_provider.is_(None), Teacher.sso_account.isnot(None))
        )
    ).all()

    if invalid_sso:
        errors.append(f"發現 {len(invalid_sso)} 個教師 SSO 欄位不一致")

    # 檢查3: auth_method 標記正確
    # ... 其他檢查 ...

    return errors
```

---

## 下一步

閱讀其他文檔：
- [02-PHASE1_IMMEDIATE_FIX.md](./02-PHASE1_IMMEDIATE_FIX.md) - 實施方案
- [03-PHASE2_SSO_PREPARATION.md](./03-PHASE2_SSO_PREPARATION.md) - SSO 準備
- [07-API_SPECIFICATIONS.md](./07-API_SPECIFICATIONS.md) - API 規格
