"""情境對話 AI 生圖服務 — Issue #1024。

Imagen 一律 mock。這裡驗的是我們自己的邏輯，重點有二：

1. **prompt 要把人物導向場景**。情境對話的題目幾乎都是校園情境，#1021 產題回傳的
   `image_prompt` 很可能長成「students talking in a classroom」——Imagen 對兒童影像
   有嚴格限制，直接送過去有相當比例會被安全過濾擋掉。
2. **被擋下時要能分辨**，不能跟「呼叫失敗」混在一起：前者要告訴老師換個描述，
   後者是「再試一次」。
"""
import pytest
from unittest.mock import patch, MagicMock

with patch.dict("sys.modules", {"vertexai": MagicMock()}):
    from services.scenario_dialogue_image import (
        ScenarioImageError,
        ScenarioImageBlockedError,
        ScenarioDialogueImageService,
        build_image_prompt,
    )


class TestPromptSteersAwayFromChildren:
    """人物描述導向場景，降低被安全過濾擋掉的機率（決策見模組說明）。"""

    @pytest.mark.parametrize(
        "raw",
        [
            "students talking in a classroom",
            "two kids playing basketball",
            "a child waiting for the bus",
            "schoolchildren in the playground",
            "a boy and a girl doing homework",
        ],
    )
    def test_child_words_are_rewritten(self, raw):
        prompt = build_image_prompt(raw)
        lowered = prompt.lower()
        for word in ["student", "kid", "child", "boy", "girl", "schoolchildren"]:
            assert word not in lowered, f"{word!r} 仍留在 prompt：{prompt}"

    def test_scene_without_people_is_kept_as_is(self):
        raw = "a yellow school bus on a street"
        assert raw in build_image_prompt(raw)

    def test_keeps_the_setting_after_rewriting(self):
        """改寫是把焦點移到場景，不是把情境整個丟掉。"""
        prompt = build_image_prompt("students talking in a classroom").lower()
        assert "classroom" in prompt

    def test_style_hint_is_appended(self):
        """統一的插畫風格 —— 同一份教材裡的圖不該一張水彩一張照片。"""
        prompt = build_image_prompt("a park").lower()
        assert "illustration" in prompt

    def test_blank_prompt_is_rejected(self):
        with pytest.raises(ScenarioImageError):
            build_image_prompt("   ")

    def test_prompt_is_length_capped(self):
        prompt = build_image_prompt("a park " * 500)
        assert len(prompt) <= ScenarioDialogueImageService.MAX_PROMPT_CHARS


class TestGenerateResultHandling:
    def _service(self):
        return ScenarioDialogueImageService()

    def test_empty_result_raises_blocked_error(self):
        """Imagen 被安全過濾擋下時回空清單，不是丟例外 —— 要自己判斷。"""
        with pytest.raises(ScenarioImageBlockedError):
            self._service().extract_image_bytes([])

    def test_result_without_bytes_raises_blocked(self):
        broken = MagicMock()
        broken._image_bytes = None
        with pytest.raises(ScenarioImageBlockedError):
            self._service().extract_image_bytes([broken])

    def test_returns_first_image_bytes(self):
        image = MagicMock()
        image._image_bytes = b"PNGDATA"
        assert self._service().extract_image_bytes([image]) == b"PNGDATA"


class TestBlockedIsNotAGenericFailure:
    def test_blocked_error_is_a_scenario_image_error(self):
        """繼承關係要在：既有只攔父類的呼叫端不會漏接。"""
        assert issubclass(ScenarioImageBlockedError, ScenarioImageError)
