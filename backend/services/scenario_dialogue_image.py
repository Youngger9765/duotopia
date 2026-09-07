"""情境對話 AI 生圖服務 — Issue #1024。

#1021 把情境對話的文字類 AI 都接成真的了，只有逐題生圖沒做（後端當時完全沒有圖片
生成能力）。這個模組補上，走 Vertex 的 Imagen。

生圖 prompt 從哪來
------------------

不必另外要老師寫：#1013 起每一題就有 ``item_metadata["scenario_dialogue"]
["image_prompt"]``，#1021 的產題也會請模型連生圖描述一起回傳。

人物與安全設定（這張單最重要的取捨）
------------------------------------

情境對話幾乎都是校園情境，AI 給的 image_prompt 十之八九長成
「students talking in a classroom」。**Imagen 對兒童影像有嚴格限制**，直接送過去會有
相當比例被安全過濾擋掉 —— 老師會看到「一半的題目生不出圖」而不知道為什麼。

所以這裡做兩件事：

1. ``person_generation="allow_adult"``：允許成人人物，不嘗試生成兒童。
2. :func:`build_image_prompt` 把兒童相關的詞改寫掉，把焦點移到**場景**
   （classroom / park / bus stop），而不是人物特寫。場景圖對「你和同學在聊天」這種
   題目仍然有輔助效果，而且穩定得多。

被安全過濾擋下時 Imagen 是**回空清單**而不是丟例外，所以要自己判斷並轉成
:class:`ScenarioImageBlockedError` —— 那要對老師說「換個描述試試」，與「呼叫失敗，
請稍後再試」是兩件事。

配額
----

生圖比文字貴一個量級、又是逐題觸發（一份 10 題可能按 10 次），所以有月上限
（``services/scenario_image_quota``）。完整的計價方式見 #1025，這一版只有「用完就擋」。
"""

import logging
import re
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# Imagen 模型。與 Gemini 一樣走 vertexai SDK（google-cloud-aiplatform）
IMAGE_MODEL = "imagen-3.0-generate-002"

# 生圖大約的單張成本（美元，僅供觀測與日誌，非計費用途）
_PRICE_USD_PER_IMAGE = 0.04


class ScenarioImageError(ValueError):
    """可預期的生圖錯誤（參數不合法、供應商回不出東西）。"""


class ScenarioImageBlockedError(ScenarioImageError):
    """被安全過濾擋下（Imagen 回空結果）。

    與一般失敗分開，因為對老師的意思不同：這個要說「換個描述試試」，一般失敗是
    「稍後再試」。繼承父類，所以只攔父類的呼叫端不會漏接。
    """


# 兒童相關詞 → 場景導向的替代寫法。
#
# 順序有意義：先處理複合詞（schoolchildren、school children），再處理單字，
# 否則 "children" 會先把 "schoolchildren" 咬掉一半。
_PERSON_REWRITES: List[tuple] = [
    (r"\bschool ?children\b", "a school scene"),
    (r"\bschoolkids\b", "a school scene"),
    (r"\bclassmates?\b", "a classroom scene"),
    (r"\bstudents?\b", "a classroom scene"),
    (r"\bpupils?\b", "a classroom scene"),
    (r"\bchildren\b", "people"),
    (r"\bchild\b", "a person"),
    (r"\bkids?\b", "people"),
    (r"\bboys?\b", "people"),
    (r"\bgirls?\b", "people"),
    (r"\bteenagers?\b", "people"),
    (r"\bteens?\b", "people"),
]

# 統一的插畫風格 —— 同一份教材裡的圖不該一張水彩一張照片
_STYLE_HINT = (
    "Simple, friendly flat illustration for a language-learning worksheet. "
    "Bright colors, clean background, no text or letters in the image."
)


def build_image_prompt(raw_prompt: Optional[str]) -> str:
    """把逐題的 image_prompt 變成真的要送給 Imagen 的 prompt。

    做兩件事：把兒童相關描述導向場景（見模組說明），以及補上統一的插畫風格。
    """
    text = (raw_prompt or "").strip()
    if not text:
        raise ScenarioImageError("生圖描述不可為空")

    for pattern, replacement in _PERSON_REWRITES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # 改寫後可能出現「a classroom scene ... a classroom scene」這種重複空白
    text = re.sub(r"\s+", " ", text).strip()

    prompt = f"{text}. {_STYLE_HINT}"
    return prompt[: ScenarioDialogueImageService.MAX_PROMPT_CHARS]


class ScenarioDialogueImageService:
    MAX_PROMPT_CHARS = 1000

    @staticmethod
    def extract_image_bytes(images: Any) -> bytes:
        """從 Imagen 回應取出圖片 bytes。

        被安全過濾擋下時 SDK 回的是**空清單**（不是例外），所以空清單一律當成被擋。
        """
        if not images:
            raise ScenarioImageBlockedError("AI 沒有產出圖片，可能是描述被安全過濾擋下，請換個描述再試")
        first = images[0]
        data = getattr(first, "_image_bytes", None)
        if not data:
            raise ScenarioImageBlockedError("AI 沒有產出圖片，可能是描述被安全過濾擋下，請換個描述再試")
        return data

    @staticmethod
    def estimate_cost(image_count: int = 1) -> float:
        return round(max(0, image_count) * _PRICE_USD_PER_IMAGE, 6)

    async def generate(self, raw_prompt: Optional[str]) -> dict:
        """產生一張圖，回傳 ``{"image_bytes": ..., "prompt": ..., "estimated_cost_usd": ...}``。

        呼叫端負責存檔與扣配額 —— 這裡只管「跟 Imagen 要一張圖」。
        """
        prompt = build_image_prompt(raw_prompt)

        from vertexai.vision_models import ImageGenerationModel
        from services.vertex_ai import get_vertex_ai_service

        # 確保 vertexai.init 已呼叫（同 magic_paste / scenario_dialogue_ai）
        get_vertex_ai_service()._ensure_initialized()

        model = ImageGenerationModel.from_pretrained(IMAGE_MODEL)
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="4:3",
            # 教材用途，安全過濾拉到較嚴格的一側
            safety_filter_level="block_some",
            # 不嘗試生成兒童影像（見模組說明），prompt 也已把兒童詞改寫成場景
            person_generation="allow_adult",
        )

        image_bytes = self.extract_image_bytes(response)
        cost = self.estimate_cost(1)
        logger.info(
            "scenario_dialogue_image generate | bytes=%s | cost≈$%.4f",
            len(image_bytes),
            cost,
        )
        return {
            "image_bytes": image_bytes,
            "prompt": prompt,
            "estimated_cost_usd": cost,
        }


_service: Optional[ScenarioDialogueImageService] = None


def get_scenario_dialogue_image_service() -> ScenarioDialogueImageService:
    global _service
    if _service is None:
        _service = ScenarioDialogueImageService()
    return _service
