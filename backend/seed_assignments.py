#!/usr/bin/env python3
"""
作業系統測試資料建立腳本
為 Phase 2 建立更多測試資料
"""

from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    Teacher, Student, Classroom, ClassroomStudent,
    Program, Lesson, Content,
    StudentAssignment, AssignmentSubmission,
    AssignmentStatus, ContentType
)
import json

def create_assignment_test_data():
    """建立作業系統測試資料"""
    db = SessionLocal()
    
    try:
        print("🌱 開始建立作業測試資料...")
        
        # 取得 demo 教師
        teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
        if not teacher:
            print("❌ 找不到 demo 教師，請先執行 seed_data.py")
            return
        
        # 取得班級
        classrooms = db.query(Classroom).filter(Classroom.teacher_id == teacher.id).all()
        if not classrooms:
            print("❌ 找不到班級，請先執行 seed_data.py")
            return
        
        print(f"✅ 找到 {len(classrooms)} 個班級")
        
        # 清除舊的作業資料
        print("🗑️  清除舊作業資料...")
        db.query(AssignmentSubmission).delete()
        db.query(StudentAssignment).delete()
        db.commit()
        
        # 建立各種狀態的作業
        assignment_count = 0
        
        for classroom in classrooms:
            # 取得班級學生
            students = db.query(Student).join(ClassroomStudent).filter(
                ClassroomStudent.classroom_id == classroom.id,
                ClassroomStudent.is_active == True
            ).all()
            
            print(f"\n📚 處理班級: {classroom.name} ({len(students)} 位學生)")
            
            # 取得班級的 Content
            contents = db.query(Content).join(Lesson).join(Program).filter(
                Program.classroom_id == classroom.id
            ).all()
            
            if not contents:
                print(f"  ⚠️ 班級 {classroom.name} 沒有 Content")
                continue
            
            print(f"  ✅ 找到 {len(contents)} 個 Content")
            
            # 為每個 Content 建立不同狀態的作業
            for i, content in enumerate(contents[:3]):  # 只用前3個 Content
                # 決定作業的時間和狀態
                if i == 0:
                    # 已過期的作業
                    due_date = datetime.now() - timedelta(days=2)
                    title = f"[已過期] {content.title}"
                    instructions = "這是一個已過期的作業測試"
                elif i == 1:
                    # 即將到期的作業（24小時內）
                    due_date = datetime.now() + timedelta(hours=20)
                    title = f"[即將到期] {content.title}"
                    instructions = "請盡快完成此作業，即將到期！"
                else:
                    # 正常的作業
                    due_date = datetime.now() + timedelta(days=7)
                    title = f"{content.title} - 練習作業"
                    instructions = "請認真完成練習，注意發音準確度"
                
                # 為每個學生建立作業
                for j, student in enumerate(students):
                    # 設定不同的狀態
                    if i == 0:  # 過期作業
                        if j == 0:
                            status = AssignmentStatus.GRADED  # 已批改
                            score = random.randint(70, 95)
                            feedback = "做得很好！繼續加油！"
                        elif j == 1:
                            status = AssignmentStatus.SUBMITTED  # 已提交
                            score = None
                            feedback = None
                        else:
                            status = AssignmentStatus.NOT_STARTED  # 未開始（過期）
                            score = None
                            feedback = None
                    elif i == 1:  # 即將到期
                        if j == 0:
                            status = AssignmentStatus.SUBMITTED  # 已提交
                            score = None
                            feedback = None
                        elif j == 1:
                            status = AssignmentStatus.IN_PROGRESS  # 進行中
                            score = None
                            feedback = None
                        else:
                            status = AssignmentStatus.NOT_STARTED  # 未開始
                            score = None
                            feedback = None
                    else:  # 正常作業
                        if j == 0:
                            status = AssignmentStatus.RETURNED  # 需修正
                            score = 65
                            feedback = "請重新錄音第2和第3題，注意發音"
                        elif j == 1:
                            status = AssignmentStatus.IN_PROGRESS  # 進行中
                            score = None
                            feedback = None
                        else:
                            status = AssignmentStatus.NOT_STARTED  # 未開始
                            score = None
                            feedback = None
                    
                    # 建立作業
                    assignment = StudentAssignment(
                        student_id=student.id,
                        content_id=content.id,
                        classroom_id=classroom.id,
                        title=title,
                        instructions=instructions,
                        status=status,
                        due_date=due_date,
                        score=score,
                        feedback=feedback
                    )
                    
                    # 如果是已提交或已批改的，設定提交時間
                    if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                        assignment.submitted_at = datetime.now() - timedelta(days=1)
                    
                    # 如果是已批改的，設定批改時間
                    if status in [AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                        assignment.graded_at = datetime.now() - timedelta(hours=12)
                    
                    db.add(assignment)
                    assignment_count += 1
                    
                    # 如果作業已提交，建立提交記錄
                    if status in [AssignmentStatus.SUBMITTED, AssignmentStatus.GRADED, AssignmentStatus.RETURNED]:
                        # 先保存作業以取得 ID
                        db.flush()
                        
                        submission = AssignmentSubmission(
                            assignment_id=assignment.id,
                            submission_data={
                                "audio_urls": [
                                    f"gs://duotopia-audio/demo/{student.id}/recording_{k}.mp3"
                                    for k in range(3)
                                ]
                            },
                            ai_scores={
                                "wpm": random.randint(60, 120),
                                "accuracy": round(random.uniform(0.7, 0.95), 2),
                                "fluency": round(random.uniform(0.6, 0.9), 2),
                                "pronunciation": round(random.uniform(0.65, 0.95), 2)
                            } if status == AssignmentStatus.GRADED else None,
                            ai_feedback="AI 評分：發音清晰，語調自然。建議加強連音練習。" if status == AssignmentStatus.GRADED else None
                        )
                        db.add(submission)
        
        # 提交所有變更
        db.commit()
        print(f"\n✅ 成功建立 {assignment_count} 個作業記錄")
        
        # 顯示統計
        print("\n📊 作業統計：")
        for status in AssignmentStatus:
            count = db.query(StudentAssignment).filter(
                StudentAssignment.status == status
            ).count()
            print(f"  - {status.value}: {count} 個")
        
        # 顯示測試帳號資訊
        print("\n📝 測試說明：")
        print("1. 教師登入: demo@duotopia.com / demo123")
        print("2. 學生測試帳號：")
        print("   - 王小明: 有已批改、已提交、需修正的作業")
        print("   - 李小美: 有已提交、進行中的作業")
        print("   - 其他學生: 有未開始的作業")
        print("3. 作業狀態：")
        print("   - 已過期作業：可查看批改結果")
        print("   - 即將到期作業：24小時內到期")
        print("   - 正常作業：7天後到期")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_assignment_test_data()