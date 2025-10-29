"""
Duotopia 專屬測試場景
提供常用的測試流程，可以直接被 MCP 呼叫
"""

from typing import Dict, Any


class DuotopiaScenarios:
    """Duotopia 測試場景集合"""

    @staticmethod
    def teacher_login(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """教師登入流程"""
        return {
            "name": "teacher_login",
            "description": "教師登入流程",
            "steps": [
                {"action": "navigate", "url": f"{base_url}/teacher/login"},
                {"action": "wait_for_selector", "selector": "input[name='email']"},
                {"action": "fill", "selector": "input[name='email']", "value": "teacher@example.com"},
                {"action": "fill", "selector": "input[name='password']", "value": "password"},
                {"action": "click", "selector": "button[type='submit']"},
                {"action": "wait_for_selector", "selector": "text=儀表板"},
                {"action": "screenshot", "path": "/tmp/teacher_logged_in.png"},
            ]
        }

    @staticmethod
    def student_login(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """學生登入流程"""
        return {
            "name": "student_login",
            "description": "學生登入流程",
            "steps": [
                {"action": "navigate", "url": f"{base_url}/student/login"},
                {"action": "wait_for_selector", "selector": "input[name='email']"},
                {"action": "fill", "selector": "input[name='email']", "value": "student@example.com"},
                {"action": "fill", "selector": "input[name='password']", "value": "password"},
                {"action": "click", "selector": "button[type='submit']"},
                {"action": "wait_for_selector", "selector": "text=我的作業"},
                {"action": "screenshot", "path": "/tmp/student_logged_in.png"},
            ]
        }

    @staticmethod
    def add_student_workflow(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """新增學生完整流程（包含登入）"""
        return {
            "name": "add_student_workflow",
            "description": "教師新增學生的完整流程",
            "steps": [
                # 先登入
                *DuotopiaScenarios.teacher_login(base_url)["steps"],
                # 進入班級管理
                {"action": "click", "selector": "a[href*='/teacher/classrooms']"},
                {"action": "wait_for_selector", "selector": "text=班級列表"},
                # 點選第一個班級
                {"action": "click", "selector": "table tbody tr:first-child"},
                {"action": "wait_for_selector", "selector": "text=學生列表"},
                # 點選新增學生
                {"action": "click", "selector": "button:has-text('新增學生')"},
                {"action": "wait_for_selector", "selector": "input[name='name']"},
                # 填寫學生資料
                {"action": "fill", "selector": "input[name='name']", "value": "測試學生A"},
                {"action": "fill", "selector": "input[name='email']", "value": "test-student-a@example.com"},
                {"action": "fill", "selector": "input[name='student_number']", "value": "S001"},
                # 儲存
                {"action": "click", "selector": "button:has-text('儲存')"},
                {"action": "wait_for_selector", "selector": "text=成功"},
                {"action": "screenshot", "path": "/tmp/student_added.png"},
            ]
        }

    @staticmethod
    def create_assignment_workflow(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """派作業完整流程"""
        return {
            "name": "create_assignment_workflow",
            "description": "教師派作業的完整流程",
            "steps": [
                # 先登入
                *DuotopiaScenarios.teacher_login(base_url)["steps"],
                # 進入班級管理
                {"action": "click", "selector": "a[href*='/teacher/classrooms']"},
                {"action": "wait_for_selector", "selector": "text=班級列表"},
                # 點選第一個班級
                {"action": "click", "selector": "table tbody tr:first-child"},
                # 切換到作業管理 tab
                {"action": "click", "selector": "button:has-text('作業管理')"},
                {"action": "wait_for_selector", "selector": "button:has-text('指派新作業')"},
                # 點選指派新作業
                {"action": "click", "selector": "button:has-text('指派新作業')"},
                {"action": "wait_for_selector", "selector": "text=選擇課程內容"},
                {"action": "screenshot", "path": "/tmp/assignment_dialog_opened.png"},
                # 檢查學生列表
                {"action": "click", "selector": "button:has-text('下一步')"},
                {"action": "wait_for_selector", "selector": "text=選擇學生"},
                {"action": "screenshot", "path": "/tmp/assignment_student_list.png"},
            ]
        }

    @staticmethod
    def test_add_student_then_assign(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """測試新增學生後立即派作業（測試修復的 bug）"""
        return {
            "name": "test_add_student_then_assign",
            "description": "測試新增學生後不重新整理頁面，直接派作業是否能看到新學生",
            "steps": [
                # 先登入
                *DuotopiaScenarios.teacher_login(base_url)["steps"],
                # 進入班級詳情
                {"action": "click", "selector": "a[href*='/teacher/classrooms']"},
                {"action": "click", "selector": "table tbody tr:first-child"},
                {"action": "wait_for_selector", "selector": "text=學生列表"},
                # 新增學生
                {"action": "click", "selector": "button:has-text('新增學生')"},
                {"action": "fill", "selector": "input[name='name']", "value": "新學生測試"},
                {"action": "fill", "selector": "input[name='email']", "value": f"new-student-{int(__import__('time').time())}@test.com"},
                {"action": "click", "selector": "button:has-text('儲存')"},
                {"action": "wait_for_selector", "selector": "text=成功"},
                # 不重新整理頁面，直接派作業
                {"action": "click", "selector": "button:has-text('作業管理')"},
                {"action": "click", "selector": "button:has-text('指派新作業')"},
                {"action": "wait_for_selector", "selector": "text=選擇課程內容"},
                # 跳到學生選擇步驟
                {"action": "click", "selector": "button:has-text('下一步')"},
                {"action": "wait_for_selector", "selector": "text=選擇學生"},
                # 截圖學生列表
                {"action": "screenshot", "path": "/tmp/student_list_after_add.png"},
                # 驗證新學生是否出現
                {"action": "execute_js", "code": """
                    const students = Array.from(document.querySelectorAll('button:has-text("新學生測試")'));
                    return {
                        found: students.length > 0,
                        studentCount: students.length
                    };
                """},
            ]
        }

    @staticmethod
    def test_ios_safari_recording(base_url: str = "http://localhost:5173") -> Dict[str, Any]:
        """測試 iOS Safari 錄音功能（模擬 iOS 環境）"""
        return {
            "name": "test_ios_safari_recording",
            "description": "測試 iOS Safari 錄音功能",
            "note": "需要實體 iOS 設備或完整的模擬器支援",
            "steps": [
                # 學生登入
                *DuotopiaScenarios.student_login(base_url)["steps"],
                # 進入作業頁面
                {"action": "click", "selector": "a:has-text('我的作業')"},
                {"action": "wait_for_selector", "selector": "text=作業列表"},
                # 點選第一個作業
                {"action": "click", "selector": "button:first-child"},
                {"action": "wait_for_selector", "selector": "button:has-text('開始錄音')"},
                # 檢查 MediaRecorder API 支援
                {"action": "execute_js", "code": """
                    return {
                        hasMediaRecorder: typeof MediaRecorder !== 'undefined',
                        hasGetUserMedia: typeof navigator.mediaDevices !== 'undefined',
                        userAgent: navigator.userAgent
                    };
                """},
                {"action": "screenshot", "path": "/tmp/ios_recording_check.png"},
            ]
        }


# 快速訪問所有場景
SCENARIOS = {
    "teacher_login": DuotopiaScenarios.teacher_login,
    "student_login": DuotopiaScenarios.student_login,
    "add_student": DuotopiaScenarios.add_student_workflow,
    "create_assignment": DuotopiaScenarios.create_assignment_workflow,
    "test_bug_fix": DuotopiaScenarios.test_add_student_then_assign,
    "test_ios_recording": DuotopiaScenarios.test_ios_safari_recording,
}
