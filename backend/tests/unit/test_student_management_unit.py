"""
學生管理功能單元測試
測試學生的建立、編輯、密碼管理等核心功能
"""
import pytest
from datetime import datetime, date
from sqlalchemy.orm import Session
import pandas as pd
from io import BytesIO

from models import User, IndividualTeacher, Student, Class, ClassStudentMapping
from schemas import StudentCreate, StudentUpdate
from auth import get_password_hash, verify_password


class TestStudentCreation:
    """學生建立功能測試"""
    
    @pytest.fixture
    def teacher(self, db: Session):
        """建立測試教師"""
        user = User(
            email="teacher@test.com",
            hashed_password=get_password_hash("password123"),
            is_active=True
        )
        db.add(user)
        db.commit()
        
        teacher = IndividualTeacher(
            user_id=user.id,
            name="Test Teacher"
        )
        db.add(teacher)
        db.commit()
        return teacher
    
    def test_create_student_basic(self, db: Session, teacher):
        """測試基本學生建立"""
        student_data = StudentCreate(
            name="張小明",
            birth_date=date(2010, 1, 1),
            email=None,
            referrer=None
        )
        
        # 生成預設密碼（生日）
        default_password = student_data.birth_date.strftime("%Y%m%d")
        
        student = Student(
            name=student_data.name,
            birth_date=student_data.birth_date,
            email=student_data.email,
            referrer=student_data.referrer,
            teacher_id=teacher.user_id,
            password_hash=get_password_hash(default_password),
            password_status="default"
        )
        db.add(student)
        db.commit()
        
        assert student.id is not None
        assert student.name == "張小明"
        assert student.birth_date == date(2010, 1, 1)
        assert student.password_status == "default"
        assert verify_password("20100101", student.password_hash)
    
    def test_create_student_with_email(self, db: Session, teacher):
        """測試建立有 Email 的學生"""
        student = Student(
            name="李小華",
            birth_date=date(2010, 2, 15),
            email="xiaohua@test.com",
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100215"),
            password_status="default"
        )
        db.add(student)
        db.commit()
        
        assert student.email == "xiaohua@test.com"
    
    def test_create_student_with_referrer(self, db: Session, teacher):
        """測試建立有推薦人的學生"""
        student = Student(
            name="王小美",
            birth_date=date(2010, 3, 20),
            referrer="家長介紹",
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100320"),
            password_status="default"
        )
        db.add(student)
        db.commit()
        
        assert student.referrer == "家長介紹"
    
    def test_student_unique_constraint(self, db: Session, teacher):
        """測試學生唯一性約束"""
        # 建立第一個學生
        student1 = Student(
            name="重複學生",
            email="duplicate@test.com",
            birth_date=date(2010, 1, 1),
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100101")
        )
        db.add(student1)
        db.commit()
        
        # 同一教師下，相同 email 的學生應該要被檢查
        existing = db.query(Student).filter(
            Student.email == "duplicate@test.com",
            Student.teacher_id == teacher.user_id
        ).first()
        
        assert existing is not None
        
        # 但不同教師可以有相同 email 的學生
        user2 = User(
            email="teacher2@test.com",
            hashed_password=get_password_hash("password123")
        )
        db.add(user2)
        db.commit()
        
        teacher2 = IndividualTeacher(
            user_id=user2.id,
            name="Teacher 2"
        )
        db.add(teacher2)
        db.commit()
        
        student2 = Student(
            name="不同老師的學生",
            email="duplicate@test.com",
            birth_date=date(2010, 1, 1),
            teacher_id=teacher2.user_id,
            password_hash=get_password_hash("20100101")
        )
        db.add(student2)
        db.commit()
        
        assert student2.id is not None


class TestStudentPasswordManagement:
    """學生密碼管理功能測試"""
    
    @pytest.fixture
    def student(self, db: Session, teacher):
        """建立測試學生"""
        student = Student(
            name="測試學生",
            birth_date=date(2010, 1, 1),
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100101"),
            password_status="default"
        )
        db.add(student)
        db.commit()
        return student
    
    def test_change_student_password(self, db: Session, student):
        """測試修改學生密碼"""
        old_password = "20100101"
        new_password = "newpass123"
        
        # 驗證舊密碼
        assert verify_password(old_password, student.password_hash)
        
        # 更新密碼
        student.password_hash = get_password_hash(new_password)
        student.password_status = "custom"
        db.commit()
        
        # 驗證新密碼
        updated_student = db.query(Student).filter(Student.id == student.id).first()
        assert verify_password(new_password, updated_student.password_hash)
        assert updated_student.password_status == "custom"
        assert not verify_password(old_password, updated_student.password_hash)
    
    def test_reset_student_password(self, db: Session, student):
        """測試重置學生密碼"""
        # 先設定自訂密碼
        student.password_hash = get_password_hash("custom123")
        student.password_status = "custom"
        db.commit()
        
        # 重置為預設密碼（生日）
        default_password = student.birth_date.strftime("%Y%m%d")
        student.password_hash = get_password_hash(default_password)
        student.password_status = "default"
        db.commit()
        
        # 驗證重置結果
        reset_student = db.query(Student).filter(Student.id == student.id).first()
        assert verify_password("20100101", reset_student.password_hash)
        assert reset_student.password_status == "default"
    
    def test_password_status_tracking(self, db: Session, teacher):
        """測試密碼狀態追蹤"""
        # 建立使用預設密碼的學生
        student1 = Student(
            name="預設密碼學生",
            birth_date=date(2010, 1, 1),
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100101"),
            password_status="default"
        )
        db.add(student1)
        
        # 建立使用自訂密碼的學生
        student2 = Student(
            name="自訂密碼學生",
            birth_date=date(2010, 2, 1),
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("mycustompass"),
            password_status="custom"
        )
        db.add(student2)
        db.commit()
        
        # 查詢不同密碼狀態的學生
        default_students = db.query(Student).filter(
            Student.teacher_id == teacher.user_id,
            Student.password_status == "default"
        ).all()
        
        custom_students = db.query(Student).filter(
            Student.teacher_id == teacher.user_id,
            Student.password_status == "custom"
        ).all()
        
        assert len(default_students) == 1
        assert len(custom_students) == 1
        assert default_students[0].name == "預設密碼學生"
        assert custom_students[0].name == "自訂密碼學生"


class TestBulkStudentImport:
    """批量匯入學生功能測試"""
    
    @pytest.fixture
    def sample_excel_data(self):
        """建立測試用的 Excel 資料"""
        data = {
            '姓名': ['張大明', '李小芳', '王小強'],
            '生日': ['2010-01-15', '2010-02-20', '2010-03-25'],
            'Email': ['daming@test.com', '', 'xiaoqiang@test.com'],
            '推薦人': ['家長A', '老師B', '']
        }
        df = pd.DataFrame(data)
        
        # 轉換為 Excel 位元組流
        output = BytesIO()
        df.to_excel(output, index=False)
        output.seek(0)
        return output
    
    def test_parse_excel_file(self, sample_excel_data):
        """測試解析 Excel 檔案"""
        df = pd.read_excel(sample_excel_data)
        
        assert len(df) == 3
        assert list(df.columns) == ['姓名', '生日', 'Email', '推薦人']
        assert df['姓名'].tolist() == ['張大明', '李小芳', '王小強']
    
    def test_validate_import_data(self, sample_excel_data):
        """測試驗證匯入資料"""
        df = pd.read_excel(sample_excel_data)
        
        errors = []
        for idx, row in df.iterrows():
            # 檢查必填欄位
            if pd.isna(row['姓名']) or row['姓名'] == '':
                errors.append(f"第 {idx+2} 行：姓名為必填")
            
            if pd.isna(row['生日']) or row['生日'] == '':
                errors.append(f"第 {idx+2} 行：生日為必填")
            
            # 檢查生日格式
            try:
                if not pd.isna(row['生日']):
                    pd.to_datetime(row['生日'])
            except:
                errors.append(f"第 {idx+2} 行：生日格式錯誤")
        
        assert len(errors) == 0
    
    def test_bulk_create_students(self, db: Session, teacher, sample_excel_data):
        """測試批量建立學生"""
        df = pd.read_excel(sample_excel_data)
        
        created_students = []
        for _, row in df.iterrows():
            # 處理日期
            birth_date = pd.to_datetime(row['生日']).date()
            default_password = birth_date.strftime("%Y%m%d")
            
            student = Student(
                name=row['姓名'],
                birth_date=birth_date,
                email=row['Email'] if not pd.isna(row['Email']) else None,
                referrer=row['推薦人'] if not pd.isna(row['推薦人']) else None,
                teacher_id=teacher.user_id,
                password_hash=get_password_hash(default_password),
                password_status="default"
            )
            db.add(student)
            created_students.append(student)
        
        db.commit()
        
        # 驗證建立結果
        assert len(created_students) == 3
        
        # 檢查每個學生
        student1 = db.query(Student).filter(Student.name == "張大明").first()
        assert student1 is not None
        assert student1.email == "daming@test.com"
        assert verify_password("20100115", student1.password_hash)
        
        student2 = db.query(Student).filter(Student.name == "李小芳").first()
        assert student2 is not None
        assert student2.email is None
        assert verify_password("20100220", student2.password_hash)


class TestStudentUpdate:
    """學生資料更新功能測試"""
    
    @pytest.fixture
    def student(self, db: Session, teacher):
        """建立測試學生"""
        student = Student(
            name="原始姓名",
            birth_date=date(2010, 1, 1),
            email="original@test.com",
            teacher_id=teacher.user_id,
            password_hash=get_password_hash("20100101")
        )
        db.add(student)
        db.commit()
        return student
    
    def test_update_student_info(self, db: Session, student):
        """測試更新學生資訊"""
        update_data = StudentUpdate(
            name="更新後姓名",
            email="updated@test.com",
            referrer="新推薦人"
        )
        
        # 更新資料
        if update_data.name:
            student.name = update_data.name
        if update_data.email:
            student.email = update_data.email
        if update_data.referrer:
            student.referrer = update_data.referrer
        
        db.commit()
        
        # 驗證更新結果
        updated = db.query(Student).filter(Student.id == student.id).first()
        assert updated.name == "更新後姓名"
        assert updated.email == "updated@test.com"
        assert updated.referrer == "新推薦人"
        # 生日不應該被更新
        assert updated.birth_date == date(2010, 1, 1)
    
    def test_soft_delete_student(self, db: Session, student):
        """測試軟刪除學生"""
        student_id = student.id
        
        # 軟刪除
        student.is_deleted = True
        student.deleted_at = datetime.utcnow()
        db.commit()
        
        # 確認被標記為刪除
        deleted_student = db.query(Student).filter(Student.id == student_id).first()
        assert deleted_student.is_deleted is True
        assert deleted_student.deleted_at is not None
        
        # 確認在一般查詢中不出現
        active_students = db.query(Student).filter(
            Student.teacher_id == student.teacher_id,
            Student.is_deleted == False
        ).all()
        assert deleted_student not in active_students
    
    def test_delete_student_with_class(self, db: Session, student, teacher):
        """測試刪除已分配班級的學生"""
        # 建立班級
        test_class = Class(
            name="測試班級",
            grade="國小三年級",
            capacity=30,
            teacher_id=teacher.user_id
        )
        db.add(test_class)
        db.commit()
        
        # 分配學生到班級
        mapping = ClassStudentMapping(
            class_id=test_class.id,
            student_id=student.id
        )
        db.add(mapping)
        db.commit()
        
        # 刪除學生前應該先移除班級關聯
        db.delete(mapping)
        db.commit()
        
        # 現在可以安全刪除學生
        student.is_deleted = True
        student.deleted_at = datetime.utcnow()
        db.commit()
        
        # 確認班級關聯已移除
        remaining_mapping = db.query(ClassStudentMapping).filter(
            ClassStudentMapping.student_id == student.id
        ).first()
        assert remaining_mapping is None