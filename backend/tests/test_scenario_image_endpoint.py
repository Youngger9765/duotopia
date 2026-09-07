"""情境對話 AI 生圖端點與配額 — Issue #1024。

Imagen 與儲存全程 mock。這裡驗的是端點的產品決策：什麼時候扣額度、什麼時候不扣、
被安全過濾擋下要回什麼、額度用完要回什麼。
"""

import pytest

from services import scenario_image_quota as siq
from services.scenario_dialogue_image import (
    ScenarioImageBlockedError,
    ScenarioImageError,
)

IMAGE_URL = "/api/teachers/scenario-dialogue/generate-image"
QUOTA_URL = "/api/teachers/scenario-dialogue/image-quota"


@pytest.fixture
def mock_image(monkeypatch):
    """生圖成功 + 存檔成功。"""
    calls = {"generate": 0, "store": 0}

    async def fake_generate(self, raw_prompt):
        calls["generate"] += 1
        calls["prompt"] = raw_prompt
        return {
            "image_bytes": b"PNGDATA",
            "prompt": f"rewritten: {raw_prompt}",
            "estimated_cost_usd": 0.04,
        }

    def fake_store(self, content, content_type, **kwargs):
        calls["store"] += 1
        return "https://cdn.example.com/img.png"

    from services import scenario_dialogue_image as mod
    from services import image_upload as upload_mod

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", fake_generate)
    monkeypatch.setattr(upload_mod.ImageUploadService, "store_image_bytes", fake_store)
    return calls


# ---------------------------------------------------------------- 鑑權


def test_generate_image_requires_auth(test_client):
    resp = test_client.post(IMAGE_URL, json={"image_prompt": "a park"})
    assert resp.status_code in (401, 403)


def test_quota_requires_auth(test_client):
    assert test_client.get(QUOTA_URL).status_code in (401, 403)


# ---------------------------------------------------------------- 正常流程


def test_generate_image_returns_url_and_charges_once(
    test_client, auth_headers_teacher, mock_image
):
    resp = test_client.post(
        IMAGE_URL,
        headers=auth_headers_teacher,
        json={"image_prompt": "students talking in a classroom"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["image_url"] == "https://cdn.example.com/img.png"
    assert body["quota"]["charged"] == "free"
    assert body["quota"]["used"] == 1
    assert mock_image["generate"] == 1
    assert mock_image["store"] == 1


def test_quota_endpoint_reflects_usage(test_client, auth_headers_teacher, mock_image):
    before = test_client.get(QUOTA_URL, headers=auth_headers_teacher).json()
    assert before["used"] == 0
    assert before["limit"] == siq.FREE_MONTHLY_LIMIT

    test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )

    after = test_client.get(QUOTA_URL, headers=auth_headers_teacher).json()
    assert after["used"] == 1
    assert after["remaining"] == siq.FREE_MONTHLY_LIMIT - 1


# ---------------------------------------------------------------- 不扣額度的情況


def test_blocked_by_safety_filter_returns_422_and_does_not_charge(
    test_client, auth_headers_teacher, monkeypatch
):
    """被安全過濾擋下 → 老師沒拿到圖，不能扣他一次（比照 magic_paste 擷取到 0 項不扣）。"""
    from services import scenario_dialogue_image as mod

    async def blocked(self, raw_prompt):
        raise ScenarioImageBlockedError("AI 沒有產出圖片，請換個描述再試")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", blocked)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert resp.status_code == 422
    assert "換個描述" in resp.json()["detail"]

    quota = test_client.get(QUOTA_URL, headers=auth_headers_teacher).json()
    assert quota["used"] == 0


def test_storage_failure_does_not_charge(
    test_client, auth_headers_teacher, monkeypatch
):
    """圖生出來卻存不進去 —— 老師一樣沒拿到圖，重試不該被罰。"""
    from services import scenario_dialogue_image as mod
    from services import image_upload as upload_mod

    async def ok(self, raw_prompt):
        return {
            "image_bytes": b"PNGDATA",
            "prompt": "p",
            "estimated_cost_usd": 0.04,
        }

    def boom(self, content, content_type, **kwargs):
        raise RuntimeError("GCS down")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", ok)
    monkeypatch.setattr(upload_mod.ImageUploadService, "store_image_bytes", boom)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert resp.status_code == 502

    quota = test_client.get(QUOTA_URL, headers=auth_headers_teacher).json()
    assert quota["used"] == 0


def test_invalid_prompt_returns_400(test_client, auth_headers_teacher, monkeypatch):
    from services import scenario_dialogue_image as mod

    async def bad(self, raw_prompt):
        raise ScenarioImageError("生圖描述不可為空")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", bad)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "  "}
    )
    assert resp.status_code == 400


def test_prompt_too_long_is_rejected_before_calling_ai(
    test_client, auth_headers_teacher, mock_image
):
    resp = test_client.post(
        IMAGE_URL,
        headers=auth_headers_teacher,
        json={"image_prompt": "x" * 5000},
    )
    assert resp.status_code == 422
    assert mock_image["generate"] == 0


# ---------------------------------------------------------------- 額度用完


def test_quota_exhausted_returns_402_without_calling_ai(
    test_client, auth_headers_teacher, mock_image, monkeypatch
):
    """額度用完就不要浪費一次 Imagen 呼叫。"""
    monkeypatch.setattr(siq, "FREE_MONTHLY_LIMIT", 1)

    first = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert first.status_code == 200
    assert mock_image["generate"] == 1

    second = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert second.status_code == 402
    assert second.json()["detail"]["error"] == "SCENARIO_IMAGE_QUOTA_EXCEEDED"
    # 沒有再打一次 AI
    assert mock_image["generate"] == 1


# ---------------------------------------------------------------- 配額服務本身


def test_quota_counts_per_month(test_client, auth_headers_teacher, db_session):
    """跨月自然重置：不同 year_month 各自計數。"""
    from models import Teacher

    teacher = db_session.query(Teacher).first()

    siq.consume(db_session, teacher, year_month="2026-01")
    siq.consume(db_session, teacher, year_month="2026-01")
    siq.consume(db_session, teacher, year_month="2026-02")

    jan = siq.get_quota_status(db_session, teacher, year_month="2026-01")
    feb = siq.get_quota_status(db_session, teacher, year_month="2026-02")
    assert jan["used"] == 2
    assert feb["used"] == 1


def test_quota_consume_stops_at_limit(
    test_client, auth_headers_teacher, db_session, monkeypatch
):
    """就算呼叫端漏檢查，consume 自己也不會讓計數超過上限。"""
    from models import Teacher

    monkeypatch.setattr(siq, "FREE_MONTHLY_LIMIT", 2)
    teacher = db_session.query(Teacher).first()

    siq.consume(db_session, teacher, year_month="2026-03")
    siq.consume(db_session, teacher, year_month="2026-03")
    third = siq.consume(db_session, teacher, year_month="2026-03")

    assert third["charged"] is None
    assert third["used"] == 2
    assert siq.get_quota_status(db_session, teacher, year_month="2026-03")["used"] == 2
