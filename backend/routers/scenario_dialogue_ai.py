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
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, StringConstraints

from database import get_db
from models import Teacher

# 共用同一份教師鑑權依賴，避免 auth 邏輯分叉（同 magic_paste）
from routers.teachers import get_current_teacher
from services import scenario_image_quota as siq
from services.scenario_dialogue_image import (
    ScenarioDialogueImageService,
    ScenarioImageBlockedError,
    ScenarioImageError,
    get_scenario_dialogue_image_service,
)
from services.scenario_dialogue_ai import (
    ScenarioDialogueAIError,
    ScenarioDialogueAIOutputError,
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
# 與服務層同一個來源 —— 兩邊各寫一次 1000 的話，改了 Pydantic 上限卻忘了改截斷
# 上限（或反過來）不會有人發現（PR #1027 review）
MAX_IMAGE_PROMPT_CHARS = ScenarioDialogueImageService.MAX_PROMPT_CHARS


class GenerateArticleRequest(BaseModel):
    """訓練目標是必填 —— 沒有它就是舊 stub 那種與老師無關的產出。"""

    goal: str = Field(max_length=MAX_GOAL_CHARS)
    # 文章難度，空字串 = 不指定（CEFR 代碼，服務層驗證）
    level: str = Field(default="", max_length=MAX_LEVEL_CHARS)


class GenerateImageRequest(BaseModel):
    """逐題生圖。`image_prompt` 已經存在 item_metadata 裡（#1013），前端直接帶回來。"""

    image_prompt: str = Field(max_length=MAX_IMAGE_PROMPT_CHARS)


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
    except ScenarioDialogueAIOutputError as e:
        # 呼叫成功但模型沒給出可用的東西 —— 不是老師填錯，回 502「請稍後再試」。
        # 這個 except 必須排在父類 ScenarioDialogueAIError 前面（PR #1023 review）
        raise _ai_failed("generate-article", e)
    except ScenarioDialogueAIError as e:
        # 參數問題（空的訓練目標、不合法的難度）→ 400，訊息直接給老師看
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
    except ScenarioDialogueAIOutputError as e:
        raise _ai_failed("generate-questions", e)
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
    except ScenarioDialogueAIOutputError as e:
        raise _ai_failed("extract-article", e)
    except ScenarioDialogueAIError as e:
        raise _bad_request(e)
    except Exception as e:
        raise _ai_failed("extract-article", e)


@router.get("/image-quota")
def image_quota(
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """本月生圖剩餘次數（Issue #1024）。前端用來顯示，也用來決定要不要先擋。"""
    return siq.get_quota_status(db, current_teacher)


@router.post("/generate-image")
async def generate_image(
    payload: GenerateImageRequest,
    current_teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
):
    """依逐題的 image_prompt 生一張圖，存好之後回傳網址。

    順序是「**先佔位額度** → 生圖 → 存檔 → 失敗才退款」（PR #1027 review）。

    先查一次 `get_quota_status` 再打 AI、最後才 consume 是擋不住並發的：同一位老師在
    29/30 時同時送兩個請求，兩個都會通過那次檢查，兩張都生出來、兩張都回 200，月上限
    等於形同虛設。改成先 consume 佔位，額度用完在**打 AI 之前**就回 402，一次呼叫都
    不會浪費。

    老師沒拿到圖的情況一律退款（被安全過濾擋下、存檔失敗）—— 扣他一次只會讓他不敢
    再試，比照 magic_paste 擷取到 0 項不扣額的決策。
    """
    charge = siq.consume(db, current_teacher)
    if charge["charged"] is None:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "SCENARIO_IMAGE_QUOTA_EXCEEDED",
                "message": "本月 AI 生成圖片次數已用完，可以改用手動上傳圖片。",
                "quota": charge,
            },
        )

    service = get_scenario_dialogue_image_service()
    try:
        result = await service.generate(payload.image_prompt)
    except ScenarioImageBlockedError as e:
        # 被安全過濾擋下：這是「換個描述」而不是「稍後再試」，訊息要能直接給老師看
        siq.refund(db, current_teacher)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except ScenarioImageError as e:
        siq.refund(db, current_teacher)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        siq.refund(db, current_teacher)
        raise _ai_failed("generate-image", e)

    try:
        from services.image_upload import get_image_upload_service

        image_url = get_image_upload_service().store_image_bytes(
            result["image_bytes"], "image/png"
        )
    except Exception as e:
        # 圖生出來了卻存不進去 —— 老師一樣沒拿到圖，退款
        siq.refund(db, current_teacher)
        raise _ai_failed("generate-image-store", e)

    return {
        "image_url": image_url,
        "prompt": result["prompt"],
        "estimated_cost_usd": result["estimated_cost_usd"],
        "quota": charge,
    }
