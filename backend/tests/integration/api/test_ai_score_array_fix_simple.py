"""
簡化的 TDD 測試：驗證 AI 評分統一陣列格式修復
測試修改後的 students.py 邏輯

注意: 此測試針對舊架構的陣列格式問題，新架構已不存在此問題。
保留此測試僅供歷史參考。
"""

import pytest
from sqlalchemy.orm import Session
from models import (
    Teacher,
    Student,
    Program,
    Lesson,
    Content,
    Assignment,
    StudentAssignment,
    StudentContentProgress,
    AssignmentContent,
)

# 標記整個模組為跳過
pytestmark = pytest.mark.skip(
    reason="Deprecated: Array format issue fixed in old architecture, not relevant for new StudentItemProgress model"
)


def test_ai_score_unified_array_logic_simulation(db_session: Session):
    """模擬修改後的邏輯，確保 AI 評分使用統一陣列格式"""

    # 創建基本測試數據
    teacher = Teacher(
        username="test_teacher",
        email="teacher@test.com",
        hashed_password="hashed",
        role="teacher",
    )
    db_session.add(teacher)
    db_session.commit()

    student = Student(
        username="test_student",
        email="student@test.com",
        hashed_password="hashed",
        role="student",
    )
    db_session.add(student)
    db_session.commit()

    # 創建課程內容
    program = Program(
        title="Test Program",
        description="Test",
        teacher_id=teacher.id,
        level="beginner",
    )
    db_session.add(program)
    db_session.commit()

    lesson = Lesson(
        title="Test Lesson", description="Test", program_id=program.id, order_index=1
    )
    db_session.add(lesson)
    db_session.commit()

    # 創建兩個 content（模擬兩個 activity）
    content1 = Content(
        lesson_id=lesson.id,
        type="pronunciation",
        title="Be Verbs and Simple Present",
        items=[
            {"text": "I am a student", "translation": "我是學生"},
            {"text": "You are happy", "translation": "你很快樂"},
        ],
        order_index=1,
    )
    db_session.add(content1)

    content2 = Content(
        lesson_id=lesson.id,
        type="pronunciation",
        title="Articles and Nouns",
        items=[
            {"text": "The cat is sleeping", "translation": "貓在睡覺"},
            {"text": "A bird is flying", "translation": "鳥在飛"},
        ],
        order_index=2,
    )
    db_session.add(content2)
    db_session.commit()

    # 創建作業
    assignment = Assignment(
        title="Test Assignment",
        description="Test",
        teacher_id=teacher.id,
        classroom_id=1,  # 模擬
    )
    db_session.add(assignment)
    db_session.commit()

    # 關聯 content 到 assignment
    assignment_content1 = AssignmentContent(
        assignment_id=assignment.id, content_id=content1.id, order_index=1
    )
    assignment_content2 = AssignmentContent(
        assignment_id=assignment.id, content_id=content2.id, order_index=2
    )
    db_session.add_all([assignment_content1, assignment_content2])
    db_session.commit()

    # 創建學生作業
    student_assignment = StudentAssignment(
        student_id=student.id, assignment_id=assignment.id, status="in_progress"
    )
    db_session.add(student_assignment)
    db_session.commit()

    # 關鍵測試：創建使用新格式的 StudentContentProgress
    # 第一個 content：第二題有錄音和 AI 評分
    progress1 = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content1.id,
        status="completed",
        response_data={
            "recordings": ["", "https://gcs.bucket.com/recording1.webm"],  # 第二題有錄音
            "answers": ["", "You are happy"],
            "ai_assessments": [  # 使用新的陣列格式
                None,  # 第一題沒有評分
                {
                    "accuracy_score": 85.5,
                    "fluency_score": 78.9,
                    "pronunciation_score": 90.2,
                },  # 第二題有評分
            ],
        },
    )
    db_session.add(progress1)

    # 第二個 content：第一題有錄音和 AI 評分
    progress2 = StudentContentProgress(
        student_assignment_id=student_assignment.id,
        content_id=content2.id,
        status="completed",
        response_data={
            "recordings": ["https://gcs.bucket.com/recording2.webm", ""],  # 第一題有錄音
            "answers": ["The cat is sleeping", ""],
            "ai_assessments": [  # 使用新的陣列格式
                {
                    "accuracy_score": 92.0,
                    "fluency_score": 89.0,
                    "pronunciation_score": 88.5,
                },  # 第一題有評分
                None,  # 第二題沒有評分
            ],
        },
    )
    db_session.add(progress2)
    db_session.commit()

    # 模擬修改後的 students.py 邏輯
    activities = []

    for assignment_content in [assignment_content1, assignment_content2]:
        content = assignment_content.content
        progress = (
            db_session.query(StudentContentProgress)
            .filter(
                StudentContentProgress.content_id == content.id,
                StudentContentProgress.student_assignment_id == student_assignment.id,
            )
            .first()
        )

        activity_data = {
            "id": content.id,
            "title": content.title,
            "type": content.type,
        }

        # 修改後的統一邏輯
        if content.items and isinstance(content.items, list) and len(content.items) > 0:
            # 多題目情況
            activity_data["items"] = content.items
            activity_data["item_count"] = len(content.items)
            activity_data["content"] = ""
            activity_data["target_text"] = ""
        else:
            # 單題目情況 - 也統一為陣列模式
            single_item = {
                "text": str(content.items) if content.items else "",
                "translation": "",
            }
            activity_data["items"] = [single_item]
            activity_data["item_count"] = 1
            activity_data["content"] = ""
            activity_data["target_text"] = ""

        # 統一處理錄音和 AI 評分（一律使用陣列模式）
        if progress and progress.response_data:
            # 處理錄音
            recordings = progress.response_data.get("recordings", [])
            audio_url = progress.response_data.get("audio_url")

            # 如果是舊格式的 audio_url，轉換為陣列格式
            if audio_url and not recordings:
                recordings = [audio_url]

            activity_data["recordings"] = recordings
            activity_data["answers"] = progress.response_data.get("answers", [])

            # 處理 AI 評分 - 統一從 response_data 中讀取陣列格式
            ai_assessments = progress.response_data.get("ai_assessments", [])
            activity_data["ai_assessments"] = ai_assessments
        else:
            # 沒有 response_data 的情況
            activity_data["recordings"] = []
            activity_data["answers"] = []
            activity_data["ai_assessments"] = []

        activities.append(activity_data)

    # 驗證結果
    assert len(activities) == 2

    # 第一個 activity (Be Verbs)
    activity1 = activities[0]
    assert activity1["title"] == "Be Verbs and Simple Present"
    assert activity1["item_count"] == 2
    assert len(activity1["recordings"]) == 2
    assert activity1["recordings"] == ["", "https://gcs.bucket.com/recording1.webm"]

    # 關鍵驗證：AI 評分在正確位置
    ai_assessments1 = activity1["ai_assessments"]
    assert len(ai_assessments1) == 2
    assert ai_assessments1[0] is None  # 第一題沒有評分
    assert ai_assessments1[1]["accuracy_score"] == 85.5  # 第二題有評分

    # 第二個 activity (Articles)
    activity2 = activities[1]
    assert activity2["title"] == "Articles and Nouns"
    assert activity2["item_count"] == 2
    assert activity2["recordings"] == ["https://gcs.bucket.com/recording2.webm", ""]

    # 關鍵驗證：AI 評分在正確位置，不會互相污染
    ai_assessments2 = activity2["ai_assessments"]
    assert len(ai_assessments2) == 2
    assert ai_assessments2[0]["accuracy_score"] == 92.0  # 第一題有評分
    assert ai_assessments2[1] is None  # 第二題沒有評分

    # 最重要的驗證：確保不同 activity 的評分不會錯位
    assert (
        activity1["ai_assessments"][1]["accuracy_score"]
        != activity2["ai_assessments"][0]["accuracy_score"]
    )
    assert activity1["ai_assessments"][1]["accuracy_score"] == 85.5
    assert activity2["ai_assessments"][0]["accuracy_score"] == 92.0


def test_legacy_audio_url_conversion():
    """測試舊格式 audio_url 轉換為陣列格式的邏輯"""

    # 模擬舊格式數據
    response_data = {
        "audio_url": "https://gcs.bucket.com/legacy.webm",
        "answers": ["Legacy answer"]
        # 沒有 recordings 和 ai_assessments
    }

    # 模擬轉換邏輯
    recordings = response_data.get("recordings", [])
    audio_url = response_data.get("audio_url")

    if audio_url and not recordings:
        recordings = [audio_url]

    ai_assessments = response_data.get("ai_assessments", [])

    # 驗證轉換結果
    assert recordings == ["https://gcs.bucket.com/legacy.webm"]
    assert ai_assessments == []


def test_single_item_array_format():
    """測試單題目也使用陣列格式"""

    # 模擬單題目 content
    content_items = "Hello world"  # 單一字符串

    # 模擬轉換邏輯
    if isinstance(content_items, list) and len(content_items) > 0:
        items = content_items
        item_count = len(content_items)
    else:
        # 單題目情況 - 統一為陣列模式
        single_item = {
            "text": str(content_items) if content_items else "",
            "translation": "",
        }
        items = [single_item]
        item_count = 1

    # 驗證結果
    assert item_count == 1
    assert len(items) == 1
    assert items[0]["text"] == "Hello world"

    # 模擬對應的 response_data
    response_data = {
        "recordings": ["https://gcs.bucket.com/single.webm"],
        "ai_assessments": [{"accuracy_score": 95.0}],
    }

    recordings = response_data.get("recordings", [])
    ai_assessments = response_data.get("ai_assessments", [])

    assert len(recordings) == 1
    assert len(ai_assessments) == 1
    assert ai_assessments[0]["accuracy_score"] == 95.0
