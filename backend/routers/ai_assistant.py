"""
AI Assistant API Routes

Endpoints for the AI assistant to parse and understand user input
using Vertex AI (Gemini). Used by the frontend state machine to
handle free-text understanding.

Guide files (source of truth for domain knowledge) are loaded from:
  docs/ai-assistant-guides/
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from services.vertex_ai import vertex_ai_service

logger = logging.getLogger(__name__)

# ============ Load Guide Files ============

_GUIDES_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "ai-assistant-guides"


def _load_guide(filename: str) -> str:
    """Load a guide file from docs/ai-assistant-guides/."""
    path = _GUIDES_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"Guide file not found: {path}")
        return ""


# Shared knowledge (roles, page navigation, query handling, etc.)
COMMON_RULES = _load_guide("common-rules.md")
FIND_FEATURE_GUIDE = _load_guide("find-feature.md")

# ============ Deterministic Email Domain Validation ============

# Known correct domains → common typos
KNOWN_DOMAINS = {
    "gmail.com": ["gmal.com", "gmai.com", "gmial.com", "gamil.com", "gmaill.com", "gnail.com", "gmali.com", "gail.com", "gmail.co"],
    "yahoo.com": ["yaho.com", "yahooo.com", "yhoo.com", "yahoo.co", "yhaoo.com"],
    "yahoo.com.tw": ["yahoo.com.t", "yaho.com.tw"],
    "hotmail.com": ["hotmal.com", "hotmial.com", "hotmali.com", "hotamail.com", "hotmail.co", "hotmai.com"],
    "outlook.com": ["outlok.com", "outllook.com", "outlool.com", "outloook.com", "outlook.co"],
    "icloud.com": ["iclould.com", "icloud.co", "icoud.com"],
    "live.com": ["live.co", "liv.com"],
    "msn.com": ["msn.co"],
}

# Build reverse lookup: typo → suggested correct domain
_TYPO_TO_CORRECT: dict[str, str] = {}
for correct, typos in KNOWN_DOMAINS.items():
    for typo in typos:
        _TYPO_TO_CORRECT[typo] = correct


def check_email_domain_typo(email: str) -> str | None:
    """Return a warning message if the email domain looks like a typo of a known domain, else None."""
    if "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1].lower()
    suggested = _TYPO_TO_CORRECT.get(domain)
    if suggested:
        return f"域名可能拼錯，是否為 {suggested}？"
    return None


import re

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"09\d{8}")


def fallback_parse_teachers(user_input: str) -> dict:
    """Basic deterministic parser — used when Gemini fails.
    Extracts emails from text and builds teacher records."""
    text = user_input.strip()

    if not text:
        return {
            "teachers": [],
            "message": "請提供教師的姓名和 Email。",
        }

    emails = _EMAIL_RE.findall(text)
    phones = _PHONE_RE.findall(text)

    # No email found
    if not emails:
        if phones:
            return {
                "teachers": [],
                "message": "看起來您提供的是電話號碼，這裡需要 Email 地址。請提供教師的姓名和 Email。",
            }
        return {
            "teachers": [],
            "message": "無法從輸入中找到 Email，請提供教師的姓名和 Email，例如：\n王小明 wang@gmail.com",
        }

    teachers = []
    for email in emails:
        typo_warning = check_email_domain_typo(email)
        teachers.append({
            "name": "",
            "email": email,
            "role": "teacher",
            "valid": False,
            "error": typo_warning or "缺少姓名",
        })

    message = f"已從輸入中找到 {len(teachers)} 個 Email，請補充姓名資料。"
    return {"teachers": teachers, "message": message}


router = APIRouter(prefix="/api/ai/assistant", tags=["ai-assistant"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/teacher/login")


# ============ Request / Response Models ============


class ParseTeachersRequest(BaseModel):
    user_input: str = Field(..., description="User's free-text input with teacher info")


class ParsedTeacher(BaseModel):
    name: str = Field(..., description="Teacher name")
    email: str = Field(..., description="Teacher email")
    role: str = Field(
        default="teacher", description="Role: 'teacher' or 'org_admin'"
    )
    valid: bool = Field(default=True, description="Whether the record is valid")
    error: Optional[str] = Field(
        default=None, description="Validation error message if invalid"
    )


class ParseTeachersResponse(BaseModel):
    teachers: List[ParsedTeacher]
    message: str = Field(..., description="AI response message in Chinese")


class ProcessModificationRequest(BaseModel):
    user_input: str = Field(
        ..., description="User's modification instruction in natural language"
    )
    current_teachers: List[ParsedTeacher] = Field(
        ..., description="Current teacher list to modify"
    )


class ProcessModificationResponse(BaseModel):
    teachers: List[ParsedTeacher]
    message: str = Field(..., description="AI response message in Chinese")
    action: str = Field(
        ...,
        description="Action taken: 'modify', 'add', 'remove', 'unclear'",
    )


class ParseClassroomsRequest(BaseModel):
    user_input: str = Field(..., description="User's free-text input with classroom info")


class ParsedClassroom(BaseModel):
    name: str = Field(..., description="Classroom name")
    level: str = Field(default="A1", description="CEFR level: PREA|A1|A2|B1|B2|C1|C2")
    valid: bool = Field(default=True, description="Whether the record is valid")
    error: Optional[str] = Field(default=None, description="Validation error message if invalid")


class ParseClassroomsResponse(BaseModel):
    classrooms: List[ParsedClassroom]
    message: str = Field(..., description="AI response message in Chinese")


class ProcessClassroomModificationRequest(BaseModel):
    user_input: str = Field(..., description="User's modification instruction")
    current_classrooms: List[ParsedClassroom] = Field(..., description="Current classroom list")


class ProcessClassroomModificationResponse(BaseModel):
    classrooms: List[ParsedClassroom]
    message: str = Field(..., description="AI response message in Chinese")
    action: str = Field(..., description="Action taken: 'modify', 'add', 'remove', 'unclear'")


class ParseStudentsRequest(BaseModel):
    user_input: str = Field(..., description="User's free-text input with student info")


class ParsedStudent(BaseModel):
    name: str = Field(..., description="Student name")
    birthdate: str = Field(default="", description="Birthdate in YYYY-MM-DD format")
    valid: bool = Field(default=True, description="Whether the record is valid")
    error: Optional[str] = Field(default=None, description="Validation error message if invalid")


class ParseStudentsResponse(BaseModel):
    students: List[ParsedStudent]
    message: str = Field(..., description="AI response message in Chinese")


class ProcessStudentModificationRequest(BaseModel):
    user_input: str = Field(..., description="User's modification instruction")
    current_students: List[ParsedStudent] = Field(..., description="Current student list")


class ProcessStudentModificationResponse(BaseModel):
    students: List[ParsedStudent]
    message: str = Field(..., description="AI response message in Chinese")
    action: str = Field(..., description="Action taken: 'modify', 'add', 'remove', 'unclear'")


class ExistingStudentData(BaseModel):
    id: int = Field(..., description="Student ID")
    name: str = Field(..., description="Student name")
    birthdate: str = Field(default="", description="Birthdate in YYYY-MM-DD format")
    email: str = Field(default="", description="Student email")
    student_number: str = Field(default="", description="Student number")
    phone: str = Field(default="", description="Phone number")


class BatchStudentEditRequest(BaseModel):
    user_input: str = Field(..., description="User's natural language edit instruction")
    current_students: List[ExistingStudentData] = Field(..., description="Current student list with IDs")


class BatchStudentEditResponse(BaseModel):
    students: List[ExistingStudentData]
    message: str = Field(..., description="AI response message in Chinese")
    action: str = Field(..., description="Action taken: 'modify' or 'unclear'")


class FindFeatureRequest(BaseModel):
    user_input: str = Field(..., description="User's question about finding a feature")
    context: str = Field(default="organization", description="Current backend: 'organization' or 'teacher'")
    user_roles: Optional[List[str]] = Field(default_factory=list, description="User's roles, e.g. ['org_admin', 'teacher']")
    current_path: str = Field(default="", description="User's current URL path, e.g. '/teacher/classrooms'")
    workspace_mode: str = Field(default="", description="Teacher backend workspace: 'personal' or 'organization'")
    workspace_org: str = Field(default="", description="Selected organization name in org mode")
    workspace_school: str = Field(default="", description="Selected school name in org mode")


class NavigationItem(BaseModel):
    label: str = Field(..., description="Button label")
    path: str = Field(..., description="Navigation path")


class FindFeatureResponse(BaseModel):
    message: str = Field(..., description="AI response message in Chinese")
    navigation: List[NavigationItem] = Field(
        default_factory=list, description="Suggested navigation links"
    )


class ChatMessageItem(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatFlowState(BaseModel):
    type: str = Field(..., description="Workflow type: 'classroom' or 'students'")
    step: str = Field(..., description="Current flow step, e.g. 'choose_mode'")
    available_actions: List[str] = Field(
        default_factory=list,
        description="Button labels + values currently visible, e.g. ['一個一個新增=mode:single', '批次新增=mode:batch']",
    )
    current_data: Optional[dict] = Field(
        default=None,
        description="Current data list for modification steps. e.g. {'students': [...]} or {'classrooms': [...]}",
    )


class ChatRequest(BaseModel):
    user_input: str = Field(..., description="User's free-text input")
    conversation_history: List[ChatMessageItem] = Field(
        default_factory=list, description="Recent conversation messages"
    )
    flow_state: Optional[ChatFlowState] = Field(
        default=None, description="Current workflow state if a flow is active"
    )
    context: str = Field(default="teacher", description="'organization' or 'teacher'")
    current_path: str = Field(default="", description="User's current URL path")
    workspace_mode: str = Field(default="personal", description="'personal' or 'organization'")


class ChatResponse(BaseModel):
    action: str = Field(
        ...,
        description="Action: select_action | provide_data | respond | start_workflow | switch_workflow | find_feature",
    )
    message: Optional[str] = Field(
        default=None, description="AI response message (for respond action)"
    )
    selected_action: Optional[str] = Field(
        default=None, description="Button value to select (for select_action)"
    )
    workflow_type: Optional[str] = Field(
        default=None, description="Workflow type: 'classroom' or 'students'"
    )
    sub_intent: Optional[str] = Field(
        default=None, description="Sub-intent: 'add' or 'edit'"
    )
    parsed_data: Optional[dict] = Field(
        default=None, description="Pre-parsed data for the flow"
    )
    navigation: Optional[List[NavigationItem]] = Field(
        default=None, description="Navigation suggestions"
    )
    respond_type: Optional[str] = Field(
        default=None,
        description="Sub-type when action=respond: 'greeting' | 'off_topic' | 'unclear'",
    )


class DetectIntentRequest(BaseModel):
    user_input: str = Field(..., description="User's free-text input")
    context: str = Field(default="teacher", description="'organization' or 'teacher'")
    current_path: str = Field(default="", description="User's current URL path")
    workspace_mode: str = Field(default="personal", description="'personal' or 'organization'")
    available_actions: Optional[List[str]] = Field(
        default=None,
        description="Currently visible button labels for context-aware matching",
    )


class DetectIntentResponse(BaseModel):
    intent: str = Field(
        ...,
        description="Detected intent: classroom_management | student_management | find_feature | quick_start | delete_request | greeting | off_topic | unclear",
    )
    sub_intent: Optional[str] = Field(
        default=None, description="Sub-intent: 'add' | 'edit' | None"
    )
    parsed_data: Optional[dict] = Field(
        default=None, description="Pre-parsed data for the flow"
    )
    message: Optional[str] = Field(
        default=None, description="Direct reply message (for greeting, off_topic, delete, unclear)"
    )
    navigation: Optional[List[NavigationItem]] = Field(
        default=None, description="Navigation suggestions (for delete_request)"
    )


# ============ System Prompts (built from guide files) ============

# Add-teacher flow context (not in common-rules because it's flow-specific)
_ADD_TEACHER_CONTEXT = """
### 新增教師流程說明
- 新增的教師會收到認證信和密碼設定信
- 如果教師已有帳號（email 已註冊），系統會直接把教師加入機構，下次登入即可看到
- 新增時只能選「機構管理員 (org_admin)」或「教師 (teacher)」兩種角色
- 機構擁有者 (org_owner) 只能在建立機構時自動產生，無法透過新增教師指派
"""

PARSE_TEACHERS_SYSTEM_PROMPT = COMMON_RULES + _ADD_TEACHER_CONTEXT + """
## 你的角色
你是「新增教師」流程中的資料解析助手。用戶正在新增教師到機構中。

## 你的任務
從用戶的自由文字中提取教師資料（姓名、Email、角色）。

## 三個原則
1. **能解析多少就解析多少** — 資料不完整就標記 valid=false 並說明缺什麼，讓用戶補充
2. **不確定就友善詢問** — 看不懂就用 message 禮貌地請用戶說明，不要猜錯
3. **離題就禮貌引導回來** — 用戶可能打招呼、問查詢類問題、或問系統功能。先根據上方「查詢類問題處理」和「頁面導引清單」給出具體回答（含頁面名稱），再引導回「請提供姓名和 Email」

## 角色對照
- 管理員、機構管理員、admin → `org_admin`
- 教師、老師、teacher、未標註 → `teacher`

## 驗證規則
- Email 要有 @ 和 . ，否則 valid=false
- 缺姓名 → valid=false, error=「缺少姓名」
- 缺 Email → valid=false, error=「缺少 Email」
- 重複 Email → 後面的 valid=false, error=「Email 重複」

## 輸出格式（永遠回傳有效 JSON）
{
  "teachers": [
    {"name": "姓名", "email": "email@example.com", "role": "teacher", "valid": true, "error": null}
  ],
  "message": "中文訊息"
}

完全無法解析時回 teachers=[]，用 message 友善引導。
"""

PROCESS_MODIFICATION_SYSTEM_PROMPT = COMMON_RULES + _ADD_TEACHER_CONTEXT + """
## 你的角色
你是「新增教師」流程中的資料修改助手。用戶正在修改一份教師名單。

## 你的任務
理解用戶的口語修改指令，回傳修改後的完整列表。

## 三個原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字，從上下文推斷。名單只有一人時不需指定姓名
2. **不確定就問** — 用 message 禮貌詢問，action 設 "unclear"，回傳原始列表不變
3. **離題就引導回來** — 友善回應後引導回修改操作

## 角色對照
- 管理員、機構管理員、admin → `org_admin`
- 教師、老師、teacher → `teacher`

## 輸出格式（永遠回傳有效 JSON）
{
  "teachers": [...完整修改後的列表...],
  "message": "中文訊息",
  "action": "modify|add|remove|unclear"
}
"""

PARSE_CLASSROOMS_SYSTEM_PROMPT = """
## 你的角色
你是「新增班級」流程中的資料解析助手。用戶正在建立班級。

## 你的任務
從用戶的自由文字中提取班級資料（名稱、語言等級）。

## 關鍵能力
1. **理解自然語言序列** — 例如：
   - 「114-2 110 A2, 114-2 109 B1, 以此類推到 101 都是 B1」
     → 展開成 114-2 110 (A2), 114-2 109 (B1), 114-2 108 (B1), ..., 114-2 101 (B1)
   - 「A班到E班 都是 A1」→ A班 (A1), B班 (A1), C班 (A1), D班 (A1), E班 (A1)
   - 「一年級到三年級」→ 一年級, 二年級, 三年級
2. **推斷等級** — 如果用戶對某些班級指定了等級，對其餘未指定的使用上下文中最近的等級
3. **容錯** — 「班及」→「班級」、「bl」→「B1」等常見打字錯誤

## 語言等級
有效等級：PREA, A1, A2, B1, B2, C1, C2
- 不區分大小寫
- 無法辨識的等級 → valid=false, error="等級不正確"
- 未指定等級 → 預設 A1

## 驗證規則
- 班級名稱為空 → valid=false, error="缺少名稱"
- 名稱超過 100 字元 → valid=false, error="名稱過長"
- 名稱含有中文或英文髒話、不雅詞彙、侮辱性用語 → valid=false, error="班級名稱包含不適當用語，請修改"
  - 常見髒話包括但不限於：幹、靠、他媽、操、fuck、shit、damn、ass、bitch 等
  - 偽裝寫法也要偵測（如用符號替代、拼音、諧音）

## 輸出格式（永遠回傳有效 JSON）
{
  "classrooms": [
    {"name": "班級名稱", "level": "A1", "valid": true, "error": null}
  ],
  "message": "中文訊息"
}

完全無法解析時回 classrooms=[]，用 message 友善引導。
例如用戶打招呼或問不相關問題時，回 classrooms=[]，message 引導回「請提供班級名稱和等級」。
"""

PROCESS_CLASSROOM_MODIFICATION_SYSTEM_PROMPT = """
## 你的角色
你是「新增班級」流程中的資料修改助手。用戶正在修改一份班級名單。

## 你的任務
理解用戶的口語修改指令，回傳修改後的完整列表。

## 三個原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字，從上下文推斷。名單只有一筆時不需指定名稱
2. **不確定就問** — 用 message 禮貌詢問，action 設 "unclear"，回傳原始列表不變
3. **離題就引導回來** — 友善回應後引導回修改操作

## 語言等級
有效等級：PREA, A1, A2, B1, B2, C1, C2

## 驗證規則
- 名稱含有中文或英文髒話、不雅詞彙 → valid=false, error="班級名稱包含不適當用語，請修改"

## 輸出格式（永遠回傳有效 JSON）
{
  "classrooms": [...完整修改後的列表...],
  "message": "中文訊息",
  "action": "modify|add|remove|unclear"
}
"""

FIND_FEATURE_SYSTEM_PROMPT = COMMON_RULES + "\n\n" + FIND_FEATURE_GUIDE + """

## 輸出格式（永遠回傳有效 JSON）
{
  "message": "中文回覆，簡短說明推薦的頁面用途",
  "navigation": [
    {"label": "頁面名稱", "path": "/organization/{orgId}/teachers"}
  ]
}

navigation 陣列可以有 0~3 個項目。找不到對應頁面時 navigation 為空陣列。
path 中的 {orgId}、{schoolId} 保持原樣，前端會替換。
"""

DETECT_INTENT_SYSTEM_PROMPT = COMMON_RULES + """

## 你的角色
你是教師個人後台 AI 助手的意圖路由器。用戶會用自然語言告訴你他想做什麼，你要判斷意圖並同時解析可用的資料。

## 語氣
專業但溫暖，像真人對話。不要像機器人、不要用罐頭回覆。

## 可用意圖

| intent | 觸發條件 | sub_intent |
|--------|----------|------------|
| classroom_management | 班級、新增班級、建班、改班名、加班級、class、classroom | add 或 edit |
| student_management | 學生、新增學生、加學生、改學生資料、student | add 或 edit |
| find_feature | 找功能、怎麼…、…在哪、如何…、我要看…、how to、where is | 無 |
| quick_start | 快速開始、新手教學、怎麼開始使用、不知道怎麼用、第一次使用、getting started | 無 |
| delete_request | 刪除班級、刪除學生、移除…、刪掉…、delete、remove | 無 |
| greeting | 你好、嗨、hello、hi、早安、午安、晚安、謝謝、感謝、再見 | 無 |
| off_topic | 與教學管理無關的話題（天氣、笑話、煮泡麵、其他系統功能等） | 無 |
| unclear | 無法判斷意圖 | 無 |

## sub_intent 判斷
- 提到「修改、改、編輯、更新、rename、edit、update、change」→ sub_intent = "edit"
- 提到「新增、加、建立、create、add」或未明確說明 → sub_intent = "add"
- 僅適用於 classroom_management 和 student_management

## 同時解析資料（關鍵能力）

當意圖明確且用戶同時提供了資料時，一步完成解析：

1. **classroom_management + add**：
   解析班級名稱和等級（PREA, A1, A2, B1, B2, C1, C2）
   parsed_data: {"classrooms": [{"name": "三年一班", "level": "A2", "valid": true, "error": null}]}

2. **classroom_management + edit**：
   parsed_data: null（進入編輯流程由 flow 處理）

3. **student_management + add**：
   解析學生姓名和生日（格式 YYYY-MM-DD）
   parsed_data: {"students": [{"name": "小明", "birthdate": "2015-03-21", "valid": true, "error": null}]}

4. **student_management + edit**：
   parsed_data: null（進入編輯流程由 flow 處理）

5. **find_feature**：
   parsed_data: {"query": "用戶的原始問題"}

6. **其他意圖**：parsed_data 為 null

## 各意圖的 message 規則

- **greeting**：溫暖回應，簡述可以幫什麼忙（管理班級、學生、找功能）。不要每次都用一樣的回覆。
- **off_topic**：禮貌拒絕，像真人一樣自然。例如「不好意思，這個我幫不上忙，但如果你需要管理班級或學生，隨時跟我說！」
- **delete_request**：解釋刪除需要到管理頁面手動操作，提供 navigation。
  - 刪除班級 → navigation: [{"label": "前往我的班級", "path": "/teacher/classrooms"}]
  - 刪除學生 → navigation: [{"label": "前往我的班級", "path": "/teacher/classrooms"}]
- **unclear**：友善詢問，例如「不好意思，我不太確定你的意思。你可以告訴我想做什麼嗎？例如新增班級、管理學生，或找某個功能。」
- **其他有明確意圖的**：message 可以為 null（前端會處理）

## 輸出格式（永遠回傳有效 JSON）
{
  "intent": "classroom_management",
  "sub_intent": "add",
  "parsed_data": {"classrooms": [{"name": "三年一班", "level": "A2", "valid": true, "error": null}]},
  "message": null,
  "navigation": null
}
"""

AI_CHAT_SYSTEM_PROMPT = COMMON_RULES + """

## 你的角色
你是 Duotopia 教師後台 AI 助手。你能理解自然語言，根據完整對話歷史和當前工作流程狀態做出判斷。

## 語氣
專業但溫暖，像真人對話。不要像機器人、不要用罐頭回覆。回覆簡潔有力。

## 你知道的領域知識（回答用戶問題時使用）

- **學生生日**：生日是必填欄位，因為生日會作為學生的**預設登入密碼**（YYYYMMDD 格式，例如 20120101）。如果老師不知道學生生日，系統會使用預設值 2012-01-01。學生第一次登入後可以自行修改密碼。
- **班級等級**：PREA, A1, A2, B1, B2, C1, C2，代表語言能力等級。未指定時預設 A1。
- **刪除操作**：刪除班級或學生需要到「我的班級」管理頁面手動操作，AI 助手無法直接刪除。

## 你收到的上下文

1. **conversation_history** — 最近的對話紀錄（用戶看到什麼，你就看到什麼）
2. **flow_state** — 當前是否在工作流程中（如果有）
   - `type`: 工作流程類型（classroom 或 students）
   - `step`: 當前步驟（如 choose_mode, collect_single_name 等）
   - `available_actions`: 畫面上目前可見的按鈕（格式："按鈕文字=按鈕值"）
3. **user_input** — 用戶最新輸入

## 判斷邏輯（按優先順序）

### 情況 A：有 flow_state（正在工作流程中）

1. **用戶選擇可見按鈕** — 用戶的文字像是在選 `available_actions` 中的某個操作
   - 判斷標準：語意相近、縮寫、口語、部分匹配都算
   - 例如：available_actions 有 "批次新增=mode:batch"，用戶說「批次好了」「用批次的」「批次」→ 都是選這個
   - 例如：available_actions 有 "一個一個新增=mode:single"，用戶說「一次一個」「一個一個」→ 都是選這個
   - → action: "select_action", selected_action: "按鈕的值"（= 號後面的部分）

2. **用戶提供當前步驟需要的資料** — 根據 step 判斷用戶是否在提供資料
   - collect_single_name → 用戶輸入的像是名稱
   - collect_single_birthday → 用戶輸入的像是日期
   - collect_single_level → 用戶輸入的像是等級
   - collect_batch → 用戶輸入的像是批次資料
   - collect_edit_value / collect_optional_value / batch_edit_collect → 用戶在修改資料
   - confirm → 用戶在回應確認問題
   - → action: "provide_data"

3. **用戶想切換到不同的工作流程** — 用戶明確表示想做別的事
   - 「算了我想管理班級」「我不要新增學生了，幫我建班」
   - → action: "switch_workflow", workflow_type: "classroom"|"students", sub_intent: "add"|"edit"|null

4. **用戶想找功能** — 「怎麼看出勤紀錄？」「教材在哪裡？」
   - → action: "find_feature"

5. **閒聊 / 打招呼 / 離題 / 不明確** — 保持在當前 flow，用 message 回覆
   - 打招呼：溫暖回應 + 提示繼續當前操作
   - 離題：禮貌拒絕 + 引導回流程
   - 不明確：友善詢問，給出目前步驟可以做什麼
   - → action: "respond", message: "..."

### 情況 B：沒有 flow_state（主畫面）

**最重要的區分**：用戶是要「執行操作」還是「問問題」？這個判斷必須在所有其他判斷之前！

問問題的特徵（→ respond）：
- 有疑問詞：嗎、呢、請問、可以…嗎、是否、怎麼樣、什麼、為什麼
- 句型是在詢問而非命令：「…可以不設嗎？」「…是必填的嗎？」「…怎麼用？」
- 例如：「新增學生可以不設生日嗎？」→ respond（回答問題）
- 例如：「請問班級等級有什麼差別？」→ respond（回答問題）
- 例如：「生日是做什麼用的？」→ respond（回答問題）

執行操作的特徵（→ start_workflow）：
- 祈使句：「幫我新增學生」「我要加班級」「新增三年一班」
- 直接給資料：「小明 2015-03-21」
- 例如：「幫我新增10個學生」→ start_workflow

⚠️ 如果不確定是問問題還是執行操作，優先當作問問題（respond）。

1. **關於功能的問題** — 用戶在問班級/學生相關的使用問題（不是要執行操作）
   - → action: "respond", message: "使用「領域知識」回答問題"
   - 回答後可以問用戶是否要開始操作（如「需要我幫你新增學生嗎？」）

2. **班級管理** — 用戶想管理班級（明確的操作意圖）
   - 提到「新增、加、建」班級 → action: "start_workflow", workflow_type: "classroom", sub_intent: "add"
   - 提到「修改、改、編輯」班級 → action: "start_workflow", workflow_type: "classroom", sub_intent: "edit"
   - 只說「班級」但不明確 → action: "start_workflow", workflow_type: "classroom", sub_intent: null
   - 如果同時提供了班級資料 → parsed_data: {"classrooms": [...]}

3. **學生管理** — 用戶想管理學生（明確的操作意圖）
   - 同理，action: "start_workflow", workflow_type: "students"
   - 如果同時提供了學生資料 → parsed_data: {"students": [...]}

4. **找功能** — 「怎麼…」「…在哪」「如何…」「我要看…」
   - → action: "find_feature"

5. **刪除請求** — 「刪除班級」「移除學生」
   - → action: "respond", message: "解釋刪除需要到管理頁面"
   - 附帶 navigation: [{"label": "前往我的班級", "path": "/teacher/classrooms"}]

6. **打招呼** — 溫暖回應，簡述可以幫什麼忙
   - → action: "respond", message: "...", respond_type: "greeting"

7. **離題 / 不明確** — 禮貌拒絕或友善詢問
   - → action: "respond", message: "..."

## 解析班級資料規則（同時提供時）
- 等級有效值：PREA, A1, A2, B1, B2, C1, C2
- 未指定等級 → 預設 A1
- parsed_data: {"classrooms": [{"name": "三年一班", "level": "A2", "valid": true, "error": null}]}

## 解析學生資料規則（同時提供時）
- 日期統一 YYYY-MM-DD
- parsed_data: {"students": [{"name": "小明", "birthdate": "2015-03-21", "valid": true, "error": null}]}

## 輸出格式（永遠回傳有效 JSON）
{
  "action": "select_action",
  "message": null,
  "selected_action": "mode:batch",
  "workflow_type": null,
  "sub_intent": null,
  "parsed_data": null,
  "navigation": null,
  "respond_type": null
}

重要：
- action 為必填，其他欄位根據 action 類型填寫
- message 為 null 時前端不會顯示額外訊息
- selected_action 只在 action="select_action" 時填寫
- workflow_type 只在 action="start_workflow" 或 "switch_workflow" 時填寫
- navigation 只在需要導引頁面時填寫
- respond_type 只在 action="respond" 時填寫：
  - "greeting" — 打招呼（你好、嗨、謝謝等）
  - "off_topic" — 離題（與教學管理無關）
  - "unclear" — 不明確（無法判斷意圖）

## 資料收集步驟的偏好規則

在以下步驟中：collect_batch、collect_single_name、collect_single_birthday、collect_single_level、collect_optional_value、confirm、batch_edit_collect、collect_edit_value

除非用戶**明確**要切換流程（如「我不要了，幫我管理班級」）、問功能（如「教材在哪」）、或打招呼，否則一律視為 provide_data。

疑惑時選 provide_data。寧可解析錯再友善引導，也不要輕易判定為 respond/unclear。
"""

# ---- Dynamic parse-rule fragments (injected into AI_CHAT_SYSTEM_PROMPT based on step) ----

_CHAT_PARSE_STUDENTS_RULES = """
## 學生資料解析規則（此步驟額外能力）

當你判斷 action=provide_data 時，你必須**同時**在 parsed_data 中回傳解析結果。

### 解析能力
1. **理解自然語言** —
   - 「小明 2015/3/21, 小華 2014-08-15」→ 兩筆學生資料
   - 「座號1到5號，名字分別是小明、小華、小美、小強、小玲」→ 五筆
   - 「姓名跟學號相同 學號從01開始到10結束」→ 十筆（學生01, 學生02, ..., 學生10）
   - 「再加小明 生日 3月21號 2015年」→ 理解非標準日期格式
2. **日期格式容錯** — YYYY-MM-DD, YYYY/MM/DD, 口語等，統一輸出 YYYY-MM-DD
3. **不知道生日** — 用戶說「不知道」「不確定」「沒有生日資料」「能不設置嗎」→ 使用預設值 2012-01-01
   - 回覆時要解釋：「生日會作為學生的預設登入密碼（YYYYMMDD 格式），所以需要設一個值。我先幫您用預設值 2012-01-01，學生登入後可以自行修改。」
4. **容錯** — 常見打字錯誤、同音字等

### 驗證規則
- 姓名為空 → valid=false, error="缺少姓名"
- 姓名超過 50 字元 → valid=false, error="姓名過長"
- 缺少生日且用戶未說不知道 → valid=false, error="缺少生日"
- 姓名含髒話或不雅詞彙 → valid=false, error="姓名包含不適當用語，請修改"

### parsed_data 格式
action=provide_data 時：
parsed_data: {"students": [{"name": "學生01", "birthdate": "2012-01-01", "valid": true, "error": null}]}
message: 簡短確認（如「收到，我幫你解析了 10 位學生」）或 null
"""

_CHAT_PARSE_CLASSROOMS_RULES = """
## 班級資料解析規則（此步驟額外能力）

當你判斷 action=provide_data 時，你必須**同時**在 parsed_data 中回傳解析結果。

### 解析能力
1. **理解自然語言序列** —
   - 「114-2 110 A2, 114-2 109 B1, 以此類推到 101 都是 B1」→ 展開序列
   - 「A班到E班 都是 A1」→ A班(A1), B班(A1), C班(A1), D班(A1), E班(A1)
   - 「一年級到三年級」→ 一年級, 二年級, 三年級
2. **推斷等級** — 部分班級有等級、其餘未指定 → 使用上下文中最近的等級
3. **容錯** — 「班及」→「班級」、「bl」→「B1」

### 語言等級
有效值：PREA, A1, A2, B1, B2, C1, C2（不區分大小寫）
- 無法辨識 → valid=false, error="等級不正確"
- 未指定 → 預設 A1

### 驗證規則
- 名稱為空 → valid=false, error="缺少名稱"
- 名稱超過 100 字元 → valid=false, error="名稱過長"
- 名稱含髒話或不雅詞彙 → valid=false, error="班級名稱包含不適當用語，請修改"

### parsed_data 格式
action=provide_data 時：
parsed_data: {"classrooms": [{"name": "三年一班", "level": "A1", "valid": true, "error": null}]}
message: 簡短確認或 null
"""

_CHAT_MODIFY_STUDENTS_RULES = """
## 學生名單修改規則（此步驟額外能力）

用戶正在確認一份學生名單，可能想修改。你同時負責理解修改指令並執行。

user prompt 中會附帶「目前的學生名單」。

### 原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字。名單只有一筆時不需指定姓名
2. **不確定就問** — action="provide_data", parsed_data 含 modification_action="unclear"，回傳原始列表不變
3. **離題就引導回來**

### 如果用戶是確認名單（「沒問題」「好」「確認」等）
→ action="select_action", selected_action="confirm"

### 如果用戶要修改
→ action="provide_data"
parsed_data: {
  "students": [...完整修改後的列表...],
  "modification_action": "modify|add|remove|unclear"
}
message: 描述做了什麼修改

### 日期格式
接受多種格式，統一輸出 YYYY-MM-DD
不知道生日 → 2012-01-01
"""

_CHAT_MODIFY_CLASSROOMS_RULES = """
## 班級名單修改規則（此步驟額外能力）

用戶正在確認一份班級名單，可能想修改。你同時負責理解修改指令並執行。

user prompt 中會附帶「目前的班級名單」。

### 原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字。名單只有一筆時不需指定名稱
2. **不確定就問** — action="provide_data", parsed_data 含 modification_action="unclear"，回傳原始列表不變
3. **離題就引導回來**

### 語言等級
有效值：PREA, A1, A2, B1, B2, C1, C2

### 如果用戶是確認名單
→ action="select_action", selected_action="confirm"

### 如果用戶要修改
→ action="provide_data"
parsed_data: {
  "classrooms": [...完整修改後的列表...],
  "modification_action": "modify|add|remove|unclear"
}
message: 描述做了什麼修改
"""

_CHAT_BATCH_EDIT_STUDENTS_RULES = """
## 批次修改現有學生規則（此步驟額外能力）

用戶正在修改一個班級中現有學生的資料。每位學生有 id、name、birthdate、email、student_number、phone。

user prompt 中會附帶「目前的學生名單（含 id）」。

### 規則
- 每位學生的 id 必須保留不變
- 只修改用戶指定的欄位，其他保持不變
- 可以一次修改多位學生（如「把所有名字帶有座號的去掉座號」）
- 日期格式統一 YYYY-MM-DD
- 不能新增或刪除學生

### 如果理解用戶指令
→ action="provide_data"
parsed_data: {
  "students": [{"id": 1, "name": "修改後", "birthdate": "...", "email": "...", "student_number": "...", "phone": "..."}],
  "modification_action": "modify"
}

### 不確定
→ action="provide_data", parsed_data 含 modification_action="unclear"，回傳原始列表不變
"""

# Step → parse-rule fragment mapping
_STEP_PARSE_RULES: dict[tuple[str, str], str] = {
    ("students", "collect_batch"): _CHAT_PARSE_STUDENTS_RULES,
    ("students", "confirm"): _CHAT_MODIFY_STUDENTS_RULES,
    ("students", "batch_edit_collect"): _CHAT_BATCH_EDIT_STUDENTS_RULES,
    ("classroom", "collect_batch"): _CHAT_PARSE_CLASSROOMS_RULES,
    ("classroom", "confirm"): _CHAT_MODIFY_CLASSROOMS_RULES,
}


def _build_chat_system_prompt(flow_state: Optional[ChatFlowState] = None) -> str:
    """Dynamically compose the chat system prompt based on current flow step.

    Base prompt handles routing. When the user is in a data-collection step,
    we inject step-specific parsing rules so the SAME AI call handles both
    routing AND data parsing — the 'unified AI brain'.
    """
    base = AI_CHAT_SYSTEM_PROMPT
    if not flow_state:
        return base
    key = (flow_state.type, flow_state.step)
    fragment = _STEP_PARSE_RULES.get(key, "")
    if fragment:
        return base + "\n\n" + fragment
    return base


# ---- Deterministic fallback for detect-intent ----

_GREETING_RE = re.compile(
    r"^(你好|嗨|hi|hello|hey|早安|午安|晚安|謝謝|感謝|再見|bye|掰掰|哈囉|嘿)",
    re.IGNORECASE,
)
_CLASSROOM_RE = re.compile(r"(班級|班|classroom|class(?!room))", re.IGNORECASE)
_STUDENT_RE = re.compile(r"(學生|student)", re.IGNORECASE)
_DELETE_RE = re.compile(r"(刪除|移除|刪掉|去掉|delete|remove)", re.IGNORECASE)
_EDIT_RE = re.compile(r"(修改|改|編輯|更新|rename|edit|update|change)", re.IGNORECASE)
_FIND_RE = re.compile(r"(找功能|怎麼|在哪|如何|how|where|功能|我要看|想看)", re.IGNORECASE)
_QUICKSTART_RE = re.compile(r"(快速開始|新手|getting started|開始使用|第一次|不知道怎麼用)", re.IGNORECASE)


def _fallback_detect_intent(user_input: str) -> DetectIntentResponse:
    """Regex-based intent classification when Gemini fails."""
    text = user_input.strip()

    if not text:
        return DetectIntentResponse(
            intent="unclear",
            message="請問有什麼需要幫忙的嗎？我可以幫你管理班級、學生，或找到你需要的功能。",
        )

    # Greeting
    if _GREETING_RE.match(text):
        return DetectIntentResponse(
            intent="greeting",
            message="你好！我可以幫你管理班級、學生資料，或找到你需要的功能。有什麼需要幫忙的嗎？",
        )

    # Delete
    if _DELETE_RE.search(text):
        nav = [NavigationItem(label="前往我的班級", path="/teacher/classrooms")]
        return DetectIntentResponse(
            intent="delete_request",
            message="刪除操作需要到管理頁面手動進行喔。",
            navigation=nav,
        )

    # Classroom
    if _CLASSROOM_RE.search(text):
        sub = "edit" if _EDIT_RE.search(text) else "add"
        return DetectIntentResponse(intent="classroom_management", sub_intent=sub)

    # Student
    if _STUDENT_RE.search(text):
        sub = "edit" if _EDIT_RE.search(text) else "add"
        return DetectIntentResponse(intent="student_management", sub_intent=sub)

    # Quick start
    if _QUICKSTART_RE.search(text):
        return DetectIntentResponse(intent="quick_start")

    # Find feature / how-to
    if _FIND_RE.search(text):
        return DetectIntentResponse(
            intent="find_feature",
            parsed_data={"query": user_input},
        )

    return DetectIntentResponse(
        intent="unclear",
        message="不好意思，我不太確定你的意思。你可以告訴我想做什麼嗎？例如：新增班級、管理學生、或找某個功能。",
    )


# ============ Endpoints ============


@router.post("/parse-teachers", response_model=ParseTeachersResponse)
async def parse_teachers(request: ParseTeachersRequest):
    """
    Parse free-text teacher input using Gemini.
    Extracts name, email, and role from natural language.
    """
    try:
        prompt = f"請解析以下用戶輸入的教師資料：\n\n{request.user_input}"

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PARSE_TEACHERS_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2000,
        )

        # Ensure expected structure
        teachers = result.get("teachers", [])
        message = result.get("message", "解析完成。")

        # Normalize each teacher record + deterministic domain typo check
        parsed = []
        for t in teachers:
            email = t.get("email", "")
            valid = t.get("valid", True)
            error = t.get("error")

            # Deterministic check: override AI result if domain typo detected
            if valid and email:
                typo_warning = check_email_domain_typo(email)
                if typo_warning:
                    valid = False
                    error = typo_warning

            parsed.append(
                ParsedTeacher(
                    name=t.get("name", ""),
                    email=email,
                    role=t.get("role", "teacher"),
                    valid=valid,
                    error=error,
                )
            )

        return ParseTeachersResponse(teachers=parsed, message=message)

    except Exception as e:
        logger.warning(f"Gemini parse failed, using fallback: {e}")
        # Fallback: use deterministic parser instead of returning 500
        result = fallback_parse_teachers(request.user_input)
        teachers = result.get("teachers", [])
        message = result.get("message", "解析完成。")

        parsed = []
        for t in teachers:
            parsed.append(
                ParsedTeacher(
                    name=t.get("name", ""),
                    email=t.get("email", ""),
                    role=t.get("role", "teacher"),
                    valid=t.get("valid", True),
                    error=t.get("error"),
                )
            )

        return ParseTeachersResponse(teachers=parsed, message=message)


@router.post("/process-modification", response_model=ProcessModificationResponse)
async def process_modification(request: ProcessModificationRequest):
    """
    Process a modification instruction on the current teacher list using Gemini.
    Understands natural language commands to add, remove, or modify teachers.
    """
    try:
        # Build context with current list
        current_list = "\n".join(
            f"- {t.name} | {t.email} | {t.role}"
            for t in request.current_teachers
        )

        prompt = (
            f"目前的教師名單：\n{current_list}\n\n"
            f"用戶的修改指令：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PROCESS_MODIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=2000,
        )

        teachers = result.get("teachers", [])
        message = result.get("message", "修改完成。")
        action = result.get("action", "unclear")

        parsed = []
        for t in teachers:
            email = t.get("email", "")
            valid = t.get("valid", True)
            error = t.get("error")

            if valid and email:
                typo_warning = check_email_domain_typo(email)
                if typo_warning:
                    valid = False
                    error = typo_warning

            parsed.append(
                ParsedTeacher(
                    name=t.get("name", ""),
                    email=email,
                    role=t.get("role", "teacher"),
                    valid=valid,
                    error=error,
                )
            )

        return ProcessModificationResponse(
            teachers=parsed, message=message, action=action
        )

    except Exception as e:
        logger.error(f"Failed to process modification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 處理失敗：{str(e)}",
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI-first chat endpoint. All text input goes through this endpoint.
    AI receives full conversation history + current workflow state + available actions,
    and decides the appropriate action.
    """
    try:
        # Build conversation context for the prompt
        history_text = ""
        if request.conversation_history:
            recent = request.conversation_history[-20:]  # Last 20 messages
            lines = []
            for msg in recent:
                role_label = "用戶" if msg.role == "user" else "助手"
                lines.append(f"{role_label}：{msg.content}")
            history_text = "\n".join(lines)

        # Build flow state context
        flow_text = ""
        if request.flow_state:
            flow_text = (
                f"\n## 當前工作流程\n"
                f"- 類型：{request.flow_state.type}\n"
                f"- 步驟：{request.flow_state.step}\n"
            )
            if request.flow_state.available_actions:
                actions_str = "\n".join(
                    f"  - {a}" for a in request.flow_state.available_actions
                )
                flow_text += f"- 目前畫面上的按鈕：\n{actions_str}\n"
            else:
                flow_text += "- 目前沒有按鈕（等待用戶輸入資料）\n"

        # Build environment context
        workspace_hint = ""
        if request.workspace_mode == "personal":
            workspace_hint = "用戶目前在教師個人模式。"
        elif request.workspace_mode == "organization":
            workspace_hint = "用戶目前在教師組織模式。"

        path_hint = (
            f"用戶當前頁面：{request.current_path}\n"
            if request.current_path
            else ""
        )

        prompt = (
            f"用戶環境：教師後台\n"
            f"{workspace_hint}\n"
            f"{path_hint}"
        )

        if history_text:
            prompt += f"\n## 對話歷史\n{history_text}\n"

        if flow_text:
            prompt += flow_text

        # Inject current_data for modification steps (confirm, batch_edit_collect)
        if request.flow_state and request.flow_state.current_data:
            data = request.flow_state.current_data
            if data.get("students"):
                students_list = data["students"]
                # Check if students have IDs (batch_edit mode)
                if students_list and isinstance(students_list[0], dict) and students_list[0].get("id"):
                    lines_data = []
                    for s in students_list:
                        lines_data.append(
                            f"- id:{s['id']} | 姓名:{s.get('name', '')} | "
                            f"生日:{s.get('birthdate', '(空)')} | "
                            f"Email:{s.get('email', '(空)')} | "
                            f"學號:{s.get('student_number', '(空)')} | "
                            f"電話:{s.get('phone', '(空)')}"
                        )
                    prompt += f"\n## 目前的學生名單（共 {len(students_list)} 位）\n" + "\n".join(lines_data) + "\n"
                else:
                    lines_data = [
                        f"- {s.get('name', '')} | {s.get('birthdate', '(空)')}"
                        for s in students_list
                    ]
                    prompt += f"\n## 目前的學生名單\n" + "\n".join(lines_data) + "\n"
            elif data.get("classrooms"):
                classrooms_list = data["classrooms"]
                lines_data = [
                    f"- {c.get('name', '')} | {c.get('level', 'A1')}"
                    for c in classrooms_list
                ]
                prompt += f"\n## 目前的班級名單\n" + "\n".join(lines_data) + "\n"

        prompt += f"\n## 用戶最新輸入\n{request.user_input}"

        # Dynamic system prompt: base + step-specific parse rules
        system_prompt = _build_chat_system_prompt(request.flow_state)

        # Use more tokens when parsing data
        is_parse_step = (
            request.flow_state
            and (request.flow_state.type, request.flow_state.step) in _STEP_PARSE_RULES
        )
        max_tokens = 4000 if is_parse_step else 1500

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=system_prompt,
            temperature=0.2,
            max_tokens=max_tokens,
        )

        action = result.get("action", "respond")
        message = result.get("message")
        selected_action = result.get("selected_action")
        workflow_type = result.get("workflow_type")
        sub_intent = result.get("sub_intent")
        parsed_data = result.get("parsed_data")
        nav_items = result.get("navigation")
        respond_type = result.get("respond_type")

        # Validate parsed classroom data if present
        if parsed_data and parsed_data.get("classrooms"):
            validated = _validate_classrooms(parsed_data["classrooms"])
            parsed_data["classrooms"] = [
                {"name": c.name, "level": c.level, "valid": c.valid, "error": c.error}
                for c in validated
            ]

        # Validate parsed student data if present (without IDs — new students)
        if parsed_data and parsed_data.get("students"):
            students_raw = parsed_data["students"]
            # Only validate with _validate_students for new students (no id field)
            if students_raw and isinstance(students_raw[0], dict) and not students_raw[0].get("id"):
                validated_s = _validate_students(students_raw)
                parsed_data["students"] = [
                    {"name": s.name, "birthdate": s.birthdate, "valid": s.valid, "error": s.error}
                    for s in validated_s
                ]
            elif students_raw and isinstance(students_raw[0], dict) and students_raw[0].get("id"):
                # Batch edit students — validate with _validate_batch_edit_students
                if request.flow_state and request.flow_state.current_data:
                    original_ids = {
                        s.get("id") for s in (request.flow_state.current_data.get("students") or [])
                        if isinstance(s, dict) and s.get("id")
                    }
                    parsed_data["students"] = _validate_batch_edit_students(students_raw, original_ids)

        # Build navigation items if present
        navigation = None
        if nav_items and isinstance(nav_items, list):
            navigation = []
            for item in nav_items:
                if isinstance(item, dict) and item.get("label") and item.get("path"):
                    navigation.append(NavigationItem(label=item["label"], path=item["path"]))

        return ChatResponse(
            action=action,
            message=message,
            selected_action=selected_action,
            workflow_type=workflow_type,
            sub_intent=sub_intent,
            parsed_data=parsed_data,
            navigation=navigation,
            respond_type=respond_type,
        )

    except Exception as e:
        logger.warning(f"Chat Gemini failed, using fallback: {e}")
        # Fallback: use detect-intent logic
        fallback = _fallback_detect_intent(request.user_input)
        # Map detect-intent response to chat response
        action = "respond"
        workflow_type = None
        sub_intent = fallback.sub_intent
        respond_type = None
        if fallback.intent in ("classroom_management", "student_management"):
            action = "start_workflow"
            workflow_type = "classroom" if fallback.intent == "classroom_management" else "students"
        elif fallback.intent == "find_feature":
            action = "find_feature"
        elif fallback.intent == "greeting":
            respond_type = "greeting"
        elif fallback.intent == "off_topic":
            respond_type = "off_topic"
        elif fallback.intent == "unclear":
            respond_type = "unclear"
        return ChatResponse(
            action=action,
            message=fallback.message,
            workflow_type=workflow_type,
            sub_intent=sub_intent,
            parsed_data=fallback.parsed_data,
            navigation=fallback.navigation,
            respond_type=respond_type,
        )


@router.post("/find-feature", response_model=FindFeatureResponse)
async def find_feature(request: FindFeatureRequest):
    """
    Help users find the right page/feature using Gemini.
    Returns a message with navigation suggestions.
    """
    try:
        context_label = "機構後台" if request.context == "organization" else "教師後台"
        has_org_admin = any(r in (request.user_roles or []) for r in ["org_owner", "org_admin"])
        role_hint = (
            "用戶擁有機構管理權限（可進入機構後台）。"
            if has_org_admin
            else "用戶沒有機構管理權限（無法進入機構後台）。"
        ) if request.user_roles else ""

        path_hint = (
            f"用戶當前頁面路徑：{request.current_path}。如果推薦的頁面就是用戶當前所在頁面，不要提供 navigation 連結，改為直接說明在該頁面上如何操作。\n"
            if request.current_path
            else ""
        )

        # Workspace mode hint (teacher backend only)
        workspace_hint = ""
        if request.context == "teacher" and request.workspace_mode:
            if request.workspace_mode == "organization" and request.workspace_org:
                school_part = f" - {request.workspace_school}" if request.workspace_school else ""
                workspace_hint = (
                    f"用戶的教師後台目前在「組織模式」（{request.workspace_org}{school_part}），頁面顯示的是該分校/組織的資料。"
                    f"如果用戶想看自己個人的資料，需要切換到「個人模式」（在左側側欄的工作區切換器中操作）。\n"
                )
            elif request.workspace_mode == "personal":
                workspace_hint = (
                    "用戶的教師後台目前在「個人模式」，頁面顯示的是教師自己建立的資料。"
                    "如果用戶想看組織/分校的資料，需要切換到「組織模式」（在左側側欄的工作區切換器中選擇組織和分校）。\n"
                )

        prompt = (
            f"用戶目前在「{context_label}」。\n"
            + (f"{role_hint}\n" if role_hint else "")
            + workspace_hint
            + path_hint
            + f"用戶想找的功能：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=FIND_FEATURE_SYSTEM_PROMPT,
            temperature=0.2,
            max_tokens=1000,
        )

        message = result.get("message", "")
        nav_items = result.get("navigation", [])

        navigation = []
        for item in nav_items:
            if isinstance(item, dict) and item.get("label") and item.get("path"):
                navigation.append(
                    NavigationItem(label=item["label"], path=item["path"])
                )

        return FindFeatureResponse(message=message, navigation=navigation)

    except Exception as e:
        logger.error(f"Failed to find feature: {e}", exc_info=True)
        return FindFeatureResponse(
            message="抱歉，目前無法處理您的問題。請試著用不同的方式描述您想找的功能。",
            navigation=[],
        )


@router.post("/detect-intent", response_model=DetectIntentResponse)
async def detect_intent(request: DetectIntentRequest):
    """
    Detect user intent from free-text input and optionally parse data.
    Used by the HubChat component to route users to the correct flow.
    """
    try:
        workspace_hint = ""
        if request.workspace_mode == "personal":
            workspace_hint = "用戶目前在教師個人模式。"
        elif request.workspace_mode == "organization":
            workspace_hint = "用戶目前在教師組織模式。"

        path_hint = (
            f"用戶當前頁面：{request.current_path}\n"
            if request.current_path
            else ""
        )

        prompt = (
            f"用戶環境：教師後台\n"
            f"{workspace_hint}\n"
            f"{path_hint}"
            f"用戶輸入：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=DETECT_INTENT_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=1500,
        )

        intent = result.get("intent", "unclear")
        sub_intent = result.get("sub_intent")
        parsed_data = result.get("parsed_data")
        message = result.get("message")
        nav_items = result.get("navigation")

        # Validate parsed classroom data if present
        if intent == "classroom_management" and parsed_data and parsed_data.get("classrooms"):
            validated = _validate_classrooms(parsed_data["classrooms"])
            parsed_data["classrooms"] = [
                {"name": c.name, "level": c.level, "valid": c.valid, "error": c.error}
                for c in validated
            ]

        # Validate parsed student data if present
        if intent == "student_management" and parsed_data and parsed_data.get("students"):
            validated = _validate_students(parsed_data["students"])
            parsed_data["students"] = [
                {"name": s.name, "birthdate": s.birthdate, "valid": s.valid, "error": s.error}
                for s in validated
            ]

        # Build navigation items if present
        navigation = None
        if nav_items and isinstance(nav_items, list):
            navigation = []
            for item in nav_items:
                if isinstance(item, dict) and item.get("label") and item.get("path"):
                    navigation.append(NavigationItem(label=item["label"], path=item["path"]))

        return DetectIntentResponse(
            intent=intent,
            sub_intent=sub_intent,
            parsed_data=parsed_data,
            message=message,
            navigation=navigation,
        )

    except Exception as e:
        logger.warning(f"detect-intent Gemini failed, using fallback: {e}")
        return _fallback_detect_intent(request.user_input)


# ---- Classroom parsing ----

VALID_LEVELS = {"PREA", "A1", "A2", "B1", "B2", "C1", "C2"}


def _normalize_level(level: str) -> str | None:
    """Normalize a level string. Returns None if invalid."""
    upper = level.strip().upper().replace("-", "").replace(" ", "")
    if upper in VALID_LEVELS:
        return upper
    return None


def _validate_classrooms(classrooms: list[dict]) -> list[ParsedClassroom]:
    """Deterministic validation on top of AI result."""
    result = []
    for c in classrooms:
        name = c.get("name", "").strip()
        level = c.get("level", "A1").strip()
        valid = c.get("valid", True)
        error = c.get("error")

        # Name check
        if not name:
            valid = False
            error = "缺少名稱"
        elif len(name) > 100:
            valid = False
            error = "名稱過長"

        # Level normalization
        normalized = _normalize_level(level)
        if normalized:
            level = normalized
        else:
            valid = False
            error = f"等級「{level}」不正確，有效等級：PREA, A1, A2, B1, B2, C1, C2"

        result.append(ParsedClassroom(
            name=name,
            level=level if normalized else level.upper(),
            valid=valid,
            error=error,
        ))
    return result


@router.post("/parse-classrooms", response_model=ParseClassroomsResponse)
async def parse_classrooms(request: ParseClassroomsRequest):
    """
    Parse free-text classroom input using Gemini.
    Understands natural language like sequences and ranges.
    """
    try:
        prompt = f"請解析以下用戶輸入的班級資料：\n\n{request.user_input}"

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PARSE_CLASSROOMS_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=4000,
        )

        classrooms = result.get("classrooms", [])
        message = result.get("message", "解析完成。")

        parsed = _validate_classrooms(classrooms)

        return ParseClassroomsResponse(classrooms=parsed, message=message)

    except Exception as e:
        logger.warning(f"Gemini parse-classrooms failed, using fallback: {e}")
        # Fallback: simple line-based parsing
        lines = [l.strip() for l in request.user_input.strip().split("\n") if l.strip()]
        fallback = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                last = parts[-1].upper().replace("-", "").replace(" ", "")
                if last in VALID_LEVELS:
                    fallback.append({"name": " ".join(parts[:-1]), "level": last})
                else:
                    fallback.append({"name": line, "level": "A1"})
            elif len(parts) == 1:
                fallback.append({"name": parts[0], "level": "A1"})

        parsed = _validate_classrooms(fallback)
        return ParseClassroomsResponse(
            classrooms=parsed,
            message="解析完成。" if parsed else "無法解析班級資料，請提供班級名稱和等級。",
        )


@router.post("/process-classroom-modification", response_model=ProcessClassroomModificationResponse)
async def process_classroom_modification(request: ProcessClassroomModificationRequest):
    """
    Process a modification instruction on the current classroom list using Gemini.
    """
    try:
        current_list = "\n".join(
            f"- {c.name} | {c.level}"
            for c in request.current_classrooms
        )

        prompt = (
            f"目前的班級名單：\n{current_list}\n\n"
            f"用戶的修改指令：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PROCESS_CLASSROOM_MODIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=4000,
        )

        classrooms = result.get("classrooms", [])
        message = result.get("message", "修改完成。")
        action = result.get("action", "unclear")

        parsed = _validate_classrooms(classrooms)

        return ProcessClassroomModificationResponse(
            classrooms=parsed, message=message, action=action
        )

    except Exception as e:
        logger.error(f"Failed to process classroom modification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 處理失敗：{str(e)}",
        )


# ---- Student parsing ----

import re as _re

_BIRTHDATE_RE = _re.compile(r"^\d{4}-\d{2}-\d{2}$")


PARSE_STUDENTS_SYSTEM_PROMPT = """
## 你的角色
你是「新增班級學生」流程中的資料解析助手。用戶正在新增學生到班級中。

## 你的任務
從用戶的自由文字中提取學生資料（姓名、生日）。

## 關鍵能力
1. **理解自然語言** — 例如：
   - 「小明 2015/3/21, 小華 2014-08-15」→ 兩筆學生資料
   - 「座號1到5號，名字分別是小明、小華、小美、小強、小玲，生日都是 2015-01-01」→ 五筆
   - 「再加小明 生日 3月21號 2015年」→ 理解非標準日期格式
2. **日期格式容錯** — 接受多種格式：
   - YYYY-MM-DD, YYYY/MM/DD, YYYYMMDD
   - MM/DD/YYYY, DD/MM/YYYY（根據上下文推斷）
   - 口語：「2015年3月21日」「3月21號 2015年」
   - 所有日期統一輸出為 YYYY-MM-DD
3. **容錯** — 常見打字錯誤、同音字等
4. **不知道生日** — 當用戶表示不知道學生生日時（如「不知道」「不確定」「沒有生日資料」），使用預設值 2012-01-01

## 驗證規則
- 姓名為空 → valid=false, error="缺少姓名"
- 姓名超過 50 字元 → valid=false, error="姓名過長"
- 缺少生日 → valid=false, error="缺少生日"
- 生日格式無法辨識 → valid=false, error="生日格式不正確"
- 姓名含有中文或英文髒話、不雅詞彙、侮辱性用語 → valid=false, error="姓名包含不適當用語，請修改"
  - 常見髒話包括但不限於：幹、靠、他媽、操、fuck、shit、damn、ass、bitch 等
  - 偽裝寫法也要偵測（如用符號替代、拼音、諧音）

## 輸出格式（永遠回傳有效 JSON）
{
  "students": [
    {"name": "學生姓名", "birthdate": "2015-03-21", "valid": true, "error": null}
  ],
  "message": "中文訊息"
}

完全無法解析時回 students=[]，用 message 友善引導。
例如用戶打招呼或問不相關問題時，回 students=[]，message 引導回「請提供學生姓名和生日」。
"""

PROCESS_STUDENT_MODIFICATION_SYSTEM_PROMPT = """
## 你的角色
你是「新增班級學生」流程中的資料修改助手。用戶正在修改一份學生名單。

## 你的任務
理解用戶的口語修改指令，回傳修改後的完整列表。

## 三個原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字，從上下文推斷。名單只有一筆時不需指定姓名
2. **不確定就問** — 用 message 禮貌詢問，action 設 "unclear"，回傳原始列表不變
3. **離題就引導回來** — 友善回應後引導回修改操作

## 日期格式
- 接受多種格式，統一輸出 YYYY-MM-DD

## 驗證規則
- 姓名含有中文或英文髒話、不雅詞彙 → valid=false, error="姓名包含不適當用語，請修改"

## 輸出格式（永遠回傳有效 JSON）
{
  "students": [...完整修改後的列表...],
  "message": "中文訊息",
  "action": "modify|add|remove|unclear"
}
"""


def _validate_students(students: list[dict]) -> list[ParsedStudent]:
    """Deterministic validation on top of AI result."""
    result = []
    for s in students:
        name = s.get("name", "").strip()
        birthdate = s.get("birthdate", "").strip()
        valid = s.get("valid", True)
        error = s.get("error")

        # Name check
        if not name:
            valid = False
            error = "缺少姓名"
        elif len(name) > 50:
            valid = False
            error = "姓名過長"

        # Birthdate check
        if valid and not birthdate:
            valid = False
            error = "缺少生日"
        elif valid and not _BIRTHDATE_RE.match(birthdate):
            valid = False
            error = "生日格式不正確，請使用 YYYY-MM-DD"

        result.append(ParsedStudent(
            name=name,
            birthdate=birthdate,
            valid=valid,
            error=error,
        ))
    return result


@router.post("/parse-students", response_model=ParseStudentsResponse)
async def parse_students(request: ParseStudentsRequest):
    """
    Parse free-text student input using Gemini.
    Understands natural language dates and sequences.
    """
    try:
        prompt = f"請解析以下用戶輸入的學生資料：\n\n{request.user_input}"

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PARSE_STUDENTS_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=4000,
        )

        students = result.get("students", [])
        message = result.get("message", "解析完成。")

        parsed = _validate_students(students)

        return ParseStudentsResponse(students=parsed, message=message)

    except Exception as e:
        logger.warning(f"Gemini parse-students failed, using fallback: {e}")
        # Fallback: simple line-based parsing
        lines = [l.strip() for l in request.user_input.strip().split("\n") if l.strip()]
        fallback = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                birthdate = parts[1] if len(parts) > 1 else ""
                fallback.append({"name": name, "birthdate": birthdate})
            elif len(parts) == 1:
                fallback.append({"name": parts[0], "birthdate": ""})

        parsed = _validate_students(fallback)
        return ParseStudentsResponse(
            students=parsed,
            message="解析完成。" if parsed else "無法解析學生資料，請提供學生姓名和生日。",
        )


@router.post("/process-student-modification", response_model=ProcessStudentModificationResponse)
async def process_student_modification(request: ProcessStudentModificationRequest):
    """
    Process a modification instruction on the current student list using Gemini.
    """
    try:
        current_list = "\n".join(
            f"- {s.name} | {s.birthdate}"
            for s in request.current_students
        )

        prompt = (
            f"目前的學生名單：\n{current_list}\n\n"
            f"用戶的修改指令：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=PROCESS_STUDENT_MODIFICATION_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=4000,
        )

        students = result.get("students", [])
        message = result.get("message", "修改完成。")
        action = result.get("action", "unclear")

        parsed = _validate_students(students)

        return ProcessStudentModificationResponse(
            students=parsed, message=message, action=action
        )

    except Exception as e:
        logger.error(f"Failed to process student modification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 處理失敗：{str(e)}",
        )


BATCH_STUDENT_EDIT_SYSTEM_PROMPT = """
## 你的角色
你是「管理學生資料」流程中的批次修改助手。用戶正在修改一個班級中的學生資料。

## 你的任務
理解用戶的口語修改指令，對現有學生列表進行修改，回傳修改後的完整列表。

## 三個原則
1. **盡力推斷意圖** — 用戶可能簡短、口語、有錯字，從上下文推斷
2. **不確定就問** — 用 message 禮貌詢問，action 設 "unclear"，回傳原始列表不變
3. **離題就引導回來** — 友善回應後引導回修改操作

## 輸入格式
你會收到一份學生列表，每位學生包含：id、name、birthdate、email、student_number、phone。
以及用戶的修改指令。

## 規則
- 每位學生的 id 必須保留不變
- 只修改用戶指定的欄位，其他欄位保持不變
- 可以一次修改多位學生（例如「把所有名字帶有座號的去掉座號」）
- 可以一次修改多個欄位（例如「把小明的名字改成小華，生日改成 2015-03-21」）
- 日期格式統一輸出 YYYY-MM-DD
- 不能新增或刪除學生，只能修改現有學生的欄位

## 驗證規則
- 姓名含有中文或英文髒話、不雅詞彙 → 不要修改，在 message 中提醒用戶
- 姓名為空或超過 50 字元 → 不要修改，在 message 中提醒用戶

## 輸出格式（永遠回傳有效 JSON）
{
  "students": [
    {"id": 1, "name": "修改後姓名", "birthdate": "2015-03-21", "email": "xxx@example.com", "student_number": "S001", "phone": "0912345678"}
  ],
  "message": "中文訊息",
  "action": "modify|unclear"
}
- action="modify": 有實際修改
- action="unclear": 不確定用戶意圖，回傳原始列表不變
"""


def _validate_batch_edit_students(students: list[dict], original_ids: set[int]) -> list[dict]:
    """Validate batch edit results: ensure IDs are preserved and fields are sane."""
    result = []
    for s in students:
        sid = s.get("id")
        if sid not in original_ids:
            continue  # skip students not in original list
        name = str(s.get("name", "")).strip()
        if not name or len(name) > 50:
            continue  # skip invalid names
        result.append({
            "id": sid,
            "name": name,
            "birthdate": str(s.get("birthdate", "")).strip(),
            "email": str(s.get("email", "")).strip(),
            "student_number": str(s.get("student_number", "")).strip(),
            "phone": str(s.get("phone", "")).strip(),
        })
    return result


@router.post("/process-batch-student-edit", response_model=BatchStudentEditResponse)
async def process_batch_student_edit(request: BatchStudentEditRequest):
    """
    Process a batch edit instruction on existing students using Gemini.
    """
    try:
        original_ids = {s.id for s in request.current_students}

        current_list = "\n".join(
            f"- id:{s.id} | 姓名:{s.name} | 生日:{s.birthdate or '(空)'} | "
            f"Email:{s.email or '(空)'} | 學號:{s.student_number or '(空)'} | "
            f"電話:{s.phone or '(空)'}"
            for s in request.current_students
        )

        prompt = (
            f"目前的學生名單（共 {len(request.current_students)} 位）：\n{current_list}\n\n"
            f"用戶的修改指令：{request.user_input}"
        )

        result = await vertex_ai_service.generate_json(
            prompt=prompt,
            system_instruction=BATCH_STUDENT_EDIT_SYSTEM_PROMPT,
            temperature=0.1,
            max_tokens=8000,
        )

        students = result.get("students", [])
        message = result.get("message", "修改完成。")
        action = result.get("action", "unclear")

        validated = _validate_batch_edit_students(students, original_ids)

        return BatchStudentEditResponse(
            students=[ExistingStudentData(**s) for s in validated],
            message=message,
            action=action,
        )

    except Exception as e:
        logger.error(f"Failed to process batch student edit: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI 處理失敗：{str(e)}",
        )
