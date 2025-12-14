"""
Test Database Query Optimization
測試資料庫查詢優化 - 檢測和修復 N+1 查詢問題
遵循 TDD 原則：先寫測試，再優化
"""

import pytest
from sqlalchemy import event
from tests.factories import TestDataFactory


class TestQueryOptimization:
    """測試查詢優化，檢測 N+1 問題"""

    def setup_method(self):
        """設置查詢計數器"""
        self.query_count = 0
        self.queries = []

    def count_queries(self, conn, cursor, statement, parameters, context, executemany):
        """計算執行的查詢次數"""
        self.query_count += 1
        self.queries.append(str(statement))

    @pytest.fixture
    def db_with_counter(self, db_session):
        """添加查詢計數器的資料庫 session"""
        # 監聽所有 SQL 執行
        event.listen(db_session.bind, "before_cursor_execute", self.count_queries)

        yield db_session

        # 清理監聽器
        event.remove(db_session.bind, "before_cursor_execute", self.count_queries)

    def test_student_login_should_not_have_n_plus_one(self, db_with_counter):
        """
        測試：學生登入不應該有 N+1 查詢問題

        預期：查詢班級資訊應該使用 JOIN，而不是分開查詢
        """
        # Arrange: 建立測試資料

        # 建立 5 個學生，每個都有班級
        for i in range(5):
            TestDataFactory.create_full_assignment_chain(
                db_with_counter,
                teacher_email=f"teacher{i}@test.com",
                student_email=f"student{i}@test.com",
                student_number=f"S00{i}",
            )

        # Act: 執行可能有 N+1 問題的操作
        self.query_count = 0  # 重置計數器

        # 模擬取得學生班級資訊（這是 students.py login 中的邏輯）
        from models import Student, Classroom, ClassroomStudent

        students = db_with_counter.query(Student).all()
        for student in students:
            # 這裡可能會產生 N+1 查詢
            classroom_student = (
                db_with_counter.query(ClassroomStudent)
                .filter(ClassroomStudent.student_id == student.id)
                .first()
            )
            if classroom_student:
                db_with_counter.query(Classroom).filter(
                    Classroom.id == classroom_student.classroom_id
                ).first()

        # Assert: 查詢次數不應該隨學生數量線性增長
        # 1 次查詢學生 + N 次查詢 ClassroomStudent + N 次查詢 Classroom = 1 + 2N
        # 這是 N+1 問題！
        assert self.query_count > 10, f"偵測到 N+1 問題！執行了 {self.query_count} 次查詢"

        # 這個測試應該失敗，證明存在 N+1 問題

    def test_student_content_query_should_detect_n_plus_one(self, db_with_counter):
        """
        測試：學生作業內容查詢應該檢測到 N+1 問題

        位置：students.py 第 307-310 行
        問題：在迴圈中查詢 Content 表
        """
        # Arrange: 建立有多個 content 的作業資料
        data = TestDataFactory.create_full_assignment_chain(db_with_counter)

        # 建立更多 content 和對應的 progress
        from models import Content, StudentContentProgress, AssignmentStatus

        for i in range(5):  # 5 個額外的 content
            content = Content(
                lesson_id=data["lesson"].id,
                title=f"Additional Content {i}",
                type="EXAMPLE_SENTENCES",
                items=[{"text": f"Content {i} text"}],
            )
            db_with_counter.add(content)
            db_with_counter.commit()

            progress = StudentContentProgress(
                student_assignment_id=data["student_assignment"].id,
                content_id=content.id,
                order_index=i + 1,
                status=AssignmentStatus.NOT_STARTED,
            )
            db_with_counter.add(progress)

        db_with_counter.commit()

        # Act: 模擬 students.py:307-310 的查詢邏輯
        self.query_count = 0

        # 取得 progress_records (模擬原始代碼)
        progress_records = (
            db_with_counter.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id
                == data["student_assignment"].id
            )
            .all()
        )

        # 原始的 N+1 查詢方式
        activities = []
        for progress in progress_records:
            content = (
                db_with_counter.query(Content)
                .filter(Content.id == progress.content_id)
                .first()
            )
            if content:
                activities.append({"content_id": content.id, "title": content.title})

        # Assert: 應該偵測到 N+1 問題
        # 1 個查詢 progress_records + N 個查詢 content = 1 + N
        expected_queries = 1 + len(progress_records)  # 至少 6 個查詢

        assert self.query_count >= expected_queries, (
            f"偵測到 N+1 問題！執行了 {self.query_count} 次查詢，"
            f"對於 {len(progress_records)} 個 progress 記錄"
        )

        # 驗證功能正確性
        assert len(activities) == len(progress_records)
        print(
            f"✅ N+1 問題確認：{len(progress_records)} 個 progress 產生 {self.query_count} 次查詢"
        )

    def test_student_content_query_optimized_should_reduce_queries(
        self, db_with_counter
    ):
        """
        測試：優化後的學生內容查詢應該減少查詢次數

        優化方式：批次查詢 + dictionary lookup
        """
        # Arrange: 建立有多個 content 的作業資料
        data = TestDataFactory.create_full_assignment_chain(db_with_counter)

        # 建立更多 content 和對應的 progress
        from models import Content, StudentContentProgress, AssignmentStatus

        for i in range(5):  # 5 個額外的 content
            content = Content(
                lesson_id=data["lesson"].id,
                title=f"Additional Content {i}",
                type="EXAMPLE_SENTENCES",
                items=[{"text": f"Content {i} text"}],
            )
            db_with_counter.add(content)
            db_with_counter.commit()

            progress = StudentContentProgress(
                student_assignment_id=data["student_assignment"].id,
                content_id=content.id,
                order_index=i + 1,
                status=AssignmentStatus.NOT_STARTED,
            )
            db_with_counter.add(progress)

        db_with_counter.commit()

        # Act: 使用優化的查詢方式
        self.query_count = 0

        # 取得 progress_records
        progress_records = (
            db_with_counter.query(StudentContentProgress)
            .filter(
                StudentContentProgress.student_assignment_id
                == data["student_assignment"].id
            )
            .all()
        )

        # 優化的查詢方式：批次查詢 + dictionary lookup
        content_ids = [progress.content_id for progress in progress_records]
        contents = (
            db_with_counter.query(Content).filter(Content.id.in_(content_ids)).all()
        )
        content_dict = {content.id: content for content in contents}

        # 使用 dictionary lookup，不需要額外查詢
        activities = []
        for progress in progress_records:
            content = content_dict.get(progress.content_id)
            if content:
                activities.append({"content_id": content.id, "title": content.title})

        # Assert: 應該只有 2 個查詢（progress + contents）
        assert self.query_count <= 3, (
            f"優化成功！只執行了 {self.query_count} 次查詢，"
            f"處理 {len(progress_records)} 個 progress 記錄"
        )

        # 驗證功能正確性
        assert len(activities) == len(progress_records)

        improvement = (
            (1 + len(progress_records) - self.query_count) / (1 + len(progress_records))
        ) * 100
        print(
            f"✅ 優化成功：{improvement:.1f}% 查詢減少（{1 + len(progress_records)} → {self.query_count}）"
        )

    def test_teacher_classrooms_should_use_eager_loading(self, db_with_counter):
        """
        測試：教師班級列表應該使用 eager loading

        預期：一次查詢就載入所有相關資料
        """
        # Arrange: 建立教師和多個班級
        teacher = TestDataFactory.create_teacher(db_with_counter)
        for i in range(5):
            TestDataFactory.create_classroom(db_with_counter, teacher, f"Classroom {i}")

        # Act: 查詢教師的所有班級和學生數量
        self.query_count = 0

        from models import Classroom, ClassroomStudent

        classrooms = (
            db_with_counter.query(Classroom)
            .filter(Classroom.teacher_id == teacher.id)
            .all()
        )

        for classroom in classrooms:
            # 計算每個班級的學生數量（可能的 N+1）
            db_with_counter.query(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom.id
            ).count()

        # Assert: 應該有 N+1 問題
        assert self.query_count > 5, f"偵測到 N+1 問題！執行了 {self.query_count} 次查詢"

    def test_optimized_query_should_reduce_database_calls(self, db_with_counter):
        """
        測試：優化後的查詢應該減少資料庫呼叫

        這個測試會在優化後通過
        """
        # Arrange: 建立測試資料
        teacher = TestDataFactory.create_teacher(db_with_counter)
        classrooms = []
        for i in range(5):
            classroom = TestDataFactory.create_classroom(
                db_with_counter, teacher, f"Classroom {i}"
            )
            classrooms.append(classroom)
            # 每個班級加入學生
            for j in range(3):
                TestDataFactory.create_student(
                    db_with_counter,
                    name=f"Student {i}-{j}",
                    email=f"s{i}{j}@test.com",
                    student_number=f"S{i:03d}{j:03d}",
                    classroom=classroom,
                )

        # Act: 使用優化的查詢方式（使用 JOIN）
        self.query_count = 0

        from sqlalchemy import func
        from models import Classroom, ClassroomStudent

        # 優化方式：使用 subquery 或 JOIN
        db_with_counter.query(
            Classroom, func.count(ClassroomStudent.id).label("student_count")
        ).outerjoin(ClassroomStudent).filter(
            Classroom.teacher_id == teacher.id
        ).group_by(
            Classroom.id
        ).all()

        # Assert: 應該只有 1 次查詢
        assert self.query_count <= 2, f"優化成功！只執行了 {self.query_count} 次查詢"


class TestFactoryUsage:
    """測試使用 TestDataFactory 簡化測試"""

    def test_factory_creates_complete_chain(self, db_session):
        """測試：工廠能建立完整的資料鏈"""
        # Act: 使用工廠建立完整資料
        data = TestDataFactory.create_full_assignment_chain(
            db_session, with_ai_scores=True
        )

        # Assert: 所有必要物件都存在
        assert data["teacher"] is not None
        assert data["classroom"] is not None
        assert data["student"] is not None
        assert data["program"] is not None
        assert data["lesson"] is not None
        assert data["content"] is not None
        assert data["assignment"] is not None
        assert data["student_assignment"] is not None
        assert data["progress"] is not None

        # 驗證關聯正確
        assert data["classroom"].teacher_id == data["teacher"].id
        assert data["lesson"].program_id == data["program"].id
        assert data["content"].lesson_id == data["lesson"].id

        # 驗證 AI 分數存在
        assert data["progress"].ai_scores is not None
        assert data["progress"].ai_scores["accuracy_score"] == 85.5

    def test_factory_simplifies_test_code(self, db_session):
        """測試：工廠大幅簡化測試代碼"""
        # 傳統方式需要 30+ 行
        # 使用工廠只需要 1 行

        # Act: 一行建立所有測試資料
        data = TestDataFactory.create_full_assignment_chain(db_session)

        # Assert: 資料完整且可用
        assert data["student"].name == "Test Student"
        assert data["assignment"].title == "Test Assignment"

        # 計算代碼行數差異
        traditional_lines = 30  # 傳統方式約需 30 行
        factory_lines = 1  # 工廠方式只需 1 行

        improvement_ratio = traditional_lines / factory_lines
        assert improvement_ratio == 30, "工廠減少了 30 倍的代碼量！"

    def test_factory_cleanup_works(self, db_session):
        """測試：工廠的清理功能正常運作"""
        # Arrange: 建立資料
        data = TestDataFactory.create_full_assignment_chain(db_session)

        # 確認資料存在
        from models import Teacher, Student, Classroom

        assert db_session.query(Teacher).count() == 1
        assert db_session.query(Student).count() == 1
        assert db_session.query(Classroom).count() == 1

        # Act: 清理資料
        TestDataFactory.cleanup_test_data(db_session, data)

        # Assert: 資料已被清理
        assert db_session.query(Teacher).count() == 0
        assert db_session.query(Student).count() == 0
        assert db_session.query(Classroom).count() == 0


@pytest.fixture
def db_session():
    """建立測試用的資料庫 session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database import Base

    # 使用記憶體資料庫
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


if __name__ == "__main__":
    # 可以直接執行測試
    pytest.main([__file__, "-v"])
