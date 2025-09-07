"""
Integration tests for template programs API endpoints
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models import (
    Teacher,
    Classroom,
    Program,
    Lesson,
    Content,
    ContentType,
    ProgramLevel,
)
from auth import get_password_hash, create_access_token


def create_demo_teacher(db: Session) -> Teacher:
    """Create demo teacher with templates"""
    teacher = db.query(Teacher).filter(Teacher.email == "demo@duotopia.com").first()
    if not teacher:
        teacher = Teacher(
            email="demo@duotopia.com",
            password_hash=get_password_hash("demo123"),
            name="Demo Teacher",
            is_demo=True,
            is_active=True,
        )
        db.add(teacher)
        db.commit()
        db.refresh(teacher)
    return teacher


def create_test_classroom(db: Session, teacher_id: int, name: str) -> Classroom:
    """Helper to create a test classroom"""
    classroom = Classroom(
        name=name,
        teacher_id=teacher_id,
        description="Test classroom for integration tests",
        level=ProgramLevel.A1,
        is_active=True,
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def create_template_programs(db: Session, teacher_id: int):
    """Create template programs for testing"""
    # Check if templates already exist
    existing = db.query(Program).filter(Program.teacher_id == teacher_id, Program.is_template is True).first()

    if existing:
        return  # Templates already created

    # Create a template program
    template = Program(
        name="Test Template Program",
        description="A template for testing",
        level="A1",
        is_template=True,
        classroom_id=None,
        teacher_id=teacher_id,
        estimated_hours=10,
        tags=["test", "template"],
        is_active=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    # Add a lesson to the template
    lesson = Lesson(
        program_id=template.id,
        name="Test Lesson",
        description="A test lesson",
        order_index=1,
        estimated_minutes=30,
        is_active=True,
    )
    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    # Add content to the lesson
    content = Content(
        lesson_id=lesson.id,
        title="Test Content",
        type=ContentType.READING_ASSESSMENT,
        items=[
            {"text": "Hello", "translation": "你好"},
            {"text": "World", "translation": "世界"},
        ],
        target_wpm=80,
        target_accuracy=0.85,
        time_limit_seconds=180,
        order_index=1,
        is_active=True,
    )
    db.add(content)
    db.commit()


def test_get_template_programs(client: TestClient, db: Session):
    """Test getting template programs"""
    # Create demo teacher with templates
    teacher = create_demo_teacher(db)
    create_template_programs(db, teacher.id)

    # Create token for authentication
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/programs/templates", headers=headers)

    assert response.status_code == 200
    templates = response.json()

    # Should have templates
    assert isinstance(templates, list)
    assert len(templates) > 0

    # Verify template structure
    for template in templates:
        assert template["is_template"] is True
        assert template["classroom_id"] is None
        assert "name" in template
        assert "id" in template


def test_get_copyable_programs(client: TestClient, db: Session):
    """Test getting copyable programs (templates + other classroom programs)"""
    # Create demo teacher with templates
    teacher = create_demo_teacher(db)
    create_template_programs(db, teacher.id)

    # Create a classroom with a program
    classroom = create_test_classroom(db, teacher.id, "Test Classroom")
    classroom_program = Program(
        name="Classroom Program",
        description="A program in a classroom",
        level="B1",
        is_template=False,
        classroom_id=classroom.id,
        teacher_id=teacher.id,
        is_active=True,
    )
    db.add(classroom_program)
    db.commit()

    # Create token for authentication
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/programs/copyable", headers=headers)

    assert response.status_code == 200
    programs = response.json()

    # Should include both templates and classroom programs
    assert isinstance(programs, list)
    assert len(programs) >= 2  # At least 1 template + 1 classroom program

    # Separate templates and classroom programs
    templates = [p for p in programs if p.get("is_template")]
    classroom_programs = [p for p in programs if not p.get("is_template")]

    # Should have both types
    assert len(templates) > 0
    assert len(classroom_programs) > 0


def test_copy_from_template(client: TestClient, db: Session):
    """Test copying a program from template"""
    # Create demo teacher with templates
    teacher = create_demo_teacher(db)
    create_template_programs(db, teacher.id)

    # Create token for authentication
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Get a template
    templates_response = client.get("/api/programs/templates", headers=headers)
    assert templates_response.status_code == 200
    templates = templates_response.json()
    assert len(templates) > 0
    template = templates[0]

    # Create a classroom to copy to
    classroom = create_test_classroom(db, teacher.id, "Target Classroom")

    # Copy template to classroom
    response = client.post(
        "/api/programs/copy-from-template",
        headers=headers,
        json={
            "template_id": template["id"],
            "classroom_id": classroom.id,
            "name": f"Copy of {template['name']}",
        },
    )

    assert response.status_code == 200
    new_program = response.json()

    # Verify the copied program
    assert new_program["name"] == f"Copy of {template['name']}"
    assert new_program["classroom_id"] == classroom.id
    assert new_program["is_template"] is False
    assert new_program["source_type"] == "template"
    assert new_program.get("source_metadata", {}).get("template_id") == template["id"]

    # Verify lessons were copied
    if template.get("lesson_count", 0) > 0:
        assert new_program.get("lesson_count", 0) == template["lesson_count"]


def test_copy_from_classroom(client: TestClient, db: Session):
    """Test copying a program from another classroom"""
    # Create demo teacher
    teacher = create_demo_teacher(db)
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Create two classrooms
    classroom1 = create_test_classroom(db, teacher.id, "Source Classroom")
    classroom2 = create_test_classroom(db, teacher.id, "Target Classroom")

    # Create a program in classroom1
    source_program = Program(
        name="Source Program",
        description="Program to copy",
        level="A2",
        is_template=False,
        classroom_id=classroom1.id,
        teacher_id=teacher.id,
        is_active=True,
    )
    db.add(source_program)
    db.commit()
    db.refresh(source_program)

    # Add a lesson to the source program
    lesson = Lesson(
        program_id=source_program.id,
        name="Source Lesson",
        order_index=1,
        is_active=True,
    )
    db.add(lesson)
    db.commit()

    # Copy from classroom1 to classroom2
    response = client.post(
        "/api/programs/copy-from-classroom",
        headers=headers,
        json={
            "source_program_id": source_program.id,
            "target_classroom_id": classroom2.id,
            "name": "Copied Program",
        },
    )

    assert response.status_code == 200
    new_program = response.json()

    # Verify the copied program
    assert new_program["name"] == "Copied Program"
    assert new_program["classroom_id"] == classroom2.id
    assert new_program["is_template"] is False
    assert new_program["source_type"] == "classroom"
    assert new_program.get("source_metadata", {}).get("source_program_id") == source_program.id


def test_create_custom_program(client: TestClient, db: Session):
    """Test creating a custom program"""
    # Create demo teacher
    teacher = create_demo_teacher(db)
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Create a classroom
    classroom = create_test_classroom(db, teacher.id, "Custom Program Classroom")

    # Create custom program
    response = client.post(
        "/api/programs/create-custom",
        headers=headers,
        json={
            "classroom_id": classroom.id,
            "name": "My Custom Program",
            "description": "A custom program created from scratch",
            "level": "B1",
            "estimated_hours": 20,
            "tags": ["custom", "test"],
        },
    )

    assert response.status_code == 200
    program = response.json()

    # Verify the custom program
    assert program["name"] == "My Custom Program"
    assert program["description"] == "A custom program created from scratch"
    assert program["classroom_id"] == classroom.id
    assert program["is_template"] is False
    assert program["source_type"] == "custom"
    assert program["level"] == "B1"
    assert program["estimated_hours"] == 20
    assert "custom" in program.get("tags", [])


def test_get_classroom_programs(client: TestClient, db: Session):
    """Test getting programs for a specific classroom"""
    # Create demo teacher
    teacher = create_demo_teacher(db)
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Create a classroom
    classroom = create_test_classroom(db, teacher.id, "Programs Test Classroom")

    # Create 2 programs in the classroom
    for i in range(2):
        program = Program(
            name=f"Program {i+1}",
            description=f"Test program {i+1}",
            level="A1",
            is_template=False,
            classroom_id=classroom.id,
            teacher_id=teacher.id,
            is_active=True,
        )
        db.add(program)
    db.commit()

    # Get classroom programs
    response = client.get(f"/api/programs/classroom/{classroom.id}", headers=headers)

    assert response.status_code == 200
    programs = response.json()

    # Should have 2 programs
    assert len(programs) == 2

    # Verify all programs belong to this classroom
    for program in programs:
        assert program["classroom_id"] == classroom.id
        assert program["is_template"] is False
        assert "Program" in program["name"]


def test_template_not_modifiable_by_copy(client: TestClient, db: Session):
    """Test that copying a template doesn't modify the original template"""
    # Create demo teacher with templates
    teacher = create_demo_teacher(db)
    create_template_programs(db, teacher.id)
    token = create_access_token({"sub": teacher.email, "type": "teacher"})
    headers = {"Authorization": f"Bearer {token}"}

    # Get a template
    templates_response = client.get("/api/programs/templates", headers=headers)
    templates = templates_response.json()
    original_template = templates[0]
    original_name = original_template["name"]
    original_lesson_count = original_template.get("lesson_count", 0)

    # Create a classroom and copy the template
    classroom = create_test_classroom(db, teacher.id, "Template Safety Test")

    client.post(
        "/api/programs/copy-from-template",
        headers=headers,
        json={
            "template_id": original_template["id"],
            "classroom_id": classroom.id,
            "name": "Modified Copy",
        },
    )

    # Get the template again
    templates_response2 = client.get("/api/programs/templates", headers=headers)
    templates2 = templates_response2.json()
    template_after = next(t for t in templates2 if t["id"] == original_template["id"])

    # Template should be unchanged
    assert template_after["name"] == original_name
    assert template_after["is_template"] is True
    assert template_after["classroom_id"] is None
    assert template_after.get("lesson_count", 0) == original_lesson_count
