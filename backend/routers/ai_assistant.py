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


class FindFeatureRequest(BaseModel):
    user_input: str = Field(..., description="User's question about finding a feature")
    context: str = Field(default="organization", description="Current backend: 'organization' or 'teacher'")
    user_roles: List[str] = Field(default_factory=list, description="User's roles, e.g. ['org_admin', 'teacher']")
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


@router.post("/find-feature", response_model=FindFeatureResponse)
async def find_feature(request: FindFeatureRequest):
    """
    Help users find the right page/feature using Gemini.
    Returns a message with navigation suggestions.
    """
    try:
        context_label = "機構後台" if request.context == "organization" else "教師後台"
        has_org_admin = any(r in request.user_roles for r in ["org_owner", "org_admin"])
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
