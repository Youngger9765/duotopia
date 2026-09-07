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


def test_blank_prompt_is_rejected_before_touching_quota(
    test_client, auth_headers_teacher, mock_image, db_session
):
    """純空白描述要在 Pydantic 就擋掉（422），不該走完「扣額度 → 失敗 → 退款」。

    只寫 min_length=1 是不夠的：" " 長度是 1，照樣會通過（PR #1027 review round 4），
    所以欄位要搭配 strip_whitespace。
    """
    from models import Teacher

    teacher = db_session.query(Teacher).first()

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "   "}
    )
    assert resp.status_code == 422
    # 連 AI 都沒打，更沒有動到額度
    assert mock_image["generate"] == 0
    assert siq.get_quota_status(db_session, teacher)["used"] == 0


def test_service_level_invalid_prompt_returns_400(
    test_client, auth_headers_teacher, monkeypatch
):
    """通過欄位驗證、但服務層仍判定不合法時回 400（與模型產不出東西的 502 分開）。"""
    from services import scenario_dialogue_image as mod

    async def bad(self, raw_prompt):
        raise ScenarioImageError("生圖描述不合法")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", bad)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
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


# ------------------------------------------------- 先佔位再生圖（PR #1027 review）
#
# 只在打 AI 之前查一次額度是擋不住並發的：同一位老師在上限邊界同時送兩個請求，
# 兩個都會通過那次檢查。改成「先 consume 佔位 → 打 AI → 失敗才 refund」。


def test_quota_is_reserved_before_calling_ai(
    test_client, auth_headers_teacher, db_session, monkeypatch
):
    """額度要在打 AI **之前**就被佔走，不是回應成功之後才扣。

    在 AI 執行的當下去查計數 —— 那一刻就該已經是 1，否則兩個並發請求都會在
    「還沒扣」的空窗期通過檢查。
    """
    from services import scenario_dialogue_image as mod
    from services import image_upload as upload_mod
    from models import Teacher

    teacher = db_session.query(Teacher).first()
    seen = {}

    async def check_quota_midflight(self, raw_prompt):
        seen["used_during_call"] = siq.get_quota_status(db_session, teacher)["used"]
        return {
            "image_bytes": b"PNGDATA",
            "prompt": "p",
            "estimated_cost_usd": 0.04,
        }

    monkeypatch.setattr(
        mod.ScenarioDialogueImageService, "generate", check_quota_midflight
    )
    monkeypatch.setattr(
        upload_mod.ImageUploadService,
        "store_image_bytes",
        lambda self, content, content_type, **kw: "https://cdn/x.png",
    )

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )

    assert resp.status_code == 200, resp.text
    assert seen["used_during_call"] == 1, "AI 執行期間額度還沒被佔走 = 並發擋不住"


def test_second_request_at_limit_gets_402_even_if_status_check_passed(
    test_client, auth_headers_teacher, mock_image, monkeypatch
):
    """consume 回 charged=None 時一定要回 402，不能照樣回 200 把圖給出去。

    這正是 review 抓到的漏洞：先前的寫法拿到 charged=None 也照樣回 200，
    月上限等於形同虛設。
    """
    monkeypatch.setattr(siq, "FREE_MONTHLY_LIMIT", 1)

    assert (
        test_client.post(
            IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
        ).status_code
        == 200
    )

    second = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert second.status_code == 402
    assert "image_url" not in second.json()


def test_refund_does_not_go_below_zero(test_client, auth_headers_teacher, db_session):
    """重複退款（例外路徑重入）只會回到 0，不會變負數。"""
    from models import Teacher

    teacher = db_session.query(Teacher).first()
    siq.refund(db_session, teacher, year_month="2026-04")
    siq.refund(db_session, teacher, year_month="2026-04")

    assert siq.get_quota_status(db_session, teacher, year_month="2026-04")["used"] == 0


def test_sdk_shape_change_is_not_reported_as_safety_block():
    """`_image_bytes` 消失（SDK 改版）不能被講成「你的描述有問題」。"""
    from services.scenario_dialogue_image import ScenarioDialogueImageService

    class NoBytes:
        pass  # 沒有 _image_bytes 屬性

    with pytest.raises(ScenarioImageError) as exc:
        ScenarioDialogueImageService.extract_image_bytes([NoBytes()])
    assert not isinstance(exc.value, ScenarioImageBlockedError)


# ------------------------------------------------- 中途取消也要退款（review round 2）


def test_cancelled_midflight_refunds_quota(
    test_client, auth_headers_teacher, db_session, monkeypatch
):
    """老師在 Imagen 跑到一半關掉分頁 → 那個名額要還回去。

    `asyncio.CancelledError` 是 **BaseException**，`except Exception` 接不到；
    退款寫在 finally 才涵蓋得到。網路不穩或冷啟動慢時，這會慢慢侵蝕老師的額度，
    而且他完全看不出原因。
    """
    import asyncio

    from models import Teacher
    from services import scenario_dialogue_image as mod

    teacher = db_session.query(Teacher).first()

    async def cancelled(self, raw_prompt):
        raise asyncio.CancelledError()

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", cancelled)

    # TestClient 會把中途取消包成別的例外（RuntimeError: No response returned.），
    # 實際型別不是重點 —— 這裡在意的是 finally 有沒有跑到、額度有沒有還回去
    try:
        test_client.post(
            IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
        )
    except BaseException:
        pass

    assert siq.get_quota_status(db_session, teacher)["used"] == 0


def test_generate_generic_failure_refunds_quota(
    test_client, auth_headers_teacher, db_session, monkeypatch
):
    """generate 丟一般例外（不是被擋、也不是參數錯）同樣要退款。"""
    from models import Teacher
    from services import scenario_dialogue_image as mod

    teacher = db_session.query(Teacher).first()

    async def boom(self, raw_prompt):
        raise RuntimeError("vertex exploded")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", boom)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert resp.status_code == 502
    assert siq.get_quota_status(db_session, teacher)["used"] == 0


def test_style_hint_survives_a_very_long_prompt():
    """原文接近上限時，風格提示不該被切掉半句。"""
    from services.scenario_dialogue_image import build_image_prompt

    prompt = build_image_prompt("a park " * 500)
    assert prompt.endswith("no text or letters in the image.")


def test_refund_targets_the_month_that_was_charged(
    test_client, auth_headers_teacher, db_session, monkeypatch
):
    """跨 UTC 午夜時，要退回「當初扣的那個月」而不是退到新的月份。

    Imagen 慢起來可能跨過月底：扣在 A 月、退到 B 月的話，A 月永遠少一格、B 月憑空
    多一格（PR #1027 review round 3）。這裡讓 consume 與 refund 之間「換月」來驗。
    """
    from models import Teacher
    from services import scenario_dialogue_image as mod

    teacher = db_session.query(Teacher).first()
    months = iter(["2026-01", "2026-02", "2026-02", "2026-02"])
    monkeypatch.setattr(siq, "current_year_month", lambda: next(months, "2026-02"))

    async def boom(self, raw_prompt):
        raise RuntimeError("slow call that straddles midnight")

    monkeypatch.setattr(mod.ScenarioDialogueImageService, "generate", boom)

    resp = test_client.post(
        IMAGE_URL, headers=auth_headers_teacher, json={"image_prompt": "a park"}
    )
    assert resp.status_code == 502

    # 扣在 1 月就要退回 1 月
    assert siq.get_quota_status(db_session, teacher, year_month="2026-01")["used"] == 0
    # 2 月不該憑空被動到
    assert siq.get_quota_status(db_session, teacher, year_month="2026-02")["used"] == 0
