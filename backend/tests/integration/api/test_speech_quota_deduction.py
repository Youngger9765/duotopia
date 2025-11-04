"""
語音評分配額扣除測試 (TDD)

測試流程：
1. 學生上傳錄音並評分
2. 系統計算錄音時長
3. 扣除老師的配額
4. 記錄 PointUsageLog
5. 配額不足時阻止評分
"""

import pytest
from fastapi.testclient import TestClient
from database import SessionLocal
from models import Teacher
from main import app

client = TestClient(app)


@pytest.fixture
def setup_teacher_with_quota():
    """準備有配額的老師"""
    db = SessionLocal()

    # 使用測試帳號
    teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    assert teacher is not None

    # 確保有有效訂閱週期
    period = teacher.current_period
    if period:
        # 重置配額為 1800 秒
        period.quota_used = 0
        period.quota_total = 1800
        db.commit()

    yield teacher

    db.close()


def test_speech_assessment_deducts_quota(setup_teacher_with_quota):
    """
    測試 1: 語音評分成功扣除配額

    流程：
    1. 學生上傳 30 秒錄音
    2. AI 評分成功
    3. 存入 DB (db.commit)
    4. ✅ 扣除老師 30 秒配額
    5. ✅ 記錄 PointUsageLog
    """
    db = SessionLocal()
    teacher = setup_teacher_with_quota

    # 檢查初始配額
    period = teacher.current_period
    initial_quota_used = period.quota_used
    assert initial_quota_used == 0

    # TODO: 模擬學生上傳錄音並評分
    # 這裡需要實際的 API call
    # audio_file = create_mock_audio(duration=30)
    # response = client.post("/assess", files={"audio": audio_file}, data={"reference_text": "hello"})

    # 預期結果：
    # - period.quota_used = 30
    # - PointUsageLog 有新記錄

    db.close()
    pytest.skip("等待實作 API integration")


def test_speech_assessment_quota_exceeded():
    """
    測試 2: 配額不足時阻止評分

    流程：
    1. 老師配額剩餘 10 秒
    2. 學生上傳 30 秒錄音
    3. ✅ 返回 402 錯誤
    4. ✅ 不扣除配額
    5. ✅ 不記錄 PointUsageLog
    """
    db = SessionLocal()

    teacher = db.query(Teacher).filter_by(email="demo@duotopia.com").first()
    period = teacher.current_period

    if period:
        # 設定配額幾乎用完
        period.quota_used = 1790  # 只剩 10 秒
        db.commit()

    # TODO: 模擬學生上傳 30 秒錄音
    # 預期返回 402 錯誤

    db.close()
    pytest.skip("等待實作 API integration")


def test_quota_log_records_student_usage():
    """
    測試 3: PointUsageLog 記錄學生使用資訊

    驗證：
    - teacher_id 正確
    - student_id 正確
    - assignment_id 正確
    - feature_type = "speech_assessment"
    - unit_count = 30 (秒)
    - unit_type = "秒"
    - points_used = 30
    """
    db = SessionLocal()

    # TODO: 執行評分後
    # 查詢最新的 PointUsageLog
    # latest_log = db.query(PointUsageLog).order_by(PointUsageLog.id.desc()).first()
    # assert latest_log.teacher_id == teacher.id
    # assert latest_log.student_id == student.id
    # assert latest_log.feature_type == "speech_assessment"

    db.close()
    pytest.skip("等待實作")


def test_multiple_assessments_accumulate_quota():
    """
    測試 4: 多次評分累積扣除配額

    流程：
    1. 學生評分 30 秒 → quota_used = 30
    2. 學生再評分 40 秒 → quota_used = 70
    3. 學生再評分 20 秒 → quota_used = 90
    """
    db = SessionLocal()

    # TODO: 實作多次評分測試

    db.close()
    pytest.skip("等待實作")


def test_teacher_own_test_also_deducts_quota():
    """
    測試 5: 老師自己測試錄音也扣配額

    如果老師自己測試功能，也應該扣配額
    """
    pytest.skip("待確認需求：老師自己測試是否扣配額？")


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 語音評分配額扣除測試 (TDD)")
    print("=" * 70)
    pytest.main([__file__, "-v"])
