#!/usr/bin/env python3
"""
測試 CASCADE DELETE 功能
"""
from sqlalchemy import text
from database import SessionLocal
from models import Program, Lesson, Content


def test_cascade_delete():
    db = SessionLocal()

    try:
        print("🔍 測試 CASCADE DELETE 功能...\n")

        # 1. 檢查初始狀態
        programs_count = db.query(Program).count()
        lessons_count = db.query(Lesson).count()
        contents_count = db.query(Content).count()

        print(f"初始狀態:")
        print(f"  - Programs: {programs_count}")
        print(f"  - Lessons: {lessons_count}")
        print(f"  - Contents: {contents_count}")

        # 2. 取得第一個 Program
        program = db.query(Program).first()
        if not program:
            print("❌ 沒有找到 Program")
            return

        program_id = program.id
        program_name = program.name

        # 計算這個 Program 有多少 Lessons 和 Contents
        program_lessons = db.query(Lesson).filter(Lesson.program_id == program_id).all()
        lesson_ids = [l.id for l in program_lessons]
        program_contents = (
            db.query(Content)
            .join(Lesson)
            .filter(Lesson.program_id == program_id)
            .count()
        )

        print(f"\n準備刪除: {program_name} (ID: {program_id})")
        print(f"  - 包含 {len(program_lessons)} 個 Lessons")
        print(f"  - 包含 {program_contents} 個 Contents")

        # 3. 刪除 Program
        print(f"\n執行刪除...")
        db.delete(program)
        db.commit()

        # 4. 檢查結果
        new_programs_count = db.query(Program).count()
        new_lessons_count = db.query(Lesson).count()
        new_contents_count = db.query(Content).count()

        # 檢查相關的 Lessons 是否被刪除
        remaining_lessons = (
            db.query(Lesson).filter(Lesson.program_id == program_id).count()
        )
        remaining_contents = (
            db.query(Content).filter(Content.lesson_id.in_(lesson_ids)).count()
            if lesson_ids
            else 0
        )

        print(f"\n刪除後狀態:")
        print(
            f"  - Programs: {programs_count} → {new_programs_count} (減少 {programs_count - new_programs_count})"
        )
        print(
            f"  - Lessons: {lessons_count} → {new_lessons_count} (減少 {lessons_count - new_lessons_count})"
        )
        print(
            f"  - Contents: {contents_count} → {new_contents_count} (減少 {contents_count - new_contents_count})"
        )

        print(f"\n檢查關聯資料:")
        print(f"  - 原 Program 的 Lessons 剩餘: {remaining_lessons}")
        print(f"  - 原 Lessons 的 Contents 剩餘: {remaining_contents}")

        # 5. 判斷結果
        if remaining_lessons == 0 and remaining_contents == 0:
            print("\n✅ CASCADE DELETE 運作正常！刪除 Program 時，相關的 Lessons 和 Contents 都被刪除了。")
        else:
            print("\n❌ CASCADE DELETE 有問題！還有孤立的資料存在。")

            # 檢查資料庫的外鍵約束
            print("\n檢查資料庫外鍵約束...")
            result = db.execute(
                text(
                    """
                SELECT
                    tc.constraint_name,
                    tc.table_name,
                    kcu.column_name,
                    rc.delete_rule
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.referential_constraints AS rc
                    ON tc.constraint_name = rc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND tc.table_name IN ('lessons', 'contents')
            """
                )
            )

            for row in result:
                print(
                    f"  - {row.table_name}.{row.column_name}: DELETE {row.delete_rule}"
                )

    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    test_cascade_delete()
