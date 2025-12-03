"""
Unit test for auto-calculating assignment scores from AI assessments

Tests the calculate_assignment_score function which aggregates
StudentItemProgress AI scores into a total assignment score.
"""

from decimal import Decimal
from unittest.mock import Mock, MagicMock
from routers.students import calculate_assignment_score


class TestCalculateAssignmentScore:
    """Test the score calculation logic"""

    def test_all_items_with_complete_scores(self):
        """
        Test: 5 items, all with complete AI scores
        Expected: Average of item averages = 88.6
        """
        # Mock database session
        mock_db = Mock()

        # Mock StudentItemProgress items with scores
        mock_items = []
        scores = [
            (90, 85, 88),  # avg = 87.67
            (92, 90, 95),  # avg = 92.33
            (88, 82, 86),  # avg = 85.33
            (95, 93, 97),  # avg = 95.00
            (85, 80, 83),  # avg = 82.67
        ]

        for acc, flu, pro in scores:
            item = Mock()
            item.accuracy_score = Decimal(str(acc))
            item.fluency_score = Decimal(str(flu))
            item.pronunciation_score = Decimal(str(pro))

            # Mock the overall_score property
            avg = (acc + flu + pro) / 3
            item.overall_score = Decimal(str(round(avg, 2)))

            mock_items.append(item)

        # Mock query result
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        # Execute
        result = calculate_assignment_score(123, mock_db)

        # Assert
        assert result is not None
        assert abs(result - 88.6) < 0.5, f"Expected ~88.6, got {result}"

    def test_some_items_missing_scores(self):
        """
        Test: 3 items, one without AI scores
        Expected: Missing item counts as 0
        """
        mock_db = Mock()

        mock_items = []

        # Item 1: has scores (avg = 87.67)
        item1 = Mock()
        item1.accuracy_score = Decimal("90")
        item1.fluency_score = Decimal("85")
        item1.pronunciation_score = Decimal("88")
        item1.overall_score = Decimal("87.67")
        mock_items.append(item1)

        # Item 2: no scores
        item2 = Mock()
        item2.accuracy_score = None
        item2.fluency_score = None
        item2.pronunciation_score = None
        item2.overall_score = None
        mock_items.append(item2)

        # Item 3: has scores (avg = 85.33)
        item3 = Mock()
        item3.accuracy_score = Decimal("88")
        item3.fluency_score = Decimal("82")
        item3.pronunciation_score = Decimal("86")
        item3.overall_score = Decimal("85.33")
        mock_items.append(item3)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        # Expected: (87.67 + 0 + 85.33) / 3 = 57.67
        assert result is not None
        assert abs(result - 57.67) < 1.0, f"Expected ~57.67, got {result}"

    def test_all_items_no_scores(self):
        """
        Test: All items have no AI scores
        Expected: Total score = 0
        """
        mock_db = Mock()

        mock_items = []
        for _ in range(3):
            item = Mock()
            item.accuracy_score = None
            item.fluency_score = None
            item.pronunciation_score = None
            item.overall_score = None
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 0.0

    def test_no_items(self):
        """
        Test: No StudentItemProgress records
        Expected: Return None
        """
        mock_db = Mock()

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result is None

    def test_partial_dimensions(self):
        """
        Test: Items with only some dimensions scored
        Expected: Calculate from available dimensions
        """
        mock_db = Mock()

        mock_items = []

        # Item 1: Only accuracy and fluency (avg = 87.5)
        item1 = Mock()
        item1.accuracy_score = Decimal("90")
        item1.fluency_score = Decimal("85")
        item1.pronunciation_score = None
        item1.overall_score = Decimal("87.5")
        mock_items.append(item1)

        # Item 2: Only accuracy (avg = 92)
        item2 = Mock()
        item2.accuracy_score = Decimal("92")
        item2.fluency_score = None
        item2.pronunciation_score = None
        item2.overall_score = Decimal("92.0")
        mock_items.append(item2)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        # Expected: (87.5 + 92) / 2 = 89.75
        assert result is not None
        assert abs(result - 89.75) < 0.5, f"Expected ~89.75, got {result}"

    def test_boundary_perfect_score(self):
        """
        Boundary test: All items have perfect scores (100)
        Expected: Total score = 100
        """
        mock_db = Mock()

        mock_items = []
        for _ in range(5):
            item = Mock()
            item.accuracy_score = Decimal("100")
            item.fluency_score = Decimal("100")
            item.pronunciation_score = Decimal("100")
            item.overall_score = Decimal("100.0")
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 100.0

    def test_boundary_zero_score(self):
        """
        Boundary test: All items have zero scores
        Expected: Total score = 0
        """
        mock_db = Mock()

        mock_items = []
        for _ in range(5):
            item = Mock()
            item.accuracy_score = Decimal("0")
            item.fluency_score = Decimal("0")
            item.pronunciation_score = Decimal("0")
            item.overall_score = Decimal("0.0")
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 0.0

    def test_boundary_score_over_100(self):
        """
        Boundary test: Item scores somehow exceed 100
        Expected: Total score clamped to 100
        """
        mock_db = Mock()

        mock_items = []
        for _ in range(3):
            item = Mock()
            item.accuracy_score = Decimal("110")  # Invalid but possible bug
            item.fluency_score = Decimal("105")
            item.pronunciation_score = Decimal("108")
            item.overall_score = Decimal("107.67")
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        # Should be clamped to 100
        assert result == 100.0

    def test_boundary_negative_scores(self):
        """
        Boundary test: Item scores are negative (data corruption)
        Expected: Total score clamped to 0
        """
        mock_db = Mock()

        mock_items = []
        item = Mock()
        item.accuracy_score = Decimal("-10")
        item.fluency_score = Decimal("-20")
        item.pronunciation_score = Decimal("-15")
        item.overall_score = Decimal("-15.0")
        mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        # Should be clamped to 0
        assert result == 0.0

    def test_mixed_10_items_6_with_scores(self):
        """
        Real scenario: 10 items, only 6 have AI scores
        Expected: 4 items count as 0, calculate average of all 10
        """
        mock_db = Mock()

        mock_items = []

        # 6 items with scores (avg ~85)
        for i in range(6):
            item = Mock()
            item.accuracy_score = Decimal("85")
            item.fluency_score = Decimal("82")
            item.pronunciation_score = Decimal("88")
            item.overall_score = Decimal("85.0")
            mock_items.append(item)

        # 4 items without scores (count as 0)
        for i in range(4):
            item = Mock()
            item.accuracy_score = None
            item.fluency_score = None
            item.pronunciation_score = None
            item.overall_score = None
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        # Expected: (85*6 + 0*4) / 10 = 51.0
        assert result is not None
        assert abs(result - 51.0) < 1.0, f"Expected ~51.0, got {result}"

    def test_item_with_only_two_dimensions(self):
        """
        Edge case: Item has only 2 out of 3 dimensions scored
        Expected: Calculate from available 2 dimensions
        """
        mock_db = Mock()

        mock_items = []

        # Item with only accuracy and fluency
        item = Mock()
        item.accuracy_score = Decimal("90")
        item.fluency_score = Decimal("80")
        item.pronunciation_score = None
        # overall_score should be (90+80)/2 = 85
        item.overall_score = Decimal("85.0")
        mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 85.0

    def test_item_with_only_one_dimension(self):
        """
        Edge case: Item has only 1 out of 3 dimensions scored
        Expected: Use that single dimension as the score
        """
        mock_db = Mock()

        mock_items = []

        # Item with only accuracy
        item = Mock()
        item.accuracy_score = Decimal("75")
        item.fluency_score = None
        item.pronunciation_score = None
        item.overall_score = Decimal("75.0")
        mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 75.0

    def test_all_items_have_null_scores(self):
        """
        Edge case: All items exist but all have NULL scores
        Expected: All count as 0, total = 0
        """
        mock_db = Mock()

        mock_items = []
        for _ in range(5):
            item = Mock()
            item.accuracy_score = None
            item.fluency_score = None
            item.pronunciation_score = None
            item.overall_score = None
            mock_items.append(item)

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_items
        mock_db.query.return_value = mock_query

        result = calculate_assignment_score(123, mock_db)

        assert result == 0.0
