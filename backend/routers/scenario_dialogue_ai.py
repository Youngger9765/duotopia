"""情境對話 AI API — Issue #1021。

- POST /api/teachers/scenario-dialogue/generate-article   依訓練目標生成情境文章
- POST /api/teachers/scenario-dialogue/generate-questions 依情境文章與出題設定產題
- POST /api/teachers/scenario-dialogue/extract-article    從圖片/PDF 擷取情境文章

三個端點都**不寫 DB**：產出來的東西先回前端給老師看、能改，按儲存才走
`/api/teachers/lessons/{id}/contents`（#1013）存起來。

配額：這一版不擋，只記 token 用量與估算成本（回傳裡也帶著，方便觀測）。等實際用量
出來再決定免費額度，屆時比照 `services/magic_paste_quota`。
"""

import logging
from typing import Annotated, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field, StringConstraints

from models import Teacher

# 共用同一份教師鑑權依賴，避免 auth 邏輯分叉（同 magic_paste）
from routers.teachers import get_current_teacher
from services.scenario_dialogue_ai import (
    ScenarioDialogueAIError,
    get_scenario_dialogue_ai_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teachers/scenario-dialogue", tags=["scenario-dialogue"])


# 各欄位的長度上限。這一版沒有配額（見 #1025），送進 prompt 的東西越大成本越高，
# 所以先用寬鬆但有界的上限擋住異常 payload —— 數字都遠大於面板正常能填出來的量，
# 老師不會撞到。
MAX_GOAL_CHARS = 1000
MAX_SCENARIO_CHARS = 8000
MAX_RUBRIC_CHARS = 2000
MAX_LANGUAGE_CHARS = 50
MAX_LEVEL_CHARS = 10
MAX_EXISTING_QUESTIONS = 20
MAX_EXISTING_QUESTION_CHARS = 1000


class GenerateArticleRequest(BaseModel):
    """訓練目標是必填 —— 沒有它就是舊 stub 那種與老師無關的產出。"""

    goal: str = Field(max_length=MAX_GOAL_CHARS)
    # 文章難度，空字串 = 不指定（CEFR 代碼，服務層驗證）
    level: str = Field(default="", max_length=MAX_LEVEL_CHARS)


class GenerateQuestionsRequest(BaseModel):
    scenario_content: str = Field(max_length=MAX_SCENARIO_CHARS)
    count: int
    question_level: str = Field(default="", max_length=MAX_LEVEL_CHARS)
    # 穩定代碼，例如 {"time": "past", "aspect": "simple"}；服務層會翻成英文描述
    global_tense: Optional[Dict[str, str]] = None
    global_voice: str = Field(default="", max_length=MAX_LEVEL_CHARS)
    global_rubric: str = Field(default="", max_length=MAX_RUBRIC_CHARS)
    # 「其他」語言存的是老師自己打的名字（#1016），不能用白名單；服務層會再壓成單行
    translate_language: str = Field(default="", max_length=MAX_LANGUAGE_CHARS)
    # 已經在清單上的題目，避免「再產一批」給出重複的。
    # 上限比 MAX_ITEMS（10）寬一點，避免老師剛好卡在邊界時整個請求被擋掉。
    existing_questions: List[
        Annotated[str, StringConstraints(max_length=MAX_EXISTING_QUESTION_CHARS)]
    ] = Field(default_factory=list, max_length=MAX_EXISTING_QUESTIONS)


def _bad_request(exc: ScenarioDialogueAIError) -> HTTPException:
    """參數不合法 → 400。這些都是前端該擋而沒擋的情況，訊息直接給前端顯示。"""
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


def _ai_failed(what: str, exc: Exception) -> HTTPException:
    logger.error("[scenario-dialogue] %s failed: %s", what, exc, exc_info=True)
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="AI 產生失敗，請稍後再試",
    )


@router.post("/generate-article")
async def generate_article(
    payload: GenerateArticleRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    service = get_scenario_dialogue_ai_service()
    try:
        return await service.generate_article(goal=payload.goal, level=payload.level)
    except ScenarioDialogueAIError as e:
        # 參數問題（空的訓練目標、不合法的難度）與「模型這次沒產出東西」都會走這裡。
        # 前者是 400；後者其實是 502 比較貼切，但對老師來說都是「再試一次」，
        # 訊息本身已經說清楚，不再細分以免端點邏輯變複雜。
        raise _bad_request(e)
    except Exception as e:
        raise _ai_failed("generate-article", e)


@router.post("/generate-questions")
async def generate_questions(
    payload: GenerateQuestionsRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
):
    service = get_scenario_dialogue_ai_service()
    try:
        return await service.generate_questions(
            scenario_content=payload.scenario_content,
            count=payload.count,
            question_level=payload.question_level,
            global_tense=payload.global_tense,
            global_voice=payload.global_voice,
            global_rubric=payload.global_rubric,
            translate_language=payload.translate_language,
            existing_questions=payload.existing_questions,
        )
    except ScenarioDialogueAIError as e:
        raise _bad_request(e)
    except Exception as e:
        raise _ai_failed("generate-questions", e)


@router.post("/extract-article")
async def extract_article(
    file: UploadFile = File(...),
    current_teacher: Teacher = Depends(get_current_teacher),
):
    """從老師上傳的圖片 / PDF 擷取情境文章。"""
    service = get_scenario_dialogue_ai_service()

    # 大小把關優先：最多讀「上限 + 1」bytes，超過就中止，避免超大檔整包先進記憶體
    # （magic_paste review PR #943 #1 的同一個理由）
    max_bytes = service.MAX_FILE_BYTES
    file_bytes = await file.read(max_bytes + 1)
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"檔案過大（上限 {max_bytes // (1024 * 1024)}MB）",
        )

    try:
        return await service.extract_article(
            file_bytes=file_bytes, mime_type=file.content_type
        )
    except ScenarioDialogueAIError as e:
        raise _bad_request(e)
    except Exception as e:
        raise _ai_failed("extract-article", e)
