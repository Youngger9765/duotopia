# Issue #202: Public Demo Assignment Feature

## Problem Summary

特定帳號 `contact@duotopia.co` 底下所有作業需要能夠公開讓訪客透過短網址（如 `duotopia.co/demo/{assignment_id}`）進行預覽示範，無需登入即可體驗。

**目標**：讓首頁訪客可以直接體驗作業功能，提升轉換率。

## Requirements

### Functional Requirements
1. 公開網址格式：`/demo/{assignment_id}`
2. 僅限 `contact@duotopia.co` 帳號建立的作業可被公開存取
3. 支援的作業類型（4 種）：
   - 例句集 → 例句朗讀 (reading)
   - 例句集 → 例句重組 (rearrangement)
   - 單字集 → 單字朗讀 (vocabulary reading)
   - 單字集 → 單字選擇 (word_selection)
4. 不儲存任何進度或分數
5. 首頁新增 Demo 體驗區塊（4 種題型按鈕）
6. Demo 完成後返回首頁

### Non-Functional Requirements
- 無需認證即可存取
- API 回應格式與現有 preview API 相同，便於重用前端元件
- **Rate Limiting**：防止 API 被惡意攻擊

### Environment Requirements
- 需要在所有環境（local、develop、staging、production）都有 demo 帳號
- Production 已有 `contact@duotopia.co`，其他環境需要自動建立

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                │
├─────────────────────────────────────────────────────────────────┤
│  Home.tsx                                                       │
│    └─ New Section: "體驗四種題型"                                │
│        └─ 4 Demo Buttons (從 API 取得 assignment_id)            │
│        └─ Opens DemoModal (slide-in from right)                 │
│                                                                 │
│  /demo/:assignmentId → DemoAssignmentPage.tsx                   │
│    └─ Reuses StudentActivityPageContent (isDemoMode=true)       │
│    └─ On complete → Return to homepage                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Backend                                 │
├─────────────────────────────────────────────────────────────────┤
│  NEW: /api/demo/config (GET demo assignment IDs from DB)        │
│  NEW: /api/demo/assignments/{id}/preview (NO AUTH + Rate Limit) │
│  NEW: /api/demo/assignments/{id}/preview/rearrangement-*        │
│  NEW: /api/demo/assignments/{id}/preview/word-selection-*       │
│  NEW: /api/demo/assignments/preview/assess-speech               │
│                                                                 │
│  Validation: assignment.teacher.email == DEMO_TEACHER_EMAIL     │
│  Rate Limit: slowapi (e.g., 60 requests/minute per IP)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Database                                │
├─────────────────────────────────────────────────────────────────┤
│  NEW TABLE: demo_config                                         │
│    - key: VARCHAR (PRIMARY KEY)                                 │
│    - value: VARCHAR                                             │
│    - updated_at: TIMESTAMP                                      │
│                                                                 │
│  Keys:                                                          │
│    - demo_reading_assignment_id                                 │
│    - demo_rearrangement_assignment_id                           │
│    - demo_vocabulary_assignment_id                              │
│    - demo_word_selection_assignment_id                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Database Migration: Demo Account Seeding

建立 migration 在 deploy 時自動建立 demo 帳號（如果不存在）。

**File**: `backend/alembic/versions/YYYYMMDD_HHMM_add_demo_teacher_account.py`

```python
"""Add demo teacher account if not exists

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# Demo account configuration
DEMO_EMAIL = "contact@duotopia.co"
DEMO_NAME = "Duotopia Demo"
# Password hash for a secure default password (will need to be set properly)
DEMO_PASSWORD_HASH = "$2b$12$..."  # bcrypt hash

def upgrade():
    # 使用 IF NOT EXISTS 確保冪等性
    op.execute(f"""
        INSERT INTO teachers (email, password_hash, name, is_active, is_demo, created_at)
        SELECT '{DEMO_EMAIL}', '{DEMO_PASSWORD_HASH}', '{DEMO_NAME}', true, true, NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM teachers WHERE email = '{DEMO_EMAIL}'
        );
    """)

def downgrade():
    # 不刪除 demo 帳號（保護 production 資料）
    pass
```

**注意**：
- 使用 `INSERT ... WHERE NOT EXISTS` 確保冪等性
- Production 已有此帳號，migration 不會重複建立
- `is_demo = true` 標記此為 demo 帳號

### 2. Database Migration: Demo Config Table

**File**: `backend/alembic/versions/YYYYMMDD_HHMM_add_demo_config_table.py`

```python
"""Add demo_config table for configurable demo assignment IDs

Revision ID: xxxx
"""

def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS demo_config (
            key VARCHAR(100) PRIMARY KEY,
            value VARCHAR(500),
            description VARCHAR(500),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
    """)

    # Insert default keys (values to be set via DB)
    op.execute("""
        INSERT INTO demo_config (key, value, description) VALUES
            ('demo_reading_assignment_id', NULL, '例句朗讀 Demo 作業 ID'),
            ('demo_rearrangement_assignment_id', NULL, '例句重組 Demo 作業 ID'),
            ('demo_vocabulary_assignment_id', NULL, '單字朗讀 Demo 作業 ID'),
            ('demo_word_selection_assignment_id', NULL, '單字選擇 Demo 作業 ID')
        ON CONFLICT (key) DO NOTHING;
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS demo_config;")
```

### 3. Backend: Demo Router with Rate Limiting

**File**: `backend/routers/demo.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
import os

router = APIRouter(prefix="/api/demo", tags=["demo"])

# Rate limiting: 60 requests per minute per IP
limiter = Limiter(key_func=get_remote_address)

DEMO_TEACHER_EMAIL = os.getenv("DEMO_TEACHER_EMAIL", "contact@duotopia.co")

def get_demo_assignment(assignment_id: int, db: Session) -> Assignment:
    """驗證作業是否屬於 demo 帳號"""
    assignment = (
        db.query(Assignment)
        .join(Classroom)
        .join(Teacher)
        .filter(
            Assignment.id == assignment_id,
            Teacher.email == DEMO_TEACHER_EMAIL,
        )
        .first()
    )
    if not assignment:
        raise HTTPException(404, "Demo assignment not found")
    return assignment


@router.get("/config")
@limiter.limit("30/minute")
async def get_demo_config(request: Request, db: Session = Depends(get_db)):
    """取得 demo 設定（4 種題型的 assignment_id）"""
    configs = db.query(DemoConfig).all()
    return {c.key: c.value for c in configs}


@router.get("/assignments/{assignment_id}/preview")
@limiter.limit("60/minute")
async def get_demo_preview(
    request: Request,
    assignment_id: int,
    db: Session = Depends(get_db),
):
    """取得 demo 作業預覽（無需認證）"""
    assignment = get_demo_assignment(assignment_id, db)
    # 重用現有 preview 邏輯...
    return build_preview_response(assignment, db)


@router.post("/assignments/preview/assess-speech")
@limiter.limit("120/minute")  # Speech assessment needs more quota
async def demo_assess_speech(
    request: Request,
    data: SpeechAssessmentRequest,
    db: Session = Depends(get_db),
):
    """Demo 語音評估（無需認證，不儲存錄音）"""
    # 驗證 assignment 屬於 demo 帳號
    get_demo_assignment(data.assignment_id, db)
    # 呼叫語音評估服務...
    return assess_speech(data, save_recording=False)

# ... 其他 endpoints (rearrangement, word_selection)
```

### 4. Backend: Model for Demo Config

**File**: `backend/models/demo_config.py`

```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from database import Base

class DemoConfig(Base):
    """Demo 設定表 - 儲存可從 DB 修改的 demo 設定"""

    __tablename__ = "demo_config"

    key = Column(String(100), primary_key=True)
    value = Column(String(500), nullable=True)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 5. Frontend: Homepage Demo Section

在「為什麼選擇 Duotopia」和「準備好重獲老師的自由時光」之間新增 Demo 體驗區塊。

**Location**: `frontend/src/pages/Home.tsx` (line 377, before CTA section)

```tsx
{/* 第 4.5 區段: Demo 體驗區 */}
<section className="py-20 bg-gradient-to-b from-gray-50 to-white">
  <div className="container mx-auto px-4">
    <div className="max-w-6xl mx-auto">
      <div className="text-center mb-12">
        <h2 className="text-3xl lg:text-4xl font-bold text-gray-900 mb-4">
          {t("home.demo.title")}
        </h2>
        <p className="text-xl text-gray-600">
          {t("home.demo.subtitle")}
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* 例句朗讀 */}
        <DemoCard
          icon={<Mic className="h-8 w-8" />}
          title={t("home.demo.reading.title")}
          description={t("home.demo.reading.description")}
          onClick={() => openDemoModal("reading")}
          gradient="from-blue-500 to-indigo-600"
        />

        {/* 例句重組 */}
        <DemoCard
          icon={<Puzzle className="h-8 w-8" />}
          title={t("home.demo.rearrangement.title")}
          description={t("home.demo.rearrangement.description")}
          onClick={() => openDemoModal("rearrangement")}
          gradient="from-green-500 to-emerald-600"
        />

        {/* 單字朗讀 */}
        <DemoCard
          icon={<BookOpen className="h-8 w-8" />}
          title={t("home.demo.vocabulary.title")}
          description={t("home.demo.vocabulary.description")}
          onClick={() => openDemoModal("vocabulary")}
          gradient="from-purple-500 to-pink-600"
        />

        {/* 單字選擇 */}
        <DemoCard
          icon={<CheckSquare className="h-8 w-8" />}
          title={t("home.demo.wordSelection.title")}
          description={t("home.demo.wordSelection.description")}
          onClick={() => openDemoModal("word_selection")}
          gradient="from-orange-500 to-red-600"
        />
      </div>
    </div>
  </div>
</section>

{/* Demo Modal - Slide in from right */}
<DemoModal
  isOpen={demoModalOpen}
  onClose={() => setDemoModalOpen(false)}
  assignmentId={selectedDemoAssignmentId}
  demoType={selectedDemoType}
/>
```

### 6. Frontend: Demo Modal Component

**File**: `frontend/src/components/DemoModal.tsx`

```tsx
import { Sheet, SheetContent } from "@/components/ui/sheet";

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignmentId: number | null;
  demoType: string;
}

export function DemoModal({ isOpen, onClose, assignmentId, demoType }: DemoModalProps) {
  if (!assignmentId) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-2xl lg:max-w-4xl p-0"
      >
        {/* Header with close button */}
        <div className="sticky top-0 z-50 bg-white border-b p-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {t(`home.demo.${demoType}.title`)} - 體驗模式
          </h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Demo Content */}
        <div className="h-[calc(100vh-64px)] overflow-y-auto">
          <StudentActivityPageContent
            activities={activities}
            assignmentTitle={title}
            assignmentId={assignmentId}
            practiceMode={practiceMode}
            isDemoMode={true}
            isPreviewMode={true}
            onBack={onClose}
            onSubmit={() => {
              toast.success(t("demo.complete"));
              onClose();
            }}
          />
        </div>
      </SheetContent>
    </Sheet>
  );
}
```

### 7. Frontend: Demo Page (Direct URL Access)

**File**: `frontend/src/pages/DemoAssignmentPage.tsx`

```tsx
export default function DemoAssignmentPage() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [activityData, setActivityData] = useState(null);

  useEffect(() => {
    fetchDemoData();
  }, [assignmentId]);

  const fetchDemoData = async () => {
    const response = await fetch(`/api/demo/assignments/${assignmentId}/preview`);
    if (!response.ok) {
      navigate("/");  // Invalid demo → redirect to home
      return;
    }
    setActivityData(await response.json());
  };

  const handleComplete = () => {
    toast.success(t("demo.complete"));
    navigate("/");  // Return to homepage
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Demo Mode Banner */}
      <div className="bg-blue-600 text-white py-2 px-4 text-center">
        <span>{t("demo.banner")}</span>
        <Button variant="link" className="text-white ml-4" onClick={() => navigate("/")}>
          {t("demo.backToHome")}
        </Button>
      </div>

      <StudentActivityPageContent
        activities={activityData.activities}
        isDemoMode={true}
        isPreviewMode={true}
        onBack={() => navigate("/")}
        onSubmit={handleComplete}
      />
    </div>
  );
}
```

### 8. I18n: Add Translation Keys

**File**: `frontend/src/i18n/locales/zh-TW/translation.json`

```json
{
  "home": {
    "demo": {
      "title": "立即體驗四種學習模式",
      "subtitle": "無需註冊，點擊即可體驗 Duotopia 的互動式學習",
      "reading": {
        "title": "例句朗讀",
        "description": "AI 即時評分你的發音"
      },
      "rearrangement": {
        "title": "例句重組",
        "description": "拖曳單字組成正確句子"
      },
      "vocabulary": {
        "title": "單字朗讀",
        "description": "學習單字正確發音"
      },
      "wordSelection": {
        "title": "單字選擇",
        "description": "從選項中選出正確答案"
      }
    }
  },
  "demo": {
    "banner": "體驗模式 - 進度不會被儲存",
    "backToHome": "返回首頁",
    "complete": "體驗完成！歡迎註冊獲得完整功能"
  }
}
```

---

## Files to Modify/Create

### Backend - New Files
| File | Purpose |
|------|---------|
| `backend/routers/demo.py` | Demo API router (no auth, rate limited) |
| `backend/models/demo_config.py` | DemoConfig model |
| `backend/alembic/versions/xxx_add_demo_teacher.py` | Seed demo account |
| `backend/alembic/versions/xxx_add_demo_config.py` | Demo config table |

### Backend - Modified Files
| File | Change |
|------|--------|
| `backend/main.py` | Register demo router |
| `backend/models/__init__.py` | Export DemoConfig |

### Frontend - New Files
| File | Purpose |
|------|---------|
| `frontend/src/pages/DemoAssignmentPage.tsx` | Demo page (direct URL) |
| `frontend/src/components/DemoModal.tsx` | Slide-in demo modal |
| `frontend/src/components/DemoCard.tsx` | Demo feature card |
| `frontend/src/lib/demoApi.ts` | Demo API client |

### Frontend - Modified Files
| File | Change |
|------|--------|
| `frontend/src/App.tsx` | Add `/demo/:assignmentId` route |
| `frontend/src/pages/Home.tsx` | Add demo section |
| `frontend/src/pages/student/StudentActivityPageContent.tsx` | Add `isDemoMode` prop |
| `frontend/src/i18n/locales/*/translation.json` | Add demo translations |

---

## Test Plan

### Unit Tests
- [ ] Demo API returns 404 for non-demo teacher assignments
- [ ] Demo API works without authentication
- [ ] Rate limiting blocks excessive requests
- [ ] Demo config API returns correct assignment IDs

### Integration Tests
- [ ] Complete demo flow: load → interact → complete → return home
- [ ] All 4 practice modes work in demo
- [ ] Modal opens and closes correctly
- [ ] Direct URL access works

### Manual Tests
- [ ] Verify demo account is created on fresh DB
- [ ] Test rate limiting (60+ requests)
- [ ] Mobile responsiveness of demo section and modal
- [ ] Speech recording works in demo mode

---

## Implementation Steps

### Phase 1: Database & Backend (Priority: High)
1. Create migration for demo account seeding
2. Create migration for demo_config table
3. Create DemoConfig model
4. Create demo router with rate limiting
5. Register router in main.py
6. Write tests

### Phase 2: Frontend Demo Page (Priority: High)
1. Create DemoAssignmentPage.tsx
2. Modify StudentActivityPageContent to support isDemoMode
3. Add route in App.tsx
4. Create demoApi.ts

### Phase 3: Homepage Integration (Priority: Medium)
1. Create DemoCard component
2. Create DemoModal component (slide-in sheet)
3. Add demo section to Home.tsx
4. Add i18n translations
5. Connect to /api/demo/config for assignment IDs

### Phase 4: Polish & Testing (Priority: Medium)
1. Add loading states
2. Add error handling
3. Mobile optimization
4. Analytics integration (optional)

---

## Security Considerations

1. **Rate Limiting**: 使用 slowapi，60 requests/minute per IP
2. **Referer Validation**: Demo Azure Speech Token API 需要 referer 驗證
   - 設定環境變數 `DEMO_ALLOWED_ORIGINS`（逗號分隔的允許來源）
   - Production: `DEMO_ALLOWED_ORIGINS=https://duotopia.co,https://www.duotopia.net`
   - Staging: `DEMO_ALLOWED_ORIGINS=https://staging.duotopia.com`
   - Development: 預設允許 localhost
3. **No Sensitive Data**: Demo API 只返回作業內容，無學生資料
4. **Demo Account Isolation**: 只允許存取 demo 帳號的作業
5. **No Recording Storage**: Demo 模式不儲存語音錄音
6. **CORS**: 確保 demo API 的 CORS 設定正確

---

## Configuration Management

### 設定 Demo Assignment IDs

部署後，在資料庫中設定各題型的 assignment_id：

```sql
-- 設定例句朗讀 Demo 作業
UPDATE demo_config SET value = '123' WHERE key = 'demo_reading_assignment_id';

-- 設定例句重組 Demo 作業
UPDATE demo_config SET value = '124' WHERE key = 'demo_rearrangement_assignment_id';

-- 設定單字朗讀 Demo 作業
UPDATE demo_config SET value = '125' WHERE key = 'demo_vocabulary_assignment_id';

-- 設定單字選擇 Demo 作業
UPDATE demo_config SET value = '126' WHERE key = 'demo_word_selection_assignment_id';
```

這樣可以隨時從 DB 調整要展示的 demo 作業，無需重新部署。

---

## Worktree Information

- **Worktree**: `.worktrees/issue-202`
- **Branch**: `fix/issue-202-public-demo-assignment`
- **Base**: `origin/staging`

---

Please review and confirm this plan, or provide feedback.
