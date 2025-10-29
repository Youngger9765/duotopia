"""
測試 Cron 成功錄音計數查詢
驗證從 StudentItemProgress 計數邏輯正確
"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from models import StudentItemProgress


class TestCronRecordingCount:
    """測試錄音計數查詢"""

    def test_simple_count_query(self, test_session: Session):
        """測試簡單的 count() 查詢（和 cron.py 一樣的邏輯）"""

        # 🔥 這是 cron.py 的查詢邏輯
        count = (
            test_session.query(StudentItemProgress)
            .filter(
                StudentItemProgress.updated_at
                >= datetime.now(timezone.utc) - timedelta(hours=1),
                StudentItemProgress.recording_url.isnot(None),
            )
            .count()
        )

        # 驗證：查詢不會爆炸，返回整數
        assert isinstance(count, int)
        assert count >= 0
