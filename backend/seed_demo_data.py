"""
Seed demo data for local development
Creates: Schools, Teachers, Programs (Materials)
"""
import os
import sys
sys.path.insert(0, '.')

from database import SessionLocal
from models.user import Teacher
from models.organization import Organization, TeacherOrganization, School
from models.program import Program
from models.base import ProgramLevel
from passlib.context import CryptContext
from datetime import datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
default_password = os.environ.get("SEED_DEFAULT_PASSWORD")
if not default_password:
    raise ValueError(
        "Missing SEED_DEFAULT_PASSWORD environment variable for seed scripts"
    )
db = SessionLocal()

# Use existing org
org_id = uuid.UUID("21a8a0c7-a5e3-4799-8336-fbb2cf1de91a")
org = db.query(Organization).filter(Organization.id == org_id).first()

if not org:
    print("❌ Organization not found! Run seed_local_org.py first")
    exit(1)

print(f"✅ Using organization: {org.name}")

# ========== Create Schools ==========
print("\n📚 Creating schools...")

schools_data = [
    {"name": "台北分校", "display_name": "台北分校", "description": "位於台北市信義區"},
    {"name": "新竹分校", "display_name": "新竹分校", "description": "位於新竹市東區"},
    {"name": "台中分校", "display_name": "台中分校", "description": "位於台中市西屯區"},
]

schools = []
for school_data in schools_data:
    existing = db.query(School).filter(
        School.organization_id == org_id,
        School.name == school_data["name"]
    ).first()

    if not existing:
        school = School(
            organization_id=org_id,
            name=school_data["name"],
            display_name=school_data["display_name"],
            description=school_data["description"],
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(school)
        db.flush()
        schools.append(school)
        print(f"  ➕ Created school: {school.name}")
    else:
        schools.append(existing)
        print(f"  ✓ School exists: {existing.name}")

db.commit()

# ========== Create Teachers ==========
print("\n👥 Creating teachers...")

teachers_data = [
    {"email": "demo@duotopia.com", "name": "Demo 老師", "phone": "0900-000-001", "role": "teacher", "is_demo": True},
    {"email": "trial@duotopia.com", "name": "試用老師", "phone": "0900-000-002", "role": "teacher", "is_demo": False},
    {"email": "expired@duotopia.com", "name": "過期老師", "phone": "0900-000-003", "role": "teacher", "is_demo": False},
    {"email": "chen@duotopia.com", "name": "陳美玲", "phone": "0912-345-678", "role": "org_admin"},
    {"email": "wang@duotopia.com", "name": "王建國", "phone": "0923-456-789", "role": "teacher"},
    {"email": "liu@duotopia.com", "name": "劉芳華", "phone": "0934-567-890", "role": "teacher"},
    {"email": "zhang@duotopia.com", "name": "張志明", "phone": "0945-678-901", "role": "teacher"},
    {"email": "lee@duotopia.com", "name": "李雅婷", "phone": "0956-789-012", "role": "teacher"},
]

for teacher_data in teachers_data:
    existing = db.query(Teacher).filter(Teacher.email == teacher_data["email"]).first()

    if not existing:
        teacher = Teacher(
            email=teacher_data["email"],
            password_hash=pwd_context.hash(default_password),
            name=teacher_data["name"],
            phone=teacher_data["phone"],
            is_active=True,
            is_demo=teacher_data.get("is_demo", False),
            is_admin=False,
            email_verified=True,
            email_verified_at=datetime.now(),
            created_at=datetime.now()
        )
        db.add(teacher)
        db.flush()

        # Link to organization
        teacher_org = TeacherOrganization(
            teacher_id=teacher.id,
            organization_id=org_id,
            role=teacher_data["role"],
            is_active=True,
            created_at=datetime.now()
        )
        db.add(teacher_org)
        db.flush()
        print(f"  ➕ Created teacher: {teacher.name} ({teacher_data['role']})")
    else:
        print(f"  ✓ Teacher exists: {existing.name}")

db.commit()

# ========== Create Programs (Materials) ==========
print("\n📖 Creating programs (materials)...")

# Get owner teacher for teacher_id
owner = db.query(Teacher).filter(Teacher.email == "owner@duotopia.com").first()

programs_data = [
    {"name": "兒童英語啟蒙", "description": "適合3-6歲兒童的英語啟蒙課程", "level": ProgramLevel.PRE_A},
    {"name": "基礎英語會話 A1", "description": "日常生活基礎會話訓練", "level": ProgramLevel.A1},
    {"name": "進階英語會話 A2", "description": "日常情境進階會話", "level": ProgramLevel.A2},
    {"name": "中級英語 B1", "description": "職場與學術英語入門", "level": ProgramLevel.B1},
    {"name": "中高級英語 B2", "description": "深度討論與簡報技巧", "level": ProgramLevel.B2},
    {"name": "高級英語 C1", "description": "學術英語與專業溝通", "level": ProgramLevel.C1},
    {"name": "精通英語 C2", "description": "母語級別的英語掌握", "level": ProgramLevel.C2},
    {"name": "商務英語基礎", "description": "商務情境英語訓練", "level": ProgramLevel.B1},
    {"name": "商務英語進階", "description": "商務談判與簡報", "level": ProgramLevel.B2},
    {"name": "多益衝刺班", "description": "TOEIC 600-800 分衝刺", "level": ProgramLevel.B1},
]

for program_data in programs_data:
    existing = db.query(Program).filter(
        Program.organization_id == org_id,
        Program.name == program_data["name"]
    ).first()

    if not existing:
        program = Program(
            organization_id=org_id,
            teacher_id=owner.id,
            name=program_data["name"],
            description=program_data["description"],
            level=program_data["level"],
            is_template=False,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(program)
        print(f"  ➕ Created program: {program.name} ({program.level})")
    else:
        print(f"  ✓ Program exists: {existing.name}")

db.commit()

# ========== Create Template Programs (公版課程) ==========
print("\n📚 Creating template programs (公版課程)...")

from models.program import Lesson, Content
from models.base import ContentType

template_programs_data = [
    {
        "name": "基礎會話訓練 A1",
        "description": "日常生活基礎會話，適合初學者",
        "level": ProgramLevel.A1,
        "estimated_hours": 20,
        "tags": ["日常會話", "初學者", "基礎"],
        "lessons": [
            {
                "title": "自我介紹",
                "description": "學習基本的自我介紹用語",
                "order": 0,
                "contents": [
                    {"title": "詞彙：個人資訊", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "句型：What's your name?", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "對話練習：初次見面", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
            {
                "title": "數字與時間",
                "description": "學習數字、日期、時間表達",
                "order": 1,
                "contents": [
                    {"title": "詞彙：數字 1-100", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "時間表達法", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "對話：約時間", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
        ]
    },
    {
        "name": "商務英語基礎",
        "description": "商務場合常用英語表達",
        "level": ProgramLevel.B1,
        "estimated_hours": 30,
        "tags": ["商務", "職場", "email"],
        "lessons": [
            {
                "title": "商務 Email 寫作",
                "description": "學習撰寫專業商務郵件",
                "order": 0,
                "contents": [
                    {"title": "Email 格式與架構", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "常用商務用語", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "實戰練習：詢價信", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
            {
                "title": "會議英語",
                "description": "參與英語會議的必備技巧",
                "order": 1,
                "contents": [
                    {"title": "會議常用句型", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "表達意見與提問", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "模擬會議", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
        ]
    },
    {
        "name": "多益衝刺 600+",
        "description": "TOEIC 600-750 分數目標訓練",
        "level": ProgramLevel.B1,
        "estimated_hours": 40,
        "tags": ["TOEIC", "考試", "聽力", "閱讀"],
        "lessons": [
            {
                "title": "聽力技巧：Part 1-2",
                "description": "照片描述與問答題型攻略",
                "order": 0,
                "contents": [
                    {"title": "題型分析", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "高頻詞彙", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "模擬練習 20 題", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
            {
                "title": "閱讀技巧：Part 5-6",
                "description": "文法與短文填空",
                "order": 1,
                "contents": [
                    {"title": "文法重點整理", "type": ContentType.READING_ASSESSMENT, "order": 0},
                    {"title": "解題技巧", "type": ContentType.READING_ASSESSMENT, "order": 1},
                    {"title": "模擬練習 30 題", "type": ContentType.READING_ASSESSMENT, "order": 2},
                ]
            },
        ]
    },
]

for tmpl_data in template_programs_data:
    existing_tmpl = db.query(Program).filter(
        Program.teacher_id == owner.id,
        Program.name == tmpl_data["name"],
        Program.is_template.is_(True)
    ).first()

    if not existing_tmpl:
        # Create template program
        template_program = Program(
            organization_id=org_id,
            teacher_id=owner.id,
            name=tmpl_data["name"],
            description=tmpl_data["description"],
            level=tmpl_data["level"],
            estimated_hours=tmpl_data.get("estimated_hours"),
            tags=tmpl_data.get("tags", []),
            is_template=True,
            is_active=True,
            order_index=0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(template_program)
        db.flush()

        # Create lessons
        for lesson_data in tmpl_data.get("lessons", []):
            lesson = Lesson(
                program_id=template_program.id,
                name=lesson_data["title"],
                description=lesson_data.get("description"),
                order_index=lesson_data["order"],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            db.add(lesson)
            db.flush()

            # Create contents
            for content_data in lesson_data.get("contents", []):
                content = Content(
                    lesson_id=lesson.id,
                    title=content_data["title"],
                    type=content_data["type"],
                    order_index=content_data["order"],
                    created_at=datetime.now()
                )
                db.add(content)

        print(f"  ➕ Created template: {template_program.name} with {len(tmpl_data.get('lessons', []))} lessons")
    else:
        print(f"  ✓ Template exists: {existing_tmpl.name}")

db.commit()

print("\n" + "="*60)
print("✅ Demo data seed complete!")
print("="*60)
print(f"\n📊 Summary:")
print(f"  - Organization: {org.name}")
print(f"  - Schools: {len(schools)} created")
print(f"  - Teachers: {len(teachers_data)} total")
print(f"  - Programs: {len(programs_data)} materials")
print(f"  - Template Programs: {len(template_programs_data)} 公版課程")

print("\n🔑 Test Accounts:")
print("  - demo@duotopia.com / [SEED_DEFAULT_PASSWORD] (Demo 教師)")
print("  - trial@duotopia.com / [SEED_DEFAULT_PASSWORD] (試用教師)")
print("  - expired@duotopia.com / [SEED_DEFAULT_PASSWORD] (過期教師)")
print("  - owner@duotopia.com / [SEED_DEFAULT_PASSWORD] (機構擁有者)")
print("  - chen@duotopia.com / [SEED_DEFAULT_PASSWORD] (機構管理員)")
print("  - wang@duotopia.com / [SEED_DEFAULT_PASSWORD] (教師)")
print("  - liu@duotopia.com / [SEED_DEFAULT_PASSWORD] (教師)")
print("  - zhang@duotopia.com / [SEED_DEFAULT_PASSWORD] (教師)")
print("  - lee@duotopia.com / [SEED_DEFAULT_PASSWORD] (教師)")

print(f"\n🌐 Visit: http://localhost:5173/organization/{org_id}")

db.close()

# Fixed URL regex validation

