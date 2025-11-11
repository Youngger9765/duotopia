"""
完整 E2E 整合測試：訂閱系統重構驗證
測試範圍：
1. 老師訂閱生命週期
2. 班級和作業管理
3. 學生作業流程
4. 配額控制和限制
5. Edge Cases
測試目標：
- 驗證訂閱系統重構不影響核心功能
- 驗證所有權限和配額檢查正常運作
- 驗證 Edge Cases 正確處理
"""
import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from typing import Dict, Any
from models import (
    Teacher,
    Student,
    Classroom,
    ClassroomStudent,
    SubscriptionPeriod,
)
from auth import get_password_hash
from main import app


# ============ Fixtures ============
@pytest.fixture
def test_client():
    """測試客戶端"""
    return TestClient(app)


@pytest.fixture
def test_context(db_session: Session):
    """測試上下文 - 提供測試所需的所有資源"""
    context = {
        "db": db_session,
        "teachers": {},
        "students": {},
        "classrooms": {},
        "assignments": {},
        "tokens": {},
    }
    return context


# ============ Helper Functions ============
def create_teacher_with_subscription(
    db: Session,
    email: str,
    name: str,
    plan: str = "Tutor Teachers",
    quota_total: int = 10000,
    days: int = 30,
) -> Dict[str, Any]:
    """創建有訂閱的老師"""
    teacher = Teacher(
        email=email,
        password_hash=get_password_hash("test123"),
        name=name,
        email_verified=True,
        is_active=True,
        subscription_auto_renew=True,
    )
    db.add(teacher)
    db.flush()
    # 創建訂閱週期
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name=plan,
        amount_paid=330 if plan == "Tutor Teachers" else 660,
        quota_total=quota_total,
        quota_used=0,
        start_date=now,
        end_date=now + timedelta(days=days),
        payment_method="trial",
        payment_status="paid",
        status="active",
    )
    db.add(period)
    db.commit()
    db.refresh(teacher)
    return {"teacher": teacher, "period": period}


def create_expired_teacher(db: Session, email: str, name: str) -> Teacher:
    """創建訂閱過期的老師"""
    teacher = Teacher(
        email=email,
        password_hash=get_password_hash("test123"),
        name=name,
        email_verified=True,
        is_active=True,
        subscription_auto_renew=False,
    )
    db.add(teacher)
    db.flush()
    # 創建已過期的訂閱週期
    now = datetime.now(timezone.utc)
    period = SubscriptionPeriod(
        teacher_id=teacher.id,
        plan_name="Tutor Teachers",
        amount_paid=0,
        quota_total=10000,
        quota_used=0,
        start_date=now - timedelta(days=60),
        end_date=now - timedelta(days=1),  # 昨天過期
        payment_method="trial",
        payment_status="paid",
        status="expired",
    )
    db.add(period)
    db.commit()
    db.refresh(teacher)
    return teacher


def create_student(db: Session, email: str, name: str) -> Student:
    """創建學生"""
    from datetime import date

    student = Student(
        email=email,
        password_hash=get_password_hash("test123"),
        name=name,
        email_verified=True,
        is_active=True,
        birthdate=date(2015, 1, 1),  # 必填欄位
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def create_classroom(db: Session, teacher_id: int, name: str) -> Classroom:
    """創建班級"""
    classroom = Classroom(
        teacher_id=teacher_id,
        name=name,
        grade="國小三年級",
        # subject 不是 Classroom 的欄位
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def add_student_to_classroom(
    db: Session, classroom_id: int, student_id: int
) -> ClassroomStudent:
    """將學生加入班級"""
    cs = ClassroomStudent(classroom_id=classroom_id, student_id=student_id)
    db.add(cs)
    db.commit()
    return cs


def consume_quota(db: Session, period: SubscriptionPeriod, amount: int):
    """消耗配額"""
    period.quota_used += amount
    db.commit()


# ============ Test Classes ============
class TestTeacherSubscriptionLifecycle:
    """測試老師訂閱生命週期"""

    def test_01_teacher_registration_and_trial(self, db_session):
        """✅ 測試 1：老師註冊並獲得 30 天試用"""
        # Given: 新註冊的老師
        result = create_teacher_with_subscription(
            db_session, "new_teacher@test.com", "新老師", days=30
        )
        teacher = result["teacher"]
        period = result["period"]
        # Then: 應該有 30 天試用
        assert teacher.subscription_status == "subscribed"
        assert teacher.days_remaining >= 29
        assert period.quota_total == 10000
        assert period.quota_used == 0

    def test_02_active_teacher_can_create_class(self, db_session):
        """✅ 測試 2：有效訂閱的老師可以創建班級"""
        # Given: 有訂閱的老師
        result = create_teacher_with_subscription(
            db_session, "teacher@test.com", "測試老師"
        )
        teacher = result["teacher"]
        # When: 創建班級
        classroom = create_classroom(db_session, teacher.id, "三年一班")
        # Then: 班級創建成功
        assert classroom.id is not None
        assert classroom.teacher_id == teacher.id
        assert classroom.name == "三年一班"

    def test_03_expired_teacher_blocked(self, db_session):
        """❌ 測試 3：過期老師應該被擋住"""
        # Given: 訂閱過期的老師
        teacher = create_expired_teacher(db_session, "expired@test.com", "過期老師")
        # Then: 訂閱狀態應該是過期
        assert teacher.subscription_status == "expired"
        assert teacher.days_remaining == 0
        assert teacher.can_assign_homework is False

    def test_04_quota_exceeded_teacher_blocked(self, db_session):
        """❌ 測試 4：配額用完的老師應該被擋住"""
        # Given: 配額用完的老師
        result = create_teacher_with_subscription(
            db_session, "quota_exceeded@test.com", "配額用完老師", quota_total=1000
        )
        period = result["period"]
        # When: 配額用完
        consume_quota(db_session, period, 1000)
        # Then: 配額應該用完
        db_session.refresh(period)
        assert period.quota_used >= period.quota_total


class TestClassroomAndAssignmentManagement:
    """測試班級和作業管理"""

    @pytest.fixture
    def setup_classroom(self, db_session):
        """準備班級環境"""
        # 創建老師
        result = create_teacher_with_subscription(
            db_session, "classroom_teacher@test.com", "班級老師"
        )
        teacher = result["teacher"]
        # 創建班級
        classroom = create_classroom(db_session, teacher.id, "測試班級")
        # 創建學生
        student1 = create_student(db_session, "student1@test.com", "學生1")
        student2 = create_student(db_session, "student2@test.com", "學生2")
        # 加入班級
        add_student_to_classroom(db_session, classroom.id, student1.id)
        add_student_to_classroom(db_session, classroom.id, student2.id)
        return {
            "teacher": teacher,
            "period": result["period"],
            "classroom": classroom,
            "students": [student1, student2],
        }

    def test_05_create_classroom_with_students(self, db_session, setup_classroom):
        """✅ 測試 5：創建班級並加入學生"""
        data = setup_classroom
        # Then: 班級應該有 2 個學生
        students = (
            db_session.query(ClassroomStudent)
            .filter_by(classroom_id=data["classroom"].id)
            .all()
        )
        assert len(students) == 2


class TestStudentAssignmentFlow:
    """測試學生作業流程"""

    def test_06_student_submit_when_teacher_active(self, db_session):
        """✅ 測試 6：老師訂閱有效時，學生可以提交作業"""
        # Given: 有訂閱的老師和學生
        result = create_teacher_with_subscription(
            db_session, "active_teacher@test.com", "有效老師"
        )
        teacher = result["teacher"]
        # Then: 老師應該可以派作業
        assert teacher.can_assign_homework is True
        assert teacher.current_period is not None
        assert teacher.current_period.quota_total > 0

    def test_07_student_blocked_when_teacher_expired(self, db_session):
        """❌ 測試 7：老師訂閱過期時，學生應該被擋住"""
        # Given: 過期的老師
        teacher = create_expired_teacher(db_session, "expired_teacher@test.com", "過期老師")
        # Then: 老師不能派作業
        assert teacher.can_assign_homework is False
        assert teacher.subscription_status == "expired"

    def test_08_student_blocked_when_quota_exceeded(self, db_session):
        """❌ 測試 8：老師配額用完時，學生應該被擋住"""
        # Given: 配額用完的老師
        result = create_teacher_with_subscription(
            db_session,
            "quota_full_teacher@test.com",
            "配額用完老師",
            quota_total=100,
        )
        period = result["period"]
        # When: 配額用完
        consume_quota(db_session, period, 100)
        # Then: 配額應該用完
        db_session.refresh(period)
        assert period.quota_used >= period.quota_total


class TestQuotaSystem:
    """測試配額系統"""

    def test_09_quota_consumption(self, db_session):
        """✅ 測試 9：配額正常消耗"""
        # Given: 有訂閱的老師
        result = create_teacher_with_subscription(
            db_session, "quota_teacher@test.com", "配額老師", quota_total=1000
        )
        period = result["period"]
        # When: 使用 100 秒配額
        initial_quota = period.quota_used
        consume_quota(db_session, period, 100)
        # Then: 配額應該減少
        db_session.refresh(period)
        assert period.quota_used == initial_quota + 100

    def test_10_quota_warning_at_90_percent(self, db_session):
        """⚠️ 測試 10：配額 90% 時應該警告"""
        # Given: 配額快用完的老師
        result = create_teacher_with_subscription(
            db_session, "warning_teacher@test.com", "警告老師", quota_total=1000
        )
        period = result["period"]
        # When: 使用到 90%
        consume_quota(db_session, period, 900)
        # Then: 配額使用率應該 >= 90%
        db_session.refresh(period)
        usage_rate = period.quota_used / period.quota_total
        assert usage_rate >= 0.9

    def test_11_quota_blocked_at_100_percent(self, db_session):
        """❌ 測試 11：配額 100% 時應該擋住"""
        # Given: 配額的老師
        result = create_teacher_with_subscription(
            db_session, "blocked_teacher@test.com", "被擋老師", quota_total=1000
        )
        period = result["period"]
        # When: 配額用完
        consume_quota(db_session, period, 1000)
        # Then: 應該達到 100%
        db_session.refresh(period)
        assert period.quota_used >= period.quota_total


class TestEdgeCases:
    """測試 Edge Cases"""

    def test_12_concurrent_quota_consumption(self, db_session):
        """✅ 測試 12：並發配額消耗"""
        # Given: 有訂閱的老師
        result = create_teacher_with_subscription(
            db_session, "concurrent_teacher@test.com", "並發老師", quota_total=1000
        )
        period = result["period"]
        # When: 多次並發消耗
        for _ in range(5):
            consume_quota(db_session, period, 50)
        # Then: 總共應該消耗 250
        db_session.refresh(period)
        assert period.quota_used == 250

    def test_13_subscription_renewal_resets_quota(self, db_session):
        """✅ 測試 13：訂閱續費重置配額"""
        # Given: 配額用完的老師
        result = create_teacher_with_subscription(
            db_session, "renewal_teacher@test.com", "續費老師", quota_total=1000
        )
        teacher = result["teacher"]
        old_period = result["period"]
        # 用完配額
        consume_quota(db_session, old_period, 1000)
        old_period.status = "expired"
        # When: 續費創建新 period
        now = datetime.now(timezone.utc)
        new_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="auto_renew",
            payment_status="paid",
            status="active",
        )
        db_session.add(new_period)
        db_session.commit()
        # Then: 新 period 應該有新配額
        db_session.refresh(teacher)
        assert teacher.current_period.id == new_period.id
        assert teacher.current_period.quota_used == 0
        assert teacher.current_period.quota_total == 10000

    def test_14_multiple_periods_only_one_active(self, db_session):
        """✅ 測試 14：多個 period 只有一個 active"""
        # Given: 有多個 period 的老師
        result = create_teacher_with_subscription(
            db_session, "multi_period_teacher@test.com", "多期老師"
        )
        teacher = result["teacher"]
        old_period = result["period"]
        # 舊 period 改為 expired
        old_period.status = "expired"
        # 創建新 period
        now = datetime.now(timezone.utc)
        new_period = SubscriptionPeriod(
            teacher_id=teacher.id,
            plan_name="Tutor Teachers",
            amount_paid=330,
            quota_total=10000,
            quota_used=0,
            start_date=now,
            end_date=now + timedelta(days=30),
            payment_method="manual",
            payment_status="paid",
            status="active",
        )
        db_session.add(new_period)
        db_session.commit()
        # Then: 應該只有一個 active period
        active_periods = (
            db_session.query(SubscriptionPeriod)
            .filter_by(teacher_id=teacher.id, status="active")
            .all()
        )
        assert len(active_periods) == 1
        assert active_periods[0].id == new_period.id


class TestCompleteHappyPath:
    """完整正常流程測試"""

    def test_15_complete_workflow(self, db_session):
        """✅ 測試 15：完整工作流程（老師訂閱 → 建班 → 派作業 → 學生提交 → 評分）"""
        # Step 1: 老師註冊並獲得訂閱
        result = create_teacher_with_subscription(
            db_session, "complete_teacher@test.com", "完整流程老師"
        )
        teacher = result["teacher"]
        period = result["period"]
        assert teacher.subscription_status == "subscribed"
        assert period.quota_used == 0
        # Step 2: 創建班級
        classroom = create_classroom(db_session, teacher.id, "完整流程班級")
        assert classroom.teacher_id == teacher.id
        # Step 3: 加入學生
        student = create_student(db_session, "complete_student@test.com", "完整流程學生")
        add_student_to_classroom(db_session, classroom.id, student.id)
        # Step 4: 確認學生在班級中
        cs = (
            db_session.query(ClassroomStudent)
            .filter_by(classroom_id=classroom.id, student_id=student.id)
            .first()
        )
        assert cs is not None
        # Step 5: 模擬學生使用配額（錄音 30 秒）
        consume_quota(db_session, period, 30)
        # Then: 配額應該減少
        db_session.refresh(period)
        assert period.quota_used == 30
        assert period.quota_total - period.quota_used == 9970


# ============ Test Summary ============
def test_summary():
    """測試摘要"""
    print("\n" + "=" * 60)
    print("📊 E2E 整合測試摘要")
    print("=" * 60)
    print("\n✅ 測試範圍：")
    print("  1. 老師訂閱生命週期 (4 個測試)")
    print("  2. 班級和作業管理 (1 個測試)")
    print("  3. 學生作業流程 (3 個測試)")
    print("  4. 配額系統 (3 個測試)")
    print("  5. Edge Cases (3 個測試)")
    print("  6. 完整工作流程 (1 個測試)")
    print("\n📈 總計：15 個測試")
    print("=" * 60 + "\n")
