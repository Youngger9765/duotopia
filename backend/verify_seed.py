"""驗證 seed data 是否成功建立"""
from database import SessionLocal
from models import Teacher, Student, Classroom, Program, Content, ContentType

db = SessionLocal()

teachers = db.query(Teacher).count()
students = db.query(Student).count()
classrooms = db.query(Classroom).count()
programs = db.query(Program).count()
sentence_contents = (
    db.query(Content).filter(Content.type == ContentType.VOCABULARY_SET).count()
)

print(f"✅ 教師數量: {teachers}")
print(f"✅ 學生數量: {students}")
print(f"✅ 班級數量: {classrooms}")
print(f"✅ 課程數量: {programs}")
print(f"✅ 句子模組內容: {sentence_contents}")

db.close()

if sentence_contents >= 4:
    print("✅ 句子模組課程建立成功！")
else:
    print("⚠️ 警告：句子模組內容數量不足")
    exit(1)
