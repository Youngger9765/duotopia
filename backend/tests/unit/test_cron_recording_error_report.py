"""
測試 Cron Recording Error Report 的資料查詢邏輯
確保學生、班級、老師的 JOIN 查詢正確
"""
import pytest
from datetime import date
from sqlalchemy.orm import Session
from models import Teacher, Student, Classroom, ClassroomStudent


class TestRecordingErrorReportDataQuery:
    """測試錄音錯誤報告的資料查詢邏輯"""

    @pytest.fixture
    def setup_student_classroom_data(self, test_session: Session):
        """建立測試資料：學生 + 班級 + 老師"""
        # 建立老師
        teacher1 = Teacher(email="teacher1@test.com", name="王老師", password_hash="hash1")
        teacher2 = Teacher(email="teacher2@test.com", name="李老師", password_hash="hash2")
        test_session.add_all([teacher1, teacher2])
        test_session.flush()

        # 建立班級
        classroom1 = Classroom(name="一年一班", teacher_id=teacher1.id)
        classroom2 = Classroom(name="一年二班", teacher_id=teacher2.id)
        test_session.add_all([classroom1, classroom2])
        test_session.flush()

        # 建立學生
        student1 = Student(
            name="學生A",
            email="studentA@test.com",
            student_number="S001",
            password_hash="hash",
            birthdate=date(2010, 1, 1),
        )
        student2 = Student(
            name="學生B",
            email="studentB@test.com",
            student_number="S002",
            password_hash="hash",
            birthdate=date(2010, 2, 1),
        )
        student3 = Student(
            name="學生C",
            email=None,  # 沒有 Email
            student_number="S003",
            password_hash="hash",
            birthdate=date(2010, 3, 1),
        )
        test_session.add_all([student1, student2, student3])
        test_session.flush()

        # 建立學生-班級關聯
        # 學生A 在一年一班
        cs1 = ClassroomStudent(student_id=student1.id, classroom_id=classroom1.id)
        # 學生B 在兩個班級
        cs2 = ClassroomStudent(student_id=student2.id, classroom_id=classroom1.id)
        cs3 = ClassroomStudent(student_id=student2.id, classroom_id=classroom2.id)
        # 學生C 沒有班級
        test_session.add_all([cs1, cs2, cs3])
        test_session.commit()

        return {
            "teacher1": teacher1,
            "teacher2": teacher2,
            "classroom1": classroom1,
            "classroom2": classroom2,
            "student1": student1,
            "student2": student2,
            "student3": student3,
        }

    def test_student_classroom_join_query(
        self, test_session: Session, setup_student_classroom_data
    ):
        """測試學生-班級-老師 JOIN 查詢（模擬 cron.py 的邏輯）"""
        data = setup_student_classroom_data
        student_ids = [data["student1"].id, data["student2"].id, data["student3"].id]

        # 🔥 這是 cron.py 裡的查詢邏輯
        students_data = (
            test_session.query(
                Student.id,
                Student.name,
                Student.email,
                Classroom.name.label("classroom_name"),
                Teacher.name.label("teacher_name"),
                Teacher.email.label("teacher_email"),
            )
            .outerjoin(ClassroomStudent, Student.id == ClassroomStudent.student_id)
            .outerjoin(Classroom, ClassroomStudent.classroom_id == Classroom.id)
            .outerjoin(Teacher, Classroom.teacher_id == Teacher.id)
            .filter(Student.id.in_(student_ids))
            .all()
        )

        # 驗證查詢結果
        assert len(students_data) > 0, "應該要查詢到學生資料"

        # 建立 student_id -> data 的 mapping（和 cron.py 一樣的邏輯）
        student_data_map = {}
        for row in students_data:
            if row.id not in student_data_map:
                student_data_map[row.id] = {
                    "name": row.name,
                    "email": row.email,
                    "classrooms": [],
                    "teachers": set(),
                }
            if row.classroom_name:
                student_data_map[row.id]["classrooms"].append(row.classroom_name)
            if row.teacher_name and row.teacher_email:
                student_data_map[row.id]["teachers"].add(
                    f"{row.teacher_name} ({row.teacher_email})"
                )

        # 驗證學生A（一個班級）
        student_a_data = student_data_map[data["student1"].id]
        assert student_a_data["name"] == "學生A"
        assert student_a_data["email"] == "studentA@test.com"
        assert len(student_a_data["classrooms"]) == 1
        assert "一年一班" in student_a_data["classrooms"]
        assert len(student_a_data["teachers"]) == 1
        assert "王老師 (teacher1@test.com)" in student_a_data["teachers"]

        # 驗證學生B（兩個班級）
        student_b_data = student_data_map[data["student2"].id]
        assert student_b_data["name"] == "學生B"
        assert len(student_b_data["classrooms"]) == 2
        assert "一年一班" in student_b_data["classrooms"]
        assert "一年二班" in student_b_data["classrooms"]
        assert len(student_b_data["teachers"]) == 2

        # 驗證學生C（沒有班級）
        student_c_data = student_data_map[data["student3"].id]
        assert student_c_data["name"] == "學生C"
        assert student_c_data["email"] is None
        assert len(student_c_data["classrooms"]) == 0
        assert len(student_c_data["teachers"]) == 0

    def test_error_report_data_structure(
        self, test_session: Session, setup_student_classroom_data
    ):
        """測試錯誤報告的資料結構組裝（模擬 cron.py 的邏輯）"""
        data = setup_student_classroom_data

        # 模擬 BigQuery 返回的錯誤資料
        class MockErrorRow:
            def __init__(self, student_id, error_count, error_types):
                self.student_id = student_id
                self.error_count = error_count
                self.error_types = error_types

        student_errors = [
            MockErrorRow(data["student1"].id, 5, "TIMEOUT,NETWORK_ERROR"),
            MockErrorRow(data["student2"].id, 3, "INVALID_AUDIO"),
            MockErrorRow(data["student3"].id, 2, "TIMEOUT"),
        ]

        # 查詢學生資料
        student_ids = [row.student_id for row in student_errors]
        students_data = (
            test_session.query(
                Student.id,
                Student.name,
                Student.email,
                Classroom.name.label("classroom_name"),
                Teacher.name.label("teacher_name"),
                Teacher.email.label("teacher_email"),
            )
            .outerjoin(ClassroomStudent, Student.id == ClassroomStudent.student_id)
            .outerjoin(Classroom, ClassroomStudent.classroom_id == Classroom.id)
            .outerjoin(Teacher, Classroom.teacher_id == Teacher.id)
            .filter(Student.id.in_(student_ids))
            .all()
        )

        # 建立 mapping
        student_data_map = {}
        for row in students_data:
            if row.id not in student_data_map:
                student_data_map[row.id] = {
                    "name": row.name,
                    "email": row.email,
                    "classrooms": [],
                    "teachers": set(),
                }
            if row.classroom_name:
                student_data_map[row.id]["classrooms"].append(row.classroom_name)
            if row.teacher_name and row.teacher_email:
                student_data_map[row.id]["teachers"].add(
                    f"{row.teacher_name} ({row.teacher_email})"
                )

        # 🔥 組裝錯誤報告資料（和 cron.py 一樣的邏輯）
        students_with_errors = []
        for error_row in student_errors:
            student_data = student_data_map.get(error_row.student_id)
            if student_data:
                students_with_errors.append(
                    {
                        "student_id": error_row.student_id,
                        "student_name": student_data["name"],
                        "student_email": student_data["email"] or "（無 Email）",
                        "classrooms": ", ".join(student_data["classrooms"]) or "（無班級）",
                        "teachers": ", ".join(student_data["teachers"]) or "（無老師）",
                        "error_count": error_row.error_count,
                        "error_types": error_row.error_types,
                    }
                )

        # 驗證結果
        assert len(students_with_errors) == 3

        # 驗證學生A的錯誤報告
        student_a_error = next(
            s for s in students_with_errors if s["student_id"] == data["student1"].id
        )
        assert student_a_error["student_name"] == "學生A"
        assert student_a_error["student_email"] == "studentA@test.com"
        assert student_a_error["classrooms"] == "一年一班"
        assert "王老師 (teacher1@test.com)" in student_a_error["teachers"]
        assert student_a_error["error_count"] == 5

        # 驗證學生B的錯誤報告（多個班級）
        student_b_error = next(
            s for s in students_with_errors if s["student_id"] == data["student2"].id
        )
        assert "一年一班" in student_b_error["classrooms"]
        assert "一年二班" in student_b_error["classrooms"]

        # 驗證學生C的錯誤報告（沒有 Email 和班級）
        student_c_error = next(
            s for s in students_with_errors if s["student_id"] == data["student3"].id
        )
        assert student_c_error["student_email"] == "（無 Email）"
        assert student_c_error["classrooms"] == "（無班級）"
        assert student_c_error["teachers"] == "（無老師）"

    def test_classroom_student_model_exists(self):
        """測試 ClassroomStudent 模型存在（防止 import 錯誤）"""
        # 這個測試確保模型名稱正確
        from models import ClassroomStudent

        # 驗證表名
        assert ClassroomStudent.__tablename__ == "classroom_students"

        # 驗證有正確的欄位
        assert hasattr(ClassroomStudent, "student_id")
        assert hasattr(ClassroomStudent, "classroom_id")
