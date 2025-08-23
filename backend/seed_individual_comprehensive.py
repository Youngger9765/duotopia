#!/usr/bin/env python3
"""
為個體戶教師建立完整的測試資料
- 多個教室
- 多個學生 (不同年級)
- 多個課程
- 課程單元
- 教室課程關聯
"""
import sys
import os
import uuid
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal
from models import (
    User, Classroom, Student, ClassroomStudent, Course, Lesson, 
    ClassroomCourseMapping, DifficultyLevel, ActivityType
)

def seed_individual_comprehensive():
    db = SessionLocal()
    try:
        print("=== 個體戶教師綜合測試資料建立 ===\n")
        
        # 1. 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name} (ID: {teacher.id})")
        
        # 2. 建立更多教室
        print("\n📚 建立教室...")
        classrooms_data = [
            ("小學英語基礎班", "小學三年級"),
            ("小學英語進階班", "小學五年級"), 
            ("國中英語會話班", "國中一年級"),
            ("國中英語閱讀班", "國中二年級"),
            ("成人英語口說班", "成人")
        ]
        
        existing_classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).all()
        existing_names = [c.name for c in existing_classrooms]
        
        new_classrooms = []
        for name, grade in classrooms_data:
            if name not in existing_names:
                classroom = Classroom(
                    id=str(uuid.uuid4()),
                    name=name,
                    grade_level=grade,
                    teacher_id=teacher.id,
                    school_id=None
                )
                db.add(classroom)
                new_classrooms.append(classroom)
                print(f"  ✓ 建立教室: {name}")
        
        if new_classrooms:
            db.flush()
            print(f"✓ 新建立 {len(new_classrooms)} 個教室")
        else:
            print("✓ 所有教室已存在")
        
        # 重新獲取所有教室
        all_classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).all()
        
        # 3. 建立更多學生
        print("\n👥 建立學生...")
        students_data = [
            ("王小明", "wang.xiaoming@email.com", "20110315"),
            ("陳美麗", "chen.meili@email.com", "20120620"), 
            ("李志強", "li.zhiqiang@email.com", "20100908"),
            ("張雅婷", "zhang.yating@email.com", "20111205"),
            ("林俊傑", "lin.junjie@email.com", "20121018"),
            ("黃詩涵", "huang.shihan@email.com", "20130224"),
            ("吳承恩", "wu.chengen@email.com", "20091130"),
            ("周佳慧", "zhou.jiahui@email.com", "20120412"),
            ("劉建宏", "liu.jianhong@email.com", "20101225"),
            ("蔡雅琪", "cai.yaqi@email.com", "20130707"),
            ("謝志明", "xie.zhiming@email.com", "20080518"),  # 成人學生
            ("江美惠", "jiang.meihui@email.com", "20070903"),  # 成人學生
        ]
        
        existing_students = db.query(Student).filter(
            Student.email.in_([email for _, email, _ in students_data])
        ).all()
        existing_emails = [s.email for s in existing_students]
        
        new_students = []
        for name, email, birth_date in students_data:
            if email not in existing_emails:
                student = Student(
                    id=str(uuid.uuid4()),
                    full_name=name,
                    email=email,
                    birth_date=birth_date  # YYYYMMDD 格式
                )
                db.add(student)
                new_students.append(student)
                print(f"  ✓ 建立學生: {name}")
        
        if new_students:
            db.flush()
            print(f"✓ 新建立 {len(new_students)} 個學生")
        else:
            print("✓ 所有學生已存在")
        
        # 重新獲取所有學生
        all_students = db.query(Student).all()
        
        # 4. 將學生分配到教室
        print("\n🔗 分配學生到教室...")
        
        # 清除現有關聯（避免重複）
        existing_mappings = db.query(ClassroomStudent).join(Classroom).filter(
            Classroom.teacher_id == teacher.id
        ).all()
        
        if not existing_mappings:  # 只有在沒有現有關聯時才建立
            student_classroom_mappings = [
                # 小學英語基礎班 (年齡較小的學生)
                (all_students[0:3], all_classrooms[0] if len(all_classrooms) > 0 else None),
                # 小學英語進階班
                (all_students[3:6], all_classrooms[1] if len(all_classrooms) > 1 else None),
                # 國中英語會話班 
                (all_students[6:9], all_classrooms[2] if len(all_classrooms) > 2 else None),
                # 國中英語閱讀班
                (all_students[9:11], all_classrooms[3] if len(all_classrooms) > 3 else None),
                # 成人英語口說班
                (all_students[11:12], all_classrooms[4] if len(all_classrooms) > 4 else None),
            ]
            
            for students_group, classroom in student_classroom_mappings:
                if classroom and students_group:
                    for student in students_group:
                        if student:  # 確保學生存在
                            classroom_student = ClassroomStudent(
                                id=str(uuid.uuid4()),
                                classroom_id=classroom.id,
                                student_id=student.id
                            )
                            db.add(classroom_student)
                    print(f"  ✓ 分配 {len(students_group)} 個學生到 {classroom.name}")
            
            db.flush()
            print("✓ 學生教室分配完成")
        else:
            print("✓ 學生教室關聯已存在")
        
        # 5. 建立更多課程
        print("\n📖 建立課程...")
        courses_data = [
            ("自然發音與基礎拼讀", "學習英語字母發音規則，建立基礎拼讀能力", DifficultyLevel.A1),
            ("生活英語會話入門", "日常生活情境對話練習，提升口語表達", DifficultyLevel.A1),
            ("小學英語文法基礎", "基礎英語文法結構學習與應用", DifficultyLevel.A2),
            ("國中英語閱讀訓練", "提升英文閱讀理解能力與技巧", DifficultyLevel.B1),
            ("英語聽力強化班", "訓練英語聽力理解與反應速度", DifficultyLevel.A2),
            ("商用英語溝通", "職場英語溝通技巧與表達方式", DifficultyLevel.B2),
        ]
        
        existing_courses = db.query(Course).filter(
            Course.created_by == teacher.id
        ).all()
        existing_titles = [c.title for c in existing_courses]
        
        new_courses = []
        for title, description, difficulty in courses_data:
            if title not in existing_titles:
                course = Course(
                    id=str(uuid.uuid4()),
                    title=title,
                    description=description,
                    difficulty_level=difficulty,
                    created_by=teacher.id,
                    subject="English"
                )
                db.add(course)
                new_courses.append(course)
                print(f"  ✓ 建立課程: {title}")
        
        if new_courses:
            db.flush()
            print(f"✓ 新建立 {len(new_courses)} 個課程")
        else:
            print("✓ 所有課程已存在")
        
        # 重新獲取所有課程
        all_courses = db.query(Course).filter(
            Course.created_by == teacher.id
        ).all()
        
        # 6. 為課程建立單元
        print("\n📝 建立課程單元...")
        
        # 檢查是否已有單元
        existing_lessons = db.query(Lesson).join(Course).filter(
            Course.created_by == teacher.id
        ).count()
        
        if existing_lessons == 0:  # 只有在沒有現有單元時才建立
            lesson_templates = [
                ("Unit 1: Introduction", ActivityType.speaking_practice),
                ("Unit 2: Basic Vocabulary", ActivityType.reading_assessment), 
                ("Unit 3: Simple Sentences", ActivityType.listening_cloze),
                ("Unit 4: Practice & Review", ActivityType.speaking_quiz),
                ("Unit 5: Advanced Practice", ActivityType.sentence_making),
            ]
            
            for course in all_courses[:3]:  # 為前3個課程建立單元
                for i, (title, activity_type) in enumerate(lesson_templates):
                    lesson = Lesson(
                        id=str(uuid.uuid4()),
                        course_id=course.id,
                        lesson_number=i + 1,
                        title=title,
                        activity_type=activity_type,
                        content={"description": f"{course.title} - {title}"}
                    )
                    db.add(lesson)
                print(f"  ✓ 為 {course.title} 建立 {len(lesson_templates)} 個單元")
            
            db.flush()
            print("✓ 課程單元建立完成")
        else:
            print("✓ 課程單元已存在")
        
        # 7. 建立教室課程關聯
        print("\n🔗 建立教室課程關聯...")
        
        existing_course_mappings = db.query(ClassroomCourseMapping).join(Classroom).filter(
            Classroom.teacher_id == teacher.id
        ).count()
        
        if existing_course_mappings == 0 and len(all_classrooms) > 0 and len(all_courses) > 0:
            # 為每個教室分配適合的課程
            classroom_course_assignments = [
                (0, [0, 1]),    # 小學基礎班 -> 自然發音, 生活會話
                (1, [1, 2]),    # 小學進階班 -> 生活會話, 文法基礎  
                (2, [3, 4]),    # 國中會話班 -> 閱讀訓練, 聽力強化
                (3, [3, 4]),    # 國中閱讀班 -> 閱讀訓練, 聽力強化
                (4, [5]),       # 成人班 -> 商用英語
            ]
            
            for classroom_idx, course_indices in classroom_course_assignments:
                if classroom_idx < len(all_classrooms):
                    classroom = all_classrooms[classroom_idx]
                    for course_idx in course_indices:
                        if course_idx < len(all_courses):
                            course = all_courses[course_idx]
                            mapping = ClassroomCourseMapping(
                                id=str(uuid.uuid4()),
                                classroom_id=classroom.id,
                                course_id=course.id
                            )
                            db.add(mapping)
            
            db.flush()
            print("✓ 教室課程關聯建立完成")
        else:
            print("✓ 教室課程關聯已存在")
        
        # 提交所有變更
        db.commit()
        
        # 8. 顯示最終統計
        print("\n✅ 個體戶教師綜合測試資料建立完成！")
        print("\n📊 最終資料統計：")
        
        total_classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).count()
        
        total_students = db.query(Student).join(ClassroomStudent).join(Classroom).filter(
            Classroom.teacher_id == teacher.id
        ).count()
        
        total_courses = db.query(Course).filter(
            Course.created_by == teacher.id
        ).count()
        
        total_lessons = db.query(Lesson).join(Course).filter(
            Course.created_by == teacher.id
        ).count()
        
        print(f"  - 教室總數: {total_classrooms}")
        print(f"  - 學生總數: {total_students}")
        print(f"  - 課程總數: {total_courses}")
        print(f"  - 單元總數: {total_lessons}")
        
        # 詳細教室資訊
        print("\n📚 教室詳情：")
        for classroom in all_classrooms:
            student_count = db.query(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom.id
            ).count()
            course_count = db.query(ClassroomCourseMapping).filter(
                ClassroomCourseMapping.classroom_id == classroom.id
            ).count()
            print(f"  - {classroom.name}: {student_count} 學生, {course_count} 課程")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    seed_individual_comprehensive()