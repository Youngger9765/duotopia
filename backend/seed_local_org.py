import os
import sys

sys.path.insert(0, ".")

from database import SessionLocal
from models.user import Teacher
from models.organization import Organization, TeacherOrganization
from passlib.context import CryptContext
from datetime import datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
owner_password = os.environ.get("SEED_DEFAULT_PASSWORD")
if not owner_password:
    raise ValueError(
        "Missing SEED_DEFAULT_PASSWORD environment variable for seed scripts"
    )
db = SessionLocal()

# Check if teacher exists
teacher = db.query(Teacher).filter(Teacher.email == "owner@duotopia.com").first()

if teacher:
    # Update existing teacher
    teacher.password_hash = pwd_context.hash(owner_password)
    teacher.is_active = True
    teacher.is_admin = True
    teacher.email_verified = True
    if not teacher.email_verified_at:
        teacher.email_verified_at = datetime.now()
    print("📝 Updated existing teacher")
else:
    # Create new teacher
    teacher = Teacher(
        email="owner@duotopia.com",
        password_hash=pwd_context.hash(owner_password),
        name="Test Owner",
        is_active=True,
        is_demo=False,
        is_admin=True,
        email_verified=True,
        email_verified_at=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(teacher)
    print("➕ Created new teacher")

db.flush()

# Check if organization exists
org_id = uuid.UUID("21a8a0c7-a5e3-4799-8336-fbb2cf1de91a")
org = db.query(Organization).filter(Organization.id == org_id).first()

if not org:
    org = Organization(
        id=org_id,
        name="測試機構",
        display_name="測試機構",
        tax_id="12345678",
        is_active=True,
        teacher_limit=10,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(org)
    print("➕ Created organization")
else:
    print("✓ Organization exists")

db.flush()

# Check if teacher-org link exists
teacher_org = (
    db.query(TeacherOrganization)
    .filter(
        TeacherOrganization.teacher_id == teacher.id,
        TeacherOrganization.organization_id == org_id,
    )
    .first()
)

if not teacher_org:
    teacher_org = TeacherOrganization(
        teacher_id=teacher.id,
        organization_id=org_id,
        role="org_owner",
        is_active=True,
        created_at=datetime.now(),
    )
    db.add(teacher_org)
    print("➕ Linked teacher to organization")
else:
    teacher_org.role = "org_owner"
    teacher_org.is_active = True
    print("✓ Teacher-org link exists")

db.commit()

print("✅ Seed complete!")
print(f"Email: owner@duotopia.com")
print("Password: [SEED_DEFAULT_PASSWORD]")
print(f"Org ID: {org_id}")

db.close()
