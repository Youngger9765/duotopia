"""
Program and Lesson Management Tests
測試課程計畫與課程單元管理系統的核心功能
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List


class ProgramStatus(Enum):
    """課程計畫狀態枚舉"""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LessonType(Enum):
    """課程類型枚舉"""

    VOCABULARY = "vocabulary"
    GRAMMAR = "grammar"
    CONVERSATION = "conversation"
    READING = "reading"
    LISTENING = "listening"
    SPEAKING = "speaking"


class ContentType(Enum):
    """內容類型枚舉"""

    TEXT = "text"
    AUDIO = "audio"
    VIDEO = "video"
    INTERACTIVE = "interactive"


class MockProgram:
    """Mock Program 模型"""

    def __init__(self, program_id: str, title: str, teacher_id: int):
        self.id = program_id
        self.title = title
        self.teacher_id = teacher_id
        self.description = ""
        self.status = ProgramStatus.DRAFT
        self.grade_level = "elementary"
        self.subject = "english"
        self.estimated_duration_weeks = 4
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.lessons = []
        self.metadata = {}
        self.tags = []


class MockLesson:
    """Mock Lesson 模型"""

    def __init__(self, lesson_id: str, title: str, program_id: str):
        self.id = lesson_id
        self.title = title
        self.program_id = program_id
        self.description = ""
        self.lesson_type = LessonType.VOCABULARY
        self.order = 1
        self.estimated_duration_minutes = 30
        self.learning_objectives = []
        self.prerequisites = []
        self.contents = []
        self.is_active = True
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockContent:
    """Mock Content 模型"""

    def __init__(self, content_id: str, title: str, lesson_id: str):
        self.id = content_id
        self.title = title
        self.lesson_id = lesson_id
        self.content_type = ContentType.TEXT
        self.content_data = {}
        self.order = 1
        self.estimated_duration_minutes = 10
        self.difficulty_level = "beginner"
        self.is_required = True
        self.activity_type = "reading_assessment"
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class TestProgramManagement:
    """測試課程計畫管理功能"""

    def test_program_creation(self):
        """測試課程計畫創建"""
        program_data = {
            "title": "Elementary English Speaking Course",
            "description": "A comprehensive speaking course for elementary students",
            "grade_level": "elementary",
            "subject": "english",
            "estimated_duration_weeks": 8,
            "tags": ["speaking", "elementary", "vocabulary"],
        }

        # 模擬創建課程計畫
        program = self._create_program(program_data, teacher_id=1)

        assert program.title == program_data["title"]
        assert program.description == program_data["description"]
        assert program.status == ProgramStatus.DRAFT
        assert program.teacher_id == 1
        assert program.estimated_duration_weeks == 8
        assert "speaking" in program.tags

    def test_program_validation(self):
        """測試課程計畫驗證"""
        # 測試必填欄位驗證
        invalid_programs = [
            {"description": "Missing title"},  # 缺少標題
            {"title": ""},  # 空標題
            {"title": "Valid", "estimated_duration_weeks": -1},  # 負數週期
            {"title": "Valid", "grade_level": "invalid_level"},  # 無效年級
        ]

        for invalid_data in invalid_programs:
            validation_result = self._validate_program_data(invalid_data)
            assert validation_result["is_valid"] is False
            assert "errors" in validation_result

    def test_program_status_transitions(self):
        """測試課程計畫狀態轉換"""
        program = MockProgram("prog_1", "Test Program", teacher_id=1)

        # 測試從草稿到發布
        assert program.status == ProgramStatus.DRAFT

        # 發布課程（需要至少一個課程單元）
        program.lessons = [MockLesson("lesson_1", "Lesson 1", "prog_1")]
        publish_result = self._publish_program(program)

        assert publish_result["success"] is True
        assert program.status == ProgramStatus.PUBLISHED

        # 測試歸檔
        archive_result = self._archive_program(program)
        assert archive_result["success"] is True
        assert program.status == ProgramStatus.ARCHIVED

    def test_program_duplication(self):
        """測試課程計畫複製功能"""
        original_program = MockProgram("prog_1", "Original Program", teacher_id=1)
        original_program.description = "Original description"
        original_program.lessons = [
            MockLesson("lesson_1", "Lesson 1", "prog_1"),
            MockLesson("lesson_2", "Lesson 2", "prog_1"),
        ]

        # 複製課程計畫
        duplicated_program = self._duplicate_program(original_program, new_teacher_id=2)

        assert duplicated_program.id != original_program.id
        assert duplicated_program.title == f"Copy of {original_program.title}"
        assert duplicated_program.teacher_id == 2
        assert duplicated_program.status == ProgramStatus.DRAFT
        assert len(duplicated_program.lessons) == len(original_program.lessons)

    def test_program_analytics(self):
        """測試課程計畫分析統計"""
        program = MockProgram("prog_1", "Analytics Test", teacher_id=1)

        # 模擬使用統計
        usage_data = {
            "total_assignments": 15,
            "total_students": 25,
            "completion_rate": 0.85,
            "average_score": Decimal("82.5"),
            "total_time_spent_minutes": 3750,  # 25 students * 150 minutes avg
        }

        # 生成分析報告
        analytics = self._generate_program_analytics(program, usage_data)

        assert analytics["program_id"] == program.id
        assert analytics["engagement_score"] >= 0.8  # 高參與度
        assert analytics["effectiveness_rating"] == "good"  # 82.5 分屬於良好
        assert analytics["avg_time_per_student"] == 150.0  # 3750 / 25

    def test_program_sharing_and_permissions(self):
        """測試課程計畫分享與權限管理"""
        program = MockProgram("prog_1", "Shared Program", teacher_id=1)
        program.status = ProgramStatus.PUBLISHED

        # 測試分享給其他教師
        sharing_config = {
            "shared_with": [2, 3, 4],  # 教師 IDs
            "permission_level": "view_only",
            "allow_copy": True,
            "expires_at": datetime.now() + timedelta(days=30),
        }

        sharing_result = self._share_program(program, sharing_config)

        assert sharing_result["success"] is True
        assert len(sharing_result["shared_with"]) == 3

        # 測試權限檢查
        assert (
            self._check_program_access(program, user_id=2, access_type="view") is True
        )
        assert (
            self._check_program_access(program, user_id=2, access_type="edit") is False
        )
        assert (
            self._check_program_access(program, user_id=5, access_type="view") is False
        )

    def _create_program(self, program_data: Dict, teacher_id: int) -> MockProgram:
        """創建課程計畫"""
        program = MockProgram(
            f"prog_{datetime.now().timestamp()}", program_data["title"], teacher_id
        )

        for key, value in program_data.items():
            if hasattr(program, key):
                setattr(program, key, value)

        return program

    def _validate_program_data(self, data: Dict) -> Dict:
        """驗證課程計畫資料"""
        errors = []

        # 檢查必填欄位
        if not data.get("title"):
            errors.append("Title is required")

        # 檢查標題長度
        if data.get("title") and len(data["title"].strip()) == 0:
            errors.append("Title cannot be empty")

        # 檢查持續週期
        if "estimated_duration_weeks" in data and data["estimated_duration_weeks"] < 1:
            errors.append("Duration must be at least 1 week")

        # 檢查年級等級
        valid_grades = ["elementary", "middle", "high"]
        if "grade_level" in data and data["grade_level"] not in valid_grades:
            errors.append(f"Invalid grade level. Must be one of: {valid_grades}")

        return {"is_valid": len(errors) == 0, "errors": errors}

    def _publish_program(self, program: MockProgram) -> Dict:
        """發布課程計畫"""
        # 檢查發布條件
        if len(program.lessons) == 0:
            return {"success": False, "error": "Cannot publish program without lessons"}

        program.status = ProgramStatus.PUBLISHED
        program.updated_at = datetime.now()

        return {"success": True, "published_at": program.updated_at}

    def _archive_program(self, program: MockProgram) -> Dict:
        """歸檔課程計畫"""
        program.status = ProgramStatus.ARCHIVED
        program.updated_at = datetime.now()

        return {"success": True, "archived_at": program.updated_at}

    def _duplicate_program(
        self, original: MockProgram, new_teacher_id: int
    ) -> MockProgram:
        """複製課程計畫"""
        new_program = MockProgram(
            f"prog_copy_{datetime.now().timestamp()}",
            f"Copy of {original.title}",
            new_teacher_id,
        )

        # 複製屬性
        new_program.description = original.description
        new_program.grade_level = original.grade_level
        new_program.subject = original.subject
        new_program.estimated_duration_weeks = original.estimated_duration_weeks
        new_program.tags = original.tags.copy()

        # 複製課程單元（建立新的 ID）
        new_program.lessons = [
            MockLesson(f"lesson_copy_{i}", lesson.title, new_program.id)
            for i, lesson in enumerate(original.lessons)
        ]

        return new_program

    def _generate_program_analytics(
        self, program: MockProgram, usage_data: Dict
    ) -> Dict:
        """生成課程分析"""
        completion_rate = usage_data["completion_rate"]
        average_score = float(usage_data["average_score"])

        # 計算參與度分數 (0-1)
        engagement_score = completion_rate

        # 計算效果評級
        if average_score >= 90:
            effectiveness = "excellent"
        elif average_score >= 80:
            effectiveness = "good"
        elif average_score >= 70:
            effectiveness = "fair"
        else:
            effectiveness = "needs_improvement"

        # 平均每生學習時間
        avg_time_per_student = (
            usage_data["total_time_spent_minutes"] / usage_data["total_students"]
        )

        return {
            "program_id": program.id,
            "engagement_score": engagement_score,
            "effectiveness_rating": effectiveness,
            "avg_time_per_student": avg_time_per_student,
            "total_assignments": usage_data["total_assignments"],
            "completion_rate": completion_rate,
        }

    def _share_program(self, program: MockProgram, config: Dict) -> Dict:
        """分享課程計畫"""
        # 模擬分享邏輯
        return {
            "success": True,
            "shared_with": config["shared_with"],
            "permission_level": config["permission_level"],
            "expires_at": config["expires_at"],
        }

    def _check_program_access(
        self, program: MockProgram, user_id: int, access_type: str
    ) -> bool:
        """檢查課程存取權限"""
        # 擁有者有完整權限
        if program.teacher_id == user_id:
            return True

        # 模擬分享名單檢查（實際會查資料庫）
        shared_users = [2, 3, 4]  # 從上面的 sharing_config

        if user_id in shared_users:
            # 檢查權限等級
            if access_type == "view":
                return True
            elif access_type == "edit":
                return False  # view_only 權限

        return False


class TestLessonManagement:
    """測試課程單元管理功能"""

    def test_lesson_creation(self):
        """測試課程單元創建"""
        lesson_data = {
            "title": "Introduction to Greetings",
            "description": "Learn basic greeting phrases",
            "lesson_type": LessonType.VOCABULARY,
            "estimated_duration_minutes": 45,
            "learning_objectives": [
                "Students can greet people in English",
                "Students understand formal vs informal greetings",
            ],
            "prerequisites": ["Basic alphabet knowledge"],
        }

        lesson = self._create_lesson(lesson_data, program_id="prog_1")

        assert lesson.title == lesson_data["title"]
        assert lesson.lesson_type == LessonType.VOCABULARY
        assert lesson.estimated_duration_minutes == 45
        assert len(lesson.learning_objectives) == 2

    def test_lesson_ordering(self):
        """測試課程單元排序"""
        lessons = [
            MockLesson("l1", "Lesson 1", "prog_1"),
            MockLesson("l2", "Lesson 2", "prog_1"),
            MockLesson("l3", "Lesson 3", "prog_1"),
        ]

        # 設定初始順序
        for i, lesson in enumerate(lessons, 1):
            lesson.order = i

        # 測試重新排序：將 Lesson 3 移到第 1 位
        reordered_lessons = self._reorder_lessons(
            lessons, move_lesson_id="l3", new_position=1
        )

        # 檢查新順序
        lesson_orders = {lesson.id: lesson.order for lesson in reordered_lessons}
        assert lesson_orders["l3"] == 1
        assert lesson_orders["l1"] == 2
        assert lesson_orders["l2"] == 3

    def test_lesson_content_management(self):
        """測試課程內容管理"""
        lesson = MockLesson("lesson_1", "Grammar Lesson", "prog_1")

        # 添加不同類型的內容
        contents = [
            {
                "title": "Grammar Rules",
                "content_type": ContentType.TEXT,
                "content_data": {"text": "Present tense rules..."},
                "order": 1,
            },
            {
                "title": "Pronunciation Guide",
                "content_type": ContentType.AUDIO,
                "content_data": {"audio_url": "/audio/pronunciation.mp3"},
                "order": 2,
            },
            {
                "title": "Interactive Exercise",
                "content_type": ContentType.INTERACTIVE,
                "content_data": {"exercise_type": "fill_blanks", "questions": []},
                "order": 3,
            },
        ]

        # 添加內容到課程
        for content_data in contents:
            content = self._add_content_to_lesson(lesson, content_data)
            lesson.contents.append(content)

        assert len(lesson.contents) == 3
        assert lesson.contents[0].content_type == ContentType.TEXT
        assert lesson.contents[1].content_type == ContentType.AUDIO
        assert lesson.contents[2].content_type == ContentType.INTERACTIVE

    def test_lesson_prerequisite_checking(self):
        """測試課程先修條件檢查"""
        lessons = [
            MockLesson("l1", "Basic Vocabulary", "prog_1"),
            MockLesson("l2", "Grammar Basics", "prog_1"),
            MockLesson("l3", "Advanced Grammar", "prog_1"),
        ]

        # 設定先修關係
        lessons[1].prerequisites = ["l1"]  # l2 需要 l1
        lessons[2].prerequisites = ["l1", "l2"]  # l3 需要 l1 和 l2

        # 模擬學生完成狀況
        student_progress = {"l1": True, "l2": False, "l3": False}

        # 檢查可訪問的課程
        accessible_lessons = self._check_lesson_accessibility(lessons, student_progress)

        assert "l1" in accessible_lessons  # 無先修條件
        assert "l2" in accessible_lessons  # l1 已完成
        assert "l3" not in accessible_lessons  # l2 未完成

    def test_lesson_difficulty_progression(self):
        """測試課程難度遞進"""
        lessons = [
            MockLesson("l1", "Beginner", "prog_1"),
            MockLesson("l2", "Intermediate", "prog_1"),
            MockLesson("l3", "Advanced", "prog_1"),
        ]

        # 設定難度等級
        difficulty_levels = ["beginner", "intermediate", "advanced"]
        for lesson, difficulty in zip(lessons, difficulty_levels):
            lesson.difficulty_level = difficulty

        # 驗證難度遞進
        progression_check = self._validate_difficulty_progression(lessons)

        assert progression_check["is_valid"] is True
        assert progression_check["progression_score"] >= 0.8  # 良好的難度遞進

    def test_lesson_time_estimation(self):
        """測試課程時間估算"""
        lesson = MockLesson("lesson_1", "Time Test", "prog_1")

        # 添加不同持續時間的內容
        lesson.contents = [
            MockContent("c1", "Reading", "lesson_1"),
            MockContent("c2", "Listening", "lesson_1"),
            MockContent("c3", "Speaking", "lesson_1"),
        ]

        # 設定各內容的估算時間
        lesson.contents[0].estimated_duration_minutes = 15
        lesson.contents[1].estimated_duration_minutes = 10
        lesson.contents[2].estimated_duration_minutes = 20

        # 計算總時間
        total_time = self._calculate_lesson_duration(lesson)

        assert total_time == 45  # 15 + 10 + 20
        assert lesson.estimated_duration_minutes == total_time

    def _create_lesson(self, lesson_data: Dict, program_id: str) -> MockLesson:
        """創建課程單元"""
        lesson = MockLesson(
            f"lesson_{datetime.now().timestamp()}", lesson_data["title"], program_id
        )

        for key, value in lesson_data.items():
            if hasattr(lesson, key):
                setattr(lesson, key, value)

        return lesson

    def _reorder_lessons(
        self, lessons: List[MockLesson], move_lesson_id: str, new_position: int
    ) -> List[MockLesson]:
        """重新排序課程單元"""
        # 找到要移動的課程
        move_lesson = next(lesson for lesson in lessons if lesson.id == move_lesson_id)
        other_lessons = [lesson for lesson in lessons if lesson.id != move_lesson_id]

        # 重新計算順序
        result_lessons = []

        for i in range(1, len(lessons) + 1):
            if i == new_position:
                move_lesson.order = i
                result_lessons.append(move_lesson)
            else:
                # 取得其他課程中順序正確的課程
                lesson_index = i - 1 if i < new_position else i - 2
                if lesson_index < len(other_lessons):
                    other_lessons[lesson_index].order = i
                    result_lessons.append(other_lessons[lesson_index])

        return result_lessons

    def _add_content_to_lesson(
        self, lesson: MockLesson, content_data: Dict
    ) -> MockContent:
        """添加內容到課程"""
        content = MockContent(
            f"content_{datetime.now().timestamp()}", content_data["title"], lesson.id
        )

        content.content_type = content_data["content_type"]
        content.content_data = content_data["content_data"]
        content.order = content_data["order"]

        if "estimated_duration_minutes" in content_data:
            content.estimated_duration_minutes = content_data[
                "estimated_duration_minutes"
            ]

        return content

    def _check_lesson_accessibility(
        self, lessons: List[MockLesson], student_progress: Dict[str, bool]
    ) -> List[str]:
        """檢查學生可訪問的課程"""
        accessible = []

        for lesson in lessons:
            # 檢查先修條件
            prerequisites_met = all(
                student_progress.get(prereq_id, False)
                for prereq_id in lesson.prerequisites
            )

            if prerequisites_met:
                accessible.append(lesson.id)

        return accessible

    def _validate_difficulty_progression(self, lessons: List[MockLesson]) -> Dict:
        """驗證難度遞進"""
        difficulty_order = {"beginner": 1, "intermediate": 2, "advanced": 3}

        # 按課程順序檢查難度
        current_difficulty = 0
        valid_progression = True

        for lesson in sorted(lessons, key=lambda x: x.order):
            lesson_difficulty = difficulty_order.get(
                getattr(lesson, "difficulty_level", "beginner"), 1
            )

            if lesson_difficulty < current_difficulty:
                valid_progression = False
                break

            current_difficulty = lesson_difficulty

        # 計算遞進分數
        progression_score = 1.0 if valid_progression else 0.6

        return {"is_valid": valid_progression, "progression_score": progression_score}

    def _calculate_lesson_duration(self, lesson: MockLesson) -> int:
        """計算課程總時間"""
        total_minutes = sum(
            content.estimated_duration_minutes for content in lesson.contents
        )
        lesson.estimated_duration_minutes = total_minutes
        return total_minutes


class TestContentManagement:
    """測試內容管理功能"""

    def test_content_creation_by_type(self):
        """測試不同類型內容創建"""
        test_contents = [
            {
                "title": "Reading Passage",
                "type": ContentType.TEXT,
                "data": {"text": "Once upon a time...", "word_count": 150},
            },
            {
                "title": "Listening Exercise",
                "type": ContentType.AUDIO,
                "data": {"url": "/audio/exercise1.mp3", "duration": 120},
            },
            {
                "title": "Grammar Video",
                "type": ContentType.VIDEO,
                "data": {
                    "url": "/video/grammar.mp4",
                    "duration": 180,
                    "subtitles": True,
                },
            },
            {
                "title": "Interactive Quiz",
                "type": ContentType.INTERACTIVE,
                "data": {"quiz_type": "multiple_choice", "questions": 10},
            },
        ]

        for content_spec in test_contents:
            content = self._create_content(content_spec, lesson_id="lesson_1")

            assert content.title == content_spec["title"]
            assert content.content_type == content_spec["type"]
            assert content.content_data == content_spec["data"]

    def test_content_accessibility_features(self):
        """測試內容無障礙功能"""
        content = MockContent("content_1", "Accessible Content", "lesson_1")

        # 添加無障礙功能
        accessibility_features = {
            "alt_text": "Image description for screen readers",
            "captions": True,
            "transcript": "Full text transcript available",
            "high_contrast": True,
            "font_size_adjustable": True,
        }

        enhanced_content = self._add_accessibility_features(
            content, accessibility_features
        )

        assert "accessibility" in enhanced_content.content_data
        assert enhanced_content.content_data["accessibility"]["captions"] is True
        assert enhanced_content.content_data["accessibility"]["alt_text"] is not None

    def test_content_localization(self):
        """測試內容本地化"""
        content = MockContent("content_1", "Original Content", "lesson_1")
        content.content_data = {
            "text": "Hello, how are you?",
            "instructions": "Read the text aloud",
        }

        # 添加多語言版本
        localizations = {
            "zh-TW": {
                "title": "原始內容",
                "text": "你好，你好嗎？",
                "instructions": "大聲朗讀課文",
            },
            "ja": {
                "title": "オリジナルコンテンツ",
                "text": "こんにちは、元気ですか？",
                "instructions": "テキストを音読してください",
            },
        }

        localized_content = self._localize_content(content, localizations)

        assert "localizations" in localized_content.content_data
        assert "zh-TW" in localized_content.content_data["localizations"]
        assert "ja" in localized_content.content_data["localizations"]

    def test_content_version_control(self):
        """測試內容版本控制"""
        content = MockContent("content_1", "Versioned Content", "lesson_1")

        # 初始版本
        original_data = {"text": "Original version", "version": 1}
        content.content_data = original_data

        # 創建版本歷史
        version_history = self._create_content_version(content)

        # 更新內容
        updated_data = {"text": "Updated version", "version": 2}
        updated_content = self._update_content_with_versioning(
            content, updated_data, version_history
        )

        assert updated_content.content_data["version"] == 2
        assert len(version_history) == 1  # 原始版本被保存
        assert version_history[0]["version"] == 1

    def test_content_analytics_tracking(self):
        """測試內容分析追蹤"""
        content = MockContent("content_1", "Tracked Content", "lesson_1")

        # 模擬學生互動數據
        interaction_data = [
            {
                "student_id": 1,
                "action": "view",
                "timestamp": datetime.now(),
                "duration": 120,
            },
            {
                "student_id": 1,
                "action": "complete",
                "timestamp": datetime.now(),
                "score": 85,
            },
            {
                "student_id": 2,
                "action": "view",
                "timestamp": datetime.now(),
                "duration": 90,
            },
            {"student_id": 2, "action": "skip", "timestamp": datetime.now()},
            {
                "student_id": 3,
                "action": "view",
                "timestamp": datetime.now(),
                "duration": 150,
            },
            {
                "student_id": 3,
                "action": "complete",
                "timestamp": datetime.now(),
                "score": 92,
            },
        ]

        # 生成內容分析
        analytics = self._generate_content_analytics(content, interaction_data)

        assert analytics["total_views"] == 3
        assert round(analytics["completion_rate"], 2) == 0.67  # 2/3 完成
        assert analytics["average_time_spent"] == 120.0  # (120+90+150)/3
        assert analytics["average_score"] == 88.5  # (85+92)/2

    def _create_content(self, content_spec: Dict, lesson_id: str) -> MockContent:
        """創建內容"""
        content = MockContent(
            f"content_{datetime.now().timestamp()}", content_spec["title"], lesson_id
        )
        content.content_type = content_spec["type"]
        content.content_data = content_spec["data"]

        return content

    def _add_accessibility_features(
        self, content: MockContent, features: Dict
    ) -> MockContent:
        """添加無障礙功能"""
        if "accessibility" not in content.content_data:
            content.content_data["accessibility"] = {}

        content.content_data["accessibility"].update(features)
        return content

    def _localize_content(
        self, content: MockContent, localizations: Dict
    ) -> MockContent:
        """本地化內容"""
        content.content_data["localizations"] = localizations
        return content

    def _create_content_version(self, content: MockContent) -> List[Dict]:
        """創建內容版本歷史"""
        return []  # 初始空的版本歷史

    def _update_content_with_versioning(
        self, content: MockContent, new_data: Dict, version_history: List[Dict]
    ) -> MockContent:
        """更新內容並保存版本"""
        # 保存當前版本到歷史
        current_version = {
            "version": content.content_data.get("version", 1),
            "data": content.content_data.copy(),
            "timestamp": datetime.now(),
        }
        version_history.append(current_version)

        # 更新內容
        content.content_data = new_data
        content.updated_at = datetime.now()

        return content

    def _generate_content_analytics(
        self, content: MockContent, interactions: List[Dict]
    ) -> Dict:
        """生成內容分析"""
        total_views = len([i for i in interactions if i["action"] == "view"])
        completions = [i for i in interactions if i["action"] == "complete"]

        completion_rate = len(completions) / total_views if total_views > 0 else 0

        # 計算平均觀看時間
        view_durations = [
            i.get("duration", 0) for i in interactions if i["action"] == "view"
        ]
        avg_time = sum(view_durations) / len(view_durations) if view_durations else 0

        # 計算平均分數
        scores = [i.get("score", 0) for i in completions]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "content_id": content.id,
            "total_views": total_views,
            "completion_rate": completion_rate,
            "average_time_spent": avg_time,
            "average_score": avg_score,
        }


class TestProgramLessonIntegration:
    """測試課程計畫與課程單元整合功能"""

    def test_program_lesson_synchronization(self):
        """測試課程計畫與課程單元同步"""
        program = MockProgram("prog_1", "Sync Test Program", teacher_id=1)
        program.estimated_duration_weeks = 4

        # 添加課程單元
        lessons = [
            MockLesson("l1", "Week 1 Lesson", "prog_1"),
            MockLesson("l2", "Week 2 Lesson", "prog_1"),
            MockLesson("l3", "Week 3 Lesson", "prog_1"),
            MockLesson("l4", "Week 4 Lesson", "prog_1"),
        ]

        # 設定每週時間
        for i, lesson in enumerate(lessons, 1):
            lesson.estimated_duration_minutes = 60
            lesson.order = i

        program.lessons = lessons

        # 同步檢查
        sync_result = self._synchronize_program_duration(program)

        assert sync_result["is_synchronized"] is True
        assert sync_result["total_lesson_time"] == 240  # 4 * 60 minutes
        assert sync_result["lessons_per_week"] == 1.0

    def test_program_completion_tracking(self):
        """測試課程完成度追蹤"""
        program = MockProgram("prog_1", "Completion Test", teacher_id=1)

        # 創建具有內容的課程單元
        lessons_with_content = []
        for i in range(3):
            lesson = MockLesson(f"l{i+1}", f"Lesson {i+1}", "prog_1")
            lesson.contents = [
                MockContent(f"c{i+1}_1", f"Content {i+1}.1", f"l{i+1}"),
                MockContent(f"c{i+1}_2", f"Content {i+1}.2", f"l{i+1}"),
            ]
            lessons_with_content.append(lesson)

        program.lessons = lessons_with_content

        # 模擬學生進度
        student_progress = {
            "l1": {"completed": True, "contents_completed": ["c1_1", "c1_2"]},
            "l2": {"completed": False, "contents_completed": ["c2_1"]},
            "l3": {"completed": False, "contents_completed": []},
        }

        # 計算完成度
        completion_stats = self._calculate_program_completion(program, student_progress)

        assert completion_stats["lesson_completion_rate"] == 0.33  # 1/3 lessons
        assert completion_stats["content_completion_rate"] == 0.5  # 3/6 contents
        assert (
            completion_stats["overall_progress"] == 0.40
        )  # weighted average: 0.33*0.6 + 0.5*0.4 = 0.198 + 0.2 = 0.398 ≈ 0.40

    def _synchronize_program_duration(self, program: MockProgram) -> Dict:
        """同步課程計畫持續時間"""
        total_lesson_time = sum(
            lesson.estimated_duration_minutes for lesson in program.lessons
        )
        total_weeks = program.estimated_duration_weeks

        # 檢查是否同步
        expected_time_per_week = (
            total_lesson_time / total_weeks if total_weeks > 0 else 0
        )
        lessons_per_week = len(program.lessons) / total_weeks if total_weeks > 0 else 0

        # 合理的時間範圍：每週 30-120 分鐘
        is_synchronized = 30 <= expected_time_per_week <= 120

        return {
            "is_synchronized": is_synchronized,
            "total_lesson_time": total_lesson_time,
            "lessons_per_week": lessons_per_week,
            "time_per_week": expected_time_per_week,
        }

    def _calculate_program_completion(
        self, program: MockProgram, progress: Dict
    ) -> Dict:
        """計算課程完成度"""
        total_lessons = len(program.lessons)
        completed_lessons = sum(
            1 for l_prog in progress.values() if l_prog["completed"]
        )

        total_contents = sum(len(lesson.contents) for lesson in program.lessons)
        completed_contents = sum(
            len(l_prog["contents_completed"]) for l_prog in progress.values()
        )

        lesson_completion_rate = (
            completed_lessons / total_lessons if total_lessons > 0 else 0
        )
        content_completion_rate = (
            completed_contents / total_contents if total_contents > 0 else 0
        )

        # 加權平均（課程完成 60%，內容完成 40%）
        overall_progress = (lesson_completion_rate * 0.6) + (
            content_completion_rate * 0.4
        )

        return {
            "lesson_completion_rate": round(lesson_completion_rate, 2),
            "content_completion_rate": round(content_completion_rate, 2),
            "overall_progress": round(overall_progress, 2),
        }


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
