"""
Test for Issue #32: 老師指派作業時看到其他班級的非公版課程
TDD Test - Red Phase

Test scenario:
- Teacher has two classrooms: ClassA and ClassB
- ClassA has a classroom-specific program (non-template)
- ClassB has a classroom-specific program (non-template)
- There's a public template program (is_template=True)

Expected behavior:
- When fetching contents for ClassA, should see:
  ✅ Public template contents
  ✅ ClassA's classroom-specific contents
  ❌ ClassB's classroom-specific contents (SHOULD NOT SEE)
"""

import pytest
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
from auth import create_access_token


@pytest.fixture
def teacher_with_two_classrooms(test_session: Session):
    """建立一個教師，擁有兩個班級，每個班級有專屬課程 + 一個公版模板"""
    # 建立教師
    teacher = Teacher(
        email="teacher_issue32@example.com",
        password_hash="hashed_password",
        name="Issue32 Teacher",
        is_active=True,
    )
    test_session.add(teacher)
    test_session.flush()

    # 建立兩個班級
    classroom_a = Classroom(
        name="Class A",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    classroom_b = Classroom(
        name="Class B",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_active=True,
    )
    test_session.add_all([classroom_a, classroom_b])
    test_session.flush()

    # 建立公版模板課程 (is_template=True, classroom_id=None)
    public_template = Program(
        name="Public Template Program",
        description="公版課程，所有班級都可見",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_template=True,
        classroom_id=None,  # 公版課程沒有 classroom_id
        is_active=True,
    )
    test_session.add(public_template)
    test_session.flush()

    # 為公版模板建立 Lesson 和 Content
    public_lesson = Lesson(
        program_id=public_template.id,
        name="Public Template Lesson",
        order_index=1,
        is_active=True,
    )
    test_session.add(public_lesson)
    test_session.flush()

    public_content = Content(
        lesson_id=public_lesson.id,
        title="Public Template Content",
        type=ContentType.READING_ASSESSMENT,
        order_index=1,
        is_active=True,
    )
    test_session.add(public_content)

    # 建立 ClassA 專屬課程 (is_template=False, classroom_id=ClassA)
    program_a = Program(
        name="ClassA Specific Program",
        description="ClassA 專屬課程，只有 ClassA 可見",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_template=False,
        classroom_id=classroom_a.id,
        is_active=True,
    )
    test_session.add(program_a)
    test_session.flush()

    lesson_a = Lesson(
        program_id=program_a.id,
        name="ClassA Specific Lesson",
        order_index=1,
        is_active=True,
    )
    test_session.add(lesson_a)
    test_session.flush()

    content_a = Content(
        lesson_id=lesson_a.id,
        title="ClassA Specific Content",
        type=ContentType.READING_ASSESSMENT,
        order_index=1,
        is_active=True,
    )
    test_session.add(content_a)

    # 建立 ClassB 專屬課程 (is_template=False, classroom_id=ClassB)
    program_b = Program(
        name="ClassB Specific Program",
        description="ClassB 專屬課程，只有 ClassB 可見",
        teacher_id=teacher.id,
        level=ProgramLevel.A1,
        is_template=False,
        classroom_id=classroom_b.id,
        is_active=True,
    )
    test_session.add(program_b)
    test_session.flush()

    lesson_b = Lesson(
        program_id=program_b.id,
        name="ClassB Specific Lesson",
        order_index=1,
        is_active=True,
    )
    test_session.add(lesson_b)
    test_session.flush()

    content_b = Content(
        lesson_id=lesson_b.id,
        title="ClassB Specific Content",
        type=ContentType.READING_ASSESSMENT,
        order_index=1,
        is_active=True,
    )
    test_session.add(content_b)

    test_session.commit()

    return {
        "teacher": teacher,
        "classroom_a": classroom_a,
        "classroom_b": classroom_b,
        "public_content": public_content,
        "content_a": content_a,
        "content_b": content_b,
    }


def test_get_contents_should_not_show_other_classroom_courses(
    test_client: TestClient, teacher_with_two_classrooms
):
    """
    測試 Issue #32: 老師指派作業時不應看到其他班級的非公版課程

    Test Red Phase - 此測試應該失敗，因為目前 API 會錯誤地顯示 ClassB 的課程
    """
    client = test_client

    teacher = teacher_with_two_classrooms["teacher"]
    classroom_a = teacher_with_two_classrooms["classroom_a"]
    public_content = teacher_with_two_classrooms["public_content"]
    content_a = teacher_with_two_classrooms["content_a"]
    content_b = teacher_with_two_classrooms["content_b"]

    # 建立 JWT token
    token = create_access_token({"sub": str(teacher.id), "type": "teacher"})

    # 呼叫 API: 取得 ClassA 的可用內容
    response = client.get(
        f"/api/teachers/contents?classroom_id={classroom_a.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    contents = response.json()

    # 提取所有 content IDs
    content_ids = [c["id"] for c in contents]

    # ✅ 應該包含公版模板內容
    assert (
        public_content.id in content_ids
    ), f"❌ 公版模板內容應該出現在 ClassA 的列表中 (Expected: {public_content.id}, Got: {content_ids})"

    # ✅ 應該包含 ClassA 專屬內容
    assert (
        content_a.id in content_ids
    ), f"❌ ClassA 專屬內容應該出現在列表中 (Expected: {content_a.id}, Got: {content_ids})"

    # ❌ 不應該包含 ClassB 專屬內容 (這裡會失敗，因為目前 API 有 bug)
    assert (
        content_b.id not in content_ids
    ), f"❌ ClassB 專屬內容不應該出現在 ClassA 的列表中 (Unexpected: {content_b.id} in {content_ids})"

    # 驗證返回的內容標題
    content_titles = [c["title"] for c in contents]
    assert "Public Template Content" in content_titles
    assert "ClassA Specific Content" in content_titles
    assert (
        "ClassB Specific Content" not in content_titles
    ), "❌ ClassB 的課程不應該出現在 ClassA 的列表中"


def test_get_contents_without_classroom_id_should_show_all(
    test_client: TestClient, teacher_with_two_classrooms
):
    """
    測試：不指定 classroom_id 時，應該顯示教師所有的內容（包含所有班級）
    這是舊行為，應該保持不變
    """
    client = test_client

    teacher = teacher_with_two_classrooms["teacher"]
    public_content = teacher_with_two_classrooms["public_content"]
    content_a = teacher_with_two_classrooms["content_a"]
    content_b = teacher_with_two_classrooms["content_b"]

    # 建立 JWT token
    token = create_access_token({"sub": str(teacher.id), "type": "teacher"})

    # 呼叫 API: 不指定 classroom_id
    response = client.get(
        "/api/teachers/contents",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    contents = response.json()

    # 提取所有 content IDs
    content_ids = [c["id"] for c in contents]

    # 應該包含所有內容（公版 + ClassA + ClassB）
    assert public_content.id in content_ids, "應該包含公版模板內容"
    assert content_a.id in content_ids, "應該包含 ClassA 專屬內容"
    assert content_b.id in content_ids, "應該包含 ClassB 專屬內容"
