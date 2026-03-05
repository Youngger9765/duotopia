"""
Test word selection phase-based logic (Issue #379)

Validates the phase-based selection algorithm ensures:
1. Unpracticed words are always selected first
2. Due-for-review words fill remaining slots
3. Not-due words (by lowest strength) fill as last resort
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal


# --- Pure logic extracted from SQL function for unit testing ---


def categorize_word(user_word_progress: dict | None, now: datetime) -> int:
    """
    Categorize a word into selection phase.
    Mirrors the SQL CASE logic in get_words_for_practice.

    Phase 1: Never practiced (no progress record)
    Phase 2: Due for review (next_review_at <= now)
    Phase 3: Not due yet (next_review_at > now)
    """
    if user_word_progress is None:
        return 1
    if user_word_progress.get("next_review_at") is None:
        return 1
    if user_word_progress["next_review_at"] <= now:
        return 2
    return 3


def calculate_priority_score(phase: int, memory_strength: float) -> float:
    """
    Calculate priority score for API response compatibility.
    Mirrors the SQL CASE logic.
    """
    if phase == 1:
        return 100.0
    elif phase == 2:
        return 50 + (1 - memory_strength) * 50
    else:
        return (1 - memory_strength) * 30


def select_words_for_practice(
    all_words: list[dict],
    progress_map: dict[int, dict],
    now: datetime,
    limit: int = 10,
) -> list[dict]:
    """
    Phase-based word selection algorithm.
    Mirrors the SQL ORDER BY c.phase ASC, c.mem_strength ASC, RANDOM()

    Args:
        all_words: All content items in the assignment
        progress_map: {content_item_id: user_word_progress} for practiced words
        now: Current timestamp
        limit: Number of words to select

    Returns:
        Selected words sorted by phase and strength
    """
    categorized = []
    for word in all_words:
        cid = word["content_item_id"]
        progress = progress_map.get(cid)
        phase = categorize_word(progress, now)
        mem_strength = progress["memory_strength"] if progress else 0.0

        categorized.append(
            {
                **word,
                "phase": phase,
                "memory_strength": mem_strength,
                "priority_score": calculate_priority_score(phase, mem_strength),
            }
        )

    # Sort: phase ASC, memory_strength ASC (weakest first)
    # Note: RANDOM() tiebreaker is omitted in tests for determinism
    categorized.sort(key=lambda w: (w["phase"], w["memory_strength"]))

    return categorized[:limit]


# --- Test fixtures ---


def make_word(cid: int) -> dict:
    """Create a minimal word dict."""
    return {
        "content_item_id": cid,
        "text": f"word_{cid}",
        "translation": f"translation_{cid}",
    }


def make_progress(
    memory_strength: float,
    next_review_at: datetime | None,
) -> dict:
    """Create a user_word_progress record."""
    return {
        "memory_strength": memory_strength,
        "next_review_at": next_review_at,
    }


# --- Tests ---


class TestCategorizeWord:
    """Test phase categorization logic."""

    def test_no_progress_is_phase_1(self):
        """Words with no progress record are phase 1 (unpracticed)."""
        assert categorize_word(None, datetime.now(timezone.utc)) == 1

    def test_no_next_review_is_phase_1(self):
        """Words with no next_review_at are phase 1."""
        progress = {"memory_strength": 0.5, "next_review_at": None}
        assert categorize_word(progress, datetime.now(timezone.utc)) == 1

    def test_due_for_review_is_phase_2(self):
        """Words past their review date are phase 2."""
        now = datetime.now(timezone.utc)
        progress = {
            "memory_strength": 0.5,
            "next_review_at": now - timedelta(hours=1),
        }
        assert categorize_word(progress, now) == 2

    def test_review_at_now_is_phase_2(self):
        """Words exactly at review time are phase 2."""
        now = datetime.now(timezone.utc)
        progress = {"memory_strength": 0.5, "next_review_at": now}
        assert categorize_word(progress, now) == 2

    def test_not_due_is_phase_3(self):
        """Words not yet due for review are phase 3."""
        now = datetime.now(timezone.utc)
        progress = {
            "memory_strength": 0.5,
            "next_review_at": now + timedelta(days=1),
        }
        assert categorize_word(progress, now) == 3


class TestPriorityScore:
    """Test priority score calculation."""

    def test_phase_1_always_100(self):
        assert calculate_priority_score(1, 0.0) == 100.0
        assert calculate_priority_score(1, 0.5) == 100.0

    def test_phase_2_range_50_to_100(self):
        assert calculate_priority_score(2, 0.0) == 100.0
        assert calculate_priority_score(2, 0.5) == 75.0
        assert calculate_priority_score(2, 1.0) == 50.0

    def test_phase_3_range_0_to_30(self):
        assert calculate_priority_score(3, 0.0) == 30.0
        assert calculate_priority_score(3, 0.5) == 15.0
        assert calculate_priority_score(3, 1.0) == 0.0


class TestSelectWordsForPractice:
    """Test the full word selection algorithm."""

    def test_round1_selects_unpracticed_words(self):
        """Round 1: All words unpracticed, should select 10 randomly."""
        words = [make_word(i) for i in range(1, 31)]  # 30 words
        progress_map = {}  # No progress yet
        now = datetime.now(timezone.utc)

        selected = select_words_for_practice(words, progress_map, now, limit=10)

        assert len(selected) == 10
        # All selected should be phase 1 (unpracticed)
        for w in selected:
            assert w["phase"] == 1
            assert w["priority_score"] == 100.0

    def test_round2_selects_different_unpracticed_words(self):
        """
        Round 2: After practicing 10 words in round 1,
        should select from the remaining 20 unpracticed words.
        THIS IS THE BUG FIX - previously same 10 words were selected.
        """
        words = [make_word(i) for i in range(1, 31)]  # 30 words
        now = datetime.now(timezone.utc)

        # Simulate round 1: words 1-10 were practiced (correct answers)
        progress_map = {}
        for i in range(1, 11):
            progress_map[i] = make_progress(
                memory_strength=0.5,
                next_review_at=now + timedelta(days=1),  # Due tomorrow
            )

        selected = select_words_for_practice(words, progress_map, now, limit=10)

        assert len(selected) == 10

        # ALL selected should be phase 1 (unpracticed) - NOT from words 1-10
        selected_ids = {w["content_item_id"] for w in selected}
        practiced_ids = set(range(1, 11))

        assert selected_ids.isdisjoint(practiced_ids), (
            f"Bug #379: Selected words {selected_ids} overlap with "
            f"already-practiced words {practiced_ids}. "
            f"Unpracticed words should be selected first!"
        )

        for w in selected:
            assert w["phase"] == 1

    def test_round3_selects_remaining_unpracticed(self):
        """Round 3: After 20 practiced, selects final 10 unpracticed."""
        words = [make_word(i) for i in range(1, 31)]  # 30 words
        now = datetime.now(timezone.utc)

        # Words 1-20 practiced
        progress_map = {}
        for i in range(1, 21):
            progress_map[i] = make_progress(
                memory_strength=0.5,
                next_review_at=now + timedelta(days=1),
            )

        selected = select_words_for_practice(words, progress_map, now, limit=10)

        assert len(selected) == 10
        selected_ids = {w["content_item_id"] for w in selected}

        # Should be words 21-30 (the unpracticed ones)
        expected_ids = set(range(21, 31))
        assert selected_ids == expected_ids

    def test_round4_all_practiced_selects_weakest(self):
        """
        Round 4: All 30 words practiced, should select 10 with
        lowest memory_strength (weakest words need more practice).
        """
        words = [make_word(i) for i in range(1, 31)]  # 30 words
        now = datetime.now(timezone.utc)

        # All 30 words practiced with varying strengths
        progress_map = {}
        for i in range(1, 31):
            # Words 1-10: weak (0.2), 11-20: medium (0.5), 21-30: strong (0.8)
            if i <= 10:
                strength = 0.2
            elif i <= 20:
                strength = 0.5
            else:
                strength = 0.8
            progress_map[i] = make_progress(
                memory_strength=strength,
                next_review_at=now + timedelta(days=1),
            )

        selected = select_words_for_practice(words, progress_map, now, limit=10)

        assert len(selected) == 10
        selected_ids = {w["content_item_id"] for w in selected}

        # Should select the 10 weakest words (1-10, strength=0.2)
        expected_weak_ids = set(range(1, 11))
        assert selected_ids == expected_weak_ids

    def test_mixed_phases_prioritize_correctly(self):
        """
        Mixed scenario: some unpracticed, some due, some not due.
        Should fill: unpracticed first, then due, then not-due.
        """
        words = [make_word(i) for i in range(1, 16)]  # 15 words
        now = datetime.now(timezone.utc)

        progress_map = {
            # Words 1-3: due for review (phase 2), weak
            1: make_progress(0.3, now - timedelta(hours=1)),
            2: make_progress(0.2, now - timedelta(hours=2)),
            3: make_progress(0.4, now - timedelta(hours=3)),
            # Words 4-8: not due yet (phase 3)
            4: make_progress(0.5, now + timedelta(days=1)),
            5: make_progress(0.6, now + timedelta(days=2)),
            6: make_progress(0.7, now + timedelta(days=3)),
            7: make_progress(0.8, now + timedelta(days=4)),
            8: make_progress(0.9, now + timedelta(days=5)),
            # Words 9-15: unpracticed (phase 1) - 7 words
        }

        selected = select_words_for_practice(words, progress_map, now, limit=10)
        assert len(selected) == 10

        # First 7 should be unpracticed (phase 1): words 9-15
        phase_1_selected = [w for w in selected if w["phase"] == 1]
        assert len(phase_1_selected) == 7

        # Next 3 should be due for review (phase 2): words 1-3
        phase_2_selected = [w for w in selected if w["phase"] == 2]
        assert len(phase_2_selected) == 3

        # No phase 3 words should be selected (we already have 10)
        phase_3_selected = [w for w in selected if w["phase"] == 3]
        assert len(phase_3_selected) == 0

    def test_due_for_review_sorted_by_weakest(self):
        """When selecting due-for-review words, weakest memory first."""
        words = [make_word(i) for i in range(1, 11)]  # 10 words, all due
        now = datetime.now(timezone.utc)

        progress_map = {}
        for i in range(1, 11):
            progress_map[i] = make_progress(
                memory_strength=i * 0.1,  # 0.1, 0.2, ..., 1.0
                next_review_at=now - timedelta(hours=1),  # All due
            )

        selected = select_words_for_practice(words, progress_map, now, limit=5)

        assert len(selected) == 5
        # Should select words 1-5 (weakest: 0.1 to 0.5)
        selected_ids = [w["content_item_id"] for w in selected]
        assert selected_ids == [1, 2, 3, 4, 5]

    def test_fewer_words_than_limit(self):
        """Assignment with fewer words than limit returns all words."""
        words = [make_word(i) for i in range(1, 6)]  # Only 5 words
        progress_map = {}
        now = datetime.now(timezone.utc)

        selected = select_words_for_practice(words, progress_map, now, limit=10)

        assert len(selected) == 5
        selected_ids = {w["content_item_id"] for w in selected}
        assert selected_ids == {1, 2, 3, 4, 5}

    def test_incorrect_answers_have_lower_strength(self):
        """
        Words answered incorrectly (strength=0.2) should be prioritized
        over correctly-answered words (strength=0.5) in phase 3.
        """
        words = [make_word(i) for i in range(1, 21)]  # 20 words
        now = datetime.now(timezone.utc)

        progress_map = {}
        for i in range(1, 21):
            if i <= 10:
                # Answered incorrectly: lower strength
                progress_map[i] = make_progress(
                    memory_strength=0.2,
                    next_review_at=now + timedelta(days=1),
                )
            else:
                # Answered correctly: higher strength
                progress_map[i] = make_progress(
                    memory_strength=0.8,
                    next_review_at=now + timedelta(days=6),
                )

        selected = select_words_for_practice(words, progress_map, now, limit=10)
        selected_ids = {w["content_item_id"] for w in selected}

        # All selected should be the weak ones (1-10)
        assert selected_ids == set(range(1, 11))
