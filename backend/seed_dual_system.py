#!/usr/bin/env python3
"""
雙體系 Seed 資料
建立機構體系和個體戶體系的測試資料
"""
from database import SessionLocal, engine
from models_dual_system import (
    DualBase, DualUser, DualSchool,
    InstitutionalClassroom, IndividualClassroom,
    InstitutionalStudent, IndividualStudent,
    InstitutionalCourse, IndividualCourse,
    InstitutionalLesson, IndividualLesson,
    InstitutionalEnrollment, IndividualEnrollment,
    UserRole, DifficultyLevel, ActivityType
)
from auth import get_password_hash
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import text

# 創建所有表
DualBase.metadata.create_all(bind=engine)

def create_dual_system_seed_data():
    db = SessionLocal()
    
    try:
        print("=== 開始建立雙體系測試資料 ===\n")
        
        # 清理現有資料
        print("清理現有資料...")
        # 先刪除關聯表
        db.query(InstitutionalEnrollment).delete()
        db.query(IndividualEnrollment).delete()
        db.query(InstitutionalLesson).delete()
        db.query(IndividualLesson).delete()
        db.query(InstitutionalCourse).delete()
        db.query(IndividualCourse).delete()
        # 刪除學生（包括base table）
        db.query(InstitutionalStudent).delete()
        db.query(IndividualStudent).delete()
        db.execute(text("DELETE FROM dual_student_base"))  # 直接清理base table
        # 刪除教室和學校
        db.query(InstitutionalClassroom).delete()
        db.query(IndividualClassroom).delete()
        db.query(DualSchool).delete()
        db.query(DualUser).delete()
        db.commit()
        print("✓ 資料清理完成\n")
        
        # 1. 創建用戶
        print("1. 創建用戶...")
        
        # 機構管理員
        inst_admin = DualUser(
            email="admin@institution.com",
            full_name="機構管理員",
            role=UserRole.ADMIN,
            phone="02-12345678",
            hashed_password=get_password_hash("test123"),
            is_individual_teacher=False,
            is_institutional_admin=True,
            current_role_context="institutional"
        )
        db.add(inst_admin)
        
        # 個體戶教師
        individual_teacher = DualUser(
            email="teacher@individual.com",
            full_name="張老師",
            role=UserRole.TEACHER,
            phone="0912-345-678",
            hashed_password=get_password_hash("test123"),
            is_individual_teacher=True,
            is_institutional_admin=False,
            current_role_context="individual"
        )
        db.add(individual_teacher)
        
        # 混合型用戶
        hybrid_user = DualUser(
            email="hybrid@test.com",
            full_name="李老師",
            role=UserRole.TEACHER,
            phone="0923-456-789",
            hashed_password=get_password_hash("test123"),
            is_individual_teacher=True,
            is_institutional_admin=True,
            current_role_context="default"
        )
        db.add(hybrid_user)
        
        db.commit()
        print("✓ 用戶創建完成")
        
        # 2. 創建學校（機構體系）
        print("\n2. 創建學校...")
        schools = []
        school_data = [
            {"name": "台北市立大安國小", "code": "DAAN001", "address": "台北市大安區信義路三段"},
            {"name": "新北市立板橋國中", "code": "BANQIAO001", "address": "新北市板橋區文化路"},
            {"name": "桃園市私立英才補習班", "code": "YINGCAI001", "address": "桃園市中壢區中山路"}
        ]
        
        for data in school_data:
            school = DualSchool(**data)
            schools.append(school)
            db.add(school)
        
        db.commit()
        print(f"✓ 創建了 {len(schools)} 所學校")
        
        # 3. 創建機構教室
        print("\n3. 創建機構教室...")
        inst_classrooms = []
        for school in schools:
            for i in range(3):
                classroom = InstitutionalClassroom(
                    name=f"{school.name[:3]}{i+1}年{chr(65+i)}班",
                    grade_level=f"國小{i+1}年級",
                    school_id=school.id,
                    room_number=f"{i+1}0{i+1}",
                    capacity=30
                )
                inst_classrooms.append(classroom)
                db.add(classroom)
        
        db.commit()
        print(f"✓ 創建了 {len(inst_classrooms)} 個機構教室")
        
        # 4. 創建個體戶教室
        print("\n4. 創建個體戶教室...")
        ind_classrooms = []
        classroom_data = [
            {"name": "Amy的英語會話班", "teacher": individual_teacher, "pricing": 800},
            {"name": "數學思維訓練班", "teacher": individual_teacher, "pricing": 1000},
            {"name": "創意寫作工作坊", "teacher": individual_teacher, "pricing": 600},
            {"name": "科學實驗小教室", "teacher": hybrid_user, "pricing": 1200},
            {"name": "程式設計入門班", "teacher": hybrid_user, "pricing": 1500}
        ]
        
        for i, data in enumerate(classroom_data):
            classroom = IndividualClassroom(
                name=data["name"],
                grade_level="國小3-6年級",
                teacher_id=data["teacher"].id,
                location="線上授課" if i % 2 == 0 else "台北市大安區",
                pricing=data["pricing"],
                max_students=random.choice([5, 8, 10])
            )
            ind_classrooms.append(classroom)
            db.add(classroom)
        
        db.commit()
        print(f"✓ 創建了 {len(ind_classrooms)} 個個體戶教室")
        
        # 5. 創建機構學生
        print("\n5. 創建機構學生...")
        inst_students = []
        for i in range(50):
            school = random.choice(schools)
            student = InstitutionalStudent(
                full_name=f"學生{i+1:03d}",
                email=f"student{i+1:03d}@school.com",
                birth_date=f"201{random.randint(0,5)}0{random.randint(1,9)}{random.randint(10,28)}",
                school_id=school.id,
                student_id=f"STU{datetime.now().year}{i+1:04d}",
                parent_phone=f"09{random.randint(10000000, 99999999)}",
                emergency_contact=f"家長{i+1} 09{random.randint(10000000, 99999999)}"
            )
            inst_students.append(student)
            db.add(student)
        
        db.commit()
        print(f"✓ 創建了 {len(inst_students)} 個機構學生")
        
        # 6. 創建個體戶學生
        print("\n6. 創建個體戶學生...")
        ind_students = []
        referral_sources = ["朋友介紹", "網路搜尋", "社群媒體", "家長推薦", "學生介紹"]
        
        for i in range(20):
            student = IndividualStudent(
                full_name=f"個人學生{i+1:02d}",
                email=f"ind_student{i+1:02d}@gmail.com",
                birth_date=f"201{random.randint(2,6)}0{random.randint(1,9)}{random.randint(10,28)}",
                referred_by=random.choice(referral_sources),
                learning_goals=random.choice([
                    "提升英語口說能力",
                    "加強數學運算",
                    "培養寫作興趣",
                    "準備升學考試",
                    "培養程式邏輯思維"
                ]),
                preferred_schedule={
                    "weekdays": random.sample(["週一", "週二", "週三", "週四", "週五"], 2),
                    "time": random.choice(["下午4-6點", "晚上7-9點", "週末上午", "週末下午"])
                }
            )
            ind_students.append(student)
            db.add(student)
        
        db.commit()
        print(f"✓ 創建了 {len(ind_students)} 個個體戶學生")
        
        # 7. 註冊學生到教室
        print("\n7. 註冊學生到教室...")
        
        # 機構學生註冊
        for student in inst_students:
            # 找到同學校的教室
            school_classrooms = [c for c in inst_classrooms if c.school_id == student.school_id]
            if school_classrooms:
                classroom = random.choice(school_classrooms)
                enrollment = InstitutionalEnrollment(
                    student_id=student.id,
                    classroom_id=classroom.id
                )
                db.add(enrollment)
        
        # 個體戶學生註冊
        for student in ind_students:
            # 隨機選1-2個教室
            num_classes = random.randint(1, 2)
            selected_classrooms = random.sample(ind_classrooms, min(num_classes, len(ind_classrooms)))
            
            for classroom in selected_classrooms:
                enrollment = IndividualEnrollment(
                    student_id=student.id,
                    classroom_id=classroom.id,
                    payment_status=random.choice(["paid", "pending", "overdue"])
                )
                db.add(enrollment)
        
        db.commit()
        print("✓ 學生註冊完成")
        
        # 8. 創建課程
        print("\n8. 創建課程...")
        
        # 機構課程
        inst_courses = []
        course_templates = [
            {"title": "標準英語課程 Level 1", "description": "適合初學者的英語課程"},
            {"title": "數學基礎班", "description": "國小數學基礎訓練"},
            {"title": "自然科學探索", "description": "有趣的科學實驗課程"}
        ]
        
        for school in schools:
            for template in course_templates:
                course = InstitutionalCourse(
                    title=f"{school.name[:3]} - {template['title']}",
                    description=template['description'],
                    school_id=school.id,
                    difficulty_level=random.choice([DifficultyLevel.A1, DifficultyLevel.A2]),
                    is_template=True,
                    shared_with_teachers=[inst_admin.id, hybrid_user.id]
                )
                inst_courses.append(course)
                db.add(course)
        
        # 個體戶課程 - 公版課程
        ind_courses = []
        public_course_data = [
            {"title": "基礎英語會話", "description": "適合初學者的英語口說課程", "price": 800},
            {"title": "進階英語會話", "description": "提升英語流利度和表達能力", "price": 1000},
            {"title": "商務英語會話", "description": "針對職場需求的英語課程", "price": 1500},
            {"title": "數學基礎班", "description": "建立扎實的數學基礎", "price": 800},
            {"title": "奧數培訓班", "description": "培養數學競賽能力", "price": 1200},
            {"title": "創意寫作營", "description": "激發寫作潛能", "price": 1000}
        ]
        
        # 創建公版課程（不屬於任何教室）
        for data in public_course_data:
            course = IndividualCourse(
                title=data["title"],
                description=data["description"],
                teacher_id=individual_teacher.id,
                difficulty_level=random.choice([DifficultyLevel.A1, DifficultyLevel.A2, DifficultyLevel.B1]),
                is_public=True,  # 公版課程
                classroom_id=None,  # 不屬於任何教室
                custom_materials=True,
                pricing_per_lesson=data["price"]
            )
            ind_courses.append(course)
            db.add(course)
        
        # 創建教室專屬課程（每個教室一個）
        for i, classroom in enumerate(ind_classrooms[:3]):  # 只給前3個教室創建課程
            course = IndividualCourse(
                title=f"{classroom.name} - 專屬課程",
                description=f"為{classroom.name}量身定制的課程",
                teacher_id=classroom.teacher_id,
                classroom_id=classroom.id,
                difficulty_level=DifficultyLevel.B1,
                is_public=False,  # 非公版
                custom_materials=True,
                pricing_per_lesson=classroom.pricing
            )
            ind_courses.append(course)
            db.add(course)
        
        db.commit()
        print(f"✓ 創建了 {len(inst_courses)} 個機構課程和 {len(ind_courses)} 個個體戶課程")
        
        # 9. 創建課時
        print("\n9. 創建課時...")
        
        # 為每個課程創建5個課時
        activity_types = list(ActivityType)
        
        for course in inst_courses + ind_courses:
            for i in range(5):
                if isinstance(course, InstitutionalCourse):
                    lesson = InstitutionalLesson(
                        course_id=course.id,
                        lesson_number=i + 1,
                        title=f"第{i+1}課：{course.title}",
                        activity_type=random.choice(activity_types),
                        content={
                            "instructions": "課程說明...",
                            "materials": ["教材1", "教材2"],
                            "objectives": ["學習目標1", "學習目標2"]
                        },
                        time_limit_minutes=random.choice([30, 45, 60])
                    )
                else:
                    lesson = IndividualLesson(
                        course_id=course.id,
                        lesson_number=i + 1,
                        title=f"第{i+1}課：個人化教學",
                        activity_type=random.choice(activity_types),
                        content={
                            "instructions": "客製化課程內容...",
                            "personalized": True,
                            "adapt_to_student": True
                        },
                        time_limit_minutes=random.choice([45, 60, 90])
                    )
                db.add(lesson)
        
        db.commit()
        print("✓ 課時創建完成")
        
        # 10. 顯示統計資訊
        print("\n=== 雙體系測試資料創建完成 ===")
        print(f"""
統計資訊：
- 用戶數：3（機構管理員1、個體戶教師1、混合型1）
- 學校數：{len(schools)}
- 機構教室數：{len(inst_classrooms)}
- 個體戶教室數：{len(ind_classrooms)}
- 機構學生數：{len(inst_students)}
- 個體戶學生數：{len(ind_students)}
- 機構課程數：{len(inst_courses)}
- 個體戶課程數：{len(ind_courses)}

測試帳號：
1. 機構管理員：admin@institution.com / test123
2. 個體戶教師：teacher@individual.com / test123
3. 混合型用戶：hybrid@test.com / test123
        """)
        
    except Exception as e:
        print(f"錯誤：{e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_dual_system_seed_data()