"""
測試作業管理工作流程的核心邏輯
覆蓋作業創建、分配、提交、批改的完整流程
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from sqlalchemy.orm import Session


class TestAssignmentCreationWorkflow:
    """測試作業創建工作流程"""

    def test_assignment_creation_logic(self):
        """測試作業創建的核心邏輯"""
        # 模擬作業創建數據
        assignment_data = {
            "title": "英語朗讀練習",
            "description": "練習英語發音和流利度",
            "classroom_id": 1,
            "teacher_id": 1,
            "due_date": datetime.now() + timedelta(days=7),
            "content_ids": [1, 2, 3],
        }

        def create_assignment_logic(data: dict, db: Session) -> dict:
            """模擬作業創建邏輯"""
            # 驗證必要欄位
            required_fields = ["title", "classroom_id", "teacher_id"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"Missing required field: {field}")

            # 創建作業
            assignment_id = 1  # 模擬生成的 ID

            # 創建作業內容關聯
            content_mappings = []
            for idx, content_id in enumerate(data.get("content_ids", [])):
                content_mappings.append(
                    {
                        "assignment_id": assignment_id,
                        "content_id": content_id,
                        "order_index": idx,
                    }
                )

            return {
                "id": assignment_id,
                "title": data["title"],
                "description": data["description"],
                "classroom_id": data["classroom_id"],
                "teacher_id": data["teacher_id"],
                "due_date": data["due_date"],
                "content_mappings": content_mappings,
                "is_active": True,
            }

        # 測試正常創建
        result = create_assignment_logic(assignment_data, Mock())
        assert result["id"] == 1
        assert result["title"] == "英語朗讀練習"
        assert len(result["content_mappings"]) == 3
        assert result["is_active"] is True

        # 測試缺少必要欄位
        invalid_data = {"description": "無標題作業"}
        with pytest.raises(ValueError) as exc_info:
            create_assignment_logic(invalid_data, Mock())
        assert "Missing required field: title" in str(exc_info.value)

    def test_assignment_content_mapping_logic(self):
        """測試作業與內容的關聯邏輯"""

        def map_contents_to_assignment(assignment_id: int, content_ids: list) -> list:
            """處理作業內容關聯"""
            mappings = []
            for index, content_id in enumerate(content_ids):
                mappings.append(
                    {
                        "assignment_id": assignment_id,
                        "content_id": content_id,
                        "order_index": index,
                        "created_at": datetime.now(),
                    }
                )
            return mappings

        # 測試內容關聯
        content_ids = [10, 20, 30]
        mappings = map_contents_to_assignment(1, content_ids)

        assert len(mappings) == 3
        assert mappings[0]["content_id"] == 10
        assert mappings[0]["order_index"] == 0
        assert mappings[2]["content_id"] == 30
        assert mappings[2]["order_index"] == 2

        # 測試空內容列表
        empty_mappings = map_contents_to_assignment(1, [])
        assert len(empty_mappings) == 0


class TestStudentAssignmentDistribution:
    """測試學生作業分配邏輯"""

    def test_distribute_assignment_to_students_logic(self):
        """測試將作業分配給學生的邏輯"""

        def distribute_assignment(assignment_data: dict, student_ids: list) -> list:
            """分配作業給學生"""
            student_assignments = []

            for student_id in student_ids:
                student_assignment = {
                    "assignment_id": assignment_data["id"],
                    "student_id": student_id,
                    "classroom_id": assignment_data["classroom_id"],
                    "title": assignment_data["title"],
                    "instructions": assignment_data.get("description", ""),
                    "due_date": assignment_data.get("due_date"),
                    "status": "NOT_STARTED",
                    "assigned_at": datetime.now(),
                    "is_active": True,
                }
                student_assignments.append(student_assignment)

            return student_assignments

        # 模擬作業數據
        assignment_data = {
            "id": 1,
            "title": "口語練習",
            "description": "練習英語口語表達",
            "classroom_id": 1,
            "due_date": datetime.now() + timedelta(days=3),
        }

        student_ids = [101, 102, 103]

        # 執行分配
        student_assignments = distribute_assignment(assignment_data, student_ids)

        # 驗證結果
        assert len(student_assignments) == 3

        for i, sa in enumerate(student_assignments):
            assert sa["assignment_id"] == 1
            assert sa["student_id"] == student_ids[i]
            assert sa["classroom_id"] == 1
            assert sa["title"] == "口語練習"
            assert sa["status"] == "NOT_STARTED"
            assert sa["is_active"] is True
            assert "assigned_at" in sa

    def test_student_assignment_progress_initialization(self):
        """測試學生作業進度初始化邏輯"""

        def initialize_content_progress(
            student_assignment_id: int, content_ids: list
        ) -> list:
            """為學生作業初始化內容進度"""
            progress_records = []

            for index, content_id in enumerate(content_ids):
                progress = {
                    "student_assignment_id": student_assignment_id,
                    "content_id": content_id,
                    "status": "NOT_STARTED",
                    "order_index": index,
                    "is_locked": index > 0,  # 第一個內容解鎖，其他鎖定
                    "score": None,
                    "checked": None,
                    "started_at": None,
                    "completed_at": None,
                }
                progress_records.append(progress)

            return progress_records

        content_ids = [1, 2, 3, 4]
        progress_records = initialize_content_progress(100, content_ids)

        # 驗證進度記錄
        assert len(progress_records) == 4

        # 第一個內容應該是解鎖的
        assert progress_records[0]["is_locked"] is False
        assert progress_records[0]["order_index"] == 0

        # 其他內容應該是鎖定的
        for i in range(1, 4):
            assert progress_records[i]["is_locked"] is True
            assert progress_records[i]["order_index"] == i
            assert progress_records[i]["status"] == "NOT_STARTED"


class TestAssignmentStatusTransitions:
    """測試作業狀態轉換邏輯"""

    def test_student_assignment_status_workflow(self):
        """測試學生作業狀態轉換工作流程"""

        def update_assignment_status(current_status: str, action: str) -> tuple:
            """更新作業狀態"""
            status_transitions = {
                "NOT_STARTED": {
                    "start": ("IN_PROGRESS", "開始作業"),
                },
                "IN_PROGRESS": {
                    "submit": ("SUBMITTED", "提交作業"),
                    "pause": ("NOT_STARTED", "暫停作業"),
                },
                "SUBMITTED": {
                    "grade": ("GRADED", "批改完成"),
                    "return": ("RETURNED", "退回訂正"),
                },
                "GRADED": {"complete": ("GRADED", "作業已完成")},
                "RETURNED": {"resubmit": ("RESUBMITTED", "重新提交")},
                "RESUBMITTED": {"grade": ("GRADED", "重新批改完成")},
            }

            if current_status not in status_transitions:
                raise ValueError(f"Invalid current status: {current_status}")

            if action not in status_transitions[current_status]:
                raise ValueError(
                    f"Invalid action '{action}' for status '{current_status}'"
                )

            new_status, message = status_transitions[current_status][action]
            return new_status, message, datetime.now()

        # 測試正常狀態轉換流程
        # NOT_STARTED -> IN_PROGRESS
        status, msg, timestamp = update_assignment_status("NOT_STARTED", "start")
        assert status == "IN_PROGRESS"
        assert "開始作業" in msg

        # IN_PROGRESS -> SUBMITTED
        status, msg, timestamp = update_assignment_status("IN_PROGRESS", "submit")
        assert status == "SUBMITTED"
        assert "提交作業" in msg

        # SUBMITTED -> GRADED
        status, msg, timestamp = update_assignment_status("SUBMITTED", "grade")
        assert status == "GRADED"
        assert "批改完成" in msg

        # SUBMITTED -> RETURNED (退回訂正流程)
        status, msg, timestamp = update_assignment_status("SUBMITTED", "return")
        assert status == "RETURNED"
        assert "退回訂正" in msg

        # RETURNED -> RESUBMITTED
        status, msg, timestamp = update_assignment_status("RETURNED", "resubmit")
        assert status == "RESUBMITTED"
        assert "重新提交" in msg

        # 測試無效狀態轉換
        with pytest.raises(ValueError) as exc_info:
            update_assignment_status("GRADED", "start")
        assert "Invalid action 'start' for status 'GRADED'" in str(exc_info.value)

    def test_content_progress_unlocking_logic(self):
        """測試內容進度解鎖邏輯"""

        def unlock_next_content(
            progress_list: list, completed_content_index: int
        ) -> list:
            """解鎖下一個內容"""
            updated_progress = progress_list.copy()

            # 標記當前內容為完成
            if completed_content_index < len(updated_progress):
                updated_progress[completed_content_index]["status"] = "COMPLETED"
                updated_progress[completed_content_index][
                    "completed_at"
                ] = datetime.now()

                # 解鎖下一個內容
                next_index = completed_content_index + 1
                if next_index < len(updated_progress):
                    updated_progress[next_index]["is_locked"] = False

            return updated_progress

        # 初始進度狀態
        initial_progress = [
            {
                "content_id": 1,
                "status": "IN_PROGRESS",
                "is_locked": False,
                "completed_at": None,
            },
            {
                "content_id": 2,
                "status": "NOT_STARTED",
                "is_locked": True,
                "completed_at": None,
            },
            {
                "content_id": 3,
                "status": "NOT_STARTED",
                "is_locked": True,
                "completed_at": None,
            },
        ]

        # 完成第一個內容
        updated_progress = unlock_next_content(initial_progress, 0)

        # 驗證第一個內容標記為完成
        assert updated_progress[0]["status"] == "COMPLETED"
        assert updated_progress[0]["completed_at"] is not None

        # 驗證第二個內容被解鎖
        assert updated_progress[1]["is_locked"] is False

        # 驗證第三個內容仍然鎖定
        assert updated_progress[2]["is_locked"] is True


class TestAssignmentGradingWorkflow:
    """測試作業批改工作流程"""

    def test_assignment_grading_logic(self):
        """測試作業批改邏輯"""

        def grade_assignment(
            student_assignment_id: int, feedback: str, score: float = None
        ) -> dict:
            """批改作業"""
            if not feedback.strip():
                raise ValueError("回饋內容不能為空")

            if score is not None and not (0 <= score <= 100):
                raise ValueError("分數必須在 0-100 之間")

            grading_result = {
                "student_assignment_id": student_assignment_id,
                "feedback": feedback.strip(),
                "score": score,
                "graded_at": datetime.now(),
                "grader_id": 1,  # 模擬教師 ID
                "status": "GRADED",
            }

            return grading_result

        # 測試正常批改
        result = grade_assignment(1, "表現優秀，發音清晰！", 85.5)
        assert result["feedback"] == "表現優秀，發音清晰！"
        assert result["score"] == 85.5
        assert result["status"] == "GRADED"
        assert "graded_at" in result

        # 測試無分數批改
        result = grade_assignment(2, "需要多練習語調變化")
        assert result["feedback"] == "需要多練習語調變化"
        assert result["score"] is None
        assert result["status"] == "GRADED"

        # 測試無效輸入
        with pytest.raises(ValueError) as exc_info:
            grade_assignment(1, "   ", 90)
        assert "回饋內容不能為空" in str(exc_info.value)

        with pytest.raises(ValueError) as exc_info:
            grade_assignment(1, "好的", 150)
        assert "分數必須在 0-100 之間" in str(exc_info.value)

    def test_bulk_grading_logic(self):
        """測試批量批改邏輯"""

        def bulk_grade_assignments(grading_data: list) -> dict:
            """批量批改作業"""
            results = {"successful": [], "failed": [], "total": len(grading_data)}

            for item in grading_data:
                try:
                    student_id = item["student_assignment_id"]
                    feedback = item["feedback"]
                    score = item.get("score")

                    if not feedback.strip():
                        raise ValueError(f"Student {student_id}: 回饋不能為空")

                    if score is not None and not (0 <= score <= 100):
                        raise ValueError(f"Student {student_id}: 分數無效")

                    graded_item = {
                        "student_assignment_id": student_id,
                        "feedback": feedback,
                        "score": score,
                        "graded_at": datetime.now(),
                    }

                    results["successful"].append(graded_item)

                except Exception as e:
                    results["failed"].append(
                        {
                            "student_assignment_id": item.get("student_assignment_id"),
                            "error": str(e),
                        }
                    )

            return results

        # 測試批量批改
        grading_data = [
            {"student_assignment_id": 1, "feedback": "表現優秀", "score": 90},
            {"student_assignment_id": 2, "feedback": "需要改進", "score": 75},
            {"student_assignment_id": 3, "feedback": "", "score": 80},  # 無效：無回饋
            {
                "student_assignment_id": 4,
                "feedback": "不錯",
                "score": 150,
            },  # 無效：分數過高
        ]

        results = bulk_grade_assignments(grading_data)

        # 驗證結果
        assert results["total"] == 4
        assert len(results["successful"]) == 2
        assert len(results["failed"]) == 2

        # 檢查成功的批改
        assert results["successful"][0]["student_assignment_id"] == 1
        assert results["successful"][0]["score"] == 90

        # 檢查失敗的批改
        failed_ids = [item["student_assignment_id"] for item in results["failed"]]
        assert 3 in failed_ids
        assert 4 in failed_ids


class TestAssignmentStatistics:
    """測試作業統計邏輯"""

    def test_assignment_completion_statistics(self):
        """測試作業完成統計邏輯"""

        def calculate_assignment_statistics(student_assignments: list) -> dict:
            """計算作業統計數據"""
            total = len(student_assignments)
            if total == 0:
                return {"total": 0, "completion_rate": 0, "average_score": None}

            status_counts = {}
            scores = []

            for sa in student_assignments:
                status = sa["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

                if sa.get("score") is not None:
                    scores.append(sa["score"])

            completed = status_counts.get("GRADED", 0)
            completion_rate = (completed / total) * 100
            average_score = sum(scores) / len(scores) if scores else None

            return {
                "total": total,
                "status_breakdown": status_counts,
                "completed": completed,
                "completion_rate": round(completion_rate, 2),
                "average_score": round(average_score, 2) if average_score else None,
                "score_count": len(scores),
            }

        # 模擬學生作業數據
        student_assignments = [
            {"student_id": 1, "status": "GRADED", "score": 85.5},
            {"student_id": 2, "status": "GRADED", "score": 92.0},
            {"student_id": 3, "status": "SUBMITTED", "score": None},
            {"student_id": 4, "status": "IN_PROGRESS", "score": None},
            {"student_id": 5, "status": "NOT_STARTED", "score": None},
        ]

        stats = calculate_assignment_statistics(student_assignments)

        # 驗證統計結果
        assert stats["total"] == 5
        assert stats["completed"] == 2
        assert stats["completion_rate"] == 40.0
        assert stats["average_score"] == 88.75  # (85.5 + 92.0) / 2
        assert stats["score_count"] == 2

        # 驗證狀態分佈
        assert stats["status_breakdown"]["GRADED"] == 2
        assert stats["status_breakdown"]["SUBMITTED"] == 1
        assert stats["status_breakdown"]["IN_PROGRESS"] == 1
        assert stats["status_breakdown"]["NOT_STARTED"] == 1

        # 測試空列表
        empty_stats = calculate_assignment_statistics([])
        assert empty_stats["total"] == 0
        assert empty_stats["completion_rate"] == 0
        assert empty_stats["average_score"] is None
