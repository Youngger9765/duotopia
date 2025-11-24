"""
Query Counter Utility for N+1 Query Detection

用於測試中監聽並計數 SQL 查詢，幫助檢測 N+1 query 問題。

使用範例：
    with QueryCounter() as counter:
        response = client.get("/api/teachers/assignments")

    # 驗證查詢次數不隨資料量增長
    assert counter.count <= 5, f"Expected <= 5 queries, got {counter.count}"
"""

from sqlalchemy import event
from sqlalchemy.engine import Engine
from typing import List, Optional


class QueryCounter:
    """
    監聽並計數 SQL 查詢的 context manager

    Attributes:
        count (int): 查詢次數
        queries (List[str]): 所有執行的 SQL 查詢
        enabled (bool): 是否啟用計數
    """

    def __init__(self, enabled: bool = True):
        """
        初始化 QueryCounter

        Args:
            enabled: 是否啟用計數（用於條件性測試）
        """
        self.count = 0
        self.queries: List[str] = []
        self.enabled = enabled
        self._listener_added = False

    def __enter__(self):
        """啟動查詢監聽"""
        if self.enabled:
            event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
            self._listener_added = True
        return self

    def __exit__(self, *args):
        """停止查詢監聽"""
        if self._listener_added:
            event.remove(Engine, "before_cursor_execute", self._before_cursor_execute)
            self._listener_added = False

    def _before_cursor_execute(
        self, conn, cursor, statement, parameters, context, executemany
    ):
        """
        SQLAlchemy event handler：在 SQL 執行前觸發

        Args:
            statement: SQL 查詢語句
        """
        self.count += 1
        self.queries.append(statement)

    def reset(self):
        """重置計數器"""
        self.count = 0
        self.queries = []

    def get_summary(self) -> str:
        """
        取得查詢摘要報告

        Returns:
            str: 包含查詢次數和每個查詢前 100 字元的報告
        """
        summary = f"Total queries: {self.count}\n"
        summary += "=" * 80 + "\n"

        for i, query in enumerate(self.queries, 1):
            # 清理查詢字串（移除多餘空白）
            cleaned_query = " ".join(query.split())
            summary += f"\nQuery {i}:\n{cleaned_query[:200]}\n"

        return summary

    def find_duplicates(self) -> List[str]:
        """
        找出重複的查詢模式（可能的 N+1 問題）

        Returns:
            List[str]: 重複查詢的列表
        """
        from collections import Counter

        # 簡化查詢（移除參數）來找出模式
        patterns = []
        for query in self.queries:
            # 簡單的模式匹配：移除數字和引號內容
            import re

            pattern = re.sub(r"\d+", "N", query)
            pattern = re.sub(r"'[^']*'", "'?'", pattern)
            patterns.append(pattern)

        # 找出出現超過 1 次的模式
        counts = Counter(patterns)
        duplicates = [pattern for pattern, count in counts.items() if count > 1]

        return duplicates


def assert_max_queries(
    counter: QueryCounter, max_queries: int, message: Optional[str] = None
):
    """
    斷言查詢次數不超過指定上限

    Args:
        counter: QueryCounter 實例
        max_queries: 最大允許查詢次數
        message: 自定義錯誤訊息

    Raises:
        AssertionError: 當查詢次數超過上限時
    """
    if counter.count > max_queries:
        error_msg = (
            message or f"Expected <= {max_queries} queries, but got {counter.count}"
        )
        error_msg += f"\n\n{counter.get_summary()}"

        # 檢查是否有重複查詢（N+1 pattern）
        duplicates = counter.find_duplicates()
        if duplicates:
            error_msg += "\n\n🚨 Detected potential N+1 query patterns:\n"
            for dup in duplicates[:3]:  # 只顯示前 3 個
                error_msg += f"  - {dup[:150]}...\n"

        raise AssertionError(error_msg)


def assert_fixed_queries(counter: QueryCounter, message: Optional[str] = None):
    """
    斷言查詢次數為固定值（不隨資料量增長）

    這是檢測 N+1 query 的核心方法：
    如果查詢次數隨著資料量線性增長，就表示有 N+1 問題。

    Args:
        counter: QueryCounter 實例
        message: 自定義錯誤訊息

    Note:
        此函數需要在測試中多次呼叫，比較不同資料量下的查詢次數
    """
    # 這個函數的實作需要在具體測試中根據場景調整
    # 這裡提供的是輔助工具，實際斷言在測試中完成
    pass
