#!/usr/bin/env python3
"""
建立教室課程關聯
"""
import sys
import os
import uuid
sys.path.append(os.path.dirname(__file__))

from database import SessionLocal
from models import User, Classroom, Course, ClassroomCourseMapping, Lesson, ActivityType

def create_course_mappings():
    db = SessionLocal()
    try:
        print("=== 建立教室課程關聯 ===\n")
        
        # 找到個體戶教師
        teacher = db.query(User).filter(
            User.email == "teacher@individual.com"
        ).first()
        
        if not teacher:
            print("❌ 找不到個體戶教師")
            return
            
        print(f"✓ 找到個體戶教師: {teacher.full_name}")
        
        # 獲取教室和課程
        classrooms = db.query(Classroom).filter(
            Classroom.teacher_id == teacher.id,
            Classroom.school_id == None
        ).order_by(Classroom.created_at).all()
        
        courses = db.query(Course).filter(
            Course.created_by == teacher.id
        ).order_by(Course.created_at).all()
        
        print(f"✓ 找到 {len(classrooms)} 個教室")
        print(f"✓ 找到 {len(courses)} 個課程")
        
        # 清除現有關聯
        print("\n🔄 清除現有課程關聯...")
        db.query(ClassroomCourseMapping).filter(
            ClassroomCourseMapping.classroom_id.in_([c.id for c in classrooms])
        ).delete(synchronize_session=False)
        db.flush()
        
        # 建立課程關聯
        print("\n🔗 建立課程關聯...")
        
        # 為每種類型的教室分配適合的課程
        classroom_course_assignments = [
            # 基礎班 - 適合基礎課程
            ("小學英語基礎班", ["自然發音與基礎拼讀", "生活英語會話入門"]),
            ("小學英語進階班", ["生活英語會話入門", "小學英語文法基礎"]),
            ("國中英語會話班", ["國中英語閱讀訓練", "英語聽力強化班"]), 
            ("國中英語閱讀班", ["國中英語閱讀訓練", "英語聽力強化班"]),
            ("成人英語口說班", ["商用英語溝通", "生活英語會話入門"]),
            # 原始教室也分配一些課程
            ("個體戶老師的班級", ["基礎英語會話 - 個體戶老師", "進階閱讀理解 - 個體戶老師"])
        ]
        
        classroom_dict = {c.name: c for c in classrooms}
        course_dict = {c.title: c for c in courses}
        
        for classroom_name, course_titles in classroom_course_assignments:
            if classroom_name in classroom_dict:
                classroom = classroom_dict[classroom_name]
                assigned_courses = []
                
                for course_title in course_titles:
                    if course_title in course_dict:
                        course = course_dict[course_title]
                        mapping = ClassroomCourseMapping(
                            id=str(uuid.uuid4()),
                            classroom_id=classroom.id,
                            course_id=course.id
                        )
                        db.add(mapping)
                        assigned_courses.append(course_title)
                
                print(f"  ✓ {classroom_name}: 分配 {len(assigned_courses)} 個課程")
                for title in assigned_courses:
                    print(f"    - {title}")
        
        # 為缺少單元的課程建立單元
        print("\n📝 建立缺少的課程單元...")
        
        for course in courses:
            existing_lessons = db.query(Lesson).filter(
                Lesson.course_id == course.id
            ).count()
            
            if existing_lessons == 0:
                # 根據課程類型建立不同的單元
                if "基礎" in course.title or "入門" in course.title:
                    lesson_data = [
                        ("第一單元：字母與發音", ActivityType.READING_ASSESSMENT),
                        ("第二單元：基礎詞彙", ActivityType.LISTENING_CLOZE),
                        ("第三單元：簡單對話", ActivityType.SPEAKING_PRACTICE),
                        ("第四單元：基礎句型", ActivityType.SENTENCE_MAKING),
                        ("第五單元：綜合練習", ActivityType.SPEAKING_QUIZ)
                    ]
                elif "進階" in course.title or "強化" in course.title:
                    lesson_data = [
                        ("Unit 1: Advanced Vocabulary", ActivityType.READING_ASSESSMENT),
                        ("Unit 2: Complex Grammar", ActivityType.SENTENCE_MAKING),
                        ("Unit 3: Listening Comprehension", ActivityType.LISTENING_CLOZE),
                        ("Unit 4: Speaking Fluency", ActivityType.SPEAKING_PRACTICE),
                        ("Unit 5: Integrated Skills", ActivityType.SPEAKING_QUIZ),
                        ("Unit 6: Real-world Application", ActivityType.SPEAKING_SCENARIO)
                    ]
                elif "商用" in course.title:
                    lesson_data = [
                        ("Business Communication Basics", ActivityType.SPEAKING_PRACTICE),
                        ("Email Writing Skills", ActivityType.SENTENCE_MAKING),
                        ("Presentation Techniques", ActivityType.SPEAKING_QUIZ),
                        ("Meeting Participation", ActivityType.SPEAKING_SCENARIO),
                        ("Negotiation Skills", ActivityType.SPEAKING_PRACTICE)
                    ]
                else:
                    lesson_data = [
                        ("Introduction", ActivityType.READING_ASSESSMENT),
                        ("Building Foundation", ActivityType.LISTENING_CLOZE),
                        ("Practice Session", ActivityType.SPEAKING_PRACTICE),
                        ("Advanced Techniques", ActivityType.SENTENCE_MAKING),
                        ("Final Assessment", ActivityType.SPEAKING_QUIZ)
                    ]
                
                for i, (title, activity_type) in enumerate(lesson_data):
                    lesson = Lesson(
                        id=str(uuid.uuid4()),
                        course_id=course.id,
                        lesson_number=i + 1,
                        title=title,
                        activity_type=activity_type,
                        content={"description": f"{course.title} - {title}"}
                    )
                    db.add(lesson)
                
                print(f"  ✓ {course.title}: 建立 {len(lesson_data)} 個單元")
        
        db.commit()
        
        # 顯示最終結果
        print("\n✅ 課程關聯建立完成！\n")
        print("📊 最終課程分配結果：")
        
        for classroom in classrooms:
            course_mappings = db.query(ClassroomCourseMapping).filter(
                ClassroomCourseMapping.classroom_id == classroom.id
            ).all()
            
            print(f"\n📚 {classroom.name} ({len(course_mappings)} 課程):")
            for mapping in course_mappings:
                course = db.query(Course).filter(
                    Course.id == mapping.course_id
                ).first()
                if course:
                    lesson_count = db.query(Lesson).filter(
                        Lesson.course_id == course.id
                    ).count()
                    print(f"  - {course.title} ({lesson_count} 單元)")
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    create_course_mappings()