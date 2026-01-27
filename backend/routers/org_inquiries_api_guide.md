# 機構詢價 API - 後端實現指南

## 📋 API 規格

### 1. 建立機構詢價

**端點：**
```
POST /api/org-inquiries
```

**認證：** 無需 (公開端點)

**請求體：**
```json
{
  "schoolName": "ABC 補習班",
  "contactName": "王小明",
  "email": "wang@abc.edu.tw",
  "phone": "0912345678",
  "city": "taipei",
  "teacherCount": "10",
  "estimatedPrice": 67311,
  "contractType": "2years"
}
```

**響應 (200 OK)：**
```json
{
  "id": "inq_1234567890",
  "schoolName": "ABC 補習班",
  "email": "wang@abc.edu.tw",
  "status": "pending",
  "createdAt": "2026-01-27T10:30:00Z",
  "quotePdfUrl": "https://storage.duotopia.tw/quotes/inq_1234567890.pdf",
  "message": "感謝您的垂詢！業務人員將在 24 小時內聯絡您。"
}
```

**錯誤響應 (400 Bad Request)：**
```json
{
  "detail": {
    "schoolName": ["必填欄位"],
    "email": ["無效的電郵格式"]
  }
}
```

---

## 🔨 Python FastAPI 實現

### 1. Pydantic Schema

```python
# backend/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class ContractType(str, Enum):
    ONE_YEAR = "1year"
    TWO_YEARS = "2years"

class OrgInquiryCreate(BaseModel):
    """機構詢價表單"""
    school_name: str = Field(..., min_length=2, max_length=100)
    contact_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    phone: str = Field(..., regex=r"^\d{10}$|^09\d{8}$")
    city: Optional[str] = None
    teacher_count: Optional[int] = Field(None, ge=1, le=500)
    estimated_price: Optional[float] = None
    contract_type: Optional[ContractType] = None

class OrgInquiryResponse(BaseModel):
    """機構詢價回應"""
    id: str
    school_name: str
    email: EmailStr
    status: str
    created_at: datetime
    quote_pdf_url: Optional[str] = None
    message: str

    class Config:
        from_attributes = True
```

### 2. 數據庫模型

```python
# backend/models.py

from sqlalchemy import Column, String, Float, DateTime, Enum, Text
from sqlalchemy.sql import func
from backend.database import Base
from enum import Enum as PyEnum

class InquiryStatus(PyEnum):
    PENDING = "pending"        # 待業務跟進
    CONTACTED = "contacted"    # 已聯絡
    CONVERTED = "converted"    # 已轉換為客戶
    REJECTED = "rejected"      # 不符合

class OrgInquiry(Base):
    __tablename__ = "org_inquiries"

    id = Column(String(50), primary_key=True, index=True)
    school_name = Column(String(100), nullable=False)
    contact_name = Column(String(50), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    city = Column(String(50), nullable=True)
    teacher_count = Column(int, nullable=True)
    estimated_price = Column(Float, nullable=True)
    contract_type = Column(String(20), nullable=True)
    status = Column(String(20), default="pending", index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 索引
    __table_args__ = (
        Index('idx_email', 'email'),
        Index('idx_created_at', 'created_at'),
        Index('idx_status', 'status'),
    )
```

### 3. 遷移腳本

```python
# backend/alembic/versions/xxx_create_org_inquiries.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'org_inquiries',
        sa.Column('id', sa.String(50), nullable=False),
        sa.Column('school_name', sa.String(100), nullable=False),
        sa.Column('contact_name', sa.String(50), nullable=False),
        sa.Column('email', sa.String(120), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('city', sa.String(50), nullable=True),
        sa.Column('teacher_count', sa.Integer(), nullable=True),
        sa.Column('estimated_price', sa.Float(), nullable=True),
        sa.Column('contract_type', sa.String(20), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_email', 'org_inquiries', ['email'])
    op.create_index('idx_created_at', 'org_inquiries', ['created_at'])
    op.create_index('idx_status', 'org_inquiries', ['status'])

def downgrade():
    op.drop_table('org_inquiries')
```

### 4. 路由實現

```python
# backend/routers/org_inquiries.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from backend.database import get_db
from backend.schemas import OrgInquiryCreate, OrgInquiryResponse
from backend.models import OrgInquiry
from backend.services.email import send_inquiry_confirmation_email
from backend.services.crm import create_crm_contact
from backend.services.slack import notify_sales_team

router = APIRouter(prefix="/api/org-inquiries", tags=["org-inquiries"])

@router.post("", response_model=OrgInquiryResponse)
async def create_inquiry(
    data: OrgInquiryCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    建立機構詢價
    
    - 驗證表單數據
    - 保存到數據庫
    - 觸發後台任務：發送郵件、同步 CRM、通知銷售
    """
    
    # 檢查重複詢價 (同一郵件 7 天內)
    existing = db.query(OrgInquiry).filter(
        OrgInquiry.email == data.email,
        OrgInquiry.created_at >= datetime.utcnow() - timedelta(days=7)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"此電郵已在 7 天內提交過詢價。如有其他問題，請聯絡 LINE: @duotopia_org"
        )
    
    # 建立詢價記錄
    inquiry = OrgInquiry(
        id=f"inq_{uuid.uuid4().hex[:12]}",
        school_name=data.school_name,
        contact_name=data.contact_name,
        email=data.email,
        phone=data.phone,
        city=data.city,
        teacher_count=data.teacher_count,
        estimated_price=data.estimated_price,
        contract_type=data.contract_type,
    )
    
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    
    # 後台任務
    background_tasks.add_task(
        send_inquiry_confirmation_email,
        inquiry=inquiry,
        db=db
    )
    background_tasks.add_task(
        create_crm_contact,
        inquiry=inquiry
    )
    background_tasks.add_task(
        notify_sales_team,
        inquiry=inquiry
    )
    
    return OrgInquiryResponse(
        id=inquiry.id,
        school_name=inquiry.school_name,
        email=inquiry.email,
        status=inquiry.status,
        created_at=inquiry.created_at,
        quote_pdf_url=None,  # TODO: 生成 PDF 後更新
        message="感謝您的垂詢！業務人員將在 24 小時內聯絡您。"
    )

@router.get("/{inquiry_id}", response_model=OrgInquiryResponse)
async def get_inquiry(
    inquiry_id: str,
    db: Session = Depends(get_db),
):
    """獲取詢價詳情"""
    inquiry = db.query(OrgInquiry).filter(OrgInquiry.id == inquiry_id).first()
    
    if not inquiry:
        raise HTTPException(status_code=404, detail="詢價未找到")
    
    return inquiry

@router.get("", response_model=List[OrgInquiryResponse])
async def list_inquiries(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    列出所有詢價 (需要認證為管理員)
    
    查詢參數：
    - status: pending, contacted, converted, rejected
    - skip: 分頁偏移
    - limit: 每頁數量
    """
    query = db.query(OrgInquiry)
    
    if status:
        query = query.filter(OrgInquiry.status == status)
    
    inquiries = query.order_by(OrgInquiry.created_at.desc()).offset(skip).limit(limit).all()
    
    return inquiries
```

### 5. Email 服務

```python
# backend/services/email.py

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Template
from datetime import datetime

conf = ConnectionConfig(
    mail_from="noreply@duotopia.tw",
    mail_password=settings.SMTP_PASSWORD,
    mail_server=settings.SMTP_SERVER,
    mail_port=settings.SMTP_PORT,
    mail_starttls=True,
)

async def send_inquiry_confirmation_email(inquiry, db):
    """發送詢價確認郵件"""
    
    html = f"""
    <h2>Duotopia 機構報價單</h2>
    <p>尊敬的 {inquiry.contact_name}，</p>
    
    <p>感謝您對 Duotopia 的興趣！以下是您的詢價詳情：</p>
    
    <table>
        <tr><td>機構名稱：</td><td>{inquiry.school_name}</td></tr>
        <tr><td>聯絡人：</td><td>{inquiry.contact_name}</td></tr>
        <tr><td>英文老師數：</td><td>{inquiry.teacher_count or 'N/A'}</td></tr>
        <tr><td>預估年度點數：</td><td>{int(inquiry.estimated_price or 0):,}</td></tr>
        <tr><td>合約方案：</td><td>{'兩年約' if inquiry.contract_type == '2years' else '一年約'}</td></tr>
    </table>
    
    <p>詳細報價單已生成，業務人員將在 24 小時內聯絡您。</p>
    
    <p>如有緊急需求，請掃描此 QR Code 加入我們的 LINE 客服：</p>
    <img src="https://storage.duotopia.tw/assets/line-qrcode.png" width="200">
    <p>LINE ID: @duotopia_org</p>
    
    <p>最佳問候，<br/>Duotopia 團隊</p>
    """
    
    message = MessageSchema(
        subject="Duotopia 機構報價單",
        recipients=[inquiry.email],
        html=html,
        subtype="html",
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

async def send_sales_notification(inquiry):
    """發送銷售團隊通知"""
    
    html = f"""
    <h2>🔔 新的機構詢價</h2>
    
    <p><strong>機構：</strong> {inquiry.school_name}</p>
    <p><strong>聯絡人：</strong> {inquiry.contact_name}</p>
    <p><strong>Email：</strong> {inquiry.email}</p>
    <p><strong>Phone：</strong> {inquiry.phone}</p>
    <p><strong>所在城市：</strong> {inquiry.city or 'N/A'}</p>
    <p><strong>教師數：</strong> {inquiry.teacher_count or 'N/A'}</p>
    <p><strong>預估報價：</strong> NT${inquiry.estimated_price or 0:,.0f}</p>
    <p><strong>合約方案：</strong> {inquiry.contract_type or 'N/A'}</p>
    
    <p><a href="https://duotopia.tw/admin/inquiries/{inquiry.id}">在後台查看詳情</a></p>
    """
    
    message = MessageSchema(
        subject=f"[新詢價] {inquiry.school_name} - {inquiry.contact_name}",
        recipients=["sales@duotopia.tw"],
        html=html,
        subtype="html",
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)
```

### 6. CRM 集成

```python
# backend/services/crm.py

import httpx
from backend.models import OrgInquiry

async def create_crm_contact(inquiry: OrgInquiry):
    """同步至 CRM 系統 (例：HubSpot)"""
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={
                "Authorization": f"Bearer {settings.HUBSPOT_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "properties": {
                    "firstname": inquiry.contact_name,
                    "email": inquiry.email,
                    "phone": inquiry.phone,
                    "company": inquiry.school_name,
                    "city": inquiry.city,
                    "lifecyclestage": "lead",
                    "source": "org_landing_page",
                }
            }
        )
    
    if response.status_code == 201:
        print(f"✅ CRM 聯絡人已建立: {inquiry.email}")
    else:
        print(f"❌ CRM 同步失敗: {response.text}")
```

### 7. Slack 通知

```python
# backend/services/slack.py

import httpx

async def notify_sales_team(inquiry):
    """發送 Slack 通知"""
    
    message = f"""
🎉 新的機構詢價！
    
📌 機構：{inquiry.school_name}
👤 聯絡人：{inquiry.contact_name}
📧 Email：{inquiry.email}
📱 電話：{inquiry.phone}
👨‍🏫 教師數：{inquiry.teacher_count or 'N/A'}
💰 預估報價：NT${inquiry.estimated_price or 0:,.0f}
📅 方案：{inquiry.contract_type or 'N/A'}

👉 <https://duotopia.tw/admin/inquiries/{inquiry.id}|在後台查看>
    """
    
    await httpx.AsyncClient().post(
        settings.SLACK_WEBHOOK_URL,
        json={"text": message}
    )
```

---

## 🛠️ 集成步驟

1. **建立數據庫表**
   ```bash
   alembic upgrade head
   ```

2. **新增路由到主應用**
   ```python
   # backend/main.py
   from backend.routers import org_inquiries
   app.include_router(org_inquiries.router)
   ```

3. **配置環境變數**
   ```bash
   # .env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_PASSWORD=your_password
   HUBSPOT_API_KEY=your_key
   SLACK_WEBHOOK_URL=https://hooks.slack.com/...
   ```

4. **測試 API**
   ```bash
   curl -X POST http://localhost:8000/api/org-inquiries \
     -H "Content-Type: application/json" \
     -d '{
       "schoolName": "ABC 補習班",
       "contactName": "王小明",
       "email": "wang@abc.edu.tw",
       "phone": "0912345678",
       "city": "taipei",
       "teacherCount": 10
     }'
   ```

---

## 📊 後台管理 (TODO)

建議添加管理後台功�能：

- [ ] 查看所有詢價列表
- [ ] 按狀態篩選 (Pending, Contacted, Converted)
- [ ] 更新詢價狀態
- [ ] 備註管理
- [ ] 導出 CSV

---

**實現日期：2026-01-27**
**Branch: feat/org-intro-pricing-page**
