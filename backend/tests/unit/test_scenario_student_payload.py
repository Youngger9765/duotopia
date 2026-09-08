"""情境對話的學生端／老師端序列化 — Issue #1031。

最重要的一條：**參考答案絕對不能出現在學生端 payload**。

`reference_answer` 是給老師與 AI 當語言特徵對照（時態、句型、用字水準、資訊完整度）
用的示範回答。學生看得到的話，這題就不是口說練習而是照著唸；而且它本來就不是唯一
正解 —— 口說同一題每個學生講的內容本來就不同。

這裡直接驗序列化函式本身（不需要 DB／HTTP），因為外洩與否完全由它們決定：學生端的
payload 是白名單組裝，只要組裝時走對函式就不會漏。
"""
import pytest

from utils import scenario_dialogue as sd


ITEM_BLOCK = {
    "tense_override": None,
    "voice_override": None,
    "keywords": ["park", "basketball"],
    "reference_answer": "I went to the park with my family last Saturday.",
    "rubric_note": "要說出地點",
    "image_prompt": "a family walking in a park",
}

SETTINGS = {
    "scenario_content": "It is Monday morning at school.",
    "question_level": "B1",
    "global_rubric": "請用完整句子回答",
    "global_tense": {"time": "past", "aspect": "simple"},
    "global_voice": "active",
    "translate_language": "chinese",
    "tts_settings": {"accent": "US", "gender": "Female", "speed": "Normal x1"},
}


class TestStudentNeverSeesTheReferenceAnswer:
    def test_reference_answer_is_not_in_the_student_item_view(self):
        view = sd.public_item_view(ITEM_BLOCK, SETTINGS)
        assert "reference_answer" not in view
        # 連值都不該以任何 key 出現
        assert ITEM_BLOCK["reference_answer"] not in str(view)

    def test_image_prompt_is_not_in_the_student_item_view(self):
        """生圖 prompt 是內部用的，學生看到只會困惑。"""
        view = sd.public_item_view(ITEM_BLOCK, SETTINGS)
        assert "image_prompt" not in view
        assert ITEM_BLOCK["image_prompt"] not in str(view)

    def test_authoring_settings_are_not_in_the_student_settings_view(self):
        """題目難度、整體時態語態、TTS 設定都是出題端的事。"""
        view = sd.public_settings_view(SETTINGS)
        for key in ("question_level", "global_tense", "global_voice", "tts_settings"):
            assert key not in view, f"{key} 不該給學生"


class TestStudentGetsWhatTheyNeedToAnswer:
    def test_item_view_has_the_answering_hints(self):
        view = sd.public_item_view(ITEM_BLOCK, SETTINGS)
        assert view["keywords"] == ["park", "basketball"]
        assert view["rubric_note"] == "要說出地點"

    def test_tense_and_voice_are_already_resolved(self):
        """學生端不該自己做「沿用整體」的繼承推導 —— 後端解析好再給。"""
        view = sd.public_item_view(ITEM_BLOCK, SETTINGS)
        assert view["tense"] == {"time": "past", "aspect": "simple"}
        assert view["voice"] == "active"

    def test_item_that_opted_out_keeps_its_own_empty_values(self):
        """本題已脫鉤（明確不指定）時，不該被整體的值蓋回去。"""
        block = {
            **ITEM_BLOCK,
            "tense_override": {"time": "", "aspect": ""},
            "voice_override": "",
        }
        view = sd.public_item_view(block, SETTINGS)
        assert view["tense"] == {"time": "", "aspect": ""}
        assert view["voice"] == ""

    def test_settings_view_has_the_context_and_guidance(self):
        view = sd.public_settings_view(SETTINGS)
        assert view["scenario_content"] == "It is Monday morning at school."
        assert view["global_rubric"] == "請用完整句子回答"
        assert view["translate_language"] == "chinese"


class TestMissingDataDoesNotBreakStudents:
    """舊資料或非情境對話轉過來的內容不該讓學生端整頁壞掉。"""

    @pytest.mark.parametrize("block", [None, {}, {"keywords": None}])
    def test_item_view_tolerates_missing_block(self, block):
        view = sd.public_item_view(block, SETTINGS)
        assert view["keywords"] == []
        assert "reference_answer" not in view

    @pytest.mark.parametrize("settings", [None, {}])
    def test_settings_view_tolerates_missing_settings(self, settings):
        view = sd.public_settings_view(settings)
        assert view["scenario_content"] == ""
        assert view["global_rubric"] == ""

    def test_item_view_without_settings_falls_back_to_unspecified(self):
        """沒有整體設定時，沿用中的題目就是「未指定」，不是崩潰。"""
        view = sd.public_item_view(ITEM_BLOCK, None)
        assert view["tense"] == {"time": "", "aspect": ""}
        assert view["voice"] == ""


class TestTeacherViewIsTheStudentViewPlusTheReferenceAnswer:
    """老師端與學生端只差「參考答案給不給」—— 兩者放在同一個模組才不會各自漂移。"""

    def test_teacher_view_has_the_reference_answer(self):
        view = sd.teacher_item_view(ITEM_BLOCK, SETTINGS)
        assert view["reference_answer"] == ITEM_BLOCK["reference_answer"]

    def test_teacher_view_is_a_superset_of_the_student_view(self):
        student = sd.public_item_view(ITEM_BLOCK, SETTINGS)
        teacher = sd.teacher_item_view(ITEM_BLOCK, SETTINGS)

        for key, value in student.items():
            assert teacher[key] == value, f"{key} 兩邊不一致"
        # 唯一的差別
        assert set(teacher) - set(student) == {"reference_answer"}

    def test_teacher_view_still_hides_the_image_prompt(self):
        """生圖 prompt 是內部用的，老師批改也不需要看。"""
        view = sd.teacher_item_view(ITEM_BLOCK, SETTINGS)
        assert "image_prompt" not in view

    def test_teacher_view_tolerates_missing_block(self):
        view = sd.teacher_item_view(None, SETTINGS)
        assert view["reference_answer"] == ""
        assert view["keywords"] == []


class TestGradingCriteria:
    """AI 評分要看的東西 — Issue #1035。

    評分端點不該自己再手組一份 dict：那等於在模組外複製資料形狀，正是 #1034 review
    抓到的問題。criteria 是老師端的視角（含參考答案）再加上題目本文與整份設定。
    """

    QUESTION = "What did you do last weekend?"

    def test_carries_everything_the_prompt_needs(self):
        criteria = sd.grading_criteria(self.QUESTION, ITEM_BLOCK, SETTINGS)

        assert criteria["question"] == self.QUESTION
        assert criteria["reference_answer"] == ITEM_BLOCK["reference_answer"]
        assert criteria["keywords"] == ITEM_BLOCK["keywords"]
        assert criteria["rubric_note"] == ITEM_BLOCK["rubric_note"]
        assert criteria["tense"] == {"time": "past", "aspect": "simple"}
        assert criteria["voice"] == "active"
        assert criteria["global_rubric"] == SETTINGS["global_rubric"]
        assert criteria["question_level"] == SETTINGS["question_level"]

    def test_never_leaks_the_image_prompt(self):
        """生圖 prompt 不是評分依據，餵給模型只會干擾。"""
        assert "image_prompt" not in sd.grading_criteria(
            self.QUESTION, ITEM_BLOCK, SETTINGS
        )

    def test_item_override_beats_the_global_setting(self):
        block = {**ITEM_BLOCK, "voice_override": "passive"}
        criteria = sd.grading_criteria(self.QUESTION, block, SETTINGS)
        assert criteria["voice"] == "passive"

    def test_tolerates_missing_block_and_settings(self):
        """舊資料或非本題型轉過來的內容，評分還是要能組出 prompt。"""
        criteria = sd.grading_criteria(self.QUESTION, None, None)
        assert criteria["question"] == self.QUESTION
        assert criteria["reference_answer"] == ""
        assert criteria["keywords"] == []
        assert criteria["global_rubric"] == ""
        assert criteria["question_level"] == ""
