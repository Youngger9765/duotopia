"""
基礎測試：驗證雙體系模型的核心功能
"""
import pytest
from sqlalchemy.orm import Session
from models_v2 import (
    InstitutionalClassroom, IndividualClassroom,
    InstitutionalStudent, IndividualStudent
)


def test_create_institutional_classroom(db: Session):
    """測試創建機構教室"""
    classroom = InstitutionalClassroom(
        name="數學教室 301",
        grade_level="國小三年級",
        school_id="test_school_id",
        room_number="301",
        capacity=30
    )
    
    db.add(classroom)
    db.commit()
    
    assert classroom.id is not None
    assert classroom.type == "institutional"
    assert classroom.school_id == "test_school_id"


def test_create_individual_classroom(db: Session):
    """測試創建個體戶教室"""
    classroom = IndividualClassroom(
        name="Amy 的英語小班",
        grade_level="國小",
        teacher_id="test_teacher_id",
        location="線上授課",
        pricing=800,
        max_students=5
    )
    
    db.add(classroom)
    db.commit()
    
    assert classroom.id is not None
    assert classroom.type == "individual"
    assert classroom.teacher_id == "test_teacher_id"
    assert classroom.pricing == 800


def test_validate_institutional_classroom_requires_school():
    """測試機構教室必須有學校"""
    with pytest.raises(ValueError, match="機構教室必須指定學校"):
        classroom = InstitutionalClassroom(
            name="測試教室",
            school_id=None
        )


def test_validate_individual_classroom_requires_teacher():
    """測試個體戶教室必須有教師"""
    with pytest.raises(ValueError, match="個體戶教室必須指定教師"):
        classroom = IndividualClassroom(
            name="測試教室",
            teacher_id=None
        )