"""
N+1 Query Detection Tests for Student Assignment APIs

測試 Student Assignment 相關 API 是否存在 N+1 query 問題。
"""

from tests.utils import QueryCounter, assert_max_queries


class TestStudentAssignmentActivitiesN1:
    """測試 Student Assignment Activities API 的 N+1 query 問題"""

    def test_get_assignment_activities_with_few_items(
        self, test_client, db_session, auth_headers_student, test_student_assignment
    ):
        """
        測試：少量題目時的查詢次數

        預期：查詢次數應該固定，不隨題目數增長
        """
        assignment_id = test_student_assignment["id"]

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/students/assignments/{assignment_id}/activities",
                headers=auth_headers_student,
            )

        # Assert: 應該成功
        assert response.status_code == 200
        data = response.json()
        activities = data.get("activities", [])
        assert len(activities) > 0

        # 🔥 關鍵斷言：查詢次數應該 <= 15（固定，不隨題目數增長）
        try:
            assert_max_queries(
                counter,
                15,
                "Student assignment activities should use <= 15 queries",
            )
        except AssertionError:
            print("\n❌ N+1 Query Detected:")
            print(f"   Activity count: {len(activities)}")
            print(f"   Query count: {counter.count}")
            print("   Expected: <= 15 queries")
            print(f"\n{counter.get_summary()}")
            raise

    def test_get_assignment_activities_with_many_items(
        self,
        test_client,
        db_session,
        auth_headers_student,
        test_student_assignment_many_items,
    ):
        """
        測試：大量題目時的查詢次數

        這個測試用來驗證查詢次數是否隨題目數線性增長（N+1 pattern）
        """
        assignment_id = test_student_assignment_many_items["id"]

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/students/assignments/{assignment_id}/activities",
                headers=auth_headers_student,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        activities = data.get("activities", [])
        assert len(activities) > 0

        # 🔥 查詢次數應該仍然 <= 15（不隨題目數增長）
        try:
            assert_max_queries(
                counter,
                15,
                f"Assignment activities with {len(activities)} items should use <= 15 queries (same as few items)",
            )
        except AssertionError:
            print("\n❌ N+1 Query Confirmed (scales with data):")
            print(f"   Activity count: {len(activities)}")
            print(f"   Query count: {counter.count}")
            print("   This confirms N+1 pattern!")
            print(f"\n{counter.get_summary()}")
            raise


class TestStudentLinkedAccountsN1:
    """測試 Student Linked Accounts API 的 N+1 query 問題"""

    def test_get_linked_accounts(
        self,
        test_client,
        db_session,
        auth_headers_student,
        test_student_with_linked_accounts,
    ):
        """
        測試：取得連結帳號列表時的查詢次數

        預期失敗原因：
        - 當前實作在循環中查詢每個 student 的 classroom
        """
        student_id = test_student_with_linked_accounts["id"]
        linked_count = test_student_with_linked_accounts["linked_count"]

        # Act: 執行 API 並計數查詢
        with QueryCounter() as counter:
            response = test_client.get(
                f"/api/students/{student_id}/linked-accounts",
                headers=auth_headers_student,
            )

        # Assert
        assert response.status_code == 200
        data = response.json()
        linked_accounts = data.get("linked_accounts", [])
        assert len(linked_accounts) == linked_count

        # 🔥 查詢次數應該 <= 10（固定，不隨連結帳號數增長）
        try:
            assert_max_queries(counter, 10, "Linked accounts should use <= 10 queries")
        except AssertionError:
            print("\n❌ N+1 Query in Linked Accounts:")
            print(f"   Linked account count: {linked_count}")
            print(f"   Query count: {counter.count}")
            print(counter.get_summary())
            raise
