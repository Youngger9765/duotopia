"""
Student Progress Tracking Tests
測試學生學習進度追蹤系統的核心功能
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, List


# Mock schemas and enums for testing
class ActivityType(Enum):
    EXAMPLE_SENTENCES = "EXAMPLE_SENTENCES"
    SPEAKING_PRACTICE = "speaking_practice"
    SPEAKING_SCENARIO = "speaking_scenario"
    LISTENING_CLOZE = "listening_cloze"
    VOCABULARY_SET = "VOCABULARY_SET"
    SPEAKING_QUIZ = "speaking_quiz"


class StudentAssignmentStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    GRADED = "GRADED"


class MockStudentAssignment:
    """Mock StudentAssignment model"""

    def __init__(self):
        self.id = 1
        self.student_id = 1
        self.assignment_id = 1
        self.status = StudentAssignmentStatus.NOT_STARTED
        self.started_at = None
        self.completed_at = None
        self.score = None
        self.feedback = None
        self.activity_results = []
        self.progress_percentage = Decimal("0")
        self.time_spent_minutes = 0


class MockActivityResult:
    """Mock ActivityResult model"""

    def __init__(self, activity_type, score=None, completed_at=None):
        self.id = 1
        self.student_assignment_id = 1
        self.content_id = 1
        self.activity_type = activity_type
        self.score = score if score is not None else Decimal("0")
        self.max_score = Decimal("100")
        self.completed_at = completed_at
        self.attempt_count = 1
        self.time_spent_seconds = 0
        self.ai_feedback = None


class TestStudentProgressCalculation:
    """測試學生進度計算邏輯"""

    def test_assignment_progress_calculation(self):
        """測試作業進度計算"""
        # 模擬學生作業
        MockStudentAssignment()

        # 總共 5 個活動，完成 3 個
        completed_activities = [
            MockActivityResult(
                ActivityType.EXAMPLE_SENTENCES, Decimal("85"), datetime.now()
            ),
            MockActivityResult(
                ActivityType.SPEAKING_PRACTICE, Decimal("78"), datetime.now()
            ),
            MockActivityResult(
                ActivityType.LISTENING_CLOZE, Decimal("92"), datetime.now()
            ),
        ]

        total_activities = 5

        # 測試進度計算邏輯
        progress_percentage = self._calculate_assignment_progress(
            completed_activities, total_activities
        )

        assert progress_percentage == Decimal("60.0")  # 3/5 = 60%

    def test_assignment_score_calculation(self):
        """測試作業總分計算（平均分）"""
        completed_activities = [
            MockActivityResult(ActivityType.EXAMPLE_SENTENCES, Decimal("85")),
            MockActivityResult(ActivityType.SPEAKING_PRACTICE, Decimal("78")),
            MockActivityResult(ActivityType.LISTENING_CLOZE, Decimal("92")),
        ]

        # 測試平均分計算
        average_score = self._calculate_average_score(completed_activities)
        expected_score = Decimal("85.0")  # (85 + 78 + 92) / 3 = 85

        assert average_score == expected_score

    def test_weighted_score_calculation(self):
        """測試加權分數計算（不同活動類型權重不同）"""
        activities_with_weights = [
            (
                MockActivityResult(ActivityType.SPEAKING_QUIZ, Decimal("90")),
                Decimal("0.4"),
            ),  # 口說測驗權重高
            (
                MockActivityResult(ActivityType.EXAMPLE_SENTENCES, Decimal("80")),
                Decimal("0.3"),
            ),  # 朗讀評測中等
            (
                MockActivityResult(ActivityType.LISTENING_CLOZE, Decimal("70")),
                Decimal("0.3"),
            ),  # 聽力填空中等
        ]

        # 測試加權平均計算
        weighted_score = self._calculate_weighted_score(activities_with_weights)
        expected_score = Decimal("81.0")  # 90*0.4 + 80*0.3 + 70*0.3 = 36 + 24 + 21 = 81

        assert weighted_score == expected_score

    def test_time_tracking_calculation(self):
        """測試學習時間統計"""
        activities = [
            MockActivityResult(ActivityType.EXAMPLE_SENTENCES),
            MockActivityResult(ActivityType.SPEAKING_PRACTICE),
            MockActivityResult(ActivityType.LISTENING_CLOZE),
        ]

        # 設置每個活動的學習時間（秒）
        activities[0].time_spent_seconds = 300  # 5 分鐘
        activities[1].time_spent_seconds = 420  # 7 分鐘
        activities[2].time_spent_seconds = 180  # 3 分鐘

        # 計算總學習時間
        total_minutes = self._calculate_total_time_spent(activities)

        assert total_minutes == 15  # (300 + 420 + 180) / 60 = 15 分鐘

    def _calculate_assignment_progress(
        self, completed_activities: List, total_activities: int
    ) -> Decimal:
        """計算作業進度百分比"""
        if total_activities == 0:
            return Decimal("0")

        completed_count = len(completed_activities)
        progress = (completed_count / total_activities) * 100
        return Decimal(str(round(progress, 1)))

    def _calculate_average_score(self, activities: List[MockActivityResult]) -> Decimal:
        """計算平均分數"""
        if not activities:
            return Decimal("0")

        total_score = sum(activity.score for activity in activities)
        return Decimal(str(round(total_score / len(activities), 1)))

    def _calculate_weighted_score(
        self, activities_with_weights: List[tuple]
    ) -> Decimal:
        """計算加權分數"""
        weighted_sum = sum(
            activity.score * weight for activity, weight in activities_with_weights
        )
        return Decimal(str(round(weighted_sum, 1)))

    def _calculate_total_time_spent(self, activities: List[MockActivityResult]) -> int:
        """計算總學習時間（分鐘）"""
        total_seconds = sum(activity.time_spent_seconds for activity in activities)
        return total_seconds // 60


class TestProgressMilestones:
    """測試學習里程碑系統"""

    def test_assignment_completion_milestone(self):
        """測試作業完成里程碑"""
        student_assignment = MockStudentAssignment()
        student_assignment.progress_percentage = Decimal("100")
        student_assignment.completed_at = datetime.now()

        # 測試完成狀態
        is_completed = self._is_assignment_completed(student_assignment)
        assert is_completed is True

        # 測試完成時間記錄
        assert student_assignment.completed_at is not None

    def test_score_based_achievements(self):
        """測試基於分數的成就系統"""
        test_cases = [
            (Decimal("95"), "excellence"),  # 優秀 (>=95)
            (Decimal("85"), "proficient"),  # 熟練 (>=85)
            (Decimal("70"), "developing"),  # 發展中 (>=70)
            (Decimal("60"), "beginning"),  # 初學 (>=60)
            (Decimal("50"), "needs_support"),  # 需要支持 (<60)
        ]

        for score, expected_level in test_cases:
            achievement_level = self._calculate_achievement_level(score)
            assert achievement_level == expected_level

    def test_streak_calculation(self):
        """測試連續學習天數計算"""
        # 模擬連續 5 天的學習記錄
        learning_dates = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            datetime.now() - timedelta(days=1),
            datetime.now(),
        ]

        streak_days = self._calculate_learning_streak(learning_dates)
        assert streak_days == 5

    def test_broken_streak_calculation(self):
        """測試中斷的學習連續天數"""
        # 模擬中斷的學習記錄（缺少昨天）
        learning_dates = [
            datetime.now() - timedelta(days=4),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=2),
            # 缺少 days=1 (昨天)
            datetime.now(),
        ]

        streak_days = self._calculate_learning_streak(learning_dates)
        assert streak_days == 1  # 只有今天算連續

    def _is_assignment_completed(self, assignment: MockStudentAssignment) -> bool:
        """檢查作業是否完成"""
        return (
            assignment.progress_percentage == Decimal("100")
            and assignment.completed_at is not None
        )

    def _calculate_achievement_level(self, score: Decimal) -> str:
        """計算成就等級"""
        if score >= 95:
            return "excellence"
        elif score >= 85:
            return "proficient"
        elif score >= 70:
            return "developing"
        elif score >= 60:
            return "beginning"
        else:
            return "needs_support"

    def _calculate_learning_streak(self, learning_dates: List[datetime]) -> int:
        """計算學習連續天數"""
        if not learning_dates:
            return 0

        # 排序日期（最新在前）
        sorted_dates = sorted(learning_dates, reverse=True)

        # 檢查是否包含今天
        today = datetime.now().date()
        if sorted_dates[0].date() != today:
            return 0

        # 計算連續天數
        streak = 1
        current_date = today

        for i in range(1, len(sorted_dates)):
            expected_date = current_date - timedelta(days=1)
            actual_date = sorted_dates[i].date()

            if actual_date == expected_date:
                streak += 1
                current_date = actual_date
            else:
                break

        return streak


class TestActivitySpecificProgress:
    """測試特定活動類型的進度追蹤"""

    def test_speaking_activity_progress(self):
        """測試口說活動進度（考慮發音準確度、流暢度等）"""
        speaking_result = MockActivityResult(ActivityType.SPEAKING_PRACTICE)

        # 模擬 AI 評分結果
        ai_feedback = {
            "pronunciation_score": 85,
            "fluency_score": 78,
            "accuracy_score": 92,
            "overall_score": 85,
            "areas_for_improvement": ["pronunciation", "speed"],
        }
        speaking_result.ai_feedback = ai_feedback
        speaking_result.score = Decimal("85")

        # 測試口說活動特定的進度計算
        detailed_progress = self._analyze_speaking_progress(speaking_result)

        assert detailed_progress["overall_score"] == 85
        assert detailed_progress["strongest_area"] == "accuracy"
        assert detailed_progress["needs_improvement"] == ["pronunciation", "speed"]

    def test_reading_assessment_progress(self):
        """測試朗讀評測進度"""
        reading_result = MockActivityResult(ActivityType.EXAMPLE_SENTENCES)

        # 模擬朗讀評測結果
        ai_feedback = {
            "word_accuracy": 0.95,  # 字詞準確度 95%
            "pronunciation_quality": 8.2,  # 發音品質 8.2/10
            "reading_speed": 120,  # 每分鐘字數
            "pause_appropriateness": 7.8,  # 停頓適當性
        }
        reading_result.ai_feedback = ai_feedback
        reading_result.score = Decimal("88")

        # 測試朗讀特定的分析
        reading_analysis = self._analyze_reading_progress(reading_result)

        assert reading_analysis["word_accuracy"] == 0.95
        assert reading_analysis["reading_level"] == "proficient"
        assert reading_analysis["reading_speed_category"] == "normal"  # 100-140 wpm 正常

    def test_listening_comprehension_progress(self):
        """測試聽力理解進度"""
        listening_result = MockActivityResult(ActivityType.LISTENING_CLOZE)

        # 模擬聽力填空結果
        listening_data = {
            "correct_answers": 8,
            "total_questions": 10,
            "question_types": {
                "vocabulary": {"correct": 3, "total": 4},
                "grammar": {"correct": 2, "total": 3},
                "comprehension": {"correct": 3, "total": 3},
            },
        }
        listening_result.score = Decimal("80")

        # 測試聽力分析
        listening_analysis = self._analyze_listening_progress(
            listening_result, listening_data
        )

        assert listening_analysis["overall_accuracy"] == 0.8  # 8/10 = 0.8
        assert listening_analysis["strongest_skill"] == "comprehension"  # 3/3 = 100%
        assert listening_analysis["needs_work"] == "grammar"  # 2/3 = 67% (最低)

    def _analyze_speaking_progress(self, result: MockActivityResult) -> Dict:
        """分析口說活動進度"""
        feedback = result.ai_feedback

        # 找出最強和最弱的領域
        scores = {
            "pronunciation": feedback["pronunciation_score"],
            "fluency": feedback["fluency_score"],
            "accuracy": feedback["accuracy_score"],
        }

        strongest = max(scores.items(), key=lambda x: x[1])
        weakest = min(scores.items(), key=lambda x: x[1])

        return {
            "overall_score": feedback["overall_score"],
            "strongest_area": strongest[0],
            "weakest_area": weakest[0],
            "needs_improvement": feedback["areas_for_improvement"],
        }

    def _analyze_reading_progress(self, result: MockActivityResult) -> Dict:
        """分析朗讀進度"""
        feedback = result.ai_feedback

        # 判定閱讀水平
        if result.score >= 90:
            reading_level = "excellent"
        elif result.score >= 80:
            reading_level = "proficient"
        elif result.score >= 70:
            reading_level = "developing"
        else:
            reading_level = "needs_support"

        # 判定閱讀速度類別
        speed = feedback["reading_speed"]
        if speed < 100:
            speed_category = "slow"
        elif speed <= 140:
            speed_category = "normal"
        else:
            speed_category = "fast"

        return {
            "word_accuracy": feedback["word_accuracy"],
            "reading_level": reading_level,
            "reading_speed_category": speed_category,
            "pronunciation_quality": feedback["pronunciation_quality"],
        }

    def _analyze_listening_progress(
        self, result: MockActivityResult, data: Dict
    ) -> Dict:
        """分析聽力理解進度"""
        overall_accuracy = data["correct_answers"] / data["total_questions"]

        # 分析各技能領域表現
        skills_performance = {}
        for skill, stats in data["question_types"].items():
            accuracy = stats["correct"] / stats["total"]
            skills_performance[skill] = accuracy

        # 找出最強和最弱的技能
        strongest_skill = max(skills_performance.items(), key=lambda x: x[1])[0]
        weakest_skill = min(skills_performance.items(), key=lambda x: x[1])[0]

        return {
            "overall_accuracy": overall_accuracy,
            "strongest_skill": strongest_skill,
            "needs_work": weakest_skill,
            "skills_breakdown": skills_performance,
        }


class TestProgressReporting:
    """測試進度報告生成"""

    def test_weekly_progress_report(self):
        """測試週進度報告"""
        # 模擬一週內的活動
        weekly_activities = [
            MockActivityResult(ActivityType.EXAMPLE_SENTENCES, Decimal("85")),
            MockActivityResult(ActivityType.SPEAKING_PRACTICE, Decimal("78")),
            MockActivityResult(ActivityType.LISTENING_CLOZE, Decimal("92")),
            MockActivityResult(ActivityType.SPEAKING_QUIZ, Decimal("88")),
        ]

        # 生成週報告
        weekly_report = self._generate_weekly_report(weekly_activities)

        assert weekly_report["total_activities"] == 4
        assert weekly_report["average_score"] == Decimal("85.8")  # (85+78+92+88)/4
        assert (
            weekly_report["most_practiced_type"]
            == ActivityType.EXAMPLE_SENTENCES.value
        )  # 第一個活動類型（按字母排序）

    def test_monthly_progress_summary(self):
        """測試月度進度摘要"""
        # 模擬一個月的學習數據
        monthly_data = {
            "assignments_completed": 8,
            "total_assignments": 10,
            "average_score": Decimal("83.5"),
            "total_learning_minutes": 420,  # 7 小時
            "activity_breakdown": {
                ActivityType.EXAMPLE_SENTENCES: 12,
                ActivityType.SPEAKING_PRACTICE: 15,
                ActivityType.LISTENING_CLOZE: 8,
                ActivityType.SPEAKING_QUIZ: 5,
            },
        }

        # 生成月報告
        monthly_summary = self._generate_monthly_summary(monthly_data)

        assert monthly_summary["completion_rate"] == Decimal("80.0")  # 8/10 = 80%
        assert monthly_summary["learning_hours"] == 7.0  # 420/60 = 7 小時
        assert (
            monthly_summary["most_active_type"] == ActivityType.SPEAKING_PRACTICE.value
        )

    def test_improvement_trend_analysis(self):
        """測試學習改善趨勢分析"""
        # 模擬時間序列的分數數據（過去 5 週）
        weekly_scores = [
            Decimal("65"),  # 第 1 週
            Decimal("72"),  # 第 2 週
            Decimal("78"),  # 第 3 週
            Decimal("83"),  # 第 4 週
            Decimal("85"),  # 第 5 週（本週）
        ]

        # 分析改善趨勢
        trend_analysis = self._analyze_improvement_trend(weekly_scores)

        assert trend_analysis["trend"] == "improving"  # 持續上升
        assert trend_analysis["improvement_rate"] == Decimal("5.0")  # 平均每週提升 5 分
        assert trend_analysis["total_improvement"] == Decimal("20.0")  # 總共提升 20 分

    def _generate_weekly_report(self, activities: List[MockActivityResult]) -> Dict:
        """生成週進度報告"""
        if not activities:
            return {"total_activities": 0, "average_score": Decimal("0")}

        total_score = sum(activity.score for activity in activities)
        average_score = total_score / len(activities)

        # 統計活動類型
        activity_counts = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1

        most_practiced = (
            max(activity_counts.items(), key=lambda x: x[1])[0]
            if activity_counts
            else None
        )

        return {
            "total_activities": len(activities),
            "average_score": Decimal(str(round(average_score, 1))),
            "most_practiced_type": most_practiced,
        }

    def _generate_monthly_summary(self, data: Dict) -> Dict:
        """生成月度摘要"""
        completion_rate = (
            data["assignments_completed"] / data["total_assignments"]
        ) * 100
        learning_hours = data["total_learning_minutes"] / 60

        # 找出最活躍的活動類型
        most_active_type = max(data["activity_breakdown"].items(), key=lambda x: x[1])[
            0
        ].value

        return {
            "completion_rate": Decimal(str(round(completion_rate, 1))),
            "learning_hours": learning_hours,
            "most_active_type": most_active_type,
            "average_score": data["average_score"],
        }

    def _analyze_improvement_trend(self, weekly_scores: List[Decimal]) -> Dict:
        """分析學習改善趨勢"""
        if len(weekly_scores) < 2:
            return {"trend": "insufficient_data"}

        # 計算總改善
        first_score = weekly_scores[0]
        last_score = weekly_scores[-1]
        total_improvement = last_score - first_score

        # 計算平均改善率
        weeks = len(weekly_scores) - 1
        improvement_rate = total_improvement / weeks

        # 判斷趨勢
        if improvement_rate > 2:
            trend = "improving"
        elif improvement_rate < -2:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "improvement_rate": Decimal(str(round(improvement_rate, 1))),
            "total_improvement": Decimal(str(round(total_improvement, 1))),
        }


if __name__ == "__main__":
    # 執行測試
    pytest.main([__file__, "-v"])
