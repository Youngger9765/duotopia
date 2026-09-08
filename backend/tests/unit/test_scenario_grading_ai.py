"""情境對話 AI 評分 — Issue #1035。

這張單最容易做錯的一件事：**把參考答案當標準答案去逐字比對**。

口說同一題每個學生講的內容本來就不同（「你上週末做了什麼？」有幾百種合理回答）。
既有的 Azure 發音評測之所以不能用，就是因為它的 `enableMiscue` 會把「講得跟範例不同」
判成漏字錯字。所以這裡的測試重點是 **prompt 有沒有把評分標準講對**：評語言特徵
（時態、句型、用字水準、資訊完整度），不是評字面相似度。

Vertex 一律 mock —— 驗的是我們自己的 prompt 組法與輸出收斂，不是模型的判斷品質。
"""
import pytest

# 一般 import 即可：本模組對 vertexai 的 import 全都在函式內（見服務模組的說明），
# 匯入時不會碰到 SDK。
#
# 不要用 `with patch.dict("sys.modules", {"vertexai": MagicMock()})` 包住這個 import：
# patch.dict 離開時會把「在 with 內才被載入」的模組從 sys.modules 移除，但
# services 套件上的屬性仍指向舊的模組物件。之後 mock.patch("services.scenario_grading_ai
# .ScenarioGradingService.grade") 會 patch 到那個舊 class，而端點在 request 時
# 重新 import 拿到的是新 class —— 於是那次呼叫會真的打 Vertex。這個坑只會讓「同時跑
# 這個檔和端點測試時的第一個測試」壞掉，非常難查。
from services.scenario_grading_ai import (  # noqa: E402
    ScenarioGradingError,
    ScenarioGradingService,
    to_gcs_uri,
)


CRITERIA = {
    "question": "What did you do last weekend?",
    "reference_answer": "I went to the park with my family last Saturday.",
    "keywords": ["went", "park"],
    "tense": {"time": "past", "aspect": "simple"},
    "voice": "active",
    "rubric_note": "要說出地點",
    "global_rubric": "請用完整句子回答",
    "question_level": "B1",
}


class TestPromptSaysWhatToGradeOn:
    def _prompt(self, **over):
        return ScenarioGradingService.build_prompt({**CRITERIA, **over})

    def test_question_and_reference_are_in_the_prompt(self):
        prompt = self._prompt()
        assert CRITERIA["question"] in prompt
        assert CRITERIA["reference_answer"] in prompt

    def test_prompt_forbids_literal_comparison(self):
        """參考答案必須被標成『示範』，而且明講不要比對字面。

        這是整張單的核心 —— 少了這段，模型會很自然地拿學生的話去對範例。
        """
        prompt = self._prompt().lower()
        assert "do not" in prompt or "don't" in prompt
        # 明確提到「不要逐字／字面比對」的意思
        assert "word-for-word" in prompt or "literal" in prompt
        # 並說明範例的正確用途
        assert "example" in prompt or "sample" in prompt

    def test_prompt_lists_the_language_features(self):
        prompt = self._prompt().lower()
        for feature in ["tense", "vocabulary", "complete"]:
            assert feature in prompt, f"評分面向缺少 {feature}"

    def test_teacher_settings_reach_the_prompt(self):
        prompt = self._prompt()
        assert "past simple" in prompt
        assert "active voice" in prompt
        assert CRITERIA["rubric_note"] in prompt
        assert CRITERIA["global_rubric"] in prompt
        assert "B1" in prompt

    def test_keywords_reach_the_prompt(self):
        prompt = self._prompt()
        for word in CRITERIA["keywords"]:
            assert word in prompt

    def test_unspecified_settings_do_not_become_empty_instructions(self):
        """老師沒指定的東西不該變成空指令去干擾模型（同 #1021 的作法）。"""
        prompt = self._prompt(
            tense={"time": "", "aspect": ""},
            voice="",
            rubric_note="",
            global_rubric="",
            keywords=[],
            question_level="",
        ).lower()
        assert "tense:" not in prompt
        assert "keywords:" not in prompt

    def test_missing_question_is_rejected(self):
        with pytest.raises(ScenarioGradingError):
            self._prompt(question="   ")

    def test_reference_answer_is_optional(self):
        """老師沒寫參考答案也要評得動 —— 靠題目、必用字詞與時態語態即可。"""
        prompt = ScenarioGradingService.build_prompt(
            {**CRITERIA, "reference_answer": ""}
        )
        assert CRITERIA["question"] in prompt


class TestRecordingUri:
    def test_public_gcs_url_becomes_gs_uri(self):
        assert (
            to_gcs_uri(
                "https://storage.googleapis.com/duotopia-audio/recordings/a.webm"
            )
            == "gs://duotopia-audio/recordings/a.webm"
        )

    def test_nested_path_is_preserved(self):
        assert (
            to_gcs_uri("https://storage.googleapis.com/b/x/y/z.mp3")
            == "gs://b/x/y/z.mp3"
        )

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:8080/static/recordings/a.webm",  # 本機開發
            "https://example.com/a.webm",
            "",
            None,
        ],
    )
    def test_non_gcs_urls_return_none(self, url):
        """非 GCS 的網址回 None，呼叫端才知道要改用下載的方式（本機開發會走到）。"""
        assert to_gcs_uri(url) is None


class TestNormalizeResult:
    def _raw(self, **over):
        return {
            "transcript": "I went to the park with my friends.",
            "scores": {
                "content": 80,
                "grammar": 70,
                "vocabulary": 75,
                "keywords": 100,
            },
            "overall": 78,
            "feedback": "時態正確，可以多描述細節",
            "suggested_pass": True,
            **over,
        }

    def test_maps_all_fields(self):
        out = ScenarioGradingService.normalize_result(self._raw())
        assert out["transcript"] == "I went to the park with my friends."
        assert out["scores"]["grammar"] == 70
        assert out["overall"] == 78
        assert out["suggested_pass"] is True

    def test_scores_are_clamped_to_0_100(self):
        out = ScenarioGradingService.normalize_result(
            self._raw(scores={"content": 140, "grammar": -20}, overall=999)
        )
        assert out["scores"]["content"] == 100
        assert out["scores"]["grammar"] == 0
        assert out["overall"] == 100

    def test_missing_scores_become_none_not_zero(self):
        """沒評到的面向要留白，不能當成 0 分 —— 0 分和「沒評」意思差很多。"""
        out = ScenarioGradingService.normalize_result(self._raw(scores={"content": 80}))
        assert out["scores"]["content"] == 80
        assert out["scores"]["grammar"] is None

    def test_non_numeric_score_is_treated_as_missing(self):
        out = ScenarioGradingService.normalize_result(
            self._raw(scores={"content": "很好"})
        )
        assert out["scores"]["content"] is None

    def test_empty_transcript_raises(self):
        """一個字都沒轉出來代表這次不可用，要讓老師知道，而不是給一份空評分。"""
        with pytest.raises(ScenarioGradingError):
            ScenarioGradingService.normalize_result(self._raw(transcript="  "))

    def test_bare_json_without_scores_raises(self):
        with pytest.raises(ScenarioGradingError):
            ScenarioGradingService.normalize_result({"transcript": "hello"})


class TestCost:
    def test_cost_is_positive_and_scales(self):
        small = ScenarioGradingService.estimate_cost(
            {"input_tokens": 1000, "output_tokens": 200}
        )
        big = ScenarioGradingService.estimate_cost(
            {"input_tokens": 8000, "output_tokens": 800}
        )
        assert 0 < small < big

    def test_missing_usage_is_zero(self):
        assert ScenarioGradingService.estimate_cost({}) == 0.0
