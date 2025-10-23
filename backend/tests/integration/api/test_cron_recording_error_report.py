"""
Integration Tests: Cron Job Recording Error Report API

測試 cron endpoint 的安全性
"""


class TestRecordingErrorReportSecurity:
    """測試錄音錯誤報告的安全性"""

    def test_unauthorized_without_secret(self, test_client):
        """測試沒有 Secret 時拒絕存取"""
        response = test_client.post("/api/cron/recording-error-report")

        assert response.status_code == 401

    def test_unauthorized_with_wrong_secret(self, test_client):
        """測試錯誤的 Secret 時拒絕存取"""
        response = test_client.post(
            "/api/cron/recording-error-report",
            headers={"X-Cron-Secret": "wrong-secret"},
        )

        assert response.status_code == 401
