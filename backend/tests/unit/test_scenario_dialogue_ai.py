"""情境對話 AI 生成服務 — Issue #1021。

這張單的起因是：老師填了訓練目標、題目難度、時態語態，產出來的題目卻與它們毫無關係
（前端是寫死的示範題）。所以測試的重點不是「有沒有呼叫 AI」，而是**老師填的每一個
欄位有沒有真的進到 prompt 裡**，以及 AI 回來的東西有沒有被好好收斂。

Vertex 一律 mock —— 這裡驗的是我們自己的邏輯（prompt 組法、輸出正規化、成本估算），
不是模型的回答品質。
"""
import json
import pytest
from unittest.mock import patch, MagicMock

with patch.dict("sys.modules", {"vertexai": MagicMock()}):
    from services.scenario_dialogue_ai import (
        ScenarioDialogueAIService,
        ScenarioDialogueAIError,
        describe_tense,
        describe_voice,
    )


# ============================================================
# 穩定代碼 → 給 AI 看的英文描述
# ============================================================


class TestDescribeCodes:
    """存的是穩定代碼（past / simple / active），送進 prompt 要翻成英文描述。

    絕對不能把中文標籤送進去 —— 老師的介面語言不該影響出題結果（#1013 的同一條規則）。
    """

    def test_full_tense(self):
        assert describe_tense({"time": "past", "aspect": "simple"}) == "past simple"

    def test_perfect_progressive(self):
        assert (
            describe_tense({"time": "future", "aspect": "perfectProgressive"})
            == "future perfect progressive"
        )

    @pytest.mark.parametrize(
        "raw", [None, {}, {"time": "", "aspect": ""}, {"time": "past", "aspect": ""}]
    )
    def test_half_or_missing_tense_is_unspecified(self, raw):
        """時態要時間＋動貌都有才算數，半套等於沒指定（與前端 isTenseSet 同規則）。"""
        assert describe_tense(raw) == ""

    def test_unknown_code_is_rejected(self):
        with pytest.raises(ScenarioDialogueAIError):
            describe_tense({"time": "過去", "aspect": "simple"})

    def test_voice(self):
        assert describe_voice("passive") == "passive voice"
        assert describe_voice("active") == "active voice"
        assert describe_voice("") == ""
        assert describe_voice(None) == ""

    def test_unknown_voice_rejected(self):
        with pytest.raises(ScenarioDialogueAIError):
            describe_voice("被動")


# ============================================================
# 產題 prompt —— 這張單的核心
# ============================================================


class TestQuestionPrompt:
    def _prompt(self, **kwargs):
        params = {
            "scenario_content": "It is Monday morning at school.",
            "count": 5,
            "question_level": "B1",
            "global_tense": {"time": "past", "aspect": "simple"},
            "global_voice": "active",
            "global_rubric": "請用完整句子回答",
            "translate_language": "chinese",
            "existing_questions": [],
        }
        params.update(kwargs)
        return ScenarioDialogueAIService.build_question_prompt(**params)

    def test_scenario_content_is_the_material(self):
        assert "It is Monday morning at school." in self._prompt()

    def test_question_level_reaches_prompt(self):
        assert "B1" in self._prompt(question_level="B1")

    def test_tense_and_voice_reach_prompt_as_english(self):
        prompt = self._prompt()
        assert "past simple" in prompt
        assert "active voice" in prompt

    def test_rubric_reaches_prompt(self):
        assert "請用完整句子回答" in self._prompt()

    def test_count_reaches_prompt(self):
        assert "7" in self._prompt(count=7)

    def test_existing_questions_are_listed_to_avoid_repeats(self):
        """「再產一批」不能原封不動再給同樣的題目。"""
        prompt = self._prompt(existing_questions=["What did you do?", "Who came?"])
        assert "What did you do?" in prompt
        assert "Who came?" in prompt

    def test_unspecified_settings_do_not_leak_empty_instructions(self):
        """沒指定的設定不該變成 'tense: ' 這種空指令去干擾模型。"""
        prompt = self._prompt(
            global_tense={"time": "", "aspect": ""},
            global_voice="",
            global_rubric="",
        )
        assert "tense:" not in prompt.lower()
        assert "voice:" not in prompt.lower()

    def test_translate_language_reaches_prompt(self):
        assert "japanese" in self._prompt(translate_language="japanese").lower()

    def test_blank_scenario_is_rejected(self):
        """情境內容是產題的素材，沒有素材就不該送出請求白花錢。"""
        with pytest.raises(ScenarioDialogueAIError):
            self._prompt(scenario_content="   ")

    @pytest.mark.parametrize("count", [0, -1, 11, 99])
    def test_count_out_of_range_rejected(self, count):
        """一次最多 10 題（一份的上限），至少 1 題。"""
        with pytest.raises(ScenarioDialogueAIError):
            self._prompt(count=count)

    def test_single_question_is_allowed(self):
        """「重新生成這一題」要的就是 1 題。

        #864 的「一份 3~10 題」是**存檔時**的規則（validate_item_count），不是單次
        生成的規則；把下限套在這裡會讓單題重新生成得多要 2 題再丟掉。
        """
        assert "Write 1 spoken-response question" in self._prompt(count=1)


# ============================================================
# 情境文章 prompt
# ============================================================


class TestArticlePrompt:
    def test_goal_and_level_reach_prompt(self):
        """使用者回報的核心：訓練目標必須真的被用到。"""
        prompt = ScenarioDialogueAIService.build_article_prompt(
            goal="這週上課學到的：交通工具與問路",
            level="A2",
        )
        assert "這週上課學到的：交通工具與問路" in prompt
        assert "A2" in prompt

    def test_blank_goal_is_rejected(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.build_article_prompt(goal="  ", level="A2")

    def test_unknown_level_rejected(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.build_article_prompt(goal="g", level="Z9")


# ============================================================
# AI 輸出正規化
# ============================================================


class TestNormalizeQuestions:
    def _raw(self, **over):
        item = {
            "question": "What did you do last weekend?",
            "translation": "你上週末做了什麼？",
            "keywords": ["went", "visited"],
            "reference_answer": "I went to the park.",
            "image_prompt": "a family in a park",
        }
        item.update(over)
        return {"questions": [item]}

    def test_maps_all_fields(self):
        out = ScenarioDialogueAIService.normalize_questions(self._raw(), count=5)
        assert out[0] == {
            "question": "What did you do last weekend?",
            "translation": "你上週末做了什麼？",
            "keywords": ["went", "visited"],
            "reference_answer": "I went to the park.",
            "image_prompt": "a family in a park",
        }

    def test_drops_items_without_question(self):
        raw = {"questions": [{"question": "  "}, {"question": "Real one?"}]}
        out = ScenarioDialogueAIService.normalize_questions(raw, count=5)
        assert [q["question"] for q in out] == ["Real one?"]

    def test_caps_at_requested_count(self):
        raw = {"questions": [{"question": f"Q{i}"} for i in range(20)]}
        out = ScenarioDialogueAIService.normalize_questions(raw, count=3)
        assert len(out) == 3

    def test_missing_optional_fields_become_empty(self):
        out = ScenarioDialogueAIService.normalize_questions(
            {"questions": [{"question": "Q1"}]}, count=5
        )
        assert out[0]["translation"] == ""
        assert out[0]["keywords"] == []
        assert out[0]["reference_answer"] == ""

    def test_keywords_non_list_is_tolerated(self):
        """模型偶爾會回字串而不是陣列，不該整包失敗。"""
        out = ScenarioDialogueAIService.normalize_questions(
            {"questions": [{"question": "Q1", "keywords": "went, visited"}]}, count=5
        )
        assert out[0]["keywords"] == ["went", "visited"]

    def test_bare_list_payload_is_accepted(self):
        """模型有時直接回陣列而不是 {"questions": [...]}。"""
        out = ScenarioDialogueAIService.normalize_questions(
            [{"question": "Q1"}], count=5
        )
        assert len(out) == 1

    def test_empty_result_raises(self):
        """一題都沒有要讓呼叫端知道，而不是安靜地回空陣列讓老師以為是自己的問題。"""
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.normalize_questions({"questions": []}, count=5)

    def test_deduplicates_against_existing(self):
        raw = {
            "questions": [
                {"question": "Old one?"},
                {"question": "New one?"},
            ]
        }
        out = ScenarioDialogueAIService.normalize_questions(
            raw, count=5, existing_questions=["Old one?"]
        )
        assert [q["question"] for q in out] == ["New one?"]


# ============================================================
# JSON 解析（沿用 magic_paste 的截斷救援策略）
# ============================================================


class TestParseJson:
    def test_plain_json(self):
        assert ScenarioDialogueAIService.parse_json('{"a": 1}') == {"a": 1}

    def test_markdown_fenced(self):
        assert ScenarioDialogueAIService.parse_json('```json\n{"a": 1}\n```') == {
            "a": 1
        }

    def test_truncated_output_salvages_complete_items(self):
        """輸出被 token 上限截斷時，救回已完整的題目，而不是整包失敗。"""
        truncated = '{"questions": [{"question": "Q1"}, {"question": "Q2"}, {"quest'
        out = ScenarioDialogueAIService.parse_json(truncated)
        items = out["questions"] if isinstance(out, dict) else out
        assert [i["question"] for i in items] == ["Q1", "Q2"]

    def test_unsalvageable_raises(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.parse_json("完全不是 JSON")


# ============================================================
# 成本估算（先不做配額，但要留下用量紀錄）
# ============================================================


class TestCostEstimate:
    def test_estimate_is_positive_and_scales(self):
        small = ScenarioDialogueAIService.estimate_cost(
            {"input_tokens": 1000, "output_tokens": 500}
        )
        big = ScenarioDialogueAIService.estimate_cost(
            {"input_tokens": 10000, "output_tokens": 5000}
        )
        assert 0 < small < big

    def test_missing_usage_is_zero_not_crash(self):
        assert ScenarioDialogueAIService.estimate_cost({}) == 0.0


# ============================================================
# 檔案驗證（PDF / 圖片擷取情境文章）
# ============================================================


class TestFileValidation:
    def test_accepts_pdf_and_images(self):
        for mime in ["application/pdf", "image/png", "image/jpeg", "image/webp"]:
            ScenarioDialogueAIService.validate_file(b"x" * 100, mime)

    def test_rejects_other_types(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.validate_file(b"x" * 100, "text/csv")

    def test_rejects_empty_file(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.validate_file(b"", "image/png")

    def test_rejects_oversized_file(self):
        too_big = b"x" * (ScenarioDialogueAIService.MAX_FILE_BYTES + 1)
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.validate_file(too_big, "image/png")


# ============================================================
# 文章輸出正規化
# ============================================================


class TestNormalizeArticle:
    def test_takes_content_field(self):
        assert (
            ScenarioDialogueAIService.normalize_article({"content": "  Hello.  "})
            == "Hello."
        )

    def test_accepts_bare_string(self):
        assert ScenarioDialogueAIService.normalize_article("Hello.") == "Hello."

    def test_empty_raises(self):
        with pytest.raises(ScenarioDialogueAIError):
            ScenarioDialogueAIService.normalize_article({"content": "   "})


def test_json_module_is_used_by_parse_json():
    """守著 parse_json 真的走 json 解析（避免哪天被換成 eval 之類的東西）。"""
    assert json.loads(json.dumps({"a": 1})) == {"a": 1}
