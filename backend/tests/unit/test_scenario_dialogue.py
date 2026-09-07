"""情境對話（Scenario Dialogue）儲存 — Issue #1013。

重點在兩件會靜默壞掉的事：

1. ``tense_override`` / ``voice_override`` 的 ``None``（沿用整體）與空字串
   （本題明確不指定）是**兩種行為**，一旦被壓平，老師之後改整體設定時，
   本來該跟著變的題目不會變（或反過來）。這裡從正規化一路測到 API round-trip。
2. ``reference_answer`` 不可外流到學生端。
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from auth import create_access_token
from models import Teacher, Program, Classroom, Lesson
from utils import scenario_dialogue as sd
from utils.score_category import resolve_score_category


# ============================================================
# 正規化 / null 語意
# ============================================================


class TestTenseNullSemantics:
    """None = 沿用整體；{"time": "", "aspect": ""} = 本題明確不指定。不可壓平。"""

    def test_none_stays_none(self):
        assert sd.normalize_tense(None) is None

    def test_empty_dict_is_not_none(self):
        result = sd.normalize_tense({"time": "", "aspect": ""})
        assert result == {"time": "", "aspect": ""}
        assert result is not None

    def test_voice_none_stays_none(self):
        assert sd.normalize_voice(None) is None

    def test_voice_empty_string_is_not_none(self):
        assert sd.normalize_voice("") == ""

    def test_item_block_keeps_none(self):
        block = sd.normalize_item({"tense_override": None, "voice_override": None})
        assert block["tense_override"] is None
        assert block["voice_override"] is None

    def test_item_block_keeps_explicit_empty(self):
        block = sd.normalize_item(
            {"tense_override": {"time": "", "aspect": ""}, "voice_override": ""}
        )
        assert block["tense_override"] == {"time": "", "aspect": ""}
        assert block["voice_override"] == ""


class TestStableCodes:
    """存的是穩定代碼，不是中文；未知代碼直接擋下。"""

    def test_valid_tense(self):
        assert sd.normalize_tense({"time": "past", "aspect": "perfectProgressive"}) == {
            "time": "past",
            "aspect": "perfectProgressive",
        }

    def test_valid_voice(self):
        assert sd.normalize_voice("passive") == "passive"

    @pytest.mark.parametrize("bad", ["過去", "Past", "pastx"])
    def test_rejects_unknown_time(self, bad):
        with pytest.raises(ValueError):
            sd.normalize_tense({"time": bad, "aspect": "simple"})

    def test_rejects_unknown_aspect(self):
        with pytest.raises(ValueError):
            sd.normalize_tense({"time": "past", "aspect": "continuous"})

    def test_rejects_unknown_voice(self):
        with pytest.raises(ValueError):
            sd.normalize_voice("middle")

    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError):
            sd.normalize_settings({"question_level": "A9"})


class TestNormalizeSettings:
    def test_defaults_are_explicit_not_none(self):
        """整體評分標準沒有「沿用上層」，缺值落成 EMPTY_TENSE 而不是 None。"""
        settings = sd.normalize_settings({})
        assert settings["global_tense"] == {"time": "", "aspect": ""}
        assert settings["global_voice"] == ""
        assert settings["scenario_content"] == ""
        assert settings["tts_settings"] is None

    def test_empty_scenario_content_is_legal(self):
        """老師只給標題、自己出題也存得起來（前端 handleSave 的合法路徑）。"""
        assert sd.normalize_settings({"scenario_content": ""})["scenario_content"] == ""

    def test_full_payload(self):
        settings = sd.normalize_settings(
            {
                "scenario_content": "It is Monday morning.",
                "question_level": "B1",
                "global_rubric": "請用完整句子回答",
                "global_tense": {"time": "past", "aspect": "simple"},
                "global_voice": "active",
                "translate_language": "chinese",
                "tts_settings": {
                    "accent": "American English",
                    "gender": "Female",
                    "speed": "Normal x1",
                },
            }
        )
        assert settings["question_level"] == "B1"
        assert settings["global_tense"] == {"time": "past", "aspect": "simple"}
        assert settings["tts_settings"]["gender"] == "Female"

    def test_none_means_not_supplied(self):
        assert sd.normalize_settings(None) is None


class TestKeywords:
    def test_strips_and_drops_blanks(self):
        block = sd.normalize_item({"keywords": [" went ", "", "   ", "visited"]})
        assert block["keywords"] == ["went", "visited"]

    def test_missing_is_empty_list(self):
        assert sd.normalize_item({})["keywords"] == []


class TestBuildItemMetadataBlock:
    """payload 沒帶就沿用既有 —— 只改音檔不該把參考答案洗掉。"""

    def test_absent_falls_back_to_existing(self):
        existing = {sd.SCENARIO_ITEM_KEY: {"reference_answer": "keep me"}}
        block = sd.build_item_metadata_block({"audio_url": "x.mp3"}, existing)
        assert block == {"reference_answer": "keep me"}

    def test_absent_with_no_existing_is_none(self):
        assert sd.build_item_metadata_block({"audio_url": "x.mp3"}, None) is None

    def test_present_replaces(self):
        existing = {sd.SCENARIO_ITEM_KEY: {"reference_answer": "old"}}
        block = sd.build_item_metadata_block(
            {sd.SCENARIO_ITEM_KEY: {"reference_answer": "new"}}, existing
        )
        assert block["reference_answer"] == "new"


class TestResolveEffective:
    SETTINGS = {
        "global_tense": {"time": "past", "aspect": "simple"},
        "global_voice": "active",
    }

    def test_none_inherits_global(self):
        block = {"tense_override": None, "voice_override": None}
        assert sd.resolve_effective_tense(block, self.SETTINGS) == {
            "time": "past",
            "aspect": "simple",
        }
        assert sd.resolve_effective_voice(block, self.SETTINGS) == "active"

    def test_explicit_empty_does_not_inherit(self):
        """本題脫鉤後，整體是什麼都不影響它 —— 這正是 null 不能壓平的原因。"""
        block = {
            "tense_override": {"time": "", "aspect": ""},
            "voice_override": "",
        }
        assert sd.resolve_effective_tense(block, self.SETTINGS) == {
            "time": "",
            "aspect": "",
        }
        assert sd.resolve_effective_voice(block, self.SETTINGS) == ""

    def test_override_wins(self):
        block = {
            "tense_override": {"time": "future", "aspect": "perfect"},
            "voice_override": "passive",
        }
        assert sd.resolve_effective_tense(block, self.SETTINGS)["time"] == "future"
        assert sd.resolve_effective_voice(block, self.SETTINGS) == "passive"


class TestStudentSafeView:
    def test_reference_answer_never_reaches_students(self):
        block = sd.normalize_item(
            {
                "reference_answer": "I went to the park.",
                "image_prompt": "a family in a park",
                "rubric_note": "說出兩個活動",
                "keywords": ["went"],
            }
        )
        view = sd.public_item_view(block, {"global_voice": "active"})
        assert "reference_answer" not in view
        assert "image_prompt" not in view
        assert view["rubric_note"] == "說出兩個活動"
        assert view["keywords"] == ["went"]
        assert view["voice"] == "active"

    def test_public_settings_view_drops_authoring_fields(self):
        settings = sd.normalize_settings(
            {"scenario_content": "S", "global_rubric": "R", "question_level": "B1"}
        )
        view = sd.public_settings_view(settings)
        assert view["scenario_content"] == "S"
        assert view["global_rubric"] == "R"
        assert "question_level" not in view


class TestItemCount:
    @pytest.mark.parametrize("n", [3, 5, 10])
    def test_allowed(self, n):
        sd.validate_item_count(n)

    @pytest.mark.parametrize("n", [0, 2, 11])
    def test_rejected(self, n):
        with pytest.raises(ValueError):
            sd.validate_item_count(n)


class TestScoreCategory:
    """情境對話＝開口作答，比照 reading / word_reading 恆為 speaking。"""

    @pytest.mark.parametrize("audio", [False, True])
    def test_always_speaking(self, audio):
        assert resolve_score_category("scenario_dialogue", audio) == "speaking"


# ============================================================
# API round-trip
# ============================================================


@pytest.fixture
def auth_token(db_session: Session):
    teacher = Teacher(
        email="scenario@teacher.com",
        name="Scenario Teacher",
        password_hash="x",
        email_verified=True,
    )
    db_session.add(teacher)
    db_session.commit()

    classroom = Classroom(name="C", teacher_id=teacher.id, grade="Grade 1")
    db_session.add(classroom)
    db_session.commit()

    program = Program(
        name="P", description="d", teacher_id=teacher.id, classroom_id=classroom.id
    )
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(
        name="L",
        description="d",
        program_id=program.id,
        order_index=1,
        estimated_minutes=30,
    )
    db_session.add(lesson)
    db_session.commit()

    return create_access_token({"sub": str(teacher.id), "type": "teacher"})


def _payload(**overrides):
    """三題：沿用整體 / 自訂 / 明確不指定 —— 三種狀態各一。"""
    payload = {
        "type": "SCENARIO_DIALOGUE",
        "title": "上週末做了什麼",
        "scenario_settings": {
            "scenario_content": "It is Monday morning at school.",
            "question_level": "B1",
            "global_rubric": "請用完整句子回答",
            "global_tense": {"time": "past", "aspect": "simple"},
            "global_voice": "active",
            "translate_language": "chinese",
            "tts_settings": {
                "accent": "American English",
                "gender": "Female",
                "speed": "Normal x1",
            },
        },
        "items": [
            {
                "text": "What did you do last weekend?",
                "translation": "你上週末做了什麼？",
                "scenario_dialogue": {
                    "tense_override": None,
                    "voice_override": None,
                    "keywords": ["went", "visited"],
                    "reference_answer": "I went to the park with my family.",
                    "rubric_note": "說出兩個活動",
                    "image_prompt": "a family walking in a park",
                },
            },
            {
                "text": "What will you do next weekend?",
                "translation": "你下週末要做什麼？",
                "scenario_dialogue": {
                    "tense_override": {"time": "future", "aspect": "simple"},
                    "voice_override": "passive",
                    "keywords": [],
                    "reference_answer": "I will visit my grandma.",
                    "rubric_note": "",
                    "image_prompt": "",
                },
            },
            {
                "text": "Tell me anything about your weekend.",
                "translation": "隨便說說你的週末。",
                "scenario_dialogue": {
                    "tense_override": {"time": "", "aspect": ""},
                    "voice_override": "",
                    "keywords": [],
                    "reference_answer": "",
                    "rubric_note": "",
                    "image_prompt": "",
                },
            },
        ],
    }
    payload.update(overrides)
    return payload


def _create(test_client: TestClient, auth_token, **overrides):
    return test_client.post(
        "/api/teachers/lessons/1/contents",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=_payload(**overrides),
    )


class TestScenarioDialogueAPI:
    def test_create_and_read_round_trip(self, test_client: TestClient, auth_token):
        created = _create(test_client, auth_token)
        assert created.status_code == 200, created.text
        content_id = created.json()["id"]
        assert created.json()["type"] == "SCENARIO_DIALOGUE"
        assert created.json()["scenario_settings"]["question_level"] == "B1"

        detail = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert detail.status_code == 200, detail.text
        data = detail.json()

        settings = data["scenario_settings"]
        assert settings["scenario_content"] == "It is Monday morning at school."
        assert settings["global_tense"] == {"time": "past", "aspect": "simple"}
        assert settings["global_voice"] == "active"
        assert settings["tts_settings"]["gender"] == "Female"

        items = sorted(data["items"], key=lambda i: i["order_index"])
        assert len(items) == 3

        # 第 1 題：沿用整體 → 必須還是 null，不能被寫成當下的 past/simple
        assert items[0]["scenario_dialogue"]["tense_override"] is None
        assert items[0]["scenario_dialogue"]["voice_override"] is None
        assert items[0]["scenario_dialogue"]["keywords"] == ["went", "visited"]
        assert (
            items[0]["scenario_dialogue"]["reference_answer"]
            == "I went to the park with my family."
        )

        # 第 2 題：自訂
        assert items[1]["scenario_dialogue"]["tense_override"] == {
            "time": "future",
            "aspect": "simple",
        }
        assert items[1]["scenario_dialogue"]["voice_override"] == "passive"

        # 第 3 題：明確不指定 → 不能被折疊成 null（否則會變成「沿用整體」）
        assert items[2]["scenario_dialogue"]["tense_override"] == {
            "time": "",
            "aspect": "",
        }
        assert items[2]["scenario_dialogue"]["voice_override"] == ""

    def test_changing_global_moves_inheriting_rows_only(
        self, test_client: TestClient, auth_token
    ):
        """改整體之後：沿用的題目跟著變，脫鉤的題目不動 —— null 語意的實際後果。"""
        content_id = _create(test_client, auth_token).json()["id"]
        detail = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        items = sorted(detail["items"], key=lambda i: i["order_index"])

        updated = test_client.put(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "scenario_settings": {
                    **detail["scenario_settings"],
                    "global_tense": {"time": "present", "aspect": "perfect"},
                    "global_voice": "passive",
                },
                "items": [
                    {
                        "id": item["id"],
                        "text": item["text"],
                        "translation": item["translation"],
                        "scenario_dialogue": item["scenario_dialogue"],
                    }
                    for item in items
                ],
            },
        )
        assert updated.status_code == 200, updated.text

        after = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        after_items = sorted(after["items"], key=lambda i: i["order_index"])
        settings = after["scenario_settings"]

        blocks = [i["scenario_dialogue"] for i in after_items]
        # 沿用的題目：生效值跟著整體走
        assert sd.resolve_effective_tense(blocks[0], settings) == {
            "time": "present",
            "aspect": "perfect",
        }
        assert sd.resolve_effective_voice(blocks[0], settings) == "passive"
        # 自訂的題目：不受整體影響
        assert sd.resolve_effective_tense(blocks[1], settings) == {
            "time": "future",
            "aspect": "simple",
        }
        # 明確不指定的題目：也不受整體影響（若被壓成 null 這裡會變成 present/perfect）
        assert sd.resolve_effective_tense(blocks[2], settings) == {
            "time": "",
            "aspect": "",
        }
        assert sd.resolve_effective_voice(blocks[2], settings) == ""

    def test_update_without_scenario_block_keeps_existing(
        self, test_client: TestClient, auth_token
    ):
        """只改音檔（沒帶 scenario_dialogue）不可以把參考答案洗掉。"""
        content_id = _create(test_client, auth_token).json()["id"]
        detail = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        items = sorted(detail["items"], key=lambda i: i["order_index"])

        resp = test_client.put(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "items": [
                    {"id": i["id"], "text": i["text"], "audio_url": "https://a/x.mp3"}
                    for i in items
                ]
            },
        )
        assert resp.status_code == 200, resp.text

        after = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        after_items = sorted(after["items"], key=lambda i: i["order_index"])
        assert (
            after_items[0]["scenario_dialogue"]["reference_answer"]
            == "I went to the park with my family."
        )
        assert after_items[0]["scenario_dialogue"]["tense_override"] is None
        # 整份設定沒帶也不能被清空
        assert after["scenario_settings"]["global_voice"] == "active"

    @pytest.mark.parametrize("count", [2, 11])
    def test_item_count_enforced_on_create(
        self, test_client: TestClient, auth_token, count
    ):
        items = [{"text": f"Q{i}"} for i in range(count)]
        resp = _create(test_client, auth_token, items=items)
        assert resp.status_code == 400

    @pytest.mark.parametrize("count", [2, 11])
    def test_item_count_enforced_on_update(
        self, test_client: TestClient, auth_token, count
    ):
        """題數上下限在 update 路徑同樣要擋（PR #1016 review 指出的覆蓋缺口）。

        只擋新增的話，老師建好 5 題再刪到剩 1 題就繞過了 #864 的下限。
        """
        content_id = _create(test_client, auth_token).json()["id"]

        resp = test_client.put(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "title": "改題數",
                "items": [{"text": f"Q{i}"} for i in range(count)],
            },
        )
        assert resp.status_code == 400

        # 擋下之後既有題目要原封不動
        detail = test_client.get(
            f"/api/teachers/contents/{content_id}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        assert len(detail["items"]) == 3

    def test_rejects_chinese_tense_label(self, test_client: TestClient, auth_token):
        """介面語言不該影響存進去的值；中文標籤代表前端串錯，直接擋下。"""
        payload = _payload()
        payload["scenario_settings"]["global_tense"] = {
            "time": "過去",
            "aspect": "simple",
        }
        resp = test_client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payload,
        )
        assert resp.status_code == 400

    def test_invalid_item_override_leaves_no_orphan_content(
        self, test_client: TestClient, auth_token, db_session
    ):
        """逐題代碼不合法要在建立 Content **之前**擋下（PR #1016 review）。

        單題驗證若跑在 Content 已 commit 之後，一筆壞資料會留下一張 0 題的空內容卡：
        老師看到 400 以為沒存成功，教材列表卻多一張卡，重試幾次就累積幾張，只能手動刪。
        """
        from models import Content

        before = db_session.query(Content).count()

        payload = _payload()
        payload["items"][0]["scenario_dialogue"]["tense_override"] = {
            "time": "過去",  # 中文標籤 = 前端串錯，不是穩定代碼
            "aspect": "simple",
        }
        resp = test_client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payload,
        )

        assert resp.status_code == 400
        db_session.expire_all()
        assert (
            db_session.query(Content).count() == before
        ), "驗證失敗卻留下了 Content 列 —— 逐題驗證必須跑在 db.commit() 之前"

    def test_invalid_item_voice_override_rejected(
        self, test_client: TestClient, auth_token
    ):
        """語態同樣只認穩定代碼（active / passive）。"""
        payload = _payload()
        payload["items"][1]["scenario_dialogue"]["voice_override"] = "被動"
        resp = test_client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=payload,
        )
        assert resp.status_code == 400

    def test_other_content_types_untouched(self, test_client: TestClient, auth_token):
        """非情境對話：不寫 scenario_settings，也不因為多了欄位而改變行為。"""
        resp = test_client.post(
            "/api/teachers/lessons/1/contents",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "type": "EXAMPLE_SENTENCES",
                "title": "普通例句集",
                "items": [{"text": "Hello", "translation": "你好"}],
            },
        )
        assert resp.status_code == 200
        assert resp.json()["scenario_settings"] is None
        detail = test_client.get(
            f"/api/teachers/contents/{resp.json()['id']}",
            headers={"Authorization": f"Bearer {auth_token}"},
        ).json()
        assert detail["scenario_settings"] is None
        assert detail["items"][0]["scenario_dialogue"] is None
