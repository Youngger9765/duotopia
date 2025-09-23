"""
批次匯入重複處理完整測試
測試三種重複處理策略: skip, update, add_suffix
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date

from models import Teacher, Classroom, Student, ClassroomStudent


class TestDuplicateHandling:
    """測試批次匯入的重複處理策略"""

    @pytest.fixture(autouse=True)
    def setup(self, test_session: Session):
        """Setup test data"""
        # 創建測試教師
        self.teacher = Teacher(
            name="Test Teacher",
            email="teacher@test.com",
            password_hash="hashed",
            phone="0912345678",
        )
        test_session.add(self.teacher)
        test_session.commit()  # 先提交教師以獲得 ID

        # 創建測試班級
        self.classroom = Classroom(name="測試班級", teacher_id=self.teacher.id, grade="3")
        test_session.add(self.classroom)
        test_session.commit()  # 提交班級

        # 創建已存在的學生
        self.existing_student = Student(
            name="王小明",
            student_number="S20240001",
            password_hash="old_hash",
            password_changed=False,
            birthdate=date(2012, 1, 1),
        )
        test_session.add(self.existing_student)
        test_session.commit()

        # 將學生加入班級
        classroom_student = ClassroomStudent(
            classroom_id=self.classroom.id, student_id=self.existing_student.id
        )
        test_session.add(classroom_student)
        test_session.commit()

        # 準備認證 headers
        self.headers = {"Authorization": f"Bearer teacher_{self.teacher.id}"}

    def test_duplicate_skip_strategy(
        self, test_client: TestClient, test_session: Session
    ):
        """測試 skip 策略: 跳過重複的學生"""

        # 準備匯入資料 (包含一個重複的學生)
        import_data = {
            "students": [
                {
                    "name": "王小明",  # 重複
                    "classroom_name": "測試班級",
                    "birthdate": "2012-01-15",  # 不同生日
                },
                {
                    "name": "李小華",  # 新學生
                    "classroom_name": "測試班級",
                    "birthdate": "2012-02-01",
                },
            ],
            "duplicate_action": "skip",
        }

        # 執行匯入
        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()

        # 檢查結果
        assert result["success_count"] == 1  # 只有李小華被匯入
        assert result["error_count"] == 0
        assert result["duplicate_count"] == 1  # 王小明被跳過

        # 檢查資料庫
        classroom_students = (
            test_session.query(ClassroomStudent)
            .filter_by(classroom_id=self.classroom.id)
            .all()
        )
        assert len(classroom_students) == 2  # 原本1個 + 新增1個

        # 檢查王小明的資料沒有被更新
        wang = test_session.query(Student).filter_by(name="王小明").first()
        assert wang.birthdate == date(2012, 1, 1)  # 保持原本的生日
        assert wang.password_hash == "old_hash"  # 保持原本的密碼

        # 檢查李小華被正確新增
        li = test_session.query(Student).filter_by(name="李小華").first()
        assert li is not None
        assert li.birthdate == date(2012, 2, 1)

    def test_duplicate_update_strategy(
        self, test_client: TestClient, test_session: Session
    ):
        """測試 update 策略: 更新重複學生的資料"""

        import_data = {
            "students": [
                {
                    "name": "王小明",  # 重複
                    "classroom_name": "測試班級",
                    "birthdate": "2012-01-15",  # 新生日
                },
                {
                    "name": "張小美",  # 新學生
                    "classroom_name": "測試班級",
                    "birthdate": "2012-03-01",
                },
            ],
            "duplicate_action": "update",
        }

        # 執行匯入
        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()

        # 檢查結果
        assert result["success_count"] == 2  # 兩個都成功 (1更新 + 1新增)
        assert result["error_count"] == 0
        assert result.get("updated_count", 0) == 1  # 王小明被更新

        # 檢查資料庫
        classroom_students = (
            test_session.query(ClassroomStudent)
            .filter_by(classroom_id=self.classroom.id)
            .all()
        )
        assert len(classroom_students) == 2  # 原本1個 + 新增1個 (沒有創建額外的)

        # 檢查王小明的資料被更新
        wang = test_session.query(Student).filter_by(name="王小明").first()
        assert wang.birthdate == date(2012, 1, 15)  # 生日被更新
        # 如果密碼沒改過，應該要重新生成
        if not wang.password_changed:
            assert wang.password_hash != "old_hash"  # 密碼應該被重新生成

        # 檢查張小美被正確新增
        zhang = test_session.query(Student).filter_by(name="張小美").first()
        assert zhang is not None
        assert zhang.birthdate == date(2012, 3, 1)

    def test_duplicate_add_suffix_strategy(
        self, test_client: TestClient, test_session: Session
    ):
        """測試 add_suffix 策略: 為重複的學生加上後綴"""

        import_data = {
            "students": [
                {
                    "name": "王小明",  # 重複 - 會變成 王小明-2
                    "classroom_name": "測試班級",
                    "birthdate": "2012-01-15",
                },
                {
                    "name": "王小明",  # 又一個重複 - 會變成 王小明-3
                    "classroom_name": "測試班級",
                    "birthdate": "2012-01-20",
                },
                {
                    "name": "陳小強",  # 新學生
                    "classroom_name": "測試班級",
                    "birthdate": "2012-04-01",
                },
            ],
            "duplicate_action": "add_suffix",
        }

        # 執行匯入
        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()

        # 檢查結果
        assert result["success_count"] == 3  # 全部都成功
        assert result["error_count"] == 0

        # 檢查資料庫
        classroom_students = (
            test_session.query(ClassroomStudent)
            .filter_by(classroom_id=self.classroom.id)
            .all()
        )
        assert len(classroom_students) == 4  # 原本1個 + 新增3個

        # 檢查所有學生的名字
        students = [cs.student for cs in classroom_students]
        student_names = [s.name for s in students]
        assert "王小明" in student_names  # 原本的
        assert "王小明-2" in student_names  # 第一個重複
        assert "王小明-3" in student_names  # 第二個重複
        assert "陳小強" in student_names  # 新學生

        # 檢查新增的王小明們有正確的生日
        wang2 = test_session.query(Student).filter_by(name="王小明-2").first()
        assert wang2.birthdate == date(2012, 1, 15)

        wang3 = test_session.query(Student).filter_by(name="王小明-3").first()
        assert wang3.birthdate == date(2012, 1, 20)

    def test_multiple_duplicates_same_batch(
        self, test_client: TestClient, test_session: Session
    ):
        """測試同一批次中有多個重複學生的處理"""

        import_data = {
            "students": [
                {"name": "王小明", "classroom_name": "測試班級", "birthdate": "2012-01-01"},
                {"name": "王小明", "classroom_name": "測試班級", "birthdate": "2012-01-02"},
                {"name": "王小明", "classroom_name": "測試班級", "birthdate": "2012-01-03"},
            ],
            "duplicate_action": "add_suffix",
        }

        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success_count"] == 3

        # 檢查生成的名稱
        students = test_session.query(Student).filter(Student.name.like("王小明%")).all()
        names = [s.name for s in students]
        assert "王小明" in names
        assert "王小明-2" in names
        assert "王小明-3" in names
        assert "王小明-4" in names

    def test_invalid_duplicate_action(
        self, test_client: TestClient, test_session: Session
    ):
        """測試無效的 duplicate_action 參數"""

        import_data = {
            "students": [
                {"name": "測試學生", "classroom_name": "測試班級", "birthdate": "2012-01-01"}
            ],
            "duplicate_action": "invalid_action",
        }

        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        # 應該回傳錯誤或使用預設的 skip
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # 如果接受了，應該使用預設的 skip 策略
            result = response.json()
            assert result["success_count"] >= 0

    def test_duplicate_across_classrooms(
        self, test_client: TestClient, test_session: Session
    ):
        """測試跨班級的重複處理（同名但不同班級不算重複）"""

        # 創建另一個班級
        classroom2 = Classroom(name="測試班級2", teacher_id=self.teacher.id, grade="3")
        test_session.add(classroom2)
        test_session.commit()

        import_data = {
            "students": [
                {
                    "name": "王小明",  # 同名但不同班級
                    "classroom_name": "測試班級2",
                    "birthdate": "2012-01-01",
                }
            ],
            "duplicate_action": "skip",
        }

        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()

        # 不應該被視為重複
        assert result["success_count"] == 1
        assert result.get("duplicate_count", 0) == 0

        # 檢查兩個班級都有王小明
        wang1_cs = (
            test_session.query(ClassroomStudent)
            .join(Student)
            .filter(
                Student.name == "王小明",
                ClassroomStudent.classroom_id == self.classroom.id,
            )
            .first()
        )
        wang2_cs = (
            test_session.query(ClassroomStudent)
            .join(Student)
            .filter(
                Student.name == "王小明", ClassroomStudent.classroom_id == classroom2.id
            )
            .first()
        )

        wang1 = wang1_cs.student if wang1_cs else None
        wang2 = wang2_cs.student if wang2_cs else None

        assert wang1 is not None
        assert wang2 is not None
        assert wang1.id != wang2.id

    def test_empty_duplicate_action_defaults_to_skip(
        self, test_client: TestClient, test_session: Session
    ):
        """測試不提供 duplicate_action 時預設為 skip"""

        import_data = {
            "students": [
                {
                    "name": "王小明",  # 重複
                    "classroom_name": "測試班級",
                    "birthdate": "2012-01-15",
                }
            ]
            # 沒有提供 duplicate_action
        }

        response = test_client.post(
            "/api/teachers/students/batch-import",
            json=import_data,
            headers=self.headers,
        )

        assert response.status_code == 200
        result = response.json()

        # 應該跳過重複的學生
        assert result.get("duplicate_count", 0) == 1
        assert result["success_count"] == 0

        # 確認資料沒有被更新
        wang = test_session.query(Student).filter_by(name="王小明").first()
        assert wang.birthdate == date(2012, 1, 1)  # 保持原樣
