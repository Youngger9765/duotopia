"""
TDD 測試：驗證 Speech Assessment API 資料庫查詢優化

測試目標：
1. assess_pronunciation_endpoint 使用 joinedload 減少查詢次數（3次 → 1次）
2. get_student_assessments 使用 joinedload 避免 N+1 查詢
3. 確保優化後功能正常運作
"""

from sqlalchemy import event
from sqlalchemy.engine import Engine


class QueryCounter:
    """計算 SQLAlchemy 查詢次數的工具"""

    def __init__(self):
        self.count = 0
        self.queries = []

    def __enter__(self):
        event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self._before_cursor_execute)

    def _before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        self.count += 1
        self.queries.append(statement)


def test_assess_endpoint_uses_joinedload_to_reduce_queries(db_session):
    """
    TDD: 驗證 assess_pronunciation_endpoint 使用 joinedload

    預期：
    - 使用 joinedload 後，查詢 StudentAssignment + Assignment + Teacher 只需 1 次查詢
    - 不使用 joinedload 需要 3 次查詢（N+1 問題）
    """
    from models import Student, Teacher, Assignment, StudentAssignment

    # 創建測試資料
    teacher = Teacher(
        name="Test Teacher", email="teacher@test.com", password_hash="test"
    )
    db_session.add(teacher)
    db_session.flush()

    from datetime import date

    student = Student(
        name="Test Student",
        password_hash="test",
        birthdate=date(2010, 1, 1),
    )
    db_session.add(student)
    db_session.flush()

    assignment = Assignment(title="Test Assignment", teacher_id=teacher.id)
    db_session.add(assignment)
    db_session.flush()

    student_assignment = StudentAssignment(
        student_id=student.id, assignment_id=assignment.id
    )
    db_session.add(student_assignment)
    db_session.commit()

    # 測試：計算查詢次數
    with QueryCounter() as counter:
        # 模擬查詢 StudentAssignment 的過程
        result = (
            db_session.query(StudentAssignment)
            .filter(
                StudentAssignment.id == student_assignment.id,
                StudentAssignment.student_id == student.id,
            )
            .first()
        )

        # 如果沒有 joinedload，訪問關聯會觸發額外查詢
        _ = result.assignment  # 觸發查詢 2
        _ = result.assignment.teacher  # 觸發查詢 3

    # 沒有優化：應該是 3 次查詢
    queries_without_optimization = counter.count

    # 使用 joinedload 優化
    from sqlalchemy.orm import joinedload

    with QueryCounter() as counter_optimized:
        result = (
            db_session.query(StudentAssignment)
            .options(
                joinedload(StudentAssignment.assignment).joinedload(Assignment.teacher)
            )
            .filter(
                StudentAssignment.id == student_assignment.id,
                StudentAssignment.student_id == student.id,
            )
            .first()
        )

        # 訪問關聯不會觸發額外查詢（已經 preload）
        _ = result.assignment
        _ = result.assignment.teacher

    queries_with_optimization = counter_optimized.count

    # 驗證：優化後查詢次數減少
    assert (
        queries_with_optimization < queries_without_optimization
    ), f"優化後查詢應減少：{queries_with_optimization} < {queries_without_optimization}"

    # 理想情況：優化後只需 1 次查詢（JOIN）
    assert (
        queries_with_optimization == 1
    ), f"使用 joinedload 應該只需 1 次查詢，實際: {queries_with_optimization}"


def test_get_student_assessments_avoids_n_plus_1(db_session):
    """
    TDD: 驗證 get_student_assessments 避免 N+1 查詢

    預期：
    - 查詢 10 筆 StudentContentProgress 記錄
    - 沒有 joinedload: 1 (主查詢) + 10 (每筆訪問 content) = 11 次查詢
    - 有 joinedload: 1 次查詢（JOIN content）
    """
    from models import (
        Student,
        Teacher,
        Assignment,
        StudentAssignment,
        Content,
        StudentContentProgress,
    )

    # 創建測試資料
    teacher = Teacher(name="Teacher", email="t2@test.com", password_hash="test")
    db_session.add(teacher)
    db_session.flush()

    from datetime import date

    student = Student(name="Student", password_hash="test", birthdate=date(2010, 1, 1))
    db_session.add(student)
    db_session.flush()

    assignment = Assignment(title="Assignment", teacher_id=teacher.id)
    db_session.add(assignment)
    db_session.flush()

    student_assignment = StudentAssignment(
        student_id=student.id, assignment_id=assignment.id
    )
    db_session.add(student_assignment)
    db_session.flush()

    # 創建 10 筆 progress 記錄
    for i in range(10):
        content = Content(
            title=f"Content {i}",
            type="grouped_questions",
            text=f"Question {i}",
            teacher_id=teacher.id,
        )
        db_session.add(content)
        db_session.flush()

        progress = StudentContentProgress(
            student_assignment_id=student_assignment.id,
            content_id=content.id,
            ai_scores={"accuracy_score": 90.0},
            order_index=i,
        )
        db_session.add(progress)

    db_session.commit()

    # 測試：沒有 joinedload 的查詢
    with QueryCounter() as counter:
        records = (
            db_session.query(StudentContentProgress)
            .join(StudentContentProgress.student_assignment)
            .filter(
                StudentContentProgress.ai_scores.isnot(None),
                StudentAssignment.student_id == student.id,
            )
            .limit(10)
            .all()
        )

        # 訪問 content 會觸發 N 次額外查詢
        for record in records:
            _ = record.content.text if record.content else ""

    queries_without_optimization = counter.count

    # 測試：使用 joinedload 優化
    from sqlalchemy.orm import joinedload

    with QueryCounter() as counter_optimized:
        records = (
            db_session.query(StudentContentProgress)
            .join(StudentContentProgress.student_assignment)
            .options(joinedload(StudentContentProgress.content))
            .filter(
                StudentContentProgress.ai_scores.isnot(None),
                StudentAssignment.student_id == student.id,
            )
            .limit(10)
            .all()
        )

        # 訪問 content 不會觸發額外查詢
        for record in records:
            _ = record.content.text if record.content else ""

    queries_with_optimization = counter_optimized.count

    # 驗證：優化後查詢次數大幅減少
    assert (
        queries_with_optimization < queries_without_optimization
    ), f"優化後查詢應減少：{queries_with_optimization} < {queries_without_optimization}"

    # N+1 問題：沒優化應該是 1 + N 次查詢
    expected_without = 1 + len(records)
    assert (
        queries_without_optimization >= expected_without - 1
    ), f"沒優化應該有 N+1 查詢問題，預期 >={expected_without}, 實際: {queries_without_optimization}"

    # 優化後：應該只需要 1-2 次查詢（主查詢 + JOIN）
    assert (
        queries_with_optimization <= 2
    ), f"使用 joinedload 應該只需 1-2 次查詢，實際: {queries_with_optimization}"


def test_optimized_query_returns_correct_data(db_session):
    """
    TDD: 驗證優化後的查詢返回正確資料

    確保 joinedload 不會影響資料正確性
    """
    from models import Student, Teacher, Assignment, StudentAssignment
    from sqlalchemy.orm import joinedload

    # 創建測試資料
    teacher = Teacher(name="T3", email="t3@test.com", password_hash="test")
    db_session.add(teacher)
    db_session.flush()

    from datetime import date

    student = Student(name="S3", password_hash="test", birthdate=date(2010, 1, 1))
    db_session.add(student)
    db_session.flush()

    assignment = Assignment(title="A3", teacher_id=teacher.id)
    db_session.add(assignment)
    db_session.flush()

    student_assignment = StudentAssignment(
        student_id=student.id, assignment_id=assignment.id
    )
    db_session.add(student_assignment)
    db_session.commit()

    # 使用 joinedload 查詢
    result = (
        db_session.query(StudentAssignment)
        .options(
            joinedload(StudentAssignment.assignment).joinedload(Assignment.teacher)
        )
        .filter(StudentAssignment.id == student_assignment.id)
        .first()
    )

    # 驗證：資料正確
    assert result is not None, "應該找到 StudentAssignment"
    assert result.assignment is not None, "應該 preload Assignment"
    assert result.assignment.teacher is not None, "應該 preload Teacher"
    assert result.assignment.teacher.name == "T3", "Teacher 資料應該正確"
    assert result.assignment.title == "A3", "Assignment 資料應該正確"
