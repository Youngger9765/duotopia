"""Rate Limiter 單元測試 - 測試 get_user_identifier"""
from core.limiter import get_user_identifier


class MockRequest:
    """模擬 FastAPI Request"""

    def __init__(self, body=None, client_ip="127.0.0.1"):
        self._json = body
        self.client = type("Client", (), {"host": client_ip})()


def test_get_user_identifier_by_email():
    """測試：優先使用 email 作為識別"""
    request = MockRequest(body={"email": "teacher@school.com", "password": "xxx"})
    result = get_user_identifier(request)
    assert result == "email:teacher@school.com"


def test_get_user_identifier_by_student_id():
    """測試：使用 student id 作為識別"""
    request = MockRequest(body={"id": "S12345", "password": "xxx"})
    result = get_user_identifier(request)
    assert result == "student:S12345"


def test_get_user_identifier_fallback_to_ip():
    """測試：無法取得 email/id 時，fallback 到 IP"""
    request = MockRequest(body={"some_field": "value"}, client_ip="203.123.45.67")
    result = get_user_identifier(request)
    assert "203.123.45.67" in result or result.startswith("ip:")


def test_get_user_identifier_email_takes_priority():
    """測試：email 優先於其他欄位"""
    request = MockRequest(body={"email": "t@s.com", "id": "S12345"})
    result = get_user_identifier(request)
    assert result == "email:t@s.com"
