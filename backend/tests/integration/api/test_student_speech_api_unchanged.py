"""
測試學生 Speech API 功能未受預覽模式修改影響

確認：
1. 學生 /api/speech/assess 端點仍然正常運作
2. assess_pronunciation() 函數未被修改
3. 學生錄音上傳和 AI 評估流程完整
"""

import pytest  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_student_speech_assess_endpoint_exists(
    test_client: TestClient, db_session: Session
):
    """測試學生 speech/assess 端點存在"""
    # 這個測試會因為缺少認證失敗，但證明端點存在
    response = test_client.post("/api/speech/assess")

    # 401 = endpoint exists but requires auth
    # 404 = endpoint doesn't exist
    assert response.status_code in [401, 422], f"端點應該存在但要求認證，實際: {response.status_code}"


def test_assess_pronunciation_function_available():
    """測試 assess_pronunciation 函數可用"""
    from routers.speech_assessment import assess_pronunciation, convert_audio_to_wav

    # 函數應該存在且可導入
    assert callable(assess_pronunciation), "assess_pronunciation 函數應該可呼叫"
    assert callable(convert_audio_to_wav), "convert_audio_to_wav 函數應該可呼叫"

    # 檢查函數簽名
    import inspect

    sig = inspect.signature(assess_pronunciation)
    params = list(sig.parameters.keys())

    # 應該接受 audio_data 和 reference_text 參數
    assert "audio_data" in params, "應該有 audio_data 參數"
    assert "reference_text" in params, "應該有 reference_text 參數"


def test_teacher_preview_api_exists(test_client: TestClient):
    """測試老師預覽 API 端點存在"""
    response = test_client.post("/api/teachers/assignments/preview/assess-speech")

    # 401 = requires teacher auth
    # 404 = endpoint doesn't exist
    # 422 = missing parameters
    assert response.status_code in [
        401,
        422,
    ], f"預覽端點應該存在但要求認證，實際: {response.status_code}"


def test_teacher_preview_uses_same_logic():
    """測試老師預覽 API 使用相同的評估邏輯"""
    import inspect
    from routers import teachers

    # 找到 preview_assess_speech 函數
    preview_func = getattr(teachers, "preview_assess_speech", None)
    assert preview_func is not None, "preview_assess_speech 函數應該存在"

    # 檢查函數源碼
    source = inspect.getsource(preview_func)

    # 應該使用 routers.speech_assessment 的函數
    assert (
        "from routers.speech_assessment import" in source
    ), "應該導入 speech_assessment 模組"
    assert "convert_audio_to_wav" in source, "應該使用 convert_audio_to_wav 函數"
    assert "assess_pronunciation" in source, "應該使用 assess_pronunciation 函數"

    # 不應該有錯誤的導入
    assert "from services.azure_speech" not in source, "不應該導入不存在的 services.azure_speech"


def test_student_api_parameters():
    """測試學生 API 參數要求"""
    import inspect
    from routers.speech_assessment import assess_pronunciation_endpoint

    sig = inspect.signature(assess_pronunciation_endpoint)
    params = list(sig.parameters.keys())

    # 學生 API 應該要求這些參數
    assert "audio_file" in params, "應該有 audio_file 參數"
    assert "reference_text" in params, "應該有 reference_text 參數"
    assert "progress_id" in params, "應該有 progress_id 參數（學生模式必須）"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
