# Phase 1: 立即修復方案

> 解決當前邀請流程問題，同時為 SSO 整合打基礎

## 🎯 Phase 1 目標

- ✅ 被邀請教師能收到通知
- ✅ 被邀請教師能順利登入
- ✅ 資料模型支援未來 SSO 整合
- ✅ 保持現有功能正常運作

**時程**: 1 週內完成

---

## 📋 實施方案比較

### 方案 A: 郵件邀請（推薦）

**優點**:
- ✅ 安全性高（密碼重設連結）
- ✅ 標準化流程
- ✅ 易於追蹤（郵件記錄）
- ✅ 未來可擴展（SSO 邀請）

**缺點**:
- ⚠️ 需要 SMTP 服務穩定
- ⚠️ 開發工作量較大（3-5 天）

**適用場景**: 生產環境、長期方案

---

### 方案 B: 顯示臨時密碼（快速方案）

**優點**:
- ✅ 快速實現（1-2 天）
- ✅ 不依賴外部服務
- ✅ 立即可用

**缺點**:
- ⚠️ 安全性較低（密碼可能被截圖）
- ⚠️ 需要管理員手動通知
- ⚠️ 未來需要重構

**適用場景**: 快速修復、緊急上線

---

## 🚀 方案 A: 郵件邀請（詳細實作）

### Step 1: 資料模型調整

#### 1.1 修改 Teacher 模型

**文件**: [backend/models/user.py](../../backend/models/user.py)

```python
class Teacher(Base):
    __tablename__ = "teachers"

    # 現有欄位...

    # 修改：password_hash 改為 nullable（支援 SSO）
    password_hash = Column(String(255), nullable=True)  # ← 改為 nullable

    # 新增：SSO 支援欄位
    sso_provider = Column(String(50), nullable=True)       # '1campus', 'google', None
    sso_account = Column(String(255), nullable=True)       # SSO 帳號
    sso_teacher_id = Column(String(100), nullable=True)    # 1Campus teacherID
    sso_source_index = Column(String(100), nullable=True)  # 1Campus sourceIndex
    auth_method = Column(String(20), default='local')      # 'local', 'sso', 'hybrid'
    primary_auth = Column(String(20), default='local')     # 主要登入方式

    # 唯一約束
    __table_args__ = (
        UniqueConstraint('sso_provider', 'sso_account', name='uq_sso_account'),
    )
```

#### 1.2 創建 Migration

**文件**: `backend/alembic/versions/xxx_add_sso_support_to_teachers.py`

```python
"""Add SSO support to teachers table

Revision ID: xxx
Revises: yyy
Create Date: 2026-02-10
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    """
    ⚠️ 注意：必須使用 Idempotent（冪等）寫法
    """
    op.execute("""
        DO $$ BEGIN
            -- 1. password_hash 改為 nullable
            ALTER TABLE teachers ALTER COLUMN password_hash DROP NOT NULL;

            -- 2. 新增 SSO 相關欄位（IF NOT EXISTS 檢查）
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

            -- 3. 創建唯一索引（IF NOT EXISTS）
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_sso_account'
            ) THEN
                ALTER TABLE teachers
                    ADD CONSTRAINT uq_sso_account
                    UNIQUE (sso_provider, sso_account);
            END IF;

            -- 4. 創建索引加速查詢
            CREATE INDEX IF NOT EXISTS idx_teachers_sso_account
                ON teachers(sso_account);
            CREATE INDEX IF NOT EXISTS idx_teachers_auth_method
                ON teachers(auth_method);
        END $$;
    """)

def downgrade():
    """
    ⚠️ 注意：Downgrade 也必須是冪等的
    """
    op.execute("""
        DO $$ BEGIN
            -- 刪除索引
            DROP INDEX IF EXISTS idx_teachers_auth_method;
            DROP INDEX IF EXISTS idx_teachers_sso_account;

            -- 刪除約束
            IF EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_sso_account'
            ) THEN
                ALTER TABLE teachers DROP CONSTRAINT uq_sso_account;
            END IF;

            -- 刪除欄位（檢查是否存在）
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

#### 1.3 執行 Migration

```bash
# 創建 migration
cd backend
alembic revision -m "add_sso_support_to_teachers"

# 編輯生成的檔案，貼上上面的代碼

# 本地測試
alembic upgrade head

# 檢查結果
psql $DATABASE_URL -c "\d teachers"

# 提交代碼
git add backend/alembic/versions/xxx_add_sso_support_to_teachers.py
git commit -m "feat(db): add SSO support to teachers table"
```

---

### Step 2: 郵件服務擴充

#### 2.1 新增邀請郵件方法

**文件**: [backend/services/email_service.py](../../backend/services/email_service.py)

```python
class EmailService:
    # 現有方法...

    def send_teacher_invitation_email(
        self,
        db: Session,
        teacher: Teacher,
        organization_name: str,
        inviter_name: str
    ) -> bool:
        """
        發送教師邀請郵件

        Args:
            db: 資料庫 session
            teacher: 被邀請的教師
            organization_name: 邀請機構名稱
            inviter_name: 邀請人姓名

        Returns:
            是否發送成功
        """
        # 生成密碼重設 token（24小時有效）
        reset_token = self.generate_verification_token()

        # 更新教師記錄
        teacher.password_reset_token = reset_token
        teacher.password_reset_sent_at = datetime.utcnow()
        teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=24)
        db.commit()

        # 生成設置密碼連結
        reset_url = f"{self.frontend_url}/teacher/set-password?token={reset_token}"

        # 開發模式：僅記錄 log
        if not self.smtp_user or not self.smtp_password:
            logger.info(
                f"[開發模式] 教師邀請郵件\n"
                f"收件人: {teacher.email}\n"
                f"機構: {organization_name}\n"
                f"設置密碼連結: {reset_url}"
            )
            return True

        # 生成郵件內容
        html_content = self._generate_invitation_email_html(
            teacher_name=teacher.name,
            organization_name=organization_name,
            inviter_name=inviter_name,
            reset_url=reset_url
        )

        # 發送郵件
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"【Duotopia】{organization_name} 邀請您加入教學平台"
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = teacher.email

            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"邀請郵件發送成功: {teacher.email}")
            return True

        except Exception as e:
            logger.error(f"邀請郵件發送失敗: {teacher.email}, 錯誤: {str(e)}")
            return False

    def _generate_invitation_email_html(
        self,
        teacher_name: str,
        organization_name: str,
        inviter_name: str,
        reset_url: str
    ) -> str:
        """生成邀請郵件 HTML 內容"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Microsoft JhengHei', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px 8px 0 0;
            text-align: center;
        }}
        .content {{
            background: white;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            background: #667eea;
            color: white !important;
            padding: 14px 30px;
            text-decoration: none;
            border-radius: 6px;
            font-weight: 600;
            margin: 20px 0;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 0 0 8px 8px;
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
        .info-box {{
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎓 Duotopia 教學平台</h1>
            <p>機構邀請通知</p>
        </div>

        <div class="content">
            <h2>親愛的 {teacher_name} 老師：</h2>

            <p>您好！<strong>{inviter_name}</strong> 代表 <strong>{organization_name}</strong> 邀請您加入 Duotopia 教學平台。</p>

            <div class="info-box">
                <p><strong>📌 Duotopia 是什麼？</strong></p>
                <p>Duotopia 是專為教師設計的智慧教學平台，提供：</p>
                <ul>
                    <li>📚 教材管理與共享</li>
                    <li>👥 學生學習追蹤</li>
                    <li>📊 數據分析與報告</li>
                    <li>🤝 團隊協作工具</li>
                </ul>
            </div>

            <p><strong>請點擊下方按鈕設置您的密碼，開始使用平台：</strong></p>

            <div style="text-align: center;">
                <a href="{reset_url}" class="button">設置我的密碼</a>
            </div>

            <p style="color: #666; font-size: 14px;">
                ⏰ 此連結將在 <strong>24 小時後失效</strong>，請儘快完成設置。
            </p>

            <p style="color: #666; font-size: 14px;">
                如果按鈕無法點擊，請複製以下連結到瀏覽器：<br>
                <code style="background: #f5f5f5; padding: 5px; display: inline-block; margin-top: 10px;">
                    {reset_url}
                </code>
            </p>

            <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">

            <p style="font-size: 14px; color: #666;">
                <strong>需要協助？</strong><br>
                如有任何問題，請聯絡 {organization_name} 的管理員或 Duotopia 客服團隊。
            </p>
        </div>

        <div class="footer">
            <p>此郵件由 Duotopia 系統自動發送，請勿直接回覆。</p>
            <p>© 2026 Duotopia. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        """
```

---

### Step 3: 修改邀請端點

**文件**: [backend/routers/organizations.py](../../backend/routers/organizations.py#L906)

```python
@router.post("/{org_id}/teachers/invite")
async def invite_teacher_to_organization(
    org_id: UUID,
    request: InviteTeacherRequest,
    background_tasks: BackgroundTasks,  # ← 新增：異步任務
    db: Session = Depends(get_db),
    teacher: Teacher = Depends(get_current_teacher)
):
    # ... 前面的邏輯保持不變 ...

    # === Step 8: 發送邀請郵件（修改此處） ===
    # 舊代碼（刪除）:
    # # TODO: Send invitation email with password reset link
    # # For now, just create the account

    # 新代碼：
    from services.email_service import EmailService
    email_service = EmailService()

    # 判斷是否為新創建的教師
    is_new_teacher = (existing_teacher is None)

    if is_new_teacher:
        # 異步發送邀請郵件
        background_tasks.add_task(
            email_service.send_teacher_invitation_email,
            db=db,
            teacher=teacher_to_return,
            organization_name=org.name,
            inviter_name=teacher.name
        )

        logger.info(
            f"邀請新教師: {request.email} 到機構 {org.name}, "
            f"邀請郵件已加入發送佇列"
        )
    else:
        # 現有教師加入機構，發送通知郵件（可選）
        logger.info(
            f"添加現有教師 {existing_teacher.email} 到機構 {org.name}"
        )

    # === Step 9: 返回結果（新增欄位） ===
    return {
        "id": teacher_org.id,
        "teacher_id": teacher_org.teacher_id,
        "organization_id": str(teacher_org.organization_id),
        "role": teacher_org.role,
        "is_active": teacher_org.is_active,
        # 新增
        "is_new_teacher": is_new_teacher,
        "invitation_sent": is_new_teacher,  # 是否發送邀請郵件
    }
```

---

### Step 4: 前端設置密碼頁面

#### 4.1 創建設置密碼頁面

**文件**: `frontend/src/pages/auth/SetPasswordPage.tsx`

```typescript
import React, { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Card, Input, Button, Alert, Form } from '@/components/ui'
import { api } from '@/lib/api'
import { toast } from 'sonner'

export function SetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token')

  const [loading, setLoading] = useState(false)
  const [validating, setValidating] = useState(true)
  const [tokenValid, setTokenValid] = useState(false)
  const [teacherEmail, setTeacherEmail] = useState('')

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordStrength, setPasswordStrength] = useState<{
    score: number
    feedback: string[]
  }>({ score: 0, feedback: [] })

  // 驗證 token
  useEffect(() => {
    if (!token) {
      toast.error('無效的設置密碼連結')
      navigate('/login')
      return
    }

    validateToken()
  }, [token])

  const validateToken = async () => {
    try {
      const response = await api.get('/auth/validate-reset-token', {
        params: { token }
      })

      setTokenValid(true)
      setTeacherEmail(response.data.email)
    } catch (error) {
      toast.error('連結已失效或無效，請聯絡機構管理員重新邀請')
      setTimeout(() => navigate('/login'), 3000)
    } finally {
      setValidating(false)
    }
  }

  // 密碼強度檢查
  useEffect(() => {
    if (password.length > 0) {
      const strength = checkPasswordStrength(password)
      setPasswordStrength(strength)
    }
  }, [password])

  const checkPasswordStrength = (pwd: string) => {
    const feedback: string[] = []
    let score = 0

    if (pwd.length >= 8) score++
    else feedback.push('至少 8 個字符')

    if (/[A-Z]/.test(pwd)) score++
    else feedback.push('包含大寫字母')

    if (/[a-z]/.test(pwd)) score++
    else feedback.push('包含小寫字母')

    if (/[0-9]/.test(pwd)) score++
    else feedback.push('包含數字')

    if (/[^A-Za-z0-9]/.test(pwd)) score++
    else feedback.push('包含特殊字符')

    return { score, feedback }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    // 驗證密碼
    if (password !== confirmPassword) {
      toast.error('兩次密碼輸入不一致')
      return
    }

    if (passwordStrength.score < 3) {
      toast.error('密碼強度不足，請參考下方建議')
      return
    }

    setLoading(true)

    try {
      await api.post('/auth/set-password', {
        token,
        password
      })

      toast.success('密碼設置成功！正在跳轉到登入頁面...')

      setTimeout(() => {
        navigate('/login', {
          state: { email: teacherEmail }
        })
      }, 2000)
    } catch (error: any) {
      toast.error(error.response?.data?.detail || '密碼設置失敗，請稍後再試')
    } finally {
      setLoading(false)
    }
  }

  if (validating) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
            <p>驗證連結中...</p>
          </div>
        </Card>
      </div>
    )
  }

  if (!tokenValid) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Card className="w-full max-w-md p-8">
          <Alert variant="destructive">
            <h3 className="font-semibold">連結無效</h3>
            <p className="text-sm mt-2">
              此設置密碼連結已失效或無效。請聯絡機構管理員重新邀請。
            </p>
          </Alert>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold">設置您的密碼</h1>
          <p className="text-gray-600 mt-2">
            帳號：{teacherEmail}
          </p>
        </div>

        <Form onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">
                新密碼
              </label>
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="請輸入新密碼"
                required
              />

              {/* 密碼強度指示器 */}
              {password.length > 0 && (
                <div className="mt-2">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className={`h-2 flex-1 rounded ${
                          level <= passwordStrength.score
                            ? passwordStrength.score <= 2
                              ? 'bg-red-500'
                              : passwordStrength.score <= 3
                              ? 'bg-yellow-500'
                              : 'bg-green-500'
                            : 'bg-gray-200'
                        }`}
                      />
                    ))}
                  </div>
                  {passwordStrength.feedback.length > 0 && (
                    <p className="text-xs text-gray-600 mt-1">
                      建議：{passwordStrength.feedback.join('、')}
                    </p>
                  )}
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">
                確認密碼
              </label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="請再次輸入密碼"
                required
              />
            </div>

            <Alert>
              <p className="text-sm">
                <strong>密碼要求：</strong>
              </p>
              <ul className="text-sm mt-1 space-y-1">
                <li>• 至少 8 個字符</li>
                <li>• 包含大小寫字母、數字和特殊字符</li>
              </ul>
            </Alert>

            <Button
              type="submit"
              className="w-full"
              disabled={loading || passwordStrength.score < 3}
            >
              {loading ? '設置中...' : '設置密碼並開始使用'}
            </Button>
          </div>
        </Form>
      </Card>
    </div>
  )
}
```

#### 4.2 新增路由

**文件**: `frontend/src/App.tsx` 或路由配置檔

```typescript
import { SetPasswordPage } from '@/pages/auth/SetPasswordPage'

// 在路由配置中新增
{
  path: '/teacher/set-password',
  element: <SetPasswordPage />
}
```

---

### Step 5: 後端設置密碼端點

**文件**: [backend/routers/auth.py](../../backend/routers/auth.py)

```python
@router.get("/validate-reset-token")
async def validate_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    """驗證密碼重設 token 是否有效"""
    teacher = db.query(Teacher).filter(
        Teacher.password_reset_token == token
    ).first()

    if not teacher:
        raise HTTPException(400, "無效的 token")

    # 檢查是否過期（24小時）
    if teacher.password_reset_expires_at:
        now_utc = datetime.utcnow().replace(tzinfo=None)
        expires_at = teacher.password_reset_expires_at.replace(tzinfo=None) \
            if teacher.password_reset_expires_at.tzinfo else teacher.password_reset_expires_at

        if now_utc > expires_at:
            raise HTTPException(400, "Token 已過期")

    return {
        "valid": True,
        "email": teacher.email,
        "name": teacher.name
    }


@router.post("/set-password")
async def set_password(
    request: SetPasswordRequest,
    db: Session = Depends(get_db)
):
    """設置新密碼（用於邀請）"""
    # 驗證 token
    teacher = db.query(Teacher).filter(
        Teacher.password_reset_token == request.token
    ).first()

    if not teacher:
        raise HTTPException(400, "無效的 token")

    # 檢查過期
    if teacher.password_reset_expires_at:
        now_utc = datetime.utcnow().replace(tzinfo=None)
        expires_at = teacher.password_reset_expires_at.replace(tzinfo=None) \
            if teacher.password_reset_expires_at.tzinfo else teacher.password_reset_expires_at

        if now_utc > expires_at:
            raise HTTPException(400, "Token 已過期，請聯絡管理員重新邀請")

    # 驗證密碼強度
    is_valid, error_msg = validate_password_strength(request.password)
    if not is_valid:
        raise HTTPException(400, error_msg)

    # 更新密碼
    teacher.password_hash = get_password_hash(request.password)
    teacher.password_reset_token = None
    teacher.password_reset_sent_at = None
    teacher.password_reset_expires_at = None

    # 確保帳號已啟用（機構邀請應該已經啟用）
    if not teacher.is_active:
        teacher.is_active = True
        teacher.email_verified = True

    db.commit()

    logger.info(f"教師 {teacher.email} 已設置密碼")

    return {
        "status": "success",
        "message": "密碼設置成功，請使用新密碼登入"
    }


# 請求模型
class SetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    password: str = Field(..., min_length=8)
```

---

### Step 6: 前端邀請對話框優化

**文件**: [frontend/src/components/organization/InviteTeacherDialog.tsx](../../frontend/src/components/organization/InviteTeacherDialog.tsx)

```typescript
// 修改成功提示訊息
const handleInvite = async (formData: InviteForm) => {
  try {
    setLoading(true)

    const response = await api.post(
      `/organizations/${organizationId}/teachers/invite`,
      formData
    )

    // 根據回應顯示不同訊息
    if (response.data.is_new_teacher) {
      toast.success(
        `邀請成功！已發送設置密碼郵件至 ${formData.email}`,
        {
          description: '教師將收到郵件通知，請提醒他們查收信箱（包含垃圾郵件匣）。',
          duration: 5000
        }
      )
    } else {
      toast.success(
        `成功將 ${formData.email} 添加到機構`,
        {
          description: '該教師已有帳號，可直接登入使用。'
        }
      )
    }

    onSuccess?.()
    onClose()
  } catch (error: any) {
    if (error.response?.status === 400) {
      // 顯示具體錯誤訊息
      toast.error(error.response.data.detail)
    } else {
      toast.error('邀請失敗，請稍後再試')
    }
  } finally {
    setLoading(false)
  }
}
```

---

## 🧪 測試計畫

### 單元測試

**文件**: `backend/tests/test_teacher_invitation.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

def test_invite_new_teacher_sends_email(db_session, test_org, test_teacher):
    """測試邀請新教師時發送郵件"""
    with patch('services.email_service.EmailService.send_teacher_invitation_email') as mock_email:
        mock_email.return_value = True

        response = client.post(
            f"/api/organizations/{test_org.id}/teachers/invite",
            json={
                "email": "newteacher@example.com",
                "name": "新教師",
                "role": "teacher"
            },
            headers={"Authorization": f"Bearer {get_admin_token(test_teacher)}"}
        )

        assert response.status_code == 200
        assert response.json()["is_new_teacher"] is True
        assert response.json()["invitation_sent"] is True

        # 驗證郵件發送被呼叫
        mock_email.assert_called_once()

def test_invite_existing_teacher_no_email(db_session, test_org, existing_teacher):
    """測試添加現有教師不發送郵件"""
    with patch('services.email_service.EmailService.send_teacher_invitation_email') as mock_email:
        response = client.post(
            f"/api/organizations/{test_org.id}/teachers/invite",
            json={
                "email": existing_teacher.email,
                "name": existing_teacher.name,
                "role": "teacher"
            }
        )

        assert response.status_code == 200
        assert response.json()["is_new_teacher"] is False
        mock_email.assert_not_called()

def test_set_password_with_valid_token(db_session, invited_teacher):
    """測試使用有效 token 設置密碼"""
    token = "valid_token_123"
    invited_teacher.password_reset_token = token
    invited_teacher.password_reset_expires_at = datetime.utcnow() + timedelta(hours=1)
    db_session.commit()

    response = client.post(
        "/auth/set-password",
        json={
            "token": token,
            "password": "NewSecurePassword123!"
        }
    )

    assert response.status_code == 200
    db_session.refresh(invited_teacher)
    assert invited_teacher.password_reset_token is None
    assert verify_password("NewSecurePassword123!", invited_teacher.password_hash)

def test_set_password_with_expired_token(db_session, invited_teacher):
    """測試使用過期 token 設置密碼"""
    token = "expired_token_123"
    invited_teacher.password_reset_token = token
    invited_teacher.password_reset_expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()

    response = client.post(
        "/auth/set-password",
        json={
            "token": token,
            "password": "NewSecurePassword123!"
        }
    )

    assert response.status_code == 400
    assert "過期" in response.json()["detail"]
```

### 整合測試

```python
def test_full_invitation_flow(db_session, test_org, admin_teacher):
    """測試完整邀請流程"""
    # 1. 邀請新教師
    invite_response = client.post(
        f"/api/organizations/{test_org.id}/teachers/invite",
        json={
            "email": "flow@example.com",
            "name": "流程測試",
            "role": "teacher"
        },
        headers={"Authorization": f"Bearer {get_token(admin_teacher)}"}
    )
    assert invite_response.status_code == 200

    # 2. 查詢教師記錄
    teacher = db_session.query(Teacher).filter(
        Teacher.email == "flow@example.com"
    ).first()
    assert teacher is not None
    assert teacher.password_reset_token is not None

    # 3. 驗證 token
    validate_response = client.get(
        f"/auth/validate-reset-token?token={teacher.password_reset_token}"
    )
    assert validate_response.status_code == 200

    # 4. 設置密碼
    set_password_response = client.post(
        "/auth/set-password",
        json={
            "token": teacher.password_reset_token,
            "password": "SecurePassword123!"
        }
    )
    assert set_password_response.status_code == 200

    # 5. 使用新密碼登入
    login_response = client.post(
        "/auth/teacher/login",
        json={
            "email": "flow@example.com",
            "password": "SecurePassword123!"
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
```

---

## 📊 部署檢查清單

### 部署前

- [ ] Migration 已測試（本地 + staging）
- [ ] 單元測試全部通過
- [ ] 整合測試全部通過
- [ ] SMTP 服務已配置並測試
- [ ] 前端路由已新增
- [ ] 郵件模板已檢查（文字、連結、樣式）

### 部署後

- [ ] 監控郵件發送成功率
- [ ] 檢查錯誤日誌
- [ ] 測試邀請流程（新教師 + 現有教師）
- [ ] 測試設置密碼流程
- [ ] 測試登入流程
- [ ] 收集用戶反饋

---

## 🔄 回滾計畫

如果部署後發現問題：

1. **郵件服務問題**
   - 暫時關閉郵件發送（環境變數）
   - 切換到方案 B（顯示臨時密碼）

2. **Migration 問題**
   - 執行 downgrade: `alembic downgrade -1`
   - 檢查並修正 migration
   - 重新執行 upgrade

3. **前端問題**
   - 回滾前端部署
   - 修復後重新部署

---

## 下一步

完成 Phase 1 後，閱讀：
- [03-PHASE2_SSO_PREPARATION.md](./03-PHASE2_SSO_PREPARATION.md) - SSO 整合準備
- [06-DATA_MODEL_CHANGES.md](./06-DATA_MODEL_CHANGES.md) - 完整資料模型文檔
