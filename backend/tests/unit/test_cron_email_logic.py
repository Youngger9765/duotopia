"""
Unit Tests: Cron Job Email Logic

測試 cron job 發信邏輯（不依賴外部服務）
"""

import pytest


class TestEmailSendingLogic:
    """測試錄音錯誤報告的發信邏輯"""

    @pytest.mark.parametrize(
        "hour,errors_1h,should_send,is_scheduled,description",
        [
            # 固定報告時間 - 無論有無錯誤都要發信
            (0, 0, True, True, "00:00 無錯誤應發信（定期報告）"),
            (6, 0, True, True, "06:00 無錯誤應發信（定期報告）"),
            (12, 0, True, True, "12:00 無錯誤應發信（定期報告）"),
            (18, 0, True, True, "18:00 無錯誤應發信（定期報告）"),
            (0, 5, True, True, "00:00 有錯誤應發信（定期報告）"),
            (6, 10, True, True, "06:00 有錯誤應發信（定期報告）"),
            # 非固定時間 - 只有錯誤時才發信
            (1, 0, False, False, "01:00 無錯誤不發信"),
            (3, 0, False, False, "03:00 無錯誤不發信"),
            (9, 0, False, False, "09:00 無錯誤不發信"),
            (15, 0, False, False, "15:00 無錯誤不發信"),
            (21, 0, False, False, "21:00 無錯誤不發信"),
            (1, 5, True, False, "01:00 有錯誤應發信"),
            (9, 3, True, False, "09:00 有錯誤應發信"),
            (15, 1, True, False, "15:00 有錯誤應發信"),
            (23, 20, True, False, "23:00 有錯誤應發信"),
        ],
    )
    def test_should_send_email(
        self, hour, errors_1h, should_send, is_scheduled, description
    ):
        """測試發信邏輯的核心判斷"""
        # 模擬 cron.py 的邏輯
        current_hour = hour
        total_errors_1h = errors_1h

        # 核心邏輯
        is_scheduled_report = current_hour in [0, 6, 12, 18]
        should_send_email = is_scheduled_report or total_errors_1h > 0

        # 驗證
        assert should_send_email == should_send, description
        assert is_scheduled_report == is_scheduled

    def test_email_subject_scheduled_report(self):
        """測試定期報告的主旨格式"""
        # 模擬定期報告（12:00，無錯誤）
        total_errors_1h = 0
        total_errors_24h = 29
        is_scheduled_report = True

        subject_emoji = (
            "🚨" if total_errors_1h > 10 else "⚠️" if total_errors_1h > 0 else "✅"
        )
        report_type = " [定期報告]" if is_scheduled_report else ""
        subject = (
            f"{subject_emoji} 錄音錯誤報告{report_type} - "
            f"10/22 12:00 "
            f"(1H: {total_errors_1h} | 24H: {total_errors_24h})"
        )

        assert "✅" in subject
        assert "[定期報告]" in subject
        assert "(1H: 0 | 24H: 29)" in subject

    def test_email_subject_error_report(self):
        """測試錯誤報告的主旨格式"""
        # 模擬錯誤報告（15:00，有錯誤）
        total_errors_1h = 5
        total_errors_24h = 29
        is_scheduled_report = False

        subject_emoji = (
            "🚨" if total_errors_1h > 10 else "⚠️" if total_errors_1h > 0 else "✅"
        )
        report_type = " [定期報告]" if is_scheduled_report else ""
        subject = (
            f"{subject_emoji} 錄音錯誤報告{report_type} - "
            f"10/22 15:00 "
            f"(1H: {total_errors_1h} | 24H: {total_errors_24h})"
        )

        assert "⚠️" in subject
        assert "[定期報告]" not in subject
        assert "(1H: 5 | 24H: 29)" in subject

    def test_email_subject_critical_error(self):
        """測試嚴重錯誤的主旨格式"""
        # 模擬嚴重錯誤（15:00，錯誤超過10次）
        total_errors_1h = 15
        total_errors_24h = 50
        is_scheduled_report = False

        subject_emoji = (
            "🚨" if total_errors_1h > 10 else "⚠️" if total_errors_1h > 0 else "✅"
        )
        report_type = " [定期報告]" if is_scheduled_report else ""
        subject = (
            f"{subject_emoji} 錄音錯誤報告{report_type} - "
            f"10/22 15:00 "
            f"(1H: {total_errors_1h} | 24H: {total_errors_24h})"
        )

        assert "🚨" in subject
        assert "[定期報告]" not in subject
        assert "(1H: 15 | 24H: 50)" in subject
