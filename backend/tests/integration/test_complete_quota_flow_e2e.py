# flake8: noqa
"""
完整配額系統 E2E 測試
測試從訂閱 → 派作業 → 學生使用 → 配額扣除 → Log 記錄的完整流程

測試場景：
1. 老師訂閱並獲得配額
2. 老師派作業（檢查訂閱）
3. 學生提交錄音（扣除配額）
4. 驗證配額與 Log 同步
5. 配額超限仍允許使用
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from models import (
    Teacher,
    Student,
    SubscriptionPeriod,
    PointUsageLog,
    Classroom,
    ClassroomStudent,
    Assignment,
    StudentAssignment,
    Content,
    AssignmentContent,
    ContentItem,
)
from services.quota_service import QuotaService
from passlib.context import CryptContext


# ==================== Fixtures ====================


@pytest.fixture(scope="module")
def db():
    """建立測試資料庫連線"""
    load_dotenv()
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://duotopia_user:duotopia_pass@localhost:5432/duotopia",
    )
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def pwd_context():
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture
def test_teacher(db, pwd_context):
    """建立測試老師"""
    import random

    email = f"test_teacher_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}@example.com"

    teacher = Teacher(
        email=email,
        name="Complete Test Teacher",
        password_hash=pwd_context.hash("password123"),
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    yield teacher

    # Cleanup
    db.delete(teacher)
    db.commit()


@pytest.fixture
def test_student(db, pwd_context):
    """建立測試學生"""
    import random

    email = f"test_student_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}@example.com"

    student = Student(
        email=email,
        name="Complete Test Student",
        password_hash=pwd_context.hash("password123"),
        birthdate=date(2010, 1, 1),
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    yield student

    # Cleanup
    db.delete(student)
    db.commit()


@pytest.fixture
def test_classroom(db, test_teacher):
    """建立測試班級"""
    classroom = Classroom(
        teacher_id=test_teacher.id,
        name="Complete Test Classroom",
        description="E2E Test Classroom",
        level="A1",
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    yield classroom

    # Cleanup
    db.delete(classroom)
    db.commit()


@pytest.fixture
def enroll_student(db, test_classroom, test_student):
    """將學生加入班級"""
    enrollment = ClassroomStudent(
        classroom_id=test_classroom.id, student_id=test_student.id
    )
    db.add(enrollment)
    db.commit()

    yield enrollment

    # Cleanup
    db.delete(enrollment)
    db.commit()


# ==================== Tests ====================


def test_complete_quota_flow_e2e(
    db, test_teacher, test_student, test_classroom, enroll_student
):
    """
    完整流程測試：訂閱 → 派作業 → 學生使用 → 配額扣除

    測試步驟：
    1. 老師訂閱 Tutor Teachers（獲得 10000 點配額）
    2. 驗證老師可以派作業
    3. 老師派作業給學生
    4. 學生提交 3 次錄音（每次 30 秒）
    5. 驗證配額正確扣除
    6. 驗證 Log 記錄完整
    7. 驗證配額與 Log 同步
    """
    print("\n" + "=" * 70)
    print("🧪 Complete Quota Flow E2E Test")
    print("=" * 70)

    # ===== Step 1: 老師訂閱並獲得配額 =====
    print("\n📝 Step 1: 老師訂閱 Tutor Teachers")

    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=test_teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=Decimal("330"),
        quota_total=10000,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )
    db.add(period)

    # 更新老師訂閱狀態
    test_teacher.subscription_end_date = now + timedelta(days=30)
    test_teacher.subscription_type = "Tutor Teachers"
    db.commit()
    db.refresh(period)
    db.refresh(test_teacher)

    print(f"✅ Created SubscriptionPeriod ID: {period.id}")
    print(f"   Quota Total: {period.quota_total} seconds")
    print(f"   Quota Used: {period.quota_used} seconds")

    # 驗證
    assert test_teacher.current_period is not None
    assert test_teacher.current_period.id == period.id
    assert test_teacher.quota_total == 10000
    assert test_teacher.quota_remaining == 10000

    # ===== Step 2: 驗證老師可以派作業 =====
    print("\n📝 Step 2: 驗證老師可以派作業")

    assert test_teacher.can_assign_homework is True
    print("✅ Teacher can assign homework")

    # ===== Step 3: 老師派作業 =====
    print("\n📝 Step 3: 老師派作業給學生")

    # 建立 Content（簡化版，不需要實際內容）
    from models import Lesson, Program

    program = Program(
        teacher_id=test_teacher.id,
        classroom_id=test_classroom.id,
        name="Test Program",
        level="A1",
    )
    db.add(program)
    db.commit()

    lesson = Lesson(program_id=program.id, name="Test Lesson", order_index=1)
    db.add(lesson)
    db.commit()

    content = Content(
        lesson_id=lesson.id,
        type="reading_assessment",
        title="Test Content",
        order_index=1,
    )
    db.add(content)
    db.commit()

    # 建立作業
    assignment = Assignment(
        title="Complete Flow Test Assignment",
        description="測試完整流程",
        classroom_id=test_classroom.id,
        teacher_id=test_teacher.id,
        due_date=now + timedelta(days=7),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    # 關聯內容
    assignment_content = AssignmentContent(
        assignment_id=assignment.id, content_id=content.id, order_index=1
    )
    db.add(assignment_content)

    # 指派給學生
    student_assignment = StudentAssignment(
        assignment_id=assignment.id,
        student_id=test_student.id,
        classroom_id=test_classroom.id,
        title=assignment.title,
        instructions=assignment.description,
        due_date=assignment.due_date,
        status="NOT_STARTED",
    )
    db.add(student_assignment)
    db.commit()
    db.refresh(student_assignment)

    print(f"✅ Created Assignment ID: {assignment.id}")
    print(f"   Assigned to Student ID: {test_student.id}")

    # ===== Step 4: 學生提交 3 次錄音（每次 30 秒）=====
    print("\n📝 Step 4: 學生提交 3 次錄音")

    recordings = [
        {"duration": 30, "feature_type": "speech_recording"},
        {"duration": 45, "feature_type": "speech_recording"},
        {"duration": 25, "feature_type": "speech_recording"},
    ]

    for idx, recording in enumerate(recordings, 1):
        print(f"\n  Recording {idx}: {recording['duration']} 秒")

        usage_log = QuotaService.deduct_quota(
            db=db,
            teacher=test_teacher,
            student_id=test_student.id,
            assignment_id=assignment.id,
            feature_type=recording["feature_type"],
            unit_count=recording["duration"],
            unit_type="秒",
            feature_detail={"duration": recording["duration"], "recording_id": idx},
        )

        print(f"  ✅ Deducted {usage_log.points_used} points")
        print(f"     Quota Before: {usage_log.quota_before}")
        print(f"     Quota After: {usage_log.quota_after}")

    # ===== Step 5: 驗證配額正確扣除 =====
    print("\n📝 Step 5: 驗證配額正確扣除")

    db.refresh(period)
    db.refresh(test_teacher)

    expected_used = sum(r["duration"] for r in recordings)  # 30 + 45 + 25 = 100
    assert period.quota_used == expected_used
    assert test_teacher.quota_remaining == 10000 - expected_used

    print(f"✅ Quota Used: {period.quota_used} / {period.quota_total}")
    print(f"✅ Quota Remaining: {test_teacher.quota_remaining}")

    # ===== Step 6: 驗證 Log 記錄完整 =====
    print("\n📝 Step 6: 驗證 Log 記錄完整")

    logs = (
        db.query(PointUsageLog)
        .filter(PointUsageLog.subscription_period_id == period.id)
        .all()
    )

    assert len(logs) == 3
    print(f"✅ Found {len(logs)} usage logs")

    for idx, log in enumerate(logs, 1):
        print(f"\n  Log {idx}:")
        print(f"    Feature Type: {log.feature_type}")
        print(f"    Points Used: {log.points_used}")
        print(f"    Student ID: {log.student_id}")
        print(f"    Assignment ID: {log.assignment_id}")

        # 驗證每筆 Log 的完整性
        assert log.teacher_id == test_teacher.id
        assert log.student_id == test_student.id
        assert log.assignment_id == assignment.id
        assert log.feature_type == "speech_recording"

    # ===== Step 7: 驗證配額與 Log 同步 =====
    print("\n📝 Step 7: 驗證配額與 Log 同步")

    total_from_logs = sum(log.points_used for log in logs)
    assert total_from_logs == period.quota_used
    print(f"✅ Log Sum: {total_from_logs} == Period Used: {period.quota_used}")

    print("\n" + "=" * 70)
    print("🎉 Complete Quota Flow E2E Test PASSED")
    print("=" * 70)

    # Cleanup
    db.delete(student_assignment)
    db.delete(assignment_content)
    db.delete(assignment)
    db.delete(content)
    db.delete(lesson)
    db.delete(program)
    for log in logs:
        db.delete(log)
    db.delete(period)
    db.commit()


def test_quota_exceeded_still_allows_usage(db, test_teacher, test_student):
    """
    測試配額超限仍允許使用

    測試步驟：
    1. 老師訂閱並獲得 100 點配額
    2. 學生已使用 90 點（剩餘 10 點）
    3. 學生再使用 30 點（超過 20 點）
    4. 驗證：仍然成功扣除，quota_used = 120
    """
    print("\n" + "=" * 70)
    print("🧪 Quota Exceeded Still Allows Usage Test")
    print("=" * 70)

    # Step 1: 建立訂閱（100 點）
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=test_teacher.id,
        plan_name="Test Plan",
        amount_paid=Decimal("100"),
        quota_total=100,
        quota_used=90,  # 已使用 90 點
        start_date=now,
        end_date=now + timedelta(days=30),
        payment_method="credit_card",
        payment_status="paid",
        status="active",
    )
    db.add(period)
    test_teacher.subscription_end_date = now + timedelta(days=30)
    db.commit()
    db.refresh(period)

    print(f"✅ Initial State:")
    print(f"   Quota Total: {period.quota_total}")
    print(f"   Quota Used: {period.quota_used}")
    print(f"   Quota Remaining: {test_teacher.quota_remaining}")

    # Step 2: 嘗試使用 30 點（超過剩餘 10 點）
    print(f"\n📝 Attempting to use 30 points (exceeds remaining 10)")

    usage_log = QuotaService.deduct_quota(
        db=db,
        teacher=test_teacher,
        student_id=test_student.id,
        assignment_id=None,
        feature_type="speech_recording",
        unit_count=30,
        unit_type="秒",
    )

    # Step 3: 驗證成功扣除
    db.refresh(period)
    db.refresh(test_teacher)

    assert period.quota_used == 120  # 90 + 30
    # quota_remaining 使用 max(0, ...) 限制，不會為負值
    assert test_teacher.quota_remaining == 0  # max(0, -20) = 0
    assert usage_log.points_used == 30

    # 但實際上已經超額使用
    actual_remaining = period.quota_total - period.quota_used
    assert actual_remaining == -20  # 實際超額 20 點

    print(f"\n✅ Deduction Successful (Over Quota Allowed):")
    print(f"   Quota Used: {period.quota_used} (exceeded by 20)")
    print(
        f"   Quota Remaining (displayed): {test_teacher.quota_remaining} (max(0, -20))"
    )
    print(f"   Actual Remaining: {actual_remaining}")

    print("\n" + "=" * 70)
    print("🎉 Quota Exceeded Test PASSED")
    print("=" * 70)

    # Cleanup
    db.delete(usage_log)
    db.delete(period)
    db.commit()


def test_subscription_expired_cannot_deduct_quota(db, test_teacher, test_student):
    """
    測試訂閱過期無法扣配額

    測試步驟：
    1. 老師訂閱已過期（status=expired）
    2. 學生嘗試使用功能
    3. 驗證：拋出 402 錯誤 "NO_SUBSCRIPTION"
    """
    print("\n" + "=" * 70)
    print("🧪 Subscription Expired Cannot Deduct Quota Test")
    print("=" * 70)

    # Step 1: 建立已過期的訂閱
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=test_teacher.id,
        plan_name="Expired Plan",
        amount_paid=Decimal("330"),
        quota_total=10000,
        quota_used=500,
        start_date=now - timedelta(days=60),
        end_date=now - timedelta(days=30),  # 已過期
        payment_method="credit_card",
        payment_status="paid",
        status="expired",  # 重點：已過期
    )
    db.add(period)
    test_teacher.subscription_end_date = now - timedelta(days=30)
    db.commit()

    print(f"✅ Created Expired Subscription")
    print(f"   Status: {period.status}")
    print(f"   End Date: {period.end_date}")

    # Step 2: 嘗試扣配額（應該失敗）
    print(f"\n📝 Attempting to deduct quota (should fail)")

    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        QuotaService.deduct_quota(
            db=db,
            teacher=test_teacher,
            student_id=test_student.id,
            assignment_id=None,
            feature_type="speech_recording",
            unit_count=30,
            unit_type="秒",
        )

    # Step 3: 驗證錯誤
    assert exc_info.value.status_code == 402
    assert "NO_SUBSCRIPTION" in str(exc_info.value.detail)

    print(f"\n✅ Correctly Rejected:")
    print(f"   Status Code: {exc_info.value.status_code}")
    print(f"   Error: {exc_info.value.detail}")

    print("\n" + "=" * 70)
    print("🎉 Subscription Expired Test PASSED")
    print("=" * 70)

    # Cleanup
    db.delete(period)
    db.commit()


def test_assign_homework_requires_subscription(db, test_teacher, test_classroom):
    """
    測試派作業需要有效訂閱

    測試步驟：
    1. 老師訂閱已過期
    2. 嘗試派作業
    3. 驗證：can_assign_homework = False
    """
    print("\n" + "=" * 70)
    print("🧪 Assign Homework Requires Subscription Test")
    print("=" * 70)

    # Step 1: 設定訂閱已過期
    now = datetime.now(timezone.utc)
    test_teacher.subscription_end_date = now - timedelta(days=1)
    db.commit()
    db.refresh(test_teacher)

    print(f"✅ Teacher subscription expired")
    print(f"   End Date: {test_teacher.subscription_end_date}")

    # Step 2: 檢查 can_assign_homework
    assert test_teacher.can_assign_homework is False
    print(f"✅ can_assign_homework = False")

    # Step 3: 續訂後可派作業
    test_teacher.subscription_end_date = now + timedelta(days=30)
    db.commit()
    db.refresh(test_teacher)

    assert test_teacher.can_assign_homework is True
    print(f"✅ After renewal: can_assign_homework = True")

    print("\n" + "=" * 70)
    print("🎉 Assign Homework Test PASSED")
    print("=" * 70)


def test_unit_conversion(db):
    """
    測試單位換算正確性

    測試場景：
    - 30 秒 = 30 點
    - 500 字 = 50 點
    - 2 張 = 20 點
    - 1.5 分鐘 = 90 點
    """
    print("\n" + "=" * 70)
    print("🧪 Unit Conversion Test")
    print("=" * 70)

    test_cases = [
        (30, "秒", 30),
        (500, "字", 50),
        (2, "張", 20),
        (1.5, "分鐘", 90),
    ]

    for unit_count, unit_type, expected in test_cases:
        result = QuotaService.convert_unit_to_seconds(unit_count, unit_type)
        assert result == expected
        print(f"✅ {unit_count} {unit_type} = {result} points (expected {expected})")

    print("\n" + "=" * 70)
    print("🎉 Unit Conversion Test PASSED")
    print("=" * 70)


# ==================== 執行測試 ====================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 Running Complete Quota System E2E Tests")
    print("=" * 70)

    pytest.main([__file__, "-v", "-s"])
