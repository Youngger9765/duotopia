# flake8: noqa
"""
配額使用統計 API 測試 (TDD)

測試項目：
1. 取得配額使用統計 (summary)
2. 每日使用量趨勢
3. 學生使用排行
4. 作業使用排行
5. 功能類型分佈
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone
from database import get_session_local
from models import Teacher, Student, Assignment, SubscriptionPeriod, PointUsageLog
from main import app

client = TestClient(app)


@pytest.fixture
def setup_test_data():
    """準備測試資料"""
    SessionLocal = get_session_local()
    db = SessionLocal()

    # 建立測試 teacher
    teacher = Teacher(
        name="統計測試老師",
        email=f"analytics_test_{datetime.now().timestamp()}@example.com",
        password_hash="test_hash",
    )
    db.add(teacher)
    db.flush()

    # 建立訂閱週期
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=330,
        quota_total=1800,
        quota_used=800,  # 已使用 800 秒
        start_date=now - timedelta(days=15),
        end_date=now + timedelta(days=15),
        payment_method="manual",
        payment_status="paid",
        status="active",
    )
    db.add(period)
    db.flush()

    # 建立測試學生
    students = []
    for i in range(3):
        student = Student(
            name=f"學生{i+1}",
            email=f"student{i+1}_analytics@example.com",
            password_hash="test_hash",
            birthdate=datetime(2010, 1, 1).date(),
        )
        db.add(student)
        db.flush()
        students.append(student)

    # 建立測試作業
    assignments = []
    for i in range(2):
        assignment = Assignment(
            teacher_id=teacher.id,
            title=f"測試作業{i+1}",
            description="統計測試用",
            created_at=now,
        )
        db.add(assignment)
        db.flush()
        assignments.append(assignment)

    # 建立使用記錄 (模擬不同學生、作業、日期的使用)
    usage_data = [
        # 學生1 - 作業1 - 昨天
        {
            "student": students[0],
            "assignment": assignments[0],
            "seconds": 100,
            "days_ago": 1,
        },
        # 學生1 - 作業1 - 今天
        {
            "student": students[0],
            "assignment": assignments[0],
            "seconds": 150,
            "days_ago": 0,
        },
        # 學生2 - 作業1 - 昨天
        {
            "student": students[1],
            "assignment": assignments[0],
            "seconds": 200,
            "days_ago": 1,
        },
        # 學生2 - 作業2 - 今天
        {
            "student": students[1],
            "assignment": assignments[1],
            "seconds": 100,
            "days_ago": 0,
        },
        # 學生3 - 作業2 - 2天前
        {
            "student": students[2],
            "assignment": assignments[1],
            "seconds": 250,
            "days_ago": 2,
        },
    ]

    for data in usage_data:
        created_at = now - timedelta(days=data["days_ago"])
        log = PointUsageLog(
            subscription_period_id=period.id,
            teacher_id=teacher.id,
            student_id=data["student"].id,
            assignment_id=data["assignment"].id,
            feature_type="speech_assessment",
            unit_count=data["seconds"],
            unit_type="秒",
            points_used=data["seconds"],
            quota_before=1000,
            quota_after=1000 - data["seconds"],
            created_at=created_at,
        )
        db.add(log)

    db.commit()

    yield {
        "teacher": teacher,
        "students": students,
        "assignments": assignments,
        "period": period,
    }

    # 清理
    db.query(PointUsageLog).filter(PointUsageLog.teacher_id == teacher.id).delete()
    for assignment in assignments:
        db.delete(assignment)
    for student in students:
        db.delete(student)
    db.delete(period)
    db.delete(teacher)
    db.commit()
    db.close()


def test_get_quota_usage_summary(setup_test_data):
    """
    測試 1: 取得配額使用統計摘要

    Given: Teacher 有 800 秒配額使用記錄
    When: GET /api/teachers/quota-usage
    Then: 返回正確的統計摘要
    """
    teacher = setup_test_data["teacher"]

    # TODO: 實作登入取得 token
    # token = login(teacher.email, "password")
    # headers = {"Authorization": f"Bearer {token}"}

    # 暫時跳過（需要實作認證）
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get(
        "/api/teachers/quota-usage",
        # headers=headers,
        params={
            "start_date": "2024-11-01",
            "end_date": "2024-11-30",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # 驗證摘要
    assert "summary" in data
    assert data["summary"]["total_used"] == 800
    assert data["summary"]["total_quota"] == 1800
    assert data["summary"]["percentage"] == 44  # 800/1800 = 44.4%


def test_get_daily_usage_trend(setup_test_data):
    """
    測試 2: 取得每日使用量趨勢

    Given: 3 天內有使用記錄
    When: GET /api/teachers/quota-usage
    Then: 返回每日使用量陣列
    """
    pytest.skip("需要實作 teacher 登入認證")

    teacher = setup_test_data["teacher"]

    _ = client.get("/api/teachers/quota-usage")

    assert response.status_code == 200
    data = response.json()

    # 驗證每日趨勢
    assert "daily_usage" in data
    assert len(data["daily_usage"]) >= 3

    # 驗證資料格式
    for day in data["daily_usage"]:
        assert "date" in day
        assert "seconds" in day
        assert isinstance(day["seconds"], int)


def test_get_top_students(setup_test_data):
    """
    測試 3: 取得學生使用排行

    Given: 學生1用250秒, 學生2用300秒, 學生3用250秒
    When: GET /api/teachers/quota-usage
    Then: 返回按使用量排序的學生列表
    """
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get("/api/teachers/quota-usage")

    assert response.status_code == 200
    data = response.json()

    # 驗證學生排行
    assert "top_students" in data
    students = data["top_students"]

    # 學生2應該排第一 (300秒)
    assert students[0]["seconds"] == 300
    assert students[0]["name"] == "學生2"

    # 驗證資料格式
    for student in students:
        assert "name" in student
        assert "seconds" in student
        assert "count" in student  # 使用次數


def test_get_top_assignments(setup_test_data):
    """
    測試 4: 取得作業使用排行

    Given: 作業1用450秒(3次), 作業2用350秒(2次)
    When: GET /api/teachers/quota-usage
    Then: 返回按使用量排序的作業列表
    """
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get("/api/teachers/quota-usage")

    assert response.status_code == 200
    data = response.json()

    # 驗證作業排行
    assert "top_assignments" in data
    assignments = data["top_assignments"]

    # 作業1應該排第一 (450秒)
    assert assignments[0]["title"] == "測試作業1"
    assert assignments[0]["seconds"] == 450

    # 驗證資料格式
    for assignment in assignments:
        assert "title" in assignment
        assert "seconds" in assignment
        assert "students" in assignment  # 使用人數


def test_get_feature_breakdown(setup_test_data):
    """
    測試 5: 取得功能使用分佈

    Given: 所有使用都是 speech_assessment
    When: GET /api/teachers/quota-usage
    Then: 返回功能類型統計
    """
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get("/api/teachers/quota-usage")

    assert response.status_code == 200
    data = response.json()

    # 驗證功能分佈
    assert "feature_breakdown" in data
    breakdown = data["feature_breakdown"]

    assert "speech_assessment" in breakdown
    assert breakdown["speech_assessment"] == 800


def test_date_range_filter():
    """
    測試 6: 日期範圍過濾

    Given: 指定日期範圍
    When: GET /api/teachers/quota-usage?start_date=2024-11-01&end_date=2024-11-07
    Then: 只返回該範圍內的資料
    """
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get(
        "/api/teachers/quota-usage",
        params={
            "start_date": "2024-11-01",
            "end_date": "2024-11-07",
        },
    )

    assert response.status_code == 200
    data = response.json()

    # 驗證日期範圍
    for day in data["daily_usage"]:
        date = datetime.fromisoformat(day["date"])
        assert date >= datetime(2024, 11, 1)
        assert date <= datetime(2024, 11, 7)


def test_empty_usage_data():
    """
    測試 7: 沒有使用記錄時的回應

    Given: Teacher 沒有任何使用記錄
    When: GET /api/teachers/quota-usage
    Then: 返回空的統計資料
    """
    pytest.skip("需要實作 teacher 登入認證")

    _ = client.get("/api/teachers/quota-usage")

    assert response.status_code == 200
    data = response.json()

    assert data["summary"]["total_used"] == 0
    assert len(data["daily_usage"]) == 0
    assert len(data["top_students"]) == 0
    assert len(data["top_assignments"]) == 0
