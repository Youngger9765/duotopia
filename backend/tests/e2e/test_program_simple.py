"""
測試簡化版 Program 模型
- Program 必須在特定班級內創建（classroom_id + teacher_id）
- Program 直接關聯到 Classroom 和 Teacher
"""

import pytest
from sqlalchemy.orm import Session
from models import Teacher, Classroom, Program, ProgramLevel
from auth import get_password_hash
from datetime import datetime


class TestSimplifiedProgramModel:
    """測試簡化版 Program 模型"""

    def test_create_program_in_classroom(self, db: Session):
        """測試在班級內創建課程"""
        # 建立教師
        teacher = Teacher(
            name="測試老師",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.flush()

        # 建立班級
        classroom = Classroom(
            name="測試班級",
            description="測試用班級",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        # 在班級內創建課程
        program = Program(
            name="英語基礎課程",
            description="這是基礎英語課程",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            estimated_hours=20,
            is_active=True,
        )
        db.add(program)
        db.commit()

        # 驗證課程創建成功
        assert program.id is not None
        assert program.name == "英語基礎課程"
        assert program.teacher_id == teacher.id
        assert program.classroom_id == classroom.id
        assert program.is_active is True

        # 驗證關聯關係
        assert program.teacher == teacher
        assert program.classroom == classroom

    def test_program_classroom_relationship(self, db: Session):
        """測試 Program 與 Classroom 的直接關聯"""
        # 建立教師
        teacher = Teacher(
            name="關聯測試老師",
            email="relation@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.flush()

        # 建立班級
        classroom = Classroom(
            name="關聯測試班級",
            description="測試關聯的班級",
            level=ProgramLevel.B1,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        # 在班級內創建多個課程
        programs = []
        for i in range(3):
            program = Program(
                name=f"課程 {i+1}",
                description=f"第 {i+1} 個課程",
                level=ProgramLevel.B1,
                teacher_id=teacher.id,
                classroom_id=classroom.id,
                estimated_hours=15 + i * 5,
                is_active=True,
            )
            programs.append(program)
            db.add(program)

        db.commit()

        # 驗證班級包含所有課程
        db.refresh(classroom)
        assert len(classroom.programs) == 3

        # 驗證每個課程都關聯到正確的班級
        for program in programs:
            db.refresh(program)
            assert program.classroom == classroom
            assert program.classroom_id == classroom.id

    def test_program_teacher_relationship(self, db: Session):
        """測試 Program 與 Teacher 的關聯"""
        # 建立教師
        teacher = Teacher(
            name="課程教師",
            email="program.teacher@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.flush()

        # 建立兩個班級
        classroom1 = Classroom(
            name="班級1",
            description="第一個班級",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            is_active=True,
        )
        classroom2 = Classroom(
            name="班級2",
            description="第二個班級",
            level=ProgramLevel.A2,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add_all([classroom1, classroom2])
        db.flush()

        # 在不同班級創建課程
        program1 = Program(
            name="班級1課程",
            description="班級1的專屬課程",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            classroom_id=classroom1.id,
            estimated_hours=15,
            is_active=True,
        )

        program2 = Program(
            name="班級2課程",
            description="班級2的專屬課程",
            level=ProgramLevel.A2,
            teacher_id=teacher.id,
            classroom_id=classroom2.id,
            estimated_hours=20,
            is_active=True,
        )

        db.add_all([program1, program2])
        db.commit()

        # 驗證教師包含所有課程
        db.refresh(teacher)
        assert len(teacher.programs) == 2

        # 驗證課程正確關聯到教師
        assert program1.teacher == teacher
        assert program2.teacher == teacher
        assert program1 in teacher.programs
        assert program2 in teacher.programs

    def test_program_must_have_classroom_and_teacher(self, db: Session):
        """測試 Program 必須有 classroom_id 和 teacher_id"""
        with pytest.raises(Exception):  # 應該會因為外鍵約束失敗
            program = Program(
                name="無效課程",
                description="缺少必要的外鍵",
                level=ProgramLevel.A1,
                # 缺少 teacher_id 和 classroom_id
                estimated_hours=10,
                is_active=True,
            )
            db.add(program)
            db.commit()

    def test_classroom_cascade_delete_programs(self, db: Session):
        """測試班級刪除時課程也會被刪除（cascade）"""
        # 建立教師
        teacher = Teacher(
            name="級聯測試老師",
            email="cascade@example.com",
            password_hash=get_password_hash("password123"),
            is_active=True,
            is_demo=False,
        )
        db.add(teacher)
        db.flush()

        # 建立班級
        classroom = Classroom(
            name="即將被刪除的班級",
            description="測試級聯刪除",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(classroom)
        db.flush()

        # 建立課程
        program = Program(
            name="即將被刪除的課程",
            description="測試級聯刪除的課程",
            level=ProgramLevel.A1,
            teacher_id=teacher.id,
            classroom_id=classroom.id,
            estimated_hours=10,
            is_active=True,
        )
        db.add(program)
        db.commit()

        program_id = program.id

        # 刪除班級
        db.delete(classroom)
        db.commit()

        # 驗證課程也被刪除
        deleted_program = db.query(Program).filter(Program.id == program_id).first()
        assert deleted_program is None
