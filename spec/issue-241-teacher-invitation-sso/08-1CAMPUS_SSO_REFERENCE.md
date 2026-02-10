# 1Campus SSO 整合參考

> 教育部 1Campus 系統整合 API 技術文檔

## 📋 目錄

- [API 概覽](#api-概覽)
- [認證流程](#認證流程)
- [身份識別](#身份識別)
- [推播通知](#推播通知)
- [整合要點](#整合要點)

---

## API 概覽

### 官方文檔

- **系統整合 API**: https://devapi.1campus.net/doc/jasmine
- **訊息推播 API**: https://devapi.1campus.net/doc/dandelion

### API 類型

| API 名稱 | 用途 | 認證方式 |
|---------|------|---------|
| **Identity API** | 取得使用者身份資訊 | 一次性代碼（30秒有效） |
| **Class Data API** | 班級、課程、名單資料 | OAuth 2.0 client_credentials |
| **Message Push API** | 推播通知給教師/學生 | OAuth 2.0 client_credentials |

---

## 認證流程

### OAuth 2.0 Token 取得

```bash
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=YOUR_CLIENT_ID
&client_secret=YOUR_CLIENT_SECRET
&scope=jasmine.public.course.v1.classes%20jasmine.public.course.v1.classMembers
```

**響應**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5...",
  "token_type": "Bearer",
  "expires_in": 3600,  // 秒數
  "scope": "jasmine.public.course.v1.classes jasmine.public.course.v1.classMembers"
}
```

**重點**:
- Token 過期時間通常為 3600 秒（1小時）
- **建議提前 2 分鐘更新** token
- 使用 `Bearer {token}` 格式進行 API 呼叫

### Token 管理策略

```python
class OneCampusTokenManager:
    def __init__(self):
        self.token = None
        self.expires_at = None

    async def get_token(self) -> str:
        """取得有效 token，自動續約"""
        now = datetime.utcnow()

        # 提前 2 分鐘續約
        if not self.token or not self.expires_at or \
           (self.expires_at - now).total_seconds() < 120:
            await self._refresh_token()

        return self.token

    async def _refresh_token(self):
        """向 1Campus 請求新 token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.CAMPUS_CLIENT_ID,
                    "client_secret": settings.CAMPUS_CLIENT_SECRET,
                    "scope": "jasmine.public.course.v1.classes ..."
                }
            )

            data = response.json()
            self.token = data["access_token"]
            self.expires_at = datetime.utcnow() + timedelta(
                seconds=data["expires_in"]
            )
```

---

## 認證流程

### 一次性代碼機制

1Campus SSO 使用**一次性代碼**進行身份驗證：

```
┌─────────────────┐
│  1. 使用者在    │
│  1Campus 平台   │
│  點擊應用連結   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 1Campus     │
│  生成臨時代碼   │
│  (30秒有效)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 重定向到    │
│  Duotopia       │
│  ?code=xxx      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. Duotopia    │
│  用代碼呼叫     │
│  Identity API   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. 取得使用者  │
│  身份資訊       │
└─────────────────┘
```

### Identity API 呼叫

**端點**: `GET /{schoolDsns}/identity/{code}`

**範例**:
```bash
GET https://devapi.1campus.net/dev/identity/ABC123XYZ
Authorization: Bearer {access_token}
```

**響應**:
```json
{
  "account": "dev.teacher01@1campus.net",
  "language": "zh-TW",
  "school": {
    "DSNS": "dev",
    "name": "開發測試學校",
    "schoolYear": 113
  },
  "teacher": {
    "name": "張老師",
    "teacherID": "T001",
    "sourceIndex": "abc123"  // 需特定 scope
  }
}
```

**重點**:
- **代碼僅 30 秒有效**，過期需重新取得
- `account` 是跨系統唯一識別符
- `teacherID` 在特定學校內唯一，跨學校可能重複
- `sourceIndex` 需要額外 scope 才能取得

---

## 身份識別

### 多重識別欄位

1Campus 提供多種識別方式：

| 欄位 | 範例 | 特性 | 用途 |
|-----|------|------|------|
| `account` | `dev.teacher01@1campus.net` | 全域唯一 | 主要識別 |
| `teacherID` | `T001` | 學校內唯一 | 校內管理 |
| `sourceIndex` | `abc123` | 需特定 scope | 備用識別 |
| `idNumberHash` | `sha256(...)` | SHA256 雜湊 | 隱私保護識別 |

### 建議使用策略

```python
class TeacherIdentifier:
    """教師識別策略"""

    @staticmethod
    def get_unique_key(identity: dict) -> tuple:
        """取得唯一識別鍵"""
        # 優先級：account > sourceIndex > teacherID
        if identity.get("account"):
            return ("account", identity["account"])
        elif identity.get("teacher", {}).get("sourceIndex"):
            return ("sourceIndex", identity["teacher"]["sourceIndex"])
        else:
            # teacherID 僅校內唯一，需搭配 school DSNS
            return (
                "teacherID",
                f"{identity['school']['DSNS']}:{identity['teacher']['teacherID']}"
            )

    @staticmethod
    def find_or_create_teacher(db: Session, identity: dict) -> Teacher:
        """根據 1Campus 身份找到或創建教師"""
        key_type, key_value = TeacherIdentifier.get_unique_key(identity)

        # 查找現有教師
        if key_type == "account":
            teacher = db.query(Teacher).filter(
                or_(
                    Teacher.sso_account == key_value,
                    Teacher.email == key_value  # 嘗試 email 匹配
                )
            ).first()
        elif key_type == "sourceIndex":
            teacher = db.query(Teacher).filter(
                Teacher.sso_source_index == key_value
            ).first()
        else:  # teacherID
            teacher = db.query(Teacher).filter(
                Teacher.sso_teacher_id == identity["teacher"]["teacherID"],
                # 需搭配其他條件確保唯一性
            ).first()

        if not teacher:
            # 創建新教師
            teacher = Teacher(
                email=identity["account"],
                name=identity["teacher"]["name"],
                sso_provider="1campus",
                sso_account=identity["account"],
                sso_teacher_id=identity["teacher"]["teacherID"],
                sso_source_index=identity["teacher"].get("sourceIndex"),
                auth_method="sso",
                primary_auth="sso",
                is_active=True,
                email_verified=True,
                password_hash=None  # SSO 不需要密碼
            )
            db.add(teacher)
            db.commit()

        return teacher
```

---

## 推播通知

### Message Push API

**端點**: `POST /{schoolDsns}/messages`

**範例**:
```bash
POST https://devapi.1campus.net/dev/messages
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "categoryName": "Duotopia 通知",
  "title": "您收到新的機構邀請",
  "body": "XX 機構邀請您加入 Duotopia 教學平台，點擊查看詳情。",
  "receivers": {
    "teachers": [
      {
        "teacherID": "T001"
      }
    ]
  }
}
```

**響應**:
```json
{
  "messageId": "msg_123456",
  "status": "sent",
  "timestamp": "2026-02-10T10:30:00Z"
}
```

### 推播服務實現

```python
class OneCampusPushService:
    def __init__(self):
        self.token_manager = OneCampusTokenManager()
        self.base_url = settings.CAMPUS_API_URL

    async def send_invitation_push(
        self,
        school_dsns: str,
        teacher_id: str,
        org_name: str,
        invitation_url: str
    ) -> bool:
        """發送邀請推播"""
        try:
            token = await self.token_manager.get_token()

            payload = {
                "categoryName": "Duotopia 機構邀請",
                "title": f"{org_name} 邀請您加入",
                "body": (
                    f"親愛的老師，{org_name} 邀請您加入 Duotopia 教學平台。\n"
                    f"點擊連結開始使用：{invitation_url}"
                ),
                "receivers": {
                    "teachers": [{"teacherID": teacher_id}]
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/{school_dsns}/messages",
                    headers={"Authorization": f"Bearer {token}"},
                    json=payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info(f"推播發送成功: {teacher_id}")
                    return True
                else:
                    logger.error(
                        f"推播發送失敗: {teacher_id}, "
                        f"狀態碼: {response.status_code}"
                    )
                    return False

        except Exception as e:
            logger.error(f"推播發送異常: {teacher_id}, 錯誤: {str(e)}")
            return False

    async def send_batch_push(
        self,
        school_dsns: str,
        teacher_ids: list[str],
        title: str,
        body: str
    ) -> dict:
        """批次發送推播"""
        payload = {
            "categoryName": "Duotopia 通知",
            "title": title,
            "body": body,
            "receivers": {
                "teachers": [{"teacherID": tid} for tid in teacher_ids]
            }
        }

        token = await self.token_manager.get_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{school_dsns}/messages",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )

            return {
                "success": response.status_code == 200,
                "message_id": response.json().get("messageId"),
                "status": response.json().get("status")
            }
```

---

## 整合要點

### 1. 學校授權清單

**重點**: 應用只能存取已授權的學校資料

```python
async def get_authorized_schools(token: str) -> list[str]:
    """取得已授權的學校清單"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/authorized-schools",
            headers={"Authorization": f"Bearer {token}"}
        )
        return response.json()["schools"]
```

### 2. 操作身分概念

**重點**: 同一教師可能在多個學校有不同角色

```json
{
  "account": "teacher@1campus.net",
  "teacher": {
    "name": "張老師",
    "teacherID": "T001"  // 在此學校的編號
  },
  "school": {
    "DSNS": "school_a"
  }
}
```

**處理策略**:
```python
# 記錄教師在不同學校的 teacherID
class TeacherSchoolMapping(Base):
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    school_dsns = Column(String(100))  # 1Campus 學校識別碼
    campus_teacher_id = Column(String(100))  # 該校的 teacherID
```

### 3. 班級 vs 課程

**重點**: 1Campus 區分「班級」和「課程」

- **班級（Class）**: 學生的行政編制（如：高一甲班）
- **課程（Course）**: 教學活動（如：數學課）

### 4. 學期轉換

**重點**: 學年度轉換時，班級和課程資料會更新

```python
def handle_semester_change():
    """學期轉換處理"""
    # 1. 標記舊學期資料為歷史資料
    # 2. 同步新學期班級和課程
    # 3. 更新教師-班級關係
    pass
```

### 5. 錯誤處理

```python
class OneCampusError(Exception):
    """1Campus API 錯誤基類"""
    pass

class InvalidCodeError(OneCampusError):
    """無效或過期的代碼"""
    pass

class UnauthorizedSchoolError(OneCampusError):
    """未授權的學校"""
    pass

class TokenExpiredError(OneCampusError):
    """Token 過期"""
    pass

# 使用範例
try:
    identity = await campus_api.get_identity(school_dsns, code)
except InvalidCodeError:
    return {"error": "登入連結已失效，請重新操作"}
except UnauthorizedSchoolError:
    return {"error": "此學校尚未授權使用 Duotopia"}
except TokenExpiredError:
    # 自動重試
    await campus_api.refresh_token()
    identity = await campus_api.get_identity(school_dsns, code)
```

---

## 環境設定

### 開發環境

```env
# .env.development
CAMPUS_API_URL=https://devapi.1campus.net
CAMPUS_CLIENT_ID=dev_client_id
CAMPUS_CLIENT_SECRET=dev_client_secret
CAMPUS_CALLBACK_URL=http://localhost:3000/auth/campus/callback
```

### 生產環境

```env
# .env.production
CAMPUS_API_URL=https://api.1campus.net
CAMPUS_CLIENT_ID=prod_client_id
CAMPUS_CLIENT_SECRET=prod_client_secret
CAMPUS_CALLBACK_URL=https://duotopia.com/auth/campus/callback
```

---

## 測試策略

### 模擬 1Campus API

```python
# tests/mocks/campus_api_mock.py

class MockOneCampusAPI:
    """測試用的 1Campus API Mock"""

    def __init__(self):
        self.valid_codes = {}  # code -> identity

    def generate_test_code(self, teacher_id: str) -> str:
        """生成測試用代碼"""
        code = secrets.token_urlsafe(16)
        self.valid_codes[code] = {
            "account": f"test.teacher{teacher_id}@1campus.net",
            "teacher": {
                "name": f"測試教師{teacher_id}",
                "teacherID": teacher_id
            },
            "school": {
                "DSNS": "test_school",
                "name": "測試學校"
            }
        }
        return code

    async def get_identity(self, school_dsns: str, code: str):
        """模擬 Identity API"""
        if code not in self.valid_codes:
            raise InvalidCodeError("Invalid or expired code")

        identity = self.valid_codes.pop(code)  # 一次性使用
        return identity
```

---

## 下一步

- [03-PHASE2_SSO_PREPARATION.md](./03-PHASE2_SSO_PREPARATION.md) - SSO 整合準備
- [04-PHASE3_SSO_INTEGRATION.md](./04-PHASE3_SSO_INTEGRATION.md) - 完整 SSO 實現
